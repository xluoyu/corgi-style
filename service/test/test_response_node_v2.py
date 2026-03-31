"""Response Node v2 增强测试"""
import pytest
from app.agent.graph.state_v2 import create_initial_state, OutfitEvaluation
from app.agent.graph.nodes.response import (
    _SLOT_EMOJI,
    _SLOT_NAMES,
    _handle_wardrobe_health,
    _handle_care_guide,
    _handle_style_match,
)


class TestSlotMappings:
    """品类映射测试"""

    def test_slot_emoji_has_all_categories(self):
        """验证所有 v2.0 品类都有 emoji"""
        expected = ["top", "pants", "outer", "inner", "accessory", "shoes"]
        for cat in expected:
            assert cat in _SLOT_EMOJI, f"Missing emoji for {cat}"
            assert _SLOT_EMOJI[cat]  # 非空

    def test_slot_names_has_all_categories(self):
        """验证所有 v2.0 品类都有中文名"""
        expected = ["top", "pants", "outer", "inner", "accessory", "shoes"]
        for cat in expected:
            assert cat in _SLOT_NAMES, f"Missing name for {cat}"
            assert _SLOT_NAMES[cat]  # 非空

    def test_shoes_emoji(self):
        """验证 shoes 品类有正确的 emoji"""
        assert _SLOT_EMOJI.get("shoes") == "👟"

    def test_inner_emoji_fixed(self):
        """验证 inner 品类 emoji 不是占位符"""
        # inner 从 🩻 改为 👙
        assert _SLOT_EMOJI.get("inner") == "👙"


class TestHandleWardrobeHealth:
    """衣橱健康检查响应测试"""

    def _make_state(self, health_score=None, unused_items=None):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["curator_health_score"] = health_score
        state["curator_unused_items"] = unused_items or []
        return state

    def test_pending_when_no_score(self):
        """无健康分时返回 pending"""
        state = self._make_state(health_score=None)
        response, data = _handle_wardrobe_health(state)
        assert data["status"] == "pending"
        assert "正在" in response

    def test_high_health_score(self):
        """健康度 >= 80"""
        state = self._make_state(health_score=85, unused_items=[])
        response, data = _handle_wardrobe_health(state)
        assert data["health_score"] == 85
        assert "健康" in response

    def test_medium_health_score(self):
        """健康度 60-79"""
        state = self._make_state(health_score=65, unused_items=[])
        response, data = _handle_wardrobe_health(state)
        assert data["health_score"] == 65
        assert "基本健康" in response or "小问题" in response

    def test_low_health_score(self):
        """健康度 40-59"""
        state = self._make_state(health_score=50, unused_items=[])
        response, data = _handle_wardrobe_health(state)
        assert data["health_score"] == 50
        assert "失衡" in response or "注意" in response

    def test_unused_items_display(self):
        """长期未穿衣物显示"""
        state = self._make_state(
            health_score=70,
            unused_items=[
                {"name": "红色衬衫", "days_since_worn": 60},
                {"name": "蓝色T恤", "days_since_worn": 90}
            ]
        )
        response, data = _handle_wardrobe_health(state)
        assert "红色衬衫" in response
        assert "60天" in response
        assert len(data["unused_items"]) == 2

    def test_response_type_is_wardrobe_health(self):
        state = self._make_state(health_score=80)
        _, data = _handle_wardrobe_health(state)
        assert data["type"] == "wardrobe_health"


class TestHandleCareGuide:
    """衣物护理指南响应测试"""

    def test_specific_care_advice_for_fleece(self):
        """羊绒大衣返回正确护理建议"""
        state = create_initial_state(user_id="u1", session_id="s1")
        state["messages"] = [{"role": "user", "content": "羊绒大衣怎么洗"}]
        response, data = _handle_care_guide(state)
        assert "干洗" in response or "羊绒" in response
        assert data["type"] == "care_guide"

    def test_specific_care_advice_for_down_jacket(self):
        """羽绒服返回正确护理建议"""
        state = create_initial_state(user_id="u1", session_id="s1")
        state["messages"] = [{"role": "user", "content": "羽绒服怎么洗"}]
        response, data = _handle_care_guide(state)
        assert "羽绒服" in response or "中性洗涤剂" in response

    def test_generic_advice_when_no_keyword(self):
        """无关键词时返回通用建议"""
        state = create_initial_state(user_id="u1", session_id="s1")
        state["messages"] = [{"role": "user", "content": "这件衣服怎么洗"}]
        response, data = _handle_care_guide(state)
        assert "护理" in response or "洗涤" in response or "衣物" in response
        assert data["type"] == "care_guide"


