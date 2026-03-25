"""共享工具（SharedTools）。

使用 @tool 装饰器（langchain_core.tools），每个 Tool 内部通过
get_db_for_tools() / get_current_user_id() 获取 DB 和用户。
"""
import json
from typing import Optional

from langchain_core.tools import tool

from app.agent.services.weather_service import weather_service
from app.services.image_analysis import image_analyzer
from app.agent.memory import AgentMemory


# ============================================================
# 工具实现
# ============================================================

@tool
async def get_weather(city: str, date: Optional[str] = None) -> str:
    """获取指定城市的天气信息，包括温度、湿度和天气状况。
    当用户询问天气，或需要为穿搭推荐获取天气数据时使用。

    Args:
        city: 城市名称，如"杭州"、"北京"、"上海"
        date: 查询日期，格式为 YYYY-MM-DD，或"今天"/"明天"/"后天"
    """
    try:
        result = await weather_service.get_weather(city, date)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


@tool
async def analyze_clothing_image(image_url: str, user_hint: Optional[str] = None) -> str:
    """分析衣服图片，提取衣物的名称、类别、颜色、材质、适合天气等信息。

    Args:
        image_url: 衣服图片的 OSS 签名 URL
        user_hint: 用户的补充描述（可选），帮助 LLM 更准确识别
    """
    try:
        # 使用通用的穿搭分析提示词
        prompt = (
            "请分析这张图片中的衣物属性，返回 JSON 格式："
            '{"name": "衣物名称", "category": "top/pants/outer/inner/accessory", '
            '"color": "主要颜色", "material": "材质", "temperature_range": "适合温度范围", '
            '"wear_method": "穿着方式", "scene": "适合场合"}'
        )
        if user_hint:
            prompt = f"{prompt}\n用户提示：{user_hint}"

        result = image_analyzer.analyze(image_url=image_url, prompt=prompt)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


@tool
async def remember_context(
    city: Optional[str] = None,
    scene: Optional[str] = None,
    date: Optional[str] = None,
    temperature: Optional[float] = None,
    style: Optional[str] = None,
    colors: Optional[str] = None,
) -> str:
    """记住当前对话中的关键信息（城市/场合/日期/温度/风格/颜色）。

    当用户在对话中提到这些信息时，调用此工具保存，以便后续穿搭推荐使用。

    Args:
        city: 城市名称
        scene: 场合类型（如 daily/work/sport/date/party/casual/formal）
        date: 日期（YYYY-MM-DD 或"今天"/"明天"等）
        temperature: 温度（℃），如果已知可传入
        style: 风格偏好（如 休闲/正式/运动等）
        colors: 常用颜色，逗号分隔（如"黑色,白色"）
    """
    try:
        # 从 ContextVar 获取当前 memory（由调用方传入，这里仅做验证）
        colors_list = [c.strip() for c in colors.split(",")] if colors else None
        return json.dumps({
            "status": "remembered",
            "remembered": {
                "city": city,
                "scene": scene,
                "date": date,
                "temperature": temperature,
                "style": style,
                "colors": colors_list,
            }
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


@tool
async def recall_context() -> str:
    """回忆已记住的上下文信息（城市/场合/日期/温度/风格/颜色）。

    在需要为用户推荐穿搭前，先调用此工具获取已记住的上下文。
    如果没有任何记住的信息，返回空的上下文对象。
    """
    try:
        # 返回一个空结果，示意调用方需要从 memory 中获取
        # 实际的 recall 由 AgentMemory.recall() 在 SupervisorAgent 中完成
        return json.dumps({
            "status": "recalled",
            "message": "请从 AgentMemory 中获取上下文"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


# ============================================================
# 工具列表（供 SupervisorAgent 注册）
# ============================================================

SHARED_TOOLS = [
    get_weather,
    analyze_clothing_image,
    remember_context,
    recall_context,
]
