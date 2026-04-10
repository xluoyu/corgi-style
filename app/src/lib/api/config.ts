/**
 * API 配置
 * 封装环境变量和基础配置
 */

// 是否启用 Mock 模式
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

// API 基础 URL
export const getBaseUrl = (): string => {
  if (USE_MOCK) {
    return "";  // Mock 模式使用相对路径
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

// Mock 模式下 API 路径前缀
export const getMockPrefix = (): string => {
  return USE_MOCK ? "/mock" : "";
};

// 设备指纹生成
export function generateDeviceFingerprint(): string {
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

export function getDeviceFingerprint(): string {
  if (!DEVICE_FINGERPRINT) {
    DEVICE_FINGERPRINT = generateDeviceFingerprint();
  }
  return DEVICE_FINGERPRINT;
}

// 用户 ID（缓存）
let USER_ID: string | null = null;

export function getUserId(): string {
  if (!USER_ID) {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("user_id");
      if (stored) {
        USER_ID = stored;
      } else {
        USER_ID = getDeviceFingerprint();
        localStorage.setItem("user_id", USER_ID);
      }
    } else {
      USER_ID = getDeviceFingerprint();
    }
  }
  return USER_ID;
}
