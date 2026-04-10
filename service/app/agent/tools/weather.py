"""天气工具"""
import json
from typing import Optional
from langchain_core.tools import tool

from app.services.weather import get_weather as service_get_weather


@tool
async def get_weather(city: str) -> str:
    """
    获取城市天气信息。

    Args:
        city: 城市名称（如"北京"、"上海"）

    Returns:
        JSON 格式的天气信息，包含温度、天气状况、湿度等
    """
    try:
        weather = await service_get_weather(city)
        return json.dumps({
            "city": weather.city,
            "date": weather.date,
            "temperature": weather.temperature,
            "weather": weather.weather,
            "humidity": weather.humidity,
            "wind": weather.wind,
            "source": weather.source
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def create_weather_tools():
    """创建天气相关工具列表"""
    return [get_weather]
