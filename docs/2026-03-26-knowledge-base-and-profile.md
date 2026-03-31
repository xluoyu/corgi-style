# FashionSteward 知识库与用户画像方案

> 文档版本：v1.0
> 创建时间：2026-03-26
> 状态：待评审
> 补充自：implementation-plan-v2.md

---

## 一、穿搭知识库（Fashion Knowledge Base）

### 1.1 定位

穿搭知识库是 Agent 的"大脑"，为 OutfitAdvisor 和 WardrobeCurator 提供结构化的时尚领域知识，使 Agent 能够：

- 理解并定义各种风格
- 基于用户身体特征推荐合适款式
- 提供专业的色彩搭配建议
- 根据场合给出着装规范

### 1.2 知识库内容

```
穿搭知识库
│
├── 风格定义库（Style Definitions）
│   ├── 韩系简约：宽松、浅色、层次
│   ├── 美式休闲：舒适、运动、基础款
│   ├── 商务精英：深色、合身、精简
│   ├── 复古学院：格纹、领带、皮鞋
│   ├── 日系Clean：黑白灰、低饱和、基础廓形
│   ├── 街头潮流：Oversize、印花、亮色
│   ├── 轻奢通勤：质感面料、低调设计
│   ├── 文艺复古：格纹、灯芯绒、复古配色
│   └── 法式优雅：碎花、针织、慵懒感
│
├── 色彩系统（Color System）
│   ├── 基础色板（四季色彩理论）
│   ├── 互补色搭配规则
│   ├── 相近色搭配规则
│   ├── 中性色过渡规则
│   └── 肤色匹配指南
│
├── 身材适配指南（Body Fit Guide）
│   ├── 身材类型定义（苹果型/梨型/沙漏/H型/倒三角）
│   ├── 各类型推荐款式
│   ├── 各类型避雷款式
│   └── 视觉调整技巧（显高/显瘦/显比例）
│
├── 场合着装规范（Occasion Guide）
│   ├── 商务正式：深色西装、白衬衫
│   ├── 商务休闲：衬衫不解全扣、卡其裤
│   ├── 日常休闲：T恤、牛仔裤
│   ├── 约会穿搭：注意但不刻意、有亮点
│   └── 正式晚宴：礼服、配饰
│
└── 季节穿搭指南（Seasonal Guide）
    ├── 春：轻薄叠穿、多层次
    ├── 夏：透气材质、清爽配色
    ├── 秋：过渡单品、温度适应
    └── 冬：保暖层次、材质混搭
```

### 1.3 知识库实现：Python 模块（非数据库）

**设计决策**：知识库用 **Python 代码实现**（而非数据库），理由：

| | Python 模块 | 数据库 |
|---|---|---|
| 访问速度 | 快（内存读取） | 需 DB 查询 |
| 更新迭代 | 改代码即可 | 需迁移 |
| Agent 友好 | 直接函数调用 | 需构造查询 |
| 结构化程度 | 高（强类型） | 中（JSONB） |
| 扩展性 | 高 | 极高 |

知识库作为 Python 模块，Agent 通过函数调用访问：

