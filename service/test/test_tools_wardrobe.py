"""衣柜工具（WardrobeTools）单元测试"""
import pytest
from unittest.mock import patch, MagicMock
import json

from app.agent.tools.wardrobe import (
    search_wardrobe,
    add_clothes_to_wardrobe,
    WARDROBE_TOOLS,
)


class TestWardrobeToolsRegistration:
    """工具注册完整性"""

    def test_all_tools_present(self):
        names = [t.name for t in WARDROBE_TOOLS]
        assert "search_wardrobe" in names
        assert "add_clothes_to_wardrobe" in names


class TestSearchWardrobe:
    """search_wardrobe 工具"""

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        with patch("app.agent.graph.nodes.wardrobe.query_wardrobe") as mock_qw:
            mock_qw.return_value = []

            with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
                with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                    result = await search_wardrobe.ainvoke({})
                    data = json.loads(result)

                    assert data == []

    @pytest.mark.asyncio
    async def test_returns_items(self):
        mock_item = {
            "id": "clothes-abc",
            "description": "白色棉质T恤",
            "category": "top",
            "color": "白色",
            "material": "棉",
            "image_url": "https://oss.example.com/t.jpg",
            "temperature_range": "summer",
            "scene": "casual",
            "wear_count": 3,
        }

        with patch("app.agent.graph.nodes.wardrobe.query_wardrobe") as mock_qw:
            mock_qw.return_value = [mock_item]

            with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
                with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                    result = await search_wardrobe.ainvoke({"category": "top"})
                    data = json.loads(result)

                    assert len(data) == 1
                    assert data[0]["id"] == "clothes-abc"
                    assert data[0]["category"] == "top"
                    assert data[0]["color"] == "白色"
                    assert data[0]["generated_image_url"] is None

    @pytest.mark.asyncio
    async def test_passes_filters(self):
        with patch("app.agent.graph.nodes.wardrobe.query_wardrobe") as mock_qw:
            mock_qw.return_value = []

            with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
                with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                    await search_wardrobe.ainvoke({
                        "category": "pants",
                        "color": "黑色",
                        "scene": "work",
                    })

                    mock_qw.assert_called_once()
                    call_kwargs = mock_qw.call_args[1]
                    assert call_kwargs["category"] == "pants"
                    assert call_kwargs["color"] == "黑色"

    @pytest.mark.asyncio
    async def test_error(self):
        with patch("app.agent.graph.nodes.wardrobe.query_wardrobe") as mock_qw:
            mock_qw.side_effect = Exception("查询失败")

            with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
                with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                    result = await search_wardrobe.ainvoke({})
                    data = json.loads(result)

                    assert "error" in data
                    assert data["error"] == "Exception"


class TestAddClothesToWardrobe:
    """add_clothes_to_wardrobe 工具"""

    @pytest.mark.asyncio
    async def test_success(self):
        mock_analysis = {
            "name": "灰色卫衣",
            "category": "outer",
            "color": "灰色",
            "material": "棉",
            "temperature_range": "all_season",
        }

        mock_clothes = MagicMock()
        mock_clothes.id = "new-clothes-id"

        with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
            with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                # clothes_agent 是模块级实例，patch 其 _create_clothes_record 方法
                with patch("app.agent.clothes_agent.clothes_agent._create_clothes_record",
                           return_value=mock_clothes):
                    with patch("app.services.image_analysis.image_analyzer") as mock_ia:
                        with patch("app.services.image_generator.image_generator") as mock_ig:
                            mock_ia.analyze = MagicMock(return_value=mock_analysis)
                            mock_ig.generate = MagicMock(return_value="https://oss.example.com/cartoon.jpg")

                            result = await add_clothes_to_wardrobe.ainvoke({
                                "image_url": "https://oss.example.com/original.jpg",
                                "name": "我的卫衣",
                            })
                            data = json.loads(result)

                            assert data["clothes_id"] == "new-clothes-id"
                            assert data["name"] == "我的卫衣"
                            assert data["category"] == "outer"
                            assert data["generated_image_url"] == "https://oss.example.com/cartoon.jpg"

    @pytest.mark.asyncio
    async def test_error(self):
        with patch("app.agent.tools.wardrobe.get_db_for_tools", return_value=MagicMock()):
            with patch("app.agent.tools.wardrobe.get_current_user_id", return_value="user-123"):
                with patch("app.services.image_analysis.image_analyzer") as mock_ia:
                    mock_ia.analyze = MagicMock(side_effect=Exception("分析服务不可用"))

                    result = await add_clothes_to_wardrobe.ainvoke({
                        "image_url": "https://bad.url/image.jpg"
                    })
                    data = json.loads(result)

                    assert "error" in data
