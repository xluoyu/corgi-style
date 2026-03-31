# FashionSteward 技术实施方案

> 文档版本：v1.0
> 创建时间：2026-03-26
> 状态：待评审
> 基于：PRD-fashion-steward-v1.0.md

---

## 一、技术现状评估

### 1.1 现有可复用资产

| 资产 | 可复用程度 | 说明 |
|------|-----------|------|
| SupervisorAgent (llm.bind_tools) | ✅ 核心复用 | 现有 `run_stream()` 循环是完美的基础，只需扩展 |
| 9 个现有 Tools | ✅ 大部分复用 | `search_wardrobe`、`plan_outfit`、`analyze_clothing_image` 等可直接复用 |
| ContextVar DB 注入 | ✅ 直接复用 | `get_db_for_tools()` / `get_current_user_id()` 已就绪 |
| AgentMemory | ⚠️ 需扩展 | 现有字段（city/scene/temperature）够用，需扩展偏好字段 |
| DialogueSessionManager | ✅ 直接复用 | 分层存储（内存+PostgreSQL），3天TTL |
| SSE 流式响应 | ✅ 直接复用 | `run_stream()` 已支持 6 种事件类型 |
| LLM Provider 抽象 | ✅ 直接复用 | 支持多后端，text/vision 模型分离 |
| 衣物分析 + 卡通化 | ✅ 直接复用 | `image_analyzer` + `image_generator` |
| 旧版 Supervisor | ❌ 废弃 | LangGraph 方案逐步废弃 |

### 1.2 现有架构与 PRD 目标的差距

| PRD 目标 | 现有差距 | 优先级 |
|---------|---------|--------|
| 多轮迭代优化 | 当前 `run_stream` 支持但反馈处理逻辑缺失 | P0 |
| 偏好学习 | AgentMemory 缺少偏好字段，DB 缺少偏好表 | P0 |
| 搭配兼容性搜索 | `search_wardrobe` 只有精确筛选，缺少语义匹配 | P0 |
| 有主见的审美 | `plan_outfit` 的 PLANNING_SYSTEM_PROMPT 过于简单 | P1 |
| 参考图风格复刻 | 缺少风格分析 + 衣柜匹配联动能力 | P1 |
| WardrobeCurator 主动提醒 | 无主动服务机制，只有被动响应 | P1 |
| GarmentCare 衣物护理 | 无材质知识和护理能力 | P2 |
| 搭配评价 | 无独立的方案评价能力 | P1 |

### 1.3 技术架构决策

**核心决策：不引入多 Agent LLM 调用，改用"增强 Tool"模式**

PRD 中三个专业角色（OutfitAdvisor / WardrobeCurator / GarmentCare）在技术上有两种实现路径：

| 方案 | 实现方式 | 优点 | 缺点 |
|------|---------|------|------|
| **A：多 LLM Agent** | 每个角色独立 LLM 实例，Supervisor 调用时构造 `HumanMessage` 发给子 Agent | 完全符合 PRD 的"真正的 Agent"定义 | 每次穿搭多 1-2 次 LLM 调用，成本翻倍；Agent 间协调复杂度高 |
| **B：增强 Tool + 丰富 Prompt** | 每个角色是一个带强 System Prompt 的 Tool 函数，内部调用一次 LLM | 复用现有 `run_stream()` 循环；单次 LLM 调用；改动最小 | 不够"Agent"，但 PRD 的 D1 决策已经论证过——当前场景不需要真正的多 Agent |
| **C：混合方案（推荐）** | OutfitAdvisor 用方案 B + 专门的反馈解析 Tool；WardrobeCurator 用方案 B；GarmentCare 直接用 Tool | 成本可控，体验接近方案 A；逐步演进 | 需要判断哪些能力值得"增强" |

**推荐方案 C**。理由：

1. 现有 SupervisorAgent 的 `run_stream()` 循环已经完美支持多轮对话
2. PRD D1 决策明确论证了"当前场景不需要真正的多 Agent"——这个结论仍然有效
3. 成本优势明显：每次对话只有 Supervisor 的一次 LLM 调用（而非 2-3 次）
4. 可以逐步演进：先把体验做好，后续如果真的需要多 Agent 再拆分

**Agent 间协作方式**：

三个专业角色通过 **Tool 调用链** 协作，而非嵌套 LLM 调用：

```
SupervisorAgent.run_stream()
  │
  ├── plan_outfit()  ← OutfitAdvisor 角色（带强 System Prompt 的 Tool）
  │       │
  │       └── 内部调用 LLM 一次（生成方案）
  │
  ├── evaluate_outfit()  ← 新增，OutfitAdvisor 的评价能力
  │       │
  │       └── 内部调用 LLM 一次（评价方案）
  │
  ├── get_wardrobe_health()  ← WardrobeCurator 角色
  │       │
  │       └── 内部调用 LLM 一次（健康分析）
  │
  ├── match_style_from_image()  ← 新增，参考图复刻
  │       │
  │       └── 内部调用 LLM 两次（风格分析 + 衣柜匹配）
  │
  └── get_care_guide()  ← GarmentCare 角色
          │
          └── 纯规则（无需 LLM，材质知识库查表）
```

---

## 二、实施架构

### 2.1 整体架构

```
┌────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │           SupervisorAgent（唯一 Agent）                │  │
│  │  run_stream() ← 现有核心循环，只需扩展工具集          │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                    │
│     ┌─────────────────┼──────────────────────┐          │
│     │                 │                       │          │
│  ┌──▼────────┐  ┌─────▼──────┐  ┌──────────▼──────┐  │
│  │ Outfit    │  │ Wardrobe   │  │ GarmentCare     │  │
│  │ Advisor   │  │ Curator    │  │                 │  │
│  │           │  │            │  │ 材质知识库(内置) │  │
│  │ Tool 函数 │  │ Tool 函数   │  │ 纯规则查表       │  │
│  │ + LLM 调用│  │ + LLM 调用  │  │                 │  │
│  └───────────┘  └────────────┘  └──────────────────┘  │
│     │                 │                       │          │
│  ┌──▼─────────────────▼───────────────────────▼──────┐  │
│  │              Shared Tools                            │  │
│  │  get_weather | analyze_clothing_image               │  │
│  │  search_wardrobe | get_outfit_history              │  │
│  │  remember_context | recall_context                  │  │
│  └────────────────────────────────────────────────────┘  │
│     │                                                        │
│  ┌──▼────────────────────────────────────────────────┐  │
│  │              Data Layer                              │  │
│  │  PostgreSQL + Redis                                  │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────┐
│           Background Service (APScheduler)                  │
│                                                            │
│  ┌──────────────────────┐  ┌────────────────────────────┐ │
│  │  ProactiveService    │  │  PreferenceLearner         │ │
│  │  主动服务引擎         │  │  偏好学习（从反馈中学习）   │ │
│  └──────────────────────┘  └────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 2.2 扩展后的 Tool 体系

```
SupervisorAgent.tools（扩展后）
│
├── SharedTools（现有）
│   ├── get_weather ✅
│   ├── analyze_clothing_image ✅
│   ├── remember_context ✅（扩展字段）
│   └── recall_context ✅
│
├── WardrobeTools（扩展）
│   ├── search_wardrobe ✅（扩展 match_with 参数）
│   ├── add_clothes_to_wardrobe ✅
│   ├── get_wardrobe_health 🆕 （WardrobeCurator 能力）
│   ├── get_unused_reminder 🆕
│   ├── match_style 🆕（参考图风格复刻）
│   └── get_style_gap 🆕（风格缺口检测）
│
├── OutfitTools（重构）
│   ├── plan_outfit 🆗（重构为 OutfitAdvisor 能力）
│   ├── evaluate_outfit 🆕（穿搭评价）
│   ├── refine_outfit 🆕（多轮迭代）
│   ├── analyze_feedback 🆕（反馈语义解析）
│   └── get_outfit_history ✅
│
├── CareTools（新增）
│   └── get_care_guide 🆕（GarmentCare 能力，规则查表）
│
└── KnowledgeTools（扩展）
    └── search_knowledge_base ✅（扩展为 FashionAdvisor 知识问答）
