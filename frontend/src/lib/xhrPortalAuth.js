import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { getDirectoryToken } from "@/lib/directoryAuth";
import { inferActivePortalForAuth, inferPortalsForApiPath } from "@/lib/portalAuthScope";

function shouldAttach(url) {
  if (typeof window === "undefined") return false;
  try {
    const target = new URL(url, window.location.origin);
    const configuredBase = new URL(process.env.REACT_APP_BACKEND_URL || window.location.origin, window.location.origin);
    return target.origin === configuredBase.origin && target.pathname.startsWith("/api/");
  } catch {
    return false;
  }
}

function inferPortalsForUrl(url) {
  try {
    const target = new URL(url, window.location.origin);
    const activePortal = inferActivePortalForAuth(
      typeof window !== "undefined" ? window.location?.pathname || "" : ""
    );
    return inferPortalsForApiPath(target.pathname, activePortal);
  } catch {
    return [];
  }
}

export function installPortalXhrAuth() {
  if (typeof window === "undefined" || window.__masciPortalXhrAuthInstalled) return;
  const proto = window.XMLHttpRequest?.prototype;
  if (!proto) return;

  const nativeOpen = proto.open;
  const nativeSetRequestHeader = proto.setRequestHeader;
  const nativeSend = proto.send;

  proto.open = function patchedOpen(method, url, ...rest) {
    this.__masciPortalAuthUrl = url;
    this.__masciPortalExplicitHeaders = new Set();
    return nativeOpen.call(this, method, url, ...rest);
  };

  proto.setRequestHeader = function patchedSetRequestHeader(name, value) {
    try {
      if (!this.__masciPortalExplicitHeaders) this.__masciPortalExplicitHeaders = new Set();
      this.__masciPortalExplicitHeaders.add(String(name || "").toLowerCase());
    } catch {
      // keep native behavior
    }
    return nativeSetRequestHeader.call(this, name, value);
  };

  proto.send = function patchedSend(body) {
    try {
      if (shouldAttach(this.__masciPortalAuthUrl)) {
        const inferred = inferPortalsForUrl(this.__masciPortalAuthUrl);
        const headers =
          inferred.length === 1 && inferred[0] === "directory"
            ? (getDirectoryToken() ? { "X-Directory-Token": getDirectoryToken() } : {})
            : buildScopedPortalAuthHeaders(inferred);
        Object.entries(headers).forEach(([key, value]) => {
          const explicit = this.__masciPortalExplicitHeaders || new Set();
          if (value && !explicit.has(String(key).toLowerCase())) {
            nativeSetRequestHeader.call(this, key, value);
          }
        });
      }
    } catch {
      // keep native behavior
    }
    return nativeSend.call(this, body);
  };

  window.__masciPortalXhrAuthInstalled = true;
}
