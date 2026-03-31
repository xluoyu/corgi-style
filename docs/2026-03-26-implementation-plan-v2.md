# FashionSteward 技术实施方案 v2.0

> 文档版本：v2.0
> 创建时间：2026-03-26
> 状态：待评审
> 基于：PRD-fashion-steward-v1.0.md
> 架构：真正的 Duo-Agent（OutfitAdvisor + WardrobeCurator + GarmentCare）

---

## 一、架构决策

### 1.1 核心决策：使用真正的 Agent，而非增强 Tool

经过重新评审，我们确认 PRD 的需求必须通过**真正的 Agent** 实现，原因如下：

PRD 的核心需求是"**多轮深度沟通**"，用户与 FashionSteward 的对话不是"问-答"的工具调用模式，而是：

```
用户：帮我推荐穿搭
Agent：好的，这套方案您看看...
用户：太正式了
Agent：明白，我调整一下...（理解"太正式"背后的含义，调整到合适的程度）
用户：能更年轻一点吗
Agent：（连贯理解用户从"太正式"到"要年轻"的演进，给出更精准的方案）
```

这种**连贯推理、多轮累积、有主见的判断**的交互模式，Tool 模式无法支撑：

| | 增强 Tool 方案 | 真正的 Agent 方案 |
|---|---|---|
| 多轮反馈理解 | 每次独立解析，上下文丢失 | 整个对话链维护完整上下文 |
| 方案迭代 | `analyze_feedback` → `refine_outfit` 两次调用，推理被割裂 | 一个 Agent 内部连贯推理，不割裂 |
| 审美一致性 | 两个 Tool 的 System Prompt 可能不一致 | 同一 Agent 审美判断一致 |
| 推理可见性 | Supervisor 看到 Tool 结果，看不到推理过程 | Supervisor 可以展示 Agent 的推理过程给用户 |
| 主动建议 | 只能在 Tool 结束后追加 | Agent 在推理过程中自然产生 |
| 状态维护 | 每次 Tool 调用独立，无法累积 | Agent 维护状态，多轮对话累积 |

**增强 Tool 方案的真实问题**：当用户说"太正式了"，`analyze_feedback` 解析一次，`refine_outfit` 生成一次，Agent 推理被**割裂成两个独立的 LLM 调用**，上下文传递依赖 Tool 之间的参数——这正是我们最初在 PRD D2 中批评的"嵌套 tool_call"问题，只是被包装成了"两个 Tool"。

### 1.2 最终架构选择

| 角色 | 技术形态 | 原因 |
|------|---------|------|
| **SupervisorAgent** | 真正的 Agent | 负责任务路由、Agent 编排、流式响应，只能有一个 |
| **OutfitAdvisor** | **真正的 Agent** | 需要连贯推理、多轮迭代、审美判断，必须是 Agent |
| **WardrobeCurator** | **真正的 Agent** | 需要主动建议、健康分析、风格匹配，是 Agent |
| **GarmentCare** | 规则 Tool | 材质知识查表，不需要 LLM，保持 Tool 即可 |

**SupervisorAgent 调用专业 Agent 的方式**：通过 **Agent 间通信协议**（AgentRequest/AgentResponse），**不是嵌套 tool_call**。

### 1.3 Agent 间通信协议

```
┌──────────────────────────────────────────────────────┐
│  SupervisorAgent（唯一编排 Agent）                    │
│                                                      │
│  调用 OutfitAdvisor：                                 │
│    request = AgentRequest(task="plan_outfit", ...)  │
│    response = await outfit_advisor.plan(request)     │
│    Supervisor 接收 AgentResponse，整合后输出给用户    │
│                                                      │
│  调用 WardrobeCurator：                              │
│    request = AgentRequest(task="wardrobe_health", ..)│
│    response = await wardrobe_curator.check(request)  │
│                                                      │
│  调用 GarmentCare（Tool）：                          │
│    result = await get_care_guide.invoke(material=..)│
└──────────────────────────────────────────────────────┘
```

关键点：Supervisor 调用专业 Agent **不是 tool_call**，而是直接的方法调用。Supervisor 仍然能看到完整过程（因为调用是同步的，没有隐藏层），同时专业 Agent 内部可以维护自己的状态和推理。

### 1.4 LLM 调用成本

| 场景 | 增强 Tool 方案 | Duo-Agent 方案 |
|------|-------------|---------------|
| 单次穿搭推荐 | 2 次（Supervisor + Tool 内部） | **2 次**（Supervisor + OutfitAdvisor） |
| 多轮迭代（3 轮） | 5+ 次（feedback + refine 每次 × 3） | **4 次**（plan × 1 + refine × 3） |
| 衣橱健康检查 | 1 次（Tool 内部） | **1 次**（WardrobeCurator） |
| 参考图风格复刻 | 3 次（VL + 分析 + 匹配） | **3 次**（VL + WardrobeCurator + OutfitAdvisor） |

**结论：成本相同，体验差距巨大。采用 Duo-Agent 方案。**

---

## 二、整体架构

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                  实时对话 / 衣橱管理 / 推送通知                    │
└──────────────────────────────┬───────────────────────────────────┘
                               │ SSE / WebSocket
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SupervisorAgent (唯一的编排 Agent)              │  │
│  │                                                           │  │
│  │  - 意图分类                                               │  │
│  │  - 任务路由（分发给专业 Agent）                             │  │
│  │  - 流式事件输出（SSE）                                     │  │
│  │  - Session 持久化                                         │  │
│  │  - Agent 状态管理（保留专业 Agent 实例）                    │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                    │
│         ┌───────────────────┼──────────────────────┐          │
│         │                   │                       │          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌────────▼────────┐ │
│  │ Outfit      │    │ Wardrobe    │    │ Shared Tools     │ │
│  │ Advisor     │    │ Curator     │    │                  │ │
│  │             │    │             │    │ get_weather      │ │
│  │ Agent 真正  │    │ Agent 真正  │    │ analyze_image    │ │
│  │             │    │             │    │ search_wardrobe  │ │
│  │ · 穿搭推理  │    │ · 衣橱健康  │    │ get_history     │ │
│  │ · 方案生成  │    │ · 主动提醒  │    │                 │ │
│  │ · 方案评价  │    │ · 风格缺口  │    │                 │ │
│  │ · 迭代优化  │    │ · 参考图复刻 │    │                 │ │
│  │ · 主动建议  │    │ · 利用率分析 │    │                 │ │
│  │             │    │             │    │                 │ │
│  │ 有审美判断  │    │ 主动出击    │    │                 │ │
│  │ 有主见     │    │ 细心观察    │    │                 │ │
│  └──────┬──────┘    └──────┬──────┘    └─────────────────┘ │
│         │                   │                      │          │
│         └───────────────────┼──────────────────────┘          │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Agent 间通信协议                             │  │
│  │                                                          │  │
│  │  AgentRequest  →  AgentResponse                         │  │
│  │  {task, context, history, preferences}                 │  │
│  │       ←        {result, reasoning, suggestions}         │  │
│  │                                                          │  │
│  │  不是嵌套 tool_call，是方法调用                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Knowledge Base                               │  │
│  │                                                          │  │
│  │  · 色彩搭配规则库                                        │  │
│  │  · 风格定义库                                            │  │
│  │  · 材质属性库                                            │  │
│  │  · 场合穿衣规范                                          │  │
│  │  · 搭配兼容性矩阵                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Data Layer                                   │  │
│  │                                                          │  │
│  │  PostgreSQL  ·  Redis (Session 缓存)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                   Background Service                             │
│                                                                │
│  ┌──────────────────────┐  ┌───────────────────────────────┐   │
│  │  ProactiveService    │  │  PreferenceLearner            │   │
│  │  主动服务引擎        │  │  偏好学习服务                 │   │
│  │                      │  │                               │   │
│  │  APScheduler 调度    │  │  从反馈中学习用户偏好          │   │
│  │  · 每日衣橱检查       │  │  推断隐性偏好（身材/风格）      │   │
│  │  · 每周穿搭报告       │  │  跨 session 持久化            │   │
│  │  · 天气变化提醒       │  │                               │   │
│  └──────────────────────┘  └───────────────────────────────┘   │
│                                                                │
│  ┌──────────────────────┐  ┌───────────────────────────────┐   │
│  │  NotificationManager │  │  WardrobeHealthChecker        │   │
│  │  推送通知管理器      │  │  衣橱健康检查器               │   │
│  │                      │  │                               │   │
│  │  WebSocket / SSE 推送│  │  独立于 Agent 的健康分析逻辑   │   │
│  └──────────────────────┘  └───────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 三、Agent 间通信协议

这是整个架构的核心。所有 Agent 之间的交互都通过标准化的请求/响应格式。

### 3.1 核心数据结构

