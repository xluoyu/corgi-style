/**
 * 穿搭 API
 */

import type {
  GenerateOutfitRequest,
  GenerateOutfitResponse,
  OutfitFeedbackResponse,
} from "@/types/api";
import { request } from "./request";
import { getUserId } from "./config";

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
