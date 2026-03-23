"use client";

import React, { createContext, useContext, ReactNode } from "react";
import { useUser } from "@/hooks/useUser";
import type { UserInfo } from "@/types/api";

interface UserContextValue {
  user: UserInfo | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const UserContext = createContext<UserContextValue>({
  user: null,
  loading: true,
  error: null,
  refetch: () => {},
});

export function useUserContext() {
  return useContext(UserContext);
}

interface UserProviderProps {
  children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const { user, loading, error, refetch } = useUser();

  return (
    <UserContext.Provider value={{ user, loading, error, refetch }}>
      {children}
    </UserContext.Provider>
  );
}