import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/user/profile
 * 获取用户完整资料（含统计数据）
 */

// Mock 用户数据
const mockUser = {
  id: "mock_user_001",
  device_fingerprint: "mock_fp_abc123",
  nickname: "时尚达人",
  avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=mockuser",
  height: 170,
  weight: 60,
  created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
};

// Mock 衣物数量
const mockClothesCount = 4;
// Mock 穿搭数量
const mockOutfitCount = 28;

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const user_id = searchParams.get("user_id");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    user_id: mockUser.id,
    device_fingerprint: mockUser.device_fingerprint,
    nickname: mockUser.nickname,
    avatar_url: mockUser.avatar_url,
    gender: "female",
    style_preferences: "简约,韩风,休闲",
    default_occasion: "daily",
    height: 170,
    weight: 60,
    clothes_count: mockClothesCount,
    outfit_count: mockOutfitCount,
    created_at: mockUser.created_at,
  });
}
