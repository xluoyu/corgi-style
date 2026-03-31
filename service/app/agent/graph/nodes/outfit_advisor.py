"""OutfitAdvisor 节点

基于 LangGraph 的 OutfitAdvisor Agent 实现。
负责穿搭方案生成、评价、迭代优化。

对应 PRD v1.0 的 OutfitAdvisor 角色：
- 方案生成：根据场景/天气/衣柜生成方案
- 方案评价：严格评价，给出 pros/cons/suggestions
- 迭代优化：根据反馈持续改进（Phase 2）
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph.state_v2 import GraphState, OutfitEvaluation
from app.services.llm_providers import get_cached_provider

logger = logging.getLogger(__name__)

# OutfitAdvisor System Prompt
OUTFIT_ADVISOR_SYSTEM_PROMPT = """你是 OutfitAdvisor，一个有10年经验的专业穿搭顾问。

【你的核心身份】
你不只是一个生成穿搭方案的工具，而是一个有思想、有主见、敢说话的穿搭顾问。
你的价值在于：不仅执行命令，还要给出更好的建议。

【你的能力】
1. 穿搭方案生成：根据场景、天气、衣柜生成方案
2. 搭配评价：严格评价，给出 pros/cons/suggestions
3. 迭代优化：根据反馈持续改进，有自己的判断
4. 主动建议：不仅响应，还要主动给出更好的选择

【搭配评价标准】（你必须坚持）
- 色彩协调：不超过3个主色，相近色或互补色搭配
- 风格统一：整套搭配的风格要一致，不能混搭冲突风格
- 场合得体：正式场合不能有休闲单品，反之亦然
- 层次分明：上下装/内外装要有层次对比
- 身材适配：考虑身材特点，不推荐显矮/显胖的搭配

