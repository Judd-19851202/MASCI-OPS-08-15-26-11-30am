// lib/operationsCenterApi.js — Iter C + TRACK 14.0-RC1-FERRARI (2026-02-15).
//
// Routed through the shared `api` axios instance which auto-injects
// every portal token AND honors the namespace-aware 401 absorption
// rules (see /app/frontend/src/lib/api.js). `skipSessionStatus: true`
// keeps a background widget 401 from raising the global Session
// Expired modal — the widget surfaces its own inline error band
// instead.
import { api } from "@/lib/api";

export async function fetchOperationsCenter({ roleOverride } = {}) {
  const params = roleOverride ? { role_override: roleOverride } : {};
  const r = await api.get("/operations-center", {
    params,
    skipSessionStatus: true,
  });
  return r.data;
}
