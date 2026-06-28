/**
 * TRACK 16.16 · Operations × Transportation Integration Layer.
 *
 * Four read-only operational-awareness components that consume the
 * existing `GET /api/operations/transportation/readiness` envelope
 * (Track 16.16 backend route). Mounted inside:
 *
 *   - PmProjectDetail.jsx           → ReadinessCard + RiskBanner + CloseoutAwareness
 *   - OperationsCenterCommand.jsx   → HealthWidget
 *   - PmCommandCenter.jsx           → HealthWidget (Overview tab)
 *
 * Doctrine:
 *   - Pure consumer. NO new business logic.
 *   - Calm, operator-first surfaces. Banner stays SILENT when fleet
 *     is healthy (no warning fatigue).
 *   - Cross-portal-token aware via the shared `api` axios helper.
 *   - One fetch per page hop. Lightweight in-component caching only.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Truck, AlertTriangle, CheckCircle2, ExternalLink, Activity,
  ShieldAlert, RefreshCw, ChevronRight, Building2, Users,
} from "lucide-react";
import { api } from "@/lib/api";

const ENDPOINT = "/operations/transportation/readiness";
const TX_HREF = "/admin/transportation";
const CLEANUP_HREF = "/admin/transportation/intelligence/cleanup";

// Module-level shared in-flight cache. Three components on the same
// page (PmProjectDetail mounts ReadinessCard + RiskBanner +
// CloseoutAwareness) would otherwise fire three parallel requests.
// We coalesce them into ONE request per CACHE_TTL_MS window.
const CACHE_TTL_MS = 30_000;
const _readinessCache = { ts: 0, data: null, inflight: null };

async function _fetchReadiness() {
  const now = Date.now();
  if (_readinessCache.data && (now - _readinessCache.ts) < CACHE_TTL_MS) {
    return _readinessCache.data;
  }
  if (_readinessCache.inflight) {
    return _readinessCache.inflight;
  }
  _readinessCache.inflight = api.get(ENDPOINT).then((r) => {
    _readinessCache.data = r.data;
    _readinessCache.ts = Date.now();
    _readinessCache.inflight = null;
    return r.data;
  }).catch((e) => {
    _readinessCache.inflight = null;
    throw e;
  });
  return _readinessCache.inflight;
}

const BAND_PALETTE = {
  green:   "bg-emerald-100 text-emerald-800 border-emerald-300",
  yellow:  "bg-amber-100 text-amber-900 border-amber-300",
  red:     "bg-rose-100 text-rose-800 border-rose-300",
  unknown: "bg-slate-100 text-slate-700 border-slate-300",
};

const SEV_PALETTE = {
  action_required: "bg-rose-50 text-rose-800 border-rose-300",
  watch:           "bg-amber-50 text-amber-900 border-amber-300",
};

/**
 * Lightweight shared fetch hook. One in-flight request per mount.
 */