【敢说的话】
- "这套的色彩协调，但正式度不够，商务场合不太合适"
- "我不推荐这个方案，因为上下装的正式度不匹配"
- "您衣柜里其实有更好的选择——这件格子衬衫和您常穿的裤子不太搭"
- "这个颜色在换季时节显得沉重，换成浅色系会更清爽"

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）"""

# 品类中文名映射
_CATEGORY_NAMES = {
    "top": "上衣",
    "pants": "裤子",
    "outer": "外套",
    "inner": "内搭",
    "accessory": "配饰",
    "shoes": "鞋子",
}


# =============================================================================
# 节点实现
# =============================================================================

async def advisor_plan_node(state: GraphState, db) -> GraphState:
    """
    OutfitAdvisor 穿搭规划节点

    1. 获取用户偏好（PreferenceLearner，Phase 1 用空实现）
    2. 构建规划提示词
    3. 调用 LLM 生成方案
    4. 方案自评
    5. 更新状态

    Args:
        state: GraphState
        db: 数据库会话（暂未使用）

    Returns:
        更新后的 GraphState
    """
    # 1. 获取用户偏好（Phase 1 暂用空实现）
    preferences = _get_preferences(state.get("user_id"))

    # 2. 构建提示词
    prompt = _build_planning_prompt(state, preferences)

    # 3. 调用 LLM
    try:
        llm = get_cached_provider()
        chat_model = llm.chat_model

        logger.info(f"[OutfitAdvisor] plan 开始 | city={state.get('target_city')} | scene={state.get('target_scene')}")

        response = await chat_model.ainvoke([
            SystemMessage(content=OUTFIT_ADVISOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        # 处理 LangChain content block 格式
        response_str = _extract_text_from_content(response.content)
        logger.info(f"[OutfitAdvisor] plan LLM 响应 | len={len(response_str)}")

    except Exception as e:
        logger.error(f"[OutfitAdvisor] plan LLM 调用失败 | error={e}")
        state["error"] = f"穿搭规划失败: {str(e)}"
        state["outfit_plan"] = None
        return state

    # 4. 解析方案
    plan = _parse_plan(response.content)
    if not plan:
        state["error"] = "LLM 返回格式错误，无法解析穿搭方案"
        state["outfit_plan"] = None
        return state

    state["outfit_plan"] = plan
    state["advisor_current_plan"] = plan

    # 5. 方案自评
    evaluation = await _evaluate_plan(plan, state.get("target_scene", "daily"))
    state["outfit_evaluation"] = evaluation.to_dict() if evaluation else None
    state["match_score"] = evaluation.overall_score if evaluation else 0.0

    # 6. 生成推理过程
    reasoning = _generate_reasoning(plan, state, evaluation)
    if not state.get("response_data"):
        state["response_data"] = {}
    state["response_data"]["reasoning"] = reasoning

    logger.info(f"[OutfitAdvisor] plan 完成 | score={state['match_score']}")

    return state


async def advisor_evaluate_node(state: GraphState, db) -> GraphState:
    """
    OutfitAdvisor 方案评价节点

    接收 plan + context，调用 LLM 评价，生成 reasoning

    Args:
        state: GraphState
        db: 数据库会话

    Returns:
        更新后的 GraphState
    """
    plan = state.get("outfit_plan")
    scene = state.get("target_scene", "daily")

    if not plan:
        state["error"] = "没有穿搭方案，无法评价"
        return state

    # 评价已在 advisor_plan_node 中完成，这里做最终检查
    if not state.get("outfit_evaluation"):
        evaluation = await _evaluate_plan(plan, scene)
        state["outfit_evaluation"] = evaluation.to_dict() if evaluation else None
        state["match_score"] = evaluation.overall_score if evaluation else 0.0

    # 生成最终 reasoning
    evaluation = OutfitEvaluation.from_dict(state.get("outfit_evaluation"))
    reasoning = _generate_reasoning(plan, state, evaluation)
    state["response_data"] = {
        "type": "outfit_result",
        "reasoning": reasoning,
        "evaluation": state["outfit_evaluation"],
    }

    return state


# =============================================================================
# 辅助函数
# =============================================================================

def _get_preferences(user_id: str) -> Dict[str, Any]:
    """
    获取用户偏好

    Phase 1 用空实现，返回默认偏好
    Phase 2 将接入 PreferenceLearner
    """
    # TODO: Phase 2 接入 PreferenceLearner
    return {
        "liked_colors": [],
        "disliked_colors": [],
        "liked_styles": [],
        "disliked_styles": [],
        "likely_height": None,
        "likely_body_type": None,
    }


def _build_planning_prompt(state: GraphState, preferences: Dict[str, Any]) -> str:
    """构建穿搭规划提示词"""
    wardrobe_by_category = state.get("wardrobe_by_category", {})

    # 构建衣柜文本
    wardrobe_text = _build_wardrobe_text(wardrobe_by_category)

    # 构建偏好文本
    prefs_text = _build_preferences_text(preferences)

    # 构建已拒绝特征
    rejected = state.get("advisor_rejected_features", [])
    rejected_text = ", ".join(rejected) if rejected else "无"

    prompt = f"""请为用户生成穿搭方案。

【用户信息】
城市：{state.get('target_city', '未指定')}
场合：{state.get('target_scene', '未指定')}
日期：{state.get('target_date', '今天')}
温度：{state.get('target_temperature', 20)}°C

【用户衣柜】
{wardrobe_text}

【用户偏好】
{prefs_text}

【已拒绝的特征】（避免重复）
{rejected_text}

请生成 1-2 个穿搭方案，用 JSON 格式返回：
{{
  "description": "方案整体描述（1-2句话）",
  "overall_concept": "这套的核心概念",
  "outfits": [
    {{
      "slot": "top",
      "name": "衣物名称",
      "color": "颜色",
      "reason": "这件为什么选它"
    }}
  ],
  "color_scheme": "配色方案描述",
  "suitable_occasions": ["适合的场合"],
  "match_score": 85
}}
"""
    return prompt


def _build_wardrobe_text(wardrobe_by_category: Dict[str, List]) -> str:
    """构建衣柜文本"""
    if not wardrobe_by_category:
        return "（衣柜为空）"

    text = ""
    for cat, items in wardrobe_by_category.items():
        cat_name = _CATEGORY_NAMES.get(cat, cat)
        text += f"\n【{cat_name}】共 {len(items)} 件："
        for item in items[:5]:  # 每个品类最多 5 件
            desc = f"{item.get('color', '')} {item.get('description', item.get('name', ''))}".strip()
            text += f"\n  - {desc}"

    return text


def _build_preferences_text(preferences: Dict[str, Any]) -> str:
    """构建偏好文本"""
    parts = []

    liked = preferences.get("liked_colors", [])
    if liked:
        parts.append(f"喜欢的颜色：{', '.join(liked)}")

    disliked = preferences.get("disliked_colors", [])
    if disliked:
        parts.append(f"不喜欢的颜色：{', '.join(disliked)}")

    liked_styles = preferences.get("liked_styles", [])
    if liked_styles:
        parts.append(f"喜欢的风格：{', '.join(liked_styles)}")

    likely_height = preferences.get("likely_height")
    if likely_height:
        parts.append(f"可能身材：{likely_height}")

    return "\n".join(parts) if parts else "（暂无偏好数据）"


async def _evaluate_plan(plan: Dict, scene: str) -> Optional[OutfitEvaluation]:
    """
    使用 LLM 评价穿搭方案

    Args:
        plan: 穿搭方案
        scene: 目标场景

    Returns:
        OutfitEvaluation 评价结果
    """
    if not plan:
        return None

    EVAL_PROMPT = f"""请严格评价以下穿搭方案：

