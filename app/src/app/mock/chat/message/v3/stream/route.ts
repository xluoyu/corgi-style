import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/chat/message/v3/stream
 * 流式对话（v3 多 Agent 架构）
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

  const sessionId = session_id || `mock_session_v3_${Date.now()}`;

  // 创建 SSE 流
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const mockEvents = [
        { event: "thinking", data: { node: "supervisor", text: "正在分析您的请求..." } },
        { event: "routing_decision", data: { agent: "outfit_advisor", params: { scene: "daily", temperature: 22 } } },
        { event: "agent_started", data: { agent: "outfit_advisor" } },
        { event: "thinking", data: { node: "outfit_advisor", text: "正在为您生成穿搭方案..." } },
        { event: "text", data: "根据当前的天气情况（22°C，多云），我为您推荐以下穿搭方案：" },
        { event: "outfit_card", data: mockOutfitCard },
        { event: "suggestions", data: [
          { type: "text", text: "这套穿搭适合日常出行" },
          { type: "text", text: "查看更多推荐" },
        ]},
        { event: "agent_finished", data: { agent: "outfit_advisor", result: { success: true } } },
        { event: "done", data: { session_id: sessionId } },
      ];

      for (let i = 0; i < mockEvents.length; i++) {
        const { event, data } = mockEvents[i];
        await new Promise((resolve) => setTimeout(resolve, 300));
        const line = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
        controller.enqueue(encoder.encode(line));
      }

      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
