# FashionSteward LangGraph Multi-Agent 架构实现记录

> 创建时间：2026-03-31
> 状态：已完成初始框架搭建
> 架构：基于 LangGraph StateGraph 的多 Agent 协调架构

---

## 一、架构概览

### 1.1 核心理念

将原有单 Agent + Function Calling 模式重构为**多 Agent 协调架构**：

- **SupervisorAgent** 退化为协调者，仅负责任务分发和结果汇总
- 各功能模块（WeatherAgent、WardrobeAgent、OutfitAdvisorAgent、KnowledgeAgent）成为独立 Agent
- Agent 之间通过 LangGraph 的 **State 共享数据**，而非 Tool Call
- 使用 **LangGraph 条件边**实现路由控制

### 1.2 工作流拓扑

```
用户消息
    ↓
[SupervisorAgent] ←────────────── (主控制流)
    ↓ 决定路由
┌─────────────────────────────────────────┐
│                                         │
↓                                         ↓
[WeatherAgent]                      [WardrobeAgent]
    ↓                                     ↓
    └──────────────┬────────────────────┘
                   ↓
           [OutfitAdvisorAgent]
                   ↓
           [SupervisorAgent] → 汇总 → 回复用户
```

---

## 二、文件结构

```
service/app/agent/
├── agents/                         # 多 Agent 模块
│   ├── __init__.py
│   ├── base_agent.py              # Agent 工厂函数（暂未使用）
│   └── supervisor.py              # SupervisorAgent + 各 Agent 节点
├── graph/
│   ├── workflow_v3.py             # 多 Agent 工作流组装
│   └── state_v2.py                # GraphState 状态定义
└── (原有 nodes/ 目录保留，供 v2 工作流使用)
```

---

## 三、核心组件

### 3.1 SupervisorAgent (`agents/supervisor.py`)

**职责**：
1. 意图识别（调用 LLM）
2. 路由决策（weather_agent / wardrobe_agent / outfit_advisor_agent / knowledge_agent）
3. 结果汇总
4. 回复生成

**Agent 节点**：
- `weather_agent_node` - 查询天气数据
- `wardrobe_agent_node` - 查询/管理衣柜
- `outfit_advisor_agent_node` - 生成穿搭方案
- `knowledge_agent_node` - 知识问答

**路由规则**：
| 用户需求 | 路由目标 |
|---------|---------|
| "穿什么" / "推荐穿搭" | outfit_advisor_agent |
| 问天气/温度 | weather_agent |
| 问衣柜里有什么 | wardrobe_agent |
| 上传衣服图片 | wardrobe_agent (add) |
| 问护理/怎么洗 | knowledge_agent |

### 3.2 多 Agent 工作流 (`graph/workflow_v3.py`)

**路由函数**：
- `_route_after_supervisor()` - Supervisor 决定后的路由
- `_route_after_agent()` - Agent 执行完成后的路由

**响应节点** (`response_node`)：
- 根据 Agent 结果生成最终回复
- 支持错误处理、天气回复、衣柜查询、穿搭方案生成

---

## 四、State 设计

```python
class GraphState(TypedDict):
    # === 对话上下文 ===
    user_id: str
    session_id: str
    messages: List[Dict[str, Any]]

    # === 目标信息 ===
    target_date: Optional[str]
    target_city: Optional[str]
    target_scene: Optional[str]
    target_temperature: Optional[float]

    # === Agent 间共享数据 ===
    weather_data: Optional[Dict]        # WeatherAgent 写入
    wardrobe_items: List[Dict]          # WardrobeAgent 写入
    outfit_plan: Optional[Dict]         # OutfitAdvisorAgent 写入

    # === 控制流 ===
    routing_decision: Optional[str]      # 当前路由决定
    routing_params: Dict[str, Any]       # 路由参数
    agent_result: Optional[Dict]        # Agent 执行结果
    supervisor_response: Optional[str]   # 直接回答的文本
    should_end: bool                    # 是否结束

    # === 响应数据 ===
    response_data: Optional[Dict[str, Any]]  # 响应附加数据
```

---

## 五、API 端点

### 5.1 后端新增端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/message/v3` | POST | 多 Agent 工作流（非流式） |

**请求格式**：
```json
{
  "user_id": "xxx",
  "session_id": "xxx",  // 可选
  "message": "今天去北京出差穿什么",
  "context": {}
}
```

**响应格式**：
```json
{
  "session_id": "xxx",
  "message": "根据北京今天的天气...",
  "contents": [{"type": "text", "content": "..."}],
  "data": {}
}
```

### 5.2 前端接入

