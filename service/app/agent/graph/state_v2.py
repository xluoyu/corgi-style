"""Graph State 定义 v2.0

基于 LangGraph 的状态机状态定义，支持 OutfitAdvisor + WardrobeCurator Agent。
"""
from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict


class Intent(str, Enum):
    """用户意图枚举（v2.0 完整版）"""
    GENERATE_OUTFIT = "generate_outfit"           # 生成穿搭
    QUERY_WARDROBE = "query_wardrobe"             # 查询衣柜
    GIVE_FEEDBACK = "give_feedback"               # 反馈调整
    WARDROBE_CHECK = "wardrobe_check"             # 衣橱健康检查
    STYLE_MATCH = "style_match"                   # 参考图风格复刻
    CARE_GUIDE = "care_guide"                     # 衣物护理
    GET_ADVICE = "get_advice"                    # 获取建议
    UNKNOWN = "unknown"                          # 未知意图


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class OutfitEvaluation:
    """
    穿搭方案评价结构

    对应 PRD v1.0 的方案评价功能：
    - 5 维度评分（色彩/风格/场合/层次/身材适配）
    - pros/cons/suggestions 专业意见
    """
    overall_score: int = 0          # 综合评分 0-100
    color_score: int = 0           # 色彩协调性 0-100
    style_score: int = 0           # 风格一致性 0-100
    scene_score: int = 0          # 场合得体性 0-100
    layering_score: int = 0        # 层次感 0-100
    body_fit_score: int = 0       # 身材适配性 0-100

    pros: List[str] = field(default_factory=list)      # 优点列表
    cons: List[str] = field(default_factory=list)      # 缺点列表
    suggestions: List[str] = field(default_factory=list)  # 改进建议

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutfitEvaluation":
        if data is None:
            return cls()
        return cls(**data)


class GraphState(TypedDict):
    """
    LangGraph 状态机状态定义（v2.0 增强版）

    包含三大模块：
    1. 对话上下文（user_id, session_id, messages）
    2. 意图识别结果（intent, entities）
    3. OutfitAdvisor 状态（advisor_*）
    4. WardrobeCurator 状态（curator_*）
    5. 系统控制（next_node, should_end）
    """

    # === 对话上下文 ===
    user_id: str
    session_id: str
    messages: List[Dict[str, Any]]                 # 对话历史 [{"role": "user", "content": "..."}]

    # === 意图识别结果 ===
    intent: Optional[Intent]
    intent_str: Optional[str]                     # intent 字符串值（持久化用）
    intent_confidence: float                       # 置信度 0-1
    entities: Dict[str, Any]                      # 提取的实体 {"city": "北京", "scene": "work"}

    # === 目标信息 ===
    target_date: Optional[str]                     # 目标日期 "2026-03-25"
    target_city: Optional[str]                    # 目标城市 "北京"
    target_scene: Optional[str]                   # 场景 "work/casual/date/sport/party"
    target_temperature: Optional[float]             # 温度 18.5

    # === 衣物检索 ===
    user_clothes: List[Dict[str, Any]]            # 用户衣柜全部衣物
    filtered_clothes: Dict[str, List[Dict]]       # 按品类过滤后的衣物
    selected_clothes: Dict[str, Optional[Dict]]   # 选中的衣物 {"top": {...}, "pants": {...}}
    wardrobe_stats: Optional[Dict[str, Any]]       # 衣柜统计
    wardrobe_by_category: Dict[str, List[Dict]]   # 按品类分组的衣物
    available_categories: List[str]                # 衣柜中已有的品类
    missing_categories: List[str]                  # 衣柜中缺失的品类

    # === 穿搭方案（OutfitAdvisor 输出）===
    outfit_plan: Optional[Dict[str, Any]]          # 穿搭方案
    outfit_evaluation: Optional[Dict[str, Any]]    # OutfitEvaluation 结构（to_dict）
    match_score: float                            # 匹配分数 0-100
    alternatives: List[Dict[str, Any]]            # 备选方案

    # === OutfitAdvisor 多轮状态 ===
    advisor_iteration_count: int                   # 迭代次数（多轮对话计数）
    advisor_rejected_features: List[str]           # 被用户拒绝的特征（用于避免重复）
    advisor_accepted_features: List[str]           # 被用户接受的特征（用于强化）
    advisor_current_plan: Optional[Dict]             # 当前方案（用于 refine 对比）
    feedback_analysis: Optional[Dict[str, Any]]     # 反馈分析结果

    # === WardrobeCurator 状态 ===
    curator_health_score: Optional[int]            # 衣橱健康度评分 0-100
    curator_unused_items: List[Dict]              # 长期未使用衣物列表
    curator_last_check: Optional[str]             # 上次检查时间 ISO 格式

    # === 参考图风格复刻 ===
    reference_image_url: Optional[str]            # 参考图 URL
    style_analysis_result: Optional[Dict[str, Any]]  # 风格分析结果
    matched_items: List[Dict]                     # 匹配到的衣物列表

    # === 知识库上下文 ===
    knowledge_context: Optional[Dict[str, Any]]   # 风格/色彩/场合知识

    # === 系统控制 ===
    next_node: Optional[str]                      # 下一个节点（调试用）
    error: Optional[str]                          # 错误信息
    should_end: bool                             # 是否结束对话
    response_data: Optional[Dict[str, Any]]       # 响应附加数据
    asking_for: Optional[str]                     # 当前追问的字段："city" / "scene" / None
    pending_intent: Optional[str]                 # 用户未完成的意图
    last_agent: Optional[str]                    # 最后执行的 Agent 名称（v3 多 Agent 用）


def create_initial_state(user_id: str, session_id: str) -> GraphState:
    """创建初始状态"""
    return GraphState(
        user_id=user_id,
        session_id=session_id,
        messages=[],
        intent=None,
        intent_str=None,
        intent_confidence=0.0,
        entities={},
        target_date=None,
        target_city=None,
        target_scene=None,
        target_temperature=None,
        user_clothes=[],
        filtered_clothes={},
        selected_clothes={},
        wardrobe_stats=None,
        wardrobe_by_category={},
        available_categories=[],
        missing_categories=[],
        outfit_plan=None,
        outfit_evaluation=None,
        match_score=0.0,
        alternatives=[],
        advisor_iteration_count=0,
        advisor_rejected_features=[],
        advisor_accepted_features=[],
        advisor_current_plan=None,
        feedback_analysis=None,
        curator_health_score=None,
        curator_unused_items=[],
        curator_last_check=None,
        reference_image_url=None,
        style_analysis_result=None,
        matched_items=[],
        knowledge_context=None,
        next_node=None,
        error=None,
        should_end=False,
        response_data=None,
        asking_for=None,
        pending_intent=None,
        last_agent=None,
    )
