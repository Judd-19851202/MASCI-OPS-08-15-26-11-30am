/**
 * <RoutingStatusPanel> — Track 15.72A
 *
 * Self-certifying observability for Email Routing V2.
 * Reads from:
 *   GET  /api/admin/email-routing/v2/status     (auto-refresh on mount)
 *   POST /api/admin/email-routing/v2/self-check (manual button)
 *
 * Goal: a MASCI admin can verify routing mode, V2 activation, critical
 * route health, and rollback readiness in under 30 seconds — without
 * Mongo creds, DevTools, Atlas, or pasted admin tokens.
 *
 * Hard rules honoured: no recipients displayed (counts only), no
 * sender/connection-string leakage, no email sends, no route mutations.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  Activity,
  ShieldCheck,
  AlertTriangle,
  CircleDot,
  RotateCw,
  PlayCircle,
  Server,
  Database,
  Clock,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { sanitizeOperatorError, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const SOURCE_LABELS = {
  db: "saved rules",
  legacy: "legacy rules",
  system: "system",
};

function humanizeMode(mode) {
  if (mode === "v2") return "modern routing";
  if (mode === "v1") return "legacy fallback";
  return sanitizeOperatorReference(mode, "routing mode");
}

const BAND_STYLES = {
  green: { row: "bg-emerald-50 border-emerald-200", pill: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: ShieldCheck, label: "Healthy" },
  amber: { row: "bg-amber-50  border-amber-200",   pill: "bg-amber-100  text-amber-800  border-amber-300",  icon: AlertTriangle, label: "Attention" },
  red:   { row: "bg-rose-50   border-rose-200",    pill: "bg-rose-100   text-rose-800   border-rose-300",   icon: XCircle,       label: "Critical" },
};

function Pill({ band, children }) {
  const s = BAND_STYLES[band] || BAND_STYLES.amber;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${s.pill}`}>
      <CircleDot className="h-3 w-3" />
      {children}
    </span>
  );
}

function StatLine({ icon: Icon, label, value, mono = false, testId }) {
  return (
    <div className="flex items-start gap-2 text-sm" data-testid={testId}>
      {Icon && <Icon className="h-4 w-4 text-slate-500 mt-0.5 shrink-0" />}
      <div className="min-w-0 flex-1">
        <div className="text-[11px] uppercase tracking-wide text-slate-500">{label}</div>
        <div className={`text-slate-900 ${mono ? "font-mono text-xs break-all" : ""}`}>{value ?? "—"}</div>
      </div>
    </div>
  );
}

function fmtAge(min) {
  if (min === null || min === undefined) return "no modern-routing activity yet";
  if (min < 1) return "just now";
  if (min < 60) return `${Math.round(min)} min ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} h ${Math.round(min - h * 60)} min ago`;
  return `${Math.floor(h / 24)} d ago`;
}

export default function RoutingStatusPanel() {
  const [status, setStatus] = useState(null);
  const [statusErr, setStatusErr] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [selfCheck, setSelfCheck] = useState(null);
  const [selfCheckLoading, setSelfCheckLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    setStatusErr(null);
    try {
      const r = await api.get("/admin/email-routing/v2/status");
      setStatus(r.data);
    } catch (e) {
      setStatusErr(sanitizeOperatorError(e?.response?.data?.detail || e?.message, "Failed to load routing status"));
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  const runSelfCheck = useCallback(async () => {
    setSelfCheckLoading(true);
    try {
      const r = await api.post("/admin/email-routing/v2/self-check");
      setSelfCheck(r.data);
      const overall = r.data?.overall;
      if (overall === "green") toast.success(`Routing review passed · ${r.data.total_routes} routes healthy`);
      else if (overall === "amber") toast.warning(r.data.overall_reason || "Self-check flagged warnings");
      else toast.error(sanitizeOperatorError(r.data.overall_reason, "Routing review failed"));
      // Refresh status to pick up new audit timestamps
      loadStatus();
    } catch (e) {
      toast.error(sanitizeOperatorError(e?.response?.data?.detail || e?.message, "Routing review failed"));
    } finally {
      setSelfCheckLoading(false);
    }
  }, [loadStatus]);

  const band = status?.band || (statusErr ? "red" : "amber");
  const bandStyle = BAND_STYLES[band] || BAND_STYLES.amber;
  const BandIcon = bandStyle.icon;

  const headerRow = useMemo(() => {
    if (statusErr) return statusErr;
    if (!status) return statusLoading ? "Loading routing status…" : "—";
    return status.band_reason;
  }, [status, statusErr, statusLoading]);

  return (
    <section
      className={`rounded-xl border-2 ${bandStyle.row} p-4 sm:p-5 space-y-4`}
      data-testid="routing-status-panel"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <BandIcon className={`h-6 w-6 ${band === "green" ? "text-emerald-600" : band === "amber" ? "text-amber-600" : "text-rose-600"}`} />
          <h3 className="text-lg font-semibold text-slate-900 leading-tight">Routing Status</h3>
        </div>
        <Pill band={band}>{bandStyle.label}</Pill>
        {status?.mode && (
          <span
            className={`px-2 py-0.5 text-[11px] font-mono rounded border ${
              status.mode === "v2"
                ? "bg-indigo-100 text-indigo-900 border-indigo-300"
                : "bg-slate-100 text-slate-800 border-slate-300"
            }`}
            data-testid="routing-status-mode"
          >
            mode={humanizeMode(status.mode)}
          </span>
        )}
        <div className="ml-auto flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={loadStatus}
            disabled={statusLoading}
            data-testid="routing-status-refresh"
          >
            <RotateCw className={`h-3.5 w-3.5 mr-1 ${statusLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={runSelfCheck}
            disabled={selfCheckLoading}
            data-testid="routing-status-self-check"
          >
            <PlayCircle className={`h-3.5 w-3.5 mr-1 ${selfCheckLoading ? "animate-spin" : ""}`} />
            Run Self-Check
          </Button>
        </div>
      </div>

      <p className="text-sm text-slate-700" data-testid="routing-status-band-reason">{headerRow}</p>

      {/* Stat grid */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <StatLine icon={Activity}   label="Flag active"        value={status.flag_active ? "true" : "false"} mono testId="rs-flag-active" />
          <StatLine icon={Server}     label="Service mode"       value={sanitizeOperatorReference(status.app_env, "standard")} mono testId="rs-app-env" />
          <StatLine icon={Database}   label="Data source"        value={status.db_name ? "Connected" : "Unavailable"} testId="rs-db-name" />
          <StatLine icon={Clock}      label="System uptime"      value={status.backend_uptime_s != null ? `${status.backend_uptime_s} s` : "—"} testId="rs-uptime" />
          <StatLine icon={CheckCircle2} label="Critical OK"      value={`${status.route_counts?.critical_populated || 0} / ${status.route_counts?.critical_total || 0}`} testId="rs-critical-ok" />
          <StatLine icon={AlertTriangle} label="Critical empty"  value={status.route_counts?.critical_empty || 0} testId="rs-critical-empty" />
          <StatLine icon={Activity}   label="Routing history (24h)" value={status.audit_counters?.db_source_last_24h ?? 0} testId="rs-db-24h" />
          <StatLine icon={XCircle}    label="Errors (24h)"       value={status.audit_counters?.errors_last_24h ?? 0} testId="rs-errors-24h" />
          <StatLine icon={Clock}      label="Last routing review" value={fmtAge(status.last_v2_audit_age_minutes)} testId="rs-last-v2" />
          <StatLine icon={Clock}      label="Routes total"       value={status.route_counts?.total} testId="rs-routes-total" />
          <StatLine icon={Clock}      label="Routes disabled"    value={status.route_counts?.disabled} testId="rs-routes-disabled" />
          <StatLine icon={RotateCw}   label="Rollback value"     value={sanitizeOperatorReference(status.rollback_target?.reverse_value, "restore previous setting")} mono testId="rs-rollback-val" />
        </div>
      )}

      {/* Per-V2-module recency */}
      {status?.v2_module_recency && (
        <div className="rounded-lg border border-slate-200 bg-white/60 p-3" data-testid="rs-v2-modules">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Modern routing activity</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
            {[["health_monitor", "Health monitor"], ["outage_alerts", "Outage alerts"], ["safety_digest", "Safety digest"]].map(([k, label]) => {
              const row = status.v2_module_recency[k];
              return (
                <div key={k} className="flex flex-col gap-0.5 p-2 rounded border border-slate-200 bg-white" data-testid={`rs-mod-${k}`}>
                  <span className="font-medium text-slate-800">{label}</span>
                  {row ? (
                    <>
                      <span className="font-mono text-[11px] text-slate-600">{row.ts}</span>
                      <span>
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-mono mr-1 ${row.source === "db" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>{SOURCE_LABELS[row.source] || sanitizeOperatorReference(row.source, "system")}</span>
                        <span className="text-slate-600">{sanitizeOperatorReference(row.route_key, "routing item")}</span>
                      </span>
                    </>
                  ) : (
                    <span className="text-slate-500 italic">no observations yet</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Latest audit rows */}
      {status?.latest_audit_rows?.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white/60 p-3" data-testid="rs-latest-rows">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Recent routing activity (most recent first · counts only · no recipients)</div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-slate-500">
                <tr>
                  <th className="text-left font-medium py-1 pr-2">ts</th>
                  <th className="text-left font-medium py-1 pr-2">route</th>
                  <th className="text-left font-medium py-1 pr-2">source</th>
                  <th className="text-left font-medium py-1 pr-2">status</th>
                  <th className="text-left font-medium py-1 pr-2">workflow</th>
                  <th className="text-right font-medium py-1 pr-2">to</th>
                  <th className="text-right font-medium py-1 pr-2">cc</th>
                  <th className="text-right font-medium py-1">bcc</th>
                </tr>
              </thead>
              <tbody>
                {status.latest_audit_rows.map((row, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="font-mono text-[10px] py-1 pr-2">{row.ts}</td>
                    <td className="font-mono text-[11px] py-1 pr-2">{sanitizeOperatorReference(row.route_key, "routing item")}</td>
                    <td className="py-1 pr-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${row.source === "db" ? "bg-emerald-100 text-emerald-800" : row.source === "legacy" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`}>{SOURCE_LABELS[row.source] || sanitizeOperatorReference(row.source, "system")}</span>
                    </td>
                    <td className="py-1 pr-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${row.status === "resolved" || row.status === "dry_run" ? "bg-emerald-50 text-emerald-700" : "bg-rose-100 text-rose-800"}`}>{row.status}</span>
                    </td>
                    <td className="py-1 pr-2 text-slate-600">{sanitizeOperatorReference(row.calling_module, "routing workflow")}</td>
                    <td className="py-1 pr-2 text-right">{row.to_count}</td>
                    <td className="py-1 pr-2 text-right">{row.cc_count}</td>
                    <td className="py-1 text-right">{row.bcc_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Self-check results panel (renders only after the operator clicks the button) */}
      {selfCheck && (
        <div className="rounded-lg border-2 border-indigo-200 bg-indigo-50/40 p-3 space-y-2" data-testid="rs-self-check-results">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wide text-slate-500">Routing review result</span>
            <Pill band={selfCheck.overall}>{(BAND_STYLES[selfCheck.overall] || BAND_STYLES.amber).label}</Pill>
            <span className="text-xs text-slate-600">{sanitizeOperatorReference(selfCheck.overall_reason, "Routing review completed.")}</span>
            <span className="ml-auto text-xs text-slate-500">
              green={selfCheck.summary?.green} · amber={selfCheck.summary?.amber} · red={selfCheck.summary?.red}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-slate-500">
                <tr>
                  <th className="text-left font-medium py-1 pr-2">route</th>
                  <th className="text-left font-medium py-1 pr-2">status</th>
                  <th className="text-left font-medium py-1 pr-2">source</th>
                  <th className="text-right font-medium py-1 pr-2">to/cc/bcc</th>
                  <th className="text-left font-medium py-1">reason</th>
                </tr>
              </thead>
              <tbody>
                {selfCheck.results.map((row, i) => (
                  <tr key={i} className="border-t border-slate-100" data-testid={`rs-sc-row-${row.route_key}`}>
                    <td className="font-mono text-[11px] py-1 pr-2">
                      {sanitizeOperatorReference(row.route_key, "routing item")}{row.critical && <span className="ml-1 px-1 rounded bg-rose-100 text-rose-700 text-[9px]">KEY</span>}
                    </td>
                    <td className="py-1 pr-2"><Pill band={row.status}>{(BAND_STYLES[row.status] || BAND_STYLES.amber).label}</Pill></td>
                    <td className="py-1 pr-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${row.source === "db" ? "bg-emerald-100 text-emerald-800" : row.source === "legacy" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`}>{SOURCE_LABELS[row.source] || sanitizeOperatorReference(row.source, "system")}</span>
                    </td>
                    <td className="py-1 pr-2 text-right font-mono text-[11px]">{row.to_count}/{row.cc_count}/{row.bcc_count}</td>
                    <td className="py-1 text-slate-600">{sanitizeOperatorReference(row.reason, "Review this item for details.")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rollback hint */}
      {status?.rollback_target && (
        <div className="text-[11px] text-slate-600 border-t border-slate-200 pt-2">
          <strong>Rollback:</strong> {sanitizeOperatorReference(status.rollback_target.mechanism, "Restore the previous setting")}. Restore value = <code className="font-mono">{sanitizeOperatorReference(status.rollback_target.reverse_value, "previous setting")}</code>. Estimated time ≤ {status.rollback_target.estimated_minutes} min.
        </div>
      )}

      {/* Track 15.73Q · PM-Email Coverage Card */}
      <PmEmailCoverageCard />
    </section>
  );
}

/**
 * <PmEmailCoverageCard> — Track 15.73Q
 *
 * Surfaces which active jobs_master rows lack a pm_email so the operator
 * can prioritise data-hygiene backfill without needing DB access.
 *
 * Reads from GET /api/admin/pm-email-coverage (admin-gated).
 */
function PmEmailCoverageCard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const r = await api.get("/admin/pm-email-coverage");
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading && !data) {
    return (
      <div className="text-[11px] text-slate-500 border-t border-slate-200 pt-2" data-testid="pm-email-coverage-loading">
        Loading PM-email coverage…
      </div>
    );
  }
  if (err) {
    return (
      <div className="text-[11px] text-rose-700 border-t border-slate-200 pt-2" data-testid="pm-email-coverage-error">
        PM-email coverage unavailable: {err}
      </div>
    );
  }
  if (!data) return null;

  const missingActive = data.active_projects_missing_pm_email || 0;
  const drImpacted = data.active_projects_with_recent_drs_and_no_pm_email || 0;
  const total = data.active_projects_total || 0;
  const coverage = total > 0 ? ((total - missingActive) / total) * 100 : 100;
  const band = drImpacted > 0 ? "red" : missingActive > 0 ? "amber" : "green";
  const bs = BAND_STYLES[band] || BAND_STYLES.amber;
  const BandIcon = bs.icon;

  return (
    <div
      className={`rounded-lg border ${bs.row} p-3 space-y-2`}
      data-testid="pm-email-coverage-card"
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <BandIcon className={`h-4 w-4 ${band === "green" ? "text-emerald-600" : band === "amber" ? "text-amber-600" : "text-rose-600"}`} />
          <span className="text-sm font-semibold text-slate-900">Daily Report PM-Email Coverage</span>
        </div>
        <Pill band={band}>{bs.label}</Pill>
        <span className="text-xs text-slate-600">{coverage.toFixed(0)}% of active projects covered</span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={load}
          disabled={loading}
          className="ml-auto"
          data-testid="pm-email-coverage-refresh"
        >
          <RotateCw className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
        <div data-testid="pm-cov-total">
          <div className="text-slate-500">Active projects</div>
          <div className="font-mono font-semibold">{total}</div>
        </div>
        <div data-testid="pm-cov-missing">
          <div className="text-slate-500">Missing PM email</div>
          <div className={`font-mono font-semibold ${missingActive > 0 ? "text-amber-700" : ""}`}>{missingActive}</div>
        </div>
        <div data-testid="pm-cov-impacted">
          <div className="text-slate-500">With recent DRs &amp; no PM</div>
          <div className={`font-mono font-semibold ${drImpacted > 0 ? "text-rose-700" : ""}`}>{drImpacted}</div>
        </div>
        <div>
          <div className="text-slate-500">Has Co-PM only</div>
          <div className="font-mono font-semibold">{data.summary?.active_with_co_pm_email_only ?? 0}</div>
        </div>
      </div>
      {data.missing_rows_top_25 && data.missing_rows_top_25.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer text-slate-600 hover:text-slate-900" data-testid="pm-cov-toggle-list">
            Show {data.missing_rows_top_25.length} affected project(s)
          </summary>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead className="text-slate-500">
                <tr>
                  <th className="text-left font-medium py-1 pr-2">project_number</th>
                  <th className="text-left font-medium py-1 pr-2">project_name</th>
                  <th className="text-right font-medium py-1 pr-2">recent DRs</th>
                  <th className="text-left font-medium py-1 pr-2">last DR</th>
                  <th className="text-left font-medium py-1 pr-2">status</th>
                  <th className="text-left font-medium py-1">co_pm_emails</th>
                </tr>
              </thead>
              <tbody>
                {data.missing_rows_top_25.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100" data-testid={`pm-cov-row-${r.project_number}`}>
                    <td className="font-mono py-1 pr-2">{r.project_number}</td>
                    <td className="py-1 pr-2 text-slate-700 truncate max-w-[260px]">{r.project_name}</td>
                    <td className="py-1 pr-2 text-right font-mono">{r.recent_dr_count}</td>
                    <td className="py-1 pr-2 font-mono text-slate-600">{r.last_dr_date || "—"}</td>
                    <td className="py-1 pr-2">
                      {r.status?.map((s, j) => (
                        <span key={j} className="inline-block mr-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800">{s}</span>
                      ))}
                    </td>
                    <td className="py-1 text-slate-600 font-mono text-[10px]">{(r.co_pm_emails || []).join(", ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
      {data.remediation_note && (
        <div className="text-[10px] text-slate-500 italic">{data.remediation_note}</div>
      )}
    </div>
  );
}
