import { buildPortalAuthHeaders } from "@/lib/authHeaders";

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

function mergeAuthHeaders(...sources) {
  const headers = new Headers();
  for (const source of sources) {
    if (!source) continue;
    const next = new Headers(source);
    next.forEach((value, key) => headers.set(key, value));
  }
  const authHeaders = buildPortalAuthHeaders();
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
          headers: mergeAuthHeaders(input.headers, init.headers),
        });
        return nativeFetch(request);
      }

      return nativeFetch(input, {
        ...init,
        headers: mergeAuthHeaders(init.headers),
      });
    } catch {
      return nativeFetch(input, init);
    }
  };

  window.__masciPortalFetchAuthInstalled = true;
}
