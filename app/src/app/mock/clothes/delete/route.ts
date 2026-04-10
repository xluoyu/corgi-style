import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/clothes/delete
 * 删除衣物
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { clothes_id } = body;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    message: "衣物删除成功",
  });
}
