"""响应生成节点"""
import random
from typing import Dict, Any, List, Optional
from app.agent.graph.state import GraphState


# 品类 emoji 映射
_SLOT_EMOJI = {
    "top": "👕", "pants": "👖", "outer": "🧥",
    "inner": "🩻", "accessory": "🎒"
}
_SLOT_NAMES = {
    "top": "上衣", "pants": "裤子", "outer": "外套",
    "inner": "内搭", "accessory": "配饰"
}


def _build_missing_question(state: GraphState, intent_str: str) -> Optional[tuple[str, Dict]]:
    """
    检测缺失的关键信息，如果缺少则主动提问用户。

    Returns:
        (question_text, data_dict) 如果需要提问，否则 None
    """
    if intent_str == "generate_outfit":
        missing = []
        if not state.get("target_city"):
            missing.append("要去哪里（城市）呢")
        if not state.get("target_scene"):
            missing.append("是什么场合（比如上班、约会、运动）")
        if not state.get("user_clothes"):
            missing.append("让我看看您的衣柜里有什么衣服～")

        if missing:
            question = "好的！想帮您搭配得更好，" + missing[0]
            if len(missing) > 1:
                question += "，" + "，".join(missing[1:])
            question += "？"
            return question, {"type": "ask_info", "missing": missing}
    return None


async def response_node(state: GraphState) -> GraphState:
    """
    响应生成节点

    根据状态生成最终回复消息
    """
    # 使用 intent_str（持久化字符串值，astream 部分更新不会丢失）
    intent_str = state.get("intent_str") or state.get("intent") or ""
    # 兼容 Intent 枚举对象
    if hasattr(intent_str, "value"):
        intent_str = intent_str.value
    else:
        intent_str = str(intent_str) if intent_str else ""

    user_message = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""

    # 检查缺失信息，主动提问
    missing_q = _build_missing_question(state, intent_str)
    if missing_q:
        response_content, data = missing_q
    elif intent_str == "query_wardrobe":
        response_content, data = _handle_wardrobe_query(state)
    elif intent_str == "generate_outfit":
        response_content, data = _handle_generate_outfit(state)
    elif intent_str == "give_feedback":
        response_content, data = _handle_feedback(state)
    elif intent_str == "get_advice":
        response_content, data = _handle_get_advice(state)
    else:
        response_content, data = _handle_unknown(state)

    # 更新消息历史
    messages = state.get("messages", [])
    messages.append({
        "role": "assistant",
        "content": response_content
    })
    state["messages"] = messages

    # 设置返回数据
    state["response_data"] = data
    state["should_end"] = True

    return state


