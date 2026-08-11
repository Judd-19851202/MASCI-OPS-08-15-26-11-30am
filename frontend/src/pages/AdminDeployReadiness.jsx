// AdminDeployReadiness — Iter136 (Phase-1 Iter D). One-screen
// deploy-readiness dashboard. Hits /api/admin/deploy-readiness and
// renders an OSHA-style green/yellow/red checklist.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { formatRelativeTime } from "@/lib/platformTime";
import {
  CheckCircle2, XCircle, AlertTriangle, RefreshCw, Rocket, Loader2, Shield,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { HelpTip } from "@/components/ui/HelpTip";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/ui/PortalStates";
import IntegrationProbesPanel from "@/components/IntegrationProbesPanel";
import { toast } from "sonner";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";
import { Link } from "react-router-dom";

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
  const [checksState, setChecksState] = useState(null);
  const [authorityState, setAuthorityState] = useState(null);
  const [loadingChecks, setLoadingChecks] = useState(true);
  const [loadingAuthority, setLoadingAuthority] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadChecks = useCallback(async () => {
    setLoadingChecks(true);
    try {
      const r = await api.get("/admin/deploy-readiness");
      setChecksState(r.data);
    } catch (err) {
      setChecksState(null);
    } finally {
      setLoadingChecks(false);
    }
  }, []);

  const loadAuthority = useCallback(async () => {
    setLoadingAuthority(true);
    try {
      const r = await api.get("/admin/deployment-readiness", { timeout: 120000 });
      setAuthorityState(r.data);
    } catch (err) {
      setAuthorityState(null);
    } finally {
      setLoadingAuthority(false);
    }
  }, []);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    await Promise.allSettled([loadChecks(), loadAuthority()]);
    if (isRefresh) {
      setRefreshing(false);
      toast.success("Refreshed");
    }
  }, [loadAuthority, loadChecks]);

  useEffect(() => { fetch(); }, [fetch]);

  const state = checksState;
  const Overall = state ? OVERALL_BAND[state.overall_status] || OVERALL_BAND.attention : null;
  const OverallIcon = Overall?.icon;
  const authorityBlockers = authorityState?.blocking_gates || [];
  const authorityAdvisories = authorityState?.advisory_findings || [];
  const authorityVerdict = useMemo(() => {
    if (loadingAuthority) {
      return {
        label: "Evaluating authoritative decision…",
        tone: OVERALL_BAND.attention,
        icon: Loader2,
        summary: "Checking the bounded deployment-readiness owner for current blocking gates and advisories.",
      };
    }
    if (!authorityState) {
      return {
        label: "Authoritative decision unavailable",
        tone: OVERALL_BAND.blocked,
        icon: XCircle,
        summary: "The canonical deployment-readiness owner did not respond.",
      };
    }
    if (authorityBlockers.length > 0) {
      return {
        label: "FAIL — BLOCKING GATES PRESENT",
        tone: OVERALL_BAND.blocked,
        icon: XCircle,
        summary: `${authorityBlockers.length} blocking gate${authorityBlockers.length !== 1 ? "s" : ""} must be cleared before deploy.`,
      };
    }
    if (authorityAdvisories.length > 0) {
      return {
        label: "PASS WITH ADVISORIES",
        tone: OVERALL_BAND.attention,
        icon: AlertTriangle,
        summary: `${authorityAdvisories.length} advisory finding${authorityAdvisories.length !== 1 ? "s" : ""} remain open, but the bounded deploy decision is PASS.`,
      };
    }
    return {
      label: "PASS — NO ACTIVE ADVISORIES",
      tone: OVERALL_BAND.ready,
      icon: CheckCircle2,
      summary: "No blocking gates or advisories are currently reported by the bounded deployment-readiness owner.",
    };
  }, [authorityAdvisories.length, authorityBlockers.length, authorityState, loadingAuthority]);
  const AuthorityIcon = authorityVerdict.icon;
  const initialLoad = loadingChecks && loadingAuthority && !checksState && !authorityState;

  return (
    <AdminShell active="deploy-readiness">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
          <div>
            <div className="ux-kicker">ADMIN · GO-LIVE REVIEW</div>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Deploy Readiness
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Aggregated go-live checks across storage, messaging, integrations, and data readiness. Run this before every production release.
            </p>
          </div>
          <Button
            onClick={() => fetch(true)}
            disabled={refreshing}
            className="bg-slate-900 hover:bg-red-700 text-white border-b-2 border-black font-bold uppercase tracking-wide h-10 shrink-0"
            data-testid="deploy-readiness-refresh"
          >
            {refreshing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Re-Run
          </Button>
        </div>

        {initialLoad ? (
          <div className="grid gap-4" data-testid="deploy-readiness-initial-loading">
            <SectionLoader
              title="Authoritative release decision"
              body="Loading the bounded deployment-readiness owner…"
              testId="deploy-readiness-authority-loading"
            />
            <SectionLoader
              title="Technical pre-deploy checks"
              body="Running the technical go-live checklist…"
              testId="deploy-readiness-checks-loading"
            />
          </div>
        ) : !state && !authorityState ? (
          <EmptyState title="Could not load readiness review" body="The readiness review did not return. Check System Health." />
        ) : (
          <>
            <div
              className={`${authorityVerdict.tone.bg} ${authorityVerdict.tone.border} border-2 rounded-md p-5 mb-5`}
              data-testid="deploy-readiness-authoritative-panel"
            >
              <div className="flex items-start gap-4">
                <AuthorityIcon className={`w-10 h-10 shrink-0 ${authorityVerdict.tone.text} ${loadingAuthority ? "animate-spin" : ""}`} />
                <div className="flex-1 min-w-0">
                  <div className="ux-kicker">Authoritative release decision</div>
                  <div className={`font-display text-2xl font-black ${authorityVerdict.tone.text}`} data-testid="deploy-readiness-authoritative-label">
                    {authorityVerdict.label}
                  </div>
                  <div className="text-sm mt-1 text-slate-700" data-testid="deploy-readiness-authoritative-summary">
                    {authorityVerdict.summary}
                  </div>
                  <div className="mt-2 text-xs text-slate-600" data-testid="deploy-readiness-authoritative-meta">
                    {loadingAuthority
                      ? "Waiting for the canonical decision surface…"
                      : authorityState
                      ? `Decision ${String(authorityState.decision || "unknown").toUpperCase()} · ${authorityBlockers.length} blocker${authorityBlockers.length !== 1 ? "s" : ""} · ${authorityAdvisories.length} advisory finding${authorityAdvisories.length !== 1 ? "s" : ""} · checked ${formatRelativeTime(authorityState.generated_at)}`
                      : "Canonical deployment-readiness owner is unavailable right now."}
                  </div>
                </div>
              </div>

              {loadingAuthority ? (
                <div className="mt-4 rounded-md border border-amber-300 bg-white/70 px-4 py-3 text-sm text-slate-600" data-testid="deploy-readiness-authority-pending">
                  Loading current blocking gates and advisory rows…
                </div>
              ) : null}

              {!loadingAuthority && authorityState ? (
                <div className="mt-4 grid grid-cols-1 xl:grid-cols-2 gap-4">
                  <FindingList
                    title="Blocking gates"
                    emptyText="No blocking gates are currently reported."
                    findings={authorityBlockers}
                    testId="deploy-readiness-blocking-list"
                    tone="red"
                  />
                  <FindingList
                    title="Advisory findings"
                    emptyText="No advisory findings are currently reported."
                    findings={authorityAdvisories}
                    testId="deploy-readiness-advisory-list"
                    tone="amber"
                  />
                </div>
              ) : null}
            </div>

            {/* Overall banner */}
            {loadingChecks ? (
              <SectionLoader
                title="Technical pre-deploy checks"
                body="Running the technical go-live checklist…"
                testId="deploy-readiness-checks-loading"
              />
            ) : state ? (
              <>
                <div className={`${Overall.bg} ${Overall.border} border-2 rounded-md p-5 mb-5 flex items-center gap-4`} data-testid="deploy-readiness-overall">
                  <OverallIcon className={`w-12 h-12 ${Overall.text} shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className={`font-display text-2xl font-black ${Overall.text}`} data-testid="deploy-readiness-overall-label">{Overall.label}</div>
                    <div className="text-sm mt-1 text-slate-700" data-testid="deploy-readiness-overall-summary">
                      {state.total_checks} checks · {state.blocker_count} blocker{state.blocker_count !== 1 && "s"} · {state.warn_count} warning{state.warn_count !== 1 && "s"} ·
                      &nbsp;Last checked {formatRelativeTime(state.checked_at)}
                    </div>
                  </div>
                </div>

                {/* Check list */}
                <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="deploy-readiness-checks">
                  <div className="bg-slate-50 border-b-2 border-slate-200 px-4 py-2 ux-kicker">
                    Technical pre-deploy checks
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
                              <div className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                                {sanitizeOperatorReference(c.label, "Readiness check")}
                                {c.formula ? (
                                  <HelpTip
                                    testId={`deploy-readiness-check-${c.id}-why`}
                                    label={`Why this number? ${sanitizeOperatorReference(c.label, "Readiness check")}`}
                                    body={[
                                      c.formula.source_of_truth ? `Source: ${sanitizeOperatorReference(c.formula.source_of_truth, "platform data")}.` : null,
                                      c.formula.denominator_definition ? `Denominator: ${c.formula.denominator_definition}.` : null,
                                      c.formula.threshold_pct != null ? `Threshold: ${c.formula.threshold_pct}% pass floor.` : null,
                                    ].filter(Boolean).join(" ")}
                                  />
                                ) : null}
                              </div>
                              <span className={`px-1.5 py-0 rounded border text-[9px] uppercase tracking-wider font-mono font-bold ${SEV_BADGE[c.severity] || SEV_BADGE.info}`}>
                                {c.severity}
                              </span>
                            </div>
                            <div className="text-xs text-slate-600 mt-0.5">{sanitizeOperatorReference(c.detail, "Review this check for more information.")}</div>
                            {Array.isArray(c.details) && c.details.length > 0 ? (
                              <div className="mt-2 text-[11px] text-slate-500" data-testid={`deploy-readiness-check-${c.id}-details`}>
                                {c.details.slice(0, 3).map((row) => (
                                  <div key={`${row.collection}-${row.binding_type}`}>
                                    {sanitizeOperatorReference(row.collection, "record")}.{sanitizeOperatorReference(row.binding_type, "status")}: {row.pct}% · eligible {row.eligible_total} · missing {row.missing_master_ref}
                                  </div>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </>
            ) : null}

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

function SectionLoader({ title, body, testId }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5" data-testid={testId}>
      <div className="ux-kicker">{title}</div>
      <div className="mt-3 flex items-center gap-3 text-slate-700">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span className="text-sm font-medium">{body}</span>
      </div>
    </div>
  );
}

function FindingList({ title, findings, emptyText, testId, tone }) {
  const toneClass = tone === "red"
    ? "border-red-200 bg-red-50/70"
    : "border-amber-200 bg-amber-50/70";
  return (
    <div className={`rounded-md border ${toneClass} p-4`} data-testid={testId}>
      <div className="ux-kicker">{title}</div>
      {findings.length === 0 ? (
        <div className="mt-2 text-sm text-slate-600" data-testid={`${testId}-empty`}>{emptyText}</div>
      ) : (
        <ul className="mt-3 space-y-3">
          {findings.map((finding, index) => (
            <li key={finding.id || `${title}-${index}`} className="rounded-md border border-white/80 bg-white px-3 py-3" data-testid={`${testId}-item-${index}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-bold text-slate-900" data-testid={`${testId}-item-${index}-summary`}>
                    {sanitizeOperatorReference(finding.summary, "Readiness finding")}
                  </div>
                  <div className="mt-1 text-[11px] font-mono uppercase tracking-wide text-slate-500" data-testid={`${testId}-item-${index}-category`}>
                    {sanitizeOperatorReference(finding.category, "general")}
                  </div>
                </div>
                <span className="px-1.5 py-0.5 rounded border border-slate-200 bg-slate-50 text-[10px] font-mono uppercase tracking-wider text-slate-700" data-testid={`${testId}-item-${index}-id`}>
                  {sanitizeOperatorReference(finding.id, "unknown")}
                </span>
              </div>
              {finding.evidence ? (
                <div className="mt-2 text-xs text-slate-600" data-testid={`${testId}-item-${index}-evidence`}>
                  {sanitizeOperatorReference(finding.evidence, "No evidence provided.")}
                </div>
              ) : null}
              {finding.remediation ? (
                <div className="mt-2 text-xs text-slate-700" data-testid={`${testId}-item-${index}-remediation`}>
                  <strong>Remediation:</strong> {sanitizeOperatorReference(finding.remediation, "No remediation provided.")}
                </div>
              ) : null}
              {finding.remediation_link ? (
                <Link
                  to={finding.remediation_link}
                  className="mt-2 inline-flex text-xs font-semibold text-slate-900 underline underline-offset-2"
                  data-testid={`${testId}-item-${index}-link`}
                >
                  Open remediation route
                </Link>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
