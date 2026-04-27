import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

/**
 * AuthContext — Phase 1 JWT auth (httpOnly cookie sessions).
 *
 * States:
 *   user === undefined  → still checking (initial page load)
 *   user === null       → not authenticated
 *   user === { ... }    → authenticated
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined);

  const refresh = useCallback(async () => {
    try {
      const r = await api.get("/auth/me");
      setUser(r.data);
      return r.data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    const r = await api.post("/auth/login", { email, password });
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      /* ignore */
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
