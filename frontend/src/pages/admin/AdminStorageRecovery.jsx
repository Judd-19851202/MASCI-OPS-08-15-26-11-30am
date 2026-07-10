// TRACK 25 · SPRINT 3 · Admin OS · Storage & Recovery Domain Landing.
//
// Mounted at `/admin/storage-recovery`. This is the canonical admin
// home for disk / R2 / backups / recovery evidence. It:
//   · Reads from the same real endpoints OCC + AdminOS already use.
//   · Reuses the shared `TrustPrimitives` so the visual language is
//     100% identical to OCC + AdminOS — same status pill, same card,
//     same evidence drawer.
//   · Renders inside `PortalShell` + `SideNavV3` so navigation matches
//     the rest of Admin OS (Sprint 1 canonical sidebar).
//   · NEVER duplicates action execution. Every maintenance action is a
//     deep-link into the OCC Maintenance Operations Console with a
//     `?highlight=<operation-id>` query param — one source of action
//     truth (per Sprint 2 rule).
//   · Honestly labels gaps as UNKNOWN with the exact reason; never
//     fabricates GREEN.
//   · Zero-UTC — all timestamps route through `platformTime.js`.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Archive,
  Database,
  HardDrive,
  History,
  RefreshCw,
  Search as SearchIcon,
  ShieldCheck,
  Wrench,
} from "lucide-react";

import { PortalShell } from "../../design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import { getAdminToken } from "@/lib/adminAuth";
import { formatPlatformTime, formatRelativeTime } from "@/lib/platformTime";
import {
  HealthCard,
  EvidenceDrawer,
  TrustStatusPill,
  TRUST_STATUS_STYLES,
  worstStatus,
  sortCardsByAttention,
  useEvidenceDrawer,
} from "@/components/admin/trust/TrustPrimitives";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

// ── HTTP helpers ─────────────────────────────────────────────────
function authHeaders() {
  const t = getAdminToken();
  return t ? { "X-Admin-Token": t } : {};
}
async function probe(path) {
  try {
    const r = await axios.get(`${API}${path}`, { headers: authHeaders() });
    return { ok: true, body: r.data, status: r.status, error: null };
  } catch (e) {
    return {
      ok: false,
      body: null,
      status: e?.response?.status || 0,
      error: e?.response?.data?.detail || e?.message || String(e),
    };
  }
}

// ── Card builders ────────────────────────────────────────────────
// Every builder takes a probe result and returns a normalized card
// object. Returns `{ status: "unknown" }` when the underlying probe
// failed — never invent GREEN.

function bDiskPreflight(recovery) {
  const endpoint = "/api/admin/recovery/snapshot";
  if (!recovery.ok) {
    return _unknownCard("disk-preflight", "Disk Preflight",
      endpoint, "/admin/recovery",
      "Recovery snapshot unreachable.", recovery.error);
  }
  const dp = recovery.body?.disk_preflight || {};
  const okFlag = dp.ok !== false;
  const pct = Number(dp.percent_free ?? -1);
  let status = "unknown", summary, action = "";
  if (pct < 0) {
    status = "unknown";
    summary = "Preflight percent_free not reported.";
  } else if (!okFlag || pct < 5) {
    status = "red";
    summary = `Preflight FAILED · ${pct}% free · writes may be blocked.`;
    action = "Investigate disk_preflight.reason and run storage.safe_cleanup.";
  } else if (pct < 15) {
    status = "yellow";
    summary = `${pct}% free · nearing the 15% safety floor.`;
    action = "Run a Safe Cleanup dry-run this week.";
  } else {
    status = "green";
    summary = `${pct}% free · preflight passing.`;
  }
  return {
    id: "disk-preflight",
    title: "Disk Preflight",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: action,
    checked_at: recovery.body?.computed_at || null,
    evidence: dp,
  };
}

