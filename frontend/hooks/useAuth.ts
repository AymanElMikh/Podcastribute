"use client";

import { useState, useEffect, useCallback } from "react";
import { auth, User } from "@/lib/api";
import { getToken, setToken, clearToken } from "@/lib/auth";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export function useAuth(): AuthState {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await auth.me();
      setUser(me);
    } catch {
      clearToken();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async (email: string, password: string) => {
    const res = await auth.login(email, password);
    setToken(res.access_token);
    const me = await auth.me();
    setUser(me);
  };

  const register = async (email: string, password: string) => {
    const res = await auth.register(email, password);
    setToken(res.access_token);
    const me = await auth.me();
    setUser(me);
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return { user, loading, login, register, logout };
}
