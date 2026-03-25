"""对话 API 路由"""
import json
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from sqlalchemy.orm import Session

from app.database import get_db
from app.agent.dialogue_session import (
    DialogueSessionManager,
    DialogueSessionData,
    ConversationContext
)
from app.agent.supervisor import SupervisorAgent
from app.agent.tools.context import set_tool_context

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
    images: Optional[List[str]] = None  # OSS 图片 URL 列表


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
# 流式 API 路由（新版：SupervisorAgent + Function Calling）
# ============================================================

@router.post("/message/stream")
async def chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    流式对话响应（新版：SupervisorAgent + Function Calling）

    event_type: thinking, tool_call, tool_result, text, done, error
    """
    done_sent = False

    async def event_generator():
        nonlocal done_sent
        agent = None
        session = None
        session_mgr = None

        try:
            # 设置工具上下文（ContextVar）
            set_tool_context(db, request.user_id)

            # Session 管理
            session_mgr = DialogueSessionManager(db)
            session = session_mgr.get_or_create(
                session_id=request.session_id,
                user_id=request.user_id
            )

            # 添加用户消息到历史
            _add_message(session, "user", request.message)

            # 创建 SupervisorAgent
            agent = SupervisorAgent(
                session_id=session.session_id,
                user_id=request.user_id,
                session_manager=session_mgr,
                db=db
            )

            # 流式执行
            async for event in agent.run_stream(request.message, request.images):
                yield _sse_event(event["type"], event)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[stream] Exception: {e}", exc_info=True)
            yield _sse_event("error", {"message": str(e)})
        finally:
            # 无条件保存到 Session
            if agent is not None and session_mgr is not None:
                try:
                    agent.save_to_session(session_mgr)
                    logger.info(f"[stream.finally] Session 保存成功: {session.session_id}")
                except Exception as e:
                    logger.error(f"[stream.finally] 保存失败: {e}")
            if not done_sent:
                done_sent = True
                if session is not None:
                    yield _sse_event("done", {"session_id": session.session_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================
# API 路由（保留旧版 LangGraph workflow，可选废弃）
# ============================================================

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    处理用户对话消息（非流式，保留兼容）

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

    # 构建初始状态（兼容旧 LangGraph workflow）
    initial_state = {
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
        # 运行工作流（使用新版 SupervisorAgent）
        set_tool_context(db, request.user_id)
        session_mgr_local = DialogueSessionManager(db)
        agent = SupervisorAgent(
            session_id=session.session_id,
            user_id=request.user_id,
            session_manager=session_mgr_local,
            db=db
        )

        # 收集所有输出
        final_text = ""
        async for event in agent.run_stream(request.message, request.images):
            if event["type"] == "done":
                final_text = event["content"]
                break
            elif event["type"] == "text":
                final_text = event["content"]

        # 保存到 session
        agent.save_to_session(session_mgr_local)

        return ChatMessageResponse(
            session_id=session.session_id,
            message=final_text,
            contents=[ChatResponseItem(type="text", content=final_text)],
            data=None,
            suggestions=None
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

def _sse_event(event_type: str, data: Any) -> str:
    """构建 SSE 事件"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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


def _generate_suggestions(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """生成建议列表"""
    suggestions = []
    intent = state.get("intent")

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

    if state.get("match_score", 0) < 80:
        suggestions.append({
            "type": "action",
            "text": "这套不太合适",
            "action": "不太满意，换一套"
        })

    return suggestions