function bR2Bucket(recovery, integrations) {
  const endpoint = "/api/admin/recovery/snapshot · /api/admin/integrations/health";
  if (!recovery.ok && !integrations.ok) {
    return _unknownCard("r2-bucket", "R2 Bucket",
      endpoint, "/admin/recovery",
      "R2 status unreachable.",
      recovery.error || integrations.error);
  }
  const bu = recovery.body?.bucket_usage || {};
  const gb = Number(bu.gb ?? -1);
  const warn = Number(bu.warn_gb ?? 0);
  const alert = Number(bu.alert_gb ?? 0);
  const bucketStatus = String(bu.status || "").toUpperCase();
  const r2Probe = (integrations.body?.probes || []).find((p) => p.id === "r2");
  const reachable = r2Probe ? r2Probe.status === "ok" : null;
  let status = "unknown", summary, action = "";
  if (bucketStatus === "RED" || (alert && gb >= alert)) {
    status = "red";
    summary = `Bucket ${gb} GB · past ${alert} GB alert · retention overdue.`;
    action = "Schedule R2 retention runner (Track 27.06).";
  } else if (bucketStatus === "YELLOW" || (warn && gb >= warn)) {
    status = "yellow";
    summary = `Bucket ${gb} GB · past ${warn} GB warn.`;
    action = `Plan retention run before hitting the ${alert} GB alert.`;
  } else if (gb >= 0) {
    status = reachable === false ? "yellow" : "green";
    summary = `Bucket ${gb} GB${reachable === null ? "" : reachable ? " · reachable" : " · reachability DEGRADED"}`;
    action = reachable === false ? "Verify Cloudflare R2 access." : "";
  }
  if (reachable === false && status === "green") status = "yellow";
  return {
    id: "r2-bucket",
    title: "R2 Bucket Health",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: action,
    checked_at: bu.ts || recovery.body?.computed_at || null,
    evidence: { bucket_usage: bu, r2_probe: r2Probe || null },
  };
}

function bR2Retention(recovery) {
  const endpoint = "/api/admin/recovery/snapshot (warnings)";
  if (!recovery.ok) {
    return _unknownCard("r2-retention", "R2 Retention",
      endpoint, "/admin/recovery",
      "Recovery snapshot unreachable.", recovery.error);
  }
  const warnings = recovery.body?.warnings || [];
  const retention = warnings.filter((w) =>
    String(w.kind || w.message || "").toLowerCase().includes("retention"),
  );
  const bu = recovery.body?.bucket_usage || {};
  const bucketRed = String(bu.status || "").toUpperCase() === "RED";
  let status, summary, action = "";
  if (retention.length > 0) {
    status = retention.some((w) => w.severity === "red") ? "red" : "yellow";
    summary = retention.map((w) => w.message).join(" · ");
    action = "Wire the R2 retention runner (Track 27.06 P1).";
  } else if (bucketRed) {
    status = "yellow";
    summary = "Bucket past alert threshold but no retention warning surfaced.";
    action = "Confirm retention runner is wired and scheduled (Track 27.06).";
  } else {
    // Honest gap: no dedicated retention endpoint yet.
    status = "unknown";
    summary = "No dedicated retention endpoint — inferred from warnings only.";
    action = "Track 27.06 will expose /api/admin/r2/retention.";
  }
  return {
    id: "r2-retention",
    title: "R2 Retention",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: action,
    checked_at: recovery.body?.computed_at || null,
    evidence: { retention_warnings: retention, bucket_usage: bu },
  };
}

function bBackupFreshness(recovery) {
  const endpoint = "/api/admin/recovery/snapshot";
  if (!recovery.ok) {
    return _unknownCard("backup-freshness", "Backup Freshness",
      endpoint, "/admin/recovery",
      "Recovery snapshot unreachable.", recovery.error);
  }
  const pill = String(recovery.body?.pill || "").toLowerCase();
  const status = pill === "green" ? "green"
    : pill === "yellow" ? "yellow"
    : pill === "red" ? "red"
    : "unknown";
  const age = Number(recovery.body?.backup_age_minutes ?? -1);
  const target = Number(recovery.body?.backup_age_target_minutes ?? 0);
  const lb = recovery.body?.last_backup || {};
  const source = lb.source || "unknown";
  const summary = age >= 0
    ? `Backup age ${age.toFixed(1)}m · target ≤ ${target}m · source=${source}`
    : "No backup age reported.";
  const action = status === "red"
    ? "Investigate backup scheduler + R2 sync now."
    : status === "yellow"
    ? "Verify the next scheduled backup completes."
    : "";
  return {
    id: "backup-freshness",
    title: "Backup Freshness",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: action,
    checked_at: lb.ts || recovery.body?.computed_at || null,
    evidence: {
      pill: pill.toUpperCase(),
      backup_age_minutes: age,
      target_minutes: target,
      last_backup: lb,
      archive_count: recovery.body?.archive_count,
      warnings: recovery.body?.warnings,
    },
  };
}

