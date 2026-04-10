import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/outfit/feedback
 * 提交穿搭反馈
 */
export async function POST(request: NextRequest) {
  const body = await request.json();

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 200));

  return NextResponse.json({
    message: "反馈已收到，感谢您的建议！",
  });
}