class TestHandleStyleMatch:
    """参考图风格复刻响应测试"""

    def _make_state(self, style_result=None, matched_items=None):
        state = create_initial_state(user_id="u1", session_id="s1")
        state["style_analysis_result"] = style_result or {}
        state["matched_items"] = matched_items or []
        return state

    def test_pending_when_no_result(self):
        """无风格分析结果时返回 pending"""
        state = self._make_state(style_result=None)
        response, data = _handle_style_match(state)
        assert data["status"] == "pending"
        assert "正在分析" in response

    def test_displays_description_and_score(self):
        """有结果时显示描述和匹配分"""
        state = self._make_state(
            style_result={"description": "美式休闲风格", "replication_score": 78},
            matched_items=[]
        )
        response, data = _handle_style_match(state)
        assert "美式休闲风格" in response
        assert "78" in response

    def test_displays_matched_items(self):
        """显示匹配到的单品（最多3个）"""
        state = self._make_state(
            style_result={"description": "简约风格", "replication_score": 85},
            matched_items=[
                {"name": "白色T恤"},
                {"name": "牛仔裤"},
                {"name": "运动鞋"}
            ]
        )
        response, data = _handle_style_match(state)
        assert "白色T恤" in response
        assert "牛仔裤" in response
        # 正好3个时，全部显示
        assert "运动鞋" in response
        
    def test_displays_at_most_3_items(self):
        """超过3个单品时，只显示前3个"""
        state = self._make_state(
            style_result={"description": "简约风格", "replication_score": 85},
            matched_items=[
                {"name": "白色T恤"},
                {"name": "牛仔裤"},
                {"name": "运动鞋"},
                {"name": "帽子"},  # 第4个，不应该显示
            ]
        )
        response, data = _handle_style_match(state)
        assert "白色T恤" in response
        assert "牛仔裤" in response
        assert "运动鞋" in response
        assert "帽子" not in response

    def test_response_type_is_style_match(self):
        state = self._make_state(
            style_result={"description": "街头风格", "replication_score": 75}
        )
        _, data = _handle_style_match(state)
        assert data["type"] == "style_match"


class TestHandleGenerateOutfitEvaluation:
    """_handle_generate_outfit 中 v2.0 评价展示测试"""

    def test_evaluation_scores_displayed(self):
        """OutfitEvaluation 各维度评分被展示"""
        from app.agent.graph.nodes.response import _handle_generate_outfit

        state = create_initial_state(user_id="u1", session_id="s1")
        state["outfit_plan"] = {
            "description": "测试方案",
            "items": {}
        }
        state["selected_clothes"] = {}
        state["missing_categories"] = []
        state["match_score"] = 85
        state["outfit_evaluation"] = {
            "overall_score": 85,
            "color_score": 90,
            "style_score": 80,
            "scene_score": 85,
            "layering_score": 75,
            "body_fit_score": 80,
            "pros": ["色彩协调", "场合得体"],
            "cons": ["层次感略差"],
            "suggestions": ["可以加一条围巾"]
        }

        response, data = _handle_generate_outfit(state)

        # 验证评分被包含
        assert "90" in response  # color_score
        assert "80" in response  # style_score
        assert "85" in response  # overall_score 或 scene_score
        # 验证 pros/cons/suggestions
        assert "色彩协调" in response
        assert "场合得体" in response
        assert "层次感略差" in response

    def test_evaluation_in_response_data(self):
        """evaluation 被包含在 response_data 中"""
        from app.agent.graph.nodes.response import _handle_generate_outfit

        state = create_initial_state(user_id="u1", session_id="s1")
        state["outfit_plan"] = {"description": "测试", "items": {}}
        state["selected_clothes"] = {}
        state["missing_categories"] = []
        state["match_score"] = 80
        state["outfit_evaluation"] = {
            "overall_score": 80,
            "color_score": 85,
            "style_score": 80,
            "scene_score": 80,
            "layering_score": 75,
            "body_fit_score": 80,
            "pros": [],
            "cons": [],
            "suggestions": []
        }

        _, data = _handle_generate_outfit(state)

        assert data["evaluation"] is not None
        assert data["evaluation"]["overall_score"] == 80
