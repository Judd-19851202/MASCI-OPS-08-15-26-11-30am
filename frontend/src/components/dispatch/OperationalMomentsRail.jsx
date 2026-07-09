/**
 * OperationalMomentsRail.jsx · iter431 · Phase 29 · Part 2.
 *
 * Read-only chronological "Operational Moments" rail for AssignmentDrawer.
 * Merges four data sources into one calm vertical timeline:
 *
 *   • lifecycle state transitions (state_history)
 *   • dispatch_continuity_events
 *   • recovery_history transitions
 *   • operational_attachments uploads
 *
 * Doctrine
 * --------
 * - Reads `/api/operational-moments/by-assignment/{id}` (ONE endpoint,
 *   ONE network round-trip). Backend does the merge + sort so the FE
 *   never juggles 4 GETs and 4 loading states.
 * - Calm operational language: "Driver started", "Returned to service",
 *   "Photo attached" — never "event", "feed", "activity".
 * - Read-only · no actions, no buttons, no alerts.
 * - Bilingual via `useT()`.
 * - Mobile-first vertical timeline. No graphs, no analytics, no KPIs.
 * - Sticky-header friendly: the rail respects the drawer's scroll
 *   container; no internal scroll trap.
 */
import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, Wrench, Camera, CircleDot, Clock,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;

function _portalHeaders() {
  const h = {};
  const a = getAdminToken();
  const d = getDispatchToken();
  let s = null, p = null, sa = null;
  try { s = getShopToken && getShopToken(); } catch { /* optional */ }
  try { p = getPmToken && getPmToken(); } catch { /* optional */ }
  try { sa = getSafetyToken && getSafetyToken(); } catch { /* optional */ }
  if (a) h["X-Admin-Token"] = a;
  if (d) h["X-Dispatch-Token"] = d;
  if (s) h["X-Shop-Token"] = s;
  if (p) h["X-PM-Token"] = p;
  if (sa) h["X-Safety-Token"] = sa;
  return h;
}

function _fmt(iso) {
  if (!iso) return "—";
  try {
    return formatPlatformTime(iso);
  } catch {
    return iso;
  }
}

// Icon + accent classes per moment kind. Coloured TEXT only · no
// gradient backgrounds · no animation · per platform doctrine.
const KIND_VISUAL = {
  lifecycle:  { Icon: CircleDot, accent: "text-slate-700",   ring: "border-slate-200" },
  recovery:   { Icon: Wrench,    accent: "text-amber-700",   ring: "border-amber-200" },
  continuity: { Icon: Activity,  accent: "text-emerald-700", ring: "border-emerald-200" },
  attachment: { Icon: Camera,    accent: "text-sky-700",     ring: "border-sky-200" },
};

function _labelFor(t, m) {
  // Translate canonical labels through useT() so EN ↔ ES works without
  // needing a server-side i18n catalogue per moment kind.
  const raw = m.label || "";
  // Common lifecycle labels we want short forms for in the rail:
  const lifecycleMap = {
    "State → acknowledged":         t("Acknowledged"),
    "State → assigned":             t("Assigned"),
    "State → en_route":             t("En route"),
    "State → on_site":              t("On site"),
    "State → completed":            t("Completed"),
    "State → cancelled":            t("Cancelled"),
    "State → breakdown":            t("Breakdown reported"),
  };
  if (m.kind === "lifecycle" && lifecycleMap[raw]) return lifecycleMap[raw];
  const recoveryMap = {
    "Recovery → waiting_on_parts":      t("Waiting on parts"),
    "Recovery → operational_test":      t("Operational test"),
    "Recovery → returned_to_service":   t("Returned to service"),
    "Recovery → diagnosed":             t("Diagnosed"),
    "Recovery → repair_in_progress":    t("Repair in progress"),
  };
  if (m.kind === "recovery" && recoveryMap[raw]) return recoveryMap[raw];
  if (m.kind === "attachment") {
    const aType = m.attachment_type || "photo";
    return `${t("Photo attached")} · ${aType}`;
  }
  // Last resort: pass the raw label through useT (no-op if no key).
  return t(raw);
}

export default function OperationalMomentsRail({ assignmentId, tenantOverride }) {
  const { t } = useT();
  const [moments, setMoments] = useState(null); // null = loading
  const [error, setError] = useState("");

  useEffect(() => {
    if (!assignmentId) return;
    let cancelled = false;
    setMoments(null);
    setError("");
    const headers = _portalHeaders();
    if (tenantOverride) headers["X-Tenant-Id"] = tenantOverride;
    fetch(
      `${API}/api/dispatch/operational-moments/by-assignment/${encodeURIComponent(assignmentId)}`,
      { headers },
    )
      .then((r) => r.ok ? r.json() : r.json().then((b) => { throw new Error(b?.detail || `HTTP ${r.status}`); }))
      .then((data) => {
        if (cancelled) return;
        setMoments(Array.isArray(data?.moments) ? data.moments : []);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e?.message || e));
        setMoments([]);
      });
    return () => { cancelled = true; };
  }, [assignmentId, tenantOverride]);

  const sorted = useMemo(() => moments || [], [moments]);

  if (moments === null) {
    return (
      <div
        className="px-5 py-4 text-xs text-slate-500"
        data-testid="moments-rail-loading"
      >
        {t("Loading operational moments…")}
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="px-5 py-3 text-xs text-rose-700 bg-rose-50 border-y border-rose-200"
        data-testid="moments-rail-error"
      >
        {error}
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div
        className="px-5 py-4 text-xs text-slate-500"
        data-testid="moments-rail-empty"
      >
        {t("No operational moments captured yet.")}
      </div>
    );
  }

  return (
    <ol
      className="space-y-0 px-5 py-2"
      data-testid="moments-rail-list"
    >
      {sorted.map((m, idx) => {
        const vis = KIND_VISUAL[m.kind] || KIND_VISUAL.lifecycle;
        const { Icon } = vis;
        return (
          <li
            key={`${m.ts || idx}-${m.source}-${idx}`}
            data-testid={`moment-row-${idx}`}
            className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-b-0"
          >
            <div className={`mt-0.5 w-7 h-7 shrink-0 rounded-full bg-white border ${vis.ring} flex items-center justify-center`}>
              <Icon className={`w-3.5 h-3.5 ${vis.accent}`} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <div className={`text-sm font-medium ${vis.accent} truncate`}>
                  {_labelFor(t, m)}
                </div>
                <div className="text-[10px] uppercase tracking-wide text-slate-400 shrink-0">
                  <Clock className="inline-block w-2.5 h-2.5 mr-0.5 -mt-0.5" />
                  {_fmt(m.ts)}
                </div>
              </div>
              {(m.actor || m.actor_role) ? (
                <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                  {[m.actor, m.actor_role].filter(Boolean).join(" · ")}
                </div>
              ) : null}
              {m.detail ? (
                <div className="text-xs text-slate-600 mt-1 whitespace-pre-wrap leading-relaxed">
                  {m.detail}
                </div>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
