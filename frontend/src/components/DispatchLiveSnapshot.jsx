// DispatchLiveSnapshot.jsx — Live Fleet snapshot strip for Dispatch hub.
//
// Track 13 · §3 Dispatch Live Map Hero Fix.
//
// Previously the Dispatch hub had a "Live Operational Board" section
// with a single orange button to open the full map page. A dispatcher
// could not see fleet truth at a glance — they had to click.
//
// This component embeds the operations-map snapshot counts (Attention
// Required · No Recent Position · Working · Idle · Total Assets) +
// a feed-status pill + last-updated timestamp directly above the
// existing button, so a dispatcher answers all five Track-13C role
// questions in one glance.
//
// No new endpoints. Reuses `/api/operations-map/snapshot` (already
// guardrail-locked by Track 6).

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CircleSlash, CheckCircle2, Clock, Boxes, Activity, RefreshCcw, ExternalLink } from "lucide-react";
import { useT } from "@/lib/i18n";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function _authHeaders() {
  const t =
    sessionStorage.getItem("masci.dispatch.token") ||
    sessionStorage.getItem("masci.admin.token") ||
    "";
  return t ? { "X-Admin-Token": t } : {};
}

const ICON_BY_ID = {
  attention: AlertTriangle,
  offline: CircleSlash,
  working: CheckCircle2,
  idle: Clock,
  assigned: Boxes,
  total: Activity,
};
const TONE_CLS = {
  rose:    "border-rose-300 bg-rose-50 text-rose-800",
  amber:   "border-amber-300 bg-amber-50 text-amber-800",
  emerald: "border-emerald-300 bg-emerald-50 text-emerald-800",
  slate:   "border-slate-200 bg-white text-slate-800",
};

export default function DispatchLiveSnapshot({ className = "" }) {
  const { t } = useT();
  const [snap, setSnap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${API}/operations-map/snapshot`, { headers: _authHeaders() })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (!cancelled) { setSnap(data); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [tick]);

  const tiles = snap?.operational_summary || [];
  const feed = snap?.feed_status || {};
  const asOf = snap?.last_updated_at || snap?.as_of || null;
  const asOfDisplay = asOf ? formatPlatformTimeOnly(asOf) : "—";
  const feedTone =
    feed.status === "live" ? "emerald"
    : feed.status === "stale" ? "amber"
    : "rose";

  return (
    <section
      className={`bg-white border-2 border-orange-300 rounded-md p-4 sm:p-5 ${className}`}
      data-testid="dispatch-live-snapshot"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold text-orange-700">
          {t("Live Fleet Snapshot")}
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider">
          <span
            data-testid="dispatch-feed-status"
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 border ${TONE_CLS[feedTone]}`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current"/>
            {feed.label || t("Status unknown")}
          </span>
          <span className="text-slate-500" data-testid="dispatch-snapshot-as-of">
            {t("Updated")} {asOfDisplay}
          </span>
          <button
            type="button"
            onClick={() => setTick((x) => x + 1)}
            className="inline-flex items-center min-h-[44px] min-w-[44px] justify-center rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100"
            aria-label={t("Refresh")}
            data-testid="dispatch-snapshot-refresh"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 animate-pulse">
          {[1,2,3,4,5,6].map((i) => (
            <div key={i} className="h-20 bg-slate-100 border border-slate-200 rounded-md" />
          ))}
        </div>
      ) : tiles.length === 0 ? (
        <div className="text-sm text-slate-600 py-3">
          {t("No live fleet signal right now.")} {" "}
          <Link to="/dispatch-portal/map" className="text-orange-700 hover:underline font-bold">
            {t("Open full Live Map")} →
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {tiles.map((tile) => {
            const Icon = ICON_BY_ID[tile.id] || Activity;
            const cls = TONE_CLS[tile.tone] || TONE_CLS.slate;
            return (
              <Link
                key={tile.id}
                to="/dispatch-portal/map"
                data-testid={`dispatch-snapshot-tile-${tile.id}`}
                className={`group border rounded-md p-3 transition-colors hover:border-slate-400 ${cls}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold opacity-80 truncate">
                    {tile.label}
                  </div>
                  <Icon className="w-3.5 h-3.5 opacity-70 shrink-0" />
                </div>
                <div className="text-2xl font-display font-black tabular-nums">{tile.value}</div>
              </Link>
            );
          })}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Link
          to="/dispatch-portal/map"
          data-testid="dispatch-live-map-open"
          className="inline-flex items-center min-h-[48px] px-5 rounded-md bg-orange-600 hover:bg-orange-500 text-white font-black tracking-wide"
        >
          <Activity className="w-5 h-5 mr-2" />
          {t("Open Full Live Map")}
        </Link>
        <Link
          to="/dispatch-portal/board"
          data-testid="dispatch-board-link-inline"
          className="inline-flex items-center min-h-[44px] px-4 rounded-md border-2 border-orange-300 hover:border-orange-500 text-orange-800 font-bold tracking-wide"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          {t("Open Operational Board")}
        </Link>
      </div>
    </section>
  );
}
