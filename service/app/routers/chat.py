"""对话 API 路由"""
import json
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal, AsyncGenerator
from sqlalchemy.orm import Session

from app.database import get_db
from app.agent.dialogue_session import (
    DialogueSessionManager,
    DialogueSessionData,
    ConversationContext
)
from app.agent.graph.workflow import DialogueWorkflow
from app.agent.graph.state import GraphState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================
# 响应内容类型（可拓展）
# ============================================================

class ResponseContent(BaseModel):
    """响应内容基类"""
    type: str  # "text" / "image" / "suggestions" / "outfit_card" / "product_card"
    content: Any  # 具体内容


class TextContent(ResponseContent):
    """文本内容"""
    type: Literal["text"] = "text"
    content: str


class ImageContent(ResponseContent):
    """图片内容"""
    type: Literal["image"] = "image"
    content: Dict[str, Any]  # {"url": "...", "alt": "..."}


class SuggestionsContent(ResponseContent):
    """推荐问题内容"""
    type: Literal["suggestions"] = "suggestions"
    content: List[Dict[str, str]]  # [{"text": "...", "action": "..."}]


class OutfitCardContent(ResponseContent):
    """穿搭卡片内容"""
    type: Literal["outfit_card"] = "outfit_card"
    content: Dict[str, Any]  # 包含 outfit_plan, clothes, match_score 等


class ProductCardContent(ResponseContent):
    """商品卡片内容（预留）"""
    type: Literal["product_card"] = "product_card"
    content: Dict[str, Any]  # 包含 product_id, image_url, title, price 等


# 联合类型
ResponseContentType = Union[
    TextContent,
    ImageContent,
    SuggestionsContent,
    OutfitCardContent,
    ProductCardContent
]


# ============================================================
# 请求/响应模型
# ============================================================

class ChatMessageRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponseItem(BaseModel):
    """响应中的单个内容项"""
    type: str
    content: Any


class ChatMessageResponse(BaseModel):
    session_id: str
    message: str = ""  # 兼容旧版本
    contents: List[ChatResponseItem]  # 新版本：多种内容
    data: Optional[Dict[str, Any]] = None  # 额外数据
    suggestions: Optional[List[Dict[str, Any]]] = None  # 兼容旧版本


class SessionInfoResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    context: Dict[str, Any]


# ============================================================
# 流式 API 路由
# ============================================================

