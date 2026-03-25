"""穿搭工具（OutfitTools）单元测试"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.agent.tools.outfit import plan_outfit, get_outfit_history, OUTFIT_TOOLS


class TestOutfitToolsRegistration:
    """工具注册完整性"""

    def test_all_tools_present(self):
        names = [t.name for t in OUTFIT_TOOLS]
        assert "plan_outfit" in names
        assert "get_outfit_history" in names


class TestPlanOutfit:
    """plan_outfit 工具"""

    @pytest.mark.asyncio
    async def test_success_parses_json(self):
        mock_response = MagicMock()
        mock_response.content = '{"description":"适合春秋的休闲穿搭","outfits":[]}'

        with patch("app.agent.tools.outfit.get_cached_provider") as mock_provider:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_provider.return_value.chat_model = mock_llm

            with patch("app.agent.graph.nodes.planning.create_planning_prompt", return_value="mock prompt"):
                result = await plan_outfit.ainvoke({
                    "scene": "casual",
                    "temperature": 20.0,
                    "wardrobe_items": [
                        {"id": "c1", "category": "top", "color": "白色"},
                        {"id": "c2", "category": "pants", "color": "蓝色"},
                    ],
                    "max_options": 3,
                })

                data = json.loads(result)
                assert "description" in data

    @pytest.mark.asyncio
    async def test_fallback_on_non_json(self):
        mock_response = MagicMock()
        mock_response.content = "这是一段纯文本回复，不含JSON"

        with patch("app.agent.tools.outfit.get_cached_provider") as mock_provider:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_provider.return_value.chat_model = mock_llm

            with patch("app.agent.graph.nodes.planning.create_planning_prompt", return_value="mock"):
                result = await plan_outfit.ainvoke({
                    "scene": "work",
                    "temperature": 15.0,
                    "wardrobe_items": [],
                })
                data = json.loads(result)
                assert "description" in data
                assert "纯文本回复" in data["description"]

    @pytest.mark.asyncio
    async def test_error(self):
        with patch("app.agent.tools.outfit.get_cached_provider") as mock_provider:
            mock_provider.side_effect = Exception("LLM 服务不可用")

            result = await plan_outfit.ainvoke({
                "scene": "date",
                "temperature": 22.0,
                "wardrobe_items": [],
            })
            data = json.loads(result)
            assert "error" in data


class TestGetOutfitHistory:
    """get_outfit_history 工具"""

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db = MagicMock()
        mock_db.query.return_value = mock_query

        with patch("app.agent.tools.outfit.get_db_for_tools", return_value=mock_db):
            with patch("app.agent.tools.outfit.get_current_user_id", return_value="user-456"):
                result = await get_outfit_history.ainvoke({})
                data = json.loads(result)
                assert data == []

    @pytest.mark.asyncio
    async def test_returns_records(self):
        mock_record = MagicMock()
        mock_record.id = "outfit-001"
        mock_record.create_time.isoformat = MagicMock(return_value="2026-03-20T10:00:00")
        mock_record.occasion = "work"
        mock_record.outfit_name = "商务穿搭"
        mock_record.outfit_snapshot = {}
        mock_record.weather_snapshot = {}

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_record]

        mock_db = MagicMock()
        mock_db.query.return_value = mock_query

        with patch("app.agent.tools.outfit.get_db_for_tools", return_value=mock_db):
            with patch("app.agent.tools.outfit.get_current_user_id", return_value="user-456"):
                result = await get_outfit_history.ainvoke({"limit": 5})
                data = json.loads(result)

                assert len(data) == 1
                assert data[0]["id"] == "outfit-001"
                assert data[0]["occasion"] == "work"
                assert data[0]["outfit_name"] == "商务穿搭"

    @pytest.mark.asyncio
    async def test_with_date_filter(self):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db = MagicMock()
        mock_db.query.return_value = mock_query

        with patch("app.agent.tools.outfit.get_db_for_tools", return_value=mock_db):
            with patch("app.agent.tools.outfit.get_current_user_id", return_value="user-456"):
                await get_outfit_history.ainvoke({"date": "2026-03-20", "limit": 10})

                # 验证 filter 被调用
                assert mock_query.filter.called

    @pytest.mark.asyncio
    async def test_error(self):
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("数据库错误")

        with patch("app.agent.tools.outfit.get_db_for_tools", return_value=mock_db):
            with patch("app.agent.tools.outfit.get_current_user_id", return_value="user-789"):
                result = await get_outfit_history.ainvoke({})
                data = json.loads(result)
                assert "error" in data