```python
# app/agent/knowledge/base.py

from app.agent.knowledge.styles import STYLE_DEFINITIONS
from app.agent.knowledge.colors import COLOR_SYSTEM
from app.agent.knowledge.body import BODY_TYPE_GUIDE
from app.agent.knowledge.occasions import OCCASION_GUIDE


class FashionKnowledgeBase:
    """穿搭知识库——Agent 的时尚知识大脑"""

    # ============================================================
    # 风格相关
    # ============================================================

    @staticmethod
    def get_style_definition(style: str) -> dict:
        """获取风格定义"""
        return STYLE_DEFINITIONS.get(style.lower(), {})

    @staticmethod
    def search_styles(keywords: list[str]) -> list[dict]:
        """搜索匹配的风格"""
        results = []
        for style_name, style_def in STYLE_DEFINITIONS.items():
            # 基于关键词匹配
            tags = style_def.get("tags", []) + style_def.get("keywords", [])
            if any(kw.lower() in " ".join(tags).lower() for kw in keywords):
                results.append({**style_def, "name": style_name})
        return results

    @staticmethod
    def get_style_for_occasion(occasion: str) -> list[dict]:
        """获取适合某场合的风格"""
        results = []
        for style_name, style_def in STYLE_DEFINITIONS.items():
            if occasion in style_def.get("suitable_occasions", []):
                results.append({**style_def, "name": style_name})
        return results

    @staticmethod
    def get_style_for_body_type(body_type: str) -> dict:
        """获取适合某身材的风格建议"""
        suitable = []
        avoid = []
        for style_name, style_def in STYLE_DEFINITIONS.items():
            if body_type in style_def.get("suitable_body_types", []):
                suitable.append(style_name)
            if body_type in style_def.get("avoid_body_types", []):
                avoid.append(style_name)
        return {
            "suitable_styles": suitable,
            "avoid_styles": avoid
        }

    # ============================================================
    # 色彩相关
    # ============================================================

    @staticmethod
    def get_color_combinations(base_color: str) -> dict:
        """获取某种颜色的搭配方案"""
        return COLOR_SYSTEM.get(base_color.lower(), {})

    @staticmethod
    def get_colors_for_skin_tone(skin_tone: str) -> dict:
        """获取适合某种肤色的颜色建议"""
        return COLOR_SYSTEM["skin_tone_guide"].get(skin_tone.lower(), {})

    @staticmethod
    def suggest_color_palette(
        target_style: str = None,
        season: str = None,
        user_colors: list[str] = None
    ) -> list[str]:
        """推荐配色方案"""
        # 基于风格和季节推荐
        pass

    # ============================================================
    # 身材相关
    # ============================================================

    @staticmethod
    def get_body_type_guide(body_type: str) -> dict:
        """获取身材指南"""
        return BODY_TYPE_GUIDE.get(body_type.lower(), {})

    @staticmethod
    def get_styling_tips(concern: str) -> list[str]:
        """根据身材顾虑获取穿搭技巧"""
        # "显瘦" → 深色系、竖线条、高腰线...
        # "显高" → 高腰、短款、竖线条...
        concerns_map = {
            "显瘦": ["深色系为主", "避免膨胀材质（粗针织、亮面）",
                     "竖线条单品", "高腰设计", "合身剪裁"],
            "显高": ["高腰设计", "短款上衣",
                     "同色系搭配", "竖线条", "避免过长的下装"],
            "显比例": ["上短下长", "腰带强调腰线",
                      "避免五五分", "适当露肤"],
            "遮胯": ["A字裙/裤", "H版型下装",
                    "长款上衣盖住胯部", "避免紧身裤"],
            "遮臂": ["飞袖设计", "灯笼袖",
                    "宽松的袖子", "中长袖"],
        }
        return concerns_map.get(concern, [])

    @staticmethod
    def get_outfit_for_body_type(
        body_type: str,
        occasion: str = None,
        season: str = None
    ) -> list[dict]:
        """获取适合某种身材的穿搭模板"""
        guide = BODY_TYPE_GUIDE.get(body_type.lower(), {})
        templates = guide.get("outfit_templates", [])

        if occasion:
            templates = [t for t in templates if occasion in t.get("occasions", [])]
        if season:
            templates = [t for t in templates if season in t.get("seasons", [])]

        return templates

    # ============================================================
    # 场合相关
    # ============================================================

    @staticmethod
    def get_occasion_guide(occasion: str) -> dict:
        """获取场合着装指南"""
        return OCCASION_GUIDE.get(occasion.lower(), {})

    @staticmethod
    def check_outfit_appropriateness(
        outfit: dict,
        occasion: str,
        body_type: str = None
    ) -> dict:
        """
        检查穿搭对某场合的合适程度。
        这是 Agent 评价方案时的重要工具。
        """
        guide = OCCASION_GUIDE.get(occasion.lower(), {})

        issues = []
        score = 100

        # 检查正式度
        formal_level = outfit.get("formal_level", 5)
        guide_formal = guide.get("formal_level_range", [3, 7])
        if not (guide_formal[0] <= formal_level <= guide_formal[1]):
            issues.append(f"正式度（{formal_level}）不在合适范围（{guide_formal[0]}-{guide_formal[1]}）")
            score -= 20

        # 检查颜色
        colors = outfit.get("colors", [])
        guide_colors = guide.get("suitable_colors", [])
        if guide_colors:
            unsuitable = [c for c in colors if c not in guide_colors]
            if unsuitable:
                issues.append(f"颜色 {unsuitable} 不太适合此场合")
                score -= 10

        # 检查品类
        items = outfit.get("items", [])
        guide_items = guide.get("required_items", [])
        if guide_items:
            missing = [i for i in guide_items if i not in items]
            if missing:
                issues.append(f"缺少关键单品：{missing}")
                score -= 15

        return {
            "appropriate": score >= 70,
            "score": score,
            "issues": issues,
            "suggestions": [
                f"建议：{issue.replace('缺少', '添加').replace('颜色', '换成')}
" for issue in issues
            ]
        }
```

### 1.4 知识库内容示例

#### 1.4.1 风格定义库

