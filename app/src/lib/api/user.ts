/**
 * 用户 API
 */

import type {
  GetUserOrCreateRequest,
  UpdateUserInfoRequest,
  UserInfo,
  UserProfile,
  UserProfileResponse,
} from "@/types/api";
import { request } from "./request";
import { getDeviceFingerprint, getUserId } from "./config";

/**
 * 获取或创建用户
 */
export async function getUserOrCreate(): Promise<UserInfo> {
  const res = await request<{
    user_id: string;
    device_fingerprint: string;
    nickname: string;
    avatar_url: string;
    height?: number;
    weight?: number;
    message: string;
  }>("/user/get-or-create", {
    method: "POST",
    body: JSON.stringify({
      device_fingerprint: getDeviceFingerprint(),
    } as GetUserOrCreateRequest),
  });
  // 映射后端字段到 UserInfo
  return {
    id: res.user_id,
    device_fingerprint: res.device_fingerprint,
    nickname: res.nickname,
    avatar_url: res.avatar_url,
    height: res.height,
    weight: res.weight,
    last_active_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

/**
 * 更新用户信息
 * user_id 从 localStorage 自动补全，无需调用方传入
 * 数组字段序列化为 JSON 字符串以匹配后端 TEXT 字段
 */
export async function updateUserInfo(data: Partial<UpdateUserInfoRequest>): Promise<{ message: string }> {
  const payload = {
    user_id: getUserId(),
    ...data,
  };
  // style_preferences 在 ORM 层由 JSON 类型自动序列化
  // 前端直接传 Python list 即可
  return await request<{ message: string }>("/user/update-info", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * 获取用户偏好
 */
export async function getUserPreference(): Promise<UserProfile> {
  return await request<UserProfile>(`/user/preference?user_id=${getUserId()}`);
}

/**
 * 获取用户完整资料（含统计数据）
 */
export async function getUserProfile(): Promise<UserProfileResponse> {
  return await request<UserProfileResponse>(`/user/profile?user_id=${getUserId()}`);
}
