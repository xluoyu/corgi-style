"""Graph State 定义"""
from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum


class Intent(str, Enum):
    """用户意图枚举"""
    GENERATE_OUTFIT = "generate_outfit"           # 生成穿搭
    QUERY_WARDROBE = "query_wardrobe"             # 查询衣柜
    GET_ADVICE = "get_advice"                     # 获取建议
    GIVE_FEEDBACK = "give_feedback"               # 反馈调整
    UNKNOWN = "unknown"                            # 未知意图


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class GraphState(TypedDict):
    """LangGraph 状态机状态定义"""

    # === 对话上下文 ===
    user_id: str
    session_id: str
    messages: List[Dict[str, Any]]                 # 对话历史

    # === 意图识别结果 ===
    intent: Optional[Intent]
    entities: Dict[str, Any]                       # 提取的实体
    intent_str: Optional[str]                          # intent 的字符串值（astream 部分更新时保留）
    intent_confidence: float                       # 置信度

    # === 穿搭规划 ===
    target_date: Optional[str]                     # 目标日期 "2026-03-25"
    target_city: Optional[str]                     # 目标城市 "北京"
    target_scene: Optional[str]                    # 场景 "casual/work/formal/sport/date/party"
    target_temperature: Optional[float]            # 温度 18.5

    # === 衣物检索 ===
    user_clothes: List[Dict[str, Any]]             # 用户衣柜衣物
    filtered_clothes: Dict[str, List[Dict]]        # 按品类过滤后的衣物
    selected_clothes: Dict[str, Optional[Dict]]   # 选中的衣物
    wardrobe_stats: Optional[Dict[str, Any]]       # 衣柜统计（顶层存储，避免 context 嵌套合并问题）
    available_categories: List[str]                # 衣柜中已有的品类
    missing_categories: List[str]                   # 衣柜中缺失的品类
    wardrobe_by_category: Dict[str, List[Dict]]   # 按品类分组的衣物

    # === 穿搭方案 ===
    outfit_plan: Optional[Dict[str, Any]]          # 穿搭方案
    match_score: float                             # 匹配分数
    alternatives: List[Dict[str, Any]]            # 备选方案

    # === 多轮反馈 ===
    feedback_type: Optional[str]                   # "too_formal" / "too_casual" / etc.
    adjustment_history: List[Dict[str, Any]]       # 调整历史

    # === 系统控制 ===
    next_node: Optional[str]                      # 下一个节点
    error: Optional[str]                           # 错误信息
    should_end: bool                              # 是否结束对话
    response_data: Optional[Dict[str, Any]]        # 响应附加数据（不出现在路由条件中）