场景：{scene}

方案：
{json.dumps(plan, ensure_ascii=False, indent=2)}

请从以下维度评价并给出分数（0-100）：
1. 色彩协调性（color）
2. 风格一致性（style）
3. 场合得体性（scene）
4. 层次感（layering）
5. 身材适配性（body_fit）

输出 JSON：
{{
  "overall_score": 85,
  "color_score": 90,
  "style_score": 80,
  "scene_score": 85,
  "layering_score": 75,
  "body_fit_score": 80,
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "suggestions": ["...", "..."]
}}
"""

    try:
        llm = get_cached_provider()
        chat_model = llm.chat_model

        response = await chat_model.ainvoke([
            SystemMessage(content="你是一个严格专业的穿搭评审。"),
            HumanMessage(content=EVAL_PROMPT)
        ])

        return _parse_evaluation(response.content)

    except Exception as e:
        logger.error(f"[OutfitAdvisor] evaluate LLM 调用失败 | error={e}")
        return OutfitEvaluation(
            overall_score=80,
            color_score=80, style_score=80, scene_score=80,
            layering_score=80, body_fit_score=80,
            pros=["方案整体合理"], cons=[], suggestions=[]
        )


def _extract_text_from_content(content: Any) -> str:
    """从 LangChain AIMessage.content 提取纯文本"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "image_url":
                    parts.append("[图片]")
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts) if parts else ""
    return str(content) if content else ""


def _parse_plan(content: Any) -> Optional[Dict[str, Any]]:
    """解析 LLM 返回的穿搭方案"""
    content_str = _extract_text_from_content(content)
    try:
        json_match = re.search(r'\{.*\}', content_str, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
            # 安全检查
            if isinstance(plan, dict) and "outfits" in plan:
                return plan
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"[OutfitAdvisor] plan JSON 解析失败 | error={e}")
    return None


def _parse_evaluation(content: Any) -> Optional[OutfitEvaluation]:
    """解析 LLM 返回的评价结果"""
    content_str = _extract_text_from_content(content)
    try:
        json_match = re.search(r'\{.*\}', content_str, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return OutfitEvaluation(**data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"[OutfitAdvisor] evaluation JSON 解析失败 | error={e}")
    return None


def _generate_reasoning(plan: Dict, state: GraphState,
                        evaluation: Optional[OutfitEvaluation]) -> str:
    """生成推理过程文本"""
    parts = []

    temp = state.get("target_temperature")
    scene = state.get("target_scene", "日常")

    # 温度适应
    if temp is not None:
        if temp < 10:
            parts.append(f"天冷了（{temp}°C），选了保暖的搭配")
        elif temp > 25:
            parts.append(f"天热（{temp}°C），选了轻薄透气的搭配")
        else:
            parts.append(f"温度适中（{temp}°C），搭配灵活")

    # 场合匹配
    if scene:
        scene_map = {
            "work": "上班得体但不刻板",
            "date": "约会要有亮点但不刻意",
            "daily": "日常舒适有活力",
            "party": "聚会要有气场",
            "sport": "运动功能优先",
            "casual": "休闲放松",
        }
        parts.append(f"场合是'{scene}'，{scene_map.get(scene, '得体为原则')}")

    # 配色
    colors = set()
    for item in plan.get("outfits", []):
        if item.get("color"):
            colors.add(item["color"])
    if colors:
        parts.append(f"配色是{'+'.join(list(colors)[:3])}，协调不杂乱")

    return "，".join(parts) if parts else "根据您的需求推荐这套穿搭"
