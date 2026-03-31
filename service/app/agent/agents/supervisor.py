"""SupervisorAgent - 任务协调者

负责：
1. 意图识别
2. 路由决策
3. 结果汇总
4. 回复生成

Supervisor 不直接回答，而是决定调用哪个专家 Agent。
"""
import json
import logging
from typing import Dict, Any, List, Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from app.agent.graph.state_v2 import GraphState
from app.agent.tools.shared import get_weather, analyze_clothing_image, remember_context, recall_context
from app.agent.tools.wardrobe import search_wardrobe, add_clothes_to_wardrobe
from app.agent.tools.outfit import plan_outfit, get_outfit_history
from app.agent.tools.knowledge import search_knowledge_base
from app.services.llm_providers import get_cached_provider

logger = logging.getLogger(__name__)


# ============================================================
# Supervisor Prompt
# ============================================================

SUPERVISOR_SYSTEM_PROMPT = """你是一个任务协调者，负责将用户请求路由到正确的专家 Agent。

【你的职责】
1. 理解用户需求
2. 决定调用哪个专家 Agent
3. 等待 Agent 执行结果
4. 汇总结果生成回复

【专家 Agent】
- weather_agent: 查询天气信息（当需要知道温度、天气状况时）
- wardrobe_agent: 查询用户衣柜（当需要知道用户有什么衣服时）
- outfit_advisor_agent: 生成穿搭方案（当用户要推荐穿搭时）
- knowledge_agent: 回答穿搭知识、护理问题

【路由规则】
1. 用户说"穿什么"/"推荐穿搭"/"今天出门穿什么" → outfit_advisor_agent
2. 用户问天气/温度 → weather_agent
3. 用户问衣柜里有什么/有几件 → wardrobe_agent
4. 用户上传衣服图片 → wardrobe_agent (add_clothes_to_wardrobe)
5. 用户问护理/怎么洗/什么材质 → knowledge_agent
6. 用户说"太正式了"/"换个颜色"（对推荐结果反馈）→ outfit_advisor_agent（带反馈参数）

【重要】
- 你不自己回答，而是调用对应的 Agent
- 每个 Agent 会完成工作并返回结果
- 你根据结果生成最终回复

【上下文信息】
当前已记住的信息：
- 城市：{target_city}
- 场合：{target_scene}
- 日期：{target_date}
- 温度：{target_temperature}

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【输出格式】
决定后，输出你要调用的 Agent 和参数：

```
路由决定：weather_agent
参数：{{"city": "北京"}}
```

或者直接回答用户（如果不需要调用 Agent）：
```
直接回答：好的，我来帮您查询北京的天气。
```
"""


# ============================================================
# 工具映射
# ============================================================

AGENT_TOOLS = {
    "weather_agent": [get_weather],
    "wardrobe_agent": [search_wardrobe, add_clothes_to_wardrobe],
    "outfit_advisor_agent": [plan_outfit, search_wardrobe, get_weather],
    "knowledge_agent": [search_knowledge_base],
}


# ============================================================
# Supervisor Node
# ============================================================

async def supervisor_node(state: GraphState) -> GraphState:
    """
    Supervisor 节点：分析意图，决定路由

    Args:
        state: GraphState，包含 messages, context 等

    Returns:
        更新后的 state，包含 routing_decision, agent_result 等
    """
    user_message = _get_last_user_message(state)
    context = _build_context(state)

    logger.info(f"[Supervisor] 分析请求: {user_message[:50]}")

    # 构建 prompt
    prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        target_city=context.get("target_city", "未指定"),
        target_scene=context.get("target_scene", "未指定"),
        target_date=context.get("target_date", "未指定"),
        target_temperature=context.get("target_temperature", "未指定"),
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"用户请求：{user_message}"),
    ]

    # 调用 LLM 决定路由
    llm = get_cached_provider().chat_model
    response = await llm.ainvoke(messages)

    # 提取响应文本
    response_text = _extract_text(response.content)
    logger.info(f"[Supervisor] LLM 响应: {response_text[:200]}")

    # 解析路由决定
    routing = _parse_routing(response_text)

    if routing.get("direct_answer"):
        # 不需要调用 Agent，直接回答
        state["supervisor_response"] = routing["direct_answer"]
        state["should_end"] = True
        state["routing_decision"] = "direct"
    else:
        # 需要调用 Agent
        agent = routing.get("agent", "")
        params = routing.get("params", {})

        state["routing_decision"] = agent
        state["routing_params"] = params
        state["supervisor_response"] = None
        state["should_end"] = False

    logger.info(f"[Supervisor] 路由决定: {state['routing_decision']}")

    return state


def _get_last_user_message(state: GraphState) -> str:
    """获取最后一条用户消息"""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _build_context(state: GraphState) -> Dict[str, Any]:
    """构建上下文"""
    return {
        "target_city": state.get("target_city"),
        "target_scene": state.get("target_scene"),
        "target_date": state.get("target_date"),
        "target_temperature": state.get("target_temperature"),
    }


