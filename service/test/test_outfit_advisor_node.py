"""OutfitAdvisor 节点单元测试"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.agent.graph.state_v2 import create_initial_state, OutfitEvaluation
from app.agent.graph.nodes.outfit_advisor import (
    _get_preferences,
    _build_wardrobe_text,
    _build_preferences_text,
    _parse_plan,
    _parse_evaluation,
    _generate_reasoning,
)


class TestGetPreferences:
    """_get_preferences 测试（Phase 1 空实现）"""

    def test_returns_empty_preferences(self):
        """Phase 1 返回空偏好"""
        prefs = _get_preferences("user-123")
        assert prefs["liked_colors"] == []
        assert prefs["disliked_colors"] == []
        assert prefs["liked_styles"] == []
        assert prefs["disliked_styles"] == []
        assert prefs["likely_height"] is None
        assert prefs["likely_body_type"] is None


class TestBuildWardrobeText:
    """_build_wardrobe_text 测试"""

    def test_empty_wardrobe(self):
        text = _build_wardrobe_text({})
        assert "衣柜为空" in text

    def test_single_category(self):
        wardrobe = {
            "top": [
                {"color": "白色", "description": "棉质T恤"},
                {"color": "蓝色", "name": "牛仔衬衫"}
            ]
        }
        text = _build_wardrobe_text(wardrobe)
        assert "上衣" in text
        assert "共 2 件" in text
        assert "白色" in text
        assert "棉质T恤" in text

    def test_limits_to_5_items_per_category(self):
        wardrobe = {
            "top": [
                {"color": f"颜色{i}", "description": f"衣服{i}"}
                for i in range(8)
            ]
        }
        text = _build_wardrobe_text(wardrobe)
        # 应该只包含前5件
        assert "颜色0" in text
        assert "颜色4" in text
        assert "颜色5" not in text  # 第6件不应该出现

    def test_handles_name_vs_description(self):
        """验证优先使用 description，fallback 到 name"""
        wardrobe = {
            "pants": [
                {"description": "卡其裤", "name": "pants_1"},  # 有 description
                {"name": "黑色休闲裤"}  # 只有 name
            ]
        }
        text = _build_wardrobe_text(wardrobe)
        assert "卡其裤" in text
        assert "黑色休闲裤" in text


class TestBuildPreferencesText:
    """_build_preferences_text 测试"""

    def test_empty_preferences(self):
        text = _build_preferences_text({})
        assert "暂无偏好数据" in text

    def test_liked_colors(self):
        prefs = {"liked_colors": ["蓝色", "白色"]}
        text = _build_preferences_text(prefs)
        assert "喜欢的颜色" in text
        assert "蓝色" in text
        assert "白色" in text

    def test_disliked_colors(self):
        prefs = {"disliked_colors": ["红色"]}
        text = _build_preferences_text(prefs)
        assert "不喜欢的颜色" in text
        assert "红色" in text

    def test_liked_styles(self):
        prefs = {"liked_styles": ["简约", "休闲"]}
        text = _build_preferences_text(prefs)
        assert "喜欢的风格" in text
        assert "简约" in text

    def test_likely_height(self):
        prefs = {"likely_height": "175cm"}
        text = _build_preferences_text(prefs)
        assert "可能身材" in text
        assert "175cm" in text


class TestParsePlan:
    """_parse_plan JSON 解析测试"""

    def test_valid_plan(self):
        content = '''
        {
          "description": "测试方案",
          "overall_concept": "简约风格",
          "outfits": [
            {"slot": "top", "name": "白T恤", "color": "白色", "reason": "基础款"}
          ],
          "color_scheme": "黑白灰",
          "match_score": 85
        }
        '''
        plan = _parse_plan(content)
        assert plan is not None
        assert plan["description"] == "测试方案"
        assert len(plan["outfits"]) == 1

    def test_plan_without_outfits(self):
        """没有 outfits 字段返回 None"""
        content = '{"description": "无 outfits"}'
        assert _parse_plan(content) is None

    def test_invalid_json(self):
        """无效 JSON 返回 None"""
        assert _parse_plan("not json at all") is None
        assert _parse_plan("{ broken json") is None

    def test_extracts_from_middle_of_text(self):
        """从文本中间提取 JSON"""
        content = "some text before\n{\"description\": \"test\", \"outfits\": []}\nmore text after"
        plan = _parse_plan(content)
        assert plan is not None
        assert plan["description"] == "test"


class TestParseEvaluation:
    """_parse_evaluation JSON 解析测试"""

    def test_valid_evaluation(self):
        content = '''
        {
          "overall_score": 85,
          "color_score": 90,
          "style_score": 80,
          "scene_score": 85,
          "layering_score": 75,
          "body_fit_score": 80,
          "pros": ["色彩协调"],
          "cons": ["层次感略差"],
          "suggestions": ["加围巾"]
        }
        '''
        evaluation = _parse_evaluation(content)
        assert evaluation is not None
        assert evaluation.overall_score == 85
        assert evaluation.color_score == 90
        assert "色彩协调" in evaluation.pros

    def test_invalid_evaluation(self):
        assert _parse_evaluation("not json") is None
        # {} 是有效 JSON，OutfitEvaluation 有默认值，所以会成功解析
        result = _parse_evaluation("{}")
        assert result is not None
        assert result.overall_score == 0  # 默认值

    def test_partial_evaluation(self):
        """部分字段也能解析"""
        content = '{"overall_score": 80}'
        evaluation = _parse_evaluation(content)
        assert evaluation is not None
        assert evaluation.overall_score == 80


class TestGenerateReasoning:
    """_generate_reasoning 推理文本生成测试"""

    def _make_state(self, **kwargs):
        state = create_initial_state(user_id="u1", session_id="s1")
        for k, v in kwargs.items():
            state[k] = v
        return state

    def test_cold_temperature(self):
        """低温生成保暖推理"""
        state = self._make_state(target_temperature=5, target_scene="daily")
        plan = {"outfits": [{"slot": "top", "color": "毛衣"}]}
        reasoning = _generate_reasoning(plan, state, None)
        assert "5" in reasoning or "保暖" in reasoning

    def test_hot_temperature(self):
        """高温生成透气推理"""
        state = self._make_state(target_temperature=30, target_scene="casual")
        plan = {"outfits": [{"slot": "top", "color": "白T恤"}]}
        reasoning = _generate_reasoning(plan, state, None)
        assert "30" in reasoning or "透气" in reasoning or "轻薄" in reasoning

    def test_scene_mapping(self):
        """各场景有对应描述"""
        scene_expectations = {
            "work": "上班",
            "date": "约会",
            "daily": "日常",
            "party": "聚会",
            "sport": "运动",
            "casual": "休闲"
        }
        plan = {"outfits": []}
        for scene, expected_word in scene_expectations.items():
            state = self._make_state(target_scene=scene)
            reasoning = _generate_reasoning(plan, state, None)
            assert expected_word in reasoning, f"场景 {scene} 缺少 {expected_word}"

    def test_color_extraction(self):
        """从 outfits 提取颜色"""
        state = self._make_state(target_scene="casual")
        plan = {
            "outfits": [
                {"slot": "top", "color": "白色"},
                {"slot": "pants", "color": "深蓝"}
            ]
        }
        reasoning = _generate_reasoning(plan, state, None)
        assert "白色" in reasoning
        assert "深蓝" in reasoning

    def test_empty_plan(self):
        """空方案返回默认文本"""
        state = self._make_state()
        reasoning = _generate_reasoning({}, state, None)
        assert reasoning  # 非空

    def test_max_3_colors(self):
        """最多显示3个颜色（set去重后取前3）"""
        state = self._make_state()
        plan = {
            "outfits": [
                {"slot": "top", "color": "红"},
                {"slot": "pants", "color": "蓝"},
                {"slot": "outer", "color": "绿"},
                {"slot": "shoes", "color": "黑"}
            ]
        }
        reasoning = _generate_reasoning(plan, state, None)
        # 由于使用 set 去重，顺序不确定，但最多显示3个颜色
        color_count = len([c for c in ["红", "蓝", "绿", "黑"] if c in reasoning])
        assert color_count <= 3, f"Expected <=3 colors, got {color_count}: {reasoning}"

class TestAdvisorPlanNodeRequiresDb:
    """验证 advisor_plan_node 接受 db 参数"""

    def test_advisor_plan_node_signature(self):
        import inspect
        from app.agent.graph.nodes.outfit_advisor import advisor_plan_node
        sig = inspect.signature(advisor_plan_node)
        params = list(sig.parameters.keys())
        assert "state" in params
        assert "db" in params

    def test_advisor_evaluate_node_signature(self):
        import inspect
        from app.agent.graph.nodes.outfit_advisor import advisor_evaluate_node
        sig = inspect.signature(advisor_evaluate_node)
        params = list(sig.parameters.keys())
        assert "state" in params
        assert "db" in params
