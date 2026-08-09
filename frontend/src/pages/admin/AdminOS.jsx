// TRACK 25 · SPRINT 1 · Admin Operating System — Canonical Landing.
//
// Mounted at /admin (AppRoutes.jsx). Renders the ten operational
// domains defined in TRACK_25_ADMIN_OS_FINAL_COMPLETION.md:
//
//   1  Platform Overview       6  Identity & Security
//   2  Operations Control      7  Governance & Trust
//   3  Storage & Recovery      8  Platform Configuration
//   4  AI Operations           9  Diagnostics
//   5  Communications         10  Maintenance
//
// Each card:
//   - Links to the CANONICAL existing route for that domain (no dead
//     links, no skeleton pages).
//   - Probes an existing endpoint for a live health signal.
//   - Falls back to a neutral "Needs wiring" pill when no endpoint
//     is available yet (honest state — no invented metrics).
//
// Uses SideNavV3 (single canonical sidebar) + CommandPaletteProvider
// (mounted at the router level in AppRoutes.jsx). Legacy hubs
// (AdminHub, AdminHubV2, AdminHubSwitcher, AdminHubV3) still exist on
// disk but their routes redirect here — no duplicate admin experience.
//
// Zero-UTC contract (Track 27.03): all operator-facing timestamps go
// through `formatPlatformTime` / `formatRelativeTime`.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  Archive,
  BarChart3,
  ChevronRight,
  Cog,
  Database,
  Download,
  HardDrive,
  Mail,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { PortalShell } from "../../design-system";
import { ResponsiveSummaryStrip } from "@/design-system/responsive";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import { buildPortalAuthHeaders } from "@/lib/authHeaders";
import { formatRelativeTime } from "@/lib/platformTime";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const DEFAULT_PROBE_TIMEOUT_MS = 15000;
const PROBE_TIMEOUTS_MS = {
  "/api/admin/occ/health": 25000,
  "/api/admin/operations-control/overview": 20000,
  "/api/admin/governance/summary": 20000,
};

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

// ── HTTP helper ─────────────────────────────────────────────────────
function adminHeaders() {
  return buildPortalAuthHeaders({ "Content-Type": "application/json" });
}

async function probe(path, attempt = 0) {
  if (!path) return { ok: false, body: null, status: 0 };
  const controller = new AbortController();
  const timeoutMs = PROBE_TIMEOUTS_MS[path] || DEFAULT_PROBE_TIMEOUT_MS;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(`${API}${path}`, { headers: adminHeaders(), signal: controller.signal });
    if (!r.ok && [502, 503, 504].includes(r.status) && attempt < 1) {
      await delay(300);
      return probe(path, attempt + 1);
    }
    return {
      ok: r.ok,
      status: r.status,
      body: r.ok ? await r.json() : null,
    };
  } catch (error) {
    const timedOut = error?.name === "AbortError";
    if (attempt < 1) {
      await delay(300);
      return probe(path, attempt + 1);
    }
    return {
      ok: false,
      body: null,
      status: 0,
      timed_out: timedOut,
      error_kind: timedOut ? "timeout" : "network",
    };
  } finally {
    window.clearTimeout(timeoutId);
  }
}

// TRACK 25 · SPRINT 7/8 · Global Trust Snapshot export.
// Walks the current in-memory domain results and produces a
// self-contained Markdown snapshot of the platform's trust state.
// No new endpoints — this is a client-side composition of the same
// data already rendered on the page. No secrets included; only the
// summarized status + source endpoints + counts.
function _statusLabel(s) {
  return ({ healthy: "HEALTHY", warning: "ATTENTION", critical: "CRITICAL",
    wiring: "AWAITING SIGNAL", offline: "OFFLINE", loading: "LOADING" })[s] || String(s || "?").toUpperCase();
}

function mapCanonicalStatus(value) {
  const normalized = String(value || "UNVERIFIABLE").toUpperCase();
  if (normalized === "VERIFIED" || normalized === "GREEN" || normalized === "HEALTHY") return "healthy";
  if (normalized === "DEGRADED" || normalized === "YELLOW" || normalized === "WARNING" || normalized === "AMBER") return "warning";
  if (normalized === "NOT_APPLICABLE") return "wiring";
  return normalized === "LOADING" ? "loading" : "critical";
}

