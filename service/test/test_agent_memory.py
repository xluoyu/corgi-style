"""Agent Memory 单元测试"""
import pytest
from app.agent.memory import AgentMemory
from app.agent.dialogue_session import ConversationContext


class TestAgentMemoryBasics:
    """基础字段读写"""

    def test_default_values(self):
        m = AgentMemory(session_id="s1", user_id="u1")
        assert m.session_id == "s1"
        assert m.user_id == "u1"
        assert m.target_city is None
        assert m.target_scene is None
        assert m.target_date is None
        assert m.target_temperature is None
        assert m.recent_messages == []
        assert m.missing_fields == []

    def test_set_context_fields(self):
        m = AgentMemory(session_id="s1", user_id="u1")
        m.target_city = "杭州"
        m.target_scene = "work"
        m.target_temperature = 22.0
        m.pending_task = "穿搭推荐"
        m.missing_fields = ["scene"]

        assert m.target_city == "杭州"
        assert m.target_scene == "work"
        assert m.target_temperature == 22.0
        assert m.pending_task == "穿搭推荐"
        assert m.missing_fields == ["scene"]


class TestAgentMemoryContextString:
    """上下文字符串生成"""

    def test_empty_context(self):
        m = AgentMemory()
        assert m.to_context_string() == "无已记住的信息"

    def test_partial_context(self):
        m = AgentMemory()
        m.target_city = "上海"
        m.target_temperature = 18.5
        s = m.to_context_string()
        assert "上海" in s
        assert "18.5" in s
        assert "场合" not in s

    def test_full_context(self):
        m = AgentMemory()
        m.target_city = "北京"
        m.target_scene = "date"
        m.target_date = "2026-03-26"
        m.target_temperature = 12.0
        m.pending_task = "穿搭推荐"
        m.missing_fields = ["scene", "color"]
        m.preferred_style = "休闲"
        m.frequent_colors = ["黑色", "白色"]

        s = m.to_context_string()
        assert "北京" in s
        assert "date" in s
        assert "2026-03-26" in s
        assert "12.0" in s
        assert "休闲" in s
        assert "黑色" in s
        assert "正在进行：穿搭推荐" in s
        assert "scene" in s  # missing_fields


class TestAgentMemorySerialization:
    """序列化 / 反序列化"""

    def test_to_dict_roundtrip(self):
        m = AgentMemory(session_id="s1", user_id="u1")
        m.target_city = "广州"
        m.target_scene = "casual"
        m.target_temperature = 28.0
        m.add_message("user", "我想穿得休闲一点")

        d = m.to_dict()
        restored = AgentMemory.from_dict(d)

        assert restored.session_id == "s1"
        assert restored.user_id == "u1"
        assert restored.target_city == "广州"
        assert restored.target_scene == "casual"
        assert restored.target_temperature == 28.0
        assert len(restored.recent_messages) == 1

    def test_from_dict_none(self):
        restored = AgentMemory.from_dict(None)
        assert restored.session_id == ""

    def test_to_context_dict(self):
        m = AgentMemory(session_id="s1", user_id="u1")
        m.target_city = "成都"
        m.target_scene = "sport"
        m.target_temperature = 15.0
        m.missing_fields = ["temperature"]
        m.pending_task = "穿搭推荐"

        ctx = m.to_context_dict()
        assert ctx["target_city"] == "成都"
        assert ctx["target_scene"] == "sport"
        assert ctx["target_temperature"] == 15.0
        assert ctx["asking_for"] == "temperature"
        assert ctx["pending_intent"] == "穿搭推荐"

    def test_from_conversation_context(self):
        ctx = ConversationContext(
            target_city="深圳",
            target_scene="formal",
            target_date="2026-03-27",
            target_temperature=20.0,
        )
        m = AgentMemory.from_conversation_context(ctx, session_id="s2", user_id="u2")

        assert m.target_city == "深圳"
        assert m.target_scene == "formal"
        assert m.target_date == "2026-03-27"
        assert m.target_temperature == 20.0
        assert m.session_id == "s2"
        assert m.user_id == "u2"


class TestAgentMemoryMessages:
    """消息管理"""

    def test_add_message(self):
        m = AgentMemory()
        m.add_message("user", "今天天气怎么样")
        m.add_message("assistant", "杭州现在是晴天，20度")

        assert len(m.recent_messages) == 2
        assert m.recent_messages[0]["role"] == "user"
        assert m.recent_messages[0]["content"] == "今天天气怎么样"
        assert m.recent_messages[1]["role"] == "assistant"
        assert "timestamp" in m.recent_messages[0]

    def test_message_truncation(self):
        m = AgentMemory()
        for i in range(25):
            m.add_message("user", f"消息{i}")

        assert len(m.recent_messages) == 20
        # 最后一条应该是第24条
        assert "消息24" in m.recent_messages[-1]["content"]
        assert "消息0" not in m.recent_messages[-1]["content"]


class TestAgentMemoryRememberRecall:
    """remember / recall 方法"""

    def test_remember_partial(self):
        m = AgentMemory()
        m.remember(city="南京", temperature=25.0)

        assert m.target_city == "南京"
        assert m.target_temperature == 25.0

    def test_remember_all(self):
        m = AgentMemory()
        m.remember(
            city="武汉",
            scene="party",
            date="2026-04-01",
            temperature=16.0,
            style="正式",
            colors=["灰色", "藏蓝"],
        )

        assert m.target_city == "武汉"
        assert m.target_scene == "party"
        assert m.target_date == "2026-04-01"
        assert m.target_temperature == 16.0
        assert m.preferred_style == "正式"
        assert m.frequent_colors == ["灰色", "藏蓝"]

    def test_recall(self):
        m = AgentMemory()
        m.target_city = "西安"
        m.target_scene = "work"
        m.preferred_style = "商务"
        m.missing_fields = ["color"]

        r = m.recall()
        assert r["target_city"] == "西安"
        assert r["target_scene"] == "work"
        assert r["preferred_style"] == "商务"
        assert r["missing_fields"] == ["color"]
        assert r["target_temperature"] is None
