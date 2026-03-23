"""天气获取节点"""
from typing import Dict, Any
from app.agent.graph.state import GraphState
from app.agent.services.weather_service import weather_service


async def weather_node(state: GraphState) -> GraphState:
    """
    天气获取节点

    如果状态中包含 target_city 和 target_date，获取对应日期的天气
    """
    city = state.get("target_city")
    date = state.get("target_date")

    if not city:
        # 没有城市信息，跳过天气获取
        return state

    try:
        weather_data = await weather_service.get_weather(city, date)

        # 提取温度
        temperature = weather_data.get("temperature")
        if temperature:
            # 温度可能是字符串，尝试转换
            if isinstance(temperature, str):
                try:
                    temperature = float(temperature.replace("°", "").replace("C", ""))
                except ValueError:
                    temperature = None

            if temperature is not None:
                state["target_temperature"] = temperature

        # 将天气信息存入 context
        if "context" not in state:
            state["context"] = {}
        state["context"]["weather"] = weather_data

    except Exception as e:
        # 天气获取失败，记录错误但不阻断流程
        if "context" not in state:
            state["context"] = {}
        state["context"]["weather_error"] = str(e)
        state["error"] = f"天气获取失败: {str(e)}"

    return state