function getCanonicalCounts(payload) {
  const canonical = payload?.canonical_counts;
  if (canonical) {
    return {
      verified: Number(canonical.verified || 0),
      degraded: Number(canonical.degraded || 0),
      mismatch: Number(canonical.mismatch || 0),
      unverifiable: Number(canonical.unverifiable || 0),
      notApplicable: Number(canonical.not_applicable || 0),
      totalApplicable: Number(canonical.total_applicable || 0),
    };
  }

  const counts = payload?.counts || {};
  return {
    verified: Number(counts.verified || counts.VERIFIED || 0),
    degraded: Number(counts.degraded || counts.DEGRADED || 0),
    mismatch: Number(counts.mismatch || counts.MISMATCH || 0),
    unverifiable: Number(counts.unverifiable || counts.UNVERIFIABLE || 0),
    notApplicable: Number(counts.not_applicable || counts.NOT_APPLICABLE || 0),
    totalApplicable: Number(counts.total_applicable || counts.total || 0),
  };
}

function isNotApplicableProbe(probeRow) {
  return String(probeRow?.status || "").toLowerCase() === "disabled" && !!probeRow?.mocked;
}
function exportTrustSnapshot(domains, results, summary, overallStatus) {
  const now = new Date();
  // TRACK-27.03-EXEMPT: rendered locally via `toLocaleString` — never a raw ISO shown to operators.
  const localStamp = now.toLocaleString(undefined, {
    dateStyle: "medium", timeStyle: "short",
  });
  const lines = [];
  lines.push(`# MASCI Platform · Trust Snapshot`);
  lines.push(``);
  lines.push(`- Generated: **${localStamp}** (your local time)`);
  lines.push(`- Overall posture: **${_statusLabel(overallStatus)}**`);
  lines.push(`- Healthy: ${summary.healthy} · Attention: ${summary.warning} · Critical: ${summary.critical} · Awaiting signal: ${summary.pending} · Total domains: ${domains.length}`);
  lines.push(``);
  lines.push(`## Domains`);
  for (const d of domains) {
    const r = d.probe ? results[d.id] : null;
    const evaluated = r?.pending
      ? { status: "loading", metric: "…", detail: "Loading live data…" }
      : r
      ? d.evaluate(r)
      : d.probe
      ? { status: "loading" }
      : d.evaluate(null);
    lines.push(``);
    lines.push(`### ${String(d.number).padStart(2, "0")} · ${d.label} · ${_statusLabel(evaluated.status)}`);
    lines.push(`- Canonical route: \`${d.to}\``);
    if (d.probe) lines.push(`- Source endpoint: \`${d.probe}\``);
    if (evaluated.metric) lines.push(`- Metric: **${evaluated.metric}**`);
    if (evaluated.detail) lines.push(`- Detail: ${evaluated.detail}`);
  }
  lines.push(``);
  lines.push(`---`);
  lines.push(`Snapshot generated from live probes on the Admin OS landing at /admin. No secrets included; only summarized status, metrics, and source endpoints.`);

  const md = lines.join("\n");
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const iso = now.toISOString().replace(/[:.]/g, "-").split("Z")[0]; // TRACK-27.03-EXEMPT: filename token only, never displayed.
  a.download = `masci-trust-snapshot-${iso}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Status pill ────────────────────────────────────────────────────
const STATUS_STYLES = {
  healthy: {
    bg: "bg-emerald-100",
    text: "text-emerald-800",
    ring: "ring-emerald-200",
    label: "HEALTHY",
  },
  warning: {
    bg: "bg-amber-100",
    text: "text-amber-900",
    ring: "ring-amber-200",
    label: "ATTENTION",
  },
  critical: {
    bg: "bg-rose-100",
    text: "text-rose-900",
    ring: "ring-rose-200",
    label: "CRITICAL",
  },
  loading: {
    bg: "bg-slate-100",
    text: "text-slate-600",
    ring: "ring-slate-200",
    label: "LOADING",
  },
  wiring: {
    bg: "bg-slate-100",
    text: "text-slate-600",
    ring: "ring-slate-200",
    label: "AWAITING SIGNAL",
  },
  offline: {
    bg: "bg-slate-200",
    text: "text-slate-700",
    ring: "ring-slate-300",
    label: "OFFLINE",
  },
};

function StatusPill({ status, testid }) {
  const { t } = useT();
  const s = STATUS_STYLES[status] || STATUS_STYLES.loading;
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ${s.bg} ${s.text} ring-1 ${s.ring}`}
    >
      {t(s.label)}
    </span>
  );
}

const ACTION_PRIORITY = {
  critical: 0,
  warning: 1,
  wiring: 2,
  offline: 2,
  loading: 3,
  healthy: 4,
};