```python
# app/agent/knowledge/styles.py

STYLE_DEFINITIONS = {
    "韩系简约": {
        "description": "以宽松版型、低饱和配色、多层次著称，强调干净利落和舒适感",
        "tags": ["韩系", "简约", "Clean", "Oversize"],
        "keywords": ["韩剧", "韩风", "男友风", "韩版"],
        "characteristics": {
            "colors": ["黑白灰", "浅蓝", "米白", "燕麦色", "浅驼色"],
            "avoid_colors": ["荧光色", "高饱和亮色", "大面积印花"],
            "silhouette": "上松下紧 or 上紧下松，避免全身宽松",
            "key_pieces": ["宽松T恤", "直筒裤", "廓形外套", "小白鞋"],
            "layering": "薄款叠穿为主，营造层次感",
        },
        "suitable_occasions": ["日常", "约会", "通勤"],
        "suitable_body_types": ["H型", "梨型", "倒三角"],
        "avoid_body_types": ["苹果型（大胸厚肩）"],
        "common_mistakes": [
            "全身Oversize显邋遢",
            "上下同时宽松没有线条",
            "颜色过暗显得没精神"
        ],
        "outfit_templates": [
            {
                "name": "韩系男友风",
                "items": ["白色圆领T恤", "深灰宽松T恤（叠穿）", "黑色直筒牛仔裤", "白色运动鞋"],
                "colors": ["白+灰+黑"],
                "formal_level": 3
            }
        ]
    },

    "商务精英": {
        "description": "低调质感的职场着装，强调合身剪裁和专业气场",
        "tags": ["商务", "精英", "职场", "Professional"],
        "keywords": ["上班", "职场", "开会", "通勤", "面试"],
        "characteristics": {
            "colors": ["深蓝", "藏青", "深灰", "黑", "白", "浅蓝"],
            "avoid_colors": ["荧光色", "大花纹", "牛仔"],
            "silhouette": "合身不紧身，肩线明确",
            "key_pieces": ["修身西装", "白衬衫", "西裤", "乐福鞋", "皮带"],
            "layering": "西装+衬衫为主，可加针织背心",
        },
        "suitable_occasions": ["上班", "商务", "面试", "正式场合"],
        "suitable_body_types": ["所有类型"],
        "avoid_body_types": [],
        "common_mistakes": [
            "西装过大显得不精神",
            "衬衫过紧不专业",
            "颜色过多显轻浮"
        ],
        "outfit_templates": [
            {
                "name": "经典商务",
                "items": ["白色衬衫", "深蓝色西装外套", "深灰西裤", "棕色皮鞋", "皮带"],
                "colors": ["白+深蓝+深灰"],
                "formal_level": 8
            }
        ]
    },

    "轻奢通勤": {
        "description": "介于商务和休闲之间，质感为先，低调有品",
        "tags": ["轻奢", "通勤", "质感", "Smart Casual"],
        "keywords": ["上班", "约会", "下班", "质感"],
        "characteristics": {
            "colors": ["驼色", "焦糖色", "浅灰", "藏蓝", "米白"],
            "avoid_colors": ["荧光色", "大面积logo"],
            "silhouette": "微宽松，舒适但不松垮",
            "key_pieces": ["羊毛大衣", "针织衫", "真丝衬衫", "吸烟裤", "切尔西靴"],
            "layering": "大衣+针织+衬衫，经典三件套",
        },
        "suitable_occasions": ["通勤", "约会", "下午茶", "看展"],
        "suitable_body_types": ["H型", "沙漏型", "苹果型"],
        "avoid_body_types": [],
        "common_mistakes": [
            "质感太差显得廉价",
            "过于正式像卖保险",
            "过于休闲不够得体"
        ],
        "outfit_templates": [
            {
                "name": "都市轻奢",
                "items": ["米白色针织开衫", "深藏蓝真丝衬衫", "焦糖色吸烟裤", "黑色切尔西靴"],
                "colors": ["米白+藏蓝+焦糖"],
                "formal_level": 6
            }
        ]
    },

    # ... 更多风格定义
}
```

#### 1.4.2 身材适配指南

```python
# app/agent/knowledge/body.py

BODY_TYPE_GUIDE = {
    "苹果型": {
        "description": "上半身（胸、腹、腰）偏胖，肩臀相对窄",
        "characteristics": ["胸部较丰满", "腰部圆润", "臀部相对窄", "腿部一般较细"],
        "recommendations": {
            "top": [
                "V领设计拉长脖颈，显脸小",
                "材质硬挺的外套，修饰身形",
                "避免高领、圆领（显胸大）",
                "A字版型的上衣",
                "深色上衣为主"
            ],
            "pants": [
                "高腰设计提升腰线",
                "直筒裤、阔腿裤修饰腿型",
                "避免紧身裤（暴露下身单薄）",
                "A字裙/伞裙平衡上下比例"
            ],
            "outer": [
                "H版型大衣",
                "长度过臀的中长款",
                "避免收腰设计"
            ],
            "avoid": [
                "紧身的上衣",
                "横条纹上衣",
                "腰部有装饰的设计",
                "短款上衣"
            ]
        },
        "outfit_templates": [
            {
                "name": "苹果型日常",
                "items": ["深色V领针织衫", "高腰直筒牛仔裤", "长款风衣"],
                "tips": ["V领显瘦", "高腰裤提升比例", "风衣盖住腰腹"]
            },
            {
                "name": "苹果型通勤",
                "items": ["V领衬衫", "A字半裙", "H版型西装外套"],
                "tips": ["V领衬衫正式但不显胖", "A字裙遮胯"]
            }
        ],
        "color_strategy": {
            "recommend": ["深色（藏青、深灰、黑）", "冷色调收缩感"],
            "avoid": ["浅色紧身上衣", "荧光色", "横纹"]
        }
    },

    "梨型": {
        "description": "下半身（胯、臀、腿）偏胖，上身相对瘦",
        "characteristics": ["肩窄", "腰细", "胯宽", "臀部丰满", "大腿粗"],
        "recommendations": {
            "top": [
                "有设计感的上衣，吸引视线到上半身",
                "泡泡袖、垫肩增加肩宽",
                "亮色上衣、图案上衣",
                "修身的针织衫",
                "大领口（方领、V领）"
            ],
            "pants": [
                "深色下装",
                "直筒裤、锥形裤",
                "A字裙、伞裙遮胯",
                "避免紧身裤"
            ],
            "outer": [
                "有肩线的外套",
                "浅色或亮色外套",
                "避免Oversize"
            ],
            "avoid": [
                "紧身裤",
                "浅色下装",
                "无肩线的软塌外套",
                "A字反穿（上窄下宽）"
            ]
        },
        "color_strategy": {
            "recommend": ["浅色上装", "深色下装", "上亮下暗"],
            "avoid": ["浅色紧身裤", "全身暗色（显沉闷）"]
        }
    },

    "H型": {
        "description": "肩、腰、胯宽度接近，身材曲线不明显",
        "characteristics": ["肩腰胯同宽", "没有明显腰线", "整体偏直板"],
        "recommendations": {
            "top": [
                "有曲线设计的上衣",
                "泡泡袖、收腰设计",
                "叠穿增加层次感",
                "材质对比（硬挺+柔软）"
            ],
            "pants": [
                "高腰裤",
                "A字裙",
                "阔腿裤",
                "任何能制造腰线的下装"
            ],
            "outer": [
                "收腰大衣",
                "腰带设计的外套",
                "系腰带的款式"
            ],
            "avoid": [
                "直筒没有腰线的连衣裙",
                "H版型外套",
                "上下同宽的单品叠加"
            ]
        },
        "color_strategy": {
            "recommend": ["强调腰线的配色", "上下颜色对比"],
            "avoid": ["全身同色（显平板）"]
        }
    },

    "沙漏型": {
        "description": "肩和胯宽，腰细，身材曲线明显",
        "characteristics": ["肩宽≈胯宽", "腰细", "曲线感强"],
        "recommendations": {
            "top": [
                "修身的衣服展示曲线",
                "V领、方领突出上半身",
                "避免过宽的肩部设计"
            ],
            "pants": [
                "包臀裙、鱼尾裙",
                "高腰裤",
                "紧身牛仔裤"
            ],
            "outer": [
                "收腰设计",
                "X版型大衣",
                "避免过于宽松"
            ],
            "avoid": [
                "Oversize",
                "H版型",
                "过于宽松掩盖曲线"
            ]
        },
        "color_strategy": {
            "recommend": ["修身的配色", "强调曲线的搭配"],
            "avoid": ["过于宽松掩盖身材"]
        }
    },

    "倒三角型": {
        "description": "肩宽背厚，下身相对瘦",
        "characteristics": ["肩宽>胯宽", "上身厚重", "腿细"],
        "recommendations": {
            "top": [
                "深色上衣",
                "避免泡泡袖、垫肩",
                "简洁的设计",
                "V领"
            ],
            "pants": [
                "浅色下装",
                "阔腿裤、喇叭裤",
                "A字裙",
                "任何吸引视线到下身的"
            ],
            "outer": [
                "深色外套",
                "简洁的肩线",
                "避免肩部有装饰"
            ],
            "avoid": [
                "泡泡袖",
                "垫肩",
                "横条纹上装",
                "高饱和色上装"
            ]
        },
        "color_strategy": {
            "recommend": ["上深下浅", "下身亮色"],
            "avoid": ["上半身亮色", "全身暗色"]
        }
    }
}
```

