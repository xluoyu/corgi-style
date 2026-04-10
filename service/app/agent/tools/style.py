"""风格相关工具"""
import json
from typing import Optional, List
from langchain_core.tools import tool

from app.services.style import (
    get_style_knowledge,
    list_builtin_styles,
    apply_style,
    StyleKnowledge
)


@tool
async def get_style_info(style_name: str) -> str:
    """
    获取指定风格的详细信息和搭配规则。

    Args:
        style_name: 风格名称（如"美式复古"、"日系简约"）

    Returns:
        JSON 格式的风格知识
    """
    try:
        style = get_style_knowledge(style_name)

        if not style:
            return json.dumps({
                "error": f"未找到风格：{style_name}",
                "available_styles": list_builtin_styles()
            }, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "style": {
                "name": style.name,
                "description": style.description,
                "tags": style.tags,
                "rules": style.rules,
                "colors": style.colors,
                "occasion": style.occasion,
                "season": style.season
            }
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def list_available_styles() -> str:
    """
    列出所有可用的预设风格。

    Returns:
        JSON 格式的风格列表
    """
    try:
        styles = list_builtin_styles()
        return json.dumps({
            "success": True,
            "styles": styles,
            "count": len(styles)
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
async def apply_style_to_items(
    style_name: str,
    item_ids: str = ""  # JSON 数组格式的衣物 ID 列表
) -> str:
    """
    将指定风格应用于衣物列表。

    Args:
        style_name: 风格名称
        item_ids: 衣物 ID 列表（JSON 数组格式）

    Returns:
        JSON 格式的调整后搭配结果
    """
    try:
        style = get_style_knowledge(style_name)
        if not style:
            return json.dumps({
                "error": f"未找到风格：{style_name}"
            }, ensure_ascii=False)

        # 解析衣物 ID
        item_list = []
        if item_ids:
            try:
                item_list = json.loads(item_ids)
            except json.JSONDecodeError:
                pass

        # 注意：这里需要从数据库加载衣物详情
        # 目前返回风格规则，实际使用需要结合衣柜数据
        return json.dumps({
            "success": True,
            "style": style_name,
            "applied_rules": style.rules,
            "suggested_colors": style.colors,
            "message": f"已应用 {style_name} 风格规则"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def create_style_tools():
    """创建风格相关工具列表"""
    return [get_style_info, list_available_styles, apply_style_to_items]
