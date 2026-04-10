/**
 * 聊天 API（流式）
 */

import type { ChatStreamEvent, ChatStreamParams, Suggestion } from "@/types/chat";
import { getBaseUrl, getMockPrefix } from "./config";
import { request } from "./request";

/**
 * 流式对话
 * 返回一个 AsyncGenerator，逐步产出事件
 */
export async function* chatMessageStream(
  params: ChatStreamParams
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const baseUrl = getBaseUrl();
  const mockPrefix = getMockPrefix();
  const url = `${baseUrl}${mockPrefix}/chat/message/stream`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: params.user_id,
      session_id: params.session_id,
      message: params.message,
      context: params.context,
    }),
  });

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("响应体为空");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 处理 SSE 事件
      // 格式: event: type\ndata: json\n\n
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("event:")) {
          const eventType = line.slice(6).trim();
          // 直接使用下一个索引获取 data 行
          const nextIdx = i + 1;
          if (nextIdx < lines.length && lines[nextIdx].startsWith("data:")) {
            const dataStr = lines[nextIdx].slice(5).trim();
            try {
              const data = JSON.parse(dataStr);
              // 提取实际的 content 字段（后端返回的是完整 event 对象）
              const extractedContent = data.content !== undefined ? data.content : data;
              yield { event: eventType as ChatStreamEvent["event"], content: extractedContent } as ChatStreamEvent;
            } catch {
              // 忽略解析错误
            }
            i = nextIdx; // 跳过已处理的 data 行
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * 非流式聊天（兼容旧版本）
 */
export async function chatMessage(params: ChatStreamParams): Promise<{
  session_id: string;
  message: string;
  contents: Array<{ type: string; content: any }>;
  data?: any;
  suggestions?: Suggestion[];
}> {
  return await request("/chat/message", {
    method: "POST",
    body: JSON.stringify({
      user_id: params.user_id,
      session_id: params.session_id,
      message: params.message,
      context: params.context,
    }),
  });
}

/**
 * V3 流式对话（基于 LangGraph Multi-Agent）
 * 返回一个 AsyncGenerator，逐步产出事件
 */
export async function* chatMessageStreamV3(
  params: ChatStreamParams
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const baseUrl = getBaseUrl();
  const mockPrefix = getMockPrefix();
  const url = `${baseUrl}${mockPrefix}/chat/message/v3/stream`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: params.user_id,
      session_id: params.session_id,
      message: params.message,
      context: params.context,
    }),
  });

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("响应体为空");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 处理 SSE 事件
      // 格式: event: type\ndata: json\n\n
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("event:")) {
          const eventType = line.slice(6).trim();
          // 直接使用下一个索引获取 data 行
          const nextIdx = i + 1;
          if (nextIdx < lines.length && lines[nextIdx].startsWith("data:")) {
            const dataStr = lines[nextIdx].slice(5).trim();
            try {
              const data = JSON.parse(dataStr);
              // 提取实际的 content 字段（后端返回的是完整 event 对象）
              const extractedContent = data.content !== undefined ? data.content : data;
              yield { event: eventType as ChatStreamEvent["event"], content: extractedContent } as ChatStreamEvent;
            } catch {
              // 忽略解析错误
            }
            i = nextIdx; // 跳过已处理的 data 行
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * V3 非流式聊天（基于 LangGraph Multi-Agent）
 */
export async function chatMessageV3(params: ChatStreamParams): Promise<{
  session_id: string;
  message: string;
  contents: Array<{ type: string; content: any }>;
  data?: any;
  suggestions?: Suggestion[];
}> {
  return await request("/chat/message/v3", {
    method: "POST",
    body: JSON.stringify({
      user_id: params.user_id,
      session_id: params.session_id,
      message: params.message,
      context: params.context,
    }),
  });
}
