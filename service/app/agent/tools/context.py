"""ContextVar DB 注入 — 解决 Tool 无法通过参数注入 DB session 的问题。

在 FastAPI 路由中（如 chat_message_stream），通过 set_tool_context() 设置上下文，
之后在任意 Tool 内部通过 get_db_for_tools() / get_current_user_id() 获取 DB 和用户。
"""
from contextvars import ContextVar
from sqlalchemy.orm import Session

_db_session: ContextVar[Session] = ContextVar("db_session")
_user_id: ContextVar[str] = ContextVar("user_id")


def get_db_for_tools() -> Session:
    """获取当前请求上下文的 DB session。必须在 set_tool_context 之后调用。"""
    return _db_session.get()


def get_current_user_id() -> str:
    """获取当前请求上下文的用户 ID。必须在 set_tool_context 之后调用。"""
    return _user_id.get()


def set_tool_context(db: Session, user_id: str) -> None:
    """在请求入口设置 DB session 和 user_id 到上下文变量。"""
    _db_session.set(db)
    _user_id.set(user_id)