@router.post("/message/stream")
async def chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    流式对话响应

    使用 text/event-stream 格式返回每个阶段的思考过程
    event_type: thinking, tool_call, tool_result, text, outfit_card, suggestions, done, error
    """
    done_sent = False  # 跟踪是否已发送 done 事件

    async def event_generator():
        nonlocal done_sent
        session_mgr = None

        try:
            # 创建 Session 管理器
            session_mgr = DialogueSessionManager(db)

            # 获取或创建 session
            session = session_mgr.get_or_create(
                session_id=request.session_id,
                user_id=request.user_id
            )

            def _do_save(state: GraphState) -> bool:
                """统一保存 session 上下文到 DB。返回是否成功。"""
                try:
                    # 保存上下文（只保存有值的字段）
                    if state.get("target_city"):
                        _update_context(session, {"target_city": state["target_city"]})
                        logger.info(f"[stream._do_save] 保存 target_city={state['target_city']}")
                    if state.get("target_scene"):
                        _update_context(session, {"target_scene": state["target_scene"]})
                        logger.info(f"[stream._do_save] 保存 target_scene={state['target_scene']}")
                    if state.get("target_temperature"):
                        _update_context(session, {"target_temperature": state["target_temperature"]})
                    if state.get("target_date"):
                        _update_context(session, {"target_date": state["target_date"]})
                    if state.get("asking_for"):
                        _update_context(session, {"asking_for": state["asking_for"]})
                    if state.get("pending_intent"):
                        _update_context(session, {"pending_intent": state["pending_intent"]})
                    if state.get("outfit_plan"):
                        _update_context(session, {"current_outfit": state["outfit_plan"]})

                    # 添加助手回复到历史
                    response_text = _get_text_message(state)
                    _add_message(session, "assistant", response_text)

                    # 写入 DB
                    session_mgr.save(session)

                    # 验证读回（确保真的写进去了）
                    saved_session = session_mgr.get(session.session_id)
                    if saved_session:
                        logger.info(f"[stream._do_save] 验证读回 | ctx.city={saved_session.context.target_city} ctx.scene={saved_session.context.target_scene} ctx.asking_for={saved_session.context.asking_for}")
                    else:
                        logger.warning(f"[stream._do_save] 验证读回失败，session不存在: {session.session_id}")

                    return True
                except Exception as e:
                    logger.error(f"[stream._do_save] 保存失败: {e}", exc_info=True)
                    return False

            # 添加用户消息到历史
            _add_message(session, "user", request.message)

            # 更新上下文
            if request.context:
                _update_context(session, request.context)

            # 加载用户画像（供 LLM 使用）
            user_profile = _load_user_profile(db, request.user_id)

            # 构建初始状态
            context = _get_context_dict(session)
            context.update(user_profile)  # 画像数据合并到 context

            # 近 2 轮对话摘要（给 intent_node 的 LLM 看）
            recent_msgs = session.history[-4:]  # 最多 4 条 = 最近 2 轮
            recent_summary = "\n".join([f"用户：{m.content}" if m.role == "user" else f"助手：{m.content}" for m in recent_msgs])
            if recent_summary:
                context["recent_conversation"] = recent_summary

            initial_state: GraphState = {
                "user_id": request.user_id,
                "session_id": session.session_id,
                "messages": [{"role": "user", "content": request.message}],
                "context": context,
                "intent": None,
                "intent_str": None,
                "entities": {},
                "intent_confidence": 0.0,
                "target_date": session.context.target_date,
                "target_city": session.context.target_city,
                "target_scene": session.context.target_scene,
                "target_temperature": session.context.target_temperature,
                "user_clothes": [],
                "filtered_clothes": {},
                "selected_clothes": {},
                "wardrobe_stats": None,
                "available_categories": [],
                "missing_categories": [],
                "wardrobe_by_category": {},
                "outfit_plan": None,
                "match_score": 0.0,
                "alternatives": [],
                "feedback_type": None,
                "adjustment_history": [],
                "next_node": None,
                "error": None,
                "should_end": False,
                "asking_for": session.context.asking_for,
                "pending_intent": session.context.pending_intent
            }

            # 运行工作流（流式）
            workflow = DialogueWorkflow(db)

            # 节点名称映射
            node_names = {
                "intent": "意图识别",
                "weather": "天气查询",
                "wardrobe_query": "衣柜检索",
                "outfit_planning": "穿搭规划",
                "clothes_retrieval": "衣物匹配",
                "outfit_evaluation": "方案评估",
                "feedback": "反馈处理",
                "response": "生成回复",
                "generate_outfit": "穿搭生成"
            }

            accumulated_text = ""
            final_state: GraphState = {}

            # 累积完整 state（astream 返回 {"node_name": partial_update}）
            accumulated: GraphState = dict(initial_state)

            async for raw_state in workflow.run_stream(initial_state):
                logger.info(f"[stream.yield] raw_type={type(raw_state).__name__} raw_keys={list(raw_state.keys()) if isinstance(raw_state, dict) else raw_state}")
                # 解析 astream 输出格式：{"node_name": partial_update_dict}
                if isinstance(raw_state, dict) and len(raw_state) == 1:
                    node_key = list(raw_state.keys())[0]
                    partial = list(raw_state.values())[0]
                    if isinstance(partial, dict):
                        accumulated.update(partial)
                        logger.info(f"[stream.yield] parsed node={node_key} should_end={accumulated.get('should_end')} msgs={len(accumulated.get('messages', []))}")
                    else:
                        logger.info(f"[stream.yield] parsed node={node_key} but partial is not dict: {type(partial)}")
                else:
                    accumulated.update(raw_state if isinstance(raw_state, dict) else {})
                    logger.info(f"[stream.yield] parsed multi-key/batch msgs={len(accumulated.get('messages', []))}")

                state: GraphState = accumulated
                next_node_val = state.get("next_node")
                intent_val = state.get("intent")
                raw_node = next_node_val if next_node_val is not None else intent_val

                # 正确处理 Intent 枚举（继承自 str）：优先用 .value 转为纯字符串
                if hasattr(raw_node, "value"):
                    current_node = raw_node.value
                elif isinstance(raw_node, str) and raw_node not in ("True", "False"):
                    current_node = raw_node
                else:
                    current_node = None

                # 发送思考过程
                if current_node:
                    node_name = node_names.get(current_node, current_node)
                    thinking_text = _get_thinking_text(state, current_node)
                    if thinking_text:
                        yield _sse_event("thinking", {
                            "node": current_node,
                            "node_name": node_name,
                            "text": thinking_text
                        })

                # 发送工具调用信息
                tool_result = state.get("context", {}).get("last_tool_call")
                if tool_result:
                    yield _sse_event("tool_result", tool_result)

                # 发送文本片段
                messages = state.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if last_msg.get("role") == "assistant":
                        new_text = last_msg.get("content", "")
                        logger.info(f"[stream] text检查 | new_text_len={len(new_text)} acc={len(accumulated_text)}")
                        if new_text and new_text != accumulated_text:
                            # 只发送新增的部分
                            delta = new_text[len(accumulated_text):]
                            logger.info(f"[stream] yield text | delta_len={len(delta)}")
                            if delta:
                                yield _sse_event("text", delta)
                                accumulated_text = new_text

                # 发送穿搭卡片
                outfit_plan = state.get("outfit_plan")
                selected_clothes = state.get("selected_clothes", {})
                if outfit_plan and selected_clothes and any(selected_clothes.values()) and state.get("should_end"):
                    card_content = {
                        "plan": outfit_plan,
                        "clothes": selected_clothes,
                        "match_score": state.get("match_score", 0),
                        "scene": state.get("target_scene"),
                        "temperature": state.get("target_temperature"),
                        "city": state.get("target_city")
                    }
                    yield _sse_event("outfit_card", card_content)

                    # 发送建议
                    suggestions = _generate_suggestions(state)
                    if suggestions:
                        yield _sse_event("suggestions", suggestions)

                # 检查是否结束
                logger.info(f"[stream] should_end={state.get('should_end')} next_node={state.get('next_node')}")
                # 标记本轮已处理的最终 state（用于最后统一保存）
                final_state = state
                if state.get("should_end"):
                    logger.info(f"[stream] should_end=True，标记完成")
                    # 不 break！继续处理后续 yield，确保所有内容发送给客户端
                    # 保存逻辑移到 finally

        except asyncio.CancelledError:
            logger.info("[stream] CancelledError")
            # 也要保存，防止数据丢失
            if not done_sent:
                _do_save(final_state)
        except Exception as e:
            logger.info(f"[stream] Exception: {e}")
            # 先保存，再发错误事件
            if not done_sent:
                success = _do_save(final_state)
                done_sent = True
            try:
                yield _sse_event("error", {"message": str(e)})
            except Exception:
                pass
        finally:
            if not done_sent:
                success = _do_save(final_state)
                done_sent = True
                if success:
                    yield _sse_event("done", {"session_id": session.session_id})
                else:
                    logger.error("[stream.finally] 保存失败，不发送done事件")
            else:
                logger.info(f"[stream.finally] done_sent={done_sent}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def _sse_event(event_type: str, data: Any) -> str:
    """构建 SSE 事件"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _get_thinking_text(state: GraphState, node: str) -> str:
    """获取节点的思考描述"""
    thinking_map = {
        "intent": "正在理解您的需求...",
        "weather": "正在查询目标天气...",
        "wardrobe_query": "正在检索您的衣柜...",
        "outfit_planning": "正在为您设计穿搭方案...",
        "clothes_retrieval": "正在匹配您的衣物...",
        "outfit_evaluation": "正在评估穿搭效果...",
        "feedback": "正在处理您的反馈...",
        "response": "正在生成回复...",
        "generate_outfit": "正在生成穿搭方案..."
    }

    # 根据实际状态返回更详细的描述
    if node == "weather" and state.get("target_city"):
        return f"正在查询 {state.get('target_city')} 的天气..."
    if node == "wardrobe_query":
        user_clothes = state.get("user_clothes", [])
        return f"正在检索您的衣柜，找到 {len(user_clothes)} 件衣物..."
    if node == "outfit_planning":
        target_scene = state.get("target_scene") or "日常"
        return f"正在为 {target_scene} 场景设计穿搭..."
    if node == "outfit_evaluation":
        score = state.get("match_score", 0)
        return f"当前匹配度 {score}%，正在评估..."

    # 过滤无效 node（防止 state dict 混入）
    if not isinstance(node, str) or len(node) > 30 or "{" in node:
        return None

    return thinking_map.get(node, f"正在{node}...")


