"""AgentMemory — Agent 的统一记忆接口。

替代 ConversationContext，作为 Agent 跨轮次的上下文管理。
支持与 DialogueSessionManager 双向序列化兼容。
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.agent.dialogue_session import ConversationContext


# ============================================================
# 数据类
# ============================================================

@dataclass
class AgentMemory:
    """Agent 的记忆，管理跨轮次上下文。"""
    session_id: str = ""
    user_id: str = ""

    # 当前任务信息
    target_city: Optional[str] = None
    target_scene: Optional[str] = None
    target_date: Optional[str] = None
    target_temperature: Optional[float] = None

    # 未完成的任务
    pending_task: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)

    # 偏好
    preferred_style: Optional[str] = None
    frequent_colors: List[str] = field(default_factory=list)

    # 对话历史（最近 20 条，用于注入 LLM）
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)

    # 兼容字段：current_outfit、asking_for、pending_intent
    # 由 ConversationContext 映射而来，AgentMemory 内部不使用
    current_outfit: Optional[Dict[str, Any]] = None
    asking_for: Optional[str] = None
    pending_intent: Optional[str] = None

    # ============================================================
    # 上下文字符串
    # ============================================================

    def to_context_string(self) -> str:
        """转化为供 LLM 读取的上下文字符串。"""
        parts = []
        if self.target_city:
            parts.append(f"城市：{self.target_city}")
        if self.target_scene:
            parts.append(f"场合：{self.target_scene}")
        if self.target_date:
            parts.append(f"日期：{self.target_date}")
        if self.target_temperature is not None:
            parts.append(f"温度：{self.target_temperature}℃")
        if self.pending_task:
            missing = ", ".join(self.missing_fields) if self.missing_fields else "无"
            parts.append(f"正在进行：{self.pending_task}（缺少：{missing}）")
        if self.preferred_style:
            parts.append(f"风格偏好：{self.preferred_style}")
        if self.frequent_colors:
            parts.append(f"常用颜色：{', '.join(self.frequent_colors)}")
        return "\n".join(parts) if parts else "无已记住的信息"

    # ============================================================
    # 序列化 / 反序列化
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """转为 dict，用于 Session 持久化。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AgentMemory":
        """
        从 dict 恢复。

        兼容两种格式：
        1. AgentMemory.to_dict() 格式（完整字段）
        2. ConversationContext.to_dict() 格式（兼容旧 Session 恢复）
        """
        if data is None:
            return cls()

        # 取 dataclass 支持的字段
        valid_fields = cls.__dataclass_fields__.keys()

        # 如果是 ConversationContext 格式（没有 session_id/user_id），使用默认值
        kwargs = {}
        for k, v in data.items():
            if k in valid_fields:
                kwargs[k] = v

        return cls(**kwargs)

    def to_context_dict(self) -> Dict[str, Any]:
        """
        转为 ConversationContext 格式，供 Session 持久化用。

        写入 session.context 字段时使用此方法，保持与 DialogueSessionManager 的兼容。
        """
        return {
            "target_city": self.target_city,
            "target_scene": self.target_scene,
            "target_date": self.target_date,
            "target_temperature": self.target_temperature,
            "current_outfit": self.current_outfit,
            "asking_for": self.missing_fields[0] if self.missing_fields else None,
            "pending_intent": self.pending_task,
        }

    @classmethod
    def from_conversation_context(cls, ctx: ConversationContext, session_id: str = "", user_id: str = "") -> "AgentMemory":
        """从 ConversationContext 转换，兼容旧数据。"""
        return cls(
            session_id=session_id,
            user_id=user_id,
            target_city=ctx.target_city,
            target_scene=ctx.target_scene,
            target_date=ctx.target_date,
            target_temperature=ctx.target_temperature,
            current_outfit=ctx.current_outfit,
            pending_task=ctx.pending_intent,
            asking_for=ctx.asking_for,
            pending_intent=ctx.pending_intent,
        )

    def update_from_context(self, ctx: ConversationContext) -> None:
        """从 ConversationContext 更新字段（保留新字段）。"""
        self.target_city = ctx.target_city
        self.target_scene = ctx.target_scene
        self.target_date = ctx.target_date
        self.target_temperature = ctx.target_temperature
        self.current_outfit = ctx.current_outfit
        self.pending_task = ctx.pending_intent
        self.asking_for = ctx.asking_for
        self.pending_intent = ctx.pending_intent

    # ============================================================
    # 消息管理
    # ============================================================

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到历史。

        Args:
            role: 角色，"user" / "assistant" / "system"
            content: 消息内容
        """
        self.recent_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # 超过 20 条自动截断（保留最新）
        if len(self.recent_messages) > 20:
            self.recent_messages = self.recent_messages[-20:]

    # ============================================================
    # 上下文更新便捷方法
    # ============================================================

    def remember(self, city: Optional[str] = None, scene: Optional[str] = None,
                 date: Optional[str] = None, temperature: Optional[float] = None,
                 style: Optional[str] = None, colors: Optional[List[str]] = None) -> None:
        """
        记住当前对话中的关键信息。

        与 remember_context 工具配合使用。
        """
        if city is not None:
            self.target_city = city
        if scene is not None:
            self.target_scene = scene
        if date is not None:
            self.target_date = date
        if temperature is not None:
            self.target_temperature = temperature
        if style is not None:
            self.preferred_style = style
        if colors is not None:
            self.frequent_colors = colors

    def recall(self) -> Dict[str, Any]:
        """回忆已记住的上下文，返回字典格式。"""
        return {
            "target_city": self.target_city,
            "target_scene": self.target_scene,
            "target_date": self.target_date,
            "target_temperature": self.target_temperature,
            "preferred_style": self.preferred_style,
            "frequent_colors": self.frequent_colors,
            "pending_task": self.pending_task,
            "missing_fields": self.missing_fields,
        }
