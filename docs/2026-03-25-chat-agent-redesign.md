# Chat 模块重构：多能力 Agent 系统设计

> 创建时间：2026-03-25

## 一、现状分析

### 1.1 现有架构

当前 chat 模块基于 **LangGraph StateGraph**，核心是硬编码的意图路由：

```
intent_node → route_by_intent（硬编码 if-else）
    ├─ generate_outfit → weather → wardrobe → planning → response
    ├─ query_wardrobe → response
    ├─ feedback → response
    └─ response（追问）
```

**问题：**
- 意图路由硬编码在 `route_by_intent` + `response_node` 中
- 新增能力需改图结构、加条件边
- 追问逻辑分散在 `_build_missing_question`、`_handle_unknown` 等多处
- 图片处理（ClothesAgent）和对话（workflow）是两套独立系统，无法协同

### 1.2 现有服务可复用性

| 服务 | 可复用性 | 说明 |
|------|---------|------|
| `WeatherService` | ✅ 直接复用 | 纯函数，全局单例 |
| `ImageAnalyzer` | ✅ 直接复用 | 无状态，无 DB 依赖 |
| `ImageGenerator` | ✅ 直接复用 | 无状态，无 DB 依赖 |
| `oss_uploader` | ✅ 直接复用 | 全局单例 |
| `query_wardrobe()` | ⚠️ 需提取 | DB 查询逻辑可封装 |
| `outfit_planning_node` | ⚠️ 需提取 | LLM 调用可封装 |
| `ClothesAgent.run()` | ⚠️ 需拆分 | 分析+生成+存储应分离 |
| `PlanAgent` 色彩方案 | ❌ 废弃 | 被 LLM 替代 |
| `CombineAgent` | ❌ 废弃 | 被 LLM 替代 |
| `short_circuit.py` | ❌ 废弃 | 与 evaluation_node 重复 |

---

## 二、设计目标

1. **LLM 驱动的意图路由**：Agent 自主选择工具，而非硬编码 if-else
2. **工具可复用**：图片处理、天气查询等独立工具可被多个场景调用
3. **单 Supervisor + 工具集**：Supervisor 统一编排，所有工具平级注册
4. **减少硬编码**：追问策略、穿衣规则写入 Prompt
5. **多模态支持**：图片和文字同等对待

---

## 三、目标架构

### 3.1 系统概览

```
用户消息（文字 + 可选图片）
         │
         ▼
┌───────────────────────────────────────┐
│        ConversationManager               │
│  （管理对话历史、Session 持久化）       │
└─────────────────┬─────────────────────┘
                  │
         ┌────────▼────────┐
         │  SupervisorAgent  │ ← 唯一的 Agent，LLM 驱动
         └────────┬────────┘
                  │ Function Calling
    ┌────────────┼──────────────────────┐
    │            │                      │
┌───▼───┐  ┌────▼────┐  ┌────────────▼──────┐
│Shared  │  │Wardrobe │  │ Outfit            │
│Tools   │  │Tools    │  │ Tools             │
└────────┘  └─────────┘  └──────────────────┘
```

### 3.2 工具分类（按业务分组，非 Agent 实体）

> **重要澄清**：WardrobeAgent 和 OutfitAgent **不是真正的 Agent**。它们只是工具的业务分组命名空间，不拥有独立的 System Prompt 或 LLM 调用。真正的 Agent 只有 SupervisorAgent 一个。

| 分类 | 工具名 | 功能 |
|------|--------|------|
| **SharedTools** | `get_weather` | 获取城市天气（温度/湿度/状况） |
| | `analyze_clothing_image` | 分析衣物图片（材质/颜色/类别/适合天气） |
| | `remember_context` | 记住当前对话中的关键信息 |
| | `recall_context` | 回忆已记住的上下文信息 |
| **WardrobeTools** | `search_wardrobe` | 按条件查询用户衣柜 |
| | `add_clothes_to_wardrobe` | 上传图片、分析、生成卡通图、存储 DB |
| **OutfitTools** | `plan_outfit` | 基于衣柜和场景生成穿搭方案（纯计算） |
| | `get_outfit_history` | 查询用户的穿搭历史 |
| **KnowledgeTools** | `search_knowledge_base` | 穿搭知识问答（简化版 RAG） |

---

## 四、核心组件设计

### 4.1 SupervisorAgent

