import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/chat/message/v3
 * 非流式对话（v3 多 Agent 架构）
 */

// Mock 穿搭卡片数据
const mockOutfitCard = {
  plan: {
    plan_id: "plan_mock_001",
    description: "这套搭配非常适合春天的日常出行，白色T恤搭配浅色牛仔裤，简约又时尚。",
    items: {
      top: { color: "白色", style: "简约", matched: true, clothes_id: "clothes_001" },
      bottom: { color: "浅蓝色", style: "休闲", matched: true, clothes_id: "clothes_002" },
      outerwear: { color: "米色", style: "韩风", matched: false },
      shoes: { color: "白色", style: "运动", matched: true, clothes_id: "clothes_004" },
    },
    missing_advice: "建议搭配一件浅色系的薄款开衫，早晚温差大时可以御寒。",
    color_harmony: "整体色彩以浅色系为主，清新自然，非常适合春季。",
    scene_appropriateness: "适合日常出行、逛街、朋友聚会等场合。",
    temperature_suitability: "适合20-25度的气温，透气舒适。",
  },
  clothes: {
    top: { id: "clothes_001", category: "top", color: "白色", image_url: "https://picsum.photos/seed/c1/400/600" },
    bottom: { id: "clothes_002", category: "bottom", color: "浅蓝色", image_url: "https://picsum.photos/seed/c2/400/600" },
    shoes: { id: "clothes_004", category: "accessory", color: "白色", image_url: "https://picsum.photos/seed/c4/400/600" },
  },
  match_score: 0.92,
  scene: "daily",
  temperature: 22,
  city: "上海",
};

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { user_id, session_id, message, context } = body;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 1200));

  return NextResponse.json({
    session_id: session_id || `mock_session_v3_${Date.now()}`,
    message: "根据当前的天气情况（22°C，多云），我为您推荐一套春日清新学院风穿搭。这套搭配以白色和浅蓝色为主色调，清新自然，非常适合春季日常出行。",
    contents: [
      { type: "text", content: "根据当前的天气情况（22°C，多云），我为您推荐以下穿搭方案：" },
      { type: "outfit_card", content: mockOutfitCard },
    ],
    data: mockOutfitCard,
    suggestions: [
      { type: "text", text: "这套穿搭适合日常出行" },
      { type: "text", text: "查看我的衣橱" },
      { type: "text", text: "换一套推荐" },
    ],
  });
}