#### 1.4.3 场合着装规范

```python
# app/agent/knowledge/occasions.py

OCCASION_GUIDE = {
    "商务正式": {
        "description": "最高级别的职场着装，需要全套正装",
        "formal_level_range": [7, 10],
        "required_items": ["西装外套", "正装衬衫", "正装裤", "正式皮鞋"],
        "suitable_colors": ["深蓝", "藏青", "深灰", "黑", "白", "浅蓝"],
        "avoid_colors": ["牛仔蓝", "米白（太休闲）", "任何亮色"],
        "dress_code": "全套西装，领带可选",
        "key_rules": [
            "西装扣子：双排扣全扣，单排扣只扣上面一颗",
            "衬衫领口扣好",
            "皮鞋与皮带同色",
            "避免白袜子",
            "领带可选但建议有"
        ],
        "style_keywords": ["商务精英", "西装", "领带"]
    },

    "商务休闲": {
        "description": "Smart Casual，不需要全套正装但仍需得体",
        "formal_level_range": [5, 7],
        "required_items": ["有领上衣（衬衫或polo）", "裤装（卡其或深色休闲裤）", "皮鞋或乐福鞋"],
        "suitable_colors": ["浅蓝", "白", "米白", "卡其", "深灰", "藏蓝"],
        "avoid_colors": ["T恤", "运动裤", "人字拖", "大logo"],
        "dress_code": "有领上衣+休闲裤+皮鞋",
        "key_rules": [
            "衬衫不解超过2颗扣",
            "Polo领口扣好",
            "皮鞋款式简洁",
            "皮带必备"
        ],
        "style_keywords": ["通勤", "上班", "商务休闲", "Smart Casual"]
    },

    "约会": {
        "description": "注意但不刻意，有亮点但不张扬",
        "formal_level_range": [4, 6],
        "required_items": ["上衣（衬衫/针织衫/干净T恤）", "裤装", "干净的鞋子"],
        "suitable_colors": ["看你", "浅蓝", "白", "米白", "黑色"],
        "avoid_colors": ["全套黑（太压抑）", "全套运动装", "过于正式的商务装"],
        "dress_code": "干净整洁，有个人风格",
        "key_rules": [
            "第一印象很重要——整洁干净是底线",
            "有1个亮点即可（手表/香水/配色），不要堆砌",
            "鞋子的重要程度被低估——穿一双好鞋",
            "避免全身logo"
        ],
        "style_keywords": ["约会", "浪漫", "有型"]
    },

    "日常": {
        "description": "舒适自在，适合日常生活",
        "formal_level_range": [1, 4],
        "required_items": ["T恤/衬衫/针织衫", "牛仔裤/休闲裤", "运动鞋/休闲鞋"],
        "suitable_colors": ["任意（日常是最大的舞台）"],
        "avoid_colors": ["过于邋遢（破洞过多、变形）"],
        "dress_code": "舒适为主，保持整洁",
        "key_rules": [
            "舒适但不邋遢",
            "基础款也能穿出好效果",
            "配饰点睛",
            "适合当天的活动"
        ],
        "style_keywords": ["日常", "休闲", "出街", "周末"]
    },

    "正式场合": {
        "description": "婚礼、晚宴、典礼等正式社交场合",
        "formal_level_range": [8, 10],
        "required_items": ["礼服/西装", "正装衬衫", "正装鞋"],
        "suitable_colors": ["黑", "深蓝", "白", "银灰"],
        "avoid_colors": ["过于花哨", "休闲单品混入"],
        "dress_code": "礼服或深色西装",
        "key_rules": [
            "场合越正式，颜色越保守",
            "领结/领带必须有",
            "口袋方巾、袖扣可选",
            "香水但不过量"
        ],
        "style_keywords": ["晚宴", "婚礼", "典礼", "正式"]
    }
}
```

