import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/clothes/list
 * 获取衣物列表
 */

// Mock 衣物数据
const mockClothes = [
  {
    id: "clothes_001",
    user_id: "mock_user_001",
    image_url: "https://picsum.photos/seed/clothes1/400/600",
    name: "白色棉质T恤",
    category: "top",
    color: "白色",
    material: "纯棉",
    temperature_range: "summer",
    scene: "daily",
    analysis_completed: 1,
    generated_completed: 1,
    wear_count: 5,
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "clothes_002",
    user_id: "mock_user_001",
    image_url: "https://picsum.photos/seed/clothes2/400/600",
    name: "深蓝色牛仔裤",
    category: "bottom",
    color: "深蓝色",
    material: "牛仔布",
    temperature_range: "all_season",
    scene: "daily",
    analysis_completed: 1,
    generated_completed: 1,
    wear_count: 8,
    created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "clothes_003",
    user_id: "mock_user_001",
    image_url: "https://picsum.photos/seed/clothes3/400/600",
    name: "灰色针织开衫",
    category: "outerwear",
    color: "灰色",
    material: "羊毛",
    temperature_range: "spring_autumn",
    scene: "work",
    analysis_completed: 1,
    generated_completed: 1,
    wear_count: 3,
    created_at: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "clothes_004",
    user_id: "mock_user_001",
    image_url: "https://picsum.photos/seed/clothes4/400/600",
    name: "黑色小皮鞋",
    category: "accessory",
    color: "黑色",
    material: "皮革",
    temperature_range: "all_season",
    scene: "formal",
    analysis_completed: 1,
    generated_completed: 1,
    wear_count: 12,
    created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const user_id = searchParams.get("user_id");
  const category = searchParams.get("category");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 300));

  let clothes = mockClothes;

  if (category) {
    clothes = clothes.filter((c) => c.category === category);
  }

  return NextResponse.json({
    clothes,
    total: clothes.length,
  });
}