# ============================================================
# API 路由
# ============================================================

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    处理用户对话消息

    支持多轮对话，session_id 相同则继承上下文
    Session TTL: 3 天
    """
    # 创建 Session 管理器
    session_mgr = DialogueSessionManager(db)

    # 获取或创建 session
    session = session_mgr.get_or_create(
        session_id=request.session_id,
        user_id=request.user_id
    )

    # 添加用户消息到历史
    _add_message(session, "user", request.message)

    # 更新上下文
    if request.context:
        _update_context(session, request.context)

    # 加载用户画像（供 LLM 使用）
    user_profile = _load_user_profile(db, request.user_id)
    context = _get_context_dict(session)
    context.update(user_profile)

    # 构建初始状态
    initial_state: GraphState = {
        "user_id": request.user_id,
        "session_id": session.session_id,
        "messages": [{"role": "user", "content": request.message}],
        "context": context,
        "intent": None,
        "intent_str": None,
        "entities": {},
        "intent_confidence": 0.0,
        "target_date": session.context.target_date,
        "target_city": session.context.target_city,
        "target_scene": session.context.target_scene,
        "target_temperature": session.context.target_temperature,
        "user_clothes": [],
        "filtered_clothes": {},
        "selected_clothes": {},
        "wardrobe_stats": None,
        "available_categories": [],
        "missing_categories": [],
        "wardrobe_by_category": {},
        "outfit_plan": None,
        "match_score": 0.0,
        "alternatives": [],
        "feedback_type": None,
        "adjustment_history": [],
        "next_node": None,
        "error": None,
        "should_end": False,
        "asking_for": session.context.asking_for,
        "pending_intent": session.context.pending_intent
    }

    try:
        # 运行工作流
        workflow = DialogueWorkflow(db)
        result = await workflow.run(initial_state)

        # 构建响应内容
        contents = _build_response_contents(result)

        # 获取文本消息（用于兼容旧版本）
        response_message = _get_text_message(result)

        # 即使是追问回复，也要保存当前已有的信息到 session context
        # 这样下一轮对话时可以继承这些信息
        if result.get("outfit_plan"):
            _update_context(session, {"current_outfit": result.get("outfit_plan")})
        if result.get("target_scene"):
            _update_context(session, {"target_scene": result.get("target_scene")})
        if result.get("target_temperature"):
            _update_context(session, {"target_temperature": result.get("target_temperature")})
        if result.get("target_date"):
            _update_context(session, {"target_date": result.get("target_date")})
        if result.get("target_city"):
            _update_context(session, {"target_city": result.get("target_city")})
        elif result.get("entities", {}).get("city"):
            _update_context(session, {"target_city": result.get("entities", {}).get("city")})
        # 保存追问状态
        if result.get("asking_for"):
            _update_context(session, {"asking_for": result.get("asking_for")})
        else:
            _update_context(session, {"asking_for": None})
        if result.get("pending_intent"):
            _update_context(session, {"pending_intent": result.get("pending_intent")})
        else:
            _update_context(session, {"pending_intent": None})

        # 添加助手消息到历史
        _add_message(session, "assistant", response_message)

        # 保存 session
        session_mgr.save(session)

        return ChatMessageResponse(
            session_id=session.session_id,
            message=response_message,
            contents=contents,
            data=result.get("response_data"),
            suggestions=_generate_suggestions(result)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取 session 状态"""
    session_mgr = DialogueSessionManager(db)
    session = session_mgr.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在或已过期")

    return SessionInfoResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at.isoformat(),
        last_active=session.last_active.isoformat(),
        context=_get_context_dict(session)
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除 session"""
    session_mgr = DialogueSessionManager(db)
    success = session_mgr.delete(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session 不存在")
    return {"message": "Session 已删除"}


@router.post("/session/{session_id}/clear")
async def clear_session_context(session_id: str, db: Session = Depends(get_db)):
    """清除 session 上下文（保留历史）"""
    session_mgr = DialogueSessionManager(db)
    session = session_mgr.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在或已过期")

    # 重置上下文
    session.context = ConversationContext()
    session_mgr.save(session)

    return {"message": "上下文已清除"}


# ============================================================
# 辅助函数
# ============================================================

def _load_user_profile(db: Session, user_id: str) -> Dict[str, Any]:
    """从数据库加载用户画像数据，供 LLM 使用"""
    from app.models import UserProfile
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile:
        return {}

    return {
        "user_gender": profile.gender,  # "男" / "女" / None
        "user_style": profile.style_preferences,  # 如 "休闲、简约" / None
        "user_season": profile.season_preference,  # 如 "春秋" / None
        "user_default_occasion": profile.default_occasion,  # 如 "casual" / None
    }


def _add_message(session: DialogueSessionData, role: str, content: str) -> None:
    """添加消息到 session 历史"""
    from datetime import datetime
    session.history.append(type("Message", (), {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })())


def _update_context(session: DialogueSessionData, updates: Dict[str, Any]) -> None:
    """更新上下文"""
    ctx = session.context
    if "target_date" in updates:
        ctx.target_date = updates["target_date"]
    if "target_city" in updates:
        ctx.target_city = updates["target_city"]
    if "target_scene" in updates:
        ctx.target_scene = updates["target_scene"]
    if "target_temperature" in updates:
        ctx.target_temperature = updates["target_temperature"]
    if "current_outfit" in updates:
        ctx.current_outfit = updates["current_outfit"]
    if "asking_for" in updates:
        ctx.asking_for = updates["asking_for"]
    if "pending_intent" in updates:
        ctx.pending_intent = updates["pending_intent"]


def _get_context_dict(session: DialogueSessionData) -> Dict[str, Any]:
    """获取上下文字典"""
    ctx_dict = session.context.to_dict()
    logger.info(f"[session] context恢复 | target_city={ctx_dict.get('target_city')} target_scene={ctx_dict.get('target_scene')} asking_for={ctx_dict.get('asking_for')} pending_intent={ctx_dict.get('pending_intent')}")
    # 确保所有字段都有值（避免 None 值导致字段丢失）
    ctx_dict.setdefault("asking_for", None)
    ctx_dict.setdefault("pending_intent", None)
    return ctx_dict


def _get_text_message(result: GraphState) -> str:
    """从结果中提取文本消息"""
    if result.get("messages"):
        for msg in reversed(result["messages"]):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
    return ""


def _build_response_contents(result: GraphState) -> List[ChatResponseItem]:
    """
    构建响应内容列表（支持多种格式）

    当前支持：
    - text: 文本消息
    - outfit_card: 穿搭卡片
    - suggestions: 推荐问题
    """
    contents = []
    intent = result.get("intent")
    outfit_plan = result.get("outfit_plan")
    selected_clothes = result.get("selected_clothes", {})
    match_score = result.get("match_score", 0)

    # 1. 文本内容
    text_msg = _get_text_message(result)
    if text_msg:
        contents.append(ChatResponseItem(type="text", content=text_msg))

    # 2. 穿搭卡片（如果有穿搭方案且有衣物）
    if outfit_plan and selected_clothes and any(selected_clothes.values()):
        card_content = {
            "plan": outfit_plan,
            "clothes": selected_clothes,
            "match_score": match_score,
            "scene": result.get("target_scene"),
            "temperature": result.get("target_temperature"),
            "city": result.get("target_city")
        }
        contents.append(ChatResponseItem(type="outfit_card", content=card_content))

    # 3. 推荐问题
    suggestions = _generate_suggestions(result)
    if suggestions:
        contents.append(ChatResponseItem(type="suggestions", content=suggestions))

    return contents


def _generate_suggestions(result: GraphState) -> List[Dict[str, Any]]:
    """生成建议列表"""
    suggestions = []
    intent = result.get("intent")

    if intent == "generate_outfit":
        suggestions.append({
            "type": "action",
            "text": "换个更休闲的版本",
            "action": "换个休闲点的风格"
        })
        suggestions.append({
            "type": "action",
            "text": "换个更正式的版本",
            "action": "换个正式点的风格"
        })

    if result.get("match_score", 0) < 80:
        suggestions.append({
            "type": "action",
            "text": "这套不太合适",
            "action": "不太满意，换一套"
        })

    return suggestions