### 1.5 Agent 调用知识库的方式

```python
# OutfitAdvisor 内部调用示例

from app.agent.knowledge.base import FashionKnowledgeBase

class OutfitAdvisorAgent:

    def _build_planning_prompt(self, context: OutfitContext) -> str:
        """构建规划提示词（融合知识库）"""

        # 1. 获取身材适配建议
        body_type = context.user_profile.get("body_type")
        if body_type:
            body_guide = FashionKnowledgeBase.get_body_type_guide(body_type)
            body_tips = body_guide.get("recommendations", {})
            style_for_body = FashionKnowledgeBase.get_style_for_body_type(body_type)

        # 2. 获取场合规范
        occasion_guide = FashionKnowledgeBase.get_occasion_guide(context.target_scene)

        # 3. 获取风格定义（如果有目标风格）
        target_style = context.preferences.get("target_style")
        if target_style:
            style_def = FashionKnowledgeBase.get_style_definition(target_style)

        # 4. 融合到提示词
        prompt = f"""...
        【身材适配】
        身材类型：{body_type}
        推荐款式：{body_guide.get('recommendations', {}).get(context.target_scene, [])}
        避雷款式：{body_guide.get('avoid', [])}

        【场合规范】
        场合：{context.target_scene}
        正式度要求：{occasion_guide.get('formal_level_range', [])}
        适合颜色：{occasion_guide.get('suitable_colors', [])}
        避雷颜色：{occasion_guide.get('avoid_colors', [])}
        关键规则：{occasion_guide.get('key_rules', [])}

        【风格定义】
        目标风格：{target_style}
        特征：{style_def.get('characteristics', {})}
        关键单品：{style_def.get('characteristics', {}).get('key_pieces', [])}
        ...
        """
        return prompt
```

### 1.6 知识库文件结构

```
app/agent/knowledge/
├── __init__.py
├── base.py              ← FashionKnowledgeBase 统一访问接口
├── styles.py            ← 风格定义库
├── colors.py            ← 色彩系统
├── body.py              ← 身材适配指南
├── occasions.py          ← 场合着装规范
├── seasons.py            ← 季节穿搭指南
└── compatibility.py      ← 搭配兼容性矩阵（哪些风格可以混搭）
```

---

## 二、用户画像系统

### 2.1 定位

用户画像是 Agent 真正"认识用户"的基础。当前的 `user_profiles` 表只有 `gender`、`style_preferences` 等简单字段，远不够用。

我们需要收集：

| 字段 | 用途 | 获取方式 | 隐私敏感度 |
|------|------|---------|-----------|
| **年龄/年龄段** | 判断风格倾向 | 用户主动填写或推断 | 中 |
| **身高** | 显高/显矮建议 | 用户主动填写或推断 | 低 |
| **体重/体型** | 显瘦建议 | 用户主动填写或推断 | 中 |
| **职业** | 场合推荐 | 用户主动填写 | 低 |
| **肤色** | 颜色推荐 | 用户主动选择或AI分析 | 低 |
| **所在地区** | 天气+风格 | 从天气查询推断 | 低 |
| **穿衣预算** | 添置建议 | 用户主动填写 | 低 |
| **已有风格偏好** | 推荐方向 | 从行为推断 | 无 |

### 2.2 画像数据模型

#### 2.2.1 数据库层扩展

```sql
-- 扩展 user_profiles 表
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS age_range VARCHAR(20);
-- 值：under18 / 18-24 / 25-34 / 35-44 / 45-54 / over55

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS height_cm INT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS weight_kg INT;

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS body_type VARCHAR(50);
-- 值：苹果型 / 梨型 / H型 / 沙漏型 / 倒三角型 / 标准型 / 不确定

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS skin_tone VARCHAR(30);
-- 值：冷白 / 暖白 / 黄白 / 黄调 / 自然 / 暖棕 / 深棕

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS occupation_type VARCHAR(50);
-- 值：it互联网 / 金融 / 教育 / 医疗 / 设计 / 公务员 / 学生 / 自由职业 / 其他

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS work_dress_code VARCHAR(50);
-- 值：商务正式 / 商务休闲 / smart_casual / 休闲 / 自由着装

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS budget_level VARCHAR(20);
-- 值：基础 / 中端 / 高端 / 奢侈

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS location VARCHAR(50);
-- 值：城市名（用于天气查询）

ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS profile_completeness FLOAT DEFAULT 0.0;
-- 画像完整度（0-1），用于判断是否需要引导用户完善
```

#### 2.2.2 ORM 层

