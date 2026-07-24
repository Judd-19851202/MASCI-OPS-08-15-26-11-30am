import axios from "axios";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

function toAbsoluteUrl(url, baseURL) {
  if (typeof window === "undefined") return null;
  try {
    const base = baseURL || process.env.REACT_APP_BACKEND_URL || window.location.origin;
    return new URL(url || "", base);
  } catch {
    return null;
  }
}

function shouldAttachAxiosAuth(config) {
  if (typeof window === "undefined") return false;
  const target = toAbsoluteUrl(config?.url, config?.baseURL);
  if (!target) return false;
  try {
    const configuredBase = new URL(process.env.REACT_APP_BACKEND_URL || window.location.origin, window.location.origin);
    return target.origin === configuredBase.origin && target.pathname.startsWith("/api/");
  } catch {
    return false;
  }
}

function ensureHeadersObject(headers) {
  if (!headers) return {};
  if (typeof headers.toJSON === "function") return headers.toJSON();
  return { ...headers };
}

function inferPortalsForPath(pathname = "") {
  const activePath = typeof window !== "undefined" ? window.location?.pathname || "" : "";
  const activePortal =
    activePath.startsWith("/admin") ? "admin"
    : activePath.startsWith("/hr") ? "hr"
    : activePath.startsWith("/safety") ? "safety"
    : activePath.startsWith("/pm") ? "pm"
    : activePath.startsWith("/shop") ? "shop"
    : activePath.startsWith("/dispatch") ? "dispatch"
    : activePath.startsWith("/field-leadership") ? "fl"
    : activePath.startsWith("/leadership") ? "leadership"
    : null;
  if (!pathname) return [];
  if (pathname.startsWith("/api/admin/") || pathname === "/api/admin") return ["admin"];
  if (pathname.startsWith("/api/hr/") || pathname === "/api/hr") return ["hr"];
  if (pathname.startsWith("/api/safety/") || pathname === "/api/safety") return ["safety"];
  if (pathname.startsWith("/api/pm/") || pathname === "/api/pm") return ["pm"];
  if (pathname.startsWith("/api/shop/") || pathname === "/api/shop") return ["shop"];
  if (pathname.startsWith("/api/dispatch/") || pathname === "/api/dispatch") return ["dispatch"];
  if (pathname.startsWith("/api/field-leadership/") || pathname === "/api/field-leadership") return ["fl"];
  if (pathname.startsWith("/api/leadership/") || pathname === "/api/leadership") return ["leadership"];
  if ((pathname.startsWith("/api/operations-actions/") || pathname.startsWith("/api/operations-map/")) && activePortal) return [activePortal];
  return [];
}

function installInterceptor(instance) {
  if (!instance || instance.__masciPortalAxiosInstalled) return instance;
  instance.interceptors.request.use((config) => {
    if (!shouldAttachAxiosAuth(config)) return config;
    const merged = ensureHeadersObject(config.headers);
    const target = toAbsoluteUrl(config?.url, config?.baseURL);
    const authHeaders = buildScopedPortalAuthHeaders(inferPortalsForPath(target?.pathname || ""));
    Object.entries(authHeaders).forEach(([key, value]) => {
      if (value && !(key in merged)) merged[key] = value;
    });
    config.headers = merged;
    return config;
  });
  instance.__masciPortalAxiosInstalled = true;
  return instance;
}

export function installPortalAxiosAuth() {
  if (typeof window === "undefined" || axios.__masciPortalAxiosPatched) return;

  installInterceptor(axios);

  const originalCreate = axios.create.bind(axios);
  axios.create = (...args) => installInterceptor(originalCreate(...args));

  axios.__masciPortalAxiosPatched = true;
}
