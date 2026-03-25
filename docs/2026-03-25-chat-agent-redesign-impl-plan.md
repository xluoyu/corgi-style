# Chat 模块重构：技术实施方案

> 创建时间：2026-03-25
> 基于：`docs/2026-03-25-chat-agent-redesign.md`

---

## 一、方案概述

### 目标架构

将现有的 **LangGraph StateGraph + 硬编码意图路由** 重构为 **LLM 驱动的单 Supervisor + 工具集** 架构。

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

### 核心变化

| 维度 | 现状 | 目标 |
|------|------|------|
| 意图路由 | `route_by_intent` 硬编码 if-else | LLM 自主选择工具 |
| 新增能力 | 需改图结构、加条件边 | 只需注册新 Tool |
| 追问逻辑 | 分散在多处 | 写入 System Prompt |
| 工具协同 | 图片处理和对话独立 | 统一 Supervisor 编排 |
| 流式体验 | 节点级（intent/weather/...） | Tool 级（get_weather/plan_outfit/...） |

---

## 二、前后端分工

### 后端改动（service/）

| 阶段 | 文件 | 操作 | 复杂度 |
|------|------|------|--------|
| P0 | `agent/tools/context.py` | ~~新增~~ ✅ 已完成（2026-03-25）— ContextVar DB 注入 | 低 |
| P0 | `agent/memory.py` | ~~新增~~ ✅ 已完成（2026-03-25）— AgentMemory 替代 ConversationContext | 中 |
| P0 | `agent/tools/shared.py` | ~~新增~~ ✅ 已完成（2026-03-25）— get_weather、analyze_clothing_image、remember_context、recall_context | 中 |
| P1 | `agent/tools/wardrobe.py` | ~~新增~~ ✅ 已完成（2026-03-25）— search_wardrobe、add_clothes_to_wardrobe | 低 |
| P1 | `agent/tools/outfit.py` | ~~新增~~ ✅ 已完成（2026-03-25）— plan_outfit（纯计算）、get_outfit_history | 中 |
| P1 | `agent/tools/knowledge.py` | ~~新增~~ ✅ 已完成（2026-03-25）— search_knowledge_base（简化 FAQ） | 低 |
| P2 | `agent/supervisor.py` | ~~重写~~ ✅ 已完成（2026-03-25）— SupervisorAgent（核心） | 高 |
| P2 | `routers/chat.py` | ~~修改~~ ✅ 已完成（2026-03-25）— 接入新 workflow，新增 images 字段 | 中 |
| P3 | `agent/plan_agent.py` | 废弃 | — |
| P3 | `agent/combine_agent.py` | 废弃 | — |
| P3 | `agent/short_circuit.py` | 废弃 | — |
| P3 | `agent/tools.py` | 废弃 | — |
| P3 | `agent/graph/edges.py` | 废弃 | — |
| P3 | `agent/graph/nodes/` | 废弃（保留 `response.py`） | — |

### 前端改动（app/）

| 文件 | 改动 | 复杂度 |
|------|------|--------|
| `src/app/chat/page.tsx` | 新增 `tool_called` / `tool_result` SSE 事件处理；修改 ThinkingIndicator 展示格式 | 低 |
| `src/app/chat/ThinkingIndicator.tsx` | 支持展示 Tool 调用状态（图标 + 工具名 + 参数） | 低 |
| `src/types/chat.ts` | 新增 `ToolCalledItem` / `ToolResultItem` 类型定义 | 低 |

> **说明**：前端已有 SSE 流式处理基础设施，主要改动是增加 2 个事件类型的展示逻辑，无需大的架构调整。

---

## 三、实施任务详解

### 阶段 1：基础设施（P0，必须先完成）

#### T1-1：`agent/tools/context.py` — ContextVar DB 注入

**目标**：解决 Tool 无法通过参数注入 DB session 的问题。

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

def set_tool_context(db: Session, user_id: str):
    _db_session.set(db)
    _user_id.set(user_id)