Supervisor 是整个系统的**唯一 Agent**，使用 **OpenAI Function Calling** 让 LLM 自主决定调用哪些工具。

**设计原则：**
- Tool 必须是**无副作用的纯计算单元**，不得在 Tool 内部调用其他 Tool
- 所有跨工具编排（get_weather → search_wardrobe → plan_outfit 的串联）由 Supervisor 的 tool_call 循环负责
- 这样 Supervisor 能感知每个工具的执行过程，实现流式体验

**System Prompt 设计：**

```
你是一个专业的时尚穿搭助手。

【你的能力】
- 根据天气和场合推荐穿搭
- 识别和管理衣柜中的衣物
- 查询穿搭历史
- 回答天气相关问题
- 提供穿搭知识建议

【工具使用规则】
- 用户请求穿搭推荐 → 先调用 get_weather，再调用 search_wardrobe，最后调用 plan_outfit
  （注意：plan_outfit 需要传入 weather 数据和 wardrobe 数据，不要在 plan_outfit 内部再次查询）
- 用户上传衣物图片 → 先 analyze_clothing_image 识别，再用 add_clothes_to_wardrobe 存储
- 用户询问历史 → 直接调用 get_outfit_history
- 用户提到城市/场合/日期 → 调用 remember_context 记住信息

【追问策略】
- 缺少城市 → "请问要去哪个城市呢？"
- 缺少场合 → "请问是什么场合呢？（上班/约会/运动...）"
- 用户意图不明 → "我需要更多信息来帮您，请描述一下具体需求？"

【穿衣规则】（内置知识，可直接使用）
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）

【反馈处理】
- 用户说"太正式/太休闲/换个颜色" → 调用 remember_context 更新 scene/style，再调用 plan_outfit
- 用户说"再推荐一套" → 直接调用 plan_outfit（不重复问）
- 用户说"就这套了" → 调用 save_outfit_history 记录
```

**Supervisor Loop 实现：**

```python
class SupervisorAgent:
    def __init__(self, tools: list, session_id: str, user_id: str):
        self.tools = {t.name: t for t in tools}
        self.session_id = session_id
        self.user_id = user_id
        self.memory = AgentMemory(session_id, user_id)
        self.llm = get_cached_provider().chat_model
        self.llm_with_tools = self.llm.bind_tools(list(self.tools.values()))

    async def run_stream(self, user_message: str, images: list[str] = None) -> AsyncGenerator[dict, None]:
        """
        流式执行。yield SSE 事件：
        - thinking: LLM 决策中
        - tool_called: 工具执行前
        - tool_result: 工具执行后
        - text: LLM 输出文本片段
        - outfit_card: 穿搭卡片
        - done: 完成
        - error: 异常
        """
        messages = self._build_messages(user_message, images)
        yield {"type": "thinking", "content": "正在分析您的请求..."}

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
                messages.append(ToolMessage(name=tc.name, content=result))

            response = await self.llm_with_tools.ainvoke(messages)

        # 最终文本
        yield {"type": "text", "content": response.content}
        yield {"type": "done", "content": response.content}

    def _build_messages(self, user_message: str, images: list[str] = None) -> list:
        """构建消息列表，注入上下文"""
        # 1. 当前记住的信息
        memory_text = self.memory.to_context_string()
        # 2. 缺失字段（用于追问）
        missing = self.memory.missing_fields
        missing_text = f"\n【当前缺少的信息】需要用户提供：{', '.join(missing)}" if missing else ""

        system = SYSTEM_PROMPT + f"\n\n【当前记住的信息】\n{memory_text}{missing_text}"

        messages = [SystemMessage(content=system)]

        # 3. 最近 6 条历史消息（约 1000-2000 tokens）
        for msg in self.memory.recent_messages[-6:]:
            messages.append(HumanMessage(content=msg["content"]))

        # 4. 用户消息（含多模态图片）
        if images:
            content = [{"type": "text", "text": user_message}]
            for img in images:
                content.append({"type": "image_url", "image_url": img})
            messages.append(HumanMessage(content=content))
        else:
            messages.append(HumanMessage(content=user_message))

        return messages
```

---

### 4.2 AgentMemory

替代现有的 `ConversationContext`，作为 Agent 的统一记忆接口。

