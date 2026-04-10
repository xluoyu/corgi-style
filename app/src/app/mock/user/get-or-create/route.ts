import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/user/get-or-create
 * 获取或创建用户
 */

// Mock 用户数据
const mockUser = {
  id: "mock_user_001",
  device_fingerprint: "mock_fp_abc123",
  nickname: "时尚达人",
  avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=mockuser",
  height: 170,
  weight: 60,
  last_active_at: new Date().toISOString(),
  created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  updated_at: new Date().toISOString(),
};

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { device_fingerprint } = body;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    user_id: mockUser.id,
    device_fingerprint: device_fingerprint || mockUser.device_fingerprint,
    nickname: mockUser.nickname,
    avatar_url: mockUser.avatar_url,
    height: mockUser.height,
    weight: mockUser.weight,
    message: "用户创建成功",
  });
}
