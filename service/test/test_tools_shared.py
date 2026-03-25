"""共享工具（SharedTools）单元测试"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.agent.tools.shared import (
    get_weather,
    analyze_clothing_image,
    remember_context,
    recall_context,
    SHARED_TOOLS,
)


class TestSharedToolsRegistration:
    """工具注册完整性"""

    def test_all_tools_present(self):
        names = [t.name for t in SHARED_TOOLS]
        assert "get_weather" in names
        assert "analyze_clothing_image" in names
        assert "remember_context" in names
        assert "recall_context" in names


class TestGetWeather:
    """get_weather 工具"""

    @pytest.mark.asyncio
    async def test_success(self):
        # 正确 patch 点：weather_service 模块中的 get_weather 方法
        with patch("app.agent.services.weather_service.WeatherService.get_weather",
                   new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "city": "杭州",
                "temperature": 22,
                "weather": "晴",
                "humidity": 65,
            }

            result = await get_weather.ainvoke({"city": "杭州"})
            data = json.loads(result)

            assert data["city"] == "杭州"
            assert data["temperature"] == 22
            mock_method.assert_called_once_with("杭州", None)

    @pytest.mark.asyncio
    async def test_with_date(self):
        with patch("app.agent.services.weather_service.WeatherService.get_weather",
                   new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {
                "city": "北京",
                "temperature": 5,
                "weather": "多云",
                "humidity": 40,
            }

            result = await get_weather.ainvoke({"city": "北京", "date": "明天"})
            data = json.loads(result)

            assert data["temperature"] == 5
            mock_method.assert_called_once_with("北京", "明天")

    @pytest.mark.asyncio
    async def test_error(self):
        with patch("app.agent.services.weather_service.WeatherService.get_weather",
                   new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("网络错误")

            result = await get_weather.ainvoke({"city": "上海"})
            data = json.loads(result)

            assert "error" in data
            assert data["error"] == "Exception"


class TestAnalyzeClothingImage:
    """analyze_clothing_image 工具"""

    @pytest.mark.asyncio
    async def test_success(self):
        with patch("app.agent.tools.shared.image_analyzer") as mock_ia:
            mock_ia.analyze = MagicMock(return_value={
                "name": "白色T恤",
                "category": "top",
                "color": "白色",
                "material": "棉",
            })

            result = await analyze_clothing_image.ainvoke({
                "image_url": "https://oss.example.com/test.jpg"
            })
            data = json.loads(result)

            assert data["name"] == "白色T恤"
            assert data["category"] == "top"
            mock_ia.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_user_hint(self):
        with patch("app.agent.tools.shared.image_analyzer") as mock_ia:
            mock_ia.analyze = MagicMock(return_value={
                "name": "黑色衬衫",
                "category": "top",
                "color": "黑色",
            })

            result = await analyze_clothing_image.ainvoke({
                "image_url": "https://oss.example.com/shirt.jpg",
                "user_hint": "这件是长袖",
            })
            data = json.loads(result)

            assert data["color"] == "黑色"
            call_kwargs = mock_ia.analyze.call_args[1]
            assert "这件是长袖" in call_kwargs["prompt"]

    @pytest.mark.asyncio
    async def test_error(self):
        with patch("app.agent.tools.shared.image_analyzer") as mock_ia:
            mock_ia.analyze = MagicMock(side_effect=RuntimeError("图片无法加载"))

            result = await analyze_clothing_image.ainvoke({
                "image_url": "https://invalid.url/bad.jpg"
            })
            data = json.loads(result)

            assert "error" in data
            assert data["error"] == "RuntimeError"


class TestRememberContext:
    """remember_context 工具"""

    @pytest.mark.asyncio
    async def test_all_fields(self):
        result = await remember_context.ainvoke({
            "city": "成都",
            "scene": "casual",
            "date": "2026-03-28",
            "temperature": 18.5,
            "style": "休闲",
            "colors": "蓝色,灰色",
        })
        data = json.loads(result)

        assert data["status"] == "remembered"
        assert data["remembered"]["city"] == "成都"
        assert data["remembered"]["scene"] == "casual"
        assert data["remembered"]["date"] == "2026-03-28"
        assert data["remembered"]["temperature"] == 18.5
        assert data["remembered"]["style"] == "休闲"
        assert data["remembered"]["colors"] == ["蓝色", "灰色"]

    @pytest.mark.asyncio
    async def test_partial_fields(self):
        result = await remember_context.ainvoke({
            "city": "重庆",
            "temperature": 30.0,
        })
        data = json.loads(result)

        assert data["status"] == "remembered"
        assert data["remembered"]["city"] == "重庆"
        assert data["remembered"]["temperature"] == 30.0
        assert data["remembered"]["scene"] is None

    @pytest.mark.asyncio
    async def test_colors_null(self):
        result = await remember_context.ainvoke({"city": "西安"})
        data = json.loads(result)

        assert data["remembered"]["colors"] is None

    @pytest.mark.asyncio
    async def test_colors_empty_string(self):
        result = await remember_context.ainvoke({"city": "西安", "colors": ""})
        data = json.loads(result)

        assert data["remembered"]["colors"] is None


class TestRecallContext:
    """recall_context 工具"""

    @pytest.mark.asyncio
    async def test_returns_status(self):
        result = await recall_context.ainvoke({})
        data = json.loads(result)

        assert data["status"] == "recalled"
        assert "message" in data
