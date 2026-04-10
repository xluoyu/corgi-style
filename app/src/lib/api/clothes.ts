/**
 * 衣物 API
 */

import type {
  AddClothesRequest,
  AddClothesResponse,
  ClothesListResponse,
  DeleteClothesRequest,
  DeleteClothesResponse,
  ClothesStatusResponse,
} from "@/types/api";
import { request, uploadRequest } from "./request";
import { getUserId } from "./config";

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
