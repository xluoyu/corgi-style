"""知识问答工具（KnowledgeTools）单元测试"""
import pytest
import json

from app.agent.tools.knowledge import search_knowledge_base, KNOWLEDGE_FAQ, KNOWLEDGE_TOOLS


class TestKnowledgeToolsRegistration:
    """工具注册完整性"""

    def test_all_tools_present(self):
        names = [t.name for t in KNOWLEDGE_TOOLS]
        assert "search_knowledge_base" in names


class TestKnowledgeFAQ:
    """知识库内容完整性"""

    def test_faq_has_entries(self):
        assert len(KNOWLEDGE_FAQ) >= 10

    def test_faq_structure(self):
        for faq in KNOWLEDGE_FAQ:
            assert "q" in faq
            assert "a" in faq
            assert isinstance(faq["q"], str)
            assert isinstance(faq["a"], str)

    def test_faq_covers_diverse_topics(self):
        questions = [f["q"] for f in KNOWLEDGE_FAQ]
        # 确保涵盖不同主题
        topics = ["春天", "面试", "保养", "夏天", "黑色", "牛仔裤",
                  "正式", "休闲", "约会", "运动"]
        for topic in topics:
            matched = any(topic in q for q in questions)
            assert matched, f"缺少主题: {topic}"


class TestSearchKnowledgeBase:
    """search_knowledge_base 工具"""

    @pytest.mark.asyncio
    async def test_exact_match(self):
        result = await search_knowledge_base.ainvoke({"query": "春天怎么搭配颜色"})
        data = json.loads(result)

        assert data["source"] == "knowledge_base"
        assert data["answer"] is not None
        assert "春季" in data["answer"]

    @pytest.mark.asyncio
    async def test_partial_keyword_match(self):
        # "牛仔裤" 应该匹配"牛仔裤怎么搭配上衣"
        result = await search_knowledge_base.ainvoke({"query": "牛仔裤"})
        data = json.loads(result)

        assert data["answer"] is not None
        assert "牛仔裤" in data["answer"]

    @pytest.mark.asyncio
    async def test_no_match(self):
        # 使用完全不相关的 ASCII 查询，确保无匹配
        result = await search_knowledge_base.ainvoke({
            "query": "abc def 123 xyz nonexistent query xyz789"
        })
        data = json.loads(result)

        # 没有任何 FAQ 包含 ASCII 字符，应该无匹配
        assert data["answer"] is None
        assert data["source"] == "knowledge_base"

    @pytest.mark.asyncio
    async def test_color_match(self):
        result = await search_knowledge_base.ainvoke({"query": "黑色"})
        data = json.loads(result)

        assert data["answer"] is not None
        assert "黑色" in data["answer"]

    @pytest.mark.asyncio
    async def test_multiple_keywords(self):
        # 多个关键词应提高匹配分数
        result = await search_knowledge_base.ainvoke({"query": "正式 场合"})
        data = json.loads(result)

        assert data["answer"] is not None

    @pytest.mark.asyncio
    async def test_error(self):
        # knowledge.py 中没有外部调用，不会抛出异常
        # 但仍测试工具签名正确
        result = await search_knowledge_base.ainvoke({"query": "测试"})
        data = json.loads(result)
        assert "source" in data
