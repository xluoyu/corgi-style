"""对话 Session 管理（分层存储）

- 短期记忆：PostgreSQL conversation_sessions 表，TTL 3 天
- 长期记忆：PostgreSQL users, clothing_items, outfit_histories 表（已有）
"""
import json
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Session as DBSession

from app.database import Base


def _safe_jsonSerialize(obj: Any) -> Any:
    """
    安全序列化对象，处理无法直接 JSON 序列化的类型
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _safe_jsonSerialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_jsonSerialize(item) for item in obj]
    elif isinstance(obj, set):
        return [_safe_jsonSerialize(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # 处理对象类型
        return _safe_jsonSerialize(obj.__dict__)
    else:
        return obj


# ============================================================
# SQLAlchemy 模型
# ============================================================

class ConversationSessionModel(Base):
    """Session 数据库模型"""
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_data = Column(JSONB, nullable=False, default=dict)
    messages = Column(JSONB, nullable=False, default=list)
    context = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_active_at = Column(DateTime, nullable=False, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)


# ============================================================
# 数据类
# ============================================================

@dataclass
class Message:
    """对话消息"""
    role: str           # "user" / "assistant" / "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationContext:
    """对话上下文（跨轮次保持）"""
    target_date: Optional[str] = None
    target_city: Optional[str] = None
    target_scene: Optional[str] = None
    target_temperature: Optional[float] = None
    current_outfit: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        if data is None:
            return cls()
        return cls(
            target_date=data.get("target_date"),
            target_city=data.get("target_city"),
            target_scene=data.get("target_scene"),
            target_temperature=data.get("target_temperature"),
            current_outfit=data.get("current_outfit"),
        )


@dataclass
class DialogueSessionData:
    """Session 内存数据结构"""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    context: ConversationContext
    history: List[Message]

    def to_db_dict(self) -> Dict[str, Any]:
        """转为数据库存储格式"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "context": self.context.to_dict(),
            "history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.history
            ]
        }

    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> "DialogueSessionData":
        """从数据库数据恢复"""
        history = [
            Message(role=m["role"], content=m["content"], timestamp=m.get("timestamp", ""))
            for m in data.get("history", [])
        ]
        context = ConversationContext.from_dict(data.get("context", {}))

        # 确保 created_at 和 last_active 是 datetime 对象
        created_at_val = data.get("created_at", datetime.now())
        last_active_val = data.get("last_active", datetime.now())

        if isinstance(created_at_val, str):
            created_at_dt = datetime.fromisoformat(created_at_val)
        elif isinstance(created_at_val, datetime):
            created_at_dt = created_at_val
        else:
            created_at_dt = datetime.now()

        if isinstance(last_active_val, str):
            last_active_dt = datetime.fromisoformat(last_active_val)
        elif isinstance(last_active_val, datetime):
            last_active_dt = last_active_val
        else:
            last_active_dt = datetime.now()

        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=created_at_dt,
            last_active=last_active_dt,
            context=context,
            history=history
        )


# ============================================================
# Session 管理器（PostgreSQL 持久化 + 内存缓存）
# ============================================================