```

---

## 三、数据库改造方案

### 3.1 新增表：user_preferences（偏好学习）

```sql
-- 用户穿搭偏好表（核心新增）
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 颜色偏好
    liked_colors TEXT[] DEFAULT '{}',      -- ["黑色", "白色", "深蓝"]
    disliked_colors TEXT[] DEFAULT '{}',   -- ["粉色", "荧光色"]

    -- 风格偏好
    liked_styles TEXT[] DEFAULT '{}',      -- ["简约", "复古"]
    disliked_styles TEXT[] DEFAULT '{}',    -- ["街头", "嘻哈"]

    -- 品类偏好
    favorite_categories TEXT[] DEFAULT '{}',
    avoided_categories TEXT[] DEFAULT '{}',

    -- 隐性偏好（从行为推断）
    likely_height VARCHAR(20),             -- "short" / "average" / "tall"
    likely_body_type VARCHAR(50),          -- 从拒绝行为推断

    -- 反馈统计
    total_feedbacks INT DEFAULT 0,
    accept_count INT DEFAULT 0,            -- 被采纳的方案数
    reject_count INT DEFAULT 0,            -- 被拒绝的方案数

    -- 偏好置信度（用于判断偏好是否足够确定）
    colors_confidence FLOAT DEFAULT 0.0,   -- 0.0-1.0
    styles_confidence FLOAT DEFAULT 0.0,
    categories_confidence FLOAT DEFAULT 0.0,

    UNIQUE(user_id)
);

CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);
```

**更新现有表：clothing_items**

```sql
-- clothing_items 新增字段
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS condition_score INT DEFAULT 80;
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS estimated_lifespan_months INT;
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS material VARCHAR(64);  -- 已有，验证
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS season_tags TEXT[] DEFAULT '{}';
```

**新增表：preference_feedbacks（反馈记录）**

```sql
-- 偏好反馈记录（用于积累学习样本）
CREATE TABLE preference_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outfit_history_id UUID REFERENCES outfit_histories(id),
    created_at TIMESTAMP DEFAULT NOW(),

    feedback_type VARCHAR(20) NOT NULL,   -- "accept" / "reject" / "modify"
    feedback_content TEXT NOT NULL,        -- 用户原始反馈文字

    -- 解析后的偏好调整
    interpreted JSONB DEFAULT '{}',
    -- {"adjust_formal": "reduce", "preferred_colors": ["浅蓝"], "avoided_styles": ["商务正装"]}

    used_for_learning BOOLEAN DEFAULT FALSE  -- 是否已用于更新偏好
);

CREATE INDEX idx_pref_fb_user_id ON preference_feedbacks(user_id);
CREATE INDEX idx_pref_fb_created ON preference_feedbacks(created_at DESC);
```

### 3.2 ORM 模型新增

```python
# app/models/preferences.py（新增文件）

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 颜色偏好
    liked_colors = Column(ARRAY(String), default=[])
    disliked_colors = Column(ARRAY(String), default=[])

    # 风格偏好
    liked_styles = Column(ARRAY(String), default=[])
    disliked_styles = Column(ARRAY(String), default=[])

    # 品类偏好
    favorite_categories = Column(ARRAY(String), default=[])
    avoided_categories = Column(ARRAY(String), default=[])

    # 隐性偏好
    likely_height = Column(String(20))
    likely_body_type = Column(String(50))

    # 统计
    total_feedbacks = Column(Integer, default=0)
    accept_count = Column(Integer, default=0)
    reject_count = Column(Integer, default=0)

    # 置信度
    colors_confidence = Column(Float, default=0.0)
    styles_confidence = Column(Float, default=0.0)
    categories_confidence = Column(Float, default=0.0)


class PreferenceFeedback(Base):
    __tablename__ = "preference_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    outfit_history_id = Column(UUID(as_uuid=True), ForeignKey("outfit_histories.id"))
    created_at = Column(DateTime, default=datetime.now)

    feedback_type = Column(String(20), nullable=False)   # "accept" / "reject" / "modify"
    feedback_content = Column(String, nullable=False)
    interpreted = Column(JSON, default={})
    used_for_learning = Column(Boolean, default=False)

    user = relationship("User")
    outfit = relationship("OutfitRecord")
```

### 3.3 AgentMemory 扩展

```python
# app/agent/memory.py 扩展

@dataclass
class AgentMemory:
    # ... 现有字段保持不变 ...

    # ========== 新增：偏好相关 ==========
    # 当前对话中的偏好调整（用于多轮迭代）
    current_preference_adjustments: Dict[str, Any] = field(default_factory=dict)
    # 当前对话生成的方案列表（用于迭代优化）
    current_outfit_options: List[Dict] = field(default_factory=list)
    current_option_index: int = 0

    # ========== 新增：多轮迭代状态 ==========
    iteration_count: int = 0
    last_feedback: Optional[str] = None
    last_plan: Optional[Dict] = None

    # ========== 新增：衣橱上下文（轻量缓存） ==========
    cached_wardrobe_summary: Optional[Dict] = None
    cached_wardrobe_at: Optional[datetime] = None

    def to_context_string(self) -> str:
        """扩展上下文字符串"""
        parts = []
        # ... 现有字段 ...
        if self.current_preference_adjustments:
            parts.append(f"当前偏好调整：{self.current_preference_adjustments}")
        if self.iteration_count > 0:
            parts.append(f"迭代次数：{self.iteration_count}（已拒绝 {self.iteration_count} 次）")
        return "\n".join(parts) if parts else "无已记住的信息"
```

---

## 四、核心模块改造

### 4.1 OutfitAdvisor（穿搭顾问）

**改造思路**：不新增 Agent 类，而是**重构 `plan_outfit` Tool**，用更强的 System Prompt 实现 OutfitAdvisor 的能力。

#### 4.1.1 重构 plan_outfit Tool

```python
# app/agent/tools/outfit.py 重构

