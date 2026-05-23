// Phase 2 P1 · Governance Health dashboard
// Route: /admin/governance · admin-strict gate
//
// Surfaces the cross-portal contradiction detection engine
// (`/api/admin/compliance/*`) as a live convergence dashboard:
//   - convergence score (0-100) + health label
//   - severity tile strip (critical/high/medium/low/info)
//   - status breakdown (open/acknowledged/resolved)
//   - per-rule open counts (sorted, click-through → findings list)
//   - last-scan timestamp + on-demand "Run scan now" trigger
//
// Strictly read-only on the data side — the only mutation is the admin
// scan trigger. Acknowledge / resolve happens on the findings page.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2, Activity,
  RefreshCw, ArrowRight, Eye, Clock, Link2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import AdminShell from "@/components/AdminShell";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { usePageTitle } from "@/lib/usePageTitle";

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

const SEVERITY_META = {
  critical: { icon: AlertOctagon, tint: "border-rose-500 bg-rose-50 text-rose-900",  pill: "bg-rose-600 text-white" },
  high:     { icon: AlertTriangle, tint: "border-amber-500 bg-amber-50 text-amber-900", pill: "bg-amber-500 text-white" },
  medium:   { icon: Activity,      tint: "border-yellow-400 bg-yellow-50 text-yellow-900", pill: "bg-yellow-500 text-white" },
  low:      { icon: ShieldCheck,   tint: "border-sky-400 bg-sky-50 text-sky-900",  pill: "bg-sky-500 text-white" },
  info:     { icon: CheckCircle2,  tint: "border-slate-300 bg-slate-50 text-slate-700", pill: "bg-slate-500 text-white" },
};

const HEALTH_META = {
  healthy:  { tint: "border-emerald-500 bg-emerald-50 text-emerald-900", label: "Healthy" },
  fair:     { tint: "border-sky-500 bg-sky-50 text-sky-900",             label: "Fair" },
  degraded: { tint: "border-amber-500 bg-amber-50 text-amber-900",       label: "Degraded" },
  critical: { tint: "border-rose-500 bg-rose-50 text-rose-900",          label: "Critical" },
};

function SeverityTile({ severity, count }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.info;
  const Icon = meta.icon;
  return (
    <Link
      to={`/admin/compliance-findings?severity=${severity}`}
      className={`block border-2 ${meta.tint} rounded-md p-3 hover:shadow-md transition-shadow`}
      data-testid={`gov-sev-tile-${severity}`}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-80" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold opacity-80">{severity}</span>
      </div>
      <div className="font-display text-3xl font-black mt-1 leading-none">{count}</div>
    </Link>
  );
}

function StatusPill({ status, count }) {
  const tints = {
    open: "bg-rose-100 text-rose-900 border-rose-300",
    acknowledged: "bg-amber-100 text-amber-900 border-amber-300",
    resolved: "bg-emerald-100 text-emerald-900 border-emerald-300",
  };
  return (
    <Link
      to={`/admin/compliance-findings?status=${status}`}
      className={`inline-flex items-center gap-2 px-3 py-1.5 border rounded text-xs font-mono uppercase tracking-wider ${tints[status] || "bg-slate-50"}`}
      data-testid={`gov-status-${status}`}
    >
      {status} <span className="font-display font-black text-sm">{count}</span>
    </Link>
  );
}

function RuleRow({ ruleId, count, catalog }) {
  const meta = catalog?.[ruleId] || {};
  const sevMeta = SEVERITY_META[meta.severity] || SEVERITY_META.info;
  return (
    <Link
      to={`/admin/compliance-findings?rule_id=${ruleId}`}
      className="flex items-center gap-3 px-3 py-2.5 border-b border-slate-100 hover:bg-slate-50 transition-colors"
      data-testid={`gov-rule-row-${ruleId}`}
    >
      <span className={`inline-flex items-center justify-center w-1.5 h-8 rounded-sm ${sevMeta.pill}`} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold text-slate-900 truncate">{meta.title || ruleId}</div>
        <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
          {ruleId} · {meta.category || "other"} · {meta.severity || "info"}
        </div>
      </div>
      <span className="font-display text-xl font-black text-slate-900 tabular-nums">{count}</span>
      <ArrowRight className="w-4 h-4 text-slate-400" />
    </Link>
  );
}

