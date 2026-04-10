import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/outfit/refresh
 * 强制刷新今日穿搭
 */

// Mock 穿搭数据
const mockOutfit = {
  description: "春日清新学院风",
  temperature: 22,
  city: "上海",
  scene: "daily",
  image_url: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&h=800&fit=crop",
  outfit_items: [
    { slot: "上装", description: "白色棉质T恤", color: "白色" },
    { slot: "下装", description: "深蓝色直筒牛仔裤", color: "深蓝色" },
    { slot: "外套", description: "灰色针织开衫", color: "灰色" },
    { slot: "鞋子", description: "黑色小皮鞋", color: "黑色" },
  ],
  cached: false,
};

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { city, temperature, scene } = body;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 800));

  return NextResponse.json({
    ...mockOutfit,
    description: "全新春日时尚搭配",
    temperature,
    city,
    scene: scene || "daily",
    cached: false,
  });
}
