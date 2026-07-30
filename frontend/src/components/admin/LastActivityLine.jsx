// LastActivityLine.jsx — iter440 · per-portal calm activity indicator.
//
// Single-line read-only "Last submission · N min ago" indicator that
// sits unobtrusively on each role hub. Quiet proof the platform is
// being USED, not just UP.
//
// Doctrine
// --------
// - One line · NEVER a card · NEVER a chart · NEVER a stack
// - Renders nothing if there's no activity in the last 7 days
// - Renders nothing on auth failure (silent · operational continuity)
// - Polls every 60 s while mounted
// - Color: muted slate (NOT amber, NOT green, NOT red) — it's a
//   calm fact, not an alert
// - Same font + spacing as `<FieldMemoryGlance />` so it feels like
//   it's been there since day 1.

import React, { useEffect, useState, useCallback } from "react";
import { Activity } from "lucide-react";
import { useT } from "@/lib/i18n";
import { buildPortalAuthHeaders } from "@/lib/authHeaders";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 60 * 1000;

function _portalHeaders() {
  return buildPortalAuthHeaders();
}

function _hasAnyPortalToken() {
  return Object.keys(_portalHeaders()).length > 0;
}

function _relative(iso, t) {
  if (!iso) return "";
  try {
    const then = new Date(iso).getTime();
    const now = Date.now();
    const mins = Math.max(0, Math.round((now - then) / 60000));
    if (mins < 1) return t("just now");
    if (mins < 60) return `${mins} ${t("min ago")}`;
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return `${hrs} ${t("hr ago")}`;
    const days = Math.round(hrs / 24);
    return `${days} ${t("d ago")}`;
  } catch {
    return "";
  }
}

export default function LastActivityLine({ portal, testId }) {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    if (!_hasAnyPortalToken()) { setLoaded(true); return; }
    try {
      const res = await fetch(
        `${API}/api/diag/last-activity?portal=${encodeURIComponent(portal)}`,
        { headers: _portalHeaders() },
      );
      if (!res.ok) { setLoaded(true); setData(null); return; }
      const body = await res.json();
      setData(body && body.last_activity_at ? body : null);
      setLoaded(true);
    } catch {
      setLoaded(true);
      setData(null);
    }
  }, [portal]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  // Doctrine: render NOTHING when no data · no auth · or loading.
  if (!loaded) return null;
  if (!data || !data.last_activity_at) return null;

  return (
    <div
      data-testid={testId || `last-activity-line-${portal}`}
      className="flex items-center gap-1.5 text-xs text-slate-500"
    >
      <Activity className="w-3 h-3" aria-hidden="true" />
      <span>
        <span className="font-medium text-slate-600">
          {t(data.label || "Activity")}
        </span>
        <span className="text-slate-400 mx-1">·</span>
        <span>{_relative(data.last_activity_at, t)}</span>
      </span>
    </div>
  );
}