```python
# app/models/user_profile.py 扩展

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    gender = Column(String(20))                          # male/female/other
    style_preferences = Column(String)                   # JSON list
    season_preference = Column(String)                   # JSON list
    default_occasion = Column(String(50), default="casual")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ========== 新增字段 ==========

    # 基础信息
    age_range = Column(String(20))                        # "18-24" / "25-34" / etc.
    height_cm = Column(Integer)                          # 身高（厘米）
    weight_kg = Column(Integer)                          # 体重（公斤）
    occupation = Column(String(100))                    # 具体职业
    occupation_type = Column(String(50))                # 职业大类

    # 身材特征
    body_type = Column(String(50))                       # 身材类型
    skin_tone = Column(String(30))                      # 肤色
    budget_level = Column(String(20))                   # 穿衣预算

    # 工作相关
    work_dress_code = Column(String(50))                # 工作着装要求

    # 地理
    location = Column(String(50))                        # 常驻城市

    # 画像状态
    profile_completeness = Column(Float, default=0.0)   # 完整度

    user = relationship("User", back_populates="profile")

    # ========== 计算属性 ==========

    @property
    def bmi(self) -> float:
        """计算BMI"""
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    @property
    def height_category(self) -> str:
        """身高分类"""
        if not self.height_cm:
            return "unknown"
        if self.height_cm < 160:
            return "short"
        elif self.height_cm < 175:
            return "average"
        else:
            return "tall"

    def calculate_completeness(self) -> float:
        """计算画像完整度"""
        total_fields = 12
        filled = 0

        fields = [
            self.gender, self.age_range, self.height_cm,
            self.body_type, self.skin_tone, self.occupation,
            self.work_dress_code, self.budget_level,
            self.style_preferences, self.location,
            self.season_preference, self.default_occasion
        ]

        for f in fields:
            if f:
                filled += 1

        return round(filled / total_fields, 2)

    def to_agent_context(self) -> dict:
        """转化为 Agent 友好的上下文格式"""
        return {
            "basic": {
                "gender": self.gender,
                "age_range": self.age_range,
            },
            "body": {
                "height_cm": self.height_cm,
                "height_category": self.height_category,
                "weight_kg": self.weight_kg,
                "bmi": self.bmi,
                "body_type": self.body_type,
                "skin_tone": self.skin_tone,
            },
            "lifestyle": {
                "occupation": self.occupation,
                "occupation_type": self.occupation_type,
                "work_dress_code": self.work_dress_code,
                "location": self.location,
            },
            "preferences": {
                "budget_level": self.budget_level,
                "style_preferences": self.style_preferences,
                "season_preference": self.season_preference,
                "default_occasion": self.default_occasion,
            },
            "metadata": {
                "completeness": self.profile_completeness,
            }
        }
```

### 2.3 画像收集策略

#### 2.3.1 分阶段收集

```
用户首次使用
    │
    ▼
Step 1: 最小信息（1 分钟）
├── 性别：男 / 女 / 其他
├── 年龄段：18-24 / 25-34 / 35-44 / 45+
└── 职业类型：上班族 / 学生 / 自由职业 / 其他

Step 2: 完善信息（引导）
├── 身高、体重
├── 身材类型（AI 辅助判断 or 用户自选）
├── 肤色（图片识别 or 用户选择）
└── 穿衣预算

Step 3: 行为推断
├── 从穿搭历史推断风格偏好
├── 从反馈中推断讨厌的元素
├── 从行为中推断身材特征（拒绝"太长"→ 小个子）
```

#### 2.3.2 画像引导交互

```python
# app/agent/profile_manager.py

class ProfileManager:
    """
    用户画像管理器。
    负责：引导收集 → 存储 → 推断 → 供 Agent 使用
    """

    # 画像引导配置
    PROFILE_QUESTIONS = [
        {
            "key": "height_cm",
            "question": "方便告诉我您的身高吗？这样我能给出更合适的穿搭建议 😊",
            "type": "number",
            "unit": "cm",
            "placeholder": "例如：175"
        },
        {
            "key": "body_type",
            "question": "您觉得自己是什么身材类型呢？",
            "type": "choice",
            "options": [
                {"value": "苹果型", "desc": "上半身偏胖，腰腹圆润"},
                {"value": "梨型", "desc": "下半身偏胖，胯宽腿粗"},
                {"value": "H型", "desc": "肩腰胯差不多宽，曲线不明显"},
                {"value": "沙漏型", "desc": "肩宽胯宽，腰细"},
                {"value": "倒三角型", "desc": "肩宽，上身厚重下身瘦"},
                {"value": "标准型", "desc": "身材匀称，什么风格都能尝试"}
            ]
        },
        {
            "key": "skin_tone",
            "question": "您是什么肤色呢？这会影响穿搭颜色的推荐",
            "type": "choice",
            "options": [
                {"value": "冷白", "desc": "皮肤偏白，带粉色或蓝调"},
                {"value": "暖白", "desc": "皮肤白但带暖色调"},
                {"value": "黄白", "desc": "皮肤偏白但带黄调"},
                {"value": "黄调", "desc": "皮肤偏黄"},
                {"value": "自然色", "desc": "皮肤为自然的中间色调"},
                {"value": "暖棕", "desc": "皮肤为小麦色或暖棕色"},
                {"value": "深棕", "desc": "皮肤为深棕色或黑色"}
            ]
        },
        {
            "key": "work_dress_code",
            "question": "您上班对着装有要求吗？",
            "type": "choice",
            "options": [
                {"value": "商务正式", "desc": "需要穿正装"},
                {"value": "商务休闲", "desc": "smart casual，不能太随便"},
                {"value": "无要求", "desc": "随便穿，公司对着装没要求"}
            ]
        },
        {
            "key": "budget_level",
            "question": "您买衣服的预算大概在什么水平？",
            "type": "choice",
            "options": [
                {"value": "基础", "desc": "单件100-300元"},
                {"value": "中端", "desc": "单件300-800元"},
                {"value": "高端", "desc": "单件800-2000元"},
                {"value": "奢侈", "desc": "不设上限"}
            ]
        }
    ]

    def get_next_question(self, profile: UserProfile) -> Optional[dict]:
        """获取下一个需要填写的问题"""
        for q in self.PROFILE_QUESTIONS:
            key = q["key"]
            if getattr(profile, key) is None:
                return q
        return None

    def calculate_completeness(self, profile: UserProfile) -> float:
        """计算完整度"""
        total = len(self.PROFILE_QUESTIONS) + 3  # 基础字段 + 问题字段
        filled = 3  # gender, age_range, occupation 已初始化

        for q in self.PROFILE_QUESTIONS:
            if getattr(profile, q["key"]) is not None:
                filled += 1

        return round(filled / total, 2)

    def infer_body_type(self, profile: UserProfile) -> Optional[str]:
        """
        从身高体重推断身材类型（辅助，不是精确判断）。
        精确判断需要用户自填或 AI 分析图片。
        """
        if not profile.height_cm or not profile.weight_kg:
            return None

        bmi = profile.bmi
        height = profile.height_cm

        # 粗略推断（BMI + 身高）
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            if height < 165:
                return "标准型"
            else:
                return "H型"
        elif bmi < 28:
            return "标准型"
        else:
            return "偏胖"

        # 注意：这种推断不准确，应该引导用户自填
```