function bScheduler(schedResp) {
  const endpoint = "/api/admin/backups-scheduler-state";
  if (!schedResp.ok) {
    return _unknownCard("scheduler", "Backup Scheduler",
      endpoint, "/admin/scheduler-runs",
      "Scheduler state unreachable.", schedResp.error);
  }
  const sch = schedResp.body?.scheduler || {};
  const alive = !!sch.alive;
  const resurrects = Number(sch.resurrect_count || 0);
  let status, summary, action = "";
  if (!alive && resurrects > 3) {
    status = "red";
    summary = `Scheduler not alive · ${resurrects} resurrects.`;
    action = "Investigate backup scheduler loop failures (/admin/scheduler-runs).";
  } else if (!alive) {
    status = "yellow";
    summary = "Scheduler dormant (may auto-resurrect on next tick).";
    action = "Watch for auto-resurrect within the next hour.";
  } else {
    status = "green";
    summary = `Scheduler alive${sch.in_progress ? " · run in progress" : ""}.`;
  }
  return {
    id: "scheduler",
    title: "Backup Scheduler",
    endpoint,
    drilldown: "/admin/scheduler-runs",
    status, summary, recommended_action: action,
    checked_at: sch.last_tick_ts || sch.last_resurrect_ts || null,
    evidence: sch,
  };
}

function bRpoRto(recovery) {
  const endpoint = "/api/admin/recovery/snapshot";
  if (!recovery.ok) {
    return _unknownCard("rpo-rto", "RPO / RTO",
      endpoint, "/admin/recovery",
      "Recovery snapshot unreachable.", recovery.error);
  }
  const rpo = recovery.body?.rpo || {};
  const rto = recovery.body?.rto || {};
  const rpoStatus = String(rpo.status || "").toLowerCase();
  const rtoStatus = String(rto.status || "").toLowerCase();
  const status = ["red", "yellow"].includes(rpoStatus) || ["red", "yellow"].includes(rtoStatus)
    ? (rpoStatus === "red" || rtoStatus === "red" ? "red" : "yellow")
    : (rpoStatus === "green" && rtoStatus === "green" ? "green" : "unknown");
  const summary =
    `RPO ${rpo.actual_min ?? "?"}m / target ≤ ${rpo.target_min ?? "?"}m · ` +
    `RTO drill ${rto.last_drill_min ?? "?"}m / target ≤ ${rto.target_min ?? "?"}m`;
  const action = status === "red"
    ? "Run a fresh backup + restore drill to restore RPO/RTO posture."
    : "";
  return {
    id: "rpo-rto",
    title: "RPO / RTO Posture",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: action,
    checked_at: recovery.body?.computed_at || null,
    evidence: { rpo, rto },
  };
}

function bRestoreDrill(recovery) {
  const endpoint = "/api/admin/recovery/snapshot";
  if (!recovery.ok) {
    return _unknownCard("restore-drill", "Restore Drill",
      endpoint, "/admin/recovery",
      "Recovery snapshot unreachable.", recovery.error);
  }
  const drill = recovery.body?.last_drill || {};
  if (!drill.ts) {
    return {
      id: "restore-drill",
      title: "Restore Drill",
      endpoint,
      drilldown: "/admin/recovery",
      status: "yellow",
      summary: "No restore drill on record — recovery path is unverified.",
      recommended_action: "Run a recovery drill from /admin/recovery.",
      checked_at: recovery.body?.computed_at || null,
      evidence: drill,
    };
  }
  const outcome = String(drill.outcome || "").toLowerCase();
  const status = outcome === "ok" ? "green"
    : outcome === "warning" ? "yellow"
    : outcome === "" ? "unknown" : "red";
  const summary = `Last drill ${outcome || "unknown outcome"} · ${drill.records || 0} records · ${drill.duration_min || "?"}m`;
  return {
    id: "restore-drill",
    title: "Restore Drill",
    endpoint,
    drilldown: "/admin/recovery",
    status, summary, recommended_action: "",
    checked_at: drill.ts || recovery.body?.computed_at || null,
    evidence: drill,
  };
}

