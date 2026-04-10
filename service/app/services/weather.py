"""天气服务"""
import httpx
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class WeatherInfo:
    """天气信息数据结构"""
    city: str
    date: str
    temperature: float
    weather: str  # 天气状况：晴/多云/小雨等
    humidity: int  # 湿度百分比
    wind: str  # 风力风向
    uv_index: Optional[int] = None  # 紫外线指数
    source: str = "unknown"


class WeatherService:
    """天气获取服务（支持高德天气 API）"""

    def __init__(self, api_key: Optional[str] = None):
        import os
        self.api_key = api_key or os.getenv("GAODE_API_KEY") or os.getenv("WEATHER_API_KEY", "")
        self.base_url = "https://restapi.amap.com/v3/weather"

    async def get_weather(
        self,
        city: str,
        date: Optional[str] = None
    ) -> WeatherInfo:
        """
        获取天气信息

        Args:
            city: 城市名称
            date: 日期，None 表示今天，"明天"/"后天" 等相对日期自动转换

        Returns:
            WeatherInfo 对象
        """
        if date and date != "今天":
            target_date = self._parse_relative_date(date)
        else:
            target_date = datetime.now().strftime("%Y-%m-%d")

        try:
            weather_data = await self._fetch_gaode_weather(city)
            return WeatherInfo(
                city=city,
                date=target_date,
                temperature=float(weather_data.get("temperature", 20)),
                weather=weather_data.get("weather", "晴"),
                humidity=int(weather_data.get("humidity", 50)),
                wind=weather_data.get("wind", ""),
                source="gaode"
            )
        except Exception:
            return self._get_mock_weather(city, target_date)

    async def _fetch_gaode_weather(self, city: str) -> Dict[str, Any]:
        """调用高德天气 API"""
        if not self.api_key:
            raise ValueError("高德天气 API Key 未配置")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "key": self.api_key,
                    "city": city,
                    "extensions": "base"
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1":
                raise ValueError(f"高德 API 返回错误: {data.get('info', '未知错误')}")

            lives = data.get("lives", [])
            if not lives:
                raise ValueError(f"未找到 {city} 的天气数据")

            return lives[0]

    def _parse_relative_date(self, date_str: str) -> str:
        """解析相对日期"""
        today = datetime.now()
        date_str = date_str.strip()

        if date_str == "今天":
            return today.strftime("%Y-%m-%d")
        elif date_str == "明天":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_str == "后天":
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        elif date_str == "大后天":
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        elif date_str == "昨天":
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                return today.strftime("%Y-%m-%d")

    def _get_mock_weather(self, city: str, date: str) -> WeatherInfo:
        """返回模拟天气数据（用于测试）"""
        return WeatherInfo(
            city=city,
            date=date,
            temperature=18.0,
            weather="晴",
            humidity=50,
            wind="东南风2级",
            source="mock"
        )

    def get_temperature_range(self, temperature: float) -> Literal["summer", "spring_autumn", "winter", "all_season"]:
        """根据温度判断季节范围"""
        if temperature >= 25:
            return "summer"
        elif temperature >= 10:
            return "spring_autumn"
        else:
            return "winter"


# 全局天气服务实例
weather_service = WeatherService()


async def get_weather(city: str, date: Optional[str] = None) -> WeatherInfo:
    """
    获取天气信息（便捷函数）

    Args:
        city: 城市名称
        date: 日期，None 表示今天

    Returns:
        WeatherInfo 对象
    """
    return await weather_service.get_weather(city, date)
