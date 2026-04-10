"""对话 API 路由（简化版）

使用新的 Agent + Memory 架构。
保留旧版端点以兼容，逐步迁移。
"""
import json
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
from sqlalchemy.orm import Session

from app.database import get_db
from app.agent.core import chat_message as agent_chat_message, get_agent
from app.agent.memory import get_session_memory, update_session_memory, clear_session_memory
from app.agent.prompts.system import get_system_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================
# 响应内容类型
# ============================================================

class ResponseContent(BaseModel):
    type: str  # "text" / "image" / "suggestions" / "outfit_card"
    content: Any


class TextContent(ResponseContent):
    type: Literal["text"] = "text"
    content: str


class OutfitCardContent(ResponseContent):
    type: Literal["outfit_card"] = "outfit_card"
    content: Dict[str, Any]


# ============================================================
# 请求/响应模型
# ============================================================

class ChatMessageRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str
    context: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None


class ChatResponseItem(BaseModel):
    type: str
    content: Any


class ChatMessageResponse(BaseModel):
    session_id: str
    message: str = ""
    contents: List[ChatResponseItem]
    data: Optional[Dict[str, Any]] = None


class SessionInfoResponse(BaseModel):
    session_id: str
    user_id: str
    context: Dict[str, Any]


# ============================================================
# 新版对话 API（使用简化 Agent）
# ============================================================

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    处理用户对话消息（简化版 Agent）

    使用新的 Agent + Memory 架构。
    支持：
    - 多轮对话（session_id 相同则继承上下文）
    - 图片分析（识别单件衣物或整套穿搭）
    - 穿搭推荐（基于衣柜 + 天气 + 场合）
    - 风格推荐（预设风格 + 用户自定义）
    """
    # 确保有 session_id
    session_id = request.session_id
    if not session_id:
        session_id = f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    try:
        # 获取/更新短期记忆
        memory_data = await get_session_memory(session_id)
        context = memory_data.context if hasattr(memory_data, 'context') else {}

        # 如果有 context 更新
        if request.context:
            context.update(request.context)

        # 调用 Agent
        result = await agent_chat_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            images=request.images
        )

        response_text = result.get("response", "")
        if isinstance(response_text, str):
            pass
        else:
            response_text = str(response_text)

        return ChatMessageResponse(
            session_id=session_id,
            message=response_text,
            contents=[ChatResponseItem(type="text", content=response_text)],
            data=result.get("context")
        )

    except Exception as e:
        logger.error(f"[chat] Exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


# ============================================================
# 新版流式对话 API
# ============================================================

@router.post("/message/stream")
async def chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    流式对话响应（简化版 Agent + SSE）

    event_type: text, tool_call, done, error
    """
    session_id = request.session_id
    if not session_id:
        session_id = f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    async def event_generator():
        try:
            # 获取/更新短期记忆
            memory_data = await get_session_memory(session_id)
            context = memory_data.context if hasattr(memory_data, 'context') else {}

            if request.context:
                context.update(request.context)

            # 获取 Agent
            agent = get_agent()

            # 构建消息
            content = request.message
            if request.images:
                content_parts = [{"type": "text", "text": request.message}]
                for img in request.images:
                    content_parts.append({"type": "image_url", "image_url": {"url": img}})

                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=content_parts)]
            else:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=request.message)]

            # 流式执行
            accumulated = ""
            async for chunk in agent.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    accumulated += chunk.content
                    yield f"event: text\ndata: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"

            yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'content': accumulated}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[stream] Exception: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

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
# Session 管理
# ============================================================

@router.get("/session/{session_id}", response_model=SessionInfoResponse)
async def get_session(session_id: str):
    """获取 session 状态"""
    memory_data = await get_session_memory(session_id)

    if not memory_data or not memory_data.user_id:
        raise HTTPException(status_code=404, detail="Session 不存在或已过期")

    context = memory_data.context if hasattr(memory_data, 'context') else {}
    if hasattr(context, 'to_dict'):
        context = context.to_dict()

    return SessionInfoResponse(
        session_id=session_id,
        user_id=memory_data.user_id,
        context=context
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除 session"""
    success = await clear_session_memory(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session 不存在")
    return {"message": "Session 已删除"}


@router.post("/session/{session_id}/close")
async def close_session(session_id: str):
    """
    关闭 session（前端应用关闭时调用）

    标记 session 为关闭状态，下次打开应用会创建新 session。
    """
    await clear_session_memory(session_id)
    return {"message": "Session 已关闭"}


@router.post("/session/{session_id}/clear")
async def clear_session_context(session_id: str):
    """清除 session 上下文（保留历史）"""
    await update_session_memory(session_id, context={})
    return {"message": "上下文已清除"}
