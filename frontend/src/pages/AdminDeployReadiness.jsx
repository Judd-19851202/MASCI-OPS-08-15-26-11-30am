// AdminDeployReadiness — Iter136 (Phase-1 Iter D). One-screen
// deploy-readiness dashboard. Hits /api/admin/deploy-readiness and
// renders an OSHA-style green/yellow/red checklist.
import React, { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2, XCircle, AlertTriangle, RefreshCw, Rocket, Loader2, Shield,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import IntegrationProbesPanel from "@/components/IntegrationProbesPanel";
import { toast } from "sonner";

const OVERALL_BAND = {
  ready:     { bg: "bg-emerald-50", border: "border-emerald-500", text: "text-emerald-900", icon: CheckCircle2, label: "READY TO DEPLOY" },
  attention: { bg: "bg-amber-50",   border: "border-amber-500",   text: "text-amber-900",   icon: AlertTriangle, label: "ATTENTION REQUIRED" },
  blocked:   { bg: "bg-red-50",     border: "border-red-500",     text: "text-red-900",     icon: XCircle,       label: "DEPLOY BLOCKED" },
};

const SEV_BADGE = {
  blocker: "bg-red-100 text-red-900 border-red-300",
  warn:    "bg-amber-100 text-amber-900 border-amber-300",
  info:    "bg-slate-100 text-slate-900 border-slate-300",
};

export default function AdminDeployReadiness() {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const r = await api.get("/admin/deploy-readiness");
      setState(r.data);
      if (isRefresh) toast.success("Refreshed");
    } catch (err) {
      toast.error("Could not load readiness check");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const Overall = state ? OVERALL_BAND[state.overall_status] || OVERALL_BAND.attention : null;
  const OverallIcon = Overall?.icon;

  return (
    <AdminShell active="deploy-readiness">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
          <div>
            <div className="ux-kicker">ADMIN · PRE-DEPLOY QA</div>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Deploy Readiness
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Aggregated pre-deploy checks across Mongo, indexes, R2, Resend, integrations, and seed data. Run this before every production push.
            </p>
          </div>
          <Button
            onClick={() => fetch(true)}
            disabled={refreshing || loading}
            className="bg-slate-900 hover:bg-red-700 text-white border-b-2 border-black font-bold uppercase tracking-wide h-10 shrink-0"
            data-testid="deploy-readiness-refresh"
          >
            {refreshing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Re-Run
          </Button>
        </div>

        {/* Body */}
        {loading ? (
          <LoadingState label="Running checks…" testId="deploy-readiness-loading" />
        ) : !state ? (
          <EmptyState title="Could not load readiness check" body="The deploy readiness check did not return. Check System Health." />
        ) : (
          <>
            {/* Overall banner */}
            <div className={`${Overall.bg} ${Overall.border} border-2 rounded-md p-5 mb-5 flex items-center gap-4`} data-testid="deploy-readiness-overall">
              <OverallIcon className={`w-12 h-12 ${Overall.text} shrink-0`} />
              <div className="flex-1 min-w-0">
                <div className={`font-display text-2xl font-black ${Overall.text}`}>{Overall.label}</div>
                <div className="text-sm mt-1 text-slate-700">
                  {state.total_checks} checks · {state.blocker_count} blocker{state.blocker_count !== 1 && "s"} · {state.warn_count} warning{state.warn_count !== 1 && "s"} ·
                  &nbsp;Last checked {String(state.checked_at).slice(11, 19)} UTC
                </div>
              </div>
            </div>

            {/* Check list */}
            <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="deploy-readiness-checks">
              <div className="bg-slate-50 border-b-2 border-slate-200 px-4 py-2 ux-kicker">
                Detail Checks
              </div>
              <ul className="divide-y divide-slate-100">
                {state.checks.map((c) => {
                  const Icon = c.passed ? CheckCircle2 : (c.severity === "blocker" ? XCircle : AlertTriangle);
                  const iconColor = c.passed
                    ? "text-emerald-700"
                    : (c.severity === "blocker" ? "text-red-700" : "text-amber-700");
                  return (
                    <li key={c.id} className="px-4 py-3 flex items-start gap-3" data-testid={`deploy-readiness-check-${c.id}`}>
                      <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${iconColor}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <div className="font-bold text-sm text-slate-900">{c.label}</div>
                          <span className={`px-1.5 py-0 rounded border text-[9px] uppercase tracking-wider font-mono font-bold ${SEV_BADGE[c.severity] || SEV_BADGE.info}`}>
                            {c.severity}
                          </span>
                        </div>
                        <div className="text-xs text-slate-600 mt-0.5">{c.detail}</div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* iter142 — Live integration probe roll-up */}
            <div className="mt-5">
              <IntegrationProbesPanel />
            </div>

            {/* Help line */}
            <div className="mt-4 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded p-3">
              <Shield className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
              <strong>Blocker</strong> = must fix before deploy.
              &nbsp;<strong>Warn</strong> = degraded but app still works.
              &nbsp;<strong>Info</strong> = informational, no action needed.
            </div>
          </>
        )}
      </div>
    </AdminShell>
  );
}
