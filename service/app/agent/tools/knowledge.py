"""知识问答工具（KnowledgeTools）。

使用 @tool 装饰器（langchain_core.tools），每个 Tool 内部通过
get_db_for_tools() / get_current_user_id() 获取 DB 和用户。
"""
import json

from langchain_core.tools import tool


# ============================================================
# 知识库（简化版 FAQ，无需向量数据库）
# ============================================================

KNOWLEDGE_FAQ = [
    {"q": "春天怎么搭配颜色", "a": "春季适合柔和的粉色、浅蓝、米色。建议选择可叠穿的搭配，外套选中性色。"},
    {"q": "面试穿什么合适", "a": "建议深色西装或简约商务装。男生：白衬衫+深色西装+领带；女生：衬衫+西裤或及膝裙。"},
    {"q": "如何保养羊毛衫", "a": "建议手洗，水温不超过30℃。平铺晾干，避免悬挂变形。可用羊毛专用洗涤剂。"},
    {"q": "夏天穿什么凉快", "a": "选择透气面料如棉、麻、竹纤维。浅色系更防晒。建议穿宽松款式促进空气流通。"},
    {"q": "黑色衣服怎么搭配", "a": "黑色是百搭色。可搭配白色、灰色营造简约感，或搭配亮色单品提亮整体造型。"},
    {"q": "牛仔裤怎么搭配上衣", "a": "牛仔裤非常百搭。白T恤、衬衫、针织衫都可以。深色牛仔裤搭配浅色上衣，浅色牛仔裤搭配深色上衣更协调。"},
    {"q": "正式场合穿什么", "a": "正式场合建议选择深色西装（黑、深蓝、炭灰），搭配白衬衫和领带。女生可选择礼服或职业套装。"},
    {"q": "休闲场合穿什么", "a": "休闲场合以舒适为主。可以选择T恤、卫衣、牛仔裤、休闲裤。颜色可以更活泼，搭配帆布鞋或运动鞋。"},
    {"q": "约会穿什么", "a": "约会穿搭建议整洁有型但不过于正式。男生可以白衬衫+休闲裤；女生可以选择连衣裙或精致上衣+半身裙。"},
    {"q": "运动穿什么", "a": "运动时选择透气、排汗的功能性衣物。上衣穿运动T恤或卫衣，下装穿运动裤或短裤，鞋子选择专业的运动鞋。"},
]


# ============================================================
# 工具实现
# ============================================================

@tool
async def search_knowledge_base(query: str) -> str:
    """穿搭知识问答（简化版，无向量数据库）。
    当用户询问穿搭技巧、衣物保养、颜色搭配等问题时使用。"""
    try:
        # 简单关键词匹配
        best_match = None
        best_score = 0
        for faq in KNOWLEDGE_FAQ:
            score = sum(1 for kw in query if kw in faq["q"])
            if score > best_score:
                best_score = score
                best_match = faq

        if best_match and best_score > 0:
            return json.dumps({"answer": best_match["a"], "source": "knowledge_base"})
        return json.dumps({"answer": None, "source": "knowledge_base"})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


# ============================================================
# 工具列表（供 SupervisorAgent 注册）
# ============================================================

KNOWLEDGE_TOOLS = [
    search_knowledge_base,
]
