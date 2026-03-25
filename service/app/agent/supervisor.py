"""SupervisorAgent — LLM 驱动的单 Supervisor 架构

核心原则：
- 唯一的 Agent（SupervisorAgent），LLM 自主选择工具
- Tool 是纯计算单元，不内嵌调用其他 Tool
- 所有跨工具编排由 Supervisor 的 tool_call 循环负责
"""
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.agent.memory import AgentMemory
from app.agent.dialogue_session import DialogueSessionManager, Message
from app.agent.tools.context import get_db_for_tools, get_current_user_id
from app.agent.tools.shared import get_weather, analyze_clothing_image, remember_context, recall_context
from app.agent.tools.wardrobe import search_wardrobe, add_clothes_to_wardrobe
from app.agent.tools.outfit import plan_outfit, get_outfit_history
from app.agent.tools.knowledge import search_knowledge_base
from app.services.llm_providers import get_cached_provider

# 旧版 Supervisor（兼容，保留用于衣柜穿搭推荐功能）
from typing import Dict, List
from sqlalchemy.orm import Session
from app.agent.plan_agent import PlanAgent
from app.agent.tools import RetrievalTool
from app.agent.short_circuit import ShortCircuitTool
from app.agent.combine_agent import CombineAgent
from app.models import OutfitRecord


# ==================== System Prompt ====================

SYSTEM_PROMPT = """你是一个专业的时尚穿搭助手。

【你的能力】
- 根据天气和场合推荐穿搭
- 识别和管理衣柜中的衣物
- 查询穿搭历史
- 回答天气相关问题
- 提供穿搭知识建议

【工具使用规则】
- 用户请求穿搭推荐 → 先调用 get_weather，再调用 search_wardrobe，最后调用 plan_outfit
  （注意：plan_outfit 需要传入 weather 数据和 wardrobe 数据，不要在 plan_outfit 内部再次查询）
- 用户上传衣物图片 → 先 analyze_clothing_image 识别，再用 add_clothes_to_wardrobe 存储
- 用户询问历史 → 直接调用 get_outfit_history
- 用户提到城市/场合/日期 → 调用 remember_context 记住信息
- 用户询问穿搭知识 → 调用 search_knowledge_base

【追问策略】
- 缺少城市 → "请问要去哪个城市呢？"
- 缺少场合 → "请问是什么场合呢？（上班/约会/运动...）"
- 用户意图不明 → "我需要更多信息来帮您，请描述一下具体需求？"

【穿衣规则】（内置知识，可直接使用）
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）

【反馈处理】
- 用户说"太正式/太休闲/换个颜色" → 调用 remember_context 更新 scene/style，再调用 plan_outfit
- 用户说"再推荐一套" → 直接调用 plan_outfit（不重复问）
- 用户说"就这套了" → 告诉用户穿搭已记录到历史
"""


# ==================== SupervisorAgent ====================