class DialogueSessionManager:
    """
    Session 管理器

    分层存储：
    - 内存缓存：最新访问的 Session（速度快）
    - PostgreSQL：持久化存储（重启不丢失，3 天 TTL）
    """

    # TTL: 3 天
    TTL_DAYS = 3
    TTL_SECONDS = TTL_DAYS * 24 * 60 * 60

    def __init__(self, db: DBSession):
        self.db = db
        # 内存缓存: session_id -> DialogueSessionData
        self._cache: Dict[str, DialogueSessionData] = {}
        # 缓存过期时间: session_id -> expires_at
        self._cache_expires: Dict[str, datetime] = {}

    def _is_cache_valid(self, session_id: str) -> bool:
        """检查缓存是否有效"""
        if session_id not in self._cache:
            return False
        if session_id not in self._cache_expires:
            return False
        return datetime.now() < self._cache_expires[session_id]

    def _cache_session(self, session: DialogueSessionData) -> None:
        """缓存 Session"""
        self._cache[session.session_id] = session
        self._cache_expires[session.session_id] = datetime.now() + timedelta(days=self.TTL_DAYS)

    def _remove_from_cache(self, session_id: str) -> None:
        """从缓存移除"""
        self._cache.pop(session_id, None)
        self._cache_expires.pop(session_id, None)

    def get_or_create(
        self,
        session_id: Optional[str],
        user_id: str
    ) -> DialogueSessionData:
        """
        获取或创建 Session

        Args:
            session_id: 传入的 session_id，为空则创建新的
            user_id: 用户 ID

        Returns:
            DialogueSessionData
        """
        # 尝试从缓存获取
        if session_id and self._is_cache_valid(session_id):
            return self._cache[session_id]

        # 尝试从数据库获取
        if session_id:
            db_session = self._load_from_db(session_id)
            if db_session:
                self._cache_session(db_session)
                return db_session

        # 创建新的 Session
        new_session = self._create_new(user_id)
        self._save_to_db(new_session)
        self._cache_session(new_session)
        return new_session

    def get(self, session_id: str) -> Optional[DialogueSessionData]:
        """获取指定 Session"""
        if self._is_cache_valid(session_id):
            return self._cache[session_id]

        db_session = self._load_from_db(session_id)
        if db_session:
            self._cache_session(db_session)
        return db_session

    def save(self, session: DialogueSessionData) -> None:
        """保存 Session 到数据库"""
        session.last_active = datetime.now()
        self._save_to_db(session)
        self._cache_session(session)

    def delete(self, session_id: str) -> bool:
        """删除 Session"""
        # 从数据库删除
        self._delete_from_db(session_id)
        # 从缓存移除
        self._remove_from_cache(session_id)
        return True

    def clear_expired(self) -> int:
        """清理过期 Session"""
        now = datetime.now()
        expired_count = 0

        # 清理数据库
        self.db.query(ConversationSessionModel).filter(
            ConversationSessionModel.expires_at < now
        ).delete()

        # 清理缓存
        expired_ids = [
            sid for sid, exp in self._cache_expires.items()
            if now >= exp
        ]
        for sid in expired_ids:
            self._remove_from_cache(sid)
            expired_count += 1

        self.db.commit()
        return expired_count

    def _create_new(self, user_id: str) -> DialogueSessionData:
        """创建新的 Session 内存数据"""
        now = datetime.now()
        return DialogueSessionData(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            last_active=now,
            context=ConversationContext(),
            history=[]
        )

    def _load_from_db(self, session_id: str) -> Optional[DialogueSessionData]:
        """从数据库加载 Session"""
        row = self.db.query(ConversationSessionModel).filter(
            ConversationSessionModel.id == session_id,
            ConversationSessionModel.expires_at > datetime.now()
        ).first()

        if not row:
            return None

        try:
            # 处理 created_at 和 last_active，确保是字符串格式
            created_at_val = row.created_at
            last_active_val = row.last_active

            # 如果是 datetime 对象，转换为 ISO 格式字符串
            if isinstance(created_at_val, datetime):
                created_at_str = created_at_val.isoformat()
            else:
                created_at_str = str(created_at_val) if created_at_val else datetime.now().isoformat()

            if isinstance(last_active_val, datetime):
                last_active_str = last_active_val.isoformat()
            else:
                last_active_str = str(last_active_val) if last_active_val else datetime.now().isoformat()

            data = {
                "session_id": str(row.id),
                "user_id": str(row.user_id),
                "created_at": created_at_str,
                "last_active": last_active_str,
                "context": row.context or {},
                "history": row.messages or []
            }
            return DialogueSessionData.from_db_dict(data)
        except Exception:
            return None

    def _save_to_db(self, session: DialogueSessionData) -> None:
        """保存 Session 到数据库"""
        expires_at = datetime.now() + timedelta(days=self.TTL_DAYS)

        # 查找已存在的记录
        existing = self.db.query(ConversationSessionModel).filter(
            ConversationSessionModel.id == session.session_id
        ).first()

        # 确保所有 datetime 字段都是字符串
        messages_data = [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp if isinstance(m.timestamp, str) else str(m.timestamp)}
            for m in session.history
        ]

        # 使用安全序列化处理所有可能包含复杂对象的数据
        session_data = _safe_jsonSerialize(session.to_db_dict())
        context_data = _safe_jsonSerialize(session.context.to_dict())

        db_data = {
            "session_data": session_data,
            "messages": messages_data,
            "context": context_data,
            "last_active_at": session.last_active.isoformat() if isinstance(session.last_active, datetime) else session.last_active,
            "expires_at": expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at
        }

        if existing:
            existing.session_data = db_data
            existing.messages = db_data["messages"]
            existing.context = db_data["context"]
            existing.last_active_at = datetime.fromisoformat(db_data["last_active_at"]) if isinstance(db_data["last_active_at"], str) else db_data["last_active_at"]
            existing.expires_at = datetime.fromisoformat(db_data["expires_at"]) if isinstance(db_data["expires_at"], str) else db_data["expires_at"]
        else:
            new_row = ConversationSessionModel(
                id=session.session_id,
                user_id=session.user_id,
                session_data=db_data,
                messages=db_data["messages"],
                context=db_data["context"],
                created_at=session.created_at if isinstance(session.created_at, datetime) else datetime.fromisoformat(session.created_at),
                last_active_at=datetime.fromisoformat(db_data["last_active_at"]) if isinstance(db_data["last_active_at"], str) else db_data["last_active_at"],
                expires_at=datetime.fromisoformat(db_data["expires_at"]) if isinstance(db_data["expires_at"], str) else db_data["expires_at"]
            )
            self.db.add(new_row)

        self.db.commit()

    def _delete_from_db(self, session_id: str) -> None:
        """从数据库删除 Session"""
        self.db.query(ConversationSessionModel).filter(
            ConversationSessionModel.id == session_id
        ).delete()
        self.db.commit()


# ============================================================
# 便捷函数（用于 FastAPI Dependency Injection）
# ============================================================

def create_session_manager(db: DBSession) -> DialogueSessionManager:
    """创建 Session 管理器"""
    return DialogueSessionManager(db)
