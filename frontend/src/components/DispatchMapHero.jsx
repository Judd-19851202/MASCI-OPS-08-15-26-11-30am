// DispatchMapHero.jsx — Track 13.2 · §2 Dispatch Real Map Embed.
//
// Wraps the certified MapLibre `MapCanvas` in a fixed-height (320 px)
// read-only hero that lives at the TOP of the Dispatch first screen.
// Re-uses the existing `useMapSnapshot` hook (15-s refresh) so we
// inherit the certified data pipeline, feed_status semantics, asset
// clustering, geofences, and tile style — no duplicate map logic.
//
// Interaction model on the hero (kept deliberately simple to avoid
// regression vs. the full /operations-map page):
//   • Asset click → navigate to /operations-map?asset=<unit>
//     (the full page already supports the `?asset=` deep-link)
//   • Counts strip → click any tile to open /operations-map
//   • Two CTAs below the map: "Open Full Live Map" + "Open Board"
//
// No editing on the preview map.

import React, { useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import MapCanvas from "@/components/operations-map/MapCanvas";
import { useMapSnapshot } from "@/lib/operations-map/useMapSnapshot";
import {
  AlertTriangle, CircleSlash, CheckCircle2, Clock, Boxes, Activity, ExternalLink, Map as MapIcon,
} from "lucide-react";
import { useT } from "@/lib/i18n";

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

const EMPTY_FILTERS = { types: [], status: [], driver: null, project: null };

export default function DispatchMapHero({ className = "" }) {
  const { t } = useT();
  const navigate = useNavigate();
  const { data, loading, lastFetchMs } = useMapSnapshot({ refreshMs: 15000 });

  const tiles = data?.operational_summary || [];
  const feed = data?.feed_status || {};
  const updated = lastFetchMs
    ? new Date(lastFetchMs).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "—";

  const feedTone =
    feed.status === "live" ? "emerald"
    : feed.status === "stale" ? "amber"
    : "rose";

  const snapshot = useMemo(() => ({
    assets: data?.assets || [],
    geofences: data?.geofences || [],
    counts: data?.counts || {},
  }), [data]);

  function handleAssetSelect(unit) {
    if (!unit) return;
    navigate(`/operations-map?asset=${encodeURIComponent(unit)}`);
  }

  return (
    <section
      className={`bg-white border-2 border-orange-300 rounded-md overflow-hidden ${className}`}
      data-testid="dispatch-map-hero"
    >
      {/* Header strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 border-b-2 border-orange-200 bg-orange-50">
        <div className="flex items-center gap-2">
          <MapIcon className="w-4 h-4 text-orange-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold text-orange-800">
            {t("Live Fleet Map")}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider">
          <span
            data-testid="dispatch-map-feed-status"
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 border ${TONE_CLS[feedTone]}`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            {feed.label || (loading ? t("Loading") : t("Status unknown"))}
          </span>
          <span className="text-slate-500" data-testid="dispatch-map-as-of">
            {t("Updated")} {updated}
          </span>
        </div>
      </div>

      {/* Real map canvas */}
      <div
        className="relative w-full"
        style={{ height: "320px" }}
        data-testid="dispatch-map-canvas-wrap"
      >
        {loading && !data ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm font-mono">
            {t("Loading live fleet positions…")}
          </div>
        ) : (
          <MapCanvas
            snapshot={snapshot}
            filters={EMPTY_FILTERS}
            onSelect={handleAssetSelect}
          />
        )}
      </div>

      {/* Counts strip — every tile click-throughs to full map */}
      {tiles.length > 0 && (
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-1 p-2 bg-slate-50 border-t border-orange-200">
          {tiles.map((tile) => {
            const Icon = ICON_BY_ID[tile.id] || Activity;
            const cls = TONE_CLS[tile.tone] || TONE_CLS.slate;
            return (
              <Link
                key={tile.id}
                to="/operations-map"
                data-testid={`dispatch-map-tile-${tile.id}`}
                className={`group border rounded-md p-2 transition-colors hover:border-slate-500 ${cls}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="font-mono text-[9px] uppercase tracking-[0.18em] font-bold opacity-80 truncate">
                    {tile.label}
                  </div>
                  <Icon className="w-3 h-3 opacity-70 shrink-0" />
                </div>
                <div className="text-xl font-display font-black tabular-nums">{tile.value}</div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Hero CTAs */}
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-t border-orange-200">
        <Link
          to="/operations-map"
          data-testid="dispatch-map-open-full"
          className="inline-flex items-center min-h-[44px] px-4 rounded-md bg-orange-600 hover:bg-orange-500 text-white font-black tracking-wide text-sm"
        >
          <Activity className="w-4 h-4 mr-2" />
          {t("Open Full Live Map")}
        </Link>
        <Link
          to="/dispatch-portal/board"
          data-testid="dispatch-map-open-board"
          className="inline-flex items-center min-h-[40px] px-4 rounded-md border-2 border-orange-300 hover:border-orange-500 text-orange-800 font-bold tracking-wide text-sm"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          {t("Open Operational Board")}
        </Link>
      </div>
    </section>
  );
}