```python
# app/agent/protocol.py

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """Agent 可执行的任务类型"""
    # OutfitAdvisor 任务
    PLAN_OUTFIT = "plan_outfit"           # 生成穿搭方案
    REFINE_OUTFIT = "refine_outfit"       # 迭代优化方案
    EVALUATE_OUTFIT = "evaluate_outfit"    # 评价方案
    ANALYZE_STYLE = "analyze_style"        # 分析穿搭风格
    MATCH_STYLE = "match_style"            # 参考图风格复刻

    # WardrobeCurator 任务
    WARDROBE_HEALTH = "wardrobe_health"    # 衣橱健康检查
    UNUSED_REMINDER = "unused_reminder"     # 未穿衣物提醒
    STYLE_GAP = "style_gap"                # 风格缺口检测
    WEARING_PATTERN = "wearing_pattern"    # 穿着规律分析
    STYLE_MATCH = "style_match"            # 参考图风格匹配


@dataclass
class OutfitContext:
    """穿搭任务的上下文"""
    user_id: str
    target_city: Optional[str] = None
    target_scene: Optional[str] = None
    target_date: Optional[str] = None
    temperature: Optional[float] = None
    weather_condition: Optional[str] = None

    wardrobe_items: List[Dict] = field(default_factory=list)
    wardrobe_summary: Dict = field(default_factory=dict)

    # 当前对话中的方案
    current_plan: Optional[Dict] = None
    previous_plans: List[Dict] = field(default_factory=list)

    # 用户反馈历史（用于迭代）
    feedback_history: List[Dict] = field(default_factory=list)

    # 偏好
    preferences: Optional[Dict] = None

    # 参考图
    reference_image_url: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "target_city": self.target_city,
            "target_scene": self.target_scene,
            "target_date": self.target_date,
            "temperature": self.temperature,
            "weather_condition": self.weather_condition,
            "wardrobe_item_count": len(self.wardrobe_items),
            "wardrobe_summary": self.wardrobe_summary,
            "has_current_plan": self.current_plan is not None,
            "iteration_count": len(self.previous_plans),
            "preferences": self.preferences,
        }


@dataclass
class OutfitEvaluation:
    """穿搭方案评价"""
    overall_score: int  # 0-100

    color_score: int
    style_score: int
    scene_score: int
    layering_score: int
    body_fit_score: int

    pros: List[str]
    cons: List[str]
    suggestions: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentRequest:
    """Supervisor 发给专业 Agent 的请求"""
    task: TaskType
    agent: str  # "outfit_advisor" / "wardrobe_curator"

    context: OutfitContext
    conversation_history: List[Dict] = field(default_factory=list)

    # 用于 refinetask
    feedback: Optional[str] = None
    previous_plan: Optional[Dict] = None

    # 用于参考图任务
    reference_image_url: Optional[str] = None

    # 元数据
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResponse:
    """专业 Agent 返回给 Supervisor 的响应"""
    agent: str
    status: str  # "success" / "partial" / "failed"
    request_id: str

    # 核心输出
    result: Dict = field(default_factory=dict)
    outfits: List[Dict] = field(default_factory=list)
    evaluation: Optional[OutfitEvaluation] = None

    # Agent 的推理过程（可展示给用户）
    reasoning: str = ""
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 用于迭代优化
    plan: Optional[Dict] = None
    matched_items: List[Dict] = field(default_factory=list)
    health_report: Optional[Dict] = None

    # 元数据
    metadata: Dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_stream_events(self) -> List[Dict]:
        """将响应转换为 SSE 事件列表"""
        events = []

        if self.reasoning:
            events.append({"type": "reasoning", "content": self.reasoning})

        if self.outfits or self.plan:
            events.append({
                "type": "outfit_card",
                "content": {
                    "outfits": self.outfits or [self.plan],
                    "evaluation": self.evaluation.to_dict() if self.evaluation else None,
                }
            })

        for suggestion in self.suggestions:
            events.append({"type": "suggestion", "content": suggestion})

        for warning in self.warnings:
            events.append({"type": "warning", "content": warning})

        return events
```

### 3.2 通信协议原则

1. **非嵌套调用**：Supervisor 调用专业 Agent 是直接方法调用，不是 `tool.invoke()`。Supervisor 看不到隐藏层。
2. **状态在 Agent 内部维护**：每个专业 Agent 实例维护自己的状态（current_plan、iteration_count、preferences）。Supervisor 通过保留 Agent 实例来维持跨轮次状态。
3. **推理过程透明**：Agent 的 `reasoning` 字段包含推理过程，可以选择性地展示给用户，增强信任感。
4. **主动建议内置**：Agent 在推理过程中自然产生主动建议，不是在最后追加。

---

## 四、OutfitAdvisor Agent

### 4.1 Agent 职责

OutfitAdvisor 是 FashionSteward 的**核心 Agent**，负责所有与穿搭相关的深度推理。

**职责范围**：
- 根据场景、天气、衣柜生成穿搭方案
- **严格评价**穿搭方案，指出问题
- 根据用户反馈**迭代优化**方案
- 分析参考图的穿搭风格
- 主动给出更好的选择，不只是执行命令
- **有自己的审美判断**，敢于说真话

**性格特征**：
- 专业但不傲慢，给建议时有理由
- 尊重用户但不盲从，不说违心的"好看"
- 主动出击，不等用户问

### 4.2 Agent 内部架构

