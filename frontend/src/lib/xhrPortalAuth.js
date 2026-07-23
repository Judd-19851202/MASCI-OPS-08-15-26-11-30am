import { buildPortalAuthHeaders } from "@/lib/authHeaders";

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

export function installPortalXhrAuth() {
  if (typeof window === "undefined" || window.__masciPortalXhrAuthInstalled) return;
  const proto = window.XMLHttpRequest?.prototype;
  if (!proto) return;

  const nativeOpen = proto.open;
  const nativeSend = proto.send;

  proto.open = function patchedOpen(method, url, ...rest) {
    this.__masciPortalAuthUrl = url;
    return nativeOpen.call(this, method, url, ...rest);
  };

  proto.send = function patchedSend(body) {
    try {
      if (shouldAttach(this.__masciPortalAuthUrl)) {
        const headers = buildPortalAuthHeaders();
        Object.entries(headers).forEach(([key, value]) => {
          if (value) this.setRequestHeader(key, value);
        });
      }
    } catch {
      // keep native behavior
    }
    return nativeSend.call(this, body);
  };

  window.__masciPortalXhrAuthInstalled = true;
}