export function useTransportationReadiness() {
  const [state, setState] = useState({
    data: null, error: null, loading: true,
  });

  const load = useCallback(async () => {
    try {
      const data = await _fetchReadiness();
      setState({ data, error: null, loading: false });
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || "load failed";
      setState({ data: null, error: msg, loading: false });
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const reload = useCallback(async () => {
    _readinessCache.ts = 0;
    _readinessCache.data = null;
    await load();
  }, [load]);

  return { ...state, reload };
}

function BandChip({ band, testid }) {
  if (!band) return null;
  const label = band.label || band.grade || "unknown";
  const palette = BAND_PALETTE[label] || BAND_PALETTE.unknown;
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-medium ${palette}`}
    >
      {String(label).toUpperCase()}
      {band.score !== undefined && band.score !== null ? ` · ${band.score}` : ""}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * 1. TransportationReadinessCard
 *    Mounted inside per-project workspaces (PmProjectDetail).
 *    Operator-first: one glance answers "is Transportation ready?".
 * ────────────────────────────────────────────────────────────── */
export function TransportationReadinessCard() {
  const { data, error, loading, reload } = useTransportationReadiness();

  if (loading && !data) {
    return (
      <section
        data-testid="ops-tx-readiness-loading"
        className="bg-white border border-slate-200 rounded-md p-4 text-xs text-slate-500"
      >
        Loading Transportation readiness…
      </section>
    );
  }

  if (error) {
    return (
      <section
        data-testid="ops-tx-readiness-error"
        className="bg-white border border-slate-200 rounded-md p-4 text-xs text-slate-500"
      >
        Transportation readiness unavailable.
      </section>
    );
  }

  const snap = data?.snapshot || {};
  const cleanup = data?.cleanup || {};
  const overall = data?.overall_readiness || {};

  return (
    <section
      data-testid="ops-tx-readiness-card"
      className="bg-white border border-slate-200 rounded-md p-4"
    >
      <header className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4 text-slate-500" />
          <h3
            data-testid="ops-tx-readiness-title"
            className="text-sm font-semibold text-slate-900"
          >
            Transportation Readiness
          </h3>
          <BandChip band={overall} testid="ops-tx-readiness-overall" />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={reload}
            data-testid="ops-tx-readiness-refresh"
            className="text-[11px] text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
            title="Refresh"
          >
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
          <Link
            to={TX_HREF}
            data-testid="ops-tx-readiness-view-link"
            className="inline-flex items-center text-[11px] font-medium text-amber-700 hover:text-amber-900"
          >
            View Transportation <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <Tile testid="ops-tx-tile-drivers"  label="Drivers"
              value={snap.available_drivers}  icon={Users} />
        <Tile testid="ops-tx-tile-trucks"   label="Trucks"
              value={snap.available_trucks}   icon={Truck} />
        <Tile testid="ops-tx-tile-carriers" label="Carriers"
              value={snap.available_carriers} icon={Building2} />
        <Tile testid="ops-tx-tile-risks"    label="Open Risks"
              value={data?.risks?.length || 0}
              icon={AlertTriangle}
              tone={(data?.risks?.length || 0) > 0 ? "amber" : null} />
        <Tile testid="ops-tx-tile-cleanup"  label="Action Items"
              value={snap.open_action_items || 0}
              icon={Activity}
              tone={(snap.open_action_items || 0) > 0 ? "amber" : null} />
        <Tile testid="ops-tx-tile-dispatch" label="Dispatch"
              value={(data?.dispatch_readiness?.score ?? 0).toString().split(".")[0]}
              suffix="%"
              icon={Truck} />
      </div>

      <div className="mt-3 text-[10px] uppercase tracking-wide text-slate-400">
        Source · Transportation engines · Tracks 16.06 / 16.10 / 16.11A / 16.12 / 16.15
      </div>
    </section>
  );
}

function Tile({ testid, label, value, suffix, icon: Icon, tone }) {
  const toneCls =
    tone === "amber" ? "border-amber-300 bg-amber-50 text-amber-900"
    : tone === "rose" ? "border-rose-300 bg-rose-50 text-rose-900"
    : "border-slate-200 bg-white text-slate-900";
  return (
    <div
      data-testid={testid}
      className={`border rounded-md p-2 ${toneCls}`}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="text-[10px] uppercase tracking-wide opacity-70">{label}</div>
        {Icon ? <Icon className="h-3.5 w-3.5 opacity-60" /> : null}
      </div>
      <div className="text-lg font-semibold leading-none">
        {value ?? 0}{suffix || ""}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * 2. TransportationRiskBanner
 *    Silent when fleet is healthy — only renders when ≥1 risk.
 * ────────────────────────────────────────────────────────────── */
export function TransportationRiskBanner() {
  const { data, loading, error } = useTransportationReadiness();
  if (loading || error || !data) return null;
  const risks = data.risks || [];
  if (risks.length === 0) {
    // Silent — no warning fatigue when nothing is wrong.
    return null;
  }

  // Worst severity wins for tone.
  const hasActionRequired = risks.some((r) => r.severity === "action_required");
  const palette = hasActionRequired
    ? "border-rose-300 bg-rose-50 text-rose-900"
    : "border-amber-300 bg-amber-50 text-amber-900";

  return (
    <section
      data-testid="ops-tx-risk-banner"
      className={`rounded-md border p-3 ${palette}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <ShieldAlert className="h-4 w-4" />
        <div className="text-xs font-semibold uppercase tracking-wide">
          Transportation risks · {risks.length}
        </div>
        <Link
          to={TX_HREF}
          data-testid="ops-tx-risk-banner-link"
          className="ml-auto text-[11px] underline-offset-2 hover:underline inline-flex items-center"
        >
          Open Transportation <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
      <ul className="space-y-1" data-testid="ops-tx-risk-list">
        {risks.map((r, i) => (
          <li
            key={r.code || i}
            data-testid={`ops-tx-risk-item-${i}`}
            className="flex items-start gap-2 text-xs"
          >
            <span
              data-testid={`ops-tx-risk-severity-${i}`}
              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] border ${SEV_PALETTE[r.severity] || SEV_PALETTE.watch}`}
            >
              {String(r.severity).replace("_", " ")}
            </span>
            <span>{r.label}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * 3. OperationsTransportationHealthWidget
 *    Compact widget for OperationsCenterCommand + PmCommandCenter.
 * ────────────────────────────────────────────────────────────── */
export function OperationsTransportationHealthWidget() {
  const { data, loading, error } = useTransportationReadiness();

  if (loading && !data) {
    return (
      <section
        data-testid="ops-tx-health-widget-loading"
        className="bg-white border border-slate-200 rounded-md p-3 text-xs text-slate-500"
      >
        Loading Transportation health…
      </section>
    );
  }
  if (error) {
    return (
      <section
        data-testid="ops-tx-health-widget-error"
        className="bg-white border border-slate-200 rounded-md p-3 text-xs text-slate-500"
      >
        Transportation health unavailable.
      </section>
    );
  }

  const overall = data?.overall_readiness || {};
  const snap = data?.snapshot || {};
  const cleanup = data?.cleanup || {};

  return (
    <section
      data-testid="ops-tx-health-widget"
      className="bg-white border border-slate-200 rounded-md p-3"
    >
      <header className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-slate-900">Transportation Health</h3>
          <BandChip band={overall} testid="ops-tx-health-widget-band" />
        </div>
        <Link
          to={TX_HREF}
          data-testid="ops-tx-health-widget-link"
          className="text-[11px] font-medium text-amber-700 hover:text-amber-900 inline-flex items-center"
        >
          Open Transportation <ExternalLink className="h-3 w-3 ml-1" />
        </Link>
      </header>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Tile testid="ops-tx-health-tile-blocked" label="Blocked Dispatch"
              value={snap.blocked_dispatches || 0} icon={AlertTriangle}
              tone={(snap.blocked_dispatches || 0) > 0 ? "rose" : null} />
        <Tile testid="ops-tx-health-tile-pending" label="Pending Reviews"
              value={snap.pending_reviews || 0} icon={Activity}
              tone={(snap.pending_reviews || 0) > 0 ? "amber" : null} />
        <Tile testid="ops-tx-health-tile-expiring" label="Expiring 30d"
              value={snap.upcoming_expirations_30d || 0} icon={Activity}
              tone={(snap.upcoming_expirations_30d || 0) > 0 ? "amber" : null} />
        <Tile testid="ops-tx-health-tile-cleanup" label="Action Items"
              value={snap.open_action_items || 0} icon={Activity}
              tone={(snap.open_action_items || 0) > 0 ? "amber" : null} />
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * 4. TransportationCloseoutAwareness
 *    Bottom-of-workspace card. Renders unresolved TX issues OR a
 *    calm "Transportation Complete" badge.
 * ────────────────────────────────────────────────────────────── */
export function TransportationCloseoutAwareness() {
  const { data, loading, error } = useTransportationReadiness();

  if (loading || error || !data) return null;

  const snap = data.snapshot || {};
  const unresolvedCounts = [
    { key: "blocked_dispatches",     label: "Blocked dispatches",
      value: snap.blocked_dispatches || 0 },
    { key: "pending_reviews",        label: "Pending reviews",
      value: snap.pending_reviews || 0 },
    { key: "documents_awaiting",     label: "Documents awaiting review",
      value: snap.documents_awaiting_review || 0 },
    { key: "open_action_items",      label: "Open action items",
      value: snap.open_action_items || 0 },
    { key: "upcoming_expirations",   label: "Documents expiring 30d",
      value: snap.upcoming_expirations_30d || 0 },
  ].filter((row) => row.value > 0);

  if (unresolvedCounts.length === 0) {
    return (
      <section
        data-testid="ops-tx-closeout-complete"
        className="rounded-md border border-emerald-200 bg-emerald-50 p-3"
      >
        <div className="flex items-center gap-2 text-emerald-900">
          <CheckCircle2 className="h-4 w-4" />
          <div className="text-sm font-medium">Transportation Complete</div>
        </div>
        <div className="text-[10px] uppercase tracking-wide text-emerald-700 mt-1">
          No unresolved Transportation issues.
        </div>
      </section>
    );
  }

  return (
    <section
      data-testid="ops-tx-closeout-unresolved"
      className="rounded-md border border-amber-200 bg-amber-50 p-3"
    >
      <div className="flex items-center gap-2 mb-2 text-amber-900">
        <AlertTriangle className="h-4 w-4" />
        <div className="text-sm font-medium">
          Unresolved Transportation items
        </div>
        <Link
          to={TX_HREF}
          data-testid="ops-tx-closeout-link"
          className="ml-auto text-[11px] underline-offset-2 hover:underline inline-flex items-center"
        >
          Open Transportation <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-xs text-amber-900">
        {unresolvedCounts.map((row, i) => (
          <li
            key={row.key}
            data-testid={`ops-tx-closeout-row-${row.key}`}
            className="flex items-center justify-between border-b border-amber-200/60 py-1"
          >
            <span>{row.label}</span>
            <span className="font-mono">{row.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
