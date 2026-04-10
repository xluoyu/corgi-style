import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/chat/message
 * 非流式对话（兼容旧版本）
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { user_id, session_id, message, context } = body;

  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 1000));

  return NextResponse.json({
    session_id: session_id || `mock_session_${Date.now()}`,
    message: "这是 Mock 模式的模拟回复。我现在处于演示模式，无法连接真实后端。如果您想体验完整功能，请设置 NEXT_PUBLIC_USE_MOCK=false 并启动后端服务。",
    contents: [{ type: "text", content: "这是 Mock 模式的模拟回复。" }],
    data: undefined,
    suggestions: [
      { type: "text", text: "试试发送「今天穿什么」" },
      { type: "text", text: "查看我的衣橱" },
    ],
  });
}