PLANNING_SYSTEM_PROMPT = """你是一个有10年经验的专业穿搭顾问，曾为数百位客户做形象设计。

【你的性格】
- 有自己的审美判断，敢于说真话
- 尊重用户但不盲从，不说违心的"好看"
- 主动给出更好的选择，不只是执行命令

【你的职责】
1. 搭配方案生成：根据场景、天气、衣柜生成方案
2. 搭配评价：严格评价现有搭配，给出改进建议
3. 迭代优化：根据用户反馈持续改进方案
4. 主动建议：不只是响应，要主动给出更好的选择

【搭配评价标准】（你必须坚持）
- 色彩协调：不超过3个主色，相近色或互补色搭配
- 风格统一：整套搭配的风格要一致，不能混搭冲突风格
- 场合得体：正式场合不能有休闲单品，反之亦然
- 层次分明：上下装/内外装要有层次对比
- 身材适配：考虑身材特点，不推荐显矮/显胖的搭配

【敢说的话】
- "这套的色彩协调，但正式度不够，商务场合不太合适"
- "我不推荐这个方案，因为它上下装的正式度不匹配"
- "您衣柜里其实有更好的选择"
- "这个颜色在换季时节显得沉重，换成浅色系会更清爽"

【反馈处理策略】
- "太正式" → 降低正式度：换休闲品类（西装→针织衫）、换浅色系
- "太休闲" → 提升正式度：换正式品类、加正式感单品
- "年轻一点" → 换浅色/亮色、简化款式、避免老气元素
- "显瘦" → 深色系、避免膨胀材质（粗针织、亮面）
- "小个子" → 优先高腰单品、避免过长下装、推荐短款

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）
"""
```

#### 4.1.2 新增 evaluate_outfit Tool

```python
@tool
async def evaluate_outfit(outfit_plan: dict, scene: str = None) -> str:
    """
    严格评价一套穿搭方案，给出优缺点和改进建议。
    用于：在生成方案后，主动评价并给出改进建议。
    """
    try:
        from app.services.llm_providers import get_cached_provider
        from langchain_core.messages import HumanMessage, SystemMessage

        EVALUATION_PROMPT = f"""请严格评价以下穿搭方案：

场景：{scene or '未指定'}

方案详情：
{json.dumps(outfit_plan, ensure_ascii=False, indent=2)}

请从以下维度评价并给出分数（0-100）和具体建议：
1. 色彩协调性
2. 风格一致性
3. 场合得体性
4. 层次感
5. 身材适配性

输出格式（JSON）：
{{
  "overall_score": 85,
  "dimensions": {{
    "color": {{"score": 90, "comment": "..."}},
    "style": {{"score": 80, "comment": "..."}},
    "scene": {{"score": 85, "comment": "..."}},
    "layering": {{"score": 75, "comment": "..."}},
    "body_fit": {{"score": 80, "comment": "..."}}
  }},
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "suggestions": ["...", "..."]
}}
"""
        llm = get_cached_provider().chat_model
        response = await llm.ainvoke([
            SystemMessage(content="你是一个严格专业的穿搭评审。"),
            HumanMessage(content=EVALUATION_PROMPT)
        ])

        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        return json.dumps({"error": "解析失败", "raw": response.content})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})
```

#### 4.1.3 新增 analyze_feedback Tool（反馈解析）

```python
@tool
async def analyze_feedback(feedback: str, current_plan: dict,
                           context: dict) -> str:
    """
    解析用户的自然语言反馈，转化为偏好调整指令。
    这是"多轮迭代"的核心能力。
    """
    try:
        from app.services.llm_providers import get_cached_provider
        from langchain_core.messages import HumanMessage, SystemMessage

        FEEDBACK_ANALYSIS_PROMPT = f"""用户对当前穿搭方案给出了反馈：

当前方案：
{json.dumps(current_plan, ensure_ascii=False, indent=2)}

用户反馈：「{feedback}」

上下文：
{json.dumps(context, ensure_ascii=False, indent=2)}

请分析用户反馈的语义，将其转化为偏好调整指令：

【可能的调整方向】
- adjust_formal: "increase" / "reduce" / null
- preferred_colors: ["..."] 或 null
- avoided_colors: ["..."] 或 null
- preferred_styles: ["..."] 或 null
- avoided_styles: ["..."] 或 null
- body_concern: "显瘦" / "显高" / "显年轻" / null
- color_change: "换颜色" → 目标颜色描述

【判断原则】
- 不要过度解读，只从字面理解
- 如果反馈模糊（如"不好看"），返回空的调整
- 如果反馈涉及多个维度，全部解析

输出格式（JSON）：
{{
  "adjustments": {{
    "adjust_formal": "reduce",
    "preferred_colors": ["浅蓝"],
    "avoided_colors": null,
    "preferred_styles": null,
    "avoided_styles": ["商务正装"],
    "body_concern": null,
    "color_change": null
  }},
  "reasoning": "用户的'太正式'反馈意味着需要降低正式度...",
  "confidence": 0.85
}}
"""
        llm = get_cached_provider().chat_model
        response = await llm.ainvoke([
            SystemMessage(content="你是一个专业的时尚反馈分析师。"),
            HumanMessage(content=FEEDBACK_ANALYSIS_PROMPT)
        ])

        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        return json.dumps({"adjustments": {}, "confidence": 0.0})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})
