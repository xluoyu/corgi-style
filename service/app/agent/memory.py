"""对话记忆管理 - Redis/Upstash 短期记忆"""
import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Message:
    """对话消息"""
    role: str  # "user" / "assistant" / "system"
    content: str
    timestamp: str = ""
    images: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "images": self.images
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            images=data.get("images", [])
        )


@dataclass
class ConversationContext:
    """对话上下文（短期记忆）"""
    date: Optional[str] = None  # 日期：今天、明天、后天
    location: Optional[str] = None  # 地点/城市
    occasion: Optional[str] = None  # 场合：daily/work/date/party
    style: Optional[str] = None  # 风格偏好
    temperature: Optional[float] = None  # 温度

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        return cls(
            date=data.get("date"),
            location=data.get("location"),
            occasion=data.get("occasion"),
            style=data.get("style"),
            temperature=data.get("temperature")
        )


@dataclass
class SessionData:
    """会话数据"""
    session_id: str
    user_id: str
    context: ConversationContext = field(default_factory=ConversationContext)
    pending_image: Optional[str] = None  # 待处理的单件衣物图片 URL
    image_attrs: Optional[Dict[str, Any]] = None  # 已分析的单件衣物属性
    pending_outfit_image: Optional[str] = None  # 待处理的整套穿搭图片 URL
    outfit_analysis: Optional[Dict[str, Any]] = None  # 已分析的整套穿搭结果
    last_update: str = ""

    def __post_init__(self):
        if not self.last_update:
            self.last_update = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context": self.context.to_dict() if isinstance(self.context, ConversationContext) else self.context,
            "pending_image": self.pending_image,
            "image_attrs": self.image_attrs,
            "pending_outfit_image": self.pending_outfit_image,
            "outfit_analysis": self.outfit_analysis,
            "last_update": self.last_update
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        context = data.get("context", {})
        if isinstance(context, dict):
            context = ConversationContext.from_dict(context)
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            context=context,
            pending_image=data.get("pending_image"),
            image_attrs=data.get("image_attrs"),
            pending_outfit_image=data.get("pending_outfit_image"),
            outfit_analysis=data.get("outfit_analysis"),
            last_update=data.get("last_update", "")
        )


class MemoryStore:
    """内存存储（开发模式，无 Redis 时使用）"""

    def __init__(self):
        self._store: Dict[str, SessionData] = {}
        self._history: Dict[str, List[Message]] = {}

    async def get(self, session_id: str) -> Optional[SessionData]:
        return self._store.get(session_id)

    async def set(self, session_id: str, data: SessionData) -> None:
        self._store[session_id] = data

    async def delete(self, session_id: str) -> bool:
        if session_id in self._store:
            del self._store[session_id]
            return True
        return False

    async def get_history(self, session_id: str) -> List[Message]:
        return self._history.get(session_id, [])

    async def add_history(self, session_id: str, message: Message) -> None:
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append(message)
        # 限制历史长度
        if len(self._history[session_id]) > 100:
            self._history[session_id] = self._history[session_id][-100:]


