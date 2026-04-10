import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/clothes/add
 * 添加衣物
 */
export async function POST(request: NextRequest) {
  const body = await request.json();

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 500));

  return NextResponse.json({
    clothes_id: `mock_clothes_${Date.now()}`,
    message: "衣物添加成功",
  });
}
