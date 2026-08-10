import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getFlToken } from "@/lib/flAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";
import { inferActivePortalForAuth } from "@/lib/portalAuthScope";

const PORTAL_HEADER_MAP = {
  admin: "X-Admin-Token",
  pm: "X-PM-Token",
  hr: "X-HR-Token",
  shop: "X-Shop-Token",
  safety: "X-Safety-Token",
  dispatch: "X-Dispatch-Token",
  field_leadership: "X-FL-Token",
  fl: "X-FL-Token",
  leadership: "X-FL-Token",
};

const DIRECTORY_COMPATIBLE_PORTALS = new Set([
  "directory",
  "admin",
  "pm",
  "hr",
  "shop",
  "safety",
  "field_leadership",
  "fl",
  "leadership",
  "dispatch",
]);

function normalizeRequestedPortals(portals = null) {
  if (portals === "all") return null;
  if (Array.isArray(portals)) return portals.filter(Boolean);
  if (typeof portals === "string" && portals.trim()) return [portals.trim()];
  try {
    if (typeof window !== "undefined") {
      const activePortal = inferActivePortalForAuth(window.location?.pathname || "");
      return activePortal ? [activePortal] : null;
    }
  } catch {
    /* ignore portal inference failures */
  }
  return null;
}

function wantsPortal(requestedPortals, portal) {
  return !requestedPortals || requestedPortals.includes(portal);
}

export function buildPortalAuthHeaders(extra = {}, portals = null) {
  const headers = { ...extra };
  const requestedPortals = normalizeRequestedPortals(portals);

  const admin = getAdminToken();
  if (admin && wantsPortal(requestedPortals, "admin")) headers["X-Admin-Token"] = admin;

  const pm = getPmToken();
  if (pm && wantsPortal(requestedPortals, "pm")) headers["X-PM-Token"] = pm;

  const hr = getHrToken();
  if (hr && wantsPortal(requestedPortals, "hr")) headers["X-HR-Token"] = hr;

  const shop = getShopToken();
  if (shop && wantsPortal(requestedPortals, "shop")) headers["X-Shop-Token"] = shop;

  const safety = getSafetyToken();
  if (safety && wantsPortal(requestedPortals, "safety")) headers["X-Safety-Token"] = safety;

  const dispatch = getDispatchToken();
  if (dispatch && wantsPortal(requestedPortals, "dispatch")) headers["X-Dispatch-Token"] = dispatch;

  const fl = getFlToken();
  if (fl && (wantsPortal(requestedPortals, "field_leadership") || wantsPortal(requestedPortals, "fl") || wantsPortal(requestedPortals, "leadership"))) {
    headers["X-FL-Token"] = fl;
  }

  const directory = getDirectoryToken();
  if (
    directory && (
      !requestedPortals
      || requestedPortals.some((portal) => DIRECTORY_COMPATIBLE_PORTALS.has(portal))
    )
  ) {
    headers["X-Directory-Token"] = directory;
  }

  return headers;
}

export function buildScopedPortalAuthHeaders(portals = [], extra = {}) {
  const requested = Array.isArray(portals) ? portals : [portals];
  const all = buildPortalAuthHeaders(extra);
  const scoped = { ...extra };

  for (const portal of requested) {
    const key = PORTAL_HEADER_MAP[portal];
    if (key && all[key]) scoped[key] = all[key];
  }
  if (
    all["X-Directory-Token"]
    && requested.some((portal) => DIRECTORY_COMPATIBLE_PORTALS.has(portal))
  ) {
    scoped["X-Directory-Token"] = all["X-Directory-Token"];
  }
  return scoped;
}

export function hasAnyPortalAuthToken() {
  return !!(
    getAdminToken()
    || getPmToken()
    || getHrToken()
    || getShopToken()
    || getSafetyToken()
    || getDispatchToken()
    || getFlToken()
    || getDirectoryToken()
  );
}