### 2.4 Agent 使用用户画像

```python
# OutfitAdvisor 使用画像的示例

class OutfitAdvisorAgent:

    def _build_planning_prompt(self, context: OutfitContext) -> str:

        # 从 context 获取用户画像
        profile = context.user_profile

        prompt_parts = []

        # 1. 身材信息 → 影响款式选择
        if profile.get("height_cm"):
            h = profile["height_cm"]
            if h < 165:
                prompt_parts.append(
                    f"【身材提醒】用户身高{h}cm，属于偏矮类型。"
                    f"建议：优先高腰线、短款单品、竖线条设计，避免过长的下装。"
                )
            elif h > 180:
                prompt_parts.append(
                    f"【身材提醒】用户身高{h}cm，属于高个子。"
                    f"建议：可以尝试Oversize、长款单品，但避免显矮的穿搭。"
                )

        if profile.get("body_type"):
            body_type = profile["body_type"]
            body_guide = FashionKnowledgeBase.get_body_type_guide(body_type)
            recommendations = body_guide.get("recommendations", {})

            prompt_parts.append(
                f"【身材类型】{body_type}身材。"
                f"推荐款式：{recommendations.get('top', [])[:3]}"
                f"避雷款式：{body_guide.get('avoid', [])[:3]}"
            )

        # 2. 肤色 → 影响颜色推荐
        if profile.get("skin_tone"):
            skin_tone = profile["skin_tone"]
            color_guide = FashionKnowledgeBase.get_colors_for_skin_tone(skin_tone)

            prompt_parts.append(
                f"【肤色适配】用户肤色为{skin_tone}。"
                f"推荐颜色：{color_guide.get('recommend', [])[:5]}"
                f"避雷颜色：{color_guide.get('avoid', [])[:3]}"
            )

        # 3. 工作着装要求 → 影响正式度
        if profile.get("work_dress_code"):
            dress_code = profile["work_dress_code"]
            if dress_code == "商务正式":
                prompt_parts.append(
                    "【工作要求】用户需要商务正式着装。"
                    "即使场合是'约会'或'日常'，整体风格仍应保持得体、稳重。"
                )
            elif dress_code == "无要求":
                prompt_parts.append(
                    "【工作要求】用户工作对着装无要求，穿搭可以更自由发挥。"
                )

        # 4. 职业 → 影响风格倾向
        if profile.get("occupation_type"):
            occ = profile["occupation_type"]
            style_hint = {
                "it互联网": "可以偏休闲技术风，但见人时建议提升正式度",
                "金融": "建议偏商务风格，建立专业形象",
                "教育": "建议知性、亲和的风格",
                "设计": "可以更有个人风格，但避免过于夸张",
                "学生": "可以偏休闲、活力，尝试多种风格",
                "自由职业": "自由度最高，可以根据当天活动选择",
            }.get(occ, "")

            if style_hint:
                prompt_parts.append(f"【职业参考】{style_hint}")

        # 5. 预算 → 影响添置建议
        if profile.get("budget_level"):
            budget = profile["budget_level"]
            prompt_parts.append(
                f"【预算参考】用户穿衣预算为{budget}级别。"
                f"添置建议应在该预算范围内。"
            )

        # 6. 肤色 + 风格 → 推荐配色
        if profile.get("skin_tone") and profile.get("preferred_styles"):
            colors = FashionKnowledgeBase.get_colors_for_skin_tone(profile["skin_tone"])
            prompt_parts.append(
                f"【配色建议】根据肤色推荐：{colors.get('recommend', [])[:3]}色系"
            )

        return "\n\n".join(prompt_parts)
```

### 2.5 画像与偏好学习的融合

用户画像和偏好学习是两个独立的用户数据体系，它们服务于不同的目的：

```
用户画像（UserProfile）
├── 静态信息（身高、体重、职业等）
├── 用户主动填写
└── 用途：生成时的硬约束（"小个子不能穿长风衣"）

偏好学习（UserPreferences）
├── 动态信息（喜欢的颜色、讨厌的风格）
├── 从行为中推断
└── 用途：方案排序和过滤（"优先推荐蓝色系"）

两者互相补充：
- 画像告诉 Agent "能穿什么"
- 偏好告诉 Agent "想穿什么"
- Agent 在两者之间找到平衡
```

