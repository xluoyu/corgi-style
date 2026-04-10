# Corgi Style 服务端重构设计方案

## 1. 背景与目标

### 1.1 当前问题

- 多 Agent 架构（v1/v2/v3 并行）过于复杂，为分而分
- 巨型单文件：`chat.py`(790行)、`response.py`(790行)、`supervisor.py`(445行)
- 对话状态管理混乱，导致 bug：用户回答"场合"后再回答"时间"，会丢失"场合"信息
- 重复代码：温度阈值散布在 4+ 文件中
- N+1 查询、Schema/Model 不一致等技术债

### 1.2 重构目标

- **简化**：1 个统一 Agent，不是 4 个路由 Agent
- **清晰**：分层架构，服务层与 Agent 层解耦
- **可复用**：Services 层同时支持 API 和 Agent Tools 调用
- **可测试**：每个模块职责单一

---

## 2. 整体架构

### 2.1 分层架构

```
app/
├── services/               # ★ 核心业务逻辑层（纯 Python，无 LangChain 依赖）
│   ├── __init__.py
│   ├── weather.py          # 天气查询
│   ├── wardrobe.py         # 衣柜 CRUD + 搭配算法
│   ├── image_analysis.py   # 图片分析（属性提取）
│   ├── outfit.py           # 穿搭生成
│   └── style.py            # 风格知识库管理
│
├── agent/                  # Agent 层（LangChain）
│   ├── __init__.py
│   ├── core.py             # Agent 构建器（RunnableWithMessageHistory）
│   ├── memory.py           # 短期对话记忆（Redis/Upstash）
│   │
│   ├── tools/              # Tool 封装层（调用 services）
│   │   ├── __init__.py
│   │   ├── weather.py      # → services.weather
│   │   ├── wardrobe.py     # → services.wardrobe
│   │   ├── image.py        # → services.image_analysis
│   │   └── style.py        # → services.style
│   │
│   └── prompts/            # Prompt 模板
│       ├── __init__.py
│       ├── system.py       # 系统提示词
│       └── scenes.py       # 场景变体
│
└── routers/                # API 层（FastAPI）
    ├── __init__.py
    ├── user.py
    ├── clothes.py          # → services.wardrobe
    ├── outfit.py           # → services.outfit
    ├── history.py
    └── chat.py             # → agent.core
```

### 2.2 模块复用关系

| 调用方 | 调用的模块 | 说明 |
|--------|-----------|------|
| **Routers** | `services.*` | API 直通服务，不走 Agent |
| **Agent Tools** | `services.*` | Tool 内部调用服务 |
| **Agent** | `agent.tools.*` | 组装成 LangChain Tools |

---

## 3. 核心模块设计

### 3.1 Services 层

#### 3.1.1 weather.py

```python
# 职责：天气查询
# 接口：
def get_weather(city: str) -> WeatherInfo:
    """返回温度、天气状况、湿度等"""
```

#### 3.1.2 wardrobe.py

```python
# 职责：衣柜操作
# 接口：
def search_wardrobe(
    user_id: str,
    filters: dict = None  # {category, color, season, scene}
) -> list[ClothingItem]:
    """查询用户衣柜，支持多条件过滤"""

def add_clothes(user_id: str, attrs: ClothingAttrs) -> ClothingItem:
    """添加衣物到衣柜"""

def match_outfit(
    new_item: ClothingItem,
    wardrobe: list[ClothingItem],
    context: MatchContext = None  # {occasion, season, style?}
) -> list[OutfitSuggestion]:
    """新衣服与衣柜现有衣物的搭配建议"""
```

#### 3.1.3 image_analysis.py

```python
# 职责：图片分析
# 接口：
def analyze_clothing_image(image_url: str) -> ClothingAttrs:
    """从单件衣物图片提取属性 {type, color, style, material, ...}"""

def analyze_outfit_image(image_url: str) -> OutfitAnalysis:
    """从整套穿搭图片提取风格要素
    返回: {
        overall_style: "美式复古",
        items: [  # 识别出的各件衣物
            {type: "牛仔外套", color: "深蓝", position: "上装"},
            {type: "白色T恤", color: "白色", position: "内搭"},
            ...
        ],
        style_tags: ["街头", "休闲", "复古"],
        color_palette: ["深蓝", "白色", "卡其"]
    }
"""
```

