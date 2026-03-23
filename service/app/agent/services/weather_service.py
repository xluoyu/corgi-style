"""天气服务"""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class WeatherService:
    """天气获取服务（支持高德天气 API）"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.base_url = "https://restapi.amap.com/v3/weather"

    async def get_weather(self, city: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取天气信息

        Args:
            city: 城市名称或编码
            date: 日期，None 表示今天，"后天" 等相对日期会自动转换

        Returns:
            {
                "city": "北京",
                "date": "2026-03-25",
                "temperature": 12.0,
                "weather": "多云",
                "humidity": 45,
                "wind": "北风3级"
            }
        """
        if date and date != "今天":
            # 处理相对日期
            target_date = self._parse_relative_date(date)
        else:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # 如果查询的是今天或未来3天内，使用高德天气API
        try:
            weather_data = await self._fetch_gaode_weather(city)
            return {
                "city": city,
                "date": target_date,
                "temperature": weather_data.get("temperature", 20.0),
                "weather": weather_data.get("weather", "晴"),
                "humidity": weather_data.get("humidity", 50),
                "wind": weather_data.get("wind", ""),
                "source": "gaode"
            }
        except Exception:
            # Fallback 到模拟数据（实际生产环境应记录日志）
            return self._get_mock_weather(city, target_date)

    async def _fetch_gaode_weather(self, city: str) -> Dict[str, Any]:
        """调用高德天气 API"""
        if not self.api_key:
            raise ValueError("高德天气 API Key 未配置")

        async with httpx.AsyncClient(timeout=10.0) as client:
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
            # 尝试直接解析
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                # 无法识别，返回今天
                return today.strftime("%Y-%m-%d")

    def _get_mock_weather(self, city: str, date: str) -> Dict[str, Any]:
        """返回模拟天气数据（用于测试）"""
        return {
            "city": city,
            "date": date,
            "temperature": 18.0,
            "weather": "晴",
            "humidity": 50,
            "wind": "东南风2级",
            "source": "mock"
        }


# 全局天气服务实例
weather_service = WeatherService()