```

**依赖**：无
**验证**：单独 import 该模块，确认无报错。

#### T1-2：`agent/memory.py` — AgentMemory

**目标**：替代 `ConversationContext`，作为 Agent 的统一记忆接口。

**字段**：
- `target_city`、`target_scene`、`target_date`、`target_temperature` — 当前任务信息
- `missing_fields: List[str]` — 缺失字段（追问用）
- `preferred_style`、`frequent_colors` — 偏好
- `recent_messages: List[Dict]` — 最近 20 条对话历史

**关键方法**：
- `to_context_string()` → 供 LLM 读取的上下文字符串
- `to_dict()` / `from_dict()` → 与 Session 序列化兼容
- `add_message(role, content)` → 添加消息（超过 20 条自动截断）

**复用现有**：`ConversationContext` 的字段映射到 `AgentMemory`，保持向后兼容。

**依赖**：T1-1
**验证**：`AgentMemory.from_dict()` 能正确恢复 `ConversationContext.to_dict()` 格式的数据。

#### T1-3：`agent/tools/shared.py` — 共享工具

**工具列表**：

| 工具名 | 功能 | 复用服务 |
|--------|------|---------|
| `get_weather` | 获取城市天气 | `WeatherService`（直接复用） |
| `analyze_clothing_image` | 分析衣物图片 | `ImageAnalyzer`（直接复用） |
| `remember_context` | 记住上下文到 Session | 调用 `DialogueSessionManager.update_context` |
| `recall_context` | 回忆已记住的上下文 | 调用 `DialogueSessionManager.get_context` |

每个 Tool 用 `@tool` 装饰器（LangChain），内部通过 `get_db_for_tools()` / `get_current_user_id()` 获取 DB 和用户。

**Schema 示例**（`get_weather`）：

```python
@tool
async def get_weather(city: str, date: str = None) -> str:
    """获取指定城市的天气信息，包括温度、湿度和天气状况。
    当用户询问天气，或需要为穿搭推荐获取天气数据时使用。"""
    result = await weather_service.get_weather(city, date)
    return json.dumps(result, ensure_ascii=False)
```

**依赖**：T1-1、T1-2
**验证**：各工具独立调用成功（mock DB 上下文）。

---

### 阶段 2：业务工具（P1）

#### T2-1：`agent/tools/wardrobe.py` — 衣柜工具

| 工具名 | 功能 |
|--------|------|
| `search_wardrobe` | 按类别/颜色/场合搜索用户衣柜 |
| `add_clothes_to_wardrobe` | 分析图片 + 生成卡通图 + 存储 DB |

**复用现有**：
- `app.agent.graph.nodes.wardrobe.query_wardrobe` — 提取为工具
- `app.agent.clothes_agent` — `_create_clothes_record` 方法
- `image_generator` — 卡通图生成
- `image_analyzer` — 图片分析

**依赖**：T1-1、T1-3

#### T2-2：`agent/tools/outfit.py` — 穿搭工具

| 工具名 | 功能 |
|--------|------|
| `plan_outfit` | 基于衣柜 + 天气 + 场合生成穿搭方案（**纯计算，不内嵌工具调用**） |
| `get_outfit_history` | 查询用户穿搭历史 |

**复用现有**：
- `app.agent.graph.nodes.planning.create_planning_prompt` — 复用 Prompt 模板
- `app.agent.graph.nodes.retrieval` — 衣物检索逻辑（但 plan_outfit 作为工具时，数据由 Supervisor 预取后传入，不自己查）

**设计原则**：Tool 必须是纯计算单元，`plan_outfit` 接收 `wardrobe_items` 参数（已由 Supervisor 预取），不再自己调用 `search_wardrobe`。

**依赖**：T2-1

#### T2-3：`agent/tools/knowledge.py` — 知识问答

简化版 FAQ 匹配（无需向量数据库），关键词匹配返回最相关的穿搭知识。

**依赖**：无

---

### 阶段 3：SupervisorAgent（P2，核心）

#### T3-1：`agent/supervisor.py` — SupervisorAgent

**System Prompt**（关键决策点，直接从方案文档移植）：

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
- 用户上传衣物图片 → 先 analyze_clothing_image 识别，再用 add_clothes_to_wardrobe 存储
- 用户询问历史 → 直接调用 get_outfit_history
- 用户提到城市/场合/日期 → 调用 remember_context 记住信息

【追问策略】
- 缺少城市 → "请问要去哪个城市呢？"
- 缺少场合 → "请问是什么场合呢？（上班/约会/运动...）"

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）
```

**Supervisor Loop**（核心逻辑）：