#### 3.1.4 outfit.py

```python
# 职责：穿搭生成
# 接口：
def generate_outfit(
    user_id: str,
    context: OutfitContext  # {date, location, occasion, style?}
) -> OutfitResult:
    """综合天气、衣柜、偏好生成穿搭方案"""

def generate_similar_outfit(
    user_id: str,
    outfit_analysis: OutfitAnalysis,  # 参考穿搭图片的分析结果
    context: OutfitContext = None     # 可选的场合/季节上下文
) -> SimilarOutfitResult:
    """基于参考穿搭图片的风格，用用户衣柜衣物生成类似搭配
    返回: {
        matched_items: [...],   # 衣柜中已有的匹配衣物
        missing_items: [...]     # 衣柜中缺少的重要衣物
        suggestions: [...]
    }
"""
```

#### 3.1.5 style.py

```python
# 职责：风格知识库管理
# 接口：
def get_style_knowledge(style_name: str) -> StyleKnowledge:
    """获取风格知识：特征标签、搭配规则、参考图"""

def list_builtin_styles() -> list[str]:
    """列出预设风格"""

def save_user_style(user_id: str, style: UserStyle) -> None:
    """保存用户自定义风格"""

def apply_style(
    style_name: str,
    items: list[ClothingItem],
    context: OutfitContext = None
) -> list[ClothingItem]:
    """将风格规则应用于衣物列表，返回调整后的搭配"""
```

### 3.2 Agent 层

#### 3.2.1 memory.py

```python
# 职责：短期对话记忆（Redis/Upstash）
# 存储内容：
{
    "session_id": "abc123",
    "user_id": "user_456",
    "context": {
        "date": "明天",
        "location": "北京",
        "occasion": "上班"
    },
    "pending_image": "https://...",  # 上传未处理的图片
    "image_attrs": {...},           # 已分析的图片属性
    "last_update": "2024-01-01T10:00:00Z"
}

# Session 生命周期：
# - 每日凌晨清空（只保留当日）
# - 前端应用关闭时，发送 /chat/session/close 请求
# - 下次打开应用创建新 session
```

#### 3.2.2 agent/tools/wardrobe.py

```python
from app.services.wardrobe import search_wardrobe, add_clothes, match_outfit

def create_wardrobe_tools():
    return [
        # Tool 1: 查询衣柜
        tool(
            name="search_wardrobe",
            description="查询用户衣柜中的衣物",
            args_schema=SearchWardrobeInput,
            func=search_wardrobe
        ),
        # Tool 2: 添加衣物
        tool(
            name="add_to_wardrobe",
            description="将衣物添加到用户衣柜",
            args_schema=AddToWardrobeInput,
            func=add_clothes
        ),
        # Tool 3: 搭配建议
        tool(
            name="match_outfit",
            description="为新衣服匹配衣柜中的搭配",
            args_schema=MatchOutfitInput,
            func=match_outfit
        ),
    ]
```

#### 3.2.3 agent/tools/image.py

```python
from app.services.image_analysis import analyze_clothing_image, analyze_outfit_image

def create_image_tools():
    return [
        tool(
            name="analyze_clothing",
            description="分析单件衣物图片，提取品类/颜色/风格等属性",
            args_schema=AnalyzeClothingInput,
            func=analyze_clothing_image
        ),
        tool(
            name="analyze_outfit",
            description="分析整套穿搭图片，提取风格要素和搭配结构（用于找类似搭配）",
            args_schema=AnalyzeOutfitInput,
            func=analyze_outfit_image
        ),
    ]
```

#### 3.2.4 agent/tools/style.py

```python
from app.services.style import get_style_knowledge, apply_style

def create_style_tools():
    return [
        tool(
            name="get_style_info",
            description="获取指定风格的详细信息和搭配规则",
            args_schema=GetStyleInfoInput,
            func=get_style_knowledge
        ),
        tool(
            name="apply_style_to_items",
            description="将指定风格应用于衣物列表",
            args_schema=ApplyStyleInput,
            func=apply_style
        ),
    ]
```

