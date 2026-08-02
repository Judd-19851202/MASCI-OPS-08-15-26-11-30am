/**
 * TRACK 18.00 · Phase B · Mission Control.
 *
 * Default landing experience for Transportation Operations. Every
 * card answers exactly ONE of these eight operator-facing questions:
 *
 *   1. Fleet Ready?         5. Anything Blocking?
 *   2. Drivers Ready?       6. What Changed Today?
 *   3. Carriers Ready?      7. What Needs Attention?
 *   4. Dispatch Healthy?    8. What Should We Do Next?
 *
 * Doctrine (locked):
 *   - Mission Control composes existing engines. It owns NOTHING.
 *   - No new backend endpoints. No new scoring. No new collections.
 *   - All data is pulled from:
 *       · `/api/operations/transportation/readiness` (Track 16.16)
 *       · `/api/admin/transportation/audit-timeline` (Track 16.07)
 *       · `/api/admin/transportation/dashboard` (Track 16.07)
 *       · `/api/admin/hr/transportation-readiness` (Track 16.11A)
 *   - Every card has a deep link into its source workspace.
 *   - Dispatch is linked, never embedded.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Truck, Users, Building2, Activity, ShieldAlert, Clock, Inbox,
  Sparkles, RefreshCw, ChevronRight, CheckCircle2, AlertTriangle,
} from "lucide-react";
import { txGet, useTxPathPrefix } from "./_shared";
import { useTransportationReadiness } from "@/components/operations_transportation_integration";
import { useT } from "@/lib/i18n";

const BAND_PALETTE = {
  green:   "bg-emerald-100 text-emerald-800 border-emerald-300",
  yellow:  "bg-amber-100 text-amber-900 border-amber-300",
  red:     "bg-rose-100 text-rose-800 border-rose-300",
  unknown: "bg-slate-100 text-slate-700 border-slate-300",
};

function BandChip({ band, testid }) {
  const { t } = useT();
  if (!band) return null;
  const label = band.label || "unknown";
  const palette = BAND_PALETTE[label] || BAND_PALETTE.unknown;
  const labelMap = {
    green: t("GREEN"),
    yellow: t("YELLOW"),
    red: t("RED"),
    unknown: t("UNKNOWN"),
  };
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-medium ${palette}`}
    >
      {labelMap[label] || String(label).toUpperCase()}
      {band.score !== undefined && band.score !== null ? ` · ${band.score}` : ""}
    </span>
  );
}

function MissionBrief({ overall, riskCount }) {
  const { t } = useT();
  let tone = "border-emerald-200 bg-emerald-50 text-emerald-900";
  let icon = <CheckCircle2 className="h-4 w-4" />;
  let line = t("Transportation Operations is healthy. No action required.");
  const label = overall?.label || "unknown";

  if (label === "red" || riskCount >= 2) {
    tone = "border-rose-300 bg-rose-50 text-rose-900";
    icon = <ShieldAlert className="h-4 w-4" />;
    line = t("Transportation Operations requires immediate attention.");
  } else if (label === "yellow" || riskCount >= 1) {
    tone = "border-amber-300 bg-amber-50 text-amber-900";
    icon = <AlertTriangle className="h-4 w-4" />;
    line = t("Transportation Operations operating with watch items.");
  }

  return (
    <section
      data-testid="mc-mission-brief"
      className={`wp17-transport-card p-3 flex items-center gap-3 ${tone}`}
    >
      {icon}
      <div className="text-sm font-medium" data-testid="mc-mission-brief-line">{line}</div>
      <BandChip band={overall} testid="mc-mission-brief-band" />
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────
// One operational card — used by all eight Mission Control cards.
// Includes: status (band) · summary · primary KPI · secondary KPI ·
// primary action · drill-down link. Never empty.
// ─────────────────────────────────────────────────────────────────
function McCard({
  testid, question, icon: Icon, band,
  primaryKpi, primaryLabel,
  secondaryKpi, secondaryLabel,
  summary, actionLabel, actionHref, drillHref,
}) {
  const { t } = useT();
  return (
    <article
      data-testid={testid}
      className="wp17-transport-card p-4 flex flex-col gap-2 hover:border-amber-300 transition-colors"
    >
      <header className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 text-slate-500 text-[10px] uppercase tracking-wider font-semibold">
          {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
          <span>{t(question)}</span>
        </div>
        {band ? <BandChip band={band} testid={`${testid}-band`} /> : null}
      </header>
      <div className="flex items-baseline gap-3">
        <div
          className="text-3xl font-semibold text-slate-900 leading-none"
          data-testid={`${testid}-primary-kpi`}
        >
          {primaryKpi ?? 0}
        </div>
        <div className="text-xs text-slate-500">{t(primaryLabel)}</div>
      </div>
      {secondaryLabel ? (
        <div
          className="text-[11px] text-slate-500"
          data-testid={`${testid}-secondary-kpi`}
        >
          <span className="font-medium text-slate-700">{secondaryKpi ?? 0}</span> {t(secondaryLabel)}
        </div>
      ) : null}
      {summary ? (
        <div
          className="text-xs text-slate-600 mt-1"
          data-testid={`${testid}-summary`}
        >
          {summary}
        </div>
      ) : null}
      <footer className="flex items-center justify-between gap-2 mt-1 pt-2 border-t border-slate-100">
        {actionHref ? (
          <Link
            to={actionHref}
            data-testid={`${testid}-action`}
            className="inline-flex items-center text-xs text-amber-700 hover:text-amber-900 font-medium"
          >
            {t(actionLabel || "Open")} <ChevronRight className="h-3 w-3" />
          </Link>
        ) : <span />}
        {drillHref ? (
          <Link
            to={drillHref}
            data-testid={`${testid}-drilldown`}
            className="text-[11px] text-slate-500 hover:text-slate-800 inline-flex items-center"
          >
            {t("View details →")}
          </Link>
        ) : null}
      </footer>
    </article>
  );
}

// ─────────────────────────────────────────────────────────────────
// Recent activity composer — Card 6.
// Pulls existing audit-timeline (Track 16.07).
// ─────────────────────────────────────────────────────────────────
function useRecentActivity(limit = 6, enabled = true) {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    let alive = true;
    if (!enabled) {
      setRows([]);
      return () => { alive = false; };
    }
    txGet("/admin/transportation/audit-timeline", { limit }).then((r) => {
      if (alive) setRows(r.data?.rows || []);
    }).catch(() => alive && setRows([]));
    return () => { alive = false; };
  }, [enabled, limit]);
  return rows;
}

function RecentActivityCard({ prefix, canLoadAudit = true }) {
  const { t } = useT();
  const rows = useRecentActivity(6, canLoadAudit);
  const count = rows == null ? null : rows.length;
  const summary = rows == null
    ? t("Loading…")
    : !canLoadAudit
      ? t("Audit timeline is available in Admin oversight. Dispatch users stay focused on live operations here.")
    : count === 0
      ? t("No transportation activity in the last 24 hours.")
      : t("{count} most-recent events across drivers, trucks, carriers, dispatch, automation, cleanup, and HR sync.").replace("{count}", count);
  return (
    <McCard
      testid="mc-card-recent"
      question="What Changed Today?"
      icon={Clock}
      primaryKpi={!canLoadAudit ? "—" : (count ?? "—")}
      primaryLabel="recent events"
      summary={summary}
      actionLabel="Open audit timeline"
      actionHref={`${prefix}/audit`}
      drillHref={`${prefix}/audit`}
    />
  );
}

// ─────────────────────────────────────────────────────────────────
// TRACK 18.12 · Workspace Actions strip.
//
// Consistent, role-aware navigation chips so operators can jump
// between operational workspaces from Mission Control without
// re-routing through the sub-nav. The strip mirrors the sub-nav
// ordering but renders as premium cards: icon + label + short
// status hint + one obvious primary action per chip. Prefix-aware
// so dispatch users stay inside `/transportation-operations/*`
// and admin users stay inside `/admin/transportation/*`.
// ─────────────────────────────────────────────────────────────────
const WORKSPACE_STRIP = [
  { to: "dispatch", icon: Activity, label: "Dispatch", hint: "Open Dispatch" },
  { to: "drivers", icon: Users, label: "Drivers", hint: "Driver readiness" },
  { to: "carriers", icon: Building2, label: "Carriers", hint: "Carrier readiness" },
  { to: "trucks", icon: Truck, label: "Fleet", hint: "Truck readiness" },
  { to: "orientation", icon: Inbox, label: "Orientation", hint: "Onboarding queue" },
  { to: "compliance", icon: ShieldAlert, label: "Compliance", hint: "Document review" },
  { to: "live-operations", icon: Activity, label: "Live Operations", hint: "Real-time view" },
  { to: "intelligence/cleanup", icon: Sparkles, label: "Cleanup", hint: "Top opportunities" },
];

function WorkspaceStrip({ prefix }) {
  const { t } = useT();
  return (
    <section
      data-testid="mc-workspace-strip"
      aria-label={t("Operational workspaces")}
      className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2"
    >
      {WORKSPACE_STRIP.map((w) => (
        <Link
          key={w.to}
          to={`${prefix}/${w.to}`}
          data-testid={`mc-workspace-${w.to.replace(/\//g, "-")}`}
          className="group wp17-transport-card flex flex-col items-start gap-1 px-3 py-2.5 hover:border-slate-900 hover:shadow-sm transition-colors min-h-[68px]"
        >
          <div className="flex items-center gap-1.5 text-slate-900">
            <w.icon className="h-4 w-4" />
            <span className="text-xs font-semibold tracking-tight">{t(w.label)}</span>
          </div>
          <span className="text-[10.5px] text-slate-500 leading-tight">{t(w.hint)}</span>
        </Link>
      ))}
    </section>
  );
}

function translateRiskLabel(risk, t) {
  if (!risk) return "";
  const count = risk.count ?? risk.value ?? risk.total ?? 0;
  if (risk.code === "blocked_dispatches") {
    return t("{count} dispatch(es) currently blocked").replace("{count}", count);
  }
  if (risk.code === "hr_mismatch") {
    return t("{count} HR ↔ Transportation mismatch(es)").replace("{count}", count);
  }
  return t(risk.label || "");
}

// ─────────────────────────────────────────────────────────────────
// Mission Control.
// ─────────────────────────────────────────────────────────────────
export default function MissionControl() {
  const { t } = useT();
  const prefix = useTxPathPrefix();
  const canLoadAudit = prefix === "/admin/transportation";
  const { data, error, loading, reload } = useTransportationReadiness();

  if (loading && !data) {
    return (
      <div
        data-testid="mc-loading"
        className="text-slate-500 text-sm"
      >
        {t("Loading Mission Control…")}
      </div>
    );
  }
  if (error || !data) {
    return (
      <div
        data-testid="mc-error"
        className="text-slate-500 text-sm"
      >
        {t("Mission Control is temporarily unavailable.")}
      </div>
    );
  }

  const snap = data.snapshot || {};
  const overall = data.overall_readiness;
  const risks = data.risks || [];
  const riskCount = risks.length;

  // Top operational priority (Card 8) — derived from the existing
  // risks ordering (action_required first). No new ranking engine.
  const topPriority = risks[0] || null;
  const nextLabel = topPriority
    ? translateRiskLabel(topPriority, t)
    : t("All clear — continue routine operations.");
  const nextActionHref = topPriority?.code === "blocked_dispatches"
    ? `${prefix}/dispatch`
    : topPriority?.code === "hr_mismatch"
      ? `${prefix}/command-queue`
      : topPriority
        ? `${prefix}/intelligence/cleanup`
        : `${prefix}/intelligence`;

  return (
    <div data-testid="mc-mission-control" className="space-y-4">
      <MissionBrief overall={overall} riskCount={riskCount} />

      {/* TRACK 18.12 · Workspace Actions strip — consistent
          role-aware navigation into every operational workspace. */}
      <WorkspaceStrip prefix={prefix} />

      {/* Eight operational cards — one question each. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Card 1 · Fleet Ready? */}
        <McCard
          testid="mc-card-fleet"
          question="Fleet Ready?"
          icon={Truck}
          band={data.truck_band}
          primaryKpi={snap.available_trucks || 0}
          primaryLabel="eligible trucks"
          secondaryKpi={snap.upcoming_expirations_30d || 0}
          secondaryLabel="docs expiring 30d"
          summary={t("Truck eligibility + inspection state, composed from existing fleet engines.")}
          actionLabel="Open Fleet"
          actionHref={`${prefix}/trucks`}
          drillHref={`${prefix}/inspections`}
        />

        {/* Card 2 · Drivers Ready? */}
        <McCard
          testid="mc-card-drivers"
          question="Drivers Ready?"
          icon={Users}
          band={data.driver_band}
          primaryKpi={snap.available_drivers || 0}
          primaryLabel="eligible drivers"
          secondaryKpi={snap.pending_reviews || 0}
          secondaryLabel="pending reviews"
          summary={t("Driver eligibility composed from HR lifecycle + Transportation compliance.")}
          actionLabel="Open Drivers"
          actionHref={`${prefix}/drivers`}
          drillHref={`${prefix}/intelligence`}
        />

        {/* Card 3 · Carriers Ready? */}
        <McCard
          testid="mc-card-carriers"
          question="Carriers Ready?"
          icon={Building2}
          band={data.carrier_band}
          primaryKpi={snap.available_carriers || 0}
          primaryLabel="eligible carriers"
          secondaryKpi={snap.documents_awaiting_review || 0}
          secondaryLabel="docs awaiting review"
          summary={t("Carrier eligibility + packet state from the Compliance Center.")}
          actionLabel="Open Carriers"
          actionHref={`${prefix}/carriers`}
          drillHref={`${prefix}/compliance`}
        />

        {/* Card 4 · Dispatch Healthy? */}
        <McCard
          testid="mc-card-dispatch"
          question="Dispatch Healthy?"
          icon={Activity}
          band={data.dispatch_readiness}
          primaryKpi={snap.blocked_dispatches || 0}
          primaryLabel="blocked dispatches"
          secondaryKpi={(data.dispatch_readiness?.score ?? 0).toString().split(".")[0] + "%"}
          secondaryLabel="readiness"
          summary={t("Dispatch never embedded — link only. Dispatch remains the operational system of record.")}
          actionLabel="Open Dispatch"
          actionHref={`${prefix}/dispatch`}
          drillHref={`${prefix}/live-operations`}
        />

        {/* Card 5 · Anything Blocking? */}
        <McCard
          testid="mc-card-blocking"
          question="Anything Blocking?"
          icon={ShieldAlert}
          band={riskCount === 0 ? { label: "green", score: 100 } : (
            risks.some((r) => r.severity === "action_required")
              ? { label: "red" } : { label: "yellow" })}
          primaryKpi={riskCount}
          primaryLabel="open risks"
          secondaryKpi={risks.filter((r) => r.severity === "action_required").length}
          secondaryLabel="action required"
          summary={riskCount === 0
            ? t("Nothing is blocking. Transportation is clear.")
            : risks.slice(0, 2).map((r) => translateRiskLabel(r, t)).join(" · ")}
          actionLabel="Open Live Operations"
          actionHref={`${prefix}/live-operations`}
          drillHref={`${prefix}/intelligence/cleanup`}
        />

        {/* Card 6 · What Changed Today? */}
        <RecentActivityCard prefix={prefix} canLoadAudit={canLoadAudit} />

        {/* Card 7 · What Needs Attention? */}
        <McCard
          testid="mc-card-attention"
          question="What Needs Attention?"
          icon={Inbox}
          primaryKpi={snap.open_action_items || 0}
          primaryLabel="open action items"
          secondaryKpi={data.cleanup?.total_signals || 0}
          secondaryLabel="materialized cleanup items"
          summary={t("Surfaced from the existing Cleanup Companion + Automation action queue. No new ranking engine.")}
          actionLabel="Open Cleanup"
          actionHref={`${prefix}/intelligence/cleanup`}
          drillHref={`${prefix}/command-queue`}
        />

        {/* Card 8 · What Should We Do Next? */}
        <McCard
          testid="mc-card-next"
          question="What Should We Do Next?"
          icon={Sparkles}
          primaryKpi={topPriority ? 1 : 0}
          primaryLabel="top priority"
          secondaryKpi={riskCount}
          secondaryLabel="risks queued"
          summary={nextLabel}
          actionLabel="Open the workflow"
          actionHref={nextActionHref}
          drillHref={topPriority ? `${prefix}/live-operations` : null}
        />
      </div>

      <div className="flex items-center justify-between text-[10px] uppercase tracking-wide text-slate-400">
        <div>
          {t("Source · composed from Tracks 16.06 / 16.07 / 16.10 / 16.11A / 16.15 / 16.15A / 16.16")}
        </div>
        <button
          type="button"
          onClick={reload}
          data-testid="mc-refresh"
          className="text-slate-500 hover:text-slate-800 inline-flex items-center gap-1 normal-case"
        >
          <RefreshCw className="h-3 w-3" /> {t("Refresh")}
        </button>
      </div>
    </div>
  );
}