function getEvaluatedDomain(domain, probeResult, loaded) {
  if (!domain.probe) {
    return domain.evaluate(null);
  }
  if (probeResult?.pending) {
    return { status: "loading", metric: "…", detail: "Loading live data…", stampedAt: null };
  }
  if (probeResult?.ok) {
    return domain.evaluate(probeResult);
  }
  if (probeResult?.status === 401 || probeResult?.status === 403) {
    return { status: "wiring", metric: "—", detail: "Sign in as admin to load live status.", stampedAt: null };
  }
  if (probeResult?.timed_out) {
    return { status: "offline", metric: "—", detail: "Live signal timed out. Refresh to retry.", stampedAt: null };
  }
  if (probeResult?.status >= 500 || probeResult?.error_kind === "network") {
    return { status: "offline", metric: "—", detail: "Live signal unavailable right now.", stampedAt: null };
  }
  if (loaded) {
    return { status: "offline", metric: "—", detail: "Probe unavailable.", stampedAt: null };
  }
  return { status: "loading", metric: "…", detail: "Loading live data…", stampedAt: null };
}

function getDomainAction(domain, evaluation) {
  const detail = typeof evaluation?.detail === "string" ? evaluation.detail : domain.description;
  const tone = evaluation?.status === "critical" ? "critical" : evaluation?.status === "warning" ? "warning" : "pending";

  switch (domain.id) {
    case "platform-overview":
      return {
        tone,
        title: "Confirm platform attestation and readiness",
        summary: detail,
        action: "Open Platform Overview",
      };
    case "operations-control":
      return {
        tone,
        title: "Review shared operational blockers",
        summary: detail,
        action: "Open Operations Control",
      };
    case "storage-recovery":
      return {
        tone,
        title: "Check backup freshness and restore evidence",
        summary: detail,
        action: "Open Storage & Recovery",
      };
    case "communications":
      return {
        tone,
        title: "Inspect routing and scheduler posture",
        summary: detail,
        action: "Open Communications",
      };
    case "identity-security":
      return {
        tone,
        title: "Review session inventory and access posture",
        summary: detail,
        action: "Open Identity & Security",
      };
    case "governance-trust":
      return {
        tone,
        title: "Resolve governance and readiness findings",
        summary: detail,
        action: "Open Governance & Trust",
      };
    case "platform-configuration":
      return {
        tone,
        title: "Verify integration and platform configuration health",
        summary: detail,
        action: "Open Platform Configuration",
      };
    case "diagnostics":
      return {
        tone,
        title: "Inspect runtime diagnostics and worker health",
        summary: detail,
        action: "Open Diagnostics",
      };
    case "maintenance":
      return {
        tone,
        title: "Use reviewed maintenance controls only when needed",
        summary: detail,
        action: "Open Maintenance",
      };
    default:
      return {
        tone,
        title: domain.label,
        summary: detail,
        action: `Open ${domain.label}`,
      };
  }
}

// ── Domain card ────────────────────────────────────────────────────
function DomainCard({ domain, evaluation }) {
  const { t } = useT();
  const Icon = domain.icon;

  return (
    <Link
      to={domain.to}
      data-testid={`admin-os-card-${domain.id}`}
      className="group relative flex flex-col rounded-lg border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-150 hover:-translate-y-0.5 overflow-hidden"
    >
      <span
        aria-hidden="true"
        className="absolute left-0 top-0 bottom-0 w-1"
        style={{ backgroundColor: domain.stripe }}
      />
      <div className="p-5 pl-6 flex flex-col gap-3 min-h-[168px]">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold"
                data-testid={`admin-os-card-${domain.id}-number`}
              >
                {String(domain.number).padStart(2, "0")}
              </span>
              <StatusPill
                status={evaluation.status}
                testid={`admin-os-card-${domain.id}-status`}
              />
            </div>
            <h3
              className="mt-0.5 font-display text-base font-black tracking-tight text-slate-900 leading-tight"
              data-testid={`admin-os-card-${domain.id}-label`}
            >
              {t(domain.label)}
            </h3>
          </div>
          <ChevronRight className="w-4 h-4 mt-2 text-slate-400 group-hover:text-slate-700 group-hover:translate-x-0.5 transition-all shrink-0" />
        </div>

        <p className="text-[12px] text-slate-600 leading-snug">
          {t(domain.description)}
        </p>

        <div className="mt-auto flex items-baseline justify-between gap-2 pt-2 border-t border-slate-100">
          <div className="min-w-0">
            <div
              className="text-2xl font-black text-slate-900 leading-none"
              data-testid={`admin-os-card-${domain.id}-metric`}
            >
              {evaluation.metric}
            </div>
            <div
              className="mt-1 text-[11px] text-slate-500 leading-tight truncate"
              data-testid={`admin-os-card-${domain.id}-detail`}
            >
              {typeof evaluation.detail === "string" ? t(evaluation.detail) : evaluation.detail}
            </div>
          </div>
          {evaluation.stampedAt ? (
            <div
              className="text-[10px] font-mono text-slate-400 text-right shrink-0"
              data-testid={`admin-os-card-${domain.id}-stamp`}
              title={t("Last checked (your local time)")}
            >
              {formatRelativeTime(evaluation.stampedAt)}
            </div>
          ) : null}
        </div>
      </div>
    </Link>
  );
}