function _unknownCard(id, title, endpoint, drilldown, summary, err) {
  return {
    id, title, endpoint, drilldown,
    status: "unknown", summary,
    recommended_action: "Investigate why the source endpoint is unreachable.",
    checked_at: null,
    evidence: { error: err || null },
  };
}

// ── Section metadata ─────────────────────────────────────────────
const SECTIONS = [
  { id: "disk-health",       label: "Disk Health",         icon: HardDrive,   cards: ["disk-preflight"] },
  { id: "r2-health",         label: "Cloudflare R2 Health", icon: Database,   cards: ["r2-bucket", "r2-retention"] },
  { id: "backup-health",     label: "Backup Health",       icon: Archive,     cards: ["backup-freshness", "scheduler"] },
  { id: "recovery-readiness",label: "Recovery Readiness",  icon: ShieldCheck, cards: ["rpo-rto", "restore-drill"] },
];

// ── Maintenance action deep-links into OCC ───────────────────────
// Sprint 2 rule: never duplicate action execution. Every entry below
// is a deep-link into the OCC Maintenance Operations Console with a
// `?highlight=<operation-id>` param that pulses the correct op card.
const MAINTENANCE_ACTIONS = [
  {
    id: "storage.audit",
    title: "Storage Audit",
    description: "Read-only inspection of local storage consumers.",
    never_touches: "Does not delete anything.",
  },
  {
    id: "storage.safe_cleanup",
    title: "Safe Cleanup",
    description: "Dry-run + apply for known-safe temp / stale artifacts.",
    never_touches: "Never touches R2, never deletes user documents.",
  },
  {
    id: "storage.r2_migration",
    title: "R2 Migration",
    description: "Dry-run + apply for pushing eligible local files to R2.",
    never_touches: "Never deletes the source before R2 confirmation.",
  },
  {
    id: "r2.health",
    title: "R2 Health Refresh",
    description: "Re-probe R2 HEAD/bucket + refresh status snapshot.",
    never_touches: "Read-only.",
  },
  {
    id: "backups.health",
    title: "Backup Health Refresh",
    description: "Re-probe local backup directory + refresh status.",
    never_touches: "Read-only.",
  },
];

// ── Trust Gaps · registered from Track 27.04 / 27.05 audit ──────
const TRUST_GAPS = [
  { id: "gap-r2-orphan-cleanup",
    title: "Orphan R2 object cleanup sweep",
    severity: "P1", owner: "platform-storage", target_track: "27.06",
    risk: "medium",
    current_status: "Not scheduled — retention runner missing.",
    blocks_production: false },
  { id: "gap-upload-metrics",
    title: "Upload success/failure metrics to OCC",
    severity: "P1", owner: "platform-storage", target_track: "27.06",
    risk: "low",
    current_status: "No aggregate — per-upload logs only.",
    blocks_production: false },
  { id: "gap-retention-runner",
    title: "Schedule R2 retention runner",
    severity: "P1", owner: "platform-storage", target_track: "27.06",
    risk: "medium",
    current_status: "Manual only — no scheduler binding.",
    blocks_production: false },
  { id: "gap-project-docs-migration",
    title: "Migrate local project docs to R2",
    severity: "P2", owner: "platform-storage", target_track: "27.06",
    risk: "low",
    current_status: "Dry-run exists; apply not scheduled.",
    blocks_production: false },
  { id: "gap-runtime-r2-fallback",
    title: "Runtime R2 fallback (local → R2 on write)",
    severity: "P2", owner: "platform-storage", target_track: "27.07",
    risk: "medium",
    current_status: "Backups only — runtime uploads still local.",
    blocks_production: false },
  { id: "gap-inflight-durability",
    title: "In-flight upload durability",
    severity: "P2", owner: "platform-storage", target_track: "27.07",
    risk: "low",
    current_status: "No resumable-upload contract.",
    blocks_production: false },
  { id: "gap-r2-latency",
    title: "R2 latency histogram surfaced in OCC",
    severity: "P2", owner: "platform-observability", target_track: "27.08",
    risk: "low",
    current_status: "Per-probe latency only — no percentiles.",
    blocks_production: false },
  { id: "gap-composite-score",
    title: "Composite storage health score",
    severity: "P2", owner: "platform-storage", target_track: "27.07",
    risk: "low",
    current_status: "Section-level worst-case only.",
    blocks_production: false },
  { id: "gap-507-surface",
    title: "Public 507 error surface for callers",
    severity: "P2", owner: "platform-api", target_track: "27.07",
    risk: "medium",
    current_status: "Backend returns 507 but frontend has no toast/UI shell.",
    blocks_production: false },
];

