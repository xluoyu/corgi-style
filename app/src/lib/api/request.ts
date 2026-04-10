/**
 * 通用请求函数
 */

import { getBaseUrl, getMockPrefix } from "./config";

/**
 * 通用请求函数
 */
export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl();
  const mockPrefix = getMockPrefix();
  const url = `${baseUrl}${mockPrefix}${endpoint}`;

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
export async function uploadRequest<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const baseUrl = getBaseUrl();
  const mockPrefix = getMockPrefix();
  const url = `${baseUrl}${mockPrefix}${endpoint}`;

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
