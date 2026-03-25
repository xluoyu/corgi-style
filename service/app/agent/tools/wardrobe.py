"""衣柜工具（WardrobeTools）。

使用 @tool 装饰器（langchain_core.tools），每个 Tool 内部通过
get_db_for_tools() / get_current_user_id() 获取 DB 和用户。
"""
import asyncio
import json
from typing import Optional

from langchain_core.tools import tool

from app.agent.tools.context import get_db_for_tools, get_current_user_id


# ============================================================
# 工具实现
# ============================================================

@tool
async def search_wardrobe(category: Optional[str] = None, color: Optional[str] = None,
                          scene: Optional[str] = None) -> str:
    """搜索用户衣柜中的衣物，按类别、颜色或场合筛选。
    用于穿搭推荐前获取用户已有的衣物。"""
    try:
        from app.agent.graph.nodes.wardrobe import query_wardrobe
        db = get_db_for_tools()
        user_id = get_current_user_id()
        items = query_wardrobe(db, user_id, category=category, color=color, tags=None)
        result = []
        for item in items:
            result.append({
                "id": str(item.get("id", "")),
                "name": item.get("description", ""),
                "category": item.get("category", "unknown"),
                "color": item.get("color", ""),
                "material": item.get("material", ""),
                "image_url": item.get("image_url", ""),
                "generated_image_url": None,
                "temperature_range": item.get("temperature_range", ""),
                "scene": item.get("scene", ""),
                "wear_count": item.get("wear_count", 0),
            })
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


@tool
async def add_clothes_to_wardrobe(image_url: str, name: Optional[str] = None) -> str:
    """将衣物添加到用户衣柜（分析+生成卡通图+存储）。
    自动分析图片内容并生成卡通化效果。"""
    try:
        from app.agent.clothes_agent import clothes_agent
        from app.services.image_analysis import image_analyzer
        from app.services.image_generator import image_generator
        from app.models import UserClothes, ClothesCategory, TemperatureRange

        db = get_db_for_tools()
        user_id = get_current_user_id()

        # 并行分析 + 生成卡通图（两者都是同步方法，直接调用）
        analysis = image_analyzer.analyze(image_url=image_url)
        cartoon = image_generator.generate(reference_image_url=image_url)

        # 构建分析结果对象（模拟 ClothesAgent 的分析输出格式）
        class AnalysisResult:
            def __init__(self, data):
                for k, v in data.items():
                    setattr(self, k, v)

        # 存储到 DB（复用 clothes_agent 的方法）
        clothes = clothes_agent._create_clothes_record(
            db_session=db,
            user_id=user_id,
            image_url=image_url,
            result=AnalysisResult({
                "name": name or analysis.get("name", "未命名衣物"),
                "color": analysis.get("color"),
                "category": analysis.get("category"),
                "material": analysis.get("material"),
                "temperature_range": analysis.get("temperature_range"),
                "wear_method": analysis.get("wear_method"),
                "scene": analysis.get("scene"),
                "generated_image_url": cartoon,
                "completed_tasks": ["analysis", "generated_image"],
            })
        )

        return json.dumps({
            "clothes_id": str(clothes.id),
            "name": name or analysis.get("name", "未命名衣物"),
            "category": analysis.get("category"),
            "color": analysis.get("color"),
            "generated_image_url": cartoon,
            "analysis": analysis
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


# ============================================================
# 工具列表（供 SupervisorAgent 注册）
# ============================================================

WARDROBE_TOOLS = [
    search_wardrobe,
    add_clothes_to_wardrobe,
]
