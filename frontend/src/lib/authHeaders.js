import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getFlToken } from "@/lib/flAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";

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

export function buildPortalAuthHeaders(extra = {}) {
  const headers = { ...extra };

  const admin = getAdminToken();
  if (admin) headers["X-Admin-Token"] = admin;

  const pm = getPmToken();
  if (pm) headers["X-PM-Token"] = pm;

  const hr = getHrToken();
  if (hr) headers["X-HR-Token"] = hr;

  const shop = getShopToken();
  if (shop) headers["X-Shop-Token"] = shop;

  const safety = getSafetyToken();
  if (safety) headers["X-Safety-Token"] = safety;

  const dispatch = getDispatchToken();
  if (dispatch) headers["X-Dispatch-Token"] = dispatch;

  const fl = getFlToken();
  if (fl) headers["X-FL-Token"] = fl;

  const directory = getDirectoryToken();
  if (directory) headers["X-Directory-Token"] = directory;

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