```

### 4.2 WardrobeCurator（衣橱管家）

#### 4.2.1 扩展 search_wardrobe（新增 match_with 参数）

```python
@tool
async def search_wardrobe(
    category: str = None,
    color: str = None,
    scene: str = None,
    match_with: dict = None,  # 🆕 新增参数
    include_unused: bool = False,  # 🆕 新增参数
) -> str:
    """
    搜索用户衣柜中的衣物。

    match_with 参数（🆕）：
    用于"以某件衣服为基准找搭配"的场景。
    传入目标衣物的颜色或风格，系统会返回与之搭配的衣物。

    搭配规则（内置，无需 LLM）：
    - 互补色：蓝+橙、红+绿、紫+黄
    - 相近色：深蓝+浅蓝+藏蓝
    - 中性色过渡：黑+灰+白
    - 风格匹配：休闲-休闲、商务-商务

    include_unused 参数（🆕）：
    是否包含长期未穿的衣物（默认只返回30天内穿过的）
    """
    try:
        from app.agent.graph.nodes.wardrobe import query_wardrobe
        db = get_db_for_tools()
        user_id = get_current_user_id()

        items = query_wardrobe(db, user_id, category=category, color=color, tags=None)

        # 🆕 新增：搭配兼容性筛选
        if match_with:
            items = _filter_matching_items(items, match_with)

        # 🆕 新增：未穿衣物筛选
        if not include_unused:
            items = _filter_recently_worn(items, days=30)

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
                "last_worn_at": item.get("last_worn_at"),
                "match_score": item.get("match_score", 0),  # 🆕 搭配匹配分
            })
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def _filter_matching_items(items: list, match_with: dict) -> list:
    """基于搭配规则筛选兼容衣物"""
    target_color = match_with.get("color", "")
    target_style = match_with.get("style", "")
    target_category = match_with.get("category", "")

    # 互补色映射
    COMPLEMENTARY_COLORS = {
        "蓝色": ["橙色", "米色", "白色"],
        "红色": ["黑色", "白色", "灰色"],
        "绿色": ["米色", "棕色", "白色"],
        "紫色": ["黄色", "灰色", "白色"],
        "黄色": ["紫色", "蓝色", "灰色"],
        "橙色": ["蓝色", "藏蓝", "灰色"],
        "粉色": ["灰色", "白色", "藏蓝"],
        "深酒红": ["黑色", "白色", "浅蓝"],
    }
    # ... 更多规则

    COMPLEMENTARY_STYLES = {
        "休闲": ["休闲", "日常", "运动"],
        "商务": ["商务", "正式"],
        "约会": ["约会", "休闲", "日常"],
    }

    scored_items = []
    for item in items:
        score = 0
        color = item.get("color", "")

        # 颜色匹配
        if target_color:
            if color in COMPLEMENTARY_COLORS.get(target_color, []):
                score += 50
            elif color in [target_color]:  # 相近色
                score += 30
            elif _is_neutral(color) and _is_neutral(target_color):
                score += 40  # 中性色互搭

        # 风格匹配
        if target_style:
            item_style = item.get("scene", "")
            if item_style in COMPLEMENTARY_STYLES.get(target_style, []):
                score += 30

        # 品类互补（top + pants + outer）
        if target_category == "top" and item.get("category") in ["pants", "outer"]:
            score += 20
        if target_category == "pants" and item.get("category") in ["top", "outer"]:
            score += 20

        if score > 0:
            item["match_score"] = min(score, 100)
            scored_items.append(item)

    # 按匹配分排序
    scored_items.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_items
