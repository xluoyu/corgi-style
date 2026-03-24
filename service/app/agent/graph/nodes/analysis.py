"""衣柜分析节点"""
from collections import defaultdict
from typing import Dict, List
from app.agent.graph.state import GraphState

# 所有品类的枚举
ALL_CATEGORIES = ["top", "pants", "outer", "inner", "accessory"]

# 品类中文名映射
CATEGORY_NAMES = {
    "top": "上衣",
    "pants": "裤子",
    "outer": "外套",
    "inner": "内搭",
    "accessory": "配饰"
}


async def wardrobe_analysis_node(state: GraphState) -> GraphState:
    """
    衣柜分析节点

    分析用户衣柜中有哪些品类、缺失哪些品类，
    为后续 LLM 规划提供准确的库存信息。
    """
    user_clothes = state.get("user_clothes", [])

    # 按品类分组
    by_category: Dict[str, List] = defaultdict(list)
    for c in user_clothes:
        cat = c.get("category", "unknown")
        by_category[cat].append(c)

    # 可用品类
    available_categories = [cat for cat in ALL_CATEGORIES if cat in by_category and by_category[cat]]

    # 缺失品类
    missing_categories = [cat for cat in ALL_CATEGORIES if cat not in available_categories]

    state["wardrobe_by_category"] = dict(by_category)
    state["available_categories"] = available_categories
    state["missing_categories"] = missing_categories

    return state
