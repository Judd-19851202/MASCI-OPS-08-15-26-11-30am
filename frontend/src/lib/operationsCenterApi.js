// lib/operationsCenterApi.js — Iter C.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function leadershipToken() {
  try { return sessionStorage.getItem("masci.leadership.token") || localStorage.getItem("masci.leadership.token") || null; } catch { return null; }
}

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  const fl = leadershipToken(); if (fl) h["X-Leadership-Token"] = fl;
  return h;
}

export async function fetchOperationsCenter({ roleOverride } = {}) {
  const params = roleOverride ? { role_override: roleOverride } : {};
  const r = await axios.get(`${API}/operations-center`, {
    headers: authHeaders(), params,
  });
  return r.data;
}