// ── The 10 domains ─────────────────────────────────────────────────
// Each domain declares:
//   - to: canonical route (must already exist in AppRoutes.jsx)
//   - probe: endpoint path (null → "Needs wiring")
//   - evaluate(result): returns { status, metric, detail, stampedAt }
//
// Zero-drift: every `to` and every `probe` was verified live before
// this file was committed. No invented endpoints, no invented pages.

const DOMAINS = [
  {
    id: "platform-overview",
    number: 1,
    label: "Platform Overview",
    stripe: "#0f172a",
    icon: BarChart3,
    to: "/admin/executive-overview",
    description:
      "Trusted platform posture — readiness, attestation, and runtime command signal.",
    probe: "/api/admin/platform/status",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "critical",
          metric: "UNKNOWN",
          detail: "Platform attestation is not reporting.",
          stampedAt: null,
        };
      }
      const ready = !!r.body.readiness?.ready_flag;
      const attestation = r.body.attestation_version || "runtime";
      return {
        status: ready ? "healthy" : "warning",
        metric: ready ? "READY" : "HOLD",
        detail: `Attestation ${attestation} · ${ready ? "platform ready" : "needs readiness review"}`,
        stampedAt: null,
      };
    },
  },
  {
    id: "operations-control",
    number: 2,
    label: "Operations Control Center",
    stripe: "#dc2626",
    icon: Activity,
    to: "/admin/operations-control",
    description:
      "The single console for platform maintenance — dry-run, apply, audit.",
    probe: "/api/admin/occ/health",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load OCC status.",
          stampedAt: null,
        };
      }
      const canonical = String(r.body.overall_canonical || r.body.overall_status || "UNVERIFIABLE").toUpperCase();
      const counts = getCanonicalCounts(r.body);
      const rootCauses = Number(r.body.unique_critical_root_causes || Object.keys(r.body.root_cause_groups || {}).length || 0);
      const status = mapCanonicalStatus(canonical);
      const mismatchCount = counts.mismatch;
      const metric = mismatchCount > 0 ? String(mismatchCount) : counts.degraded > 0 ? String(counts.degraded) : canonical;
      const detail =
        canonical === "VERIFIED"
          ? `Canonical ${canonical.toLowerCase()} · OCC aggregator in bounds`
          : mismatchCount > 0
          ? `${mismatchCount} critical signal(s) · ${rootCauses} root cause(s)`
          : `${counts.degraded} signal(s) need attention`;
      return { status, metric, detail, stampedAt: r.body.generated_at || null };
    },
  },
  {
    id: "storage-recovery",
    number: 3,
    label: "Storage & Recovery",
    stripe: "#0891b2",
    icon: HardDrive,
    to: "/admin/storage-recovery",
    description:
      "Backups, R2 bucket usage, RPO / RTO posture, restore drills.",
    probe: "/api/admin/recovery/snapshot",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load recovery snapshot.",
          stampedAt: null,
        };
      }
      const pill = String(r.body.pill || "").toLowerCase();
      const status =
        pill === "green" ? "healthy" : pill === "yellow" ? "warning" : pill === "red" ? "critical" : "warning";
      const ageMin = Number(r.body.backup_age_minutes ?? -1);
      const target = Number(r.body.backup_age_target_minutes ?? 0);
      const archiveTotal = Number(r.body.archive_count?.r2_total ?? 0);
      const metric = ageMin >= 0 ? `${ageMin.toFixed(1)}m` : "—";
      const detail =
        ageMin >= 0
          ? `Backup age · target ≤ ${target}m · ${archiveTotal} archives`
          : "No completed backup recorded yet.";
      return {
        status,
        metric,
        detail,
        stampedAt: r.body.last_backup?.ts || r.body.computed_at || null,
      };
    },
  },
  {
    id: "ai-operations",
    number: 4,
    label: "AI Operations",
    stripe: "#7c3aed",
    icon: Sparkles,
    to: "/admin/ai-operations",
    description:
      "Provider selection, model routing, gateway posture, failover.",
    probe: "/api/ai/gateway/status",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load AI gateway status.",
          stampedAt: null,
        };
      }
      const enabled = !!r.body.gateway_enabled;
      const resolved = !!r.body.resolved_provider_available;
      const provider = r.body.resolved_selected_provider || r.body.default_provider || "—";
      const status = enabled && resolved ? "healthy" : enabled ? "critical" : "warning";
      const metric = provider.toUpperCase();
      const detail = enabled
        ? resolved
          ? `Gateway ON · provider available`
          : `Gateway ON · provider unavailable`
        : `Gateway OFF · tenant-level opt-in`;
      return { status, metric, detail, stampedAt: null };
    },
  },
  {
    id: "communications",
    number: 5,
    label: "Communications",
    stripe: "#0284c7",
    icon: Mail,
    to: "/admin/communications",
    description:
      "Email routing, digest scheduler, notification broadcast health.",
    probe: "/api/admin/email-routing/v2/status",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load email routing status.",
          stampedAt: null,
        };
      }
      const empty = Array.isArray(r.body.critical_empty_route_keys)
        ? r.body.critical_empty_route_keys.length
        : 0;
      const band = String(r.body.band || "").toLowerCase();
      const status =
        empty > 0 || band === "red" ? "critical" : ["yellow", "amber"].includes(band) ? "warning" : "healthy";
      const mode = r.body.mode || "—";
      const routeCount = r.body.route_counts?.total ?? 0;
      // Operator-facing metric: route count is meaningful; the mode
      // identifier ("v2") is an internal implementation detail and
      // must never surface as the card's headline.
      const metric = String(routeCount);
      const detail =
        empty > 0
          ? `${empty} critical route(s) empty`
          : `${routeCount} routes configured`;
      return { status, metric, detail, stampedAt: r.body.ts || null };
    },
  },
  {
    id: "identity-security",
    number: 6,
    label: "Identity & Security",
    stripe: "#b45309",
    icon: Users,
    to: "/admin/identity-security",
    description:
      "Active sessions, MFA enrollment, portal access, people directory.",
    probe: "/api/admin/sessions/recent",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load session inventory.",
          stampedAt: null,
        };
      }
      const count = Number(r.body.count ?? 0);
      const status = "healthy";
      const metric = String(count);
      const detail = `${count} active session(s) · timeouts ${r.body.timeouts_enabled ? "on" : "off"}`;
      return { status, metric, detail, stampedAt: r.body.server_now || null };
    },
  },
  {
    id: "governance-trust",
    number: 7,
    label: "Governance & Trust",
    stripe: "#7c2d12",
    icon: ShieldCheck,
    to: "/admin/governance-trust",
    description:
      "Governance rules, audit log, compliance findings, deploy readiness.",
    probe: "/api/admin/governance/summary",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load governance summary.",
          stampedAt: null,
        };
      }
      const severity = r.body.severity_counts || {};
      const highs = Number(severity.high || 0) + Number(severity.critical || 0);
      const health = String(r.body.health_label || "").toLowerCase();
      const freshnessState = String(r.body.freshness?.state || "UNKNOWN").toUpperCase();
      const status =
        freshnessState === "SCAN_FAILED" || health === "critical" || highs > 0
          ? "critical"
          : freshnessState === "STALE" || freshnessState === "AGING"
          ? "warning"
          : health === "warning"
          ? "warning"
          : "healthy";
      const score = r.body.convergence_score;
      const metric =
        typeof score === "number" ? `${Math.round(score)}/100` : String(highs || 0);
      const trackedRules = Object.keys(r.body.rule_counts || {}).length;
      const detail = `${highs} high/critical · ${trackedRules} active rules · ${freshnessState.toLowerCase()} scan`;
      return { status, metric, detail, stampedAt: r.body.freshness?.last_scan_at || r.body.last_scan?.finished_at || null };
    },
  },
  {
    id: "platform-configuration",
    number: 8,
    label: "Platform Configuration",
    stripe: "#4338ca",
    icon: Cog,
    to: "/admin/platform-configuration",
    description:
      "Integration wiring (Motive, Resend, R2), brand, feature flags.",
    probe: "/api/admin/integrations/health",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load integration probes.",
          stampedAt: null,
        };
      }
      const probes = Array.isArray(r.body.probes) ? r.body.probes : [];
      const liveProbes = probes.filter((probeRow) => !isNotApplicableProbe(probeRow));
      const notApplicable = probes.length - liveProbes.length;
      const degraded = liveProbes.filter((p) => p.status && p.status !== "ok").length;
      const overall = String(r.body.overall_status || "").toLowerCase();
      const status =
        degraded > 0 || overall === "critical"
          ? "critical"
          : overall === "warning"
          ? "warning"
          : "healthy";
      const metric = `${liveProbes.length - degraded}/${liveProbes.length || 0}`;
      const detail =
        degraded > 0
          ? `${degraded} integration(s) degraded`
          : `${liveProbes.length} live probe(s) green${notApplicable > 0 ? ` · ${notApplicable} not applicable` : ""}`;
      return { status, metric, detail, stampedAt: r.body.checked_at || null };
    },
  },
  {
    id: "diagnostics",
    number: 9,
    label: "Diagnostics",
    stripe: "#0f766e",
    icon: Database,
    to: "/admin/diagnostics",
    description:
      "System health probes, database capacity, asset-spine, analytics.",
    probe: "/api/admin/system-health",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "critical",
          metric: "OFFLINE",
          detail: "Health probe is not responding.",
          stampedAt: null,
        };
      }
      const canonical = String(r.body.overall_canonical || r.body.overall || "UNVERIFIABLE").toUpperCase();
      const counts = getCanonicalCounts(r.body);
      const needsAttention = counts.mismatch + counts.degraded;
      const ok = canonical === "VERIFIED";
      return {
        status: ok ? "healthy" : canonical === "DEGRADED" ? "warning" : "critical",
        metric: ok ? "GREEN" : `${needsAttention}`,
        detail: ok ? `Diagnostics in bounds` : `${needsAttention} diagnostic signal(s) need attention`,
        stampedAt: r.body.generated_at || null,
      };
    },
  },
  {
    id: "maintenance",
    number: 10,
    label: "Maintenance",
    stripe: "#525252",
    icon: Archive,
    to: "/admin/maintenance",
    description:
      "Legacy imports, master history, cleanup routines, geofence reconcile.",
    probe: "/api/admin/operations-control/overview",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load maintenance overview.",
          stampedAt: null,
        };
      }
      const ops = r.body.operations || [];
      const total = ops.length;
      const bad = ops.filter((o) => {
        const s = (o.status_snapshot || {}).status;
        return s === "critical" || s === "warning";
      }).length;
      const status = bad > 0 ? "warning" : total ? "healthy" : "wiring";
      return {
        status,
        metric: `${total}`,
        detail: bad > 0
          ? `${total} ops · ${bad} need attention`
          : `${total} maintenance operations available`,
        stampedAt: null,
      };
    },
  },
];

