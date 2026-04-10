/**
 * 穿搭历史 API
 */

import type {
  OutfitHistoryListResponse,
  OutfitHistoryDetail,
  SaveOutfitSnapshotRequest,
  SaveOutfitSnapshotResponse,
  OutfitStatsSummary,
} from "@/types/api";
import { request } from "./request";
import { getUserId } from "./config";

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
