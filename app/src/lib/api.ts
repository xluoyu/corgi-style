/**
 * API 客户端
 * 封装所有后端 API 调用
 */

import type {
  GetUserOrCreateRequest,
  UserInfo,
  UpdateUserInfoRequest,
  UserProfile,
  AddClothesRequest,
  AddClothesResponse,
  ClothesListResponse,
  DeleteClothesRequest,
  DeleteClothesResponse,
  UploadClothesResponse,
  ClothesStatusResponse,
  GenerateOutfitRequest,
  GenerateOutfitResponse,
  OutfitFeedbackResponse,
  OutfitHistoryListResponse,
  OutfitHistoryDetail,
  SaveOutfitSnapshotRequest,
  SaveOutfitSnapshotResponse,
  OutfitStatsSummary,
} from "@/types/api";

// API 基础 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 设备指纹生成
function generateDeviceFingerprint(): string {
  let fp = "";
  if (typeof window !== "undefined") {
    fp += window.navigator.userAgent;
    fp += window.screen.width + "x" + window.screen.height;
    fp += window.navigator.language;
    fp += new Date().getTimezoneOffset();
  }
  // 简单哈希
  let hash = 0;
  for (let i = 0; i < fp.length; i++) {
    const char = fp.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return "fp_" + Math.abs(hash).toString(36);
}

// 设备指纹（缓存）
let DEVICE_FINGERPRINT: string | null = null;

function getDeviceFingerprint(): string {
  if (!DEVICE_FINGERPRINT) {
    DEVICE_FINGERPRINT = generateDeviceFingerprint();
  }
  return DEVICE_FINGERPRINT;
}

// 用户 ID（缓存）
let USER_ID: string | null = null;

export function getUserId(): string {
  if (!USER_ID) {
    const stored = localStorage.getItem("user_id");
    if (stored) {
      USER_ID = stored;
    } else {
      USER_ID = getDeviceFingerprint();
      localStorage.setItem("user_id", USER_ID);
    }
  }
  return USER_ID;
}

/**
 * 通用请求函数
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `请求失败: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API 请求错误 [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * 上传文件的请求函数
 */
async function uploadRequest<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `上传失败: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API 上传错误 [${endpoint}]:`, error);
    throw error;
  }
}

// ============ 用户 API ============

/**
 * 获取或创建用户
 */
export async function getUserOrCreate(): Promise<UserInfo> {
  return await request<UserInfo>("/user/get-or-create", {
    method: "POST",
    body: JSON.stringify({
      device_fingerprint: getDeviceFingerprint(),
    } as GetUserOrCreateRequest),
  });
}

/**
 * 更新用户信息
 */