class SupervisorAgent:
    """唯一的 Agent，使用 LLM Function Calling 自主选择工具"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        session_manager: DialogueSessionManager = None,
        db=None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.session_manager = session_manager

        # 初始化 AgentMemory（从 Session 恢复或新建）
        if session_manager:
            session = session_manager.get(session_id)
            if session and session.context:
                ctx = session.context
                self.memory = AgentMemory(
                    session_id=session_id,
                    user_id=user_id,
                    target_city=getattr(ctx, 'target_city', None),
                    target_scene=getattr(ctx, 'target_scene', None),
                    target_date=getattr(ctx, 'target_date', None),
                    target_temperature=getattr(ctx, 'target_temperature', None),
                )
            else:
                self.memory = AgentMemory(session_id=session_id, user_id=user_id)
        else:
            self.memory = AgentMemory(session_id=session_id, user_id=user_id)

        # 收集所有工具
        self.tools = {
            get_weather.name: get_weather,
            analyze_clothing_image.name: analyze_clothing_image,
            remember_context.name: remember_context,
            recall_context.name: recall_context,
            search_wardrobe.name: search_wardrobe,
            add_clothes_to_wardrobe.name: add_clothes_to_wardrobe,
            plan_outfit.name: plan_outfit,
            get_outfit_history.name: get_outfit_history,
            search_knowledge_base.name: search_knowledge_base,
        }
        self.tool_list = list(self.tools.values())

        # LLM
        self.llm = get_cached_provider().chat_model
        self.llm_with_tools = self.llm.bind_tools(self.tool_list)

    def _build_messages(
        self, user_message: str, images: List[str] = None
    ) -> List:
        """构建消息列表，注入上下文"""
        # 1. 当前记住的信息
        memory_text = self.memory.to_context_string()
        # 2. 缺失字段
        missing = self.memory.missing_fields
        missing_text = (
            f"\n【当前缺少的信息】需要用户提供：{', '.join(missing)}"
            if missing
            else ""
        )

        system = SYSTEM_PROMPT + f"\n\n【当前记住的信息】\n{memory_text}{missing_text}"

        messages = [SystemMessage(content=system)]

        # 3. 最近对话历史（最近 6 条）
        for msg in self.memory.recent_messages[-6:]:
            messages.append(HumanMessage(content=msg["content"]))

        # 4. 用户消息（含多模态图片）
        if images:
            content = [{"type": "text", "text": user_message}]
            for img in images:
                content.append({"type": "image_url", "image_url": img})
            messages.append(HumanMessage(content=content))
        else:
            messages.append(HumanMessage(content=user_message))

        return messages

    async def run_stream(
        self, user_message: str, images: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行主循环"""
        # 添加用户消息到记忆
        self.memory.add_message("user", user_message)

        messages = self._build_messages(user_message, images)
        yield {"type": "thinking", "content": "正在分析您的请求..."}

        response = await self.llm_with_tools.ainvoke(messages)

        max_turns = 10
        turn = 0

        while response.tool_calls and turn < max_turns:
            turn += 1

            for tc in response.tool_calls:
                tool_name = tc.name
                tool_args = tc.args

                yield {
                    "type": "tool_called",
                    "tool": tool_name,
                    "args": tool_args,
                }

                try:
                    result = await self.tools[tool_name].invoke(tool_args)
                except Exception as e:
                    result = json.dumps({
                        "error": type(e).__name__,
                        "message": str(e)
                    })

                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": result,
                }

                # 解析结果，更新 memory
                self._update_memory_from_tool_result(tool_name, result, tool_args)

                # 添加 tool 消息到列表
                messages.append(
                    ToolMessage(
                        name=tool_name,
                        content=result
                    )
                )

            # 继续 LLM 调用
            response = await self.llm_with_tools.ainvoke(messages)

        # 最终文本输出
        final_text = response.content if response.content else ""

        # 添加助手回复到记忆
        if final_text:
            self.memory.add_message("assistant", final_text)

        yield {"type": "text", "content": final_text}
        yield {"type": "done", "content": final_text}

    def _update_memory_from_tool_result(
        self, tool_name: str, result: str, args: Dict
    ) -> None:
        """从工具结果中提取信息更新 memory"""
        try:
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
        except (json.JSONDecodeError, TypeError):
            return

        if tool_name == "get_weather" and isinstance(data, dict):
            if data.get("temperature"):
                self.memory.target_temperature = float(data["temperature"])
                self.memory.missing_fields = [f for f in self.memory.missing_fields if f != "temperature"]

        elif tool_name == "plan_outfit" and isinstance(data, dict):
            # 穿搭方案已生成，清空 missing_fields
            self.memory.missing_fields = []

    def save_to_session(self, session_manager: DialogueSessionManager) -> None:
        """将 memory 写回 Session（无条件保存）"""
        if not session_manager:
            return
        session = session_manager.get(self.session_id)
        if not session:
            return

        # 更新 session context
        ctx = session.context
        if hasattr(ctx, 'target_city'):
            ctx.target_city = self.memory.target_city
        if hasattr(ctx, 'target_scene'):
            ctx.target_scene = self.memory.target_scene
        if hasattr(ctx, 'target_date'):
            ctx.target_date = self.memory.target_date
        if hasattr(ctx, 'target_temperature'):
            ctx.target_temperature = self.memory.target_temperature

        # 同步 recent_messages 到 session（转为 Message 对象）
        session.history = [
            Message(role=m["role"], content=m["content"], timestamp=m.get("timestamp", ""))
            for m in self.memory.recent_messages
        ]

        session_manager.save(session)


