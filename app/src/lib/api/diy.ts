/**
 * DIY 穿搭 API
 */

import type { DIYOutfitRecord } from "@/types/diy";
import { request } from "./request";
import { getUserId } from "./config";

/**
 * 获取 DIY 穿搭记录列表
 */
export async function getDIYRecords(): Promise<DIYOutfitRecord[]> {
  const response = await request<{ records: DIYOutfitRecord[] }>(`/mock/diy/records`);
  return response.records;
}

/**
 * 更新 DIY 记录名称
 */
export async function updateDIYRecordName(id: string, name: string): Promise<void> {
  // TODO: 真实 API 实现后替换
  console.log(`Updating record ${id} name to: ${name}`);
}

/**
 * 删除 DIY 记录
 */
export async function deleteDIYRecord(id: string): Promise<void> {
  // TODO: 真实 API 实现后替换
  console.log(`Deleting record: ${id}`);
}