export async function updateUserInfo(data: UpdateUserInfoRequest): Promise<{ message: string }> {
  return await request<{ message: string }>("/user/update-info", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * 获取用户偏好
 */
export async function getUserPreference(): Promise<UserProfile> {
  return await request<UserProfile>(`/user/preference?user_id=${getUserId()}`);
}

// ============ 衣物 API ============

/**
 * 添加衣物
 */
export async function addClothes(data: AddClothesRequest): Promise<AddClothesResponse> {
  return await request<AddClothesResponse>("/clothes/add", {
    method: "POST",
    body: JSON.stringify({ ...data, user_id: getUserId() }),
  });
}

/**
 * 获取衣物列表
 */
export async function getClothesList(category?: string): Promise<ClothesListResponse> {
  const params = new URLSearchParams({ user_id: getUserId() });
  if (category) {
    params.set("category", category);
  }
  return await request<ClothesListResponse>(`/clothes/list?${params.toString()}`);
}

/**
 * 删除衣物
 */
export async function deleteClothes(clothesId: string): Promise<DeleteClothesResponse> {
  return await request<DeleteClothesResponse>("/clothes/delete", {
    method: "POST",
    body: JSON.stringify({
      user_id: getUserId(),
      clothes_id: clothesId,
    } as DeleteClothesRequest),
  });
}

/**
 * 上传衣物图片（仅上传到OSS，后台异步处理分析和生成）
 */
export async function uploadClothesImage(
  file: File
): Promise<{ clothes_id: number; message: string; image_url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", getUserId());

  return await uploadRequest<{ clothes_id: number; message: string; image_url: string }>(
    "/clothes/upload",
    formData
  );
}

/**
 * 获取衣物处理状态
 */
export async function getClothesStatus(clothesId: string): Promise<ClothesStatusResponse> {
  return await request<ClothesStatusResponse>(`/clothes/status/${clothesId}`);
}

// ============ 穿搭 API ============

/**
 * 生成今日穿搭
 */
export async function generateTodayOutfit(
  city: string,
  temperature: number,
  scene?: string
): Promise<GenerateOutfitResponse> {
  return await request<GenerateOutfitResponse>("/outfit/generate-today", {
    method: "POST",
    body: JSON.stringify({
      city,
      temperature,
      scene,
    } as GenerateOutfitRequest),
  });
}

/**
 * 强制刷新今日穿搭
 */
export async function refreshOutfit(
  city: string,
  temperature: number,
  scene?: string
): Promise<GenerateOutfitResponse> {
  return await request<GenerateOutfitResponse>("/outfit/refresh", {
    method: "POST",
    body: JSON.stringify({
      city,
      temperature,
      scene,
    } as GenerateOutfitRequest),
  });
}

/**
 * 提交穿搭反馈
 */
export async function submitOutfitFeedback(
  feedback?: string,
  rating?: number
): Promise<OutfitFeedbackResponse> {
  return await request<OutfitFeedbackResponse>("/outfit/feedback", {
    method: "POST",
    body: JSON.stringify({
      user_id: getUserId(),
      description: feedback,
      rating,
    }),
  });
}

// ============ 工具函数 ============

/**
 * 轮询衣物处理状态
 */
export async function pollClothesStatus(
  clothesId: string,
  maxAttempts = 60,
  interval = 1000
): Promise<ClothesStatusResponse> {
  for (let i = 0; i < maxAttempts; i++) {
    const status = await getClothesStatus(clothesId);

    if (status.analysis_completed && status.generated_completed) {
      return status;
    }

    if (i < maxAttempts - 1) {
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
  }

  throw new Error("衣物处理超时");
}

// ============ 穿搭历史 API ============

/**
 * 获取穿搭历史列表
 */
export async function getOutfitHistory(params: {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
}): Promise<OutfitHistoryListResponse> {
  const searchParams = new URLSearchParams({ user_id: getUserId() });

  if (params.page) searchParams.set("page", params.page.toString());
  if (params.pageSize) searchParams.set("page_size", params.pageSize.toString());
  if (params.startDate) searchParams.set("start_date", params.startDate);
  if (params.endDate) searchParams.set("end_date", params.endDate);

  return await request<OutfitHistoryListResponse>(`/history/list?${searchParams.toString()}`);
}

/**
 * 获取穿搭历史详情
 */
export async function getOutfitHistoryDetail(historyId: number): Promise<OutfitHistoryDetail> {
  return await request<OutfitHistoryDetail>(
    `/history/${historyId}?user_id=${getUserId()}`
  );
}

/**
 * 保存穿搭快照
 */
export async function saveOutfitSnapshot(data: SaveOutfitSnapshotRequest): Promise<SaveOutfitSnapshotResponse> {
  return await request<SaveOutfitSnapshotResponse>("/history/save", {
    method: "POST",
    body: JSON.stringify({
      ...data,
      user_id: getUserId(),
    }),
  });
}

/**
 * 获取穿搭统计摘要
 */
export async function getOutfitStatsSummary(days = 30): Promise<OutfitStatsSummary> {
  const params = new URLSearchParams({
    user_id: getUserId(),
    days: days.toString(),
  });
  return await request<OutfitStatsSummary>(`/history/stats/summary?${params.toString()}`);
}

// ============ 聊天 API（流式） ============

import type { ChatStreamEvent, ChatStreamParams, OutfitCard, Suggestion } from "@/types/chat";

/**
 * 流式对话
 * 返回一个 AsyncGenerator，逐步产出事件
 */
export async function* chatMessageStream(
  params: ChatStreamParams
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const url = `${API_BASE_URL}/chat/message/stream`;

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
              yield { event: eventType as ChatStreamEvent["event"], content: data } as ChatStreamEvent;
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