```python
async def run_stream(self, user_message: str, images: list[str] = None) -> AsyncGenerator[dict, None]:
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

    yield {"type": "text", "content": response.content}
    yield {"type": "done", "content": response.content}
```

**SSE 事件类型**：

| 事件 | 触发时机 |
|------|---------|
| `thinking` | LLM 决策中 |
| `tool_called` | **新增** 工具执行前 |
| `tool_result` | **新增** 工具执行后 |
| `text` | LLM 输出文本 |
| `outfit_card` | 穿搭卡片（复用现有） |
| `done` | 完成 |
| `error` | 异常 |

**与 Session 的集成**：
- 初始化时从 `DialogueSessionManager.get(session_id)` 恢复 AgentMemory
- 每次 `run_stream` 结束后，`memory.to_dict()` 写回 Session
- **无条件保存**（finally 块，不在 if-else 中）

**依赖**：T1-1、T1-2、T1-3、T2-1、T2-2、T2-3

#### T3-2：`routers/chat.py` — 接入新 workflow

**修改点**：

1. **`/chat/message/stream`** 端点接入 `SupervisorAgent`：
   - `set_tool_context(db, user_id)` 设置 ContextVar
   - `SupervisorAgent(tools, session_id, user_id).run_stream()` 替换现有 LangGraph workflow
   - Session 保存逻辑保留（finally 块无条件保存）
   - `ChatMessageRequest` 新增 `images: Optional[List[str]]` 字段（支持多模态）

2. **保留现有接口**（不修改功能）：
   - `/chat/message` — 非流式接口（可选，是否废弃视情况）
   - `/chat/session/{id}` — Session 查询
   - `/chat/session/{id}/clear` — Session 清除

3. **移除依赖**：
   - 删除 `from app.agent.graph.workflow import DialogueWorkflow`
   - 删除 `from app.agent.graph.state import GraphState`
   - 删除 `from app.agent.plan_agent import PlanAgent`
   - 删除 `from app.agent.tools import RetrievalTool`
   - 删除 `from app.agent.short_circuit import ShortCircuitTool`
   - 删除 `from app.agent.combine_agent import CombineAgent`

**依赖**：T3-1

---

### 阶段 4：前端适配（与后端 T3-1/T3-2 并行）

#### T4-1：`src/types/chat.ts` — 新增类型

```typescript
interface ToolCalledItem {
  tool: string;
  tool_name: string; // 中文展示名
  args: Record<string, any>;
  timestamp: number;
}

interface ToolResultItem {
  tool: string;
  tool_name: string;
  result: string; // JSON 字符串
  success: boolean;
  timestamp: number;
}
```

#### T4-2：`src/app/chat/ThinkingIndicator.tsx` — 增强展示

支持展示 Tool 调用状态：
- 调用前：`⚡ 正在调用 get_weather(city=杭州)`
- 成功：`✅ get_weather 返回：杭州 18℃ 晴`
- 失败：`❌ get_weather 失败：API 超时`

可复用现有的 `ThinkingItem` 结构，新增 `status` 字段（`pending` | `success` | `error`）。

#### T4-3：`src/app/chat/page.tsx` — SSE 事件处理

```typescript
case "tool_called": {
  const item: ToolCalledItem = {
    tool: event.content.tool,
    tool_name: getToolName(event.content.tool),
    args: event.content.args,
    timestamp: Date.now(),
  };
  setThinkingItems((prev) => [...prev, {
    node: event.content.tool,
    node_name: getToolName(event.content.tool),
    text: `正在调用 ${getToolName(event.content.tool)}...`,
    timestamp: Date.now(),
    status: "pending"
  }]);
  break;
}

case "tool_result": {
  // 更新最后一条 tool_called 状态
  setThinkingItems((prev) => {
    const last = prev[prev.length - 1];
    if (last?.status === "pending" && last.node === event.content.tool) {
      const success = !event.content.result?.startsWith('{"error":');
      return [...prev.slice(0, -1), {
        ...last,
        text: success ? `${last.node_name} 返回结果` : `❌ ${last.node_name} 失败`,
        status: success ? "success" : "error"
      }];
    }
    return prev;
  });
  break;
}
```

**并行**：T4-1、T4-2、T4-3 可在 T3-1 开发期间同步进行，前端用 mock SSE 数据调试。

---

### 阶段 5：清理（P3，最后一步）

