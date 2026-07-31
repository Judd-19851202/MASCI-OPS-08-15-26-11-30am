// StorageObservabilityCard.jsx — iter437 · Phase Sigma-III · P1
//
// Calm operational read-only widget for /admin/database.
// Renders a single SVG sparkline + a one-line runway summary.
//
// Doctrine (user-confirmed):
//   - Pure inline SVG (no chart library · no animation · no hover-heavy UX)
//   - Mobile-safe (responds to container width via viewBox)
//   - Accessible: <title> + aria-label
//   - Fallback text when history data is unavailable
//   - Operational display only: "+5.5 MB/day · ~1696d runway"
//   - NEVER alerts, NEVER red/amber until severity flips at backend

import React, { useEffect, useMemo, useState } from "react";
import { Database, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { HelpTip } from "@/components/ui/HelpTip";
import { buildKpiHelpContent } from "@/lib/kpiMetadata";

// ---------------------------------------------------------------------
// Sparkline — pure SVG, takes a numeric array, produces a polyline.
// Designed for storage_used_mb history, but accepts any series.
// ---------------------------------------------------------------------
function Sparkline({ values, width = 240, height = 36, label = "" }) {
  if (!values || values.length < 2) {
    return (
      <div
        className="text-xs text-slate-400 font-mono"
        data-testid="storage-sparkline-empty"
      >
        not enough samples yet
      </div>
    );
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 0.01); // avoid div-by-zero on flat line
  const stepX = width / (values.length - 1);

  const points = values
    .map((v, i) => {
      const x = i * stepX;
      // Invert Y because SVG origin is top-left
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      preserveAspectRatio="none"
      role="img"
      aria-label={label || "storage sparkline"}
      data-testid="storage-sparkline-svg"
      className="block"
    >
      <title>{label || "storage sparkline"}</title>
      {/* baseline (very subtle) */}
      <line
        x1="0"
        y1={height - 0.5}
        x2={width}
        y2={height - 0.5}
        stroke="#e2e8f0"
        strokeWidth="1"
      />
      <polyline
        points={points}
        fill="none"
        stroke="#475569"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* terminal dot */}
      <circle
        cx={(values.length - 1) * stepX}
        cy={height - ((values[values.length - 1] - min) / range) * height}
        r="2"
        fill="#0f172a"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------
function fmtSlope(slope) {
  if (slope === null || slope === undefined) return "—";
  const sign = slope >= 0 ? "+" : "";
  return `${sign}${slope.toFixed(1)} MB/day`;
}

function fmtRunway(days) {
  if (days === null || days === undefined) return "—";
  if (days >= 365 * 5) return `>5y runway`;
  if (days >= 365) return `~${(days / 365).toFixed(1)}y runway`;
  if (days >= 60) return `~${Math.round(days)}d runway`;
  return `~${days.toFixed(1)}d runway`;
}

function fmtMb(v) {
  if (v === null || v === undefined) return "—";
  if (v >= 1024) return `${(v / 1024).toFixed(2)} GB`;
  return `${v.toFixed(1)} MB`;
}

// ---------------------------------------------------------------------
// Main card
// ---------------------------------------------------------------------
export default function StorageObservabilityCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setErr(null);
      try {
        const r = await api.get("/cluster/capacity/history?days=30");
        if (!cancelled) setData(r.data);
      } catch (e) {
        if (!cancelled) setErr(e?.message || "fetch failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    // Refresh once an hour while the page stays open — backend snapshots
    // every hour so anything tighter is wasted work.
    const t = setInterval(load, 60 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  const series = useMemo(() => {
    if (!data?.rows) return [];
    return data.rows
      .map((r) => Number(r.storage_used_mb))
      .filter((v) => Number.isFinite(v));
  }, [data]);

  const summary = useMemo(() => {
    if (!data) return null;
    return {
      first: data.first_mb,
      last: data.last_mb,
      slope: data.slope_mb_per_day,
      runway: data.days_to_quota,
      samples: data.samples,
      days: data.days,
      predictive: data.predictive || {},
      metadata: data.kpi_metadata || null,
    };
  }, [data]);

  const help = useMemo(() => buildKpiHelpContent(summary?.metadata, "Atlas Capacity Forecast"), [summary]);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-4"
      data-testid="storage-observability-card"
      aria-label="Storage observability"
    >
      <header className="flex items-center gap-2 mb-2">
        <Database className="w-4 h-4 text-slate-600" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold text-slate-600">
          Storage Trend · last {summary?.days ?? 30}d
        </span>
        {help ? <HelpTip label={help.label} body={help.body} testId="storage-card-help" /> : null}
        {loading && (
          <Loader2
            className="w-3 h-3 animate-spin text-slate-400 ml-auto"
            data-testid="storage-card-loading"
          />
        )}
      </header>

      {err ? (
        <p
          className="text-xs text-slate-500 font-mono"
          data-testid="storage-card-error"
        >
          history unavailable · {err}
        </p>
      ) : !summary ? (
        <p
          className="text-xs text-slate-400 font-mono"
          data-testid="storage-card-empty"
        >
          warming up…
        </p>
      ) : summary.samples < 2 ? (
        <p
          className="text-xs text-slate-500 font-mono"
          data-testid="storage-card-not-enough-samples"
        >
          {summary.samples ?? 0} sample{summary.samples === 1 ? "" : "s"} · not enough yet
        </p>
      ) : (
        <div className="space-y-2">
          <Sparkline
            values={series}
            label={`storage usage · last ${summary.days}d`}
          />
          <div
            className="text-xs text-slate-700 font-mono leading-tight"
            data-testid="storage-card-summary"
          >
            {fmtMb(summary.last)} · {fmtSlope(summary.slope)} · {fmtRunway(summary.runway)}
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-500 font-mono" data-testid="storage-card-predictive-grid">
            <div data-testid="storage-card-daily-growth">daily {fmtSlope(summary.predictive?.daily_growth_rate_mb)}</div>
            <div data-testid="storage-card-weekly-growth">weekly {fmtSlope(summary.predictive?.weekly_growth_rate_mb)}</div>
            <div data-testid="storage-card-monthly-growth">monthly {fmtSlope(summary.predictive?.monthly_growth_rate_mb)}</div>
            <div data-testid="storage-card-prediction-quality">quality {summary.predictive?.prediction_quality || "—"}</div>
          </div>
          {summary.predictive?.projected_exhaustion_date ? (
            <div className="text-[10px] text-slate-500 font-mono" data-testid="storage-card-exhaustion-date">
              projected exhaustion · {summary.predictive.projected_exhaustion_date}
            </div>
          ) : null}
          {Array.isArray(summary.predictive?.recommendations) && summary.predictive.recommendations.length ? (
            <div className="text-[10px] text-slate-500" data-testid="storage-card-recommendations">
              {summary.predictive.recommendations[0]}
            </div>
          ) : null}
          <div
            className="text-[10px] text-slate-400 font-mono"
            data-testid="storage-card-meta"
          >
            {summary.samples} samples · from {fmtMb(summary.first)} → {fmtMb(summary.last)}
          </div>
        </div>
      )}
    </section>
  );
}