# ============================================================
# 旧版 Supervisor（兼容保留，供衣柜穿搭推荐使用）
# ============================================================

class Supervisor:
    """旧版 Supervisor，用于衣柜穿搭推荐（兼容保留）"""

    def __init__(self, db: Session):
        self.db = db
        self.plan_agent = PlanAgent(db)
        self.retrieval_tool = RetrievalTool(db)
        self.short_circuit_tool = ShortCircuitTool(db)
        self.combine_agent = CombineAgent(db)

    def generate_outfit(
        self,
        user_id: str,
        temperature: float,
        city: str,
        scene: str = "daily"
    ) -> Dict:
        schemes = self.plan_agent.generate_schemes(user_id, temperature, city, scene)

        all_retrieved = {}
        for scheme in schemes:
            retrieved = self.retrieval_tool.retrieve_by_scheme(user_id, scheme, temperature)
            all_retrieved[scheme["scheme_id"]] = retrieved

        perfect_scheme = self.short_circuit_tool.find_perfect_scheme(schemes, all_retrieved)

        if perfect_scheme:
            retrieved = all_retrieved[perfect_scheme["scheme_id"]]
            score = 100.0
        else:
            best_scheme = schemes[0]
            retrieved = all_retrieved[best_scheme["scheme_id"]]
            retrieved = self.combine_agent.combine_outfit(user_id, temperature, retrieved)
            score = self.short_circuit_tool.calculate_match_score(best_scheme, retrieved)
            perfect_scheme = best_scheme

        outfit_record = self._save_outfit_record(
            user_id=user_id,
            scheme_id=perfect_scheme["scheme_id"],
            temperature=temperature,
            city=city,
            retrieved=retrieved,
            scheme_description=perfect_scheme.get("description", ""),
            match_score=score
        )

        return {
            "outfit_id": outfit_record.id,
            "scheme_id": perfect_scheme["scheme_id"],
            "description": perfect_scheme.get("description", ""),
            "match_score": score,
            "temperature": temperature,
            "city": city,
            "scene": scene,
            "clothes": self._format_clothes_response(retrieved),
            "is_perfect_match": score >= 100.0
        }

    def _save_outfit_record(
        self,
        user_id: str,
        scheme_id: str,
        temperature: float,
        city: str,
        retrieved: Dict[str, Optional],
        scheme_description: str,
        match_score: float
    ) -> OutfitRecord:
        outfit = OutfitRecord(
            user_id=user_id,
            scheme_id=scheme_id,
            weather_temp=temperature,
            weather_city=city,
            top_clothes_id=retrieved.get("top").id if retrieved.get("top") else None,
            pants_clothes_id=retrieved.get("pants").id if retrieved.get("pants") else None,
            outer_clothes_id=retrieved.get("outer").id if retrieved.get("outer") else None,
            inner_clothes_id=retrieved.get("inner").id if retrieved.get("inner") else None,
            accessory_clothes_id=retrieved.get("accessory").id if retrieved.get("accessory") else None,
            scheme_description=scheme_description,
            match_score=match_score
        )
        self.db.add(outfit)
        self.db.commit()
        self.db.refresh(outfit)
        return outfit

    def _format_clothes_response(self, retrieved: Dict) -> List[Dict]:
        result = []
        for item_name, clothes in retrieved.items():
            if clothes:
                result.append({
                    "slot": item_name,
                    "clothes_id": clothes.id,
                    "image_url": clothes.image_url,
                    "category": clothes.category.value if hasattr(clothes.category, 'value') else clothes.category,
                    "color": clothes.color,
                    "description": clothes.description
                })
        return result