#### T5-1：废弃文件（确认新系统稳定后执行）

```
agent/plan_agent.py           — 废弃（穿搭规划逻辑已移入 tools/outfit.py）
agent/combine_agent.py        — 废弃（LLM 替代）
agent/short_circuit.py        — 废弃（与 evaluation_node 重复）
agent/tools.py                — 废弃（旧版工具）
agent/graph/edges.py          — 废弃（LangGraph 移除）
agent/graph/nodes/intent.py   — 废弃（LLM 自主路由）
agent/graph/nodes/weather.py  — 废弃（已转为 Tool）
agent/graph/nodes/wardrobe.py — 废弃（已转为 Tool）
agent/graph/nodes/planning.py — 废弃（已转为 Tool）
agent/graph/nodes/retrieval.py — 废弃（已转为 Tool）
agent/graph/nodes/evaluation.py — 废弃（已转为 Tool）
agent/graph/nodes/feedback.py — 废弃（LLM 处理）
agent/graph/nodes/analysis.py — 废弃（已转为 Tool）
agent/graph/workflow.py       — 废弃（核心逻辑移入 SupervisorAgent）
agent/graph/state.py          — 废弃（GraphState 不再使用）
```

#### T5-2：保留文件

```
agent/dialogue_session.py     — 保留（Session 持久化，继续使用）
agent/clothes_agent.py        — 保留（衣物入库逻辑，add_clothes_to_wardrobe 工具依赖）
agent/services/weather_service.py — 保留（直接复用）
agent/graph/nodes/response.py — 保留（可作为 Tool 输出格式化辅助）
```

---

## 四、API 变更

### 请求格式变更

**新增字段**：

```typescript
// ChatMessageRequest 新增
interface ChatMessageRequest {
  user_id: string;
  session_id?: string;
  message: string;
  context?: Record<string, any>;
  images?: string[]; // 新增：OSS 图片 URL 列表
}
```

### SSE 事件变更

**新增事件**（前端需适配）：

```typescript
// tool_called 事件
event: tool_called
data: {"tool": "get_weather", "args": {"city": "杭州"}}

// tool_result 事件
event: tool_result
data: {"tool": "get_weather", "result": "{\"temperature\": 18, ...}"}
```

**废弃事件**（不再使用）：

```
intent, weather, wardrobe_query, outfit_planning,
clothes_retrieval, outfit_evaluation, feedback, generate_outfit
```

替换为统一的 `tool_called` / `tool_result` 事件。

---

## 五、验证方案

| # | 场景 | 验证方法 |
|---|------|---------|
| V1 | 天气查询 | 发送"杭州今天多少度" → 返回天气 + 穿衣建议 |
| V2 | 穿搭推荐（3 轮） | 推荐穿搭 → 杭州 → 约会 → 观察 `tool_called` 事件串联 |
| V3 | 图片识别 | 发送衣服图片 → 返回识别结果（name/category/color） |
| V4 | 衣物入库 | 图片 + "帮我存衣柜" → 存储成功 → 衣柜列表验证 |
| V5 | 历史查询 | 发送"我上周穿了什么" → 返回历史 |
| V6 | Session 持久化 | 3 轮对话后重启，同 session_id 记住之前信息 |
| V7 | 回归测试 | 现有 API（/clothes/add, /history/list）继续正常工作 |
| V8 | 追问验证 | 只说"约会" → 自动追问城市（missing_fields） |
| V9 | 错误恢复 | 模拟天气 API 超时 → LLM 降级处理 |
| V10 | 多模态 | 同时发送文字 + 2 张图片 → 分别识别后入库 |

---

## 六、风险与缓解

| 风险 | 缓解方案 |
|------|---------|
| LLM 路由不稳定（反复调用同一 Tool） | `max_turns=10` 强制上限；Prompt 中明确调用顺序 |
| Tool 结果 JSON 解析失败 | 每个 Tool 内加 try-except；异常时返回错误 JSON |
| Session 保存遗漏（教训来自原方案） | 强制 finally 块无条件保存 |
| 废弃旧文件导致回归问题 | T5-1 在 T1-T4 全部分支测试通过后执行；废弃前做完整备份 |
| 前端 tool_called 事件展示不友好 | 先复用现有 `ThinkingIndicator`，逐步增强 |

---

## 七、执行顺序