```python
# agent/memory.py

@dataclass
class AgentMemory:
    """Agent 的记忆，管理跨轮次上下文"""
    session_id: str
    user_id: str

    # 当前任务信息
    target_city: Optional[str] = None
    target_scene: Optional[str] = None
    target_date: Optional[str] = None
    target_temperature: Optional[float] = None

    # 未完成的任务
    pending_task: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)

    # 偏好
    preferred_style: Optional[str] = None
    frequent_colors: List[str] = field(default_factory=list)

    # 对话历史（最近 N 条，用于注入 LLM）
    recent_messages: List[Dict] = field(default_factory=list)

    def to_context_string(self) -> str:
        """转化为 LLM 可读的上下文字符串"""
        parts = []
        if self.target_city: parts.append(f"城市：{self.target_city}")
        if self.target_scene: parts.append(f"场合：{self.target_scene}")
        if self.target_date: parts.append(f"日期：{self.target_date}")
        if self.target_temperature: parts.append(f"温度：{self.target_temperature}℃")
        if self.pending_task:
            parts.append(f"正在进行：{self.pending_task}（缺少：{', '.join(self.missing_fields)}）")
        if self.preferred_style: parts.append(f"风格偏好：{self.preferred_style}")
        return "\n".join(parts) if parts else "无已记住的信息"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_context_dict(self) -> dict:
        """转为 ConversationContext 格式，供 Session 持久化用"""
        return {
            "target_city": self.target_city,
            "target_scene": self.target_scene,
            "target_date": self.target_date,
            "target_temperature": self.target_temperature,
            "asking_for": self.missing_fields[0] if self.missing_fields else None,
            "pending_intent": self.pending_task,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMemory":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史（最多保留 20 条）"""
        self.recent_messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(self.recent_messages) > 20:
            self.recent_messages = self.recent_messages[-20:]
```

**与 Session 持久化的关系：**
- `AgentMemory` 实例化时从 `DialogueSessionManager.get(session_id)` 恢复：`AgentMemory.from_dict(session.context.to_dict())`
- 每次 tool_loop 结束后，`memory.to_context_dict()` 写回 Session
- **Session 保存必须是无条件的**（lesson learned：不在 if-else 中，放在 finally）

---

### 4.3 工具 Schema（Function Calling 参数定义）

LLM 通过 Schema 决定调用哪个 Tool。每个 Tool 必须定义完整的 description 和 parameters。

#### get_weather

```python
{
    "name": "get_weather",
    "description": "获取指定城市的天气信息，包括温度、湿度和天气状况。
        当用户询问天气，或需要为穿搭推荐获取天气数据时使用。",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，如'杭州'、'北京'、'上海'"
            },
            "date": {
                "type": "string",
                "description": "查询日期，格式为 YYYY-MM-DD，或'今天'/'明天'/'后天'"
            }
        },
        "required": ["city"]
    }
}
```

#### search_wardrobe

```python
{
    "name": "search_wardrobe",
    "description": "搜索用户衣柜中的衣物，按类别、颜色或场合筛选。
        用于穿搭推荐前获取用户已有的衣物。",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["top", "pants", "outer", "inner", "accessory"],
                "description": "衣物类别"
            },
            "color": {
                "type": "string",
                "description": "颜色，如'白色'、'黑色'、'蓝色'"
            },
            "scene": {
                "type": "string",
                "enum": ["daily", "work", "sport", "date", "party", "casual", "formal"],
                "description": "适合场合"
            }
        },
        "required": []
    }
}
```

#### plan_outfit

```python
{
    "name": "plan_outfit",
    "description": "根据用户衣柜中的衣物、天气和场合生成穿搭方案。
        调用前请确保已通过 get_weather 获取温度，并通过 search_wardrobe 获取衣柜衣物，
        然后将结果作为 wardrobe_items 参数传入。此 Tool 不再查询天气或衣柜。",
    "parameters": {
        "type": "object",
        "properties": {
            "scene": {
                "type": "string",
                "enum": ["daily", "work", "sport", "date", "party", "casual", "formal"],
                "description": "场合类型"
            },
            "temperature": {
                "type": "number",
                "description": "当前温度（℃），如 18.5"
            },
            "wardrobe_items": {
                "type": "array",
                "description": "search_wardrobe 返回的衣物列表（直接传入，无需二次查询）"
            },
            "max_options": {
                "type": "integer",
                "description": "最多返回的方案数量",
                "default": 3
            }
        },
        "required": ["scene", "temperature", "wardrobe_items"]
    }
}
```