前端目前使用：
- `/chat/message/stream` - SSE 流式（基于旧版 SupervisorAgent + Function Calling）
- `/chat/message` - 非流式

**暂未修改前端**，v3 端点已添加但未集成到前端。前端接入可在后续迭代中完成。

---

## 六、已实现功能

### 6.1 已完成

1. **多 Agent 框架搭建** - `workflow_v3.py`
   - Supervisor 节点
   - WeatherAgent / WardrobeAgent / OutfitAdvisorAgent / KnowledgeAgent 节点
   - 条件边路由

2. **SupervisorAgent 重构** - `agents/supervisor.py`
   - 新 Prompt 设计（主动行动、协调者职责）
   - 路由解析逻辑
   - 各 Agent 节点函数（已绑定真正的工具）

3. **API 端点集成** - `routers/chat.py`
   - 添加 `/chat/message/v3` 端点

4. **导入问题修复** - `agents/base_agent.py`
   - 修复 `create_react_agent` 导入错误

5. **v3 workflow bug 修复** (2026-03-31)
   - `agents/supervisor.py`: 添加 `last_agent` 字段设置到各 Agent 节点
   - `state_v2.py`: 添加 `last_agent` 字段到 GraphState 和 `create_initial_state`
   - 修复 `_route_after_agent` 因缺少 `last_agent` 而无法正确路由的问题

6. **v3 流式输出支持** (2026-03-31)
   - `workflow_v3.py`: 添加 `run_stream_sse` 方法生成 SSE 格式事件
   - `chat.py`: 添加 `/chat/message/v3/stream` 端点

7. **v3 Session 持久化完善** (2026-03-31)
   - `dialogue_session.py`: 添加 v3 特有字段到 ConversationContext
   - `chat.py`: 修改 `_save_v2_state_to_session` 保存 v3 字段
   - v3 端点从 session 恢复 `last_agent`, `routing_decision`, `weather_data` 等字段

### 6.2 待完成

1. **Agent 工具绑定** - 各 Agent 节点已绑定真正的工具（✅ 已完成）
2. **前端集成** - 已添加 v3 API 函数，前端可选择切换到 v3
3. **流式输出支持** - 已添加 v3 SSE 端点（✅ 已完成）
4. **Session 持久化完善** - v3 特有字段已支持持久化（✅ 已完成）

---

## 七、与旧架构对比

| 方面 | 旧架构 (v2) | 新架构 (v3) |
|------|------------|------------|
| Agent 形态 | 单 Agent + Function Calling | 多 Agent 协调 |
| 状态管理 | 分散在 Agent 类属性 | GraphState 统一管理 |
| 通信协议 | Tool Call | State 共享 |
| 路由方式 | LLM 决定调用哪个 Tool | Supervisor 决定调用哪个 Agent |
| 迭代控制 | while 循环 + is_terminal | LangGraph 条件边 |

---

## 八、后续计划

### Phase 1：完善 Agent 实现
- [x] WeatherAgent - 绑定真正的天气查询工具 ✅
- [x] WardrobeAgent - 绑定衣柜查询/添加工具 ✅
- [x] OutfitAdvisorAgent - 绑定穿搭生成工具 ✅
- [x] KnowledgeAgent - 绑定知识库工具 ✅

### Phase 2：前端集成
- [x] 添加 `chatMessageV3` API 函数 ✅
- [x] 添加 `chatMessageStreamV3` API 函数 ✅
- [x] 前端切换到 v3 端点 ✅
- [x] 支持流式输出（SSE）✅

### Phase 3：高级功能
- [ ] Feedback 处理（"太正式了" → 重新生成）
- [ ] 多轮迭代优化
- [ ] 偏好学习集成

---

## 九、修改的文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/agent/agents/__init__.py` | 新增 | Agent 模块初始化 |
| `app/agent/agents/base_agent.py` | 新增 | Agent 工厂函数（暂未使用） |
| `app/agent/agents/supervisor.py` | 新增 | SupervisorAgent + 各 Agent 节点 |
| `app/agent/graph/workflow_v3.py` | 新增 | 多 Agent 工作流组装 |
| `app/routers/chat.py` | 修改 | 添加 `/message/v3` 和 `/message/v3/stream` 端点 |
| `app/agent/graph/state_v2.py` | 修改 | 添加 `last_agent` 字段（2026-03-31） |
| `app/agent/dialogue_session.py` | 修改 | 添加 v3 特有字段到 ConversationContext |
| `app/src/lib/api.ts` | 修改 | 添加 `chatMessageV3` 和 `chatMessageStreamV3` |

---

*文档版本：1.2 — 2026-03-31*