```
P0 基础设施（T1-1, T1-2, T1-3）
    ↓
P1 业务工具（T2-1, T2-2, T2-3）
    ↓
P2 SupervisorAgent（T3-1, T3-2）
    ↓
P3 前端适配（T4-1, T4-2, T4-3，可与 P2 并行）
    ↓
P4 验证（V1-V10）
    ↓
P5 清理（T5-1, T5-2，仅在稳定后执行）
```

---

## 八、工作量估算

| 阶段 | 后端 | 前端 | 验证 |
|------|------|------|------|
| P0 基础设施 | 2 人日 | — | 0.5 人日 |
| P1 业务工具 | 2 人日 | — | 0.5 人日 |
| P2 SupervisorAgent | 3 人日 | — | 1 人日 |
| P3 前端适配 | — | 1 人日 | 0.5 人日 |
| P4 验证 | 0.5 人日 | 0.5 人日 | — |
| P5 清理 | 0.5 人日 | — | — |
| **合计** | **~8.5 人日** | **~2 人日** | **~2.5 人日** |

> 前后端可并行开发（P3 前端与 P2 后端同步），实际工期约 **6-7 人日**。

---

## X、P0 完成记录（2026-03-25）

### 实际创建文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `service/app/agent/tools/context.py` | ✅ 新增 | ContextVar DB 注入（`_db_session`、`_user_id` + `get_db_for_tools`/`get_current_user_id`/`set_tool_context`） |
| `service/app/agent/memory.py` | ✅ 新增 | AgentMemory 数据类（session_id、target_city/scene/date/temperature、missing_fields、pending_task、preferred_style、frequent_colors、recent_messages + 完整方法） |
| `service/app/agent/tools/shared.py` | ✅ 新增 | 4 个共享工具（`get_weather`、`analyze_clothing_image`、`remember_context`、`recall_context`）+ `SHARED_TOOLS` 列表导出 |
| `service/app/agent/tools/__init__.py` | ✅ 新增 | tools 包入口，同时内嵌迁移 `RetrievalTool`（原 `tools.py`）以保持向后兼容 |

### 与方案设计差异

1. **`agent/tools/` 目录 vs `tools.py` 文件**：方案设计时将 `tools/` 作为新目录，但未明确旧 `tools.py` 处理方式。实现中创建 `tools/` 目录并将 `RetrievalTool` 内容迁移至 `tools/__init__.py`，确保 `from app.agent.tools import RetrievalTool` 继续工作。旧 `tools.py` 文件保留在磁盘但不再作为 import 路径。
2. **`remember_context`/`recall_context` 工具**：方案设计中 `recall_context` 依赖 `session_manager`，但 P0 阶段未引入 `SupervisorAgent`，因此工具返回提示文本，实际 recall 逻辑由 SupervisorAgent 在 P2 阶段实现时接入 `AgentMemory.recall()`。
3. **`AgentMemory.to_context_dict()` 的 `asking_for` 映射**：方案中 `asking_for` 取 `missing_fields[0]`，实现一致。`pending_intent` 取 `pending_task`，实现一致。

### 验证结果

- [x] `context.py`: `from app.agent.tools.context import get_db_for_tools` — 无报错
- [x] `memory.py`: `from_dict(ConversationContext格式)` 兼容正确
- [x] `memory.py`: `from_dict(AgentMemory格式)` 字段完整
- [x] `memory.py`: `add_message` 超过 20 条自动截断至 20 条
- [x] `memory.py`: `to_context_string()` 正确生成上下文字符串
- [x] `memory.py`: `to_context_dict()` 返回 ConversationContext 兼容格式
- [x] `shared.py`: 4 个 `@tool` 装饰器工具正确注册，`SHARED_TOOLS` 列表含 4 项
- [x] `tools/__init__.py`: `RetrievalTool` 可正常导入，`from app.agent import PlanAgent, CombineAgent, Supervisor, RetrievalTool` 全部通过
- [x] 现有 `agent/__init__.py` 未修改，兼容性保持

---

## XI、P1 完成记录（2026-03-25）