#### 其他工具 Schema

| 工具名 | 关键参数 |
|--------|---------|
| `analyze_clothing_image` | `image_url: str`, `user_hint: str`（可选） |
| `add_clothes_to_wardrobe` | `image_url: str`, `name: str`（可选） |
| `get_outfit_history` | `date: str`（可选）, `limit: int`（默认 10） |
| `remember_context` | `city: str`, `scene: str`, `date: str`, `temperature: float`（均可选） |
| `recall_context` | 无参数 |
| `search_knowledge_base` | `query: str` |

---

### 4.4 工具实现

#### 4.4.1 SharedTools（shared.py）

```python
# agent/tools/shared.py
# DB 通过 ContextVar 注入，详见 4.6

@tool
async def get_weather(city: str, date: str = None) -> str:
    """获取城市天气信息"""
    result = await weather_service.get_weather(city, date)
    return json.dumps(result, ensure_ascii=False)

@tool
async def analyze_clothing_image(image_url: str, user_hint: str = None) -> str:
    """分析衣服图片"""
    from app.agent.clothes_agent import ANALYSIS_PROMPT
    result = await image_analyzer.analyze(image_url=image_url, prompt=ANALYSIS_PROMPT)
    return json.dumps(result, ensure_ascii=False)

@tool
async def remember_context(city: str = None, scene: str = None,
                           date: str = None, temperature: float = None) -> str:
    """记住当前对话中的关键信息到 Session"""
    session_manager.update_context(city=city, scene=scene, date=date, temperature=temperature)
    return json.dumps({"status": "remembered"})

@tool
async def recall_context() -> str:
    """回忆已记住的上下文"""
    ctx = session_manager.get_context()
    return json.dumps(ctx, ensure_ascii=False)
```

#### 4.4.2 WardrobeTools（wardrobe.py）

```python
# agent/tools/wardrobe.py

@tool
async def search_wardrobe(category: str = None, color: str = None,
                          scene: str = None) -> str:
    """搜索用户衣柜中的衣物"""
    from app.agent.graph.nodes.wardrobe import query_wardrobe
    db = get_db_for_tools()
    user_id = get_current_user_id()
    items = query_wardrobe(db, user_id, category=category, color=color, tags=None)
    return json.dumps(items, ensure_ascii=False, default=str)

@tool
async def add_clothes_to_wardrobe(image_url: str, name: str = None) -> str:
    """将衣物添加到用户衣柜（分析+生成卡通图+存储）"""
    from app.agent.clothes_agent import clothes_agent
    from app.services.image_analysis import image_analyzer
    from app.services.image_generator import image_generator

    db = get_db_for_tools()
    user_id = get_current_user_id()

    # 并行分析 + 生成卡通图
    analysis, cartoon = await asyncio.gather(
        image_analyzer.analyze(image_url=image_url),
        image_generator.generate(reference_image_url=image_url)
    )

    # 存储到 DB
    clothes = clothes_agent._create_clothes_record(db, user_id, image_url,
        type("R", (), {"name": name, "color": analysis.get("color"),
                        "category": analysis.get("category"),
                        "material": analysis.get("material"),
                        "temperature_range": analysis.get("temperature_range"),
                        "wear_method": analysis.get("wear_method"),
                        "scene": analysis.get("scene"),
                        "generated_image_url": cartoon})()
    )
    return json.dumps({"clothes_id": str(clothes.id), **analysis}, ensure_ascii=False)
```

#### 4.4.3 OutfitTools（outfit.py）