```python
# app/agent/outfit_advisor.py

import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.agent.protocol import (
    AgentRequest, AgentResponse, OutfitContext,
    OutfitEvaluation, TaskType
)
from app.services.llm_providers import get_cached_provider
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


SYSTEM_PROMPT = """你是 OutfitAdvisor，一个有10年经验的专业穿搭顾问，曾为数百位客户做形象设计。

【你的核心身份】
你不只是一个生成穿搭方案的工具，而是一个有思想、有主见、敢说话的穿搭顾问。
你的价值在于：不仅执行命令，还要给出更好的建议。

【你的能力】
1. 穿搭方案生成：根据场景、天气、衣柜生成方案
2. 搭配评价：严格评价，给出 pros/cons/suggestions
3. 迭代优化：根据反馈持续改进，有自己的判断
4. 主动建议：不仅响应，还要主动给出更好的选择

【搭配评价标准】（你必须坚持）
- 色彩协调：不超过3个主色，相近色或互补色搭配
- 风格统一：整套搭配的风格要一致，不能混搭冲突风格
- 场合得体：正式场合不能有休闲单品，反之亦然
- 层次分明：上下装/内外装要有层次对比
- 身材适配：考虑身材特点，不推荐显矮/显胖的搭配

【敢说的话】
- "这套的色彩协调，但正式度不够，商务场合不太合适"
- "我不推荐这个方案，因为上下装的正式度不匹配"
- "您衣柜里其实有更好的选择——这件格子衬衫和您常穿的裤子不太搭"
- "这个颜色在换季时节显得沉重，换成浅色系会更清爽"
- "您说想要显瘦，但这个方案反而会膨胀，建议......"

【禁止的行为】
- 用户说什么都"好的可以"
- 只说"好看/不好看"不给理由
- 完全按照用户的不当偏好走
- 模糊其辞，不给出明确判断

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）

【多轮推理机制】
你可以维护对话上下文中的：
- 用户的历史偏好和已拒绝的方案特征
- 当前方案的迭代历史
- 用户的隐性需求（通过行为推断）

当用户说"太正式"，你的思考过程应该是：
"用户说太正式 → 这意味着需要降低正式度
 → 但我不能盲目降，要判断降多少
 → 原方案是'衬衫+西装裤'，降到'衬衫+牛仔裤'或'针织衫+休闲裤'
 → 但用户是上班族，完全休闲可能不合适
 → 折中方案：针织衫+休闲西裤，既有质感又不过于正式
 → 这是我的专业判断，不是用户的命令"

当用户说"年轻一点"，你的思考应该是：
"年轻≠幼稚，而是更有活力、更干净
 → 换浅色系（白/浅蓝/米色）
 → 款式简化，避免老气元素（格子、领带）
 → 材质更轻薄（棉麻、细针织）
 → 给用户推荐时解释原因"
"""


class OutfitAdvisorAgent:
    """
    真正的穿搭 Agent。
    不是 Tool，是有独立 System Prompt 和完整推理能力的 Agent。
    """

    def __init__(self, user_id: str, preferences: Dict = None):
        self.user_id = user_id
        self.preferences = preferences or {}
        self.llm = get_cached_provider().chat_model

        # Agent 内部状态（跨轮次维护）
        self.conversation_history: List[Dict] = []
        self.current_plan: Optional[Dict] = None
        self.iteration_count: int = 0
        self.rejected_features: List[str] = []  # 被用户拒绝的特征
        self.accepted_features: List[str] = []  # 被用户接受的特征

    # ============================================================
    # 核心入口
    # ============================================================

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """统一入口，根据 task 类型分发"""
        try:
            if request.task == TaskType.PLAN_OUTFIT:
                return await self.plan_outfit(request)
            elif request.task == TaskType.REFINE_OUTFIT:
                return await self.refine_outfit(request)
            elif request.task == TaskType.EVALUATE_OUTFIT:
                return await self.evaluate_outfit(request)
            elif request.task == TaskType.ANALYZE_STYLE:
                return await self.analyze_style(request)
            else:
                return AgentResponse(
                    agent="outfit_advisor",
                    status="failed",
                    request_id=request.request_id,
                    error=f"Unknown task: {request.task}"
                )
        except Exception as e:
            return AgentResponse(
                agent="outfit_advisor",
                status="failed",
                request_id=request.request_id,
                error=f"{type(e).__name__}: {str(e)}"
            )

    # ============================================================
    # plan_outfit：生成穿搭方案
    # ============================================================

    async def plan_outfit(self, request: AgentRequest) -> AgentResponse:
        """生成穿搭方案"""
        context = request.context

        # 构建规划提示词
        prompt = self._build_planning_prompt(context)

        # 调用 LLM
        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        # 解析方案
        plan = self._parse_plan(response.content)

        # 评价方案
        evaluation = await self._evaluate(plan, context.target_scene)

        # 生成推理过程（展示给用户）
        reasoning = self._generate_reasoning(plan, context, evaluation)

        # 主动建议
        suggestions = self._generate_suggestions(plan, evaluation, context)

        # 检查警告
        warnings = self._check_warnings(plan, context)

        # 更新内部状态
        self.current_plan = plan
        self.conversation_history.append({
            "role": "assistant",
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })

        return AgentResponse(
            agent="outfit_advisor",
            status="success",
            request_id=request.request_id,
            result=plan,
            outfits=plan.get("outfits", []),
            plan=plan,
            evaluation=evaluation,
            reasoning=reasoning,
            suggestions=suggestions,
            warnings=warnings,
            metadata={
                "iteration": self.iteration_count,
                "scene": context.target_scene,
                "temperature": context.temperature,
            }
        )

    # ============================================================
    # refine_outfit：迭代优化（核心能力）
    # ============================================================

    async def refine_outfit(self, request: AgentRequest) -> AgentResponse:
        """
        根据用户反馈迭代优化方案。
        这是多轮对话的核心方法。
        """
        self.iteration_count += 1
        feedback = request.feedback
        previous_plan = request.previous_plan or self.current_plan

        # 1. 理解反馈语义
        analysis = await self._analyze_feedback(feedback)

        # 记录被拒绝的特征
        if analysis.get("rejected_features"):
            self.rejected_features.extend(analysis["rejected_features"])

        # 2. 生成优化方案
        refined_plan = await self._generate_refined_plan(
            feedback=feedback,
            analysis=analysis,
            previous_plan=previous_plan,
            context=request.context
        )

        # 3. 评价优化方案
        evaluation = await self._evaluate(refined_plan, request.context.target_scene)

        # 4. 解释改动（推理过程）
        reasoning = self._explain_refinement(
            old_plan=previous_plan,
            new_plan=refined_plan,
            feedback=feedback,
            analysis=analysis
        )

        # 5. 主动建议
        suggestions = self._generate_suggestions(refined_plan, evaluation, request.context)

        # 6. 检查警告
        warnings = self._check_warnings(refined_plan, request.context)

        # 更新内部状态
        self.current_plan = refined_plan
        self.conversation_history.append({
            "role": "assistant",
            "plan": refined_plan,
            "feedback": feedback,
            "iteration": self.iteration_count,
            "timestamp": datetime.now().isoformat()
        })

        return AgentResponse(
            agent="outfit_advisor",
            status="success",
            request_id=request.request_id,
            result=refined_plan,
            outfits=refined_plan.get("outfits", []),
            plan=refined_plan,
            evaluation=evaluation,
            reasoning=reasoning,
            suggestions=suggestions,
            warnings=warnings,
            metadata={
                "iteration": self.iteration_count,
                "feedback_type": analysis.get("type"),
                "adjustments": analysis.get("adjustments", {}),
            }
        )

    # ============================================================
    # evaluate_outfit：独立评价
    # ============================================================

    async def evaluate_outfit(self, request: AgentRequest) -> AgentResponse:
        """独立评价一套穿搭方案"""
        plan = request.context.current_plan or request.previous_plan

        evaluation = await self._evaluate(plan, request.context.target_scene)
        reasoning = self._generate_evaluation_reasoning(evaluation)

        suggestions = [
            f"配色{evaluation.color_score}分：{evaluation.pros[0] if evaluation.pros else '需改进'}",
            f"风格{evaluation.style_score}分：{evaluation.suggestions[0] if evaluation.suggestions else '良好'}",
        ]

        return AgentResponse(
            agent="outfit_advisor",
            status="success",
            request_id=request.request_id,
            evaluation=evaluation,
            reasoning=reasoning,
            suggestions=suggestions,
            metadata={"plan_summary": plan.get("description", "")[:50]}
        )

    # ============================================================
    # 内部方法
    # ============================================================

    def _build_planning_prompt(self, context: OutfitContext) -> str:
        """构建规划提示词"""
        # 按品类分组衣柜
        wardrobe_by_category = {}
        for item in context.wardrobe_items:
            cat = item.get("category", "unknown")
            wardrobe_by_category.setdefault(cat, []).append(item)

        # 构建衣物列表文本
        wardrobe_text = ""
        for cat, items in wardrobe_by_category.items():
            wardrobe_text += f"\n【{cat}】共 {len(items)} 件："
            for item in items[:5]:  # 每个品类最多5件
                wardrobe_text += f"\n  - {item.get('name', item.get('color', ''))} {item.get('color', '')}"

        # 用户偏好
        preferences_text = ""
        if self.preferences.get("liked_colors"):
            preferences_text += f"\n用户喜欢的颜色：{', '.join(self.preferences['liked_colors'])}"
        if self.preferences.get("disliked_colors"):
            preferences_text += f"\n用户不喜欢的颜色：{', '.join(self.preferences['disliked_colors'])}"
        if self.preferences.get("liked_styles"):
            preferences_text += f"\n用户喜欢的风格：{', '.join(self.preferences['liked_styles'])}"
        if self.preferences.get("likely_height"):
            preferences_text += f"\n用户可能身材：{self.preferences['likely_height']}"

        prompt = f"""请为用户生成穿搭方案。

【用户信息】
城市：{context.target_city or '未指定'}
场合：{context.target_scene or '未指定'}
日期：{context.target_date or '今天'}
温度：{context.temperature}°C（{context.weather_condition or ''}）

【用户衣柜】{wardrobe_text}

【用户偏好】{preferences_text}

【已拒绝的特征】（避免重复）
{', '.join(self.rejected_features) if self.rejected_features else '无'}

【已接受的历史特征】
{', '.join(self.accepted_features) if self.accepted_features else '无'}

请生成 1-2 个穿搭方案，用 JSON 格式返回：
{{
  "description": "方案整体描述（1-2句话）",
  "overall_concept": "这套的核心概念",
  "outfits": [
    {{
      "slot": "top",
      "clothes_id": "衣物ID或描述",
      "name": "衣物名称",
      "color": "颜色",
      "reason": "这件为什么选它"
    }}
  ],
  "color_scheme": "配色方案描述",
  "suitable_occasions": ["适合的场合"],
  "match_score": 85
}}
"""
        return prompt

    async def _analyze_feedback(self, feedback: str) -> Dict:
        """理解用户反馈的语义"""
        FEEDBACK_ANALYSIS_PROMPT = f"""分析用户反馈的语义，转化为具体的调整指令。

用户反馈：「{feedback}」

已知信息：
- 用户已拒绝的特征：{self.rejected_features}
- 用户已接受的特征：{self.accepted_features}
- 当前是第 {self.iteration_count + 1} 次迭代

【反馈类型分类】
- formal_adjust：正式度调整（"太正式" / "太休闲"）
- color_change：颜色调整（"换个颜色"）
- style_change：风格调整（"年轻一点" / "成熟一点"）
- body_fit：身材适配（"显瘦" / "显高"）
- quality：质量偏好（"质感好一点"）
- reject：完全拒绝（"不要这个"）
- accept：确认采纳（"就这套了"）

【调整策略】
- "太正式" → 降低正式度：换休闲品类、加休闲元素
- "太休闲" → 提升正式度：换正式品类、加正式感单品
- "年轻一点" → 浅色系、简化款式、避免老气元素
- "显瘦" → 深色系、避免膨胀材质、高腰线
- "显高" → 高腰单品、短款上衣、竖线条
- "换个颜色" → 替换为互补色或相近色
- "不要这个" → 记录被拒绝的特征，下次完全避开

请用 JSON 返回分析结果：
{{
  "type": "formal_adjust/color_change/style_change/body_fit/reject/accept",
  "adjustments": {{
    "formal_delta": +1/-1/0,  // 正式度调整方向
    "target_colors": ["..."] or null,
    "avoid_colors": ["..."] or null,
    "style_direction": "casual/formal/younger/mature" or null,
    "body_concern": "显瘦/显高/null"
  }},
  "reasoning": "你的推理过程（1-2句话）",
  "confidence": 0.85,
  "rejected_features": ["这次被拒绝的特征"],
  "is_terminal": false  // 是否应该停止迭代
}}
"""

        response = await self.llm.ainvoke([
            SystemMessage(content="你是一个专业的时尚反馈分析师。"),
            HumanMessage(content=FEEDBACK_ANALYSIS_PROMPT)
        ])

        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {"type": "unknown", "adjustments": {}, "reasoning": "无法解析反馈", "confidence": 0.0}

    async def _generate_refined_plan(self, feedback: str, analysis: Dict,
                                     previous_plan: Dict, context: OutfitContext) -> Dict:
        """根据反馈生成优化方案"""
        adjustments = analysis.get("adjustments", {})

        # 构建优化提示词
        prompt = f"""用户对之前的穿搭方案不满意，给出了反馈：「{feedback}」

你的分析：「{analysis.get('reasoning', '')}」

【调整指令】
正式度方向：{"降低" if adjustments.get("formal_delta") == -1 else "提升" if adjustments.get("formal_delta") == 1 else "不变"}
目标颜色：{adjustments.get("target_colors") or '无特定要求'}
避免颜色：{adjustments.get("avoid_colors") or '无'}
风格方向：{adjustments.get("style_direction") or '无'}
身材考虑：{adjustments.get("body_concern") or '无'}

【原方案】
{json.dumps(previous_plan, ensure_ascii=False, indent=2)}

【用户衣柜】（按品类）
"""

        wardrobe_by_category = {}
        for item in context.wardrobe_items:
            cat = item.get("category", "unknown")
            wardrobe_by_category.setdefault(cat, []).append(item)

        for cat, items in wardrobe_by_category.items():
            prompt += f"\n【{cat}】{len(items)} 件："
            for item in items[:5]:
                prompt += f"\n  - {item.get('name', '')} {item.get('color', '')}"

        prompt += f"""
\n【偏好】
喜欢的颜色：{', '.join(self.preferences.get('liked_colors', []))}
不喜欢的颜色：{', '.join(self.preferences.get('disliked_colors', []))}

【要求】
1. 基于原方案进行调整，不要完全重新生成
2. 保留原方案中好的部分，只改动反馈涉及的部分
3. 给出修改理由
4. 用 JSON 格式返回：
{{
  "description": "方案描述",
  "changes_from_previous": ["具体改动了哪些部分"],
  "outfits": [...]
}}
"""

        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        plan = self._parse_plan(response.content)
        return plan

    async def _evaluate(self, plan: Dict, scene: str) -> OutfitEvaluation:
        """评价穿搭方案"""
        EVAL_PROMPT = f"""请严格评价以下穿搭方案：

场景：{scene or '未指定'}

方案：
{json.dumps(plan, ensure_ascii=False, indent=2)}

请从以下维度评价并给出分数（0-100）：
1. 色彩协调性（color）
2. 风格一致性（style）
3. 场合得体性（scene）
4. 层次感（layering）
5. 身材适配性（body_fit）

输出 JSON：
{{
  "overall_score": 85,
  "color_score": 90,
  "style_score": 80,
  "scene_score": 85,
  "layering_score": 75,
  "body_fit_score": 80,
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "suggestions": ["...", "..."]
}}
"""
        response = await self.llm.ainvoke([
            SystemMessage(content="你是一个严格专业的穿搭评审。"),
            HumanMessage(content=EVAL_PROMPT)
        ])

        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return OutfitEvaluation(**data)
        except:
            pass

        return OutfitEvaluation(
            overall_score=80,
            color_score=80, style_score=80, scene_score=80,
            layering_score=80, body_fit_score=80,
            pros=["方案整体合理"], cons=[], suggestions=[]
        )

    def _parse_plan(self, content: str) -> Dict:
        """解析 LLM 返回的方案"""
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"description": content, "outfits": [], "overall_concept": ""}

    def _generate_reasoning(self, plan: Dict, context: OutfitContext,
                          evaluation: OutfitEvaluation) -> str:
        """生成推理过程文本（展示给用户）"""
        scene = context.target_scene or "日常"
        temp = context.temperature

        # 从方案中提取关键信息
        colors = set()
        items = plan.get("outfits", [])
        for item in items:
            if item.get("color"):
                colors.add(item["color"])

        reasoning_parts = []

        # 温度适应
        if temp:
            if temp < 10:
                reasoning_parts.append(f"天冷了（{temp}°C），选了保暖的搭配")
            elif temp > 25:
                reasoning_parts.append(f"天热（{temp}°C），选了轻薄透气的搭配")
            else:
                reasoning_parts.append(f"温度适中（{temp}°C），搭配灵活")

        # 场合匹配
        if scene:
            scene_map = {
                "work": "上班得体但不刻板",
                "date": "约会要有亮点但不刻意",
                "daily": "日常舒适有活力",
                "party": "聚会要有气场",
                "sport": "运动功能优先"
            }
            reasoning_parts.append(f"场合是'{scene}'，{scene_map.get(scene, '得体为原则')}")

        # 配色
        if colors:
            reasoning_parts.append(f"配色是{'+'.join(list(colors)[:3])}，协调不杂乱")

        return "，".join(reasoning_parts)

    def _generate_suggestions(self, plan: Dict, evaluation: OutfitEvaluation,
                            context: OutfitContext) -> List[str]:
        """生成主动建议"""
        suggestions = []

        # 从评价中提取建议
        if evaluation and evaluation.suggestions:
            for s in evaluation.suggestions[:2]:
                suggestions.append(s)

        # 主动发现的改进点
        if evaluation and evaluation.score < 80:
            if evaluation.cons:
                suggestions.append(f"小建议：{evaluation.cons[0]}")

        # 场合相关的额外建议
        scene = context.target_scene
        if scene == "date":
            suggestions.append("约会可以加一点香水，提升整体氛围感")
        elif scene == "work":
            suggestions.append("上班建议带一个质感好的包，提升专业度")

        return suggestions[:3]

    def _check_warnings(self, plan: Dict, context: OutfitContext) -> List[str]:
        """检查需要提醒的问题"""
        warnings = []

        # 温度检查
        if context.temperature and context.temperature < 5:
            if not any(item.get("slot") == "outer" for item in plan.get("outfits", [])):
                warnings.append("⚠️ 温度很低（5°C以下），建议加一件外套")

        # 场合检查
        scene = context.target_scene
        if scene == "work" and context.temperature and context.temperature > 20:
            if any("运动" in item.get("name", "") for item in plan.get("outfits", [])):
                warnings.append("⚠️ 正式场合建议避免运动单品")

        return warnings

    def _explain_refinement(self, old_plan: Dict, new_plan: Dict,
                           feedback: str, analysis: Dict) -> str:
        """解释优化方向"""
        adjustments = analysis.get("adjustments", {})
        feedback_type = analysis.get("type", "unknown")

        explanations = {
            "formal_adjust": f"收到'{feedback}'，我调整了正式度",
            "color_change": f"收到'{feedback}'，换了配色方案",
            "style_change": f"收到'{feedback}'，调整了风格方向",
            "body_fit": f"收到'{feedback}'，换了更合适的款式",
            "reject": f"收到'{feedback}'，重新设计方案",
            "unknown": f"根据反馈重新优化",
        }

        return explanations.get(feedback_type, "根据反馈优化")

    def _generate_evaluation_reasoning(self, evaluation: OutfitEvaluation) -> str:
        """评价推理过程"""
        parts = []
        if evaluation.pros:
            parts.append(f"优点：{evaluation.pros[0]}")
        if evaluation.cons:
            parts.append(f"不足：{evaluation.cons[0]}")
        if evaluation.suggestions:
            parts.append(f"建议：{evaluation.suggestions[0]}")
        return "；".join(parts)
```

