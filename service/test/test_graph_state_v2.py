"""GraphState v2 单元测试"""
import pytest
from app.agent.graph.state_v2 import (
    Intent,
    OutfitEvaluation,
    GraphState,
    create_initial_state,
)


class TestIntentEnum:
    """Intent 枚举测试"""

    def test_all_intents_exist(self):
        """验证所有 v2.0 意图类型都存在"""
        assert Intent.GENERATE_OUTFIT.value == "generate_outfit"
        assert Intent.QUERY_WARDROBE.value == "query_wardrobe"
        assert Intent.GIVE_FEEDBACK.value == "give_feedback"
        assert Intent.WARDROBE_CHECK.value == "wardrobe_check"
        assert Intent.STYLE_MATCH.value == "style_match"
        assert Intent.CARE_GUIDE.value == "care_guide"
        assert Intent.GET_ADVICE.value == "get_advice"
        assert Intent.UNKNOWN.value == "unknown"

    def test_intent_from_string(self):
        """验证可以从字符串创建 Intent"""
        assert Intent("generate_outfit") == Intent.GENERATE_OUTFIT
        assert Intent("wardrobe_check") == Intent.WARDROBE_CHECK
        assert Intent("unknown") == Intent.UNKNOWN

    def test_intent_is_string_enum(self):
        """验证 Intent 是字符串枚举（可序列化）"""
        intent = Intent.GENERATE_OUTFIT
        assert isinstance(intent, str)
        assert intent.value == "generate_outfit"


class TestOutfitEvaluation:
    """OutfitEvaluation 数据类测试"""

    def test_default_values(self):
        """验证默认值"""
        eval = OutfitEvaluation()
        assert eval.overall_score == 0
        assert eval.color_score == 0
        assert eval.style_score == 0
        assert eval.scene_score == 0
        assert eval.layering_score == 0
        assert eval.body_fit_score == 0
        assert eval.pros == []
        assert eval.cons == []
        assert eval.suggestions == []

    def test_with_values(self):
        """验证带值的创建"""
        eval = OutfitEvaluation(
            overall_score=85,
            color_score=90,
            style_score=80,
            scene_score=85,
            layering_score=75,
            body_fit_score=80,
            pros=["色彩协调", "场合得体"],
            cons=["层次感略差"],
            suggestions=["可以加一条围巾"]
        )
        assert eval.overall_score == 85
        assert eval.color_score == 90
        assert len(eval.pros) == 2

    def test_to_dict(self):
        """验证序列化为字典"""
        eval = OutfitEvaluation(
            overall_score=85,
            pros=["色彩协调"]
        )
        d = eval.to_dict()
        assert d["overall_score"] == 85
        assert d["pros"] == ["色彩协调"]
        assert isinstance(d, dict)

    def test_from_dict(self):
        """验证从字典创建"""
        data = {
            "overall_score": 85,
            "color_score": 90,
            "style_score": 80,
            "scene_score": 85,
            "layering_score": 75,
            "body_fit_score": 80,
            "pros": ["色彩协调"],
            "cons": [],
            "suggestions": []
        }
        eval = OutfitEvaluation.from_dict(data)
        assert eval.overall_score == 85
        assert eval.pros == ["色彩协调"]

    def test_from_dict_with_none(self):
        """验证 from_dict 处理 None"""
        eval = OutfitEvaluation.from_dict(None)
        assert eval.overall_score == 0
        assert eval.pros == []

    def test_round_trip(self):
        """验证 to_dict → from_dict 往返"""
        original = OutfitEvaluation(
            overall_score=85,
            color_score=90,
            style_score=80,
            scene_score=85,
            layering_score=75,
            body_fit_score=80,
            pros=["色彩协调", "场合得体"],
            cons=["层次感略差"],
            suggestions=["可以加一条围巾"]
        )
        restored = OutfitEvaluation.from_dict(original.to_dict())
        assert restored.overall_score == original.overall_score
        assert restored.pros == original.pros
        assert restored.cons == original.cons


class TestCreateInitialState:
    """create_initial_state 函数测试"""

    def test_creates_required_fields(self):
        """验证创建的状态包含所有必需字段"""
        state = create_initial_state(user_id="user-123", session_id="session-456")

        assert state["user_id"] == "user-123"
        assert state["session_id"] == "session-456"
        assert state["messages"] == []
        assert state["intent"] is None
        assert state["intent_str"] is None
        assert state["entities"] == {}
        assert state["target_city"] is None
        assert state["target_scene"] is None
        assert state["advisor_iteration_count"] == 0
        assert state["advisor_rejected_features"] == []
        assert state["advisor_accepted_features"] == []
        assert state["outfit_plan"] is None
        assert state["outfit_evaluation"] is None
        assert state["match_score"] == 0.0
        assert state["should_end"] is False
        assert state["asking_for"] is None
        assert state["pending_intent"] is None

    def test_v2_fields_present(self):
        """验证 v2.0 新增字段存在"""
        state = create_initial_state(user_id="u1", session_id="s1")

        # GraphState 是 TypedDict，必须包含所有键
        assert "advisor_iteration_count" in state
        assert "advisor_rejected_features" in state
        assert "advisor_accepted_features" in state
        assert "advisor_current_plan" in state
        assert "feedback_analysis" in state
        assert "curator_health_score" in state
        assert "curator_unused_items" in state
        assert "reference_image_url" in state
        assert "style_analysis_result" in state
        assert "matched_items" in state


class TestGraphStateTypedDict:
    """GraphState TypedDict 行为测试"""

    def test_graph_state_is_dict(self):
        """验证 GraphState 本质是 dict"""
        state = create_initial_state(user_id="u1", session_id="s1")
        assert isinstance(state, dict)

    def test_can_add_arbitrary_fields(self):
        """验证可以添加任意字段（TypedDict 不阻止）"""
        state = create_initial_state(user_id="u1", session_id="s1")
        state["custom_field"] = "test"
        assert state["custom_field"] == "test"

    def test_missing_keys_return_none_or_default(self):
        """验证访问不存在的键返回 None"""
        state = create_initial_state(user_id="u1", session_id="s1")
        # 直接访问不存在的键会抛出 KeyError，但 get 方法不会
        assert state.get("nonexistent") is None
        assert state.get("nonexistent", "default") == "default"
