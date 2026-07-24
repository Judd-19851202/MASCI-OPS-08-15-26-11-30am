import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

function toAbsoluteUrl(input) {
  if (typeof window === "undefined") return null;
  const raw = typeof input === "string" ? input : input?.url;
  if (!raw) return null;
  try {
    return new URL(raw, window.location.origin);
  } catch {
    return null;
  }
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

export function shouldAttachPortalAuth(input) {
  if (typeof window === "undefined") return false;
  const target = toAbsoluteUrl(input);
  if (!target) return false;
  try {
    const configuredBase = new URL(process.env.REACT_APP_BACKEND_URL || window.location.origin, window.location.origin);
    const sameBackendOrigin = target.origin === configuredBase.origin;
    const sameFrontendOrigin = target.origin === window.location.origin;
    return (sameBackendOrigin || sameFrontendOrigin) && target.pathname.startsWith("/api/");
  } catch {
    return false;
  }
}

function mergeAuthHeaders(input, ...sources) {
  const headers = new Headers();
  for (const source of sources) {
    if (!source) continue;
    const next = new Headers(source);
    next.forEach((value, key) => headers.set(key, value));
  }
  const target = toAbsoluteUrl(input);
  const authHeaders = buildScopedPortalAuthHeaders(inferPortalsForPath(target?.pathname || ""));
  Object.entries(authHeaders).forEach(([key, value]) => {
    if (value && !headers.has(key)) headers.set(key, value);
  });
  return headers;
}

export function installPortalFetchAuth() {
  if (typeof window === "undefined" || window.__masciPortalFetchAuthInstalled) return;
  const nativeFetch = window.fetch.bind(window);

  window.fetch = (input, init = {}) => {
    try {
      if (!shouldAttachPortalAuth(input)) {
        return nativeFetch(input, init);
      }

      if (input instanceof Request) {
        const request = new Request(input, {
          ...init,
          headers: mergeAuthHeaders(input, input.headers, init.headers),
        });
        return nativeFetch(request);
      }

      return nativeFetch(input, {
        ...init,
        headers: mergeAuthHeaders(input, init.headers),
      });
    } catch {
      return nativeFetch(input, init);
    }
  };

  window.__masciPortalFetchAuthInstalled = true;
}