```python
# OutfitAdvisor 中融合两者

@dataclass
class OutfitContext:
    # ... 现有字段 ...
    user_profile: Dict = {}     # 用户画像（静态）
    preferences: Dict = {}      # 用户偏好（动态）

    def to_agent_dict(self) -> Dict:
        """转化为完整的 Agent 上下文"""
        return {
            "profile": self.user_profile,  # 静态约束
            "preferences": self.preferences,  # 动态偏好
            "constraints": self._build_constraints(),  # 硬约束
        }

    def _build_constraints(self) -> Dict:
        """从画像中提取硬约束"""
        constraints = {}

        # 身材硬约束
        if self.user_profile.get("height_cm", 0) < 165:
            constraints["max_outer_length"] = "膝盖以上"
            constraints["avoid"] = ["超长风衣", "拖地裤"]

        if self.user_profile.get("body_type") == "苹果型":
            constraints["avoid"] = constraints.get("avoid", []) + ["紧身T恤", "横纹上衣"]

        # 预算硬约束
        budget = self.user_profile.get("budget_level")
        if budget == "基础":
            constraints["avoid_items"] = ["奢侈品", "设计师品牌"]

        # 工作着装硬约束
        if self.user_profile.get("work_dress_code") == "商务正式":
            constraints["min_formal_level"] = 6

        return constraints
```

---

## 三、整合后的完整架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent 层                                       │
│                                                                 │
│  SupervisorAgent                                                 │
│    │                                                            │
│    ├──→ OutfitAdvisor Agent                                      │
│    │         穿搭推理（使用知识库 + 用户画像 + 偏好）           │
│    │                                                           │
│    └──→ WardrobeCurator Agent                                   │
│              衣橱管理（使用知识库 + 用户画像）                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    知识层（FashionKnowledgeBase）                  │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ 风格定义库    │ │ 色彩系统      │ │ 身材适配指南  │            │
│  │              │ │              │ │              │            │
│  │ 15+种风格    │ │ 肤色配色      │ │ 5种身材类型  │            │
│  │ 详细定义     │ │ 互补/相近色   │ │ 视觉调整     │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐                            │
│  │ 场合着装规范  │ │ 季节穿搭指南  │                             │
│  │              │ │              │                            │
│  │ 正式度评分   │ │ 温度适应     │                             │
│  │ 颜色规则     │ │ 材质推荐     │                             │
│  └──────────────┘ └──────────────┘                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    用户数据层                                    │
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────────┐   │
│  │     UserProfile         │  │     UserPreferences          │   │
│  │     用户画像（静态）      │  │     用户偏好（动态）          │   │
│  │                        │  │                            │   │
│  │ · 身高/体重/体型        │  │ · 喜欢的颜色                │   │
│  │ · 肤色                 │  │ · 讨厌的风格                │   │
│  │ · 职业/工作着装         │  │ · 隐性偏好（从行为推断）     │   │
│  │ · 预算/地区            │  │ · 置信度                    │   │
│  │ · 画像完整度           │  │                              │   │
│  └────────────────────────┘  └────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    数据存储层                                    │
│                                                                 │
│  PostgreSQL                                                      │
│  · user_profiles（扩展）                                        │
│  · user_preferences（偏好学习）                                  │
│  · preference_feedbacks                                          │
│  · clothing_items                                               │
│  · outfit_histories                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/agent/knowledge/__init__.py` | 知识库模块入口 |
| `app/agent/knowledge/base.py` | FashionKnowledgeBase 统一接口 |
| `app/agent/knowledge/styles.py` | 风格定义库（15+种风格） |
| `app/agent/knowledge/colors.py` | 色彩系统 |
| `app/agent/knowledge/body.py` | 身材适配指南（5种身材） |
| `app/agent/knowledge/occasions.py` | 场合着装规范 |
| `app/agent/knowledge/seasons.py` | 季节穿搭指南 |
| `app/agent/profile_manager.py` | 用户画像管理器 |
| `app/routers/profile.py` | 画像相关 API（获取/更新/引导） |

### 修改文件

| 文件 | 说明 |
|------|------|
| `app/models/user_profile.py` | 扩展字段（身高/体重/肤色/职业等） |
| `service/schema.sql` | 扩展 user_profiles 表 |
| `app/agent/outfit_advisor.py` | 融合知识库 + 用户画像到规划提示词 |
| `app/agent/wardrobe_curator.py` | 使用身材指南进行搭配推荐 |
| `app/agent/protocol.py` | OutfitContext 扩展 user_profile 字段 |

---

## 五、实施计划

| 阶段 | 任务 | 周数 |
|------|------|------|
| **Phase 3（扩展）** | | |
| T3.1 | 知识库基础框架 + 风格定义库 | 0.5 周 |
| T3.2 | 身材适配指南 + 场合规范 | 0.5 周 |
| T3.3 | 用户画像数据模型扩展 | 0.5 周 |
| T3.4 | ProfileManager 画像管理器 | 0.5 周 |
| T3.5 | 画像引导交互 API | 0.5 周 |
| T3.6 | Agent 融合知识库 + 画像（OutfitAdvisor） | 1 周 |
| **合计** | | **3.5 周** |

---

## 六、知识库迭代策略

知识库不是一次性建完的，需要持续迭代：

### 6.1 冷启动（v1.0）

- 定义 10-15 种主流风格
- 覆盖 5 种身材类型
- 覆盖主要场合

### 6.2 扩展（v1.1+）

- 增加更多细分风格（如"City Boy"、"Old Money"、"Clean Fit"）
- 增加地域特色风格（如"日系"、"韩系"、"欧美"细分）
- 增加季节性专题（如"梅雨季穿搭"、"滑雪穿搭"）

### 6.3 持续优化

- 从用户反馈中学习：用户说"不准确" → 更新知识库
- 从数据中学习：某种风格在某地区流行 → 更新知识库
- 从专家中学习：时尚编辑/造型师建议 → 更新知识库

---

*知识库与用户画像方案结束*
