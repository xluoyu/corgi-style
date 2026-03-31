"""Edges v2 单元测试"""
import pytest
from app.agent.graph.state_v2 import Intent, create_initial_state
from app.agent.graph.edges_v2 import (
    route_by_intent,
    route_generate_outfit,
    route_feedback_iteration,
    route_wardrobe_query,
    should_continue,
    is_terminal_node,
)


class TestRouteByIntent:
    """route_by_intent 路由测试"""

    def _make_state(self, intent=None, **kwargs):
        state = create_initial_state(user_id="u1", session_id="s1")
        if intent:
            state["intent"] = intent
            state["intent_str"] = intent.value if hasattr(intent, "value") else str(intent)
        for k, v in kwargs.items():
            state[k] = v
        return state

    def test_generate_outfit_routes_to_flow(self):
        state = self._make_state(Intent.GENERATE_OUTFIT)
        assert route_by_intent(state) == "generate_outfit_flow"

    def test_query_wardrobe_routes_to_flow(self):
        state = self._make_state(Intent.QUERY_WARDROBE)
        assert route_by_intent(state) == "query_wardrobe_flow"

    def test_give_feedback_routes_to_flow(self):
        state = self._make_state(Intent.GIVE_FEEDBACK)
        assert route_by_intent(state) == "feedback_flow"

    def test_wardrobe_check_routes_to_flow(self):
        state = self._make_state(Intent.WARDROBE_CHECK)
        assert route_by_intent(state) == "wardrobe_check_flow"

    def test_style_match_routes_to_flow(self):
        state = self._make_state(Intent.STYLE_MATCH)
        assert route_by_intent(state) == "style_match_flow"

    def test_care_guide_routes_to_flow(self):
        state = self._make_state(Intent.CARE_GUIDE)
        assert route_by_intent(state) == "care_guide_flow"

    def test_get_advice_routes_to_response(self):
        """get_advice 直接响应，不走子图"""
        state = self._make_state(Intent.GET_ADVICE)
        assert route_by_intent(state) == "response"

    def test_unknown_routes_to_response(self):
        state = self._make_state(Intent.UNKNOWN)
        assert route_by_intent(state) == "response"

    def test_intent_as_string(self):
        """验证字符串形式的 intent 也能正确路由"""
        state = self._make_state()
        state["intent"] = Intent.GENERATE_OUTFIT
        state["intent_str"] = "generate_outfit"
        assert route_by_intent(state) == "generate_outfit_flow"


class TestRouteGenerateOutfit:
    """route_generate_outfit 内部路由测试"""

    def _make_state(self, city=None, scene=None, **kwargs):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["target_city"] = city
        state["target_scene"] = scene
        for k, v in kwargs.items():
            state[k] = v
        return state

    def test_both_city_and_scene_returns_advisor_plan(self):
        """有 city + scene → 进入 advisor_plan"""
        state = self._make_state(city="北京", scene="work")
        assert route_generate_outfit(state) == "advisor_plan"

    def test_only_city_returns_response(self):
        """只有 city → 追问 scene"""
        state = self._make_state(city="北京", scene=None)
        assert route_generate_outfit(state) == "response"

    def test_only_scene_returns_response(self):
        """只有 scene → 追问 city"""
        state = self._make_state(city=None, scene="date")
        assert route_generate_outfit(state) == "response"

    def test_neither_returns_response(self):
        """都没有 → 追问"""
        state = self._make_state(city=None, scene=None)
        assert route_generate_outfit(state) == "response"


class TestRouteFeedbackIteration:
    """route_feedback_iteration 测试（Phase 2）"""

    def _make_state(self, feedback_type=None, iteration_count=0, **kwargs):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["feedback_type"] = feedback_type
        state["advisor_iteration_count"] = iteration_count
        for k, v in kwargs.items():
            state[k] = v
        return state

    def test_accept_feedback_ends(self):
        """feedback_type == accept → 结束"""
        state = self._make_state(feedback_type="accept", iteration_count=1)
        assert route_feedback_iteration(state) == "response"

    def test_max_iterations_ends(self):
        """iteration_count >= 5 → 结束"""
        state = self._make_state(feedback_type="", iteration_count=5)
        assert route_feedback_iteration(state) == "response"

    def test_under_max_iterations_continues(self):
        """iteration_count < 5 且非 accept → 继续迭代"""
        state = self._make_state(feedback_type="too_formal", iteration_count=2)
        assert route_feedback_iteration(state) == "advisor_refine"

    def test_zero_iterations_continues(self):
        """iteration_count == 0 → 继续迭代"""
        state = self._make_state(feedback_type="color_change", iteration_count=0)
        assert route_feedback_iteration(state) == "advisor_refine"


class TestRouteWardrobeQuery:
    """route_wardrobe_query 测试"""

    def _make_state(self, user_clothes=None, wardrobe_stats=None):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["user_clothes"] = user_clothes or []
        state["wardrobe_stats"] = wardrobe_stats
        return state

    def test_with_user_clothes_routes_to_wardrobe_query(self):
        state = self._make_state(user_clothes=[{"id": "1", "name": "衬衫"}])
        assert route_wardrobe_query(state) == "wardrobe_query"

    def test_with_wardrobe_stats_routes_to_wardrobe_query(self):
        state = self._make_state(wardrobe_stats={"total": 10})
        assert route_wardrobe_query(state) == "wardrobe_query"

    def test_empty_wardrobe_routes_to_response(self):
        state = self._make_state(user_clothes=[], wardrobe_stats=None)
        assert route_wardrobe_query(state) == "response"


class TestShouldContinue:
    """should_continue 通用结束判断测试"""

    def test_should_end_true_returns_end(self):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["should_end"] = True
        assert should_continue(state) == "end"

    def test_should_end_false_returns_continue(self):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["should_end"] = False
        assert should_continue(state) == "continue"


class TestIsTerminalNode:
    """is_terminal_node 测试"""

    def test_should_end_true_returns_true(self):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["should_end"] = True
        assert is_terminal_node(state) is True

    def test_should_end_false_returns_false(self):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["should_end"] = False
        assert is_terminal_node(state) is False