export default function AdminGovernance() {
  usePageTitle("Governance Health · Admin");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [backfillResult, setBackfillResult] = useState(null);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const { data } = await api.get("/admin/governance/summary");
      setSummary(data || null);
    } catch (e) {
      setErr(operationalError(e, "Could not load governance summary."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const runScan = useCallback(async () => {
    setScanning(true); setErr("");
    try {
      await api.post("/admin/compliance/scan");
      await load();
    } catch (e) {
      setErr(operationalError(e, "Scan failed."));
    } finally {
      setScanning(false);
    }
  }, [load]);

  const runBackfill = useCallback(async (dryRun) => {
    setBackfilling(true); setErr(""); setBackfillResult(null);
    try {
      const { data } = await api.post(
        "/admin/compliance/backfill-employee-links",
        { dry_run: !!dryRun }
      );
      setBackfillResult(data);
      // Refresh summary if we actually mutated.
      if (!dryRun) await load();
    } catch (e) {
      setErr(operationalError(e, "Backfill failed."));
    } finally {
      setBackfilling(false);
    }
  }, [load]);

  const sevCounts = summary?.severity_counts || {};
  const statusCounts = summary?.status_counts || {};
  const ruleCounts = summary?.rule_counts || {};
  const catalog = summary?.rule_catalog || {};
  const score = summary?.convergence_score ?? 0;
  const healthLabel = summary?.health_label || "fair";
  const healthMeta = HEALTH_META[healthLabel] || HEALTH_META.fair;

  const totalOpen = useMemo(
    () => Object.values(sevCounts).reduce((a, b) => a + (b || 0), 0),
    [sevCounts]
  );

  const lastScan = summary?.last_scan;
  const lastScanRel = useMemo(() => {
    if (!lastScan?.finished_at) return "—";
    const t = new Date(lastScan.finished_at);
    if (Number.isNaN(t.getTime())) return "—";
    const sec = Math.max(1, Math.floor((Date.now() - t.getTime()) / 1000));
    if (sec < 60)   return `${sec}s ago`;
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
    if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
    return `${Math.floor(sec / 86400)}d ago`;
  }, [lastScan]);

  const sortedRules = useMemo(() => {
    const entries = Object.entries(ruleCounts);
    entries.sort((a, b) => b[1] - a[1]);
    return entries;
  }, [ruleCounts]);

  return (
    <AdminShell
      title="Governance Health"
      section="governance"
      intro={
        <p className="text-sm text-slate-700 leading-relaxed">
          Cross-portal contradiction detection. Surfaces operational gaps before humans
          discover them manually — driver expirations, expired training, missing PPE
          accountability, incident/CAPA lifecycle breaks, and employee identity anomalies.
          Read-only intelligence layer over the existing source-of-truth collections.
        </p>
      }
    >
      <div className="space-y-5 mt-5" data-testid="admin-governance">
        {/* Convergence score banner */}
        <div className={`border-2 rounded-md p-4 sm:p-5 flex flex-wrap items-center gap-4 ${healthMeta.tint}`} data-testid="gov-score-banner">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-8 h-8" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold opacity-80">Convergence Score</div>
              <div className="font-display text-4xl font-black leading-none mt-1" data-testid="gov-score-value">
                {loading ? "…" : score}<span className="text-base opacity-70">/100</span>
              </div>
            </div>
          </div>
          <div className="px-3 py-1.5 bg-white/70 border border-current/30 rounded">
            <div className="font-mono text-[10px] uppercase tracking-wider opacity-70">Health</div>
            <div className="font-display text-lg font-black leading-none" data-testid="gov-health-label">{healthMeta.label}</div>
          </div>
          <div className="px-3 py-1.5 bg-white/70 border border-current/30 rounded">
            <div className="font-mono text-[10px] uppercase tracking-wider opacity-70">Total Open</div>
            <div className="font-display text-lg font-black leading-none" data-testid="gov-total-open">{totalOpen}</div>
          </div>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-700 inline-flex items-center gap-1">
              <Clock className="w-3 h-3" /> Last scan: <strong data-testid="gov-last-scan-rel">{lastScanRel}</strong>
            </span>
            <Button onClick={runScan} disabled={scanning || loading} size="sm" data-testid="gov-run-scan">
              <RefreshCw className={`w-4 h-4 mr-1.5 ${scanning ? "animate-spin" : ""}`} />
              {scanning ? "Scanning…" : "Run scan now"}
            </Button>
            <Link to="/admin/compliance-findings">
              <Button variant="outline" size="sm" data-testid="gov-view-findings">
                <Eye className="w-4 h-4 mr-1.5" /> View findings
              </Button>
            </Link>
          </div>
        </div>

        {err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="gov-error">{err}</div>
        ) : null}

        {/* Severity tile strip */}
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">By severity (open + acknowledged)</div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3" data-testid="gov-severity-strip">
            {SEVERITY_ORDER.map((s) => (
              <SeverityTile key={s} severity={s} count={sevCounts[s] ?? 0} />
            ))}
          </div>
        </div>

        {/* Status pills */}
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">By status</div>
          <div className="flex flex-wrap gap-2" data-testid="gov-status-strip">
            <StatusPill status="open" count={statusCounts.open ?? 0} />
            <StatusPill status="acknowledged" count={statusCounts.acknowledged ?? 0} />
            <StatusPill status="resolved" count={statusCounts.resolved ?? 0} />
          </div>
        </div>

        {/* Per-rule open counts */}
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="gov-rule-table">
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-200">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
              Open by rule (click any row to filter findings)
            </div>
          </div>
          {sortedRules.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-500" data-testid="gov-rule-empty">
              No open findings. Convergence is clean — last scan {lastScanRel}.
            </div>
          ) : (
            sortedRules.map(([ruleId, count]) => (
              <RuleRow key={ruleId} ruleId={ruleId} count={count} catalog={catalog} />
            ))
          )}
        </div>

        {/* Last scan stats */}
        {lastScan ? (
          <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-xs text-slate-600 font-mono" data-testid="gov-last-scan-stats">
            Last scan {lastScan.finished_at?.slice(0, 19).replace("T", " ")} ·
            <strong> {lastScan.detected_total ?? 0}</strong> detected ·
            <strong> {lastScan.upserts ?? 0}</strong> upserts ·
            <strong> {lastScan.auto_resolved ?? 0}</strong> auto-resolved
            {Object.keys(lastScan.detector_errors || {}).length > 0
              ? ` · errors: ${Object.keys(lastScan.detector_errors).join(", ")}`
              : ""}
          </div>
        ) : null}

        {/* iter355 · Employee linkage backfill panel */}
        <div className="bg-white border border-slate-200 border-l-4 border-l-indigo-600 rounded-md p-4" data-testid="gov-backfill-panel">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-indigo-600 text-white shrink-0">
              <Link2 className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-display text-base font-black tracking-tight text-slate-900">Employee Linkage Backfill</h3>
              <p className="text-xs text-slate-600 mt-1 leading-snug">
                Walks every operational record (training · PPE · CAPAs · incidents) and writes <code className="font-mono text-[11px]">employee_id</code> on records whose <code className="font-mono text-[11px]">employee_name</code> uniquely resolves to one active employee. Ambiguous names are never auto-linked. Idempotent. Pair with the <code className="font-mono text-[11px]">EMP_LINK_*</code> detector findings above to clean up identity drift.
              </p>
              <div className="flex flex-wrap gap-2 mt-3">
                <Button variant="outline" size="sm" onClick={() => runBackfill(true)} disabled={backfilling} data-testid="gov-backfill-dry-run">
                  <Link2 className={`w-4 h-4 mr-1.5 ${backfilling ? "animate-spin" : ""}`} />
                  Preview (dry-run)
                </Button>
                <Button size="sm" onClick={() => runBackfill(false)} disabled={backfilling} data-testid="gov-backfill-execute">
                  <Link2 className={`w-4 h-4 mr-1.5 ${backfilling ? "animate-spin" : ""}`} />
                  Execute backfill
                </Button>
                {backfillResult ? (
                  <Link to="/admin/compliance-findings?rule_id=EMP_LINK_UNRESOLVABLE">
                    <Button variant="ghost" size="sm" data-testid="gov-view-unresolvable">
                      View unresolvable identities <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                ) : null}
              </div>
              {backfillResult ? (
                <div className="mt-3 bg-slate-50 border border-slate-200 rounded p-3 text-xs font-mono text-slate-700 space-y-1" data-testid="gov-backfill-result">
                  <div>
                    {backfillResult.dry_run ? "DRY-RUN" : "EXECUTED"} ·
                    total backfilled: <strong>{backfillResult.total_backfilled}</strong> ·
                    active unique names: {backfillResult.active_unique_names} ·
                    ambiguous skipped: {backfillResult.ambiguous_names_skipped}
                  </div>
                  {Object.entries(backfillResult.per_collection || {}).map(([k, v]) => (
                    <div key={k} className="pl-4">
                      <span className="text-slate-500">{k}:</span>{" "}
                      scanned {v.scanned} · backfilled <strong>{v.backfilled}</strong> ·
                      no-match {v.skipped_no_match} · ambiguous {v.skipped_ambiguous}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