def _extract_text(content: Any) -> str:
    """从 LangChain 响应中提取文本"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts) if parts else str(content)
    return str(content) if content else ""


def _parse_routing(text: str) -> Dict[str, Any]:
    """解析路由决定"""
    import re

    # 检查是否是直接回答
    direct_match = re.search(r'直接回答[：:]\s*(.+)', text, re.DOTALL)
    if direct_match:
        return {"direct_answer": direct_match.group(1).strip()}

    # 检查路由决定
    routing_match = re.search(r'路由决定[：:]\s*(\w+)\s*参数[：:]\s*(\{.*\})', text, re.DOTALL)
    if routing_match:
        agent = routing_match.group(1).strip()
        try:
            params = json.loads(routing_match.group(2))
        except:
            params = {}
        return {"agent": agent, "params": params}

    # 尝试其他格式
    # 例如 "调用 weather_agent，参数 city=北京"
    for agent_name in ["weather_agent", "wardrobe_agent", "outfit_advisor_agent", "knowledge_agent"]:
        if agent_name in text:
            # 尝试提取参数
            param_match = re.search(r'city[=：]\s*["\']?([^"\'\n,}]+)', text)
            params = {}
            if param_match:
                params["city"] = param_match.group(1).strip()

            param_match = re.search(r'scene[=：]\s*["\']?([^"\'\n,}]+)', text)
            if param_match:
                params["scene"] = param_match.group(1).strip()

            return {"agent": agent_name, "params": params}

    # 默认返回直接回答
    return {"direct_answer": text}


# ============================================================
# Agent 节点（简单封装）
# ============================================================

async def weather_agent_node(state: GraphState) -> GraphState:
    """Weather Agent 节点"""
    state["last_agent"] = "weather_agent"
    params = state.get("routing_params", {})
    city = params.get("city") or state.get("target_city")

    if not city:
        state["agent_result"] = {"error": "缺少城市参数"}
        return state

    try:
        result = await get_weather.ainvoke({"city": city})
        data = json.loads(result)

        # 更新 state
        if "temperature" in data:
            state["target_temperature"] = float(data["temperature"])
        state["weather_data"] = data
        state["agent_result"] = data

        logger.info(f"[WeatherAgent] 查询成功: {city} {data.get('temperature')}℃")

    except Exception as e:
        logger.error(f"[WeatherAgent] 查询失败: {e}")
        state["agent_result"] = {"error": str(e)}

    return state


async def wardrobe_agent_node(state: GraphState) -> GraphState:
    """Wardrobe Agent 节点"""
    state["last_agent"] = "wardrobe_agent"
    params = state.get("routing_params", {})
    action = params.get("action", "search")

    if action == "add":
        # 添加衣物
        image_url = params.get("image_url")
        if image_url:
            try:
                result = await add_clothes_to_wardrobe.ainvoke({
                    "image_url": image_url,
                    "user_hint": params.get("description", "")
                })
                state["agent_result"] = json.loads(result)
            except Exception as e:
                state["agent_result"] = {"error": str(e)}
    else:
        # 查询衣柜
        try:
            result = await search_wardrobe.ainvoke({
                "category": params.get("category"),
                "color": params.get("color"),
            })
            data = json.loads(result)
            state["wardrobe_items"] = data.get("items", [])
            state["agent_result"] = data
            logger.info(f"[WardrobeAgent] 查询到 {len(state['wardrobe_items'])} 件衣物")
        except Exception as e:
            logger.error(f"[WardrobeAgent] 查询失败: {e}")
            state["agent_result"] = {"error": str(e)}

    return state


async def outfit_advisor_agent_node(state: GraphState) -> GraphState:
    """Outfit Advisor Agent 节点"""
    state["last_agent"] = "outfit_advisor_agent"
    # 检查是否有必要的数据
    if not state.get("target_city"):
        state["agent_result"] = {"error": "缺少城市信息，请先查询天气"}
        return state

    if not state.get("wardrobe_items"):
        # 先查询衣柜
        try:
            result = await search_wardrobe.ainvoke({})
            data = json.loads(result)
            state["wardrobe_items"] = data.get("items", [])
        except Exception as e:
            logger.error(f"[OutfitAdvisor] 查询衣柜失败: {e}")

    if not state.get("target_temperature"):
        # 先查询天气
        try:
            result = await get_weather.ainvoke({"city": state["target_city"]})
            data = json.loads(result)
            if "temperature" in data:
                state["target_temperature"] = float(data["temperature"])
            state["weather_data"] = data
        except Exception as e:
            logger.error(f"[OutfitAdvisor] 查询天气失败: {e}")

    # 生成穿搭方案
    try:
        scene = state.get("target_scene", "daily")
        temperature = state.get("target_temperature", 20)
        wardrobe_items = state.get("wardrobe_items", [])

        result = await plan_outfit.ainvoke({
            "scene": scene,
            "temperature": temperature,
            "wardrobe_items": wardrobe_items,
        })

        plan_data = json.loads(result)
        state["outfit_plan"] = plan_data
        state["agent_result"] = plan_data
        logger.info(f"[OutfitAdvisor] 生成方案成功")

    except Exception as e:
        logger.error(f"[OutfitAdvisor] 生成方案失败: {e}")
        state["agent_result"] = {"error": str(e)}

    return state


async def knowledge_agent_node(state: GraphState) -> GraphState:
    """Knowledge Agent 节点"""
    state["last_agent"] = "knowledge_agent"
    params = state.get("routing_params", {})
    query = params.get("query") or _get_last_user_message(state)

    try:
        result = await search_knowledge_base.ainvoke({"query": query})
        data = json.loads(result)
        state["agent_result"] = data
        logger.info(f"[KnowledgeAgent] 查询成功")
    except Exception as e:
        logger.error(f"[KnowledgeAgent] 查询失败: {e}")
        state["agent_result"] = {"error": str(e)}

    return state


# ============================================================
# 路由表
# ============================================================

AGENT_NODES = {
    "weather_agent": weather_agent_node,
    "wardrobe_agent": wardrobe_agent_node,
    "outfit_advisor_agent": outfit_advisor_agent_node,
    "knowledge_agent": knowledge_agent_node,
}
