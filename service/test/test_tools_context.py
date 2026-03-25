"""ContextVar DB 注入单元测试"""
import pytest
from app.agent.tools.context import (
    set_tool_context,
    get_db_for_tools,
    get_current_user_id,
)


class TestContextVar:
    """ContextVar 函数测试（无 DB 依赖）"""

    def test_set_and_get_db(self):
        """验证 set_tool_context 后能正确取回 db session"""
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.query = MagicMock()

        set_tool_context(mock_db, "user-abc")
        retrieved = get_db_for_tools()

        assert retrieved is mock_db

    def test_set_and_get_user_id(self):
        """验证 set_tool_context 后能正确取回 user_id"""
        set_tool_context(None, "user-xyz-123")
        assert get_current_user_id() == "user-xyz-123"

    def test_context_isolation(self):
        """验证 ContextVar 在同一协程内的隔离性（同一个值）"""
        from unittest.mock import MagicMock

        db1, db2 = MagicMock(), MagicMock()
        uid1, uid2 = "user-A", "user-B"

        set_tool_context(db1, uid1)
        assert get_db_for_tools() is db1
        assert get_current_user_id() == uid1

        set_tool_context(db2, uid2)
        assert get_db_for_tools() is db2
        assert get_current_user_id() == uid2
