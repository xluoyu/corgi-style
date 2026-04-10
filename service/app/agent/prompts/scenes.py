"""不同场景的 prompt 变体"""
from typing import Dict, Any


def get_outfit_generation_prompt(context: Dict[str, Any]) -> str:
    """穿搭生成场景的 prompt"""
    return f"""用户请求生成穿搭。

当前上下文：
- 日期：{context.get('date', '未知')}
- 地点：{context.get('location', '未知')}
- 场合：{context.get('occasion', '日常')}
- 温度：{context.get('temperature', '未知')}°C

请按以下步骤执行：
1. 如果没有天气信息，调用 get_weather
2. 查询用户衣柜（search_wardrobe）
3. 根据衣柜现有衣物生成搭配方案
4. 如果衣柜衣物不足，告知用户缺少什么
"""


def get_style_recommendation_prompt(style_name: str, context: Dict[str, Any]) -> str:
    """风格推荐场景的 prompt"""
    return f"""用户请求风格化推荐：{style_name}

1. 先获取该风格的详细信息（get_style_info）
2. 查询用户衣柜中与该风格匹配的衣物
3. 如果衣柜缺少关键衣物，提示用户
4. 生成符合该风格的搭配方案
"""


def get_image_analysis_prompt(has_command: bool = False) -> str:
    """图片分析场景的 prompt"""
    if has_command:
        return """用户上传了图片并给出了命令（如"入库"、"搭配"）。
请先分析图片，然后根据用户命令执行相应操作。"""
    else:
        return """用户上传了图片但没有给出明确命令。
请先分析图片，识别衣物属性，然后询问用户想要执行什么操作（入库/搭配/风格迁移）。
"""


def get_wardrobe_management_prompt(action: str) -> str:
    """衣橱管理场景的 prompt"""
    actions = {
        "add": """用户想要添加衣物到衣柜。
请确认衣物信息（名称、品类等），然后调用 add_to_wardrobe。""",
        "search": """用户想要查询衣柜。
调用 search_wardrobe 获取衣物列表。""",
        "delete": """用户想要删除衣物。
请确认要删除的衣物ID。""",
    }
    return actions.get(action, "未知操作")
