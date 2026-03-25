"use client";

import { useState, useEffect, useCallback } from "react";
import { getUserOrCreate } from "@/lib/api";
import type { UserInfo } from "@/types/api";

interface UseUserResult {
  user: UserInfo | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const USER_CACHE_KEY = "corgi_user_cache";

/**
 * useUser - 用户初始化 Hook
 * 在前端加载时自动获取或创建用户
 * 使用 localStorage 缓存用户信息
 */
export function useUser(): UseUserResult {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initUser = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const userInfo = await getUserOrCreate();
      setUser(userInfo);
      localStorage.setItem(USER_CACHE_KEY, JSON.stringify(userInfo));
      localStorage.setItem("user_id", userInfo.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取用户信息失败");
      console.error("用户初始化失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refetch = useCallback(() => {
    localStorage.removeItem(USER_CACHE_KEY);
    localStorage.removeItem("user_id");
    initUser();
  }, [initUser]);

  useEffect(() => {
    const cachedUser = localStorage.getItem(USER_CACHE_KEY);
    if (cachedUser) {
      try {
        const parsed = JSON.parse(cachedUser) as UserInfo;
        setUser(parsed);
        setLoading(false);
        return;
      } catch {
        localStorage.removeItem(USER_CACHE_KEY);
      }
    }
    initUser();
  }, [initUser]);

  return { user, loading, error, refetch };
}