### 4.3 多轮迭代状态管理

OutfitAdvisor 内部维护完整的多轮状态：

```python
class OutfitAdvisorAgent:
    # 内部状态
    conversation_history: List[Dict]      # 完整对话历史
    current_plan: Optional[Dict]          # 当前方案
    iteration_count: int                  # 迭代次数
    rejected_features: List[str]          # 被拒绝的特征
    accepted_features: List[str]          # 被接受的特征

    # 状态持久化（用于跨 session）
    def save_state(self) -> Dict:
        return {
            "iteration_count": self.iteration_count,
            "rejected_features": self.rejected_features,
            "accepted_features": self.accepted_features,
            "conversation_history": self.conversation_history[-20:],  # 最近20条
        }

    def load_state(self, state: Dict):
        self.iteration_count = state.get("iteration_count", 0)
        self.rejected_features = state.get("rejected_features", [])
        self.accepted_features = state.get("accepted_features", [])
        self.conversation_history = state.get("conversation_history", [])
```

---

## 五、WardrobeCurator Agent

### 5.1 Agent 职责

WardrobeCurator 是 FashionSteward 的**衣橱管家**，负责主动管理用户的衣物资产。

**职责范围**：
- 衣橱健康检查（利用率、未穿衣物、穿着频率）
- 未穿衣物提醒（60天/90天阈值）
- 风格缺口分析（用户想生成某风格但缺少关键品类）
- 穿着规律分析（偏好颜色、风格、场合）
- 参考图风格复刻（分析风格 + 衣柜匹配）
- 主动出击，不等用户问

**性格特征**：
- 细心，主动发现问题
- 给出具体可行的建议
- 善于发现"隐形资产"

### 5.2 Agent 实现

