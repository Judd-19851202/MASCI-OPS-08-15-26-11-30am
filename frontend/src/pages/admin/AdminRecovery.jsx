// AdminRecovery.jsx — Phase D · iter443 · Recovery Dashboard
//
// Single-screen recovery posture view. Polls the read-only snapshot
// endpoint every 30s. NO action buttons (per RECOVERY_DASHBOARD_SPEC.md
// §7 — Admin must navigate to /admin/system for actions).
//
// All data sourced from /api/admin/recovery/snapshot (cached server-side
// for 15s).
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { Activity } from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { api } from "@/lib/api";
import { TruthOwnerPanel } from "@/components/admin/trust/TrustPrimitives";
import { sanitizeOperatorError, sanitizeOperatorReference } from "@/lib/operatorLanguage";
const POLL_MS = 30000;

const PILL_STYLES = {
  GREEN: "bg-emerald-100 text-emerald-800 border-emerald-300",
  AMBER: "bg-amber-100 text-amber-800 border-amber-300",
  RED: "bg-rose-100 text-rose-800 border-rose-300",
};

function fmtAge(minutes) {
  if (minutes == null) return "—";
  if (minutes < 1) return "< 1m";
  if (minutes < 60) return `${Math.round(minutes)} m`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m`;
}

function fmtTs(ts) {
  if (!ts) return "—";
  try {
    return new Date(ts).toISOString().replace("T", " ").slice(0, 19) + "Z";
  } catch {
    return ts;
  }
}

function Card({ title, status, children, testid }) {
  const tone =
    status === "GREEN"
      ? "border-emerald-300 bg-emerald-50/70"
      : status === "AMBER"
      ? "border-amber-300 bg-amber-50/80"
      : status === "RED"
      ? "border-rose-300 bg-rose-50/80"
      : "border-slate-200 bg-white";
  const chip =
    status === "GREEN"
      ? "bg-emerald-700 text-white"
      : status === "AMBER"
      ? "bg-amber-600 text-white"
      : status === "RED"
      ? "bg-rose-700 text-white"
      : "bg-slate-200 text-slate-700";
  return (
    <div
      className={`rounded-xl border-2 p-4 shadow-sm ${tone}`}
      data-testid={testid}
    >
      <div className="mb-2 flex items-center gap-2">
        <div className="text-[10px] font-mono font-bold uppercase tracking-[0.18em] text-slate-500">
          {title}
        </div>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-[0.18em] ${chip}`}>
          {status || "INFO"}
        </span>
      </div>
      {children}
    </div>
  );
}

const GRID_BACKGROUND = {
  backgroundImage:
    "linear-gradient(rgba(15,23,42,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.045) 1px, transparent 1px), radial-gradient(circle at top right, rgba(15,118,110,0.12), transparent 32%), radial-gradient(circle at bottom left, rgba(30,64,175,0.08), transparent 28%)",
  backgroundSize: "24px 24px, 24px 24px, auto, auto",
  backgroundPosition: "0 0, 0 0, 100% 0, 0 100%",
};

function Sparkline({ data, width = 600, height = 80 }) {
  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-slate-400">No trend data available yet.</div>
    );
  }
  const xs = data.map((_, i) => i);
  const ys = data.map((d) => d.size_mb || 0);
  const maxY = Math.max(...ys) || 1;
  const minY = Math.min(...ys);
  const pad = 4;
  const sx = (x) =>
    pad + (x * (width - 2 * pad)) / Math.max(1, xs.length - 1);
  const sy = (y) =>
    height - pad - ((y - minY) * (height - 2 * pad)) / Math.max(1, maxY - minY);
  const pts = ys.map((y, i) => `${sx(i)},${sy(y)}`).join(" ");
  const last = data[data.length - 1];
  return (
    <div data-testid="archive-size-trend">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-20"
        preserveAspectRatio="none"
      >
        <polyline
          fill="none"
          stroke="rgb(15 118 110)"
          strokeWidth="2"
          points={pts}
        />
        {ys.map((y, i) => (
          <circle key={i} cx={sx(i)} cy={sy(y)} r="2" fill="rgb(15 118 110)" />
        ))}
      </svg>
      <div className="flex justify-between text-xs text-slate-500 mt-1">
        <span>{fmtTs(data[0]?.ts)}</span>
        <span>min {minY.toFixed(1)} · max {maxY.toFixed(1)} MB</span>
        <span>{fmtTs(last?.ts)}</span>
      </div>
    </div>
  );
}