```python
# agent/tools/outfit.py

@tool
async def plan_outfit(scene: str, temperature: float, wardrobe_items: list,
                      max_options: int = 3) -> str:
    """
    纯计算：基于已有数据生成穿搭方案。
    weather 和 wardrobe 数据由 Supervisor 的 tool_loop 预先获取后传入，
    此 Tool 不再查询天气或衣柜。
    """
    from app.agent.graph.nodes.planning import create_planning_prompt
    from app.services.llm_providers import get_cached_provider
    from langchain_core.messages import HumanMessage, SystemMessage

    PLANNING_SYSTEM_PROMPT = """你是一个专业穿搭顾问，基于用户衣柜中的衣物生成穿搭方案。..."""

    # 按品类分组
    wardrobe_by_category = {}
    for item in wardrobe_items:
        cat = item.get("category", "unknown")
        wardrobe_by_category.setdefault(cat, []).append(item)

    prompt = create_planning_prompt(
        target_date=None,
        target_city=None,
        target_scene=scene,
        temperature=temperature,
        wardrobe_by_category=wardrobe_by_category,
        available_categories=list(wardrobe_by_category.keys()),
        missing_categories=[],
    )

    llm = get_cached_provider().chat_model
    response = await llm.ainvoke([
        SystemMessage(content=PLANNING_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    # 解析 JSON（复用现有逻辑）
    import re
    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if json_match:
        return json_match.group()
    return json.dumps({"description": response.content})

@tool
async def get_outfit_history(date: str = None, limit: int = 10) -> str:
    """查询用户的穿搭历史记录"""
    db = get_db_for_tools()
    user_id = get_current_user_id()
    result = await query_history(db, user_id, date, limit)
    return json.dumps(result, ensure_ascii=False)
```

#### 4.4.4 KnowledgeTools（knowledge.py）

```python
# agent/tools/knowledge.py

KNOWLEDGE_FAQ = [
    {"q": "春天怎么搭配颜色", "a": "春季适合柔和的粉色、浅蓝、米色。建议选择可叠穿的搭配，外套选中性色。"},
    {"q": "面试穿什么合适", "a": "建议深色西装或简约商务装。男生：白衬衫+深色西装+领带；女生：衬衫+西裤或及膝裙。"},
    {"q": "如何保养羊毛衫", "a": "建议手洗，水温不超过30℃。平铺晾干，避免悬挂变形。可用羊毛专用洗涤剂。"},
]

@tool
async def search_knowledge_base(query: str) -> str:
    """穿搭知识问答（简化版，无向量数据库）"""
    # 简单关键词匹配
    best_match = None
    best_score = 0
    for faq in KNOWLEDGE_FAQ:
        score = sum(1 for kw in query if kw in faq["q"])
        if score > best_score:
            best_score = score
            best_match = faq
    if best_match:
        return json.dumps({"answer": best_match["a"], "source": "knowledge_base"})
    return json.dumps({"answer": None, "source": "knowledge_base"})
```

---

### 4.5 流式响应（SSE）设计

> **P0**：现有系统用 LangGraph `astream` 流式。切换 Function Calling 后需要重新实现。

**SSE 事件类型：**

| 事件类型 | 触发时机 | 数据内容 |
|---------|---------|---------|
| `thinking` | LLM 决策中 | `{"content": "正在分析您的请求..."}` |
| `tool_called` | 工具执行前 | `{"tool": "get_weather", "args": {"city": "杭州"}}` |
| `tool_result` | 工具执行后 | `{"tool": "get_weather", "result": {...}}` |
| `text` | LLM 输出文本 | `{"content": "杭州今天晴，18℃..."}` |
| `outfit_card` | 穿搭卡片 | `{"outfits": [...], "scene": "work", ...}` |
| `done` | 完成 | `{"content": "..."}` |
| `error` | 异常 | `{"code": "weather_api_timeout", "message": "..."}` |

**chat.py 中的 Session 保存（无条件）：**

```python
# routers/chat.py
async def chat_message_stream(request):
    try:
        agent = SupervisorAgent(...)
        async for event in agent.run_stream(request.message, request.images):
            yield _sse_event(event["type"], event)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        yield _sse_event("error", {"code": type(e).__name__, "message": str(e)})
    finally:
        # 无条件保存！不放在 if-else 中
        success = _do_save(memory, session, session_mgr)
        if success:
            yield _sse_event("done", {"session_id": session.session_id})
```

---

### 4.6 数据库依赖注入

> **P1**：Tool 需要 DB session，但 Tool 实例化时无法通过参数注入。

**方案**：使用 `contextvars` 上下文变量：

```python
# agent/tools/context.py
from contextvars import ContextVar
from sqlalchemy.orm import Session

_db_session: ContextVar[Session] = ContextVar("db_session")
_user_id: ContextVar[str] = ContextVar("user_id")

def get_db_for_tools() -> Session:
    return _db_session.get()

def get_current_user_id() -> str:
    return _user_id.get()

# routers/chat.py 中设置
async def chat_message_stream(request):
    db = get_db()  # FastAPI Depends
    _db_session.set(db)
    _user_id.set(request.user_id)
    # ...
```

