// signaturesApi.js — Iter154 (Phase F). Thin client for the unified
// signature engine.
import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getFlToken } from "@/lib/flAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const s = getSafetyToken(); if (s) h["X-Safety-Token"] = s;
  const p = getPmToken(); if (p) h["X-PM-Token"] = p;
  const sh = getShopToken(); if (sh) h["X-Shop-Token"] = sh;
  const d = getDispatchToken(); if (d) h["X-Dispatch-Token"] = d;
  const l = getFlToken(); if (l) h["X-FL-Token"] = l;
  return h;
}

export const SIGNATURE_TYPES = [
  "supervisor", "employee", "witness", "approver",
  "receiver", "inspector", "trainer", "trainee", "other",
];

export async function captureSignature(body) {
  const r = await axios.post(`${API}/signatures`, body, { headers: authHeaders() });
  return r.data;
}

export async function listSignatures(params = {}) {
  const r = await axios.get(`${API}/signatures`, { headers: authHeaders(), params });
  return r.data;
}