function normalizeStatus(value) {
  const raw = String(value || "").trim().toUpperCase();
  if (["RED", "FAIL", "FAILED", "CRITICAL", "ERROR", "BLOCKED", "EMERGENCY"].includes(raw)) return "RED";
  if (["AMBER", "WARN", "WARNING", "HIGH", "DEGRADED", "YELLOW", "MISMATCH", "UNAVAILABLE", "UNKNOWN"].includes(raw)) return "AMBER";
  return "GREEN";
}

function summarizeWorstStatus(statuses) {
  if (statuses.some((status) => status === "RED")) return "RED";
  if (statuses.some((status) => status === "AMBER")) return "AMBER";
  return "GREEN";
}

export default function AdminRecovery() {
  const [snap, setSnap] = useState(null);
  const [backupTrust, setBackupTrust] = useState(null);
  const [deploymentReadiness, setDeploymentReadiness] = useState(null);
  const [platformStatus, setPlatformStatus] = useState(null);
  const [clusterCapacity, setClusterCapacity] = useState(null);
  const [clusterCapacityHistory, setClusterCapacityHistory] = useState(null);
  const [schedulerRuns, setSchedulerRuns] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [performanceBudget, setPerformanceBudget] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const otsSurface = snap?.ots_truth?.truth_surface || {
    surface_name: "Operational Truth Spine",
    owner_endpoint: "/api/admin/recovery/snapshot",
    owner_module: "platform recovery service",
    canonical_owner_id: "bcss_recovery_posture",
    surface_id: "bcss_recovery_posture",
    role: "AGGREGATOR",
    upstream_owner_ids: [
      "bcss_backup_archive_lineage",
      "bcss_backup_slot_execution",
      "bcss_restore_drill_evidence",
    ],
  };
  const otsRelationship = snap?.truth_relationship || {
    role: "AGGREGATOR",
    canonical_status: "UNVERIFIABLE",
    derived_status: "UNVERIFIABLE",
    derivation_explanation: loading
      ? "Loading recovery status from the latest saved update."
      : "Recovery status is not currently available.",
    canonical_owner_id: "bcss_recovery_posture",
    evidence_age_source: loading ? "Pending" : "Unavailable",
    conflicts: [],
    has_conflict: false,
  };

  const load = useCallback(async () => {
    try {
      const [r, trust, deploy, platform, capacity, capacityHistory, scheduler, system, perf] = await Promise.all([
        api.get("/admin/recovery/snapshot", { skipSessionStatus: true, timeout: 120000 }),
        api.get("/admin/backup-trust-score", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/admin/deployment-readiness", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/admin/platform/status", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/cluster/capacity", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/cluster/capacity/history?days=30", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/admin/scheduler-runs?limit=25", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/admin/system-health", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
        api.get("/admin/deployment-readiness/performance-budget-contract", { skipSessionStatus: true, timeout: 120000 }).catch(() => null),
      ]);
      setSnap(r.data);
      setBackupTrust(trust?.data || null);
      setDeploymentReadiness(deploy?.data || null);
      setPlatformStatus(platform?.data || null);
      setClusterCapacity(capacity?.data || null);
      setClusterCapacityHistory(capacityHistory?.data || null);
      setSchedulerRuns(scheduler?.data || null);
      setSystemHealth(system?.data || null);
      setPerformanceBudget(perf?.data || null);
      setErr(null);
    } catch (e) {
      setErr(sanitizeOperatorError(e?.response?.data?.detail || e?.message || e, "Recovery saved update is unavailable right now."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  const reliabilityCards = useMemo(() => {
    const runtimeStatus = systemHealth || platformStatus
      ? summarizeWorstStatus([
          normalizeStatus(systemHealth?.overall),
          platformStatus?.readiness?.ready_flag ? "GREEN" : "AMBER",
        ])
      : "AMBER";
    const schedulerStatus = summarizeWorstStatus([
      snap?.scheduler?.alive ? "GREEN" : "RED",
      (schedulerRuns?.failed_total || 0) > 0 ? "AMBER" : "GREEN",
    ]);
    const releaseStatus = summarizeWorstStatus([
      deploymentReadiness?.decision === "pass" ? "GREEN" : deploymentReadiness ? "RED" : "AMBER",
      performanceBudget?.ok ? "GREEN" : performanceBudget ? "RED" : "AMBER",
    ]);
    const capacityStatus = summarizeWorstStatus([
      normalizeStatus(clusterCapacity?.severity),
      clusterCapacityHistory?.predictive?.capacity_risk_level === "critical"
        ? "RED"
        : clusterCapacityHistory?.predictive?.capacity_risk_level === "watch"
        ? "AMBER"
        : "GREEN",
    ]);
    const providerStatus = normalizeStatus(systemHealth?.overall || "unknown");
    const backupStatus = summarizeWorstStatus([
      normalizeStatus(snap?.pill),
      backupTrust?.score_band === "red" ? "RED" : backupTrust?.score_band === "amber" ? "AMBER" : "GREEN",
      snap?.last_drill?.status === "GREEN" ? "GREEN" : "AMBER",
    ]);

    return [
      {
        id: "runtime",
        title: "Platform availability",
        status: runtimeStatus,
        why: systemHealth
          ? `System Health is reporting ${String(systemHealth?.overall || "unknown").toUpperCase()} and platform ready flag is ${String(platformStatus?.readiness?.ready_flag ?? false)}.`
          : "Runtime evidence is still loading.",
        evidence: systemHealth
          ? `system cards ${systemHealth?.cards?.length ?? "—"} · platform alerts ${platformStatus?.alerts?.length ?? 0} · ready flag ${String(platformStatus?.readiness?.ready_flag ?? false)}`
          : "Awaiting platform-status and system-health endpoints.",
        confidence: systemHealth && platformStatus ? "HIGH" : "MEDIUM",
        action: platformStatus?.readiness?.ready_flag ? "Keep public health and platform status under watch." : "Hold release until the platform ready flag returns true.",
      },
      {
        id: "scheduler",
        title: "Scheduler and background durability",
        status: schedulerStatus,
        why: snap?.scheduler?.alive
          ? "Canonical scheduler heartbeat is present."
          : "Scheduler heartbeat is missing or stale.",
        evidence: `failed runs ${schedulerRuns?.failed_total ?? "—"} · dedup prevented ${schedulerRuns?.dedup_total ?? "—"} · last tick ${fmtTs(snap?.scheduler?.evidence_ts)}`,
        confidence: schedulerRuns && snap?.scheduler ? "HIGH" : "MEDIUM",
        action: snap?.scheduler?.alive ? "Review scheduler runs for any failed slots before release." : "Repair scheduler heartbeat before release.",
      },
      {
        id: "release",
        title: "Release and performance gate",
        status: releaseStatus,
        why: deploymentReadiness
          ? `Deployment readiness is ${deploymentReadiness?.decision || "unknown"}.`
          : "Deployment readiness evidence is still loading.",
        evidence: `blocking gates ${deploymentReadiness?.blocking_gates?.length ?? "—"} · budget rows ${performanceBudget?.row_count ?? "—"} · missing budget keys ${performanceBudget?.missing_keys?.length ?? "—"}`,
        confidence: deploymentReadiness && performanceBudget ? "HIGH" : "MEDIUM",
        action: releaseStatus === "GREEN" ? "Release guard is aligned with current budget evidence." : "Clear blocking gates or failing budget rows before release.",
      },
      {
        id: "capacity",
        title: "Database and storage headroom",
        status: capacityStatus,
        why: clusterCapacity
          ? `Current storage posture is ${clusterCapacity?.severity || "unknown"}.`
          : "Capacity evidence is still loading.",
        evidence: `used ${clusterCapacity?.storage_used_pct ?? "—"}% · days to quota ${clusterCapacityHistory?.days_to_quota ?? "—"} · slope ${clusterCapacityHistory?.slope_mb_per_day ?? "—"} MB/day`,
        confidence: clusterCapacity && clusterCapacityHistory ? "HIGH" : "MEDIUM",
        action: capacityStatus === "GREEN" ? "Capacity runway is currently acceptable." : "Review storage growth and capacity runway before release.",
      },
      {
        id: "backup-restore",
        title: "Backup and restore readiness",
        status: backupStatus,
        why: snap?.last_drill?.status === "GREEN"
          ? "Latest isolated restore drill is green against the latest complete archive."
          : "Latest drill or backup trust still needs attention.",
        evidence: `recovery pill ${snap?.pill || "—"} · trust score ${backupTrust?.trust_score ?? "—"} · backup age ${fmtAge(snap?.backup_age_minutes)} · last drill ${fmtTs(snap?.last_drill?.finished_at)}`,
        confidence: snap && backupTrust ? "HIGH" : "MEDIUM",
        action: backupStatus === "GREEN" ? "Maintain fresh archive cadence and drill recency." : "Resolve recovery drivers before release.",
      },
      {
        id: "provider",
        title: "Operator-facing provider resilience",
        status: providerStatus,
        why: systemHealth
          ? `System Health is reporting ${String(systemHealth?.overall || "unknown").toUpperCase()} for operator-visible dependencies.`
          : "Provider/system-health evidence is still loading.",
        evidence: `system cards ${systemHealth?.cards?.length ?? "—"} · platform status ready ${platformStatus?.readiness?.ready_flag ?? "—"}`,
        confidence: systemHealth && platformStatus ? "MEDIUM" : "LOW",
        action: providerStatus === "GREEN" ? "Keep operator messaging aligned with safe degraded modes." : "Use System Health to inspect the failing operator-facing dependency before release.",
      },
    ];
  }, [snap, schedulerRuns, deploymentReadiness, performanceBudget, clusterCapacity, clusterCapacityHistory, backupTrust, systemHealth, platformStatus]);

  const recommendedActions = useMemo(() => {
    const actions = [];
    if (reliabilityCards.some((card) => card.status === "RED")) {
      actions.push("Do not release until every red reliability card returns to green or a governed external-owner dependency is documented.");
    }
    if (snap?.pill !== "GREEN") {
      actions.push(`Recovery posture is ${snap?.pill || "unknown"}; keep archive freshness and restore recency under active review.`);
    }
    if ((schedulerRuns?.failed_total || 0) > 0) {
      actions.push("Review failed scheduler slots and confirm no recurring job remains unhealthy.");
    }
    if ((deploymentReadiness?.blocking_gates || []).length > 0) {
      actions.push("Deployment readiness still has blocking gates; clear each blocker before Save & Deploy.");
    }
    if (performanceBudget && !performanceBudget.ok) {
      actions.push("Performance budget contract is blocking release; all required budget rows must pass.");
    }
    if (!actions.length) {
      actions.push("All loaded executive reliability signals are currently in release-ready posture. Continue the final regression pass before deployment.");
    }
    return actions;
  }, [reliabilityCards, snap, schedulerRuns, deploymentReadiness, performanceBudget]);

  return (
    <LegacyAdminModernShell
      title="Recovery Posture"
      subtitle="Read-only recovery posture with governed release and continuity signals."
      breadcrumb={[
        { label: "Storage & Recovery", to: "/admin/storage-recovery" },
        { label: "Recovery Posture" },
      ]}
      testidPrefix="admin-recovery"
    >
      <div className="mb-5 rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm sm:p-5" style={GRID_BACKGROUND} data-testid="admin-recovery-governed-surface">
        <div className="rounded-2xl border border-slate-200 bg-white/95 p-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex items-start gap-3">
              <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <div className="text-[10px] font-mono font-bold uppercase tracking-[0.2em] text-slate-500">Storage & Recovery</div>
                <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-950" data-testid="admin-recovery-page-heading">Recovery posture and release readiness</h1>
                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
                  Read-only posture board for archive freshness, restore proof, scheduler durability, release guard, and capacity runway. To run a backup, drill, or archive restore, open <a className="font-medium text-slate-900 underline decoration-slate-300 underline-offset-4" href="/admin/operations-control">Operations Control</a>.
                </p>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[320px]" data-testid="admin-recovery-hero-chips">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <div className="font-mono uppercase tracking-[0.16em] text-slate-500">Update rhythm</div>
                <div className="mt-1 font-semibold text-slate-900">Polls every 30 seconds</div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <div className="font-mono uppercase tracking-[0.16em] text-slate-500">Action model</div>
                <div className="mt-1 font-semibold text-slate-900">Read-only posture board</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {loading && (
        <div className="text-sm text-slate-500" data-testid="recovery-loading">
          Loading recovery posture…
        </div>
      )}
      {err && (
        <div
          className="rounded-md bg-rose-50 border border-rose-200 text-rose-700 p-3 text-sm"
          data-testid="recovery-error"
        >
          Failed to load the latest saved update: {err}
        </div>
      )}
      {(snap || loading) && (
        <div className="space-y-4">
          <TruthOwnerPanel
            title="Operational Records Board"
            surface={otsSurface}
            relationship={otsRelationship}
            checkedAt={snap?.ots_truth?.evaluation_timestamp ? fmtTs(snap.ots_truth.evaluation_timestamp) : (loading ? "Loading…" : "Unavailable")}
            testidPrefix="recovery-ots-truth-panel"
          />
          <div className="text-xs text-slate-500" data-testid="recovery-ots-disclosure">
            Recovery subject=<span className="font-semibold">{sanitizeOperatorReference(snap?.ots_truth?.truth_subject, "Recovery posture")}</span> · current signal=<span className="font-semibold">{sanitizeOperatorReference(snap?.ots_truth?.permitted_claim, "UNKNOWN")}</span> · confidence=<span className="font-semibold">{sanitizeOperatorReference(snap?.ots_truth?.evidence_confidence, "UNKNOWN")}</span> · this panel summarizes governed evidence and does not replace live recovery action controls.
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-sm" data-testid="reliability-executive-panel">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <div className="text-[10px] font-mono font-bold uppercase tracking-[0.18em] text-slate-500">Operations readiness board</div>
                <h2 className="text-lg font-black tracking-tight text-slate-950" data-testid="reliability-executive-title">Platform reliability, recovery, and release readiness</h2>
                <p className="text-sm text-slate-600 mt-1">
                  Uses the governed recovery, deployment, capacity, scheduler, and system-health surfaces already in the platform.
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500" data-testid="reliability-executive-sources">
                Sources: recovery archive · deployment readiness · cluster capacity · scheduler runs · system health
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3" data-testid="reliability-executive-cards">
              {reliabilityCards.map((card) => (
                <Card key={card.id} title={card.title} status={card.status} testid={`reliability-card-${card.id}`}>
                  <div className="space-y-2 text-sm">
                    <div data-testid={`reliability-card-${card.id}-why`}>
                      <span className="font-semibold text-slate-900">Current signal:</span> {card.why}
                    </div>
                    <div className="text-slate-600" data-testid={`reliability-card-${card.id}-evidence`}>
                      <span className="font-semibold text-slate-900">Evidence:</span> {card.evidence}
                    </div>
                    <div className="text-slate-600" data-testid={`reliability-card-${card.id}-confidence`}>
                      <span className="font-semibold text-slate-900">Confidence:</span> {card.confidence}
                    </div>
                    <div className="text-slate-600" data-testid={`reliability-card-${card.id}-action`}>
                      <span className="font-semibold text-slate-900">Next move:</span> {card.action}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
              <Card title="Immediate actions" status={reliabilityCards.some((card) => card.status === "RED") ? "RED" : summarizeWorstStatus(reliabilityCards.map((card) => card.status))} testid="reliability-immediate-actions">
                <ul className="space-y-2 text-sm" data-testid="reliability-immediate-actions-list">
                  {recommendedActions.map((action, index) => (
                    <li key={`${action}-${index}`} className="leading-relaxed">• {action}</li>
                  ))}
                </ul>
              </Card>
              <Card title="Release evidence" status={summarizeWorstStatus(reliabilityCards.map((card) => card.status))} testid="reliability-release-evidence">
                <div className="space-y-1 text-sm" data-testid="reliability-release-evidence-list">
                  <div>Deployment readiness: <span className="font-semibold">{deploymentReadiness?.decision || "loading"}</span></div>
                  <div>Performance budget contract: <span className="font-semibold">{performanceBudget?.ok ? "pass" : performanceBudget ? "fail" : "loading"}</span></div>
                  <div>Capacity runway: <span className="font-semibold">{clusterCapacityHistory?.days_to_quota == null ? "—" : `${clusterCapacityHistory.days_to_quota} day(s)`}</span></div>
                  <div>Platform status ready flag: <span className="font-semibold">{String(platformStatus?.readiness?.ready_flag ?? "loading")}</span></div>
                </div>
              </Card>
            </div>
          </div>
          {snap ? (
            <>
          {(() => {
            const lineage = snap?.archive_lineage || {};
            return (
              <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="archive-lineage-summary">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">Archive lineage</div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
                  <div data-testid="archive-lineage-authoritative-time">
                    <div className="text-slate-500 text-xs">Authoritative point</div>
                    <div className="font-semibold">{fmtTs(lineage.authoritative_recovery_point_time)}</div>
                  </div>
                  <div data-testid="archive-lineage-time-source">
                    <div className="text-slate-500 text-xs">Timestamp source</div>
                    <div className="font-semibold">{lineage.authoritative_time_source || "UNKNOWN"}</div>
                  </div>
                  <div data-testid="archive-lineage-confidence">
                    <div className="text-slate-500 text-xs">Lineage confidence</div>
                    <div className="font-semibold">{lineage.lineage_confidence || "LOW"}</div>
                  </div>
                  <div data-testid="archive-lineage-integrity">
                    <div className="text-slate-500 text-xs">Integrity / completeness</div>
                    <div className="font-semibold">{lineage.integrity_status || "UNKNOWN"} · {lineage.completeness_status || "UNKNOWN"}</div>
                  </div>
                </div>
              </div>
            );
          })()}
          {/* Hero pill */}
          <div
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-base font-semibold ${
              PILL_STYLES[snap.pill] || PILL_STYLES.AMBER
            }`}
            data-testid="recovery-pill"
          >
            <span>Recovery Posture:</span>
            <span>{snap.pill}</span>
            <span className="ml-2 text-xs font-normal opacity-70">
              ({fmtTs(snap.computed_at)})
            </span>
          </div>

          {/* Top row: last backup · last drill · backup age */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card
              title="Last backup"
              status={snap.last_backup?.ok ? "GREEN" : "RED"}
              testid="card-last-backup"
            >
              {snap.last_backup ? (
                <div className="text-sm space-y-1">
                  <div className="font-mono text-xs break-all">
                    {snap.last_backup.filename}
                  </div>
                  <div>
                    <span className="font-semibold">{snap.last_backup.size_mb}</span> MB ·{" "}
                    <span className="font-semibold">
                      {snap.last_backup.records.toLocaleString()}
                    </span>{" "}
                    records · ok={String(snap.last_backup.ok)}
                  </div>
                  <div className="text-xs text-slate-500">
                    inlined_photos = {snap.last_backup.inlined_photos} · {fmtTs(snap.last_backup.ts)} · source={snap.last_backup.source}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400">No backups yet.</div>
              )}
            </Card>

            <Card title="Last restore drill" status={snap.last_drill?.outcome === "ok" ? "GREEN" : "AMBER"} testid="card-last-drill">
              {snap.last_drill ? (
                <div className="text-sm space-y-1">
                  <div className="text-xs font-mono uppercase tracking-wide text-slate-500">
                    Representative namespace restore
                  </div>
                  <div className="font-semibold">
                    outcome: {snap.last_drill.outcome}
                  </div>
                  <div>
                    {(snap.last_drill.records || 0).toLocaleString()} records ·{" "}
                    {snap.last_drill.photos || 0} photos
                  </div>
                  <div className="text-xs text-slate-500">
                    {snap.last_drill.duration_min ? `${snap.last_drill.duration_min}m · ` : ""}
                    {fmtTs(snap.last_drill.ts)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400">
                  No representative namespace restore drill on file.
                </div>
              )}
            </Card>

            <Card title="Backup age" status={
              snap.backup_age_minutes == null
                ? "RED"
                : snap.backup_age_minutes > 2 * snap.backup_age_target_minutes
                ? "RED"
                : snap.backup_age_minutes > snap.backup_age_target_minutes
                ? "AMBER"
                : "GREEN"
            } testid="card-backup-age">
              <div className="text-2xl font-bold">
                {fmtAge(snap.backup_age_minutes)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                target ≤ {fmtAge(snap.backup_age_target_minutes)}
              </div>
            </Card>

            <Card
              title="Backup Trust Score"
              status={(backupTrust?.score_band || "amber").toUpperCase()}
              testid="card-backup-trust-score"
            >
              <div className="space-y-1 text-sm" data-testid="backup-trust-score-panel">
                <div className="text-3xl font-bold text-slate-900">{backupTrust?.trust_score ?? "—"}</div>
                <div className="font-semibold text-slate-700">{backupTrust?.score_band_label || "Missing evidence"}</div>
                <div className="text-xs text-slate-500">{backupTrust?.score_reason || "Backup trust evidence not yet loaded."}</div>
                <div className="text-xs text-slate-500">
                  Production activation disabled: {String(backupTrust?.production_activation_disabled ?? true)}
                </div>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Card title="Hourly activation" status={snap.hourly_activation?.hourly_cadence_enabled ? "GREEN" : "AMBER"} testid="card-hourly-activation">
              <div className="space-y-1 text-sm" data-testid="hourly-activation-panel">
                <div className="font-semibold">{snap.hourly_activation?.activation_status || "DISABLED BY CONFIGURATION"}</div>
                <div>requested={String(snap.hourly_activation?.r2_hourly_requested)} · effective={String(snap.hourly_activation?.r2_hourly_effective)}</div>
                <div className="text-xs text-slate-500">environment={snap.hourly_activation?.environment || "unknown"} · next slot={fmtTs(snap.hourly_activation?.next_eligible_hourly_slot)}</div>
              </div>
            </Card>
            <Card title="Restore scope" status="AMBER" testid="card-restore-scope">
              <div className="space-y-1 text-sm">
                <div className="font-semibold">{snap.full_restore_status?.status || "NOT YET EXERCISED"}</div>
                <div className="text-xs text-slate-500">{snap.full_restore_status?.message}</div>
                <div className="text-xs text-slate-500">{snap.production_only_evidence_status?.message}</div>
              </div>
            </Card>
          </div>

          {/* Row 2: RPO/RTO · archive count · bucket usage */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card title="RPO / RTO" status={
              snap.rpo.status === "GREEN" && snap.rto.status === "GREEN" ? "GREEN" : "AMBER"
            } testid="card-rpo-rto">
              <div className="space-y-1 text-sm">
                <div>
                  RPO target: <span className="font-semibold">{snap.rpo.target_min}m</span> · actual:{" "}
                  <span className="font-semibold">{snap.rpo.actual_min == null ? "—" : `${snap.rpo.actual_min}m`}</span>{" "}
                  <span className="text-xs">({snap.rpo.status})</span>
                </div>
                <div>
                  RTO target: <span className="font-semibold">{snap.rto.target_min}m</span> · last drill:{" "}
                  <span className="font-semibold">
                    {snap.rto.last_drill_min == null ? "—" : `${snap.rto.last_drill_min}m`}
                  </span>{" "}
                  <span className="text-xs">({snap.rto.status})</span>
                </div>
              </div>
            </Card>

            <Card title="Archive count" status="GREEN" testid="card-archive-count">
              <div className="text-sm space-y-1">
                <div>
                  Total in R2: <span className="font-semibold">{snap.archive_count.r2_total}</span>
                </div>
                <div>
                  Last 7 d: <span className="font-semibold">{snap.archive_count.last_7d}</span> · Last 30 d:{" "}
                  <span className="font-semibold">{snap.archive_count.last_30d}</span>
                </div>
              </div>
            </Card>

            <Card title="Bucket usage" status={snap.bucket_usage.status} testid="card-bucket-usage">
              <div className="text-sm space-y-1">
                <div>
                  <span className="font-semibold">{snap.bucket_usage.gb}</span> GB
                </div>
                <div className="text-xs text-slate-500">
                  WARN ≥ {snap.bucket_usage.warn_gb} GB · ALERT ≥ {snap.bucket_usage.alert_gb} GB
                </div>
                <div className="text-xs text-slate-500">
                  Lifecycle: 90 d on backups/auto-90d/*
                </div>
              </div>
            </Card>
          </div>

          {/* Trend */}
          <Card title="Archive size trend (last 30)" status="GREEN" testid="card-trend">
            <Sparkline data={snap.archive_size_trend} />
          </Card>

          {/* Failures + warnings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Card
              title="Failures (last 7 days)"
              status={snap.failures_7d.length === 0 ? "GREEN" : "AMBER"}
              testid="card-failures"
            >
              {snap.failures_7d.length === 0 ? (
                <div className="text-sm text-slate-400">No failures in the last 7 days.</div>
              ) : (
                <div className="space-y-1 max-h-40 overflow-auto">
                  {snap.failures_7d.map((f, i) => (
                    <div key={i} className="text-xs">
                      <span className="font-mono text-slate-500">{fmtTs(f.ts)}</span>{" "}
                      <span className="font-semibold">{f.mode}</span> — {f.error}
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card
              title="Warnings (active)"
              status={snap.warnings.length === 0 ? "GREEN" : "AMBER"}
              testid="card-warnings"
            >
              {snap.warnings.length === 0 ? (
                <div className="text-sm text-slate-400">No active warnings.</div>
              ) : (
                <ul className="space-y-1">
                  {snap.warnings.map((w, i) => (
                    <li key={i} className="text-sm">
                      <span className="font-semibold">[{w.severity}]</span>{" "}
                      {w.message}{" "}
                      <span className="text-xs text-slate-400">({w.kind})</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          {/* Footer · scheduler line */}
          <div className="text-xs text-slate-500 border-t pt-2" data-testid="recovery-footer">
            Scheduler: alive=<span className="font-semibold">{String(snap.scheduler.alive)}</span> ·
            last lock = {fmtTs(snap.scheduler.last_lock_ts)} · pod={" "}
            <span className="font-mono">{snap.scheduler.owner_pod || "—"}</span> ·
            BACKUP_R2_HOURLY={String(snap.hourly_cadence_enabled)} ·
            status={<span className="font-semibold">{snap.hourly_activation?.activation_status || "DISABLED BY CONFIGURATION"}</span>} ·
            cached={String(snap.cached)} ·
            overlap_blocked={String(snap.scheduler?.backup_runtime?.overlap?.overlap_blocked || false)}
          </div>
            </>
          ) : null}
        </div>
      )}
    </LegacyAdminModernShell>
  );
}
