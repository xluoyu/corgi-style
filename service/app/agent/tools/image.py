"""图片分析工具"""
import json
from typing import Optional
from langchain_core.tools import tool

from app.services.image_analysis import (
    analyze_clothing_image,
    analyze_outfit_image,
    ClothingAttrs,
    OutfitAnalysisResult
)
from app.agent.memory import update_session_memory


@tool
async def analyze_clothing(image_url: str, session_id: str = "", user_id: str = "") -> str:
    """
    分析单件衣物图片，提取品类/颜色/风格等属性。

    Args:
        image_url: 图片 URL
        session_id: 会话 ID
        user_id: 用户 ID

    Returns:
        JSON 格式的衣物属性
    """
    try:
        result = await analyze_clothing_image(image_url)

        # 更新短期记忆
        if session_id:
            await update_session_memory(
                session_id,
                pending_image=image_url,
                image_attrs={
                    "name": result.name,
                    "category": result.category,
                    "color": result.color,
                    "material": result.material,
                    "style": result.style,
                    "temperature_range": result.temperature_range,
                    "scene": result.scene,
                    "tags": result.tags
                } if isinstance(result, ClothingAttrs) else result.__dict__,
                user_id=user_id
            )

        return json.dumps({
            "success": True,
            "attrs": result.__dict__ if hasattr(result, '__dict__') else result,
            "message": f"识别为：{result.name or result.category}"
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def analyze_outfit(image_url: str, session_id: str = "", user_id: str = "") -> str:
    """
    分析整套穿搭图片，提取风格要素和搭配结构。

    用于"找类似搭配"场景：用户上传一套喜欢的穿搭，AI 分析后从用户衣柜匹配相似单品。

    Args:
        image_url: 整套穿搭图片 URL
        session_id: 会话 ID
        user_id: 用户 ID

    Returns:
        JSON 格式的风格分析结果
    """
    try:
        result = await analyze_outfit_image(image_url)

        # 更新短期记忆
        if session_id:
            await update_session_memory(
                session_id,
                pending_outfit_image=image_url,
                outfit_analysis={
                    "overall_style": result.overall_style,
                    "items": result.items,
                    "style_tags": result.style_tags,
                    "color_palette": result.color_palette,
                    "description": result.description
                } if isinstance(result, OutfitAnalysisResult) else result.__dict__,
                user_id=user_id
            )

        return json.dumps({
            "success": True,
            "analysis": {
                "overall_style": result.overall_style,
                "items": result.items,
                "style_tags": result.style_tags,
                "color_palette": result.color_palette,
                "description": result.description
            },
            "message": f"识别为 {result.overall_style} 风格，包含 {len(result.items)} 件单品"
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def create_image_tools():
    """创建图片分析相关工具列表"""
    return [analyze_clothing, analyze_outfit]