const SEVERITY_STYLES = {
  P0: "bg-rose-100 text-rose-800 ring-rose-200",
  P1: "bg-amber-100 text-amber-900 ring-amber-200",
  P2: "bg-slate-100 text-slate-700 ring-slate-300",
};

// ── Page ─────────────────────────────────────────────────────────
export default function AdminStorageRecovery() {
  const [recovery, setRecovery] = useState(null);
  const [scheduler, setScheduler] = useState(null);
  const [integrations, setIntegrations] = useState(null);
  const [auditRows, setAuditRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshingAt, setRefreshingAt] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { card: drawerCard, open: drawerOpen, setOpen: setDrawerOpen, openWith } =
    useEvidenceDrawer();

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rc, sc, ih, au] = await Promise.all([
        probe("/admin/recovery/snapshot"),
        probe("/admin/backups-scheduler-state"),
        probe("/admin/integrations/health"),
        probe("/admin/operations-control/audit?limit=25"),
      ]);
      setRecovery(rc);
      setScheduler(sc);
      setIntegrations(ih);
      setAuditRows((au.body?.audit || []).filter((r) =>
        ["storage", "r2", "backups"].some((k) => String(r.operation_id || "").startsWith(k))
      ));
      // machine timestamp — always rendered via formatPlatformTime.
      setRefreshingAt(new Date().toISOString()); // TRACK-27.03-EXEMPT: never displayed as raw ISO.
      if (!rc.ok && [401, 403].includes(rc.status)) {
        setError("Super-admin access required.");
      }
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const cards = useMemo(() => {
    if (!recovery || !scheduler || !integrations) return [];
    return [
      bDiskPreflight(recovery),
      bR2Bucket(recovery, integrations),
      bR2Retention(recovery),
      bBackupFreshness(recovery),
      bScheduler(scheduler),
      bRpoRto(recovery),
      bRestoreDrill(recovery),
    ];
  }, [recovery, scheduler, integrations]);

  const cardsById = useMemo(() =>
    Object.fromEntries(cards.map((c) => [c.id, c])), [cards]);

  const overall = worstStatus(cards);
  const counts = useMemo(() => {
    const c = { green: 0, yellow: 0, red: 0, unknown: 0 };
    cards.forEach((x) => { c[x.status] = (c[x.status] || 0) + 1; });
    return c;
  }, [cards]);
  const highest = useMemo(
    () => sortCardsByAttention(cards).find((c) => c.status !== "green") || null,
    [cards],
  );

  const filterFn = useCallback((c) => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return (
      c.title.toLowerCase().includes(q) ||
      (c.summary || "").toLowerCase().includes(q) ||
      (c.endpoint || "").toLowerCase().includes(q)
    );
  }, [statusFilter, query]);

  return (
    <div className="min-h-screen bg-slate-50" data-testid="admin-storage-recovery-root">
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle="Storage & Recovery"
        subtitle="Disk · R2 · backups · recovery drills. One evidence-first surface."
        primaryActions={
          <div className="flex items-center gap-2">
            <Link
              to="/admin"
              className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100"
              data-testid="storage-recovery-back-adminos"
            >
              ← Admin OS
            </Link>
            <button
              type="button"
              onClick={reload}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
              data-testid="storage-recovery-refresh"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        }
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        {/* ── Executive Storage Verdict ─────────────────────── */}
        <section
          className="mb-6 rounded-lg border border-slate-200 bg-white p-4"
          data-testid="storage-recovery-verdict"
        >
          <div className="flex flex-wrap items-center gap-4">
            <div className="min-w-[220px]">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                Executive Verdict
              </div>
              <div className="mt-1 flex items-center gap-2">
                <TrustStatusPill
                  status={overall}
                  testid="storage-recovery-verdict-pill"
                />
                <span
                  className="text-sm font-semibold text-slate-900"
                  data-testid="storage-recovery-verdict-summary"
                >
                  {loading
                    ? "Loading storage evidence…"
                    : overall === "red"
                    ? "Storage / recovery has a critical condition."
                    : overall === "yellow"
                    ? "Storage / recovery needs attention."
                    : overall === "green"
                    ? "Storage & recovery healthy across every wired signal."
                    : "Storage evidence unavailable — press Refresh."}
                </span>
              </div>
              {highest ? (
                <p
                  className="mt-2 text-xs text-slate-600"
                  data-testid="storage-recovery-verdict-highest"
                >
                  Highest-risk item · <strong>{highest.title}</strong>: {highest.summary}
                </p>
              ) : null}
            </div>
            <div className="flex items-center gap-4 ml-auto text-sm">
              {[
                ["green", "Healthy"], ["yellow", "Attention"],
                ["red", "Critical"], ["unknown", "Unknown"],
              ].map(([k, label]) => (
                <div key={k} data-testid={`storage-recovery-count-${k}`}>
                  <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                    {label}
                  </div>
                  <div
                    className={`font-black text-xl leading-none ${TRUST_STATUS_STYLES[k]?.text || "text-slate-800"}`}
                  >
                    {counts[k] || 0}
                  </div>
                </div>
              ))}
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  Last refreshed
                </div>
                <div
                  className="font-mono text-xs text-slate-800"
                  data-testid="storage-recovery-last-refreshed"
                >
                  {refreshingAt ? formatPlatformTime(refreshingAt) : "—"}
                </div>
              </div>
            </div>
          </div>
          <div
            className="mt-3 text-[11px] font-mono text-slate-500"
            data-testid="storage-recovery-verdict-sources"
          >
            Sources: /api/admin/recovery/snapshot · /api/admin/backups-scheduler-state · /api/admin/integrations/health · /api/admin/operations-control/audit
          </div>
        </section>

        {error ? (
          <div
            className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
            data-testid="storage-recovery-error"
          >
            {error}
          </div>
        ) : null}

        {/* ── Filter row ─────────────────────────────────────── */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[220px] max-w-md">
            <SearchIcon className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter storage cards by title, summary, or endpoint…"
              className="w-full rounded-md border border-slate-300 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
              data-testid="storage-recovery-search"
            />
          </div>
          {["all", "red", "yellow", "unknown", "green"].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`rounded-md border px-2 py-1 text-[11px] font-semibold uppercase tracking-wider ${
                statusFilter === s
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
              }`}
              data-testid={`storage-recovery-filter-${s}`}
            >
              {s === "all" ? "All" : (TRUST_STATUS_STYLES[s]?.label || s)}
            </button>
          ))}
        </div>

        {/* ── Health sections ───────────────────────────────── */}
        <div className="space-y-6" data-testid="storage-recovery-sections">
          {SECTIONS.map((sec) => {
            const secCards = sec.cards
              .map((id) => cardsById[id])
              .filter(Boolean);
            const filtered = sortCardsByAttention(secCards).filter(filterFn);
            const secStatus = worstStatus(secCards);
            const Icon = sec.icon;
            return (
              <section key={sec.id} data-testid={`storage-recovery-section-${sec.id}`}>
                <div className="mb-2 flex items-center gap-2">
                  <Icon className="w-4 h-4 text-slate-500" />
                  <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                    {sec.label}
                  </div>
                  <TrustStatusPill
                    status={secStatus}
                    testid={`storage-recovery-section-${sec.id}-status`}
                  />
                  <div className="text-[10px] font-mono text-slate-400">
                    {filtered.length}/{secCards.length} card(s)
                  </div>
                </div>
                {filtered.length === 0 && !loading ? (
                  <div
                    className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-4 text-xs text-slate-500"
                    data-testid={`storage-recovery-section-${sec.id}-empty`}
                  >
                    {secCards.length === 0
                      ? "Loading…"
                      : "No cards match the current filter."}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                    {filtered.map((c) => (
                      <HealthCard
                        key={c.id}
                        card={c}
                        onOpen={openWith}
                        testidPrefix="storage-recovery-card"
                      />
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>

        {/* ── Maintenance actions (deep-link only) ──────────── */}
        <section
          className="mt-8"
          data-testid="storage-recovery-actions"
        >
          <div className="mb-2 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-slate-500" />
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
              Storage Maintenance Actions
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              deep-link · runs in OCC console (dry-run first)
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {MAINTENANCE_ACTIONS.map((a) => (
              <Link
                key={a.id}
                to={`/admin/operations-control?highlight=${encodeURIComponent(a.id)}`}
                data-testid={`storage-recovery-action-${a.id}`}
                className="group relative flex flex-col rounded-lg border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-150 p-4"
              >
                <div className="text-sm font-semibold text-slate-900 leading-tight">
                  {a.title}
                </div>
                <p className="mt-1 text-[12px] text-slate-600 leading-snug">
                  {a.description}
                </p>
                <p className="mt-2 text-[11px] font-mono text-slate-500">
                  Never touches: {a.never_touches}
                </p>
                <div className="mt-3 text-[11px] font-mono text-emerald-700">
                  Open in OCC →
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* ── Recent storage events ─────────────────────────── */}
        <section
          className="mt-8"
          data-testid="storage-recovery-events"
        >
          <div className="mb-2 flex items-center gap-2">
            <History className="w-4 h-4 text-slate-500" />
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
              Recent Storage Events
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              /api/admin/operations-control/audit (storage · r2 · backups)
            </div>
          </div>
          {auditRows.length === 0 ? (
            <div
              className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-4 text-xs text-slate-500"
              data-testid="storage-recovery-events-empty"
            >
              No storage operations recorded in the recent audit window.
            </div>
          ) : (
            <ul
              className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
              data-testid="storage-recovery-events-list"
            >
              {auditRows.slice(0, 12).map((r) => (
                <li
                  key={r.action_id}
                  className="px-4 py-2 text-xs"
                  data-testid={`storage-recovery-event-${r.action_id}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-800">{r.operation_id}</span>
                    <span
                      className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                        r.mode === "apply"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-sky-100 text-sky-800"
                      }`}
                    >
                      {r.mode}
                    </span>
                  </div>
                  <div className="text-slate-500 flex items-center justify-between mt-0.5">
                    <span>{r.actor_email || r.actor_id}</span>
                    <span>{formatRelativeTime(r.ts)}</span>
                  </div>
                  {r.error ? (
                    <div className="mt-1 text-rose-700 text-[11px]">error: {r.error}</div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ── Trust gaps ─────────────────────────────────────── */}
        <section
          className="mt-8"
          data-testid="storage-recovery-gaps"
        >
          <div className="mb-2 flex items-center gap-2">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
              Storage Trust Gaps (Track 27.04 / 27.05 audit backlog)
            </div>
          </div>
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Gap</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Severity</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Owner</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Target</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Risk</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Status</th>
                  <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Blocks prod?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {TRUST_GAPS.map((g) => (
                  <tr key={g.id} data-testid={`storage-recovery-${g.id}`}>
                    <td className="px-3 py-2 text-slate-800 font-medium">{g.title}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ring-1 ${SEVERITY_STYLES[g.severity] || "bg-slate-100 text-slate-700 ring-slate-300"}`}>
                        {g.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-700 font-mono">{g.owner}</td>
                    <td className="px-3 py-2 text-slate-700 font-mono">{g.target_track}</td>
                    <td className="px-3 py-2 text-slate-700">{g.risk}</td>
                    <td className="px-3 py-2 text-slate-700">{g.current_status}</td>
                    <td className="px-3 py-2 text-slate-700">
                      {g.blocks_production ? (
                        <span className="text-rose-700 font-semibold">YES</span>
                      ) : (
                        <span className="text-slate-500">no</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Evidence drawer ─────────────────────────────── */}
        <EvidenceDrawer
          card={drawerCard}
          open={drawerOpen}
          onOpenChange={setDrawerOpen}
          testidPrefix="storage-recovery-drawer"
        />
      </PortalShell>
    </div>
  );
}