### 实际创建文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `service/app/agent/tools/wardrobe.py` | ✅ 新增 | search_wardrobe（调用 query_wardrobe，返回衣物列表 JSON）、add_clothes_to_wardrobe（并行分析+卡通图+存储 DB）+ `WARDROBE_TOOLS` 列表 |
| `service/app/agent/tools/outfit.py` | ✅ 新增 | plan_outfit（复用 create_planning_prompt，纯计算）、get_outfit_history（查询 OutfitRecord）+ `OUTFIT_TOOLS` 列表 |
| `service/app/agent/tools/knowledge.py` | ✅ 新增 | search_knowledge_base（10 条 FAQ 关键词匹配）+ `KNOWLEDGE_TOOLS` 列表 |

### 与方案设计差异

1. **`add_clothes_to_wardrobe` 签名参数**：方案中方法名为 `_create_clothes_record`，第一个参数是 `db`，实现中参数名为 `db_session`，与 clothes_agent 实际方法签名一致。
2. **`search_wardrobe` 返回字段**：方案中引用 `item.id` 等 ORM 属性，实现中改为从 `query_wardrobe` 返回的 dict 中取字段（`item.get("id")` 等），与 `_clothes_to_dict` 返回格式一致。
3. **`get_outfit_history` 返回字段**：方案中引用 `scene`、`temperature`、`city`、`match_score`、`description` 等字段，但实际 `OutfitRecord` 模型使用 `occasion`、`outfit_name`、`outfit_snapshot`、`weather_snapshot`、`create_time`，实现中按实际模型字段返回。
4. **`search_knowledge_base` FAQ 条目**：方案中仅列出 5 条，实现中补充至 10 条（新增牛仔裤搭配、正式场合、休闲场合、约会、运动穿着）。
5. **`plan_outfit` 的 `PLANNING_SYSTEM_PROMPT`**：方案中内嵌于工具内，实现中提取为模块级常量，与 planning.py 中的 `PLANNING_SYSTEM_PROMPT` 各自独立（该 Tool 使用独立的简化版 Prompt）。

### 验证结果

- [x] wardrobe: `from app.agent.tools.wardrobe import search_wardrobe, add_clothes_to_wardrobe` — 无报错
- [x] outfit: `from app.agent.tools.outfit import plan_outfit, get_outfit_history` — 无报错
- [x] knowledge: `from app.agent.tools.knowledge import search_knowledge_base` — 无报错
- [x] `WARDROBE_TOOLS` 包含 `search_wardrobe`、`add_clothes_to_wardrobe`（2 项）
- [x] `OUTFIT_TOOLS` 包含 `plan_outfit`、`get_outfit_history`（2 项）
- [x] `KNOWLEDGE_TOOLS` 包含 `search_knowledge_base`（1 项）
- [x] 所有工具均使用 `@tool` 装饰器，返回值均为 `str`（JSON 字符串）

---

## XII、P3 完成记录（2026-03-25）

> 完成日期：2026-03-25