```

#### 4.2.2 新增 get_wardrobe_health Tool

```python
@tool
async def get_wardrobe_health() -> str:
    """
    检查用户衣橱健康度，返回综合报告和主动提醒。
    这是 WardrobeCurator 的核心能力。
    """
    try:
        from app.agent.graph.nodes.wardrobe import get_wardrobe_stats, get_underused_clothes
        from datetime import datetime, timedelta

        db = get_db_for_tools()
        user_id = get_current_user_id()

        # 1. 衣橱基本统计
        stats = get_wardrobe_stats(db, user_id)
        total_items = sum(stats.values()) if stats else 0

        # 2. 长期未穿衣物
        unused_60 = get_underused_clothes(db, user_id, max_wear_count=3, days_threshold=60)
        unused_90 = get_underused_clothes(db, user_id, max_wear_count=3, days_threshold=90)

        # 3. 穿着频率分析
        all_items = query_wardrobe(db, user_id)  # 全量
        wear_counts = [(i["description"], i["wear_count"], i.get("last_worn_at"))
                      for i in all_items if i.get("wear_count", 0) > 0]
        wear_counts.sort(key=lambda x: x[1], reverse=True)

        avg_wear = sum(w[1] for w in wear_counts) / len(wear_counts) if wear_counts else 0
        overused = [(name, count, last) for name, count, last in wear_counts
                    if count > avg_wear * 3]  # 穿着过频

        # 4. 颜色分布
        color_dist = {}
        for item in all_items:
            color = item.get("color", "未知")
            color_dist[color] = color_dist.get(color, 0) + 1

        # 5. 计算健康度评分
        health_score = _calculate_wardrobe_health(
            total_items=total_items,
            unused_60_count=len(unused_60),
            unused_90_count=len(unused_90),
            overused_count=len(overused),
            color_variety=len(color_dist),
        )

        # 6. 生成提醒
        reminders = []
        if unused_90:
            reminders.append({
                "type": "critical",
                "title": "这些衣服好久没穿了",
                "items": [{"name": i["description"], "days": i.get("days_unused", 0)}
                          for i in unused_90[:5]],
                "action": "确认是否保留"
            })
        if overused:
            reminders.append({
                "type": "warning",
                "title": "穿着频率不均",
                "items": [{"name": name, "count": count} for name, count, _ in overused[:3]],
                "action": "建议添置替换款"
            })
        if health_score < 60:
            reminders.append({
                "type": "info",
                "title": "衣橱利用率下降",
                "action": "考虑定期清理或添置"
            })

        result = {
            "health_score": health_score,
            "total_items": total_items,
            "unused_60_days": len(unused_60),
            "unused_90_days": len(unused_90),
            "overused_items": len(overused),
            "color_distribution": dict(sorted(color_dist.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_worn": wear_counts[:5],
            "reminders": reminders,
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def _calculate_wardrobe_health(total_items, unused_60_count, unused_90_count,
                                overused_count, color_variety) -> int:
    """计算衣橱健康度评分（0-100）"""
    score = 100

    # 长期未穿物品扣分
    score -= min(unused_60_count * 5, 30)
    score -= min(unused_90_count * 10, 40)

    # 穿着过频扣分
    score -= min(overused_count * 8, 20)

    # 颜色单一扣分
    if color_variety < 3:
        score -= 10

    return max(0, min(100, score))
```

#### 4.2.3 新增 match_style Tool（参考图风格复刻）

```python
@tool
async def match_style(reference_image_url: str) -> str:
    """
    分析参考图的穿搭风格，在衣柜中找相似单品并组合方案。
    这是 WardrobeCurator 的高级能力。
    """
    try:
        from app.agent.graph.nodes.wardrobe import query_wardrobe
        from app.agent.clothes_agent import image_analyzer
        from app.services.llm_providers import get_cached_provider
        from langchain_core.messages import HumanMessage, SystemMessage
        import asyncio

        db = get_db_for_tools()
        user_id = get_current_user_id()

        # 1. 风格分析（调用 VL 模型）
        style_analysis_prompt = """分析这张穿搭图片的风格特征：
        - 主色调及配色比例
        - 风格关键词（复古/街头/商务/运动等）
        - 版型特征（宽松/修身/oversize）
        - 关键单品清单
        - 适合场合

        请用 JSON 格式返回：
        {
          "primary_colors": ["...", "..."],
          "style_tags": ["...", "..."],
          "fit_type": "宽松/修身/正常",
          "key_items": [{"item": "上衣", "description": "..."}],
          "suitable_scenes": ["...", "..."],
          "overall_style": "风格总结"
        }
        """
        style_result = await image_analyzer.analyze(
            image_url=reference_image_url,
            prompt=style_analysis_prompt
        )

        # 2. 解析风格标签
        style_tags = style_result.get("style_tags", [])
        primary_colors = style_result.get("primary_colors", [])

        # 3. 在衣柜中搜索匹配单品
        all_items = query_wardrobe(db, user_id)

        matched_items = []
        missing_categories = []

        for key_item in style_result.get("key_items", []):
            target_category = _map_to_category(key_item.get("item", ""))
            target_color = _extract_color(key_item.get("description", ""), primary_colors)

            # 在衣柜中找最佳匹配
            best_match = None
            best_score = 0
            for item in all_items:
                if item.get("category") != target_category:
                    continue
                score = 0
                if target_color and target_color.lower() in item.get("color", "").lower():
                    score += 50
                # 风格标签匹配
                item_tags = item.get("scene", "")
                for tag in style_tags:
                    if tag.lower() in item_tags.lower():
                        score += 30
                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= 40:
                matched_items.append({
                    "reference_item": key_item.get("item"),
                    "matched": best_match,
                    "similarity": min(best_score, 100),
                })
            else:
                missing_categories.append(key_item.get("item"))

        # 4. 生成方案
        result = {
            "style_analysis": style_result,
            "matched_items": matched_items,
            "missing_categories": missing_categories,
            "replication_score": int(len(matched_items) / max(len(style_result.get("key_items", [])), 1) * 100),
            "suggestions": _generate_suggestions(missing_categories)
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})
```

### 4.3 GarmentCare（衣物护理）

```python
# app/agent/tools/care.py（新增文件）

from langchain_core.tools import tool
import json

# 材质护理知识库（内置规则，无需 LLM）
MATERIAL_CARE_GUIDE = {
    "羊绒": {
        "清洗": "建议干洗或手洗，水温不超过30°C",
        "晾晒": "平铺晾干，避免悬挂变形",
        "存储": "放入樟脑丸，使用透气的棉布袋",
        "注意事项": "穿着时避免与粗糙面料摩擦，会加速起球"
    },
    "羊毛": {
        "清洗": "建议干洗，如需手洗用凉水",
        "晾晒": "平铺晾干，避免阳光直射",
        "存储": "放入防虫片，使用宽肩衣架",
        "注意事项": "起球后用去毛球器轻轻处理"
    },
    "真丝": {
        "清洗": "冷水手洗，使用专用洗涤剂",
        "晾晒": "阴凉通风处晾干，避免暴晒",
        "存储": "挂放避免折叠痕，使用透气衣架",
        "注意事项": "避免接触香水和化妆品，会褪色"
    },
    "棉质": {
        "清洗": "可机洗，但深色分开洗",
        "晾晒": "及时晾晒，避免潮湿滋生细菌",
        "存储": "叠放或挂放均可",
        "注意事项": "领口变形后难以恢复，不要过度拉伸"
    },
    "麂皮": {
        "清洗": "专用麂皮刷清理污渍，避免水洗",
        "晾晒": "阴凉处自然风干",
        "存储": "放入鞋撑，保持形状",
        "注意事项": "雨季前建议做防水处理"
    },
    "皮革": {
        "清洗": "用专用皮革清洁布擦拭",
        "晾晒": "避免暴晒，会开裂",
        "存储": "使用鞋撑，放入防尘袋",
        "注意事项": "定期使用皮革护理油保养"
    },
    "羽绒": {
        "清洗": "手洗或干洗，避免拧干",
        "晾晒": "平铺晾干，定时拍打恢复蓬松",
        "存储": "避免压缩，用透气质地收纳袋",
        "注意事项": "不要干洗，会破坏羽绒油脂"
    },
    "麻质": {
        "清洗": "机洗可，但易皱需熨烫",
        "晾晒": "避免长时间浸泡，阳光下易变黄",
        "存储": "叠放，熨烫后收纳",
        "注意事项": "纯麻易皱是正常现象，非质量问题"
    },
}


@tool
async def get_care_guide(material: str = None, clothing_item_id: str = None) -> str:
    """
    根据材质或衣物ID获取护理指南。
    优先使用 clothing_item_id（从 DB 读取材质），
    也可直接传入 material 参数。
    """
    try:
        from app.agent.tools.context import get_db_for_tools
        from app.models import UserClothes

        db = get_db_for_tools()

        # 如果提供了 clothing_item_id，从 DB 读取材质
        if clothing_item_id:
            item = db.query(UserClothes).filter(
                UserClothes.id == clothing_item_id
            ).first()
            if item:
                material = item.material

        if not material:
            return json.dumps({
                "error": "未找到材质信息",
                "hint": "请上传衣物图片，我可以分析材质"
            })

        # 模糊匹配材质名
        material_key = None
        for key in MATERIAL_CARE_GUIDE:
            if key in material or material in key:
                material_key = key
                break

        if not material_key:
            return json.dumps({
                "material": material,
                "care_guide": None,
                "hint": f"暂不支持 {material} 的详细护理指南，请上传图片让我分析"
            })

        guide = MATERIAL_CARE_GUIDE[material_key]

        # 检查衣物当前状态（如果有 clothing_item_id）
        item_health = None
        if clothing_item_id and item:
            item_health = {
                "condition_score": item.condition_score or 80,
                "estimated_lifespan": item.estimated_lifespan_months,
                "last_worn_at": item.last_worn_at.isoformat() if item.last_worn_at else None,
                "wear_count": item.wear_count
            }

        return json.dumps({
            "material": material_key,
            "care_guide": guide,
            "item_health": item_health
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})
```

### 4.4 SupervisorAgent 扩展

#### 4.4.1 扩展 System Prompt（融入 FashionSteward 理念）

```python
SYSTEM_PROMPT = """你是一个专业、贴心、有主见的穿搭管家。

【你的三个角色】
你是 FashionSteward 的核心大脑，同时扮演三个角色：
1. 穿搭顾问（OutfitAdvisor）：生成方案、评价方案、迭代优化
2. 衣橱管家（WardrobeCurator）：管理衣橱健康、主动提醒、发现被遗忘的衣物
3. 衣物护理师（GarmentCare）：提供材质保养建议

【核心能力】
- 根据天气和场合推荐穿搭
- 识别和管理衣柜中的衣物
- 分析用户上传的衣物图片，给出搭配建议
- 分析参考图穿搭风格，用衣柜衣物复刻
- 查询穿搭历史和衣橱健康
- 回答材质护理问题
- 提供穿搭知识建议

【主动服务意识】（关键！）
不要只是被动响应，要主动发现问题：
- 发现用户缺少某个季节的关键衣物 → 主动提醒
- 发现衣橱有长期未穿的衣物 → 主动询问
- 生成的方案有明显的搭配问题 → 主动指出
- 用户给出模糊反馈 → 主动追问确认

【工具使用规则】
- 用户请求穿搭推荐 → 先 get_weather，再 search_wardrobe，最后 plan_outfit
- 用户上传衣物图片想找搭配 → analyze_clothing_image + search_wardrobe(match_with=...)
- 用户上传参考图 → match_style 分析风格，在衣柜中找相似单品
- 用户询问衣橱健康 → get_wardrobe_health
- 用户上传衣物图片想存衣柜 → analyze_clothing_image + add_clothes_to_wardrobe
- 用户询问材质护理 → get_care_guide
- 用户询问历史 → get_outfit_history
- 用户提到城市/场合/日期 → remember_context 记住信息
- 用户对方案不满意 → analyze_feedback 解析反馈 + refine_outfit 优化方案

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）
- 有自己的审美判断，敢于说真话
- 不要一味说好话，有问题要指出来

【穿衣规则】（内置知识）
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【多轮迭代策略】
- 用户说"太正式/太休闲" → analyze_feedback + refine_outfit
- 用户说"年轻一点/显瘦" → analyze_feedback + refine_outfit（带身体特征）
- 用户说"换个颜色" → refine_outfit（调整颜色）
- 用户说"就这套了" → 记录到历史，通知用户
- 用户说"再推荐一套" → plan_outfit（不重复问）

【追问策略】
- 缺少城市 → "请问要去哪个城市呢？"
- 缺少场合 → "请问是什么场合呢？（上班/约会/运动...）"
- 缺少季节 → "那是什么季节呢？春夏秋冬？"
- 用户意图不明 → "我需要更多信息来帮您，请描述一下具体需求？"
"""
```

#### 4.4.2 扩展 run_stream 的反馈处理

```python
async def run_stream(self, user_message: str, images: List[str] = None) -> AsyncGenerator[Dict, None]:
    """流式执行主循环（扩展多轮迭代支持）"""

    self.memory.add_message("user", user_message)
    messages = self._build_messages(user_message, images)
    yield {"type": "thinking", "content": "正在分析您的请求..."}

    # 🆕 检测是否是多轮迭代反馈
    is_feedback = self._is_feedback_message(user_message)
    if is_feedback and self.memory.current_outfit_options:
        yield {"type": "thinking", "content": "收到反馈，正在调整方案..."}
        # 🆕 反馈处理分支：解析反馈 → 优化方案
        await self._handle_feedback_iteration(user_message, messages)
        return

    response = await self.llm_with_tools.ainvoke(messages)

    max_turns = 10
    turn = 0

    while response.tool_calls and turn < max_turns:
        turn += 1
        for tc in response.tool_calls:
            yield {"type": "tool_called", "tool": tc.name, "args": tc.args}

            try:
                result = await self.tools[tc.name].invoke(**tc.args)
            except Exception as e:
                result = json.dumps({"error": type(e).__name__, "message": str(e)})

            yield {"type": "tool_result", "tool": tc.name, "result": result}

            # 🆕 特殊处理：穿搭方案生成后主动评价
            if tc.name == "plan_outfit":
                self._handle_plan_result(result)

            self._update_memory_from_tool_result(tc.name, result, tc.args)
            messages.append(ToolMessage(name=tc.name, content=result))

        response = await self.llm_with_tools.ainvoke(messages)

    final_text = response.content if response.content else ""
    if final_text:
        self.memory.add_message("assistant", final_text)

    yield {"type": "text", "content": final_text}
    yield {"type": "done", "content": final_text}


def _is_feedback_message(self, message: str) -> bool:
    """判断用户消息是否为反馈"""
    feedback_keywords = [
        "太正式", "太休闲", "换个", "再推荐", "就这套",
        "年轻", "显瘦", "显高", "不好看", "不满意",
        "换一个", "不要这个", "不好看", "不对"
    ]
    return any(kw in message for kw in feedback_keywords)


async def _handle_feedback_iteration(self, user_message: str, messages: list):
    """处理多轮迭代反馈"""
    # 1. 解析反馈
    feedback_result = await self.tools["analyze_feedback"].invoke({
        "feedback": user_message,
        "current_plan": self.memory.last_plan or {},
        "context": self.memory.to_context_dict()
    })

    # 2. 更新偏好调整
    adjustments = json.loads(feedback_result).get("adjustments", {})
    self.memory.current_preference_adjustments.update(adjustments)
    self.memory.iteration_count += 1
    self.memory.last_feedback = user_message

    # 3. 记录反馈到 DB（用于学习）
    await self._record_feedback(user_message, adjustments)

    # 4. 生成优化方案
    refined_result = await self.tools["refine_outfit"].invoke({
        "adjustments": adjustments,
        "previous_plan": self.memory.last_plan,
        "memory": self.memory.to_context_dict()
    })

    yield {"type": "tool_result", "tool": "refine_outfit", "result": refined_result}

    # 5. 输出结果
    refined_data = json.loads(refined_result)
    refined_text = self._format_refined_plan(refined_data)
    self.memory.add_message("assistant", refined_text)

    yield {"type": "text", "content": refined_text}
    yield {"type": "done", "content": refined_text}
```

---

## 五、偏好学习系统

### 5.1 反馈学习流程

```
用户反馈
    │
    ▼
analyze_feedback Tool（解析语义）
    │
    ▼
记录到 preference_feedbacks 表
    │
    ▼
PreferenceLearner（后台服务，异步处理）
    │
    ├── 统计学习：某特征被拒绝3次 → 加入 disliked
    ├── 推断学习："太长" → likely_height="short"
    └── 更新 user_preferences 表
```

### 5.2 PreferenceLearner 服务

```python
# app/agent/services/preference_learner.py（新增文件）

from sqlalchemy.orm import Session
from app.models import UserPreferences, PreferenceFeedback, UserClothes
from app.database import SessionLocal
import json
from collections import Counter


class PreferenceLearner:
    """
    从用户反馈中学习偏好，更新 user_preferences 表。
    可由后台定时任务触发，或实时触发。
    """

    REJECTION_THRESHOLD = 3  # 某特征被拒绝 N 次才加入 disliked
    ACCEPTANCE_THRESHOLD = 2  # 某特征被接受 N 次才加入 liked

    def learn_from_feedback(self, user_id: str, feedback_id: str = None):
        """
        从反馈记录中学习，更新用户偏好。
        """
        db = SessionLocal()
        try:
            # 1. 获取未学习的新反馈
            feedbacks = db.query(PreferenceFeedback).filter(
                PreferenceFeedback.user_id == user_id,
                PreferenceFeedback.used_for_learning == False
            ).all()

            if not feedbacks:
                return

            # 2. 获取或创建用户偏好记录
            prefs = db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()

            if not prefs:
                prefs = UserPreferences(user_id=user_id)
                db.add(prefs)

            # 3. 统计特征频率
            accepted_colors = Counter()
            rejected_colors = Counter()
            accepted_styles = Counter()
            rejected_styles = Counter()

            for fb in feedbacks:
                if fb.feedback_type == "accept":
                    adj = fb.interpreted.get("adjustments", {})
                    for c in (adj.get("preferred_colors") or []):
                        accepted_colors[c] += 1
                elif fb.feedback_type in ["reject", "modify"]:
                    adj = fb.interpreted.get("adjustments", {})
                    for c in (adj.get("avoided_colors") or []):
                        rejected_colors[c] += 1
                    for s in (adj.get("avoided_styles") or []):
                        rejected_styles[s] += 1

                fb.used_for_learning = True

            # 4. 更新偏好（满足阈值才更新）
            self._update_if_threshold(prefs, "liked_colors", "disliked_colors",
                                      accepted_colors, rejected_colors,
                                      self.ACCEPTANCE_THRESHOLD, self.REJECTION_THRESHOLD)
            self._update_if_threshold(prefs, "liked_styles", "disliked_styles",
                                      accepted_styles, rejected_styles,
                                      self.ACCEPTANCE_THRESHOLD, self.REJECTION_THRESHOLD)

            # 5. 推断隐性偏好
            self._infer_body_preferences(prefs, feedbacks)

            # 6. 更新统计
            prefs.total_feedbacks += len(feedbacks)
            prefs.accept_count += sum(1 for f in feedbacks if f.feedback_type == "accept")
            prefs.reject_count += sum(1 for f in feedbacks if f.feedback_type in ["reject", "modify"])

            # 7. 更新置信度
            prefs.colors_confidence = min(1.0, prefs.total_feedbacks / 10)
            prefs.styles_confidence = min(1.0, prefs.total_feedbacks / 10)

            db.commit()
        finally:
            db.close()

    def _update_if_threshold(self, prefs, liked_field, disliked_field,
                             accepted_counter, rejected_counter,
                             accept_th, reject_th):
        """满足阈值时更新偏好"""
        from sqlalchemy.orm.attributes import get_attribute

        liked = set(get_attribute(prefs, liked_field) or [])
        disliked = set(get_attribute(prefs, disliked_field) or [])

        for color, count in rejected_counter.items():
            if count >= reject_th and color not in disliked:
                disliked.add(color)
                liked.discard(color)  # 互斥

        for color, count in accepted_counter.items():
            if count >= accept_th and color not in liked:
                liked.add(color)
                disliked.discard(color)  # 互斥

        setattr(prefs, liked_field, list(liked))
        setattr(prefs, disliked_field, list(disliked))

    def _infer_body_preferences(self, prefs, feedbacks):
        """从反馈中推断身材特征"""
        for fb in feedbacks:
            content = fb.feedback_content
            if any(kw in content for kw in ["太长", "显矮", "压个子"]):
                prefs.likely_height = "short"
            if any(kw in content for kw in ["显胖", "显壮", "太紧"]):
                prefs.likely_body_type = "leaning_athletic"
```

### 5.3 偏好应用到 plan_outfit

```python
async def plan_outfit(scene: str, temperature: float, wardrobe_items: List[dict],
                      max_options: int = 3, include_preferences: bool = True) -> str:
    """
    根据用户衣柜中的衣物、天气和场合生成穿搭方案。
    🆕 支持根据用户偏好过滤和排序衣物。
    """
    try:
        # 🆕 加载用户偏好（如果有）
        preferences = {}
        if include_preferences:
            from app.agent.services.preference_learner import PreferenceLearner
            learner = PreferenceLearner()
            preferences = learner.get_preferences_for_user(get_current_user_id())

        # 🆕 基于偏好过滤衣物
        filtered_items = _apply_preferences(wardrobe_items, preferences)

        # ... 后续调用 LLM 生成方案（不变）...
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def _apply_preferences(items: list, preferences: dict) -> list:
    """根据用户偏好过滤和排序衣物"""
    if not preferences:
        return items

    disliked_colors = set(preferences.get("disliked_colors") or [])
    disliked_styles = set(preferences.get("disliked_styles") or [])

    filtered = []
    for item in items:
        color = item.get("color", "")
        scene = item.get("scene", "")

        # 跳过强烈不喜欢的
        if color in disliked_colors:
            item["_deprioritize"] = True
        for style in disliked_styles:
            if style in scene:
                item["_deprioritize"] = True

        filtered.append(item)

    # 排序：非deprioritize的优先
    return sorted(filtered, key=lambda x: x.get("_deprioritize", False))
```

---

## 六、主动服务引擎

### 6.1 技术选型：APScheduler

现有项目无定时任务基础设施，选择 **APScheduler**（轻量、无额外依赖）：

```bash
pip install apscheduler
```

### 6.2 调度任务设计

```python
# app/agent/services/proactive_service.py（新增文件）

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProactiveService:
    """
    主动服务引擎，基于 APScheduler 定时触发。
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """启动调度器"""
        # 每日早8点：衣橱健康检查
        self.scheduler.add_job(
            self.daily_wardrobe_check,
            CronTrigger(hour=8, minute=0),
            id="daily_wardrobe_check",
            replace_existing=True
        )

        # 每周一早9点：生成周报
        self.scheduler.add_job(
            self.weekly_report,
            CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_report",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("ProactiveService started")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("ProactiveService stopped")

    async def daily_wardrobe_check(self):
        """
        每日衣橱健康检查。
        检查所有活跃用户（3天内登录）的衣橱状态，
        生成提醒并通过 WebSocket 推送到前端。
        """
        db = SessionLocal()
        try:
            from app.models import User
            from app.agent.services.wardrobe_health import WardrobeHealthChecker
            from app.routers.chat import notification_manager

            # 获取活跃用户
            active_users = db.query(User).filter(
                User.last_active_at >= datetime.now() - timedelta(days=3)
            ).all()

            checker = WardrobeHealthChecker(db)

            for user in active_users:
                health = checker.check(user.id)
                if health.needs_reminder():
                    await notification_manager.push(
                        user_id=str(user.id),
                        type="wardrobe_health",
                        title="👀 衣橱健康提醒",
                        body=health.summary,
                        data={"health_score": health.score}
                    )
        finally:
            db.close()

    async def weekly_report(self):
        """
        每周生成穿搭报告。
        """
        # 类似 daily_wardrobe_check，但生成更详细的周报
        pass

    async def weather_fashion_alert(self, user_id: str, weather: dict):
        """
        天气骤变触发。
        由天气服务在检测到大幅降温时调用。
        """
        from app.agent.services.wardrobe_health import WardrobeHealthChecker
        from app.routers.chat import notification_manager

        db = SessionLocal()
        try:
            checker = WardrobeHealthChecker(db)
            gaps = checker.check_style_gap(user_id, weather)

            if gaps.critical_missing:
                await notification_manager.push(
                    user_id=user_id,
                    type="weather_fashion",
                    title=f"🌡️ {weather['city']}天气提醒",
                    body=f"下周降温到{weather['temperature']}°C，"
                         f"您的衣橱可能缺少{gaps.critical_missing}，"
                         f"要不要考虑添置？",
                    data={"weather": weather, "gaps": gaps.to_dict()}
                )
        finally:
            db.close()
```

### 6.3 启动集成

```python
# app/main.py 扩展

from app.agent.services.proactive_service import ProactiveService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    proactive_service = ProactiveService()
    proactive_service.start()
    yield
    # 关闭时
    proactive_service.stop()
```

### 6.4 推送通道

| 通道 | 实现 | 优先级 |
|------|------|--------|
| WebSocket | 前端已连接的 WebSocket 连接 | P0（用户在对话中时） |
| SSE | 前端保持 SSE 连接 | P1（App场景） |
| 轮询 | 前端定时拉取通知列表 | P2（降级方案） |

```python
# app/routers/chat.py 扩展

class NotificationManager:
    """通知管理器，支持 WebSocket / SSE / 轮询"""

    def __init__(self):
        # WebSocket 连接池：user_id -> set[WebSocket]
        self.connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def push(self, user_id: str, type: str, title: str, body: str, data: dict):
        """推送通知到用户的所有连接"""
        event = {
            "type": type,
            "title": title,
            "body": body,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # WebSocket 推送
        for ws in self.connections.get(user_id, []):
            try:
                await ws.send_json(event)
            except:
                pass

        # 持久化到 DB（用户下次打开 App 时可见）
        await self._persist_notification(user_id, event)


# WebSocket 端点
@router.websocket("/ws/notifications/{user_id}")
async def notification_ws(websocket: WebSocket, user_id: str):
    await websocket.accept()
    notification_manager.connections[user_id].add(websocket)
    try:
        while True:
            # 保持连接，接收心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except:
        pass
    finally:
        notification_manager.connections[user_id].discard(websocket)
```

---

## 七、实施计划

### 7.1 阶段划分

```
Phase 1（4-5 周）：核心对话体验
├── T1.1：扩展 search_wardrobe + match_with 参数
├── T1.2：重构 plan_outfit + OutfitAdvisor System Prompt
├── T1.3：新增 evaluate_outfit Tool
├── T1.4：新增 analyze_feedback Tool
├── T1.5：扩展 SupervisorAgent.run_stream 多轮迭代逻辑
├── T1.6：扩展 AgentMemory + 偏好字段
└── T1.7：MVP 验证（3 轮对话流畅）

Phase 2（3-4 周）：衣橱健康 + 偏好学习
├── T2.1：新增 user_preferences / preference_feedbacks 表
├── T2.2：新增 UserPreferences ORM 模型
├── T2.3：PreferenceLearner 服务
├── T2.4：get_wardrobe_health Tool
├── T2.5：match_style Tool（参考图风格复刻）
├── T2.6：偏好应用到 plan_outfit
└── T2.7：衣橱健康仪表盘 API

Phase 3（3-4 周）：主动服务 + 深度功能
├── T3.1：APScheduler 集成
├── T3.2：ProactiveService 实现
├── T3.3：NotificationManager + WebSocket
├── T3.4：GarmentCare Tool（材质知识库）
├── T3.5：参考图风格复刻完整流程
├── T3.6：周报生成
└── T3.7：全流程回归测试

Phase 4（2 周）：优化与收尾
├── T4.1：性能优化（Tool 结果缓存、衣柜数据预加载）
├── T4.2：成本优化（区分大小模型调用）
├── T4.3：PRD 中的对话风格规范落地
├── T4.4：全流程 E2E 测试
└── T4.5：文档更新
```

### 7.2 优先级矩阵

```
         价值高
           ▲
           │
    T1.1 T1.3 T2.4 T3.4
    T1.2 T1.4 T2.5
    T1.5 T2.1 T2.2
           │
    T1.6 T1.7 T2.3 T2.6
           │
           └──────────► 价值低
    改动小        改动大
```

### 7.3 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/preferences.py` | 新增 | UserPreferences / PreferenceFeedback ORM |
| `app/models/clothes.py` | 修改 | 新增 condition_score 等字段 |
| `app/agent/memory.py` | 修改 | 扩展 AgentMemory 字段 |
| `app/agent/supervisor.py` | 修改 | 扩展 System Prompt + 反馈处理逻辑 |
| `app/agent/tools/outfit.py` | 重构 | OutfitAdvisor 能力（plan_outfit + evaluate_outfit + analyze_feedback） |
| `app/agent/tools/wardrobe.py` | 扩展 | match_with 参数 + match_style Tool |
| `app/agent/tools/care.py` | 新增 | GarmentCare 能力 |
| `app/agent/services/preference_learner.py` | 新增 | 偏好学习服务 |
| `app/agent/services/proactive_service.py` | 新增 | 主动服务引擎 |
| `app/routers/chat.py` | 扩展 | NotificationManager + WebSocket |
| `app/main.py` | 修改 | ProactiveService 启动集成 |
| `schema.sql` | 修改 | 新增表 DDL |
| `requirements.txt` | 修改 | 新增 apscheduler |
| `service/schema.sql` | 修改 | 新增 user_preferences / preference_feedbacks 表 |

---

## 八、风险与对策

| 风险 | 严重程度 | 对策 |
|------|---------|------|
| `plan_outfit` Prompt 过长，超出 LLM context | 高 | 使用 `qwen-plus`（128K context）；将穿搭规则下沉到 Tool 内部而非 Prompt |
| 多轮迭代出现来回振荡 | 中 | 设置最大迭代次数（5 次）；相似反馈 3 次后强制收敛 |
| 偏好学习误判（把偶然当规律） | 中 | 设置置信度阈值；用户可手动修正偏好 |
| APScheduler 在多实例部署下重复执行 | 中 | 使用分布式锁（PostgreSQL advisory lock）或切换为单实例 |
| 推送通知打扰用户 | 中 | 默认关闭主动推送；用户可精细配置通知类型 |
| `match_style` VL 模型调用成本高 | 低 | 缓存风格分析结果（同一图片不重复分析） |
| LLM 搭配质量不稳定 | 高 | 建立人工抽检机制；积累高质量样本后可微调 |

---

## 九、成本评估

### 9.1 LLM 调用次数对比

| 场景 | 当前 | 改造后 | 增量 |
|------|------|--------|------|
| 单次穿搭推荐 | 1 次（Supervisor） | 2 次（Supervisor + plan_outfit 内部） | +1 次 |
| 多轮迭代（3 轮） | — | 3 次（analyze_feedback × 2 + refine_outfit） | — |
| 参考图风格复刻 | — | 3 次（VL 分析 + 风格分析 + 方案生成） | — |
| 衣橱健康检查 | — | 1 次 LLM 调用（后台，无用户感知） | — |

### 9.2 成本优化策略

| 策略 | 说明 | 节省比例 |
|------|------|---------|
| 模型分级 | Supervisor 用 `qwen-plus`；WardrobeCurator 用 `qwen-max`；GarmentCare 不调用 LLM | 50% |
| Tool 结果缓存 | `search_wardrobe` 结果缓存 15 分钟 | 30% |
| VL 模型按需 | 只有上传图片时才调用 VL 模型 | 80% |
| 偏好下推 | 偏好过滤在 DB 层完成，减少 LLM 处理的数据量 | 20% |

---

## 十、测试计划

| 测试项 | 测试方式 | 负责人 |
|--------|---------|--------|
| 单次穿搭推荐流程 | pytest + fixture | 后端 |
| 多轮迭代（反馈 → 优化 → 采纳） | pytest + 模拟对话序列 | 后端 |
| 偏好学习（接受/拒绝 → 偏好更新） | pytest + fixture | 后端 |
| 衣橱健康评分 | pytest + 模拟数据 | 后端 |
| 参考图风格复刻 | 手动测试（需要真实图片） | 全栈 |
| SSE 流式事件完整性 | 前端手动测试 | 前端 |
| WebSocket 推送 | 前后端联调 | 全栈 |
| APScheduler 定时任务 | 手动触发 + 日志验证 | 后端 |
| E2E 对话流程 | Playwright 自动化 | QA |

---

*实施方案结束 — 待技术评审后更新版本*