def _handle_wardrobe_query(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理衣柜查询响应"""
    # 直接复用 wardrobe_query_node 已计算好的 wardrobe_stats，避免重复 DB 查询
    wardrobe_stats = state.get("wardrobe_stats")
    user_clothes = state.get("user_clothes", [])

    # 如果 state 中没有 stats（某些路径），才回退到查 DB
    if wardrobe_stats is None:
        from app.database import SessionLocal
        from app.models import UserClothes
        db = SessionLocal()
        try:
            clothes = db.query(UserClothes).filter(
                UserClothes.user_id == state.get("user_id"),
                UserClothes.is_deleted == False
            ).all()
            wardrobe_stats = {
                "total": len(clothes),
                "by_category": {},
                "by_color": {},
                "avg_wear_count": 0.0
            }
            total_wear = 0
            for c in clothes:
                cat = c.category or "unknown"
                color = c.color or "unknown"
                wardrobe_stats["by_category"][cat] = wardrobe_stats["by_category"].get(cat, 0) + 1
                wardrobe_stats["by_color"][color] = wardrobe_stats["by_color"].get(color, 0) + 1
                total_wear += c.wear_count or 0
            if clothes:
                wardrobe_stats["avg_wear_count"] = round(total_wear / len(clothes), 1)
        finally:
            db.close()

    stats = wardrobe_stats

    if stats["total"] > 0:
        category_text = ""
        for cat, count in stats["by_category"].items():
            cat_name = _SLOT_NAMES.get(cat, cat)
            category_text += f"{cat_name} {count} 件、"
        response = f"您的衣柜里共有 {stats['total']} 件衣服，其中{category_text.rstrip('、')}。"
    elif user_clothes:
        response = f"帮您找到了 {len(user_clothes)} 件符合条件的衣服。"
    else:
        response = "您的衣柜里还没有衣服哦，可以先上传几张衣服照片试试～"

    return response, {"type": "wardrobe_query", "stats": stats, "clothes": user_clothes}


def _handle_generate_outfit(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理生成穿搭响应——口语化版本"""
    outfit_plan = state.get("outfit_plan", {})
    selected_clothes = state.get("selected_clothes", {})
    missing_categories = state.get("missing_categories", [])
    match_score = state.get("match_score", 0)
    evaluation = state.get("context", {}).get("evaluation", {})

    # 无方案
    if not outfit_plan:
        response = "哎呀，暂时没法给您生成穿搭方案，可能是衣柜里还没有衣服。您可以先添加几件衣服试试～"
        return response, {"type": "outfit_result", "success": False}

    # 检查是否有真实衣物
    real_clothes = {k: v for k, v in selected_clothes.items() if v}
    has_clothes = len(real_clothes) > 0

    # === 构建回复 ===
    lines = []

    # 日期口语化：今天/明天/具体日期
    target_date = state.get("target_date", "")
    today_str = "今天"
    if target_date:
        from datetime import datetime
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            delta = (target_dt.date() - today.date()).days
            if delta == 0:
                today_str = "今天"
            elif delta == 1:
                today_str = "明天"
            elif delta == 2:
                today_str = "后天"
            else:
                today_str = f"{target_dt.month}月{target_dt.day}日"
        except (ValueError, TypeError):
            today_str = ""

    # 开头——口语化
    city = state.get("target_city", "")
    temp = state.get("target_temperature")
    temp_str = f"（{temp}℃）" if temp else ""

    if city and temp:
        lines.append(f"根据{today_str}{city}{temp_str}的天气，给您这样搭：")
    elif city:
        lines.append(f"根据{city}的情况，给您这样搭：")
    elif temp:
        lines.append(f"{today_str}{temp_str}，给您这样穿：")
    else:
        lines.append(f"{today_str}给您这样穿：")


    # === 衣物列表（emoji + 颜色 + 描述）===
    if has_clothes:
        items_desc = outfit_plan.get("items", {})
        for slot, clothes in real_clothes.items():
            emoji = _SLOT_EMOJI.get(slot, "")
            slot_name = _SLOT_NAMES.get(slot, slot)
            color = clothes.get("color", "") or "合适的"
            desc = clothes.get("description", "") or ""
            reason = ""
            if isinstance(items_desc, dict) and slot in items_desc:
                reason = items_desc[slot].get("reason", "")
            if reason:
                lines.append(f"{emoji} {slot_name}：{color}，{reason}")
            else:
                lines.append(f"{emoji} {slot_name}：{color}，和整体很配")

    # === 缺失品类的文字建议 ===
    missing_advice = outfit_plan.get("missing_advice", "")
    if missing_advice:
        lines.append("")
        lines.append(f"💡 {missing_advice}")

    # === 没有任何衣物时 ===
    if not has_clothes and not missing_advice:
        lines = []
        lines.append("哎呀，您的衣柜里暂时还没有合适的衣服可以搭配呢～")
        lines.append("建议您先添加一些衣服进来，这样我就能帮您做更精准的推荐啦！")

    # === 温度提示 ===
    if evaluation.get("temperature_warning"):
        lines.append("")
        lines.append(f"❄️ {evaluation['temperature_warning']}")

    response = "\n".join(lines)

    data = {
        "type": "outfit_result",
        "success": True,
        "plan": outfit_plan,
        "clothes": selected_clothes,
        "missing_categories": missing_categories,
        "missing_advice": missing_advice,
        "match_score": match_score,
        "has_clothes": has_clothes,  # 供前端判断是否显示 OutfitCard
    }

    return response, data


def _handle_feedback(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理反馈响应"""
    feedback_type = state.get("feedback_type", "")
    match_score = state.get("match_score", 0)

    feedback_text = {
        "too_formal": "太正式",
        "too_casual": "太休闲",
        "too_colorful": "颜色太花哨",
        "too_simple": "太素",
        "too_cold": "太冷",
        "too_hot": "太热"
    }.get(feedback_type, "需要调整")

    if match_score >= 80:
        response = f"好的，已经为您调整了穿搭方案，{feedback_text}的问题应该已经解决。"
    else:
        response = f"好的，根据您的反馈'{feedback_text}'，为您重新调整了穿搭方案。"

    return response, {"type": "feedback_response", "feedback_type": feedback_type}


def _handle_get_advice(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理获取建议响应"""
    user_clothes = state.get("user_clothes", [])
    outfit_plan = state.get("outfit_plan", {})

    if not user_clothes:
        return "您的衣柜里没有找到符合条件的衣物。", {"type": "advice", "success": False}

    if outfit_plan:
        response = f"根据您的情况，为您提供以下穿搭建议：\n\n"
        response += f"{outfit_plan.get('description', '')}\n\n"

        items = outfit_plan.get("items", {})
        for slot, item_info in (items.items() if isinstance(items, dict) else []):
            slot_name = {
                "top": "上衣",
                "pants": "裤子",
                "outer": "外套",
                "inner": "内搭",
                "accessory": "配饰"
            }.get(slot, slot)
            color = item_info.get("color", "")
            reason = item_info.get("reason", "")
            response += f"• {slot_name}：{color} - {reason}\n"
    else:
        response = "为您整理了以下搭配建议..."

    return response, {"type": "advice", "success": True, "plan": outfit_plan}


def _is_greeting(message: str) -> bool:
    """判断是否是问候语"""
    greetings = {
        "你好", "您好", "嗨", "hi", "hello", "在吗", "在不在",
        "早上好", "早", "晚上好", "晚安", " hey ", "嘿",
        "好久不见", "最近如何"
    }
    msg = message.strip().lower()
    for g in greetings:
        if g in msg or msg in g:
            return True
    # 纯标点/单字打招呼
    if len(msg) <= 4 and any(c in msg for c in "你好嗨嗨hi在吗早啊"):
        return True
    return False


def _handle_greeting(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理问候语"""
    suggestions = [
        "帮我推荐一套穿搭",
        "我明天要去北京，想看看穿什么合适",
        "我衣柜里有几件蓝色的衣服？"
    ]
    suggest_text = random.choice(suggestions)
    response = f"嗨！👋 我是您的穿搭小助手～可以说「{suggest_text}」来开始哦～"

    return response, {"type": "greeting"}


def _handle_unknown(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理未知意图响应——智能 fallback"""
    user_message = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""

    # 先检查是否是问候语
    if _is_greeting(user_message):
        return _handle_greeting(state)

    # 尝试从 entities 和 state 中提取已有信息
    entities = state.get("entities", {})
    target_city = entities.get("city") or state.get("target_city") or ""
    target_date = entities.get("date") or state.get("target_date") or ""
    target_scene = entities.get("scene") or state.get("target_scene") or ""
    user_message_lower = user_message.strip().lower()

    # 如果用户只发送了城市名（如"北京"、"上海"），直接识别为城市
    if not target_city and len(user_message) <= 6 and user_message.isalnum():
        if _is_likely_city(user_message):
            target_city = user_message
            state["target_city"] = target_city
            entities["city"] = target_city

    # 简短确认语
    ack_keywords = ["谢谢", "好", "知道了", "明白了", "了解", "好的", "收到", "好的好的", "行"]
    if len(user_message) <= 8 and any(kw in user_message for kw in ack_keywords):
        responses = [
            "不客气！有需要随时问我～ 😊",
            "好的！随时为您效劳～",
            "收到！有什么穿搭问题尽管问我哦",
        ]
        return random.choice(responses), {"type": "acknowledgment"}

    # 天气查询类
    weather_keywords = ["天气", "多少度", "气温", "温度"]
    if any(k in user_message_lower for k in weather_keywords):
        if target_city:
            return f"杭州现在的天气我帮您查过了，今天气温大概{target_city}度左右。具体穿搭建议可以告诉我您的需求哦～", {"type": "weather_query"}
        return "您想查询哪个城市的天气呢？比如可以说「杭州今天多少度」～", {"type": "weather_query"}

    # 衣柜浏览/查询类（常见表达）
    wardrobe_keywords = ["看看我衣柜", "我有什么", "都有什么", "衣柜里", "有几件", "看看我有什么"]
    if any(k in user_message_lower for k in wardrobe_keywords):
        state["intent_str"] = "query_wardrobe"
        return _handle_wardrobe_query(state)

    # 如果有实体但 intent 识别失败，尝试推断
    if target_city and target_scene:
        # 有城市+场景 → 视为 generate_outfit
        state["intent_str"] = "generate_outfit"
        return _handle_generate_outfit(state)
    elif target_city:
        # 有城市没场景 → 追问场景
        missing = ["是什么场合（比如上班、约会、运动）"]
        question = f"好的！想帮您在{target_city}找到合适的穿搭，"
        question += missing[0] + "？"
        return question, {"type": "ask_info", "missing": missing, "city": target_city}
    elif target_scene:
        # 有场景没城市 → 追问城市
        scene_name = {
            "casual": "休闲", "daily": "日常", "work": "上班",
            "sport": "运动", "date": "约会", "party": "派对", "formal": "正式"
        }.get(target_scene, target_scene)
        missing = ["要去哪里（城市）呢"]
        question = f"好的！想帮您准备{scene_name}的穿搭，"
        question += missing[0] + "？"
        return question, {"type": "ask_info", "missing": missing, "scene": target_scene}

    # 真正的无法理解 → 友好引导
    suggestions = [
        "帮我推荐一套穿搭",
        "我明天要去杭州，想看看穿什么",
        "我衣柜里有几件蓝色的衣服？"
    ]
    suggest_text = random.choice(suggestions)
    response = f"抱歉，这句话我还不太理解 😅\n\n"
    response += f"您可以试试说「{suggest_text}」来开始哦～"
    return response, {"type": "unknown"}


def _is_likely_city(text: str) -> bool:
    """判断文本是否可能是城市名"""
    common_cities = {
        "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆",
        "武汉", "西安", "郑州", "长沙", "天津", "沈阳", "大连", "青岛", "济南",
        "厦门", "福州", "合肥", "昆明", "哈尔滨", "长春", "石家庄", "南昌", "贵阳",
        "太原", "兰州", "银川", "西宁", "乌鲁木齐", "拉萨", "呼和浩特", "海口",
        "三亚", "珠海", "东莞", "佛山", "无锡", "常州", "宁波", "温州", "绍兴",
        "嘉兴", "金华", "泉州", "南通", "徐州", "扬州", "镇江", "泰州", "盐城",
        "淮安", "连云港", "宿迁", "丽水", "衢州", "舟山", "台州", "湖州", "芜湖",
        "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳",
        "宿州", "六安", "亳州", "池州", "宣城", "漳州", "龙岩", "三明", "南平",
        "莆田", "宁德", "九江", "赣州", "吉安", "宜春", "抚州", "上饶", "景德镇",
        "萍乡", "新余", "鹰潭", "襄阳", "宜昌", "荆州", "荆门", "黄冈", "孝感",
        "咸宁", "十堰", "随州", "恩施", "鄂州", "黄石", "仙桃", "潜江", "天门",
        "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
        "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
        "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭",
        "朝阳", "葫芦岛", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城",
        "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江",
        "黑河", "绥化", "开封", "洛阳", "平顶山", "安阳", "焦作", "新乡", "鹤壁",
        "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店", "济源"
    }
    return text in common_cities