### 实际创建/修改的文件列表

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/src/types/chat.ts` | 修改 | 新增 `ToolCalledItem`、`ToolResultItem`、`SSEEvent` 类型；`ThinkingItem` 增加 `status?` 字段；`ChatEventType` 增加 `'tool_called'` |
| `app/src/app/chat/ThinkingIndicator.tsx` | 修改 | `ThinkingItem` 渲染增加 `status` 字段视觉区分：pending 为橙色脉冲、`success` 为绿色加勾、`error` 为红色加叉 |
| `app/src/app/chat/page.tsx` | 修改 | 新增 `TOOL_NAME_MAP` 映射表、`getToolName()` 辅助函数；`handleSend` 的 SSE switch 中新增 `tool_called` 和 `tool_result` 两个 case |

### 与方案设计差异

1. **`ThinkingItem.status`** 方案设计描述为"复用现有 ThinkingItem 结构，新增 status 字段"，实现在原 `ThinkingItem` 接口上通过 `old_string` 替换的方式添加了 `status?` 字段（向后兼容）。
2. **`ThinkingIndicator.tsx`** 的 status 样式展示使用 emoji 前缀（`⚡`/`✅`/`❌`）+ 对应颜色（橙色/绿色/红色），pending 状态保留脉冲动画。
3. **`tool_result`** 的成功/失败判断使用字符串检测 `resultStr.includes('"error"')` 而非方案中的 `startsWith('{"error":')`，逻辑一致但更健壮。
4. **`ChatEventType`** 中保留了原有的 `'tool_call'`（后端旧事件名），同时新增 `'tool_called'`（后端新事件名），确保向后兼容。

### TypeScript 验证结果

运行 `npx tsc --noEmit`：
- **P3 相关文件（chat/page.tsx、chat/ThinkingIndicator.tsx、types/chat.ts）**：0 个新增错误
- 项目中存在的 pre-existing 错误（如 `ClothesDetailModal.tsx`、`history/page.tsx`、`wardrobe/page.tsx`、`lib/api.ts` 等）均与本次 P3 改动无关

---

## XIII、P2 完成记录（2026-03-25）

### 实际创建/修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `service/app/agent/supervisor.py` | 重写 | 新增 `SupervisorAgent`（LLM Function Calling Loop）：`run_stream()`、`_build_messages()`、`_update_memory_from_tool_result()`、`save_to_session()`；旧版 `Supervisor` 类保留在文件底部（兼容） |
| `service/app/routers/chat.py` | 修改 | 移除旧 LangGraph imports，新增 `SupervisorAgent` + `set_tool_context`；`ChatMessageRequest` 新增 `images` 字段；`/message/stream` 接入 SupervisorAgent 流式执行；finally 无条件保存 Session |
| `service/app/agent/__init__.py` | 修改 | 同时导出 `SupervisorAgent`（新版）和 `Supervisor`（旧版兼容） |

### 与方案设计差异

1. **`Supervisor` 旧版保留**：方案中计划废弃旧版 Supervisor，但实现中将其保留在 `supervisor.py` 底部，供衣柜穿搭推荐功能（`/outfit/generate-today` 等）继续使用，避免回归问题。
2. **`remember_context` 参数扩展**：`remember_context` 工具的 Schema 参数在实现中扩展为 `city/scene/date/temperature/style/colors`（方案中仅 `city/scene/date/temperature`），以支持更多上下文记忆。
3. **Session 保存时机**：`save_to_session` 在 `finally` 块中无条件执行，与方案一致。

### 验证结果

```bash
python -c "from app.agent.supervisor import SupervisorAgent; print('supervisor OK')"
# ✅ supervisor OK