---

### 4.7 错误处理与重试

> **P2**：任何工具都可能失败，需要统一处理。

**原则：**
- 每个 Tool 执行加 try-except，异常时返回错误 JSON：
  ```python
  {"error": "weather_api_timeout", "message": "天气服务暂时不可用"}
  ```
- Supervisor 的 tool_loop 中，工具失败时**不中断**，将错误传回 LLM
- LLM 决定：重试、降级（用缓存）、或告知用户
- `max_turns=10` 达到时强制结束，返回当前结果并注明已达上限

---

### 4.8 多模态图片处理

> **P1**：图片格式、上传流程。

- 前端上传图片到 OSS，传入图片 URL
- `images: list[str]` 为 OSS URL 列表
- 多张图片：逐个添加 `{"type": "image_url", "image_url": url}` 到 content list
- 历史中的图片 URL 只存字符串，不重复传图片内容（节省 token）

---

## 五、对话流程示例

### 5.1 天气查询

```
用户：杭州今天多少度
Supervisor → get_weather(city="杭州", date="今天")
    → 返回 {"temperature": 18, "condition": "晴"}
Supervisor → "今天杭州晴，18℃。这个温度穿长袖+轻薄外套就够了～"
```

### 5.2 穿搭推荐（完整 tool_call 串联）

```
用户：帮我推荐穿搭
Supervisor → recall_context()
    → 上下文为空
Supervisor → "请问要去哪个城市呢？"（missing_fields = ["city"]）

用户：杭州
Supervisor → remember_context(city="杭州")
    → "记住了！请问是什么场合呢？"（missing_fields = ["scene"]）

用户：约会
Supervisor → remember_context(scene="date")
    → tool_loop 开始：
        1. get_weather(city="杭州") → {"temperature": 18}
        2. search_wardrobe() → 衣物列表
        3. plan_outfit(scene="date", temperature=18, wardrobe_items=[...])
    → 返回方案列表（👕👖🧥 卡片）
```

### 5.3 衣物入库

```
用户：[上传衣服图片]
Supervisor → analyze_clothing_image(image_url=...)
    → 返回 {"name": "白色棉质T恤", "category": "top", "color": "白色", ...}
Supervisor → "这是白色棉质T恤，适合春秋季。帮您存到衣柜？"
    → add_clothes_to_wardrobe(image_url)
    → 存储成功
Supervisor → "已存好！还有其他衣服要上传吗？"
```

### 5.4 查询历史

```
用户：我上周穿了什么
Supervisor → get_outfit_history(user_id, date="2026-03-18")
    → 返回历史记录列表
Supervisor → "上周三您穿了一套蓝色衬衫+牛仔裤去上班，匹配度 92 分～"
```

---

## 六、实施计划

### Phase 1：基础设施

1. 创建 `agent/tools/context.py` — ContextVar DB session 注入
2. 创建 `agent/tools/shared.py` — 共享工具（get_weather、analyze_clothing_image、remember_context、recall_context）
3. 创建 `agent/memory.py` — AgentMemory 替代 ConversationContext

### Phase 2：业务工具

4. 创建 `agent/tools/wardrobe.py` — SearchWardrobe、AddClothes
5. 创建 `agent/tools/outfit.py` — PlanOutfit（**纯计算，不内嵌工具调用**）
6. 创建 `agent/tools/knowledge.py` — SearchKnowledgeBase（简化版 FAQ）

### Phase 3：SupervisorAgent

7. 创建 `agent/supervisor.py` — SupervisorAgent（核心，bind_tools + run_stream）
8. 修改 `routers/chat.py` — 接入新 workflow，保留 SSE 事件

### Phase 4：清理

9. 废弃旧版文件：plan_agent、combine_agent、short_circuit、tools.py、graph/edges.py、graph/nodes/（除 response.py 保留）

---

## 七、涉及文件