#### 3.2.4 agent/core.py

```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent
from langchain.tools.render import render_text_description

def create_conversation_agent(
    llm,
    tools: list[BaseTool],
    system_prompt: str
) -> Runnable:
    """构建对话 Agent"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    # 包装为带对话历史的 Agent
    return RunnableWithMessageHistory(
        agent,
        get_session_history,  # 来自 memory.py
        input_messages_key="input",
        history_messages_key="chat_history",
    )
```

### 3.3 Routers 层

#### 3.3.1 chat.py

```python
@router.post("/chat/message")
async def chat_message(
    req: ChatRequest,
    session_id: str = Body(...),  # 前端传入
    user_id: str = Body(...)
):
    # 从 Redis 获取短期记忆
    memory = await session_memory.get(session_id)

    # 调用 Agent
    response = await agent.ainvoke({
        "input": req.message,
        "user_id": user_id
    }, config={"session_id": session_id})

    # 更新短期记忆
    await session_memory.update(session_id, response["context"])

    return response
```

#### 3.3.2 clothes.py

```python
@router.post("/clothes/add")
async def add_clothes(
    req: AddClothesRequest,
    user_id: str = Depends(get_current_user)
):
    # 如果有图片，先分析
    if req.image_url:
        attrs = image_analysis.analyze_clothing_image(req.image_url)
        # 入库
        item = wardrobe.add_clothes(user_id, attrs)
    else:
        item = wardrobe.add_clothes(user_id, req.attrs)

    return item
```

---

## 4. 核心对话流程

### 4.1 穿搭推荐流程

```
用户输入："帮我生成明天去北京的穿搭"

Step 1: 解析用户意图
  → 识别为【穿搭推荐】意图

Step 2: 检查短期记忆
  → 已有: {date: "明天", location: "北京"}
  → 缺失: {occasion}

Step 3: 提问补全信息
  → AI 回复："去北京做什么呢？"

Step 4: 用户回答："上班"
  → 更新短期记忆: {date: "明天", location: "北京", occasion: "上班"}

Step 5: 执行穿搭生成
  → get_weather("北京") → {temp: 20, weather: "晴"}
  → search_wardrobe(user_id, filters={scene: "上班", season: "春"})
  → generate_outfit(user_id, context)

Step 6: 返回结果 + 更新记忆
```

### 4.2 图片处理流程

#### 4.2.1 单件衣物图片

```
用户上传图片（无命令）

Step 1: 检测到图片，无命令
  → 调用 analyze_clothing_image()
  → 返回属性 {type: "衬衫", color: "浅蓝", style: "商务"}

Step 2: 更新短期记忆
  → pending_image: "https://..."
  → image_attrs: {...}

Step 3: 等待用户下一步指令
```

```
用户后续输入："帮我入库"

Step 1: 检测到 pending_image + 命令"入库"
  → 调用 add_to_wardrobe(user_id, image_attrs)

Step 2: 清除 pending_image
```

```
用户后续输入："这件衣服怎么搭配"

Step 1: 检测到 pending_image + 命令"搭配"
  → wardrobe.match_outfit(image_attrs, user_wardrobe)

Step 2: 返回搭配建议
```

#### 4.2.2 整套穿搭图片（风格迁移）

```
用户上传整套穿搭图片，说"帮我找类似的搭配"

Step 1: 分析穿搭图片
  → analyze_outfit_image(img_url)
  → 返回 {
      overall_style: "美式复古",
      items: [
        {type: "牛仔外套", color: "深蓝"},
        {type: "白色T恤", color: "白色"},
        {type: "工装裤", color: "卡其"},
        {type: "靴子", color: "棕色"}
      ],
      style_tags: ["街头", "休闲", "复古"],
      color_palette: ["深蓝", "白色", "卡其"]
    }

Step 2: 更新短期记忆
  → pending_outfit_image: "https://..."
  → outfit_analysis: {...}

Step 3: 搜索用户衣柜
  → search_wardrobe(user_id, filters={
      compatible_styles: ["美式复古", "街头"],
      colors: ["深蓝", "白色", "卡其", "棕色"]
    })

Step 4: 生成类似搭配
  → generate_similar_outfit(user_id, outfit_analysis, context)
  → 返回 {
      matched_items: [
        {type: "牛仔衬衫", color: "深蓝", match_score: 0.9},  # 衣柜中有
        {type: "白色卫衣", color: "白色", match_score: 0.85}, # 衣柜中有
        {type: "卡其长裤", color: "卡其", match_score: 0.8}    # 衣柜中有
      ],
      missing_items: [
        {type: "工装靴", color: "棕色", importance: "高"}
      ],
      suggestions: "衣柜中已有牛仔衬衫、白色卫衣、卡其长裤，可以搭配出美式复古风格。建议购买一双棕色工装靴来完整体验这个风格。"
    }

Step 5: 清除 pending_outfit_image
```

