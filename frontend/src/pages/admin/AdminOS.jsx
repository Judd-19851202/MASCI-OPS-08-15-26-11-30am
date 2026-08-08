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
  AlertTriangle,
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
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import { buildPortalAuthHeaders } from "@/lib/authHeaders";
import { formatRelativeTime } from "@/lib/platformTime";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;

// ── HTTP helper ─────────────────────────────────────────────────────
function adminHeaders() {
  return buildPortalAuthHeaders({ "Content-Type": "application/json" });
}

async function probe(path) {
  if (!path) return { ok: false, body: null, status: 0 };
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 10000);
  try {
    const r = await fetch(`${API}${path}`, { headers: adminHeaders(), signal: controller.signal });
    return {
      ok: r.ok,
      status: r.status,
      body: r.ok ? await r.json() : null,
    };
  } catch (_e) {
    return { ok: false, body: null, status: 0, timed_out: true };
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
  lines.push(`- Healthy: ${summary.healthy} · Attention: ${summary.warning} · Critical: ${summary.critical} · Awaiting signal: ${summary.wiring} · Total domains: ${domains.length}`);
  lines.push(``);
  lines.push(`## Domains`);
  for (const d of domains) {
    const r = d.probe ? results[d.id] : null;
    const evaluated = r ? d.evaluate(r) : d.probe ? { status: "loading" } : d.evaluate(null);
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

// ── Domain card ────────────────────────────────────────────────────
function DomainCard({ domain, probeResult, loaded }) {
  const { t } = useT();
  // Three states, in order:
  //   1. Domain has no probe            → call evaluate(null) once — the
  //                                       card owns its honest "Needs
  //                                       wiring" (or similar) state.
  //   2. Probe done (result available)  → call evaluate(result).
  //   3. Probe pending (loaded=false)   → generic loading placeholder.
  let evaluated;
  if (!domain.probe) {
    evaluated = domain.evaluate(null);
  } else if (probeResult) {
    evaluated = domain.evaluate(probeResult);
  } else if (loaded) {
    // Loaded but somehow no result key — treat as offline.
    evaluated = { status: "offline", metric: "—", detail: "Probe unavailable.", stampedAt: null };
  } else {
    evaluated = { status: "loading", metric: "…", detail: "Loading live data…", stampedAt: null };
  }
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
                status={evaluated.status}
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
              {evaluated.metric}
            </div>
            <div
              className="mt-1 text-[11px] text-slate-500 leading-tight truncate"
              data-testid={`admin-os-card-${domain.id}-detail`}
            >
              {typeof evaluated.detail === "string" ? t(evaluated.detail) : evaluated.detail}
            </div>
          </div>
          {evaluated.stampedAt ? (
            <div
              className="text-[10px] font-mono text-slate-400 text-right shrink-0"
              data-testid={`admin-os-card-${domain.id}-stamp`}
              title={t("Last checked (your local time)")}
            >
              {formatRelativeTime(evaluated.stampedAt)}
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
      "One-glance executive summary — service health, build version, uptime.",
    probe: "/api/version",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "critical",
          metric: "OFFLINE",
          detail: "Service is not reporting.",
          stampedAt: null,
        };
      }
      const uptime = Number(r.body.uptime_s || 0);
      const hours = Math.floor(uptime / 3600);
      const minutes = Math.floor((uptime % 3600) / 60);
      const commit = String(r.body.commit || "—").slice(0, 8);
      return {
        status: "healthy",
        metric: `${hours}h ${minutes}m`,
        detail: `Build ${commit} · ${r.body.service || "service"}`,
        stampedAt: r.body.started_at,
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
    probe: "/api/admin/operations-control/overview",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "wiring",
          metric: "—",
          detail: "Sign in as admin to load OCC status.",
          stampedAt: null,
        };
      }
      const ops = r.body.operations || [];
      let critical = 0;
      let warning = 0;
      for (const op of ops) {
        const s = op?.status_snapshot?.status;
        if (s === "critical") critical += 1;
        else if (s === "warning") warning += 1;
      }
      const status = critical > 0 ? "critical" : warning > 0 ? "warning" : "healthy";
      const metric = String(ops.length);
      const detail =
        critical > 0
          ? `${critical} critical · ${warning} warning`
          : warning > 0
          ? `${warning} attention · ${ops.length - warning} healthy`
          : `${ops.length} operations · all green`;
      return { status, metric, detail, stampedAt: r.body.checked_at || null };
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
      const status = enabled && resolved ? "healthy" : enabled ? "warning" : "warning";
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
        empty > 0 || band === "red" ? "critical" : band === "yellow" ? "warning" : "healthy";
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
      const degraded = probes.filter((p) => p.status && p.status !== "ok").length;
      const overall = String(r.body.overall_status || "").toLowerCase();
      const status =
        degraded > 0 || overall === "critical"
          ? "critical"
          : overall === "warning"
          ? "warning"
          : "healthy";
      const metric = `${probes.length - degraded}/${probes.length || 0}`;
      const detail =
        degraded > 0
          ? `${degraded} integration(s) degraded`
          : `${probes.length} probes green`;
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
    probe: "/api/health",
    evaluate: (r) => {
      if (!r.ok || !r.body) {
        return {
          status: "critical",
          metric: "OFFLINE",
          detail: "Health probe is not responding.",
          stampedAt: null,
        };
      }
      const ok = !!r.body.ok;
      return {
        status: ok ? "healthy" : "critical",
        metric: ok ? "OK" : "FAIL",
        detail: ok ? `Service reporting healthy` : `Service reporting failure`,
        stampedAt: r.body.ts || null,
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
    setResults({});
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

  const summary = useMemo(() => {
    let healthy = 0;
    let warning = 0;
    let critical = 0;
    let wiring = 0;
    for (const d of DOMAINS) {
      const r = results[d.id];
      const evaluated = r
        ? d.evaluate(r)
        : d.probe
        ? { status: "loading" }
        : d.evaluate(null);
      const s = evaluated.status;
      if (s === "healthy") healthy += 1;
      else if (s === "warning") warning += 1;
      else if (s === "critical") critical += 1;
      else if (s === "wiring") wiring += 1;
    }
    return { healthy, warning, critical, wiring };
  }, [results]);

  const overallStatus =
    !loaded
      ? "loading"
      : summary.critical > 0
      ? "critical"
      : summary.warning > 0
      ? "warning"
      : "healthy";
  const displaySummary = loaded ? summary : null;

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

        {/* ── Overall posture strip ─────────────────────────────── */}
        <section
          className="mb-6 wp16-card wp16-hairline-grid flex flex-wrap items-center gap-4 p-4 sm:p-5 wp17-panel"
          data-testid="admin-os-posture"
        >
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
                  : overallStatus === "healthy"
                  ? t("All wired domains report healthy.")
                  : t("Loading domain probes…")}
              </span>
            </div>
          </div>
          <div className="w-full xl:w-auto xl:ml-auto flex flex-wrap xl:flex-nowrap items-stretch gap-3 text-sm" data-testid="admin-os-kpi-row">
            <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-healthy">
              <div className="wp17-metric-card">
                <div className="wp17-metric-card__label">
                {t("Healthy")}
                </div>
                <div className="wp17-metric-card__value text-emerald-700">
                {displaySummary ? displaySummary.healthy : "—"}
                </div>
              </div>
            </div>
            <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-warning">
              <div className="wp17-metric-card">
                <div className="wp17-metric-card__label">
                {t("Attention")}
                </div>
                <div className="wp17-metric-card__value text-amber-700">
                {displaySummary ? displaySummary.warning : "—"}
                </div>
              </div>
            </div>
            <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-critical">
              <div className="wp17-metric-card">
                <div className="wp17-metric-card__label">
                {t("Critical")}
                </div>
                <div className="wp17-metric-card__value text-rose-700">
                {displaySummary ? displaySummary.critical : "—"}
                </div>
              </div>
            </div>
            <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]" data-testid="admin-os-count-wiring">
              <div className="wp17-metric-card">
                <div className="wp17-metric-card__label">
                {t("Awaiting signal")}
                </div>
                <div className="wp17-metric-card__value text-slate-600">
                {displaySummary ? displaySummary.wiring : "—"}
                </div>
              </div>
            </div>
            <div className="min-w-[9.5rem] flex-1 xl:flex-none xl:w-[10.25rem]">
              <div className="wp17-metric-card">
                <div className="wp17-metric-card__label">
                {t("Total domains")}
                </div>
                <div className="wp17-metric-card__value text-slate-800">
                {displaySummary ? DOMAINS.length : "—"}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-6" data-testid="admin-os-backup-integrity-section">
          <CrewRecoveryPanel />
        </section>

        {/* ── 10 domain cards ────────────────────────────────── */}
        <section
          className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4"
          data-testid="admin-os-domain-grid"
        >
          {DOMAINS.map((d) => (
            <DomainCard
              key={d.id}
              domain={d}
              probeResult={d.probe ? results[d.id] : null}
              loaded={loaded}
            />
          ))}
        </section>

        {/* ── Trust note ─────────────────────────────────────── */}
        <div
          data-testid="admin-os-trace-note"
          className="mt-6 rounded-[var(--radius-card)] border border-dashed border-[color:var(--border-bold)] bg-white p-4 text-[12px] text-[color:var(--ink-soft)] shadow-sm wp17-panel"
        >
          <strong className="text-[color:var(--ink-strong)]">
            {t("Platform command center.")}
          </strong>{" "}
          {t("Review system health, investigate risks, and open the right operational area from one screen. Every metric is read from a live platform endpoint — cards without a live signal are honestly labelled “Awaiting signal”.")}{" "}
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
