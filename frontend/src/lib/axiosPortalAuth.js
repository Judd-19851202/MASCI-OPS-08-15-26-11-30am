import axios from "axios";
import { buildPortalAuthHeaders } from "@/lib/authHeaders";

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

function installInterceptor(instance) {
  if (!instance || instance.__masciPortalAxiosInstalled) return instance;
  instance.interceptors.request.use((config) => {
    if (!shouldAttachAxiosAuth(config)) return config;
    const merged = ensureHeadersObject(config.headers);
    const authHeaders = buildPortalAuthHeaders();
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
