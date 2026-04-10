import { NextRequest, NextResponse } from "next/server";

/**
 * GET /mock/user/preference
 * 获取用户偏好
 */

// Mock 用户偏好数据
const mockUserProfile = {
  id: "mock_profile_001",
  user_id: "mock_user_001",
  nickname: "时尚达人",
  avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=mockuser",
  gender: "female",
  style_preferences: ["简约", "韩风", "休闲"],
  default_occasion: "daily",
  height: 170,
  weight: 60,
  created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  updated_at: new Date().toISOString(),
};

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const user_id = searchParams.get("user_id");

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json(mockUserProfile);
}
