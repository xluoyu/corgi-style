# 对话式多 Agent 编排系统设计方案

## 1. 背景与目标

### 1.1 现有系统问题

当前 Corgi Style 的 Agent 系统是**同步 OOP 顺序调用**模式：
- `Supervisor` → `PlanAgent` → `RetrievalTool` → `ShortCircuitTool` → `CombineAgent`
- `PlanAgent` 硬编码配色方案，没有 LLM 参与
- 无法理解自然语言意图
- 不支持多轮对话和反馈调整
- 缺少天气获取能力

### 1.2 目标

支持 C 端用户通过**自然语言对话**使用穿搭推荐功能：
- "我后天想去北京参加晚宴" → 理解时间、地点、场景
- "帮我看看蓝色的短袖怎么搭" → 识别衣物、查询搭配
- "太正式了，换个休闲点的" → 多轮反馈调整

## 2. 架构设计

### 2.1 设计理念：衣柜优先（Wardrobe-First）

```
用户需求
    ↓
Intent Agent 解析意图（LLM）
    ↓
┌─────────────────────┐
│ Weather Tool         │ ← 仅当指定 date + city 时调用
│ (获取目标日期天气)   │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Wardrobe Query       │
│ (查用户现有衣物)      │ ← 核心：先知道有什么衣服
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Outfit Planning      │ ← LLM 基于实际衣物做搭配
│ (生成穿搭方案)        │
└─────────────────────┘
    ↓
Clothes Retrieval → 计算匹配分数
    ↓
返回结果 / 触发重试
```

### 2.2 基于 LangGraph 的状态机

#### GraphState 定义

```python
class GraphState(TypedDict):
    # 对话上下文
    user_id: str
    session_id: str
    messages: List[Dict]           # 对话历史

    # 意图识别
    intent: Intent                  # generate_outfit / query_wardrobe / give_feedback / unknown
    entities: Dict                 # date, city, scene, clothes_color, clothes_category
    intent_confidence: float

    # 穿搭规划
    target_date: Optional[str]
    target_city: Optional[str]
    target_scene: Optional[str]
    target_temperature: Optional[float]

    # 衣物数据
    user_clothes: List[Dict]       # 用户衣柜
    filtered_clothes: Dict[str, List[Dict]]  # 按品类过滤

    # 方案结果
    outfit_plan: Optional[Dict]
    match_score: float
    alternatives: List[Dict]

    # 反馈调整
    feedback_type: Optional[str]
    adjustment_history: List[Dict]

    # 系统控制
    should_end: bool
```

### 2.3 节点设计

| 节点 | 类型 | 职责 |
|------|------|------|
| `intent_node` | Agent | 意图识别 + 实体提取（LLM） |
| `weather_node` | Tool | 获取目标日期+城市的天气 |
| `wardrobe_query_node` | Tool | 查询用户衣柜可用衣物 |
| `outfit_planning_node` | Agent | LLM 基于实际衣物生成穿搭方案 |
| `clothes_retrieval_node` | Tool | 按方案检索具体衣物 |
| `outfit_evaluation_node` | Agent | 评估方案并计算匹配分 |
| `feedback_node` | Agent | 处理用户反馈（太正式/太休闲等） |
| `response_node` | Agent | 生成最终回复 |

### 2.4 边路由

```
START → intent_node → route_by_intent
  ├─ QUERY_WARDROBE → wardrobe_query_node → response_node
  ├─ GENERATE_OUTFIT → weather_node → wardrobe_query_node → outfit_planning_node → clothes_retrieval_node → outfit_evaluation_node
  │                      ↓ route_by_score                                          ↓
  │                  score >= 80 ──────────────────────────────────────────→ response_node
  │                  score < 80 ─────────────────→ 反馈建议（最多重试3次）
  │
  └─ GIVE_FEEDBACK → feedback_node → outfit_planning_node → ... → response_node
```

## 3. Tool 接口设计

| Tool | 功能 | 参数 |
|------|------|------|
| `get_weather` | 获取天气 | `city: str, date: str` |
| `query_wardrobe` | 查询衣柜 | `user_id, category, color, temperature, scene, tags` |
| `get_wardrobe_stats` | 衣橱统计 | `user_id` |
| `retrieve_by_scheme` | 方案匹配 | `user_id, plan, temperature` |
| `save_outfit_record` | 保存穿搭 | `user_id, outfit_data` |

## 4. 多轮对话状态管理

### 4.1 上下文继承规则

| 字段 | 继承策略 |
|------|----------|
| `user_id` | 固定，不变 |
| `session_id` | 固定，不变 |
| `target_city` | 若新消息未指定，继承上轮值 |
| `target_scene` | 若新消息未指定，继承上轮值 |
| `user_clothes` | 固定为用户当前衣柜 |
| `current_outfit` | 反馈调整时继承 |
| `adjustment_history` | 累加记录 |

