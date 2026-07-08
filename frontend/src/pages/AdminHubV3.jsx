// TRACK 25.02 · Admin Operating System — Phase D · Executive Home V3.
//
// Attention-first landing page. Displayed at /admin when the
// `masci.admin.nav.v3` feature flag is on. Prioritizes what needs
// attention right now over listing every possible action.
//
// Data sources — ALL existing, no new APIs:
//   GET /api/admin/operations-control/overview  (health · red/yellow/green)
//   GET /api/admin/integrations/health          (integration probes)
//   GET /api/operations/expirations/summary     (cert / doc expirations)
//   GET /api/dispatch/command/summary           (safety / fleet)
//
// This page renders alongside SideNavV3 and CommandPaletteProvider —
// wired in AppRoutes.jsx. The legacy AdminHubV2 remains at /admin
// when the flag is OFF, preserving zero-drift.
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { PortalShell } from "../design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import { CommandPaletteProvider } from "@/components/admin/CommandPalette";
import {
  Activity, AlertTriangle, ChevronRight, ShieldAlert, Sparkles, Search,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

function h() {
  const t = getAdminToken();
  return t
    ? { "Content-Type": "application/json", "X-Admin-Token": t }
    : { "Content-Type": "application/json" };
}

async function jget(p) {
  try {
    const r = await fetch(`${API}${p}`, { headers: h() });
    return { ok: r.ok, body: r.ok ? await r.json() : null };
  } catch {
    return { ok: false, body: null };
  }
}

function StatusPill({ status }) {
  const map = {
    healthy: { bg: "bg-emerald-100", text: "text-emerald-800", label: "GREEN" },
    warning: { bg: "bg-amber-100", text: "text-amber-900", label: "YELLOW" },
    critical: { bg: "bg-rose-100", text: "text-rose-900", label: "RED" },
    unavailable: { bg: "bg-slate-200", text: "text-slate-700", label: "—" },
  };
  const s = map[status] || map.unavailable;
  return (
    <span
      className={`inline-block ${s.bg} ${s.text} text-[10px] font-mono font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded`}
      data-testid={`hub-v3-status-pill-${status || "unknown"}`}
    >
      {s.label}
    </span>
  );
}

function Row({ testid, to, title, snapshot, why }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="flex items-start gap-3 px-4 py-3 border-b border-slate-200 hover:bg-slate-50 transition-colors text-slate-900"
    >
      <div className="mt-0.5 shrink-0">
        <StatusPill status={snapshot?.status} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold text-slate-900 leading-tight">
          {title}
        </div>
        <div className="text-[12px] text-slate-600 mt-0.5 truncate">
          {snapshot?.summary || why}
        </div>
      </div>
      <ChevronRight className="w-4 h-4 mt-1 text-slate-400 shrink-0" />
    </Link>
  );
}

function AttentionCard({ testid, title, subtitle, count, tone, cta, to }) {
  const toneMap = {
    critical: "bg-rose-50 border-rose-300",
    warning: "bg-amber-50 border-amber-300",
    healthy: "bg-emerald-50 border-emerald-300",
    neutral: "bg-slate-50 border-slate-200",
  };
  return (
    <Link
      to={to}
      className={`block border rounded-lg p-4 ${toneMap[tone] || toneMap.neutral} hover:shadow-md transition-shadow text-slate-900`}
      data-testid={testid}
    >
      <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-semibold">
        {subtitle}
      </div>
      <div className="mt-1 text-3xl font-black text-slate-900 leading-none">
        {count === null || count === undefined ? "—" : count}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{title}</div>
      <div className="mt-2 text-[11px] text-slate-600 flex items-center gap-1">
        {cta} <ChevronRight className="w-3.5 h-3.5" />
      </div>
    </Link>
  );
}

