import { NextRequest, NextResponse } from "next/server";

/**
 * POST /mock/chat/message/stream
 * 流式对话（v1）
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { user_id, session_id, message, context } = body;

  const sessionId = session_id || `mock_session_${Date.now()}`;

  // 创建 SSE 流
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const events = [
        { event: "thinking", data: { node: "supervisor", text: "正在分析您的请求..." } },
        { event: "text", data: "您好！我是 Corgi Style 的 AI 穿搭助手。" } },
        { event: "text", data: "请问有什么可以帮助您的？" } },
        { event: "done", data: { session_id: sessionId } },
      ];

      for (let i = 0; i < events.length; i++) {
        const { event, data } = events[i];
        await new Promise((resolve) => setTimeout(resolve, 300));
        const line = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
        controller.enqueue(encoder.encode(line));
      }

      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