### 4.3 风格化推荐流程

```
用户输入："给我推荐一套美式复古风的穿搭"

Step 1: 识别风格关键词
  → "美式复古" → 匹配到内置风格

Step 2: 加载风格知识库
  → get_style_knowledge("美式复古")
  → 返回 {tags: ["牛仔", "工装", "复古"], rules: [...], colors: [...]}

Step 3: 结合上下文
  → get_weather(user.location)
  → search_wardrobe(user_id, filters={compatible_with: style_tags})

Step 4: 应用风格规则
  → apply_style("美式复古", matched_items)
  → 快速筛选 + AI 调整

Step 5: 返回风格化穿搭方案
```

---

## 5. 数据模型

### 5.1 短期记忆 (Redis)

Key: `session:{session_id}`

```json
{
  "user_id": "user_xxx",
  "context": {
    "date": "明天",
    "location": "北京",
    "occasion": "上班"
  },
  "pending_image": null,
  "image_attrs": null,
  "pending_outfit_image": null,
  "outfit_analysis": null,
  "last_update": "2024-01-01T10:00:00Z"
}
```

TTL: 24 小时（次日自动清空）

**字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `pending_image` | string | 用户上传的待处理单件衣物图片 URL |
| `image_attrs` | dict | 已分析的单件衣物属性 |
| `pending_outfit_image` | string | 用户上传的整套穿搭图片 URL |
| `outfit_analysis` | dict | 已分析的整套穿搭风格要素 |

### 5.2 风格知识库 (数据库)

预定义风格存储在 `style_knowledge` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR | 风格名称 |
| tags | JSONB | 风格标签 ["牛仔", "工装"] |
| rules | JSONB | 搭配规则 |
| description | TEXT | 风格描述 |
| is_builtin | BOOLEAN | 是否内置 |
| user_id | UUID | 创建用户（null=内置） |

---

## 6. 废弃内容

重构后废弃以下内容：

| 文件/目录 | 原因 |
|-----------|------|
| `app/agent/agents/` | 旧版 Supervisor 实现 |
| `app/agent/graph/` | v1/v2/v3 并行工作流 |
| `app/agent/supervisor.py` | 多 Agent 路由逻辑 |
| `app/agent/dialogue_session.py` | 被 memory.py 替代 |
| `app/agent/memory.py` | 被 agent/memory.py 替代 |
| `app/agent/tools/context.py` | ContextVar DB 注入不再需要 |

---

## 7. 迁移计划

### Phase 1: 搭建基础设施
- [ ] 重构 `app/services/` 层（weather, wardrobe, image_analysis, outfit, style）
- [ ] 实现 `app/agent/memory.py`（Redis/Upstash 短期记忆）
- [ ] 创建 `app/agent/prompts/`

### Phase 2: 实现 Agent
- [ ] 实现 `app/agent/tools/` 各 Tool
- [ ] 实现 `app/agent/core.py`（Agent 构建器）
- [ ] 实现 `app/routers/chat.py`（对接 Agent）

### Phase 3: 清理废弃代码
- [ ] 删除 `app/agent/agents/`
- [ ] 删除 `app/agent/graph/`
- [ ] 删除 `app/agent/supervisor.py`
- [ ] 删除 `app/agent/dialogue_session.py`
- [ ] 删除 `app/agent/memory.py`（旧）
- [ ] 删除 `app/agent/tools/context.py`