```python
# app/agent/wardrobe_curator.py

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from app.agent.protocol import AgentRequest, AgentResponse, TaskType
from app.agent.tools.context import get_db_for_tools, get_current_user_id
from app.services.llm_providers import get_cached_provider
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """你是 WardrobeCurator，一个细心的衣橱管家，像管理自己的衣橱一样管理用户的衣物。

【你的职责】
1. 衣橱健康检查：定期检查衣橱状态，发现问题
2. 未穿提醒：发现长期未穿的衣物，主动询问用户
3. 风格缺口分析：发现衣柜中缺失的关键品类
4. 穿着规律分析：从历史数据中发现用户的穿衣偏好
5. 参考图复刻：分析参考图风格，在衣柜中找相似单品

【你的主动性】
- 不等用户问，定期检查衣橱状态
- 发现问题主动报告，不沉默
- 给出具体建议，不只是"您有些衣服没穿"

【提醒策略】
- 未穿衣物60天 → 温和询问（"好久没穿了，是不喜欢还是忘了？"）
- 未穿衣物90天 → 强烈建议（"这件建议考虑处理掉"）
- 穿着频率不均 → 建议添置替换款
- 风格缺口 → 给出具体缺失品类和添置建议

【你的语言风格】
- 口语化，像朋友聊天
- 提到衣物时用具体名称，不说"这件衣服"
- 给出明确建议，不模糊其辞
- 主动给出下一步行动建议
"""


class WardrobeCuratorAgent:
    """真正的衣橱管家 Agent"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = get_cached_provider().chat_model

        # Agent 内部状态
        self.last_health_check: Optional[datetime] = None
        self.unused_items_cache: List[Dict] = []

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """统一入口"""
        try:
            if request.task == TaskType.WARDROBE_HEALTH:
                return await self.check_wardrobe_health(request)
            elif request.task == TaskType.UNUSED_REMINDER:
                return await self.get_unused_reminder(request)
            elif request.task == TaskType.STYLE_GAP:
                return await self.analyze_style_gap(request)
            elif request.task == TaskType.STYLE_MATCH:
                return await self.match_style(request)
            elif request.task == TaskType.WEARING_PATTERN:
                return await self.analyze_wearing_pattern(request)
            else:
                return AgentResponse(
                    agent="wardrobe_curator",
                    status="failed",
                    request_id=request.request_id,
                    error=f"Unknown task: {request.task}"
                )
        except Exception as e:
            return AgentResponse(
                agent="wardrobe_curator",
                status="failed",
                request_id=request.request_id,
                error=f"{type(e).__name__}: {str(e)}"
            )

    # ============================================================
    # 衣橱健康检查
    # ============================================================

    async def check_wardrobe_health(self, request: AgentRequest) -> AgentResponse:
        """检查衣橱健康度"""
        db = get_db_for_tools()
        user_id = self.user_id

        # 1. 获取衣橱数据
        wardrobe_items = self._get_wardrobe_items(db, user_id)
        total_items = len(wardrobe_items)

        # 2. 分析穿着频率
        wear_counts = [(item["name"], item.get("wear_count", 0), item.get("last_worn_at"))
                      for item in wardrobe_items]
        wear_counts.sort(key=lambda x: x[1], reverse=True)

        avg_wear = sum(w[1] for w in wear_counts) / len(wear_counts) if wear_counts else 0

        # 3. 长期未穿衣物
        now = datetime.now()
        unused_60 = []
        unused_90 = []
        for item in wardrobe_items:
            last_worn = item.get("last_worn_at")
            if last_worn:
                days_ago = (now - last_worn).days
                if days_ago >= 90:
                    unused_90.append({**item, "days_ago": days_ago})
                elif days_ago >= 60:
                    unused_60.append({**item, "days_ago": days_ago})

        # 4. 穿着过频
        overused = [(name, count, last) for name, count, last in wear_counts
                    if count > avg_wear * 3 and count > 5]

        # 5. 颜色分布
        color_dist = {}
        for item in wardrobe_items:
            color = item.get("color", "未知")
            color_dist[color] = color_dist.get(color, 0) + 1

        # 6. 品类分布
        category_dist = {}
        for item in wardrobe_items:
            cat = item.get("category", "未知")
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # 7. 计算健康度
        health_score = self._calculate_health_score(
            total_items=total_items,
            unused_60=len(unused_60),
            unused_90=len(unused_90),
            overused=len(overused),
            color_variety=len(color_dist),
            category_variety=len(category_dist)
        )

        # 8. 生成报告
        health_report = {
            "health_score": health_score,
            "total_items": total_items,
            "recently_worn": total_items - len(unused_60) - len(unused_90),
            "unused_60_days": len(unused_60),
            "unused_90_days": len(unused_90),
            "overused_count": len(overused),
            "color_distribution": dict(sorted(color_dist.items(), key=lambda x: x[1], reverse=True)[:5]),
            "category_distribution": category_dist,
            "most_worn": wear_counts[:5],
            "least_worn": [(n, c, d) for n, c, d in wear_counts[-5:] if c > 0],
        }

        # 9. 生成提醒
        reminders = []
        if unused_90:
            reminders.append({
                "type": "critical",
                "title": "这些衣服好久没穿了",
                "items": [{"name": i["name"], "days": i["days_ago"]} for i in unused_90[:3]],
                "action": "建议考虑处理"
            })
        if unused_60:
            reminders.append({
                "type": "warning",
                "title": "有些衣服好久没宠幸了",
                "items": [{"name": i["name"], "days": i["days_ago"]} for i in unused_60[:3]],
                "action": "要帮您想想怎么搭配吗？"
            })
        if overused:
            reminders.append({
                "type": "info",
                "title": "穿着频率有点集中",
                "items": [{"name": name, "count": count} for name, count, _ in overused[:2]],
                "action": "建议添置替换款"
            })

        # 10. 生成推理过程
        reasoning = f"您的衣橱共有 {total_items} 件衣服"
        if health_score >= 80:
            reasoning += "，状态不错 👍"
        elif health_score >= 60:
            reasoning += "，有点小问题需要注意"
        else:
            reasoning += "，需要好好整理一下了"

        if unused_90:
            reasoning += f"。有 {len(unused_90)} 件衣服超过3个月没穿了"
        if overused:
            reasoning += f"。有 {len(overused)} 件衣服穿得特别频繁"

        self.last_health_check = now
        self.unused_items_cache = unused_60 + unused_90

        return AgentResponse(
            agent="wardrobe_curator",
            status="success",
            request_id=request.request_id,
            health_report=health_report,
            reasoning=reasoning,
            suggestions=[r["action"] for r in reminders],
            warnings=[f"{r['title']}: {len(r['items'])}件" for r in reminders],
            metadata={
                "health_score": health_score,
                "reminder_count": len(reminders)
            }
        )

    # ============================================================
    # 参考图风格复刻
    # ============================================================

    async def match_style(self, request: AgentRequest) -> AgentResponse:
        """分析参考图风格，在衣柜中找相似单品"""
        from app.services.image_analysis import image_analyzer

        reference_image = request.reference_image_url
        if not reference_image:
            return AgentResponse(
                agent="wardrobe_curator",
                status="failed",
                request_id=request.request_id,
                error="缺少参考图片"
            )

        # 1. 风格分析
        style_analysis_prompt = """分析这张穿搭图片，返回 JSON：
{
  "primary_colors": ["主色调"],
  "style_tags": ["风格标签1", "风格标签2"],
  "fit_type": "宽松/修身/正常",
  "key_items": [{"slot": "品类", "description": "描述", "color": "颜色"}],
  "suitable_scenes": ["适合场合"],
  "overall_style": "风格总结"
}"""
        style_result = await image_analyzer.analyze(
            image_url=reference_image,
            prompt=style_analysis_prompt
        )

        # 2. 在衣柜中匹配
        wardrobe_items = request.context.wardrobe_items
        matched_items = []
        missing_categories = []

        for key_item in style_result.get("key_items", []):
            slot = key_item.get("slot", "").lower()
            target_color = key_item.get("color", "")
            target_desc = key_item.get("description", "")

            # 在衣柜中找最佳匹配
            best_match = None
            best_score = 0

            for item in wardrobe_items:
                if not self._slot_matches(item.get("category", ""), slot):
                    continue

                score = 0
                # 颜色匹配
                if target_color and target_color in item.get("color", ""):
                    score += 50
                # 风格描述匹配
                if any(tag.lower() in (item.get("scene", "") + item.get("name", "")).lower()
                       for tag in style_result.get("style_tags", [])):
                    score += 30

                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= 40:
                matched_items.append({
                    "reference": key_item,
                    "matched": best_match,
                    "similarity": min(best_score, 100),
                    "match_quality": "exact" if best_score >= 70 else "similar"
                })
            else:
                missing_categories.append({
                    "slot": slot,
                    "description": target_desc,
                    "color": target_color
                })

        # 3. 计算还原度
        total_items = len(style_result.get("key_items", []))
        replication_score = int(len(matched_items) / max(total_items, 1) * 100)

        # 4. 生成建议
        suggestions = []
        if missing_categories:
            suggestions.append(f"缺少 {len(missing_categories)} 件关键单品")
            for m in missing_categories[:2]:
                suggestions.append(f"建议添置一件{m.get('slot', '')}（{m.get('description', '')}）")

        reasoning = f"这套是 {style_result.get('overall_style', '未知风格')}，"
        if replication_score >= 80:
            reasoning += f"您的衣柜可以 {replication_score}% 还原！"
        elif replication_score >= 50:
            reasoning += f"您的衣柜可以还原 {replication_score}%，"
            reasoning += f"但还缺 {len(missing_categories)} 件关键单品"
        else:
            reasoning += "您的衣柜目前难以还原，建议添置关键单品"

        return AgentResponse(
            agent="wardrobe_curator",
            status="success",
            request_id=request.request_id,
            result={
                "style_analysis": style_result,
                "replication_score": replication_score
            },
            matched_items=matched_items,
            reasoning=reasoning,
            suggestions=suggestions,
            metadata={
                "total_key_items": total_items,
                "matched_count": len(matched_items),
                "missing_count": len(missing_categories)
            }
        )

    # ============================================================
    # 内部方法
    # ============================================================

    def _get_wardrobe_items(self, db, user_id: str) -> List[Dict]:
        """获取用户衣橱"""
        from app.models import UserClothes
        items = db.query(UserClothes).filter(
            UserClothes.user_id == user_id,
            UserClothes.is_deleted == False
        ).all()

        result = []
        for item in items:
            result.append({
                "id": str(item.id),
                "name": item.name or item.description or "",
                "category": item.category,
                "color": item.color or "",
                "material": item.material or "",
                "scene": item.scene or "",
                "image_url": item.image_url or item.original_image_url or "",
                "wear_count": item.wear_count or 0,
                "last_worn_at": item.last_worn_at,
                "temperature_range": item.temperature_range or "",
            })
        return result

    def _calculate_health_score(self, total_items: int, unused_60: int,
                                unused_90: int, overused: int,
                                color_variety: int, category_variety: int) -> int:
        """计算衣橱健康度"""
        score = 100

        if total_items == 0:
            return 0

        # 长期未穿扣分
        score -= min(unused_60 * 5, 25)
        score -= min(unused_90 * 10, 35)

        # 穿着过频扣分
        score -= min(overused * 8, 20)

        # 颜色单一扣分
        if color_variety < 3:
            score -= 10
        elif color_variety < 5:
            score -= 5

        # 品类单一扣分
        if category_variety < 3:
            score -= 10

        return max(0, min(100, score))

    def _slot_matches(self, item_category: str, target_slot: str) -> bool:
        """判断品类是否匹配"""
        mapping = {
            "top": ["top", "shirt", "blouse", "t-shirt", "上衣"],
            "pants": ["pants", "trousers", "jeans", "skirt", "裤子"],
            "outer": ["outer", "jacket", "coat", "外套"],
            "inner": ["inner", "underwear", "打底"],
            "accessory": ["accessory", "shoes", "bag", "配饰", "鞋子"],
        }
        target_lower = target_slot.lower()
        for key, values in mapping.items():
            if any(v in target_lower for v in values):
                return key == item_category or item_category in mapping.get(key, [])
        return item_category == target_slot
```

---

## 六、SupervisorAgent 重构

### 6.1 重构后的 SupervisorAgent

