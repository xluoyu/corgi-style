# 对话系统 AI 架构优化 - 实施计划

> 基于：`docs/2026-03-24-对话系统AI架构优化方案.md`
> 状态：待用户确认

## 概述

将当前"LLM 意图识别 + 硬编码规则兜底"的混合模式，优化为"AI First + 规则兜底"模式。

## 实施阶段

---

## 阶段一：移除硬编码 Fallback（预计 1-2 天）

### 任务 1.1：修改 `response.py` - 移除硬编码函数

**文件**：`service/app/agent/graph/nodes/response.py`

**修改内容**：
1. 移除 `_is_likely_city()` 硬编码城市列表函数
2. 移除 `_is_greeting()` 关键词匹配函数
3. 新增 `_ai_classify_input()` - 使用 LLM 统一分类用户输入
4. 新增 `_ai_generate_followup()` - 使用 LLM 动态生成追问语
5. 新增 `_ai_generate_greeting()` - 使用 LLM 生成问候回复
6. 新增 `_ai_generate_fallback()` - 使用 LLM 生成友好引导
7. 修改 `_handle_unknown()` 函数，改为调用 AI 分类而非硬编码

**新增函数签名**：
```python
async def _ai_classify_input(user_message: str, context: dict) -> dict:
    """使用 LLM 分类用户输入类型（city/scene/greeting/confirmation/unknown）"""

async def _ai_generate_followup(missing_type: str, context: dict) -> str:
    """使用 LLM 生成追问语"""

async def _ai_generate_greeting() -> tuple[str, dict]:
    """使用 LLM 生成问候回复"""

async def _ai_generate_fallback(user_message: str) -> tuple[str, dict]:
    """使用 LLM 生成无法理解时的友好引导"""
```

### 任务 1.2：测试验证

**验证点**：
- 用户说"帝都"能识别为城市
- 用户说"魔都"能识别为城市
- 用户说"嗨咯"能识别为问候
- 用户说"北京"能继续追问场景

---

## 阶段二：合并节点减少调用（预计 3-5 天）

### 任务 2.1：创建统一理解节点

**新建文件**：`service/app/agent/graph/nodes/unified.py`

**内容**：
```python
# 统一理解节点
async def understand_node(state: GraphState) -> GraphState:
    """
    合并原 intent_node + 部分 response_node 功能
    一次 LLM 调用完成：意图识别 + 实体提取 + 行动决策
    """

# 相关辅助函数
def _build_context_summary(state: GraphState) -> str:
def _parse_understand_response(response: str) -> dict:
def _validate_understand_result(result: dict) -> dict:
```

### 任务 2.2：修改 `workflow.py` 调整节点流程

**文件**：`service/app/agent/graph/workflow.py`

**修改**：
1. 导入新的 `unified.py` 模块
2. 调整 workflow 图结构，使用 `understand_node` 替代原有部分逻辑

### 任务 2.3：可选 - 创建统一 Agent 类

**新建文件**：`service/app/agent/outfit_agent.py`

**内容**：
```python
class OutfitAgent:
    async def handle_message(self, user_input: str, session: DialogueSessionData) -> tuple[str, dict]:
```

---

## 阶段三：统一 Agent 架构（预计 1-2 周）

### 任务 3.1：完善 OutfitAgent 类

实现完整的 Agent 架构，包括：
- Tool 调用协调
- 状态管理
- 流式响应支持

### 任务 3.2：创建监控指标

**新建文件**：`service/app/agent/metrics.py`

---

## 文件变更清单

| 序号 | 文件路径 | 变更类型 | 说明 |
|------|----------|----------|------|
| 1 | `service/app/agent/graph/nodes/response.py` | 修改 | 移除硬编码，新增 AI 分类函数 |
| 2 | `service/app/agent/graph/nodes/unified.py` | 新增 | 统一理解节点 |
| 3 | `service/app/agent/graph/workflow.py` | 修改 | 调整节点流程 |
| 4 | `service/app/agent/outfit_agent.py` | 新增 | 统一 Agent 类（可选） |
| 5 | `service/app/agent/metrics.py` | 新增 | 监控指标（可选） |

---

## 推荐实施顺序

1. **阶段一（必须）** - 快速提升智能度，用户可直接感知改善
2. **阶段二（推荐）** - 降低延迟和成本
3. **阶段三（可选）** - 架构重构，适合长期维护

---

## 验证标准

| 指标 | 目标 |
|------|------|
| 意图识别准确率 | ≥95% |
| 多轮对话成功率 | ≥90% |
| "帝都"/"魔都"等别名识别 | 支持 |
| 新城市自动识别 | 支持 |