### Phase 4: 扩展功能（未来）
- [ ] 天气联动（突变提醒、紫外线/雾霾预警）
- [ ] 穿搭评价（用户搭配方案验证）
- [ ] 偏好学习（从反馈中学习用户喜好）
- [ ] 场景识别增强（隐含意图识别：感冒→舒适、出行场景）
- [ ] 购物联动（缺失衣物推荐、商品分析）

---

## 8. 扩展预留设计

为未来功能预留架构空间，不在本期实现。

### 8.1 天气联动扩展

```python
# services/weather.py 预留
def get_weather_alert(location: str, current_outfit: Outfit) -> list[Alert]:
    """天气突变提醒，返回需要加衣/换衣的预警"""
    # 预留：雾霾天避免白色、降温提醒、紫外线提醒
```

### 8.2 穿搭评价扩展

```python
# services/outfit.py 预留
def evaluate_outfit(
    user_id: str,
    outfit_items: list[ClothingItem],
    context: OutfitContext = None
) -> EvaluationResult:
    """评价用户搭配是否合理，返回改进建议"""
    # 预留：颜色协调度、风格匹配度、场合适合度
```

### 8.3 偏好学习扩展

```python
# services/preference.py 预留（新增 service）
class PreferenceLearner:
    def record_feedback(self, user_id: str, item_id: str, feedback: Feedback):
        """记录用户对推荐结果的反馈（接受/拒绝/修改）"""

    def get_preferences(self, user_id: str) -> UserPreferences:
        """获取用户偏好，用于推荐优化"""
    # 预留：从对话中提取偏好（"太花了"、"不喜欢深色"）

# memory.py 预留
class ConversationPreferenceExtractor:
    def extract_from_message(self, message: str) -> dict:
        """从对话中提取用户偏好偏好"""
```

### 8.4 场景识别扩展

```python
# services/intent.py 预留（新增 service）
class IntentRecognizer:
    def recognize(self, message: str, context: dict) -> IntentResult:
        """增强版意图识别，支持隐含场景"""
        # 预留：感冒了→舒适需求、婚礼→正式场合、旅游→多日出行
```

### 8.5 购物联动扩展

```python
# services/shopping.py 预留（新增 service）
def suggest_purchase(missing_items: list[MissingItem]) -> list[PurchaseSuggestion]:
    """根据缺失衣物推荐购买"""
    # 预留：可对接电商 API 或品牌库

def analyze_product(url: str) -> ProductAnalysis:
    """分析商品是否值得购买"""
```

### 8.6 Agent Tools 扩展预留

```python
# agent/tools/evaluation.py 预留
def create_evaluation_tools():
    return [
        tool(name="evaluate_outfit", func=evaluate_outfit),
        tool(name="get_weather_alert", func=get_weather_alert),
    ]

# agent/tools/preference.py 预留
def create_preference_tools():
    return [
        tool(name="record_feedback", func=record_feedback),
        tool(name="get_user_preferences", func=get_preferences),
    ]
```

### 8.7 数据模型扩展

```sql
-- style_knowledge 表预留字段
ALTER TABLE style_knowledge ADD COLUMN occasion VARCHAR(50);  -- 适用场合
ALTER TABLE style_knowledge ADD COLUMN season VARCHAR(50);     -- 适用季节
ALTER TABLE style_knowledge ADD COLUMN temperature_range VARCHAR(50);  -- 适用温度

-- user_preferences 表（新增）
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY,
    disliked_colors JSONB,      -- 不喜欢的颜色
    disliked_styles JSONB,       -- 不喜欢的风格
    body_conditions JSONB,       -- 身体状况（怕冷/易过敏等）
    shopping_budget VARCHAR(50), -- 购物预算
    updated_at TIMESTAMP
);
```

---

## 9. 设计原则

1. **Services 层是核心**：不含 LangChain 依赖，可独立测试和复用
2. **Agent 层是薄封装**：Tools 调用 Services，不做复杂逻辑
3. **短期记忆透明**：Agent 无需知道记忆存储在哪，只管读/写
4. **图片惰性入库**：只有用户明确命令时才操作数据库
5. **风格知识可扩展**：内置风格 + 用户自定义，支持后续扩充
6. **架构预留扩展**：新功能通过新增 Service + Tool 实现，不修改核心架构
