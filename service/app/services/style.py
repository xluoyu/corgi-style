"""风格知识库服务"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_


@dataclass
class StyleKnowledge:
    """风格知识"""
    id: str
    name: str
    description: str
    tags: List[str]
    rules: Dict[str, Any]  # 搭配规则
    colors: List[str]  # 主色调
    occasion: Optional[str] = None  # 适用场合
    season: Optional[str] = None  # 适用季节
    temperature_range: Optional[str] = None  # 适用温度
    is_builtin: bool = True


@dataclass
class UserStyle:
    """用户自定义风格"""
    name: str
    description: str
    tags: List[str]
    rules: Dict[str, Any]
    colors: List[str]


# 预设内置风格
BUILTIN_STYLES = {
    "美式复古": StyleKnowledge(
        id="builtin_1",
        name="美式复古",
        description="20世纪50-70年代美国风格，代表元素：牛仔、工装、丹宁",
        tags=["牛仔", "工装", "复古", "丹宁", "皮带", "靴子"],
        rules={
            "base_items": ["牛仔外套", "工装裤", "白色T恤", "皮靴"],
            "color_palette": ["深蓝", "浅蓝", "白色", "卡其", "棕色"],
            "patterns": ["条纹", "格子", "丹宁"],
            "accessories": ["皮带", "棒球帽", "工装靴"]
        },
        colors=["深蓝", "浅蓝", "白色", "卡其", "棕色"],
        occasion="daily",
        season="spring_autumn"
    ),
    "日系简约": StyleKnowledge(
        id="builtin_2",
        name="日系简约",
        description="日本街头简约风格，强调基础款、棉麻、素色",
        tags=["基础款", "棉麻", "素色", "宽松", "文艺"],
        rules={
            "base_items": ["衬衫", "针织衫", "休闲裤", "帆布鞋"],
            "color_palette": ["白色", "米色", "灰色", "藏蓝", "军绿"],
            "patterns": ["纯色", "细条纹"],
            "accessories": ["帆布包", "渔夫帽"]
        },
        colors=["白色", "米色", "灰色", "藏蓝", "军绿"],
        occasion="daily",
        season="all_season"
    ),
    "韩系通勤": StyleKnowledge(
        id="builtin_3",
        name="韩系通勤",
        description="韩国时尚通勤风格，精致但不夸张",
        tags=["通勤", "精致", "西装裤", "衬衫", "高跟鞋"],
        rules={
            "base_items": ["衬衫", "西装裤", "针织开衫", "乐福鞋"],
            "color_palette": ["白色", "黑色", "灰色", "浅粉", "浅蓝"],
            "patterns": ["纯色", "微条纹"],
            "accessories": ["手表", "简约包包"]
        },
        colors=["白色", "黑色", "灰色", "浅粉", "浅蓝"],
        occasion="work",
        season="all_season"
    ),
    "街头潮流": StyleKnowledge(
        id="builtin_4",
        name="街头潮流",
        description="年轻街头风格，宽松、个性、有态度",
        tags=["宽松", "印花", "卫衣", "运动裤", "球鞋"],
        rules={
            "base_items": ["卫衣", "运动裤", "棒球帽", "球鞋"],
            "color_palette": ["黑色", "白色", "红色", "荧光绿", "灰色"],
            "patterns": ["大印花", "logo", "拼接"],
            "accessories": ["棒球帽", "双肩包", "耳机"]
        },
        colors=["黑色", "白色", "红色", "荧光绿", "灰色"],
        occasion="daily",
        season="all_season"
    ),
    "文艺清新": StyleKnowledge(
        id="builtin_5",
        name="文艺清新",
        description="文艺气质风格，碎花、蕾丝、自然",
        tags=["碎花", "蕾丝", "连衣裙", "草编", "自然"],
        rules={
            "base_items": ["碎花裙", "蕾丝上衣", "草编帽", "帆布鞋"],
            "color_palette": ["白色", "浅黄", "浅绿", "粉色", "淡蓝"],
            "patterns": ["碎花", "波点", "格纹"],
            "accessories": ["草编帽", "帆布包", "细项链"]
        },
        colors=["白色", "浅黄", "浅绿", "粉色", "淡蓝"],
        occasion="date",
        season="summer"
    ),
    "商务正装": StyleKnowledge(
        id="builtin_6",
        name="商务正装",
        description="正式商务场合着装",
        tags=["西装", "衬衫", "领带", "皮鞋", "正式"],
        rules={
            "base_items": ["西装", "衬衫", "西裤", "皮鞋"],
            "color_palette": ["黑色", "深灰", "深蓝", "白色"],
            "patterns": ["纯色", "细条纹"],
            "accessories": ["领带", "领夹", "皮带"]
        },
        colors=["黑色", "深灰", "深蓝", "白色"],
        occasion="work",
        season="all_season"
    ),
}


class StyleService:
    """风格服务"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_style_knowledge(self, style_name: str) -> Optional[StyleKnowledge]:
        """
        获取风格知识

        Args:
            style_name: 风格名称

        Returns:
            风格知识，如果不存在返回 None
        """
        # 先查内置风格
        if style_name in BUILTIN_STYLES:
            return BUILTIN_STYLES[style_name]

        # 查数据库用户自定义风格
        if self.db:
            from app.models.style import StyleKnowledgeModel
            style = self.db.query(StyleKnowledgeModel).filter(
                and_(
                    StyleKnowledgeModel.name == style_name,
                    StyleKnowledgeModel.is_builtin == False
                )
            ).first()

            if style:
                return self._model_to_knowledge(style)

        return None

    def list_builtin_styles(self) -> List[str]:
        """列出所有内置风格名称"""
        return list(BUILTIN_STYLES.keys())

    def list_all_styles(self) -> List[str]:
        """列出所有可用风格（内置 + 用户自定义）"""
        styles = list(BUILTIN_STYLES.keys())

        if self.db:
            from app.models.style import StyleKnowledgeModel
            user_styles = self.db.query(StyleKnowledgeModel).filter(
                StyleKnowledgeModel.is_builtin == False
            ).all()
            styles.extend([s.name for s in user_styles])

        return styles

    def save_user_style(self, user_id: str, style: UserStyle) -> StyleKnowledge:
        """
        保存用户自定义风格

        Args:
            user_id: 用户 ID
            style: 风格数据

        Returns:
            保存的风格知识
        """
        if not self.db:
            raise ValueError("需要数据库会话来保存用户风格")

        from app.models.style import StyleKnowledgeModel

        # 检查是否已存在
        existing = self.db.query(StyleKnowledgeModel).filter(
            and_(
                StyleKnowledgeModel.name == style.name,
                StyleKnowledgeModel.user_id == UUID(user_id)
            )
        ).first()

        if existing:
            # 更新
            existing.description = style.description
            existing.tags = json.dumps(style.tags)
            existing.rules = json.dumps(style.rules)
            existing.colors = json.dumps(style.colors)
            model = existing
        else:
            # 创建
            model = StyleKnowledgeModel(
                name=style.name,
                description=style.description,
                tags=json.dumps(style.tags),
                rules=json.dumps(style.rules),
                colors=json.dumps(style.colors),
                is_builtin=False,
                user_id=UUID(user_id)
            )
            self.db.add(model)

        self.db.commit()
        self.db.refresh(model)

        return self._model_to_knowledge(model)

    def apply_style(
        self,
        style_name: str,
        items: List[Any],
        context: Optional[Any] = None
    ) -> List[Any]:
        """
        将风格规则应用于衣物列表

        Args:
            style_name: 风格名称
            items: 衣物列表
            context: 可选的上下文

        Returns:
            调整后的衣物列表
        """
        style = self.get_style_knowledge(style_name)
        if not style:
            return items

        # 简单实现：按风格标签过滤和排序
        filtered = []
        style_tags = set(style.tags)

        for item in items:
            # 检查衣物标签是否与风格匹配
            item_tags = set(item.tags) if hasattr(item, "tags") else set()
            if item_tags & style_tags:  # 有交集
                filtered.append(item)

        # 如果过滤后为空，返回原列表
        return filtered if filtered else items

    def _model_to_knowledge(self, model) -> StyleKnowledge:
        """将数据库模型转为 StyleKnowledge"""
        tags = json.loads(model.tags) if isinstance(model.tags, str) else (model.tags or [])
        rules = json.loads(model.rules) if isinstance(model.rules, str) else (model.rules or {})
        colors = json.loads(model.colors) if isinstance(model.colors, str) else (model.colors or [])

        return StyleKnowledge(
            id=str(model.id),
            name=model.name,
            description=model.description or "",
            tags=tags,
            rules=rules,
            colors=colors,
            occasion=model.occasion,
            season=model.season,
            temperature_range=model.temperature_range,
            is_builtin=model.is_builtin
        )


def get_style_knowledge(style_name: str, db: Optional[Session] = None) -> Optional[StyleKnowledge]:
    """便捷函数：获取风格知识"""
    service = StyleService(db)
    return service.get_style_knowledge(style_name)


def list_builtin_styles() -> List[str]:
    """便捷函数：列出内置风格"""
    service = StyleService()
    return service.list_builtin_styles()


def apply_style(
    style_name: str,
    items: List[Any],
    context: Optional[Any] = None,
    db: Optional[Session] = None
) -> List[Any]:
    """便捷函数：应用风格"""
    service = StyleService(db)
    return service.apply_style(style_name, items, context)
