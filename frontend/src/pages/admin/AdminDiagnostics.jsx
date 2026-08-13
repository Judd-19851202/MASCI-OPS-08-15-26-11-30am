// TRACK 25 · SPRINT 6 · Admin OS · Diagnostics Domain.
import React from "react";
import { Activity, Database, Gauge, ClipboardList } from "lucide-react";
import DomainLandingShell from "@/components/admin/trust/DomainLandingShell";
import { canonicalReleaseShaShort } from "@/lib/versionCache";

function _api_health(probes) {
  const p = probes.health;
  if (!p?.ok) return { status: "red", summary: "API not reachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  return { status: b.ok ? "green" : "red",
    summary: b.ok ? `Service ${b.service || "svc"} reporting OK` : "Service reporting FAILURE",
    checked_at: b.ts,
    evidence: b };
}
function _version_diag(probes) {
  const p = probes.version;
  if (!p?.ok) return { status: "unknown", summary: "Version endpoint unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const up = Number(b.uptime_s || 0);
  const h = Math.floor(up / 3600); const m = Math.floor((up % 3600) / 60);
  return { status: "green",
    summary: `Build ${canonicalReleaseShaShort(b) || "unverified"} · uptime ${h}h ${m}m`,
    checked_at: b.started_at,
    evidence: b };
}
function _system_health(probes) {
  const p = probes.sys;
  if (!p?.ok) return { status: "unknown", summary: "System health probe unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const overall = String(b.overall || "").toLowerCase();
  const cards = b.cards || [];
  // TRACK 28.11 · Prefer backend-emitted canonical counts. Falls back
  // to legacy status parsing but includes "green" and "pass" as
  // healthy synonyms so the old "0/8" bug (green ≠ ok) cannot recur.
  const canonical = b.counts || null;
  let healthy, applicable, bad;
  if (canonical && typeof canonical.healthy === "number") {
    healthy = canonical.healthy;
    applicable = canonical.total_applicable ?? cards.length;
    bad = canonical.critical + canonical.attention + canonical.unknown;
  } else {
    const HEALTHY_SYN = new Set(["ok", "healthy", "green", "pass"]);
    const NON_APP = new Set(["not_applicable", "n/a", "disabled"]);
    const applicableCards = cards.filter(
      (c) => !NON_APP.has(String(c.status || "").toLowerCase())
    );
    bad = applicableCards.filter(
      (c) => !HEALTHY_SYN.has(String(c.status || "").toLowerCase())
    ).length;
    healthy = applicableCards.length - bad;
    applicable = applicableCards.length;
  }
  const status = overall === "critical" ? "red" : (bad > 0 || overall === "warning" || overall === "yellow") ? "yellow" : "green";
  return { status,
    summary: `${healthy}/${applicable} system health cards healthy`,
    recommended_action: bad ? "Open Diagnostics → System Health for details." : "",
    checked_at: b.checked_at,
    evidence: { overall, counts: canonical, cards_sample: cards.slice(0, 6) } };
}
function _occ_health(probes) {
  const p = probes.occ;
  if (!p?.ok) return { status: "unknown", summary: "OCC health aggregator unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const counts = b.counts || {};
  const canonicalCounts = b.canonical_counts || null;
  const overall = String(b.overall_status || "").toLowerCase();
  const status = overall === "red" ? "red" : overall === "yellow" ? "yellow" : overall === "green" ? "green" : "unknown";
  // TRACK 28.11 · When shared root causes are present, surface the
  // *unique* count so the operator doesn't panic over "5 critical"
  // when 2 of those criticals share one R2-bucket root cause.
  const uniqueCrit = Number(b.unique_critical_root_causes ?? counts.red ?? 0);
  const rootGroups = b.root_cause_groups || {};
  const groupNote = Object.keys(rootGroups).length
    ? ` · ${Object.keys(rootGroups).length} shared root cause${Object.keys(rootGroups).length > 1 ? "s" : ""}`
    : "";
  return { status,
    summary: `OCC · ${uniqueCrit} unique critical · ${counts.yellow || 0} attention · ${counts.green || 0} healthy · ${counts.unknown || 0} unknown${groupNote}`,
    checked_at: b.generated_at,
    evidence: { counts, canonical_counts: canonicalCounts, root_cause_groups: rootGroups, total_cards: b.total_cards, sections: (b.sections || []).map((s) => ({ id: s.id, status: s.status, cards: s.cards.length })) } };
}
function _scheduler_runs(probes) {
  const p = probes.scheduler;
  if (!p?.ok) return { status: "unknown", summary: "Scheduler runs unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const total = Number(b.total || 0);
  const failed = Number(b.failed_total || 0);
  const status = failed > 3 ? "red" : failed > 0 ? "yellow" : total ? "green" : "yellow";
  return { status,
    summary: `${total} scheduler run(s) tracked · ${failed} failed`,
    recommended_action: failed ? "Open Scheduler Runs to inspect failures." : "",
    evidence: { total, failed_total: failed, dedup_total: b.dedup_total, items_sample: (b.items || []).slice(0, 3) } };
}
function _prod_cert_diag(probes) {
  const p = probes.prod_cert;
  if (!p?.ok) return { status: "unknown", summary: "Production certification unreachable.", evidence: { error: p?.error } };
  const b = p.body || {};
  const band = String(b.platform_band || "").toLowerCase();
  const counters = b.counters || {};
  const defaultWindow = b.freshness_policy?.default_window_hours;
  const status = ["green", "healthy"].includes(band) ? "green"
    : ["yellow", "warning"].includes(band) ? "yellow"
    : ["red", "critical"].includes(band) ? "red" : "unknown";
  return { status,
    summary: `Platform band ${band || "unknown"} · ${counters.stale || 0} stale · window ${defaultWindow || "?"}h`,
    checked_at: b.generated_at,
    evidence: { platform_band: band, counters: b.counters, track: b.track } };
}
const manifest = {
  id: "diagnostics",
  label: "Diagnostics",
  subtitle: "Runtime health · system probes · OCC snapshot · scheduler · certification.",
  probes: [
    { id: "health", path: "/health" },
    { id: "version", path: "/version" },
    { id: "sys", path: "/admin/system-health" },
    { id: "occ", path: "/admin/occ/health" },
    { id: "scheduler", path: "/admin/scheduler-runs?limit=5" },
    { id: "prod_cert", path: "/admin/production-certification" },
  ],
  cards: [
    { id: "api-health", section: "runtime", title: "API Health",
      endpoint: "/api/health", drilldown: "/admin/system-health", evaluator: _api_health },
    { id: "build-version", section: "runtime", title: "Build & Uptime",
      endpoint: "/api/version", drilldown: "/admin/system-health", evaluator: _version_diag },
    { id: "system-health", section: "probes", title: "System Health Cards",
      endpoint: "/api/admin/system-health", drilldown: "/admin/system-health", evaluator: _system_health },
    { id: "occ-snapshot", section: "probes", title: "OCC Trust Snapshot",
      endpoint: "/api/admin/occ/health", drilldown: "/admin/operations-control", evaluator: _occ_health },
    { id: "scheduler-runs", section: "workers", title: "Scheduler Runs",
      endpoint: "/api/admin/scheduler-runs", drilldown: "/admin/scheduler-runs", evaluator: _scheduler_runs },
    { id: "prod-cert", section: "certification", title: "Production Certification",
      endpoint: "/api/admin/production-certification", drilldown: "/admin/governance-trust", evaluator: _prod_cert_diag },
  ],
  sections: [
    { id: "runtime", label: "Runtime", icon: Activity, cards: ["api-health", "build-version"] },
    { id: "probes", label: "Probes & OCC", icon: Gauge, cards: ["system-health", "occ-snapshot"] },
    { id: "workers", label: "Workers & Schedulers", icon: Database, cards: ["scheduler-runs"] },
    { id: "certification", label: "Certification", icon: ClipboardList, cards: ["prod-cert"] },
  ],
  maintenance_actions: [
    { id: "system-health-open", title: "System Health Detail",
      deep_link: "/admin/system-health",
      description: "Per-probe health cards, deeper than the OCC snapshot.",
      never_touches: "Read-only." },
    { id: "scheduler-runs-open", title: "Scheduler Runs",
      deep_link: "/admin/scheduler-runs",
      description: "Full history of scheduler run outcomes.",
      never_touches: "Read-only." },
    { id: "occ-open", title: "OCC Trust Center",
      deep_link: "/admin/operations-control",
      description: "Full 8-section Trust Layer + maintenance console.",
      never_touches: "Trust layer is read-only; maintenance is dry-run first." },
  ],
  trust_gaps: [
    { id: "gap-diag-error-log", title: "Recent errors / Sentry-style log surface",
      severity: "P1", owner: "platform-observability", target_track: "27.12", risk: "medium",
      current_status: "Backend logs only — no admin UI surface.", blocks_production: false },
    { id: "gap-diag-latency", title: "Endpoint latency percentiles",
      severity: "P2", owner: "platform-observability", target_track: "27.12", risk: "low",
      current_status: "Not measured.", blocks_production: false },
    { id: "gap-diag-cluster-capacity", title: "Mongo cluster capacity & connection pool surface",
      severity: "P2", owner: "platform-observability", target_track: "27.13", risk: "low",
      current_status: "Read-only cluster capacity surface is now exposed through /api/admin/database.", blocks_production: false },
  ],
  source_endpoints_line: "/api/health · /api/version · /api/admin/system-health · /api/admin/occ/health · /api/admin/scheduler-runs · /api/admin/production-certification",
};

export default function AdminDiagnostics() {
  return <DomainLandingShell manifest={manifest} testidPrefix="admin-diagnostics" />;
}
