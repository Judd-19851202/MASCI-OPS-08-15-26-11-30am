// searchApi.js — Iter155 (Phase G). Thin client for the unified
// /api/search endpoint. Forwards whichever portal token is live so
// the backend can scope results to the caller's role.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getFlToken } from "@/lib/flAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  const fl = getFlToken(); if (fl) h["X-FL-Token"] = fl;
  return h;
}

export function hasAnyPortalToken() {
  return Object.keys(authHeaders()).length > 0;
}

export async function globalSearch(q, { kinds, limit = 6, signal } = {}) {
  const params = { q, limit };
  if (kinds && kinds.length) params.kinds = Array.isArray(kinds) ? kinds.join(",") : String(kinds);
  const r = await axios.get(`${API}/search`, {
    headers: authHeaders(), params, signal,
  });
  return r.data;
}