### 4.2 反馈类型映射

```python
FEEDBACK_SCENE_MAP = {
    "too_formal": "casual",
    "too_casual": "smart_casual",
    "too_colorful": "neutral",
    "too_simple": "statement",
    "too_cold": "warm",
    "too_hot": "cool",
}
```

## 5. 文件结构

```
service/app/agent/
├── graph/                      # LangGraph 对话系统
│   ├── __init__.py
│   ├── state.py               # GraphState 定义
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── intent.py          # intent_node
│   │   ├── weather.py         # weather_node
│   │   ├── wardrobe.py        # wardrobe_query_node
│   │   ├── planning.py        # outfit_planning_node
│   │   ├── retrieval.py       # clothes_retrieval_node
│   │   ├── evaluation.py      # outfit_evaluation_node
│   │   ├── feedback.py        # feedback_node
│   │   └── response.py        # response_node
│   ├── edges.py               # 条件分支函数
│   └── workflow.py            # StateGraph 组装
├── intent_agent.py            # Intent Agent (LLM)
├── outfit_agent.py            # Outfit Planning Agent (LLM)
├── dialogue_session.py        # Session 管理
└── services/
    └── weather_service.py     # 天气服务
```

## 6. 实施顺序

### Phase 1: 基础设施
- [ ] 新增 `graph/state.py` - State 定义
- [ ] 新增 `dialogue_session.py` - Session 管理
- [ ] 新增 `weather_service.py` - 天气服务

### Phase 2: 核心节点
- [ ] 新增 `graph/nodes/intent.py` - intent_node
- [ ] 新增 `graph/nodes/wardrobe.py` - wardrobe_query_node
- [ ] 新增 `graph/nodes/weather.py` - weather_node

### Phase 3: 穿搭流程
- [ ] 新增 `graph/nodes/planning.py` - outfit_planning_node
- [ ] 新增 `graph/nodes/retrieval.py` - clothes_retrieval_node
- [ ] 新增 `graph/nodes/evaluation.py` - outfit_evaluation_node

### Phase 4: Graph 组装
- [ ] 新增 `graph/edges.py` - 条件分支
- [ ] 新增 `graph/workflow.py` - StateGraph 组装
- [ ] 新增 `graph/nodes/response.py` - response_node

### Phase 5: 反馈与对话
- [ ] 新增 `graph/nodes/feedback.py` - feedback_node
- [ ] 实现上下文继承
- [ ] 新增 `routers/chat.py` - 对话 API

## 7. API 设计

### 7.1 对话路由

```
POST /chat/message
Request:
{
    "user_id": "uuid",
    "session_id": "uuid",        // 可选，不传则创建新 session
    "message": "后天去北京参加晚宴",
    "context": {}                // 可选附加上下文
}

Response:
{
    "session_id": "uuid",
    "message": "为您推荐以下穿搭...",
    "data": {
        "outfit_plan": {...},
        "match_score": 85,
        "clothes": [...]
    },
    "suggestions": [
        {"type": "alternative", "description": "换个更休闲的版本"}
    ]
}
```

### 7.2 Session 管理

```
GET /chat/session/{session_id}      # 获取 session 状态
DELETE /chat/session/{session_id}   # 结束 session
POST /chat/session/{session_id}/clear  # 清除上下文
```

## 8. 典型对话流程

### 8.1 生成穿搭

**用户**: "我后天想去北京参加晚宴"

**Agent 响应**: "好的，后天（3月25日）北京参加晚宴，我来为您查询天气并生成穿搭方案..."

**流程**:
1. Intent Agent 识别：intent=generate_outfit, date=后天, city=北京, scene=晚宴
2. Weather Tool 获取：3月25日北京天气 12°C，多云
3. Wardrobe Query 查询用户衣柜
4. Outfit Planning Agent 基于衣物生成方案
5. 返回穿搭方案

### 8.2 反馈调整

**用户**: "太正式了，换个休闲点的"

**Agent 响应**: "好的，为您调整为空闲舒适的风格..."

**流程**:
1. Intent Agent 识别：intent=give_feedback, feedback_type=too_formal
2. Feedback Agent 更新 target_scene=casual
3. 继承其他上下文，重新生成方案
4. 返回调整后的方案

### 8.3 查询衣柜

**用户**: "我衣柜里有几件衬衫？"

**Agent 响应**: "您的衣柜里有 5 件衬衫，其中 2 件蓝色、1 件白色、2 件条纹款式。"

**流程**:
1. Intent Agent 识别：intent=query_wardrobe, category=衬衫→top
2. Wardrobe Query 统计衬衫数量
3. 返回统计结果