class RedisMemoryStore:
    """Redis/Upstash 存储"""

    def __init__(self):
        self._client = None
        self._use_upstash = False
        self._init_client()

    def _init_client(self):
        """初始化 Redis 或 Upstash 客户端"""
        upstash_url = os.getenv("UPSTASH_REDIS_URL")
        upstash_token = os.getenv("UPSTASH_REDIS_TOKEN")

        if upstash_url and upstash_token:
            try:
                from upstash_redis import Redis
                self._client = Redis(url=upstash_url, token=upstash_token)
                self._use_upstash = True
            except ImportError:
                pass

        if not self._client:
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self._client = redis.from_url(redis_url)
                self._use_upstash = False
            except ImportError:
                pass

    async def get(self, session_id: str) -> Optional[SessionData]:
        if not self._client:
            return None

        key = f"session:{session_id}"
        try:
            if self._use_upstash:
                data = self._client.get(key)
            else:
                data = self._client.get(key)

            if data:
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                return SessionData.from_dict(json.loads(data))
        except Exception:
            pass
        return None

    async def set(self, session_id: str, data: SessionData, ttl: int = 86400) -> None:
        if not self._client:
            return

        key = f"session:{session_id}"
        try:
            json_data = json.dumps(data.to_dict())
            if self._use_upstash:
                self._client.setex(key, ttl, json_data)
            else:
                self._client.setex(key, ttl, json_data)
        except Exception:
            pass

    async def delete(self, session_id: str) -> bool:
        if not self._client:
            return False

        key = f"session:{session_id}"
        try:
            if self._use_upstash:
                result = self._client.delete(key)
            else:
                result = self._client.delete(key)
            return result > 0
        except Exception:
            return False

    async def get_history(self, session_id: str) -> List[Message]:
        if not self._client:
            return []

        key = f"history:{session_id}"
        try:
            if self._use_upstash:
                data = self._client.lrange(key, 0, -1)
            else:
                data = self._client.lrange(key, 0, -1)

            return [Message.from_dict(json.loads(m)) for m in data]
        except Exception:
            return []

    async def add_history(self, session_id: str, message: Message) -> None:
        if not self._client:
            return

        key = f"history:{session_id}"
        try:
            json_data = json.dumps(message.to_dict())
            if self._use_upstash:
                self._client.rpush(key, json_data)
                self._client.ltrim(key, -100, -1)
            else:
                self._client.rpush(key, json_data)
                self._client.ltrim(key, -100, -1)
        except Exception:
            pass


class ConversationMemory:
    """
    短期对话记忆管理器

    存储内容：
    - 当前对话上下文（date, location, occasion, style, temperature）
    - 待处理的图片（pending_image, outfit_image）
    - 已分析的图片来源

    Session 生命周期：
    - 每日凌晨清空（通过 TTL）
    - 前端应用关闭时调用 /chat/session/close
    """

    def __init__(self):
        self._redis = RedisMemoryStore()
        self._memory = MemoryStore()
        self._use_redis = self._redis._client is not None

    async def get(self, session_id: str) -> SessionData:
        """获取会话数据"""
        if self._use_redis:
            data = await self._redis.get(session_id)
        else:
            data = await self._memory.get(session_id)

        if data:
            return data

        return SessionData(session_id=session_id, user_id="")

    async def update(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        pending_image: Optional[str] = None,
        image_attrs: Optional[Dict[str, Any]] = None,
        pending_outfit_image: Optional[str] = None,
        outfit_analysis: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> SessionData:
        """更新会话数据"""
        data = await self.get(session_id)

        if user_id:
            data.user_id = user_id

        if context:
            if isinstance(data.context, dict):
                data.context = ConversationContext.from_dict(context)
            else:
                for key, value in context.items():
                    if hasattr(data.context, key):
                        setattr(data.context, key, value)

        if pending_image is not None:
            data.pending_image = pending_image
        if image_attrs is not None:
            data.image_attrs = image_attrs
        if pending_outfit_image is not None:
            data.pending_outfit_image = pending_outfit_image
        if outfit_analysis is not None:
            data.outfit_analysis = outfit_analysis

        data.last_update = datetime.now().isoformat()

        if self._use_redis:
            await self._redis.set(session_id, data)
        else:
            await self._memory.set(session_id, data)

        return data

    async def clear(self, session_id: str) -> bool:
        """清空会话数据"""
        if self._use_redis:
            return await self._redis.delete(session_id)
        else:
            return await self._memory.delete(session_id)

    async def get_messages(self, session_id: str) -> List[Message]:
        """获取对话历史"""
        if self._use_redis:
            return await self._redis.get_history(session_id)
        else:
            return await self._memory.get_history(session_id)

    async def add_message(self, session_id: str, role: str, content: str, images: List[str] = None) -> None:
        """添加消息到历史"""
        message = Message(role=role, content=content, images=images or [])
        if self._use_redis:
            await self._redis.add_history(session_id, message)
        else:
            await self._memory.add_history(session_id, message)


# 全局实例
memory = ConversationMemory()


async def get_session_memory(session_id: str) -> SessionData:
    """获取会话记忆"""
    return await memory.get(session_id)


async def update_session_memory(session_id: str, **kwargs) -> SessionData:
    """更新会话记忆"""
    return await memory.update(session_id, **kwargs)


async def clear_session_memory(session_id: str) -> bool:
    """清空会话记忆"""
    return await memory.clear(session_id)