python -c "from app.routers.chat import router; print('chat router OK')"
# ✅ chat router OK
```

### P4 验证结果（2026-03-25）

#### 静态验证

| 检查项 | 结果 |
|--------|------|
| 后端 import 检查（全部 9 个 Tool + SupervisorAgent + Router） | ✅ 通过 |
| 工具 Schema（9 个 Tool，参数定义正确） | ✅ 通过 |
| 前端 TypeScript（P3 相关文件 0 个新增错误） | ✅ 通过 |

#### 工具注册清单

| 工具分类 | 工具名 | 参数 |
|---------|--------|------|
| SharedTools | `get_weather` | city, date |
| | `analyze_clothing_image` | image_url, user_hint |
| | `remember_context` | city, scene, date, temperature, style, colors |
| | `recall_context` | (无) |
| WardrobeTools | `search_wardrobe` | category, color, scene |
| | `add_clothes_to_wardrobe` | image_url, name |
| OutfitTools | `plan_outfit` | scene, temperature, wardrobe_items, max_options |
| | `get_outfit_history` | date, limit |
| KnowledgeTools | `search_knowledge_base` | query |

**合计：9 个工具，9 个 Tool Schema 定义正确**

#### 待运行时验证（需启动服务后手动测试）

- [ ] V1 天气查询：发送"杭州今天多少度" → 返回天气 + 穿衣建议
- [ ] V2 穿搭推荐（3 轮）：推荐穿搭 → 杭州 → 约会 → 观察 `tool_called` 事件串联
- [ ] V3 图片识别：发送衣服图片 → 返回识别结果
- [ ] V4 衣物入库：图片 + "帮我存衣柜" → 存储成功
- [ ] V5 历史查询：发送"我上周穿了什么" → 返回历史
- [ ] V6 Session 持久化：3 轮后重启，同 session_id 记住之前信息
- [ ] V7 回归测试：现有 API（/clothes/add, /history/list）继续正常工作
- [ ] V8 追问验证：只说"约会" → 自动追问城市
- [ ] V9 错误恢复：模拟天气 API 超时 → LLM 降级处理
- [ ] V10 多模态：同时发送文字 + 2 张图片 → 分别识别后入库

### P5 清理状态（2026-03-25）

#### 废弃文件（待物理删除，确认稳定后执行）

以下文件在磁盘上仍存在，但**已被新系统替代**，不再作为 import 路径。建议在所有运行时验证通过后物理删除：

| 文件 | 状态 | 替代 |
|------|------|------|
| `agent/plan_agent.py` | 待废弃 | `agent/tools/outfit.py`（plan_outfit） |
| `agent/combine_agent.py` | 待废弃 | LLM 替代 |
| `agent/short_circuit.py` | 待废弃 | LLM 替代 |
| `agent/tools.py`（旧版） | 待废弃 | `agent/tools/__init__.py` |
| `agent/graph/edges.py` | 待废弃 | LangGraph 已移除 |
| `agent/graph/nodes/intent.py` | 待废弃 | LLM 自主路由 |
| `agent/graph/nodes/weather.py` | 待废弃 | `agent/tools/shared.py`（get_weather） |
| `agent/graph/nodes/wardrobe.py` | 待废弃 | `agent/tools/wardrobe.py`（search_wardrobe） |
| `agent/graph/nodes/planning.py` | 待废弃 | `agent/tools/outfit.py`（plan_outfit） |
| `agent/graph/nodes/retrieval.py` | 待废弃 | `agent/tools/wardrobe.py` |
| `agent/graph/nodes/evaluation.py` | 待废弃 | LLM 替代 |
| `agent/graph/nodes/feedback.py` | 待废弃 | LLM 替代 |
| `agent/graph/nodes/analysis.py` | 待废弃 | `agent/tools/shared.py`（analyze_clothing_image） |
| `agent/graph/workflow.py` | 待废弃 | `agent/supervisor.py`（SupervisorAgent） |
| `agent/graph/state.py` | 待废弃 | `agent/memory.py`（AgentMemory） |

#### 保留文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `agent/dialogue_session.py` | ✅ 保留 | Session 持久化，继续使用 |
| `agent/clothes_agent.py` | ✅ 保留 | 衣物入库逻辑，`add_clothes_to_wardrobe` 依赖 |
| `agent/services/weather_service.py` | ✅ 保留 | 天气服务，直接复用 |
| `agent/graph/nodes/response.py` | ✅ 保留 | 可作为 Tool 输出格式化辅助 |
| `agent/supervisor.py`（旧版 Supervisor 类） | ✅ 保留 | 兼容旧衣柜穿搭推荐功能 |

#### 清理原则

1. **暂不物理删除**：废弃文件保留在磁盘，确保旧功能（如 `/outfit/generate-today`）仍可回退使用
2. **确认稳定后删除**：待运行时验证（V1-V10）全部通过后，再物理删除废弃文件
3. **git commit 前检查**：执行 `git status` 确认无意外删除

---

## 总结

### 完成里程碑

| 里程碑 | 状态 | 完成日期 |
|--------|------|---------|
| P0 基础设施 | ✅ 完成 | 2026-03-25 |
| P1 业务工具 | ✅ 完成 | 2026-03-25 |
| P2 SupervisorAgent | ✅ 完成 | 2026-03-25 |
| P3 前端适配 | ✅ 完成 | 2026-03-25 |
| P4 静态验证 | ✅ 完成 | 2026-03-25 |
| P4 运行时验证 | ⏳ 待执行 | — |
| P5 废弃文件清理 | ⏳ 待执行 | — |

### 新增文件清单

```
service/app/agent/
├── tools/
│   ├── __init__.py          # 工具包入口（迁移 RetrievalTool）
│   ├── context.py           # ContextVar DB 注入
│   ├── shared.py            # 共享工具（4个）
│   ├── wardrobe.py          # 衣柜工具（2个）
│   ├── outfit.py            # 穿搭工具（2个）
│   └── knowledge.py         # 知识问答（1个）
├── memory.py                # AgentMemory 统一记忆接口
└── supervisor.py             # SupervisorAgent（重写）✅ + 旧版 Supervisor（保留）
```

### 架构变更摘要

- **路由**：硬编码 if-else → LLM Function Calling 自主选择
- **工具数**：旧版 ~3 个 → 新版 **9 个**（可扩展）
- **SSE 事件**：节点级 → Tool 级（`tool_called` / `tool_result`）
- **追问逻辑**：分散多处 → 统一写入 System Prompt
- **Session 保存**：条件分支 → finally 无条件保存