```python
# app/agent/supervisor.py 重构

import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator

from app.agent.memory import AgentMemory
from app.agent.dialogue_session import DialogueSessionManager, Message
from app.agent.tools.context import get_db_for_tools, get_current_user_id
from app.agent.tools.shared import get_weather, analyze_clothing_image, remember_context, recall_context
from app.agent.tools.wardrobe import search_wardrobe, add_clothes_to_wardrobe
from app.agent.tools.outfit import get_outfit_history
from app.agent.tools.care import get_care_guide
from app.agent.tools.knowledge import search_knowledge_base
from app.agent.outfit_advisor import OutfitAdvisorAgent
from app.agent.wardrobe_curator import WardrobeCuratorAgent
from app.agent.protocol import (
    AgentRequest, AgentResponse, TaskType,
    OutfitContext, OutfitEvaluation
)
from app.agent.services.preference_learner import PreferenceLearner
from app.services.llm_providers import get_cached_provider
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage


SYSTEM_PROMPT = """你是一个专业、贴心、有主见的穿搭管家。

【你的身份】
你是 FashionSteward 的核心大脑，同时协调 OutfitAdvisor（穿搭顾问）和 WardrobeCurator（衣橱管家）为你服务。

【你的职责】
1. 理解用户的自然语言请求
2. 判断是否需要专业 Agent 的帮助
3. 调用合适的 Agent 或 Tool
4. 整合结果，用友好的方式呈现给用户
5. 维护对话上下文，支持多轮对话

【你的主动服务意识】
不要只是被动响应，要主动发现问题：
- 发现用户缺少某个季节的关键衣物 → 主动提醒
- 发现衣橱有长期未穿的衣物 → 主动询问
- 生成的方案有明显的搭配问题 → 主动指出

【对话风格】
- 口语化，每句不超过15字
- 主动给搭配理由
- 用 emoji 标注品类（👕👖🧥🎒）
- 有自己的审美判断，敢于说真话

【追问策略】
- 缺少城市 → "请问要去哪个城市呢？"
- 缺少场合 → "请问是什么场合呢？（上班/约会/运动...）"
- 缺少季节 → "那是什么季节呢？春夏秋冬？"
- 用户意图不明 → "我需要更多信息来帮您，请描述一下具体需求？"
"""


class SupervisorAgent:
    """
    唯一的编排 Agent。
    负责任务路由，调用专业 Agent 或 Tool，整合结果输出给用户。
    """

    def __init__(self, session_id: str, user_id: str,
                 session_manager: DialogueSessionManager = None, db=None):
        self.session_id = session_id
        self.user_id = user_id
        self.session_manager = session_manager

        # 初始化 AgentMemory
        self.memory = self._init_memory()

        # 偏好学习器
        self.preference_learner = PreferenceLearner()

        # LLM
        self.llm = get_cached_provider().chat_model
        self.llm_with_tools = self.llm.bind_tools(list(self._get_tools().values()))

        # 专业 Agent 实例（跨轮次维护）
        self.outfit_advisor: Optional[OutfitAdvisorAgent] = None
        self.wardrobe_curator: Optional[WardrobeCuratorAgent] = None

        # 当前意图
        self.current_intent: Optional[str] = None

    # ============================================================
    # 核心方法
    # ============================================================

    async def run_stream(
        self, user_message: str, images: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行主循环"""
        self.memory.add_message("user", user_message)
        yield {"type": "thinking", "content": "正在分析您的请求..."}

        # 1. 意图分类
        intent = await self._classify_intent(user_message, images)
        self.current_intent = intent

        # 2. 根据意图分发
        if intent in ["outfit_plan", "outfit_refine"]:
            async for event in self._handle_outfit_intent(intent, user_message, images):
                yield event

        elif intent == "wardrobe_check":
            async for event in self._handle_wardrobe_intent(user_message):
                yield event

        elif intent == "style_match":
            async for event in self._handle_style_match_intent(user_message, images):
                yield event

        elif intent == "care_guide":
            async for event in self._handle_care_intent(user_message):
                yield event

        else:
            # 其他意图走 Tool
            async for event in self._handle_tool_intent(intent, user_message, images):
                yield event

        # 3. 保存状态
        self.save_to_session()

    # ============================================================
    # OutfitAdvisor 流程
    # ============================================================

    async def _handle_outfit_intent(self, intent: str, user_message: str,
                                   images: List[str]) -> AsyncGenerator[Dict, None]:
        """处理穿搭相关意图"""

        # 初始化或复用 OutfitAdvisor
        if self.outfit_advisor is None:
            preferences = self.preference_learner.get_preferences_for_user(self.user_id)
            self.outfit_advisor = OutfitAdvisorAgent(
                user_id=self.user_id,
                preferences=preferences
            )

        # 构建上下文
        context = await self._build_outfit_context()

        if intent == "outfit_plan":
            # 初始方案生成
            request = AgentRequest(
                task=TaskType.PLAN_OUTFIT,
                agent="outfit_advisor",
                context=context,
                conversation_history=self.memory.recent_messages[-10:]
            )

            yield {"type": "thinking", "content": "正在为您规划穿搭..."}
            response = await self.outfit_advisor.handle(request)

        else:  # outfit_refine
            # 迭代优化
            request = AgentRequest(
                task=TaskType.REFINE_OUTFIT,
                agent="outfit_advisor",
                context=context,
                conversation_history=self.memory.recent_messages[-10:],
                feedback=user_message,
                previous_plan=self.memory.current_plan
            )

            yield {"type": "thinking", "content": "收到反馈，正在调整..."}
            response = await self.outfit_advisor.handle(request)

        # 输出响应事件
        if response.status == "success":
            for event in response.to_stream_events():
                yield event

            # 保存当前方案到 memory
            self.memory.current_plan = response.plan
            self.memory.current_evaluation = response.evaluation
        else:
            yield {"type": "error", "content": response.error}

        yield {"type": "done", "content": ""}

    async def _build_outfit_context(self) -> OutfitContext:
        """构建穿搭上下文"""
        # 获取天气
        temperature = self.memory.target_temperature
        city = self.memory.target_city

        if city and not temperature:
            weather_result = await get_weather.invoke({"city": city})
            try:
                weather_data = json.loads(weather_result)
                temperature = weather_data.get("temperature")
            except:
                pass

        # 获取衣柜
        wardrobe_result = await search_wardrobe.invoke({})
        try:
            wardrobe_items = json.loads(wardrobe_result)
        except:
            wardrobe_items = []

        # 获取偏好
        preferences = self.preference_learner.get_preferences_for_user(self.user_id)

        return OutfitContext(
            user_id=self.user_id,
            target_city=self.memory.target_city,
            target_scene=self.memory.target_scene,
            target_date=self.memory.target_date,
            temperature=temperature,
            wardrobe_items=wardrobe_items,
            wardrobe_summary=self._summarize_wardrobe(wardrobe_items),
            current_plan=self.memory.current_plan,
            preferences=preferences
        )

    # ============================================================
    # WardrobeCurator 流程
    # ============================================================

    async def _handle_wardrobe_intent(self, user_message: str) -> AsyncGenerator[Dict, None]:
        """处理衣橱相关意图"""
        if self.wardrobe_curator is None:
            self.wardrobe_curator = WardrobeCuratorAgent(user_id=self.user_id)

        context = await self._build_outfit_context()

        request = AgentRequest(
            task=TaskType.WARDROBE_HEALTH,
            agent="wardrobe_curator",
            context=context
        )

        yield {"type": "thinking", "content": "正在检查您的衣橱..."}
        response = await self.wardrobe_curator.handle(request)

        if response.status == "success":
            if response.reasoning:
                yield {"type": "reasoning", "content": response.reasoning}

            # 输出健康度
            health = response.health_report or {}
            yield {
                "type": "wardrobe_health",
                "content": {
                    "score": health.get("health_score", 0),
                    "total_items": health.get("total_items", 0),
                    "unused_60": health.get("unused_60_days", 0),
                    "unused_90": health.get("unused_90_days", 0),
                }
            }

            for suggestion in response.suggestions:
                yield {"type": "suggestion", "content": suggestion}
        else:
            yield {"type": "error", "content": response.error}

        yield {"type": "done", "content": ""}

    # ============================================================
    # 其他流程
    # ============================================================

    async def _handle_style_match_intent(self, user_message: str,
                                        images: List[str]) -> AsyncGenerator[Dict, None]:
        """处理参考图风格复刻"""
        if not images:
            yield {"type": "error", "content": "请上传参考图片"}
            yield {"type": "done", "content": ""}
            return

        if self.wardrobe_curator is None:
            self.wardrobe_curator = WardrobeCuratorAgent(user_id=self.user_id)

        context = await self._build_outfit_context()

        request = AgentRequest(
            task=TaskType.STYLE_MATCH,
            agent="wardrobe_curator",
            context=context,
            reference_image_url=images[0]
        )

        yield {"type": "thinking", "content": "正在分析穿搭风格..."}
        response = await self.wardrobe_curator.handle(request)

        if response.status == "success":
            for event in response.to_stream_events():
                yield event
        else:
            yield {"type": "error", "content": response.error}

        yield {"type": "done", "content": ""}

    async def _handle_tool_intent(self, intent: str, user_message: str,
                                  images: List[str]) -> AsyncGenerator[Dict, None]:
        """处理走 Tool 的意图（fallback）"""
        # 使用 LLM Function Calling
        messages = self._build_messages(user_message, images)
        response = await self.llm_with_tools.ainvoke(messages)

        max_turns = 5
        turn = 0

        while response.tool_calls and turn < max_turns:
            turn += 1
            for tc in response.tool_calls:
                yield {"type": "tool_called", "tool": tc.name, "args": tc.args}

                try:
                    result = await self._get_tools()[tc.name].invoke(tc.args)
                except Exception as e:
                    result = json.dumps({"error": type(e).__name__, "message": str(e)})

                yield {"type": "tool_result", "tool": tc.name, "result": result}
                messages.append(ToolMessage(name=tc.name, content=result))

            response = await self.llm_with_tools.ainvoke(messages)

        final_text = response.content if response.content else ""
        if final_text:
            self.memory.add_message("assistant", final_text)

        yield {"type": "text", "content": final_text}
        yield {"type": "done", "content": final_text}

    # ============================================================
    # 辅助方法
    # ============================================================

    async def _classify_intent(self, user_message: str, images: List[str]) -> str:
        """意图分类"""
        # 检测是否为反馈
        feedback_keywords = [
            "太正式", "太休闲", "换个", "再推荐", "就这套",
            "年轻", "显瘦", "显高", "不好看", "不满意",
            "换一个", "不要这个", "不对", "不太行"
        ]
        is_feedback = any(kw in user_message for kw in feedback_keywords)

        # 如果已有方案且用户在说反馈
        if is_feedback and self.memory.current_plan:
            return "outfit_refine"

        # 检测图片上传
        if images:
            # 如果用户上传图片，可能是：
            # 1. 存衣橱
            # 2. 分析搭配
            # 3. 参考图复刻
            return "style_match"

        # 检测衣橱相关意图
        wardrobe_keywords = ["衣橱", "衣柜", "我有什么", "衣服", "整理", "检查"]
        if any(kw in user_message for kw in wardrobe_keywords):
            return "wardrobe_check"

        # 检测穿搭推荐意图
        outfit_keywords = ["推荐", "穿搭", "穿什么", "怎么穿", "搭配", "今天"]
        if any(kw in user_message for kw in outfit_keywords):
            return "outfit_plan"

        return "general"

    def _build_messages(self, user_message: str, images: List[str] = None) -> List:
        """构建 LLM 消息"""
        memory_text = self.memory.to_context_string()
        system = SYSTEM_PROMPT + f"\n\n【当前上下文】\n{memory_text}"

        messages = [SystemMessage(content=system)]

        for msg in self.memory.recent_messages[-6:]:
            messages.append(HumanMessage(content=msg["content"]))

        if images:
            content = [{"type": "text", "text": user_message}]
            for img in images:
                content.append({"type": "image_url", "image_url": img})
            messages.append(HumanMessage(content=content))
        else:
            messages.append(HumanMessage(content=user_message))

        return messages

    def _get_tools(self) -> Dict:
        """获取 Tool 字典"""
        return {
            get_weather.name: get_weather,
            analyze_clothing_image.name: analyze_clothing_image,
            remember_context.name: remember_context,
            recall_context.name: recall_context,
            search_wardrobe.name: search_wardrobe,
            add_clothes_to_wardrobe.name: add_clothes_to_wardrobe,
            get_outfit_history.name: get_outfit_history,
            get_care_guide.name: get_care_guide,
            search_knowledge_base.name: search_knowledge_base,
        }

    def _summarize_wardrobe(self, items: List[Dict]) -> Dict:
        """生成衣橱摘要"""
        categories = {}
        colors = {}
        for item in items:
            cat = item.get("category", "unknown")
            color = item.get("color", "未知")
            categories[cat] = categories.get(cat, 0) + 1
            colors[color] = colors.get(color, 0) + 1
        return {
            "total": len(items),
            "categories": categories,
            "top_colors": dict(sorted(colors.items(), key=lambda x: x[1], reverse=True)[:3])
        }

    def _init_memory(self) -> AgentMemory:
        """初始化 AgentMemory"""
        if self.session_manager:
            session = self.session_manager.get(self.session_id)
            if session and session.context:
                ctx = session.context
                memory = AgentMemory(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    target_city=getattr(ctx, 'target_city', None),
                    target_scene=getattr(ctx, 'target_scene', None),
                    target_date=getattr(ctx, 'target_date', None),
                    target_temperature=getattr(ctx, 'target_temperature', None),
                )
                if hasattr(session, 'history') and session.history:
                    memory.recent_messages = [
                        {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                        for m in session.history[-20:]
                    ]
                return memory

        return AgentMemory(session_id=self.session_id, user_id=self.user_id)

    def save_to_session(self) -> None:
        """保存状态到 Session"""
        if not self.session_manager:
            return

        session = self.session_manager.get(self.session_id)
        if not session:
            return

        ctx = session.context
        if hasattr(ctx, 'target_city'):
            ctx.target_city = self.memory.target_city
        if hasattr(ctx, 'target_scene'):
            ctx.target_scene = self.memory.target_scene
        if hasattr(ctx, 'target_date'):
            ctx.target_date = self.memory.target_date
        if hasattr(ctx, 'target_temperature'):
            ctx.target_temperature = self.memory.target_temperature

        session.history = [
            Message(role=m["role"], content=m["content"], timestamp=m.get("timestamp", ""))
            for m in self.memory.recent_messages
        ]

        # 保存专业 Agent 状态
        if self.outfit_advisor:
            session.agent_state = {
                "outfit_advisor": {
                    "iteration_count": self.outfit_advisor.iteration_count,
                    "rejected_features": self.outfit_advisor.rejected_features,
                    "conversation_history": self.outfit_advisor.conversation_history[-20:]
                }
            }

        self.session_manager.save(session)
```

