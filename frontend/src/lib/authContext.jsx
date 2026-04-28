import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { setJwt, clearJwt, getJwt } from "@/lib/jwtAuth";

/**
 * AuthContext — Crew Hub JWT auth.
 *
 * Tokens are stored in localStorage (see lib/jwtAuth.js) and attached to every
 * request via the Authorization header (see lib/api.js). The backend accepts
 * either a cookie or `Authorization: Bearer …` — we use the header so requests
 * don't trip the credentialed-CORS rules on Cloudflare wildcard origins.
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
    // Skip the network round-trip if we don't even have a token stored.
    if (!getJwt()) {
      setUser(null);
      return null;
    }
    try {
      const r = await api.get("/auth/me");
      setUser(r.data);
      return r.data;
    } catch {
      // 401 / network error — drop the bad token
      clearJwt();
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    const r = await api.post("/auth/login", { email, password });
    if (r.data?.access_token) {
      setJwt(r.data.access_token);
    }
    setUser(r.data.user);
    return r.data.user;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      /* ignore — we're clearing locally anyway */
    }
    clearJwt();
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
