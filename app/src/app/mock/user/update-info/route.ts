import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/user/update-info
 * 更新用户信息
 */
export async function POST(request: NextRequest) {
  const body = await request.json();

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    message: "更新成功",
  });
}