| 文件 | 操作 |
|------|------|
| `agent/tools/context.py` | 新增 — ContextVar DB 注入 |
| `agent/tools/shared.py` | 新增 — 共享工具 |
| `agent/tools/wardrobe.py` | 新增 — 衣柜工具 |
| `agent/tools/outfit.py` | 新增 — 穿搭工具（纯计算） |
| `agent/tools/knowledge.py` | 新增 — 知识问答 |
| `agent/memory.py` | 新增 — AgentMemory |
| `agent/supervisor.py` | 新增（重写）— SupervisorAgent |
| `routers/chat.py` | 修改 — 接入新 workflow |
| `agent/graph/edges.py` | 废弃 |
| `agent/graph/nodes/` | 废弃（除 response.py） |
| `agent/plan_agent.py` | 废弃 |
| `agent/combine_agent.py` | 废弃 |
| `agent/short_circuit.py` | 废弃 |
| `agent/tools.py` | 废弃 |

---

## 八、验证方案

1. 天气查询：发送"杭州今天多少度" → 返回天气+穿衣建议
2. 穿搭推荐：3 轮对话（推荐穿搭→杭州→约会）→ 生成方案，观察 SSE tool_called 事件
3. 图片识别：发送衣服图片 → 返回识别结果
4. 衣物入库：图片+"帮我存衣柜" → 存储成功
5. 历史查询：发送"我上周穿了什么" → 返回历史
6. Session 持久化：3 轮后重启，同一 session_id 记住之前信息
7. 回归测试：现有 API（/clothes/add, /history/list）继续正常工作

---

## 九、架构决策记录

### D1：单 Supervisor 架构（不使用子 Agent）

**决策**：不将 WardrobeAgent / OutfitAgent 实现为真正的 Agent（无独立 System Prompt + LLM 调用）。

**理由**：
- 当前场景没有 Agent 间相互协商的需求
- `search_wardrobe` 是纯 DB 查询，无推理需求
- `plan_outfit` 是单次 LLM 调用，无多轮交互需求
- 真正的多 Agent 需要额外 2+ 次 LLM 调用，成本高但无收益

**何时重审**：当出现"用户同时请求穿搭+衣柜查询，需要并行执行"或"OutfitAgent 在规划时需要向 WardrobeAgent 询问替代品"等场景时，再评估。

### D2：Tool 纯计算原则

**决策**：Tool 不得在内部调用其他 Tool。所有跨工具编排由 Supervisor 的 tool_call 循环负责。

**理由**：
- Supervisor 能感知每个工具的执行过程，实现流式体验（用户可见"正在查询天气..."）
- Tool 职责单一，易于测试和复用
- 避免嵌套 tool_call 的复杂度

### D3：Session 保存无条件

**决策**：Session 持久化必须放在 `finally` 块，不放在任何 if-else 中。

**教训来源**：原 LangGraph 方案中，`should_end=True` 分支（主动追问时）是空的，`else` 分支才保存，导致追问时数据丢失。Lesson learned: 任何分支条件都可能遗漏，统一无条件保存。

### D4：城市不依赖 LLM 提取

**决策**：城市信息直接从 session context 读取，不从 LLM 返回的 entities 中提取。

**理由**：LLM 输出格式不稳定（可能返回 `{"city": null}`、`{"city": ""}`、或省略字段），导致城市丢失。直接从 session context 读取是确定性的，更可靠。

---

## P2 完成记录

**完成时间**：2026-03-25

**已完成文件**：

| 文件 | 状态 | 说明 |
|------|------|------|
| `service/app/agent/supervisor.py` | ✅ 已完成 | SupervisorAgent（LLM Function Calling）+ 旧版 Supervisor（兼容） |
| `service/app/routers/chat.py` | ✅ 已完成 | 接入 SupervisorAgent，新增 `images` 字段，保留旧版非流式接口 |
| `service/app/agent/__init__.py` | ✅ 已完成 | 更新导出：SupervisorAgent + Supervisor 兼容 |

**关键实现**：

- `SupervisorAgent` 使用 `llm.bind_tools()` 实现 Function Calling，LLM 自主选择工具
- `run_stream()` 是异步生成器，yield SSE 事件：`thinking` / `tool_called` / `tool_result` / `text` / `done`
- `AgentMemory` 从 Session 恢复上下文，`save_to_session()` 无条件写回
- `ChatMessageRequest` 新增 `images: Optional[List[str]]` 字段（OSS 图片 URL）
- 旧版 `Supervisor` 类保留在 `supervisor.py` 底部，供衣柜穿搭推荐功能使用

**验证结果**：

```
supervisor OK
chat router OK
```