export default function AdminHubV3() {
  const [state, setState] = useState({
    loaded: false,
    occ: null,
    integrations: null,
    expirations: null,
    dispatch: null,
  });

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      jget("/api/admin/operations-control/overview"),
      jget("/api/admin/integrations/health"),
      jget("/api/operations/expirations/summary"),
      jget("/api/dispatch/command/summary"),
    ]).then(([occ, integ, exp, disp]) => {
      if (cancelled) return;
      setState({
        loaded: true,
        occ: occ.body,
        integrations: integ.body,
        expirations: exp.body,
        dispatch: disp.body,
      });
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Compute overall platform posture from OCC snapshots.
  const occOps = state.occ?.operations || [];
  const posture = useMemo(() => {
    let critical = 0;
    let warning = 0;
    for (const op of occOps) {
      const s = op?.status_snapshot?.status;
      if (s === "critical") critical += 1;
      else if (s === "warning") warning += 1;
    }
    return { critical, warning };
  }, [occOps]);

  const overall = posture.critical
    ? "critical"
    : posture.warning
      ? "warning"
      : state.loaded
        ? "healthy"
        : "unavailable";

  const expC = state.expirations?.counts || {};
  const ds = state.dispatch || {};
  const incidentsOpen = ds.safety?.incidents_open ?? null;
  const capasOpen = ds.safety?.corrective_actions_open ?? null;
  const fleetOos = ds.fleet?.counts?.oos ?? null;

  // Pick the top 5 OCC ops needing attention (critical first, then
  // warning). Rest are still one click away in OCC.
  const attentionOps = useMemo(() => {
    const sortOrder = { critical: 0, warning: 1, unavailable: 2, healthy: 3 };
    return [...occOps]
      .sort(
        (a, b) =>
          (sortOrder[a?.status_snapshot?.status] ?? 4) -
          (sortOrder[b?.status_snapshot?.status] ?? 4),
      )
      .slice(0, 5);
  }, [occOps]);

  return (
    <CommandPaletteProvider>
      <div
        data-testid="admin-hub-v3-root"
        className="min-h-screen bg-slate-50"
      >
        <PortalShell
          portalName="MASCI"
          portalRole="Admin"
          pageTitle="What needs attention right now?"
          subtitle="Executive Home · one-glance view of platform health, safety, fleet, and compliance."
          primaryActions={
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => window.__masciAdminOpenPalette?.()}
                className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100"
                data-testid="admin-hub-v3-open-palette"
              >
                <Search className="w-3.5 h-3.5" />
                Search everything
                <kbd className="text-[10px] px-1 py-0.5 rounded border border-slate-300 text-slate-500 font-mono">
                  ⌘K
                </kbd>
              </button>
              <Link
                to="/admin/operations-control"
                data-testid="admin-hub-v3-open-occ"
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-bold text-white bg-rose-600 hover:bg-rose-700"
              >
                <Activity className="w-3.5 h-3.5" />
                Open Operations Control Center
              </Link>
            </div>
          }
          sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
        >
          {/* ── Platform posture strip ────────────────────────────── */}
          <section
            className="mb-6 rounded-lg border border-slate-200 bg-white p-4 flex items-center gap-4"
            data-testid="admin-hub-v3-posture"
          >
            <div>
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                Platform posture
              </div>
              <div className="mt-1 flex items-center gap-2">
                <StatusPill status={overall} />
                <span className="text-sm font-semibold text-slate-900">
                  {overall === "critical"
                    ? "Platform has issues that block operations."
                    : overall === "warning"
                      ? "Platform is degraded — investigate soon."
                      : overall === "healthy"
                        ? "Platform is healthy across every checked surface."
                        : "Loading platform posture…"}
                </span>
              </div>
            </div>
            <div className="ml-auto flex items-center gap-4 text-sm">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  Red
                </div>
                <div className="font-black text-rose-700 text-xl leading-none">
                  {posture.critical}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  Yellow
                </div>
                <div className="font-black text-amber-700 text-xl leading-none">
                  {posture.warning}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  Total ops
                </div>
                <div className="font-black text-slate-800 text-xl leading-none">
                  {occOps.length || "—"}
                </div>
              </div>
            </div>
          </section>

          {/* ── Attention now ─────────────────────────────────────── */}
          <section className="mb-6">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
              Attention now
            </div>
            <h2 className="mt-1 text-lg font-black text-slate-900">
              Top items to look at first
            </h2>
            <div
              className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3"
              data-testid="admin-hub-v3-attention-cards"
            >
              <AttentionCard
                testid="admin-hub-v3-attention-incidents"
                subtitle="Safety"
                title="Open incidents"
                count={incidentsOpen}
                tone={incidentsOpen && incidentsOpen > 0 ? "warning" : "neutral"}
                cta="Review in Safety Portal"
                to="/safety-portal"
              />
              <AttentionCard
                testid="admin-hub-v3-attention-capas"
                subtitle="Safety"
                title="Open corrective actions"
                count={capasOpen}
                tone={capasOpen && capasOpen > 0 ? "warning" : "neutral"}
                cta="Review CAPAs"
                to="/safety-portal"
              />
              <AttentionCard
                testid="admin-hub-v3-attention-fleet-oos"
                subtitle="Fleet"
                title="Units out of service"
                count={fleetOos}
                tone={fleetOos && fleetOos > 0 ? "warning" : "neutral"}
                cta="Open Dispatch"
                to="/dispatch-portal"
              />
              <AttentionCard
                testid="admin-hub-v3-attention-exp-expired"
                subtitle="Compliance"
                title="Expired documents"
                count={expC.expired ?? null}
                tone={expC.expired && expC.expired > 0 ? "critical" : "neutral"}
                cta="Open Training & Certs"
                to="/admin/training"
              />
              <AttentionCard
                testid="admin-hub-v3-attention-exp-30"
                subtitle="Compliance"
                title="Expiring within 30 days"
                count={expC.in_30 ?? null}
                tone={expC.in_30 && expC.in_30 > 0 ? "warning" : "neutral"}
                cta="Open Training & Certs"
                to="/admin/training"
              />
              <AttentionCard
                testid="admin-hub-v3-attention-platform-red"
                subtitle="Platform"
                title="Operations at red"
                count={posture.critical}
                tone={posture.critical > 0 ? "critical" : "neutral"}
                cta="Open Operations Control Center"
                to="/admin/operations-control"
              />
            </div>
          </section>

          {/* ── Platform Health Timeline (OCC surfaces) ──────────── */}
          <section className="mb-6">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
              Platform operations
            </div>
            <h2 className="mt-1 text-lg font-black text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              Operations Control Center · top status
            </h2>
            <div
              className="mt-3 rounded-lg border border-slate-200 bg-white overflow-hidden"
              data-testid="admin-hub-v3-occ-list"
            >
              {!state.loaded && (
                <div className="p-4 text-sm text-slate-500">
                  Loading operations…
                </div>
              )}
              {state.loaded && attentionOps.length === 0 && (
                <div className="p-4 text-sm text-slate-500">
                  No operations registered yet.
                </div>
              )}
              {state.loaded &&
                attentionOps.map((op) => (
                  <Row
                    key={op.id}
                    testid={`admin-hub-v3-op-${op.id}`}
                    to={`/admin/operations-control?highlight=${encodeURIComponent(op.id)}`}
                    title={op.title || op.id}
                    snapshot={op.status_snapshot}
                    why={op.description}
                  />
                ))}
              <Link
                to="/admin/operations-control"
                data-testid="admin-hub-v3-occ-see-all"
                className="flex items-center justify-between px-4 py-2.5 text-xs font-semibold text-rose-700 hover:bg-rose-50"
              >
                See every platform operation in the Operations Control Center
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </section>

          <div
            data-testid="admin-hub-v3-trace-note"
            className="mt-6 rounded-md border border-dashed border-slate-300 bg-white p-3 text-[12px] text-slate-600"
          >
            <strong className="text-slate-900">Executive Home.</strong>{" "}
            Every number above is a live count read from an existing platform
            endpoint. Every card opens the workflow that resolves it. Full
            section access is available in the sidebar. Search everything with{" "}
            <kbd className="px-1 rounded border border-slate-300 font-mono text-[10px]">
              ⌘K
            </kbd>
            .
          </div>
        </PortalShell>
      </div>
    </CommandPaletteProvider>
  );
}