// ── Page ────────────────────────────────────────────────────────────
export default function AdminOS() {
  const { t } = useT();
  const [results, setResults] = useState({});
  const [loaded, setLoaded] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const domainsWithProbe = DOMAINS.filter((d) => d.probe);
    setLoaded(false);
    setResults(Object.fromEntries(domainsWithProbe.map((domain) => [domain.id, { pending: true }])));
    if (domainsWithProbe.length === 0) {
      setLoaded(true);
      return () => {
        cancelled = true;
      };
    }
    Promise.allSettled(
      domainsWithProbe.map(async (d) => {
        const row = await probe(d.probe);
        if (cancelled) return;
        setResults((prev) => ({ ...prev, [d.id]: row }));
      })
    ).finally(() => {
      if (!cancelled) setLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, [refreshTick]);

  const domainStates = useMemo(
    () => DOMAINS.map((domain) => ({
      ...domain,
      evaluation: getEvaluatedDomain(domain, results[domain.id], loaded),
    })),
    [results, loaded]
  );

  const summary = useMemo(() => {
    let healthy = 0;
    let warning = 0;
    let critical = 0;
    let pending = 0;
    for (const domain of domainStates) {
      const s = domain.evaluation.status;
      if (s === "healthy") healthy += 1;
      else if (s === "warning") warning += 1;
      else if (s === "critical") critical += 1;
      else pending += 1;
    }
    return { healthy, warning, critical, pending };
  }, [domainStates]);

  const nextActions = useMemo(
    () => domainStates
      .filter((domain) => domain.evaluation.status !== "healthy")
      .sort((a, b) => {
        const priorityDelta = (ACTION_PRIORITY[a.evaluation.status] ?? 9) - (ACTION_PRIORITY[b.evaluation.status] ?? 9);
        return priorityDelta !== 0 ? priorityDelta : a.number - b.number;
      })
      .slice(0, 4)
      .map((domain) => ({
        domain,
        actionCopy: getDomainAction(domain, domain.evaluation),
      })),
    [domainStates]
  );

  const overallStatus =
    summary.critical > 0
      ? "critical"
      : summary.warning > 0
      ? "warning"
      : summary.pending > 0
      ? "wiring"
      : "healthy";
  const displaySummary = summary;

  return (
    <div
      data-testid="admin-os-root"
      className="min-h-screen bg-slate-50"
    >
      <PortalShell
        portalName="MASCI"
        portalRole={t("Admin")}
        experienceLevel="wp17c"
        experienceTone="admin"
        pageTitle={t("Admin Operating System")}
        subtitle={t("One governed command surface for platform posture, domain ownership, and the next safe action.")}
        primaryActions={
          <div className="flex flex-wrap items-center gap-2 min-w-0">
            <Button
              type="button"
              onClick={() => window.__masciAdminOpenPalette?.()}
              variant="outline"
              size="sm"
              data-testid="admin-os-open-palette"
            >
              <Search className="w-3.5 h-3.5" />
              {t("Search everything")}
              <kbd className="rounded border border-[color:var(--border-bold)] px-1 py-0.5 font-mono text-[10px] text-[color:var(--ink-soft)]">
                ⌘K
              </kbd>
            </Button>
            <Button
              type="button"
              onClick={() => setRefreshTick((n) => n + 1)}
              variant="outline"
              size="sm"
              data-testid="admin-os-refresh"
            >
              {t("Refresh")}
            </Button>
            <Button
              type="button"
              onClick={() => exportTrustSnapshot(DOMAINS, results, summary, overallStatus)}
              data-testid="admin-os-export-snapshot"
              title={t("Download a Markdown snapshot of the current platform trust state")}
            >
              <Download className="w-3.5 h-3.5" />
              {t("Export snapshot")}
            </Button>
          </div>
        }
        sideNav={
          <SideNavV3
            onOpenPalette={() => window.__masciAdminOpenPalette?.()}
          />
        }
      >
        {/* Root of the Admin OS — breadcrumb makes the location obvious. */}
        <AdminBreadcrumb crumbs={[]} testidPrefix="admin-os-breadcrumb" />

        <section className="wp17-mission-banner mb-6" data-testid="admin-os-mission-banner">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="wp17-kicker text-white/70">{t("Portal mission")}</div>
              <h2 className="mt-2 font-display text-2xl font-black tracking-tight text-white">{t("Run the platform without hunting for the right domain.")}</h2>
              <p className="mt-3 text-sm sm:text-base">
                {t("Start with posture, open the domain that needs attention, and keep maintenance/governance actions separated from business operations noise.")}
              </p>
            </div>
            <div className="wp17-chip-row">
              <Link to="/admin/operations-control" className="wp17-chip" data-testid="admin-os-next-occ-chip">{t("Operations Control")}</Link>
              <Link to="/admin/governance-trust" className="wp17-chip" data-testid="admin-os-next-governance-chip">{t("Governance & Trust")}</Link>
              <Link to="/admin/platform-configuration" className="wp17-chip" data-testid="admin-os-next-config-chip">{t("Platform Configuration")}</Link>
            </div>
          </div>
        </section>

        <section className="mb-6 grid gap-4 xl:grid-cols-[1.1fr_0.9fr] xl:items-start" data-testid="admin-os-command-surface">
          <ResponsiveSummaryStrip
            className="mb-0 wp16-card wp16-hairline-grid p-4 sm:p-5 wp17-panel"
            testid="admin-os-posture"
            left={(
              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  {t("Platform posture")}
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2 min-w-0">
                  <StatusPill
                    status={overallStatus}
                    testid="admin-os-posture-pill"
                  />
                  <span className="text-sm font-semibold text-slate-900 min-w-0 break-words">
                    {overallStatus === "critical"
                      ? t("One or more domains report a critical condition.")
                      : overallStatus === "warning"
                      ? t("One or more domains need attention.")
                      : overallStatus === "wiring"
                      ? t("One or more trust signals are still pending.")
                      : t("All wired domains report healthy.")}
                  </span>
                </div>
              </div>
            )}
            right={(
              <>
                <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-healthy">
                  <div className="wp17-metric-card">
                    <div className="wp17-metric-card__label">{t("Healthy")}</div>
                    <div className="wp17-metric-card__value text-emerald-700">{displaySummary.healthy}</div>
                  </div>
                </div>
                <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-warning">
                  <div className="wp17-metric-card">
                    <div className="wp17-metric-card__label">{t("Attention")}</div>
                    <div className="wp17-metric-card__value text-amber-700">{displaySummary.warning}</div>
                  </div>
                </div>
                <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-critical">
                  <div className="wp17-metric-card">
                    <div className="wp17-metric-card__label">{t("Critical")}</div>
                    <div className="wp17-metric-card__value text-rose-700">{displaySummary.critical}</div>
                  </div>
                </div>
                <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-wiring">
                  <div className="wp17-metric-card">
                    <div className="wp17-metric-card__label">{t("Pending")}</div>
                    <div className="wp17-metric-card__value text-slate-600">{displaySummary.pending}</div>
                  </div>
                </div>
                <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-kpi-row">
                  <div className="wp17-metric-card">
                    <div className="wp17-metric-card__label">{t("Total domains")}</div>
                    <div className="wp17-metric-card__value text-slate-800">{DOMAINS.length}</div>
                  </div>
                </div>
              </>
            )}
          />

          <section className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm" data-testid="admin-os-next-actions">
            <div className="mb-3">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Next actions</div>
              <h3 className="mt-1 font-display text-lg font-black tracking-tight text-slate-900">
                Attention-first command surface
              </h3>
              <p className="mt-2 text-sm text-slate-600">
                Recovery, diagnostics, and destructive controls stay off this landing until requested.
              </p>
            </div>

            {nextActions.length > 0 ? (
              <div className="space-y-2.5" data-testid="admin-os-next-action-grid">
                {nextActions.map(({ domain, actionCopy }, index) => (
                  <Link
                    key={domain.id}
                    to={domain.to}
                    className="group flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 transition-[border-color,background-color] duration-150 hover:border-slate-300 hover:bg-white"
                    data-testid={`admin-os-next-action-${domain.id}`}
                  >
                    <div className="min-w-0">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                        {String(index + 1).padStart(2, "0")} · {t(domain.label)}
                      </div>
                      <div className="mt-1 text-sm font-black tracking-tight text-slate-900">
                        {t(actionCopy.title)}
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-slate-600" data-testid={`admin-os-next-action-${domain.id}-summary`}>
                        {t(actionCopy.summary)}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <StatusPill status={domain.evaluation.status} testid={`admin-os-next-action-${domain.id}-status`} />
                      <ArrowUpRight className="h-3.5 w-3.5 text-slate-500 transition-transform duration-150 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-[var(--radius-card)] border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-900" data-testid="admin-os-next-actions-clear">
                All wired domains are healthy right now. Use the domain grid below for deeper review.
              </div>
            )}
          </section>
        </section>

        {/* ── 10 domain cards ────────────────────────────────── */}
        <section
          className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4"
          data-testid="admin-os-domain-grid"
        >
          {domainStates.map((d) => (
            <DomainCard
              key={d.id}
              domain={d}
              evaluation={d.evaluation}
            />
          ))}
        </section>

        <section className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3" data-testid="admin-os-recovery-governance">
          <Link
            to="/admin/storage-recovery"
            className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
            data-testid="admin-os-recovery-link-storage"
          >
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Recovery evidence</div>
            <div className="mt-1 font-semibold text-slate-900">Storage & Recovery</div>
            <p className="mt-2 text-sm text-slate-600">Backups, manifests, retention, restore drills, recovery history, and integrity verification.</p>
          </Link>
          <Link
            to="/admin/diagnostics"
            className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
            data-testid="admin-os-recovery-link-diagnostics"
          >
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Technical detail</div>
            <div className="mt-1 font-semibold text-slate-900">Diagnostics</div>
            <p className="mt-2 text-sm text-slate-600">Runtime probes, database capacity, workers, and deployment-readiness diagnostics on request.</p>
          </Link>
          <Link
            to="/admin/system"
            className="rounded-[var(--radius-card)] border border-amber-200 bg-amber-50 p-4 shadow-sm hover:border-amber-300 hover:shadow-md transition-all"
            data-testid="admin-os-recovery-link-system"
          >
            <div className="text-[10px] uppercase tracking-widest text-amber-800 font-mono">Exception-only</div>
            <div className="mt-1 font-semibold text-slate-900">System Recovery</div>
            <p className="mt-2 text-sm text-slate-700">Guarded destructive reconstruction controls stay off the landing and require explicit consequence review.</p>
          </Link>
        </section>

        {/* ── Trust note ─────────────────────────────────────── */}
        <div
          data-testid="admin-os-trace-note"
          className="mt-6 rounded-[var(--radius-card)] border border-dashed border-[color:var(--border-bold)] bg-white p-4 text-[12px] text-[color:var(--ink-soft)] shadow-sm wp17-panel"
        >
          <strong className="text-[color:var(--ink-strong)]">
            {t("Platform command center.")}
          </strong>{" "}
          {t("Review system health, investigate risks, and open the right operational area from one screen. Every metric is read from a live platform endpoint — cards without a live signal are honestly labelled “Awaiting signal”. Destructive controls are intentionally excluded from this landing.")}{" "}
          {t("Search everything with")}{" "}
          <kbd className="rounded border border-[color:var(--border-bold)] px-1 font-mono text-[10px]">
            ⌘K
          </kbd>
          . {t("Timestamps display in your local time.")}
        </div>
      </PortalShell>
    </div>
  );
}
