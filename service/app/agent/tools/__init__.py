"""Agent Tools — 按业务分组的 LangChain 工具集。

新版工具调用 services 层，复用业务逻辑。
"""
from typing import List

# 新版工具（调用 services 层）
from app.agent.tools.weather import create_weather_tools
from app.agent.tools.wardrobe import create_wardrobe_tools
from app.agent.tools.image import create_image_tools
from app.agent.tools.style import create_style_tools


def get_all_tools() -> List:
    """获取所有 Agent Tools"""
    tools = []
    tools.extend(create_weather_tools())
    tools.extend(create_wardrobe_tools())
    tools.extend(create_image_tools())
    tools.extend(create_style_tools())
    return tools


__all__ = [
    "create_weather_tools",
    "create_wardrobe_tools",
    "create_image_tools",
    "create_style_tools",
    "get_all_tools",
]