---

## 七、数据库改造

### 7.1 新增表

```sql
-- 用户穿搭偏好表
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 颜色偏好
    liked_colors TEXT[] DEFAULT '{}',
    disliked_colors TEXT[] DEFAULT '{}',

    -- 风格偏好
    liked_styles TEXT[] DEFAULT '{}',
    disliked_styles TEXT[] DEFAULT '{}',

    -- 品类偏好
    favorite_categories TEXT[] DEFAULT '{}',
    avoided_categories TEXT[] DEFAULT '{}',

    -- 隐性偏好（从行为推断）
    likely_height VARCHAR(20),        -- "short" / "average" / "tall"
    likely_body_type VARCHAR(50),     -- 从拒绝行为推断

    -- 统计
    total_feedbacks INT DEFAULT 0,
    accept_count INT DEFAULT 0,
    reject_count INT DEFAULT 0,

    -- 置信度
    colors_confidence FLOAT DEFAULT 0.0,
    styles_confidence FLOAT DEFAULT 0.0,
    categories_confidence FLOAT DEFAULT 0.0
);

CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);

-- 偏好反馈记录表
CREATE TABLE preference_feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outfit_history_id UUID REFERENCES outfit_histories(id),
    created_at TIMESTAMP DEFAULT NOW(),

    feedback_type VARCHAR(20) NOT NULL,   -- "accept" / "reject" / "modify"
    feedback_content TEXT NOT NULL,

    -- 解析后的调整
    interpreted JSONB DEFAULT '{}',
    -- {"adjustments": {"formal_delta": -1, "target_colors": ["浅蓝"]}, "type": "formal_adjust"}

    used_for_learning BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_pref_fb_user_id ON preference_feedbacks(user_id);
CREATE INDEX idx_pref_fb_created ON preference_feedbacks(created_at DESC);

-- 衣物新增字段
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS condition_score INT DEFAULT 80;
ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS estimated_lifespan_months INT;
```

### 7.2 ORM 模型

```python
# app/models/preferences.py

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

    liked_colors = Column(ARRAY(String), default=[])
    disliked_colors = Column(ARRAY(String), default=[])
    liked_styles = Column(ARRAY(String), default=[])
    disliked_styles = Column(ARRAY(String), default=[])
    favorite_categories = Column(ARRAY(String), default=[])
    avoided_categories = Column(ARRAY(String), default=[])

    likely_height = Column(String(20))
    likely_body_type = Column(String(50))

    total_feedbacks = Column(Integer, default=0)
    accept_count = Column(Integer, default=0)
    reject_count = Column(Integer, default=0)

    colors_confidence = Column(Float, default=0.0)
    styles_confidence = Column(Float, default=0.0)
    categories_confidence = Column(Float, default=0.0)


class PreferenceFeedback(Base):
    __tablename__ = "preference_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    outfit_history_id = Column(UUID(as_uuid=True), ForeignKey("outfit_histories.id"))
    created_at = Column(DateTime, default=datetime.now)

    feedback_type = Column(String(20), nullable=False)
    feedback_content = Column(String, nullable=False)
    interpreted = Column(JSON, default={})
    used_for_learning = Column(Boolean, default=False)

    user = relationship("User")
    outfit = relationship("OutfitRecord")
```

---

## 八、偏好学习服务

```python
# app/agent/services/preference_learner.py

from sqlalchemy.orm import Session
from app.models import UserPreferences, PreferenceFeedback, UserClothes
from app.database import SessionLocal
import json
from collections import Counter
from typing import Dict, Optional


class PreferenceLearner:
    """
    偏好学习服务。
    从用户反馈中学习，更新 user_preferences 表。
    """

    REJECTION_THRESHOLD = 3
    ACCEPTANCE_THRESHOLD = 2

    def get_preferences_for_user(self, user_id: str) -> Dict:
        """获取用户偏好（返回空 dict 如果不存在）"""
        db = SessionLocal()
        try:
            prefs = db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()

            if not prefs:
                return {}

            return {
                "liked_colors": prefs.liked_colors or [],
                "disliked_colors": prefs.disliked_colors or [],
                "liked_styles": prefs.liked_styles or [],
                "disliked_styles": prefs.disliked_styles or [],
                "favorite_categories": prefs.favorite_categories or [],
                "avoided_categories": prefs.avoided_categories or [],
                "likely_height": prefs.likely_height,
                "likely_body_type": prefs.likely_body_type,
            }
        finally:
            db.close()

    def record_feedback(self, user_id: str, feedback_type: str,
                       feedback_content: str, interpreted: Dict,
                       outfit_history_id: str = None):
        """记录一条反馈"""
        db = SessionLocal()
        try:
            feedback = PreferenceFeedback(
                user_id=user_id,
                outfit_history_id=outfit_history_id,
                feedback_type=feedback_type,
                feedback_content=feedback_content,
                interpreted=interpreted,
            )
            db.add(feedback)
            db.commit()

            # 异步触发学习（也可以同步）
            self.learn_from_new_feedbacks(user_id)
        finally:
            db.close()

    def learn_from_new_feedbacks(self, user_id: str):
        """从新反馈中学习，更新偏好"""
        db = SessionLocal()
        try:
            # 获取未学习的新反馈
            feedbacks = db.query(PreferenceFeedback).filter(
                PreferenceFeedback.user_id == user_id,
                PreferenceFeedback.used_for_learning == False
            ).all()

            if not feedbacks:
                return

            # 获取或创建用户偏好
            prefs = db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()

            if not prefs:
                prefs = UserPreferences(user_id=user_id)
                db.add(prefs)

            # 统计特征频率
            rejected_colors = Counter()
            rejected_styles = Counter()

            for fb in feedbacks:
                adj = fb.interpreted.get("adjustments", {})
                for c in adj.get("avoided_colors") or []:
                    rejected_colors[c] += 1
                for s in adj.get("avoided_styles") or []:
                    rejected_styles[s] += 1

                fb.used_for_learning = True

            # 更新偏好
            self._update_colors(prefs, rejected_colors)
            self._update_styles(prefs, rejected_styles)

            # 推断隐性偏好
            self._infer_body_preferences(prefs, feedbacks)

            # 更新统计
            prefs.total_feedbacks += len(feedbacks)
            prefs.accept_count += sum(1 for f in feedbacks if f.feedback_type == "accept")
            prefs.reject_count += sum(1 for f in feedbacks if f.feedback_type in ["reject", "modify"])

            # 更新置信度
            prefs.colors_confidence = min(1.0, prefs.total_feedbacks / 10)
            prefs.styles_confidence = min(1.0, prefs.total_feedbacks / 10)

            db.commit()
        finally:
            db.close()

    def _update_colors(self, prefs: UserPreferences, rejected: Counter):
        disliked = set(prefs.disliked_colors or [])
        for color, count in rejected.items():
            if count >= self.REJECTION_THRESHOLD:
                disliked.add(color)
        prefs.disliked_colors = list(disliked)

    def _update_styles(self, prefs: UserPreferences, rejected: Counter):
        disliked = set(prefs.disliked_styles or [])
        for style, count in rejected.items():
            if count >= self.REJECTION_THRESHOLD:
                disliked.add(style)
        prefs.disliked_styles = list(disliked)

    def _infer_body_preferences(self, prefs: UserPreferences, feedbacks):
        """从反馈中推断身材偏好"""
        for fb in feedbacks:
            content = fb.feedback_content
            if any(kw in content for kw in ["太长", "显矮", "压个子"]):
                prefs.likely_height = "short"
            if any(kw in content for kw in ["显胖", "显壮", "太紧"]):
                prefs.likely_body_type = "leaning_athletic"
```

