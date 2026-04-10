import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/history/save
 * 保存穿搭快照
 */
export async function POST(request: NextRequest) {
  const body = await request.json();

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json({
    message: "穿搭快照已保存",
    history_id: Date.now(),
  });
}