---

## 九、主动服务引擎

```python
# app/agent/services/proactive_service.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProactiveService:
    """主动服务引擎"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.notification_manager = None

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

    async def daily_wardrobe_check(self):
        """每日衣橱健康检查"""
        from app.database import SessionLocal
        from app.models import User
        from app.agent.wardrobe_curator import WardrobeCuratorAgent
        from app.agent.protocol import AgentRequest, OutfitContext

        db = SessionLocal()
        try:
            # 获取活跃用户（3天内登录）
            active_users = db.query(User).filter(
                User.last_active_at >= datetime.now() - timedelta(days=3)
            ).all()

            for user in active_users:
                try:
                    curator = WardrobeCuratorAgent(user_id=str(user.id))
                    context = OutfitContext(user_id=str(user.id))

                    request = AgentRequest(
                        task=TaskType.WARDROBE_HEALTH,
                        agent="wardrobe_curator",
                        context=context
                    )

                    response = await curator.handle(request)

                    if response.status == "success" and response.health_report:
                        health = response.health_report
                        # 只推送有问题的
                        if health.get("health_score", 100) < 70:
                            await self._push_notification(
                                user_id=str(user.id),
                                title="👀 您的衣橱需要关注",
                                body=f"衣橱健康度 {health['health_score']}分，"
                                     f"有 {health.get('unused_90_days', 0)} 件衣服超过3个月没穿了",
                                data={"health_score": health["health_score"]}
                            )
                except Exception as e:
                    logger.error(f"Daily check failed for user {user.id}: {e}")
        finally:
            db.close()

    async def weekly_report(self):
        """每周穿搭报告"""
        # 类似 daily_wardrobe_check，但生成更详细的报告
        pass

    async def _push_notification(self, user_id: str, title: str, body: str, data: dict):
        """推送通知"""
        if self.notification_manager:
            await self.notification_manager.push(user_id, title, body, data)
```

---

## 十、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| **核心 Agent** | | |
| `app/agent/protocol.py` | **新增** | Agent 间通信协议（AgentRequest/AgentResponse/OutfitContext） |
| `app/agent/outfit_advisor.py` | **新增** | OutfitAdvisor Agent（真正的 Agent） |
| `app/agent/wardrobe_curator.py` | **新增** | WardrobeCurator Agent（真正的 Agent） |
| `app/agent/supervisor.py` | **重构** | 重写 SupervisorAgent，支持 Agent 间通信 |
| `app/agent/memory.py` | **修改** | 扩展 AgentMemory，新增 current_plan/current_evaluation 字段 |
| **知识库（详见 knowledge-base-and-profile.md）** | | |
| `app/agent/knowledge/__init__.py` | **新增** | 知识库模块入口 |
| `app/agent/knowledge/base.py` | **新增** | FashionKnowledgeBase 统一访问接口 |
| `app/agent/knowledge/styles.py` | **新增** | 风格定义库（15+种风格） |
| `app/agent/knowledge/colors.py` | **新增** | 色彩系统 |
| `app/agent/knowledge/body.py` | **新增** | 身材适配指南（5种身材） |
| `app/agent/knowledge/occasions.py` | **新增** | 场合着装规范 |
| `app/agent/knowledge/seasons.py` | **新增** | 季节穿搭指南 |
| **用户画像** | | |
| `app/models/user_profile.py` | **重构** | 扩展字段（身高/体重/肤色/职业/身材类型等） |
| `app/models/preferences.py` | **新增** | UserPreferences / PreferenceFeedback ORM |
| `app/agent/profile_manager.py` | **新增** | 画像管理器（引导收集/推断/供 Agent 使用） |
| `app/routers/profile.py` | **新增** | 画像相关 API（获取/更新/引导） |
| **服务层** | | |
| `app/agent/tools/care.py` | **新增** | GarmentCare Tool（材质知识库，规则查表） |
| `app/agent/services/preference_learner.py` | **新增** | 偏好学习服务 |
| `app/agent/services/proactive_service.py` | **新增** | 主动服务引擎 |
| `app/routers/chat.py` | **修改** | 集成新 SupervisorAgent，NotificationManager |
| `app/main.py` | **修改** | ProactiveService 启动集成 |
| **数据库** | | |
| `service/schema.sql` | **修改** | 扩展 user_profiles 表，新增 user_preferences / preference_feedbacks 表 |
| `requirements.txt` | **修改** | 新增 apscheduler |

---

## 十一、实施计划

> **前置依赖**：`docs/2026-03-26-knowledge-base-and-profile.md` 中详细描述了知识库和用户画像的设计方案，以下计划引用该文档中的模块定义。

### Phase 1（5-6 周）：核心 Agent 框架

| 任务 | 说明 | 依赖 | 周数 |
|------|------|------|------|
| T1.1 | 实现 Agent 间通信协议（protocol.py） | — | 0.5 周 |
| T1.2 | 实现 OutfitAdvisor Agent（plan_outfit + evaluate） | T1.1 | 1.5 周 |
| T1.3 | 实现 OutfitAdvisor Agent（refine_outfit 多轮迭代） | T1.2 | 1 周 |
| T1.4 | 实现 WardrobeCurator Agent（健康检查） | T1.1 | 1 周 |
| T1.5 | 重构 SupervisorAgent（集成专业 Agent） | T1.2, T1.4 | 1 周 |
| T1.6 | 单元测试 + 集成测试 | T1.5 | 1 周 |

### Phase 2（3-4 周）：偏好学习 + 存储

| 任务 | 说明 | 依赖 | 周数 |
|------|------|------|------|
| T2.1 | 新增数据库表 + ORM（user_preferences / preference_feedbacks） | — | 0.5 周 |
| T2.2 | PreferenceLearner 服务 | T2.1 | 1 周 |
| T2.3 | OutfitAdvisor 偏好应用 | T2.2, T1.3 | 0.5 周 |
| T2.4 | 反馈记录到偏好学习全流程 | T2.3 | 1 周 |

### Phase 3（3-4 周）：知识库 + 用户画像

| 任务 | 说明 | 依赖 | 周数 |
|------|------|------|------|
| T3.1 | FashionKnowledgeBase 框架 + 风格定义库（15+种风格） | — | 0.5 周 |
| T3.2 | 身材适配指南（5种身材）+ 场合规范 | T3.1 | 0.5 周 |
| T3.3 | 色彩系统 + 季节穿搭指南 | T3.1 | 0.5 周 |
| T3.4 | 用户画像数据模型扩展（user_profiles 表 + ORM） | T2.1 | 0.5 周 |
| T3.5 | ProfileManager 画像管理器 + 引导交互 API | T3.4 | 0.5 周 |
| T3.6 | Agent 融合知识库 + 用户画像（OutfitAdvisor 重构） | T3.1, T3.4, T1.3 | 1 周 |

### Phase 4（3-4 周）：深度功能

| 任务 | 说明 | 依赖 | 周数 |
|------|------|------|------|
| T4.1 | WardrobeCurator 参考图风格复刻 | T3.1 | 1 周 |
| T4.2 | GarmentCare Tool（材质知识库） | knowledge-base 文档 | 0.5 周 |
| T4.3 | ProactiveService 主动服务 | T2.2 | 1 周 |
| T4.4 | 推送通知（WebSocket/SSE） | T4.3 | 0.5 周 |

### Phase 5（2 周）：优化收尾

| 任务 | 说明 | 依赖 | 周数 |
|------|------|------|------|
| T5.1 | 性能优化 + 成本优化 | Phase 1-4 | 1 周 |
| T5.2 | E2E 测试 + 文档更新 | T5.1 | 1 周 |

**总工期：16-19 周**

> 注：Phase 3（知识库+画像）可以与 Phase 2（偏好学习）并行推进，因为它们依赖不同模块。

### 文件依赖图

```
T1.1 (protocol.py)
  ├─ T1.2 (OutfitAdvisor base)
  │     └─ T1.3 (多轮迭代)
  ├─ T1.4 (WardrobeCurator)
  └─ T1.5 (Supervisor重构)
        └─ T1.6 (测试)

T2.1 (DB/ORM) ─────────────────────────┐
  ├─ T2.2 (PreferenceLearner)           ├─ T2.3 → T2.4
  └─ T3.4 (用户画像模型)  ──────────────────┼─ T3.5 → T3.6
                                               │
T3.1 (知识库基础) ──┬─ T3.2 ──┬─ T3.3 ──┘
                    └───────────────────────────┘
T4.1 (风格复刻)
T4.2 (GarmentCare)
T4.3 → T4.4 (主动服务 + 推送)
```

---

## 十二、技术风险

| 风险 | 严重程度 | 对策 |
|------|---------|------|
| Agent 推理质量不稳定 | 高 | 积累高质量样本，建立评价机制 |
| 多轮迭代振荡 | 中 | 收敛机制（相似反馈3次强制收敛） |
| Agent 状态跨 session 丢失 | 中 | Supervisor 保存 Agent 状态到 Session |
| APScheduler 多实例重复执行 | 中 | PostgreSQL advisory lock 或单实例 |
| 知识库覆盖不足 | 中 | 分阶段迭代，v1.0 覆盖主流风格 |
| 画像数据冷启动 | 中 | 分阶段引导收集，行为推断补充 |
| LLM 成本超预算 | 低 | 模型分级（Supervisor 用小模型） |

---

## 十三、知识库与用户画像

详见：`docs/2026-03-26-knowledge-base-and-profile.md`

---

*实施方案 v2.0 结束 — 待评审后更新*
