import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, ShieldAlert, Ban, Camera, BarChart3, ArrowRight } from "lucide-react";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { DataTable } from "@/design-system";

const INVENTORY_TOTAL = 1190;
const SURVIVOR_COUNTS = [
  { key: "route-shell", label: "Route / Shell", count: 102, detail: "Remaining page-level shell migrations" },
  { key: "navigation", label: "Navigation", count: 62, detail: "Duplicate nav and shell-path inconsistencies" },
  { key: "tables", label: "Tables", count: 100, detail: "Legacy tables pending canonical DataTable treatment" },
  { key: "dialogs", label: "Dialogs / Overlays", count: 89, detail: "Shared modal and overlay convergence still open" },
  { key: "forms", label: "Forms", count: 38, detail: "Legacy form frames and control families remaining" },
  { key: "coaching", label: "Coaching", count: 10, detail: "Legacy helper copy still awaiting rewrite or removal" },
];

const ROUTE_STATUS = [
  {
    route: "/admin/safety/issuance/:id",
    status: "CERTIFIED",
    evidence: "Screenshots 390/430/768/1024/1440 · frontend QA pass",
    lastCertified: "2026-08-01 16:18 UTC",
    block: "—",
  },
  {
    route: "/admin/safety/training/:id",
    status: "CERTIFIED",
    evidence: "Screenshots 390/430/768/1024/1440 · frontend QA pass",
    lastCertified: "2026-08-01 16:18 UTC",
    block: "—",
  },
  {
    route: "/admin/jha-plans",
    status: "CERTIFIED",
    evidence: "Screenshots 390/430/768/1024/1440 · frontend QA pass",
    lastCertified: "2026-08-01 16:24 UTC",
    block: "—",
  },
  {
    route: "/admin/trench-boxes",
    status: "CERTIFIED",
    evidence: "Screenshots 390/430/768/1024/1440 · frontend QA pass",
    lastCertified: "2026-08-01 16:26 UTC",
    block: "—",
  },
  {
    route: "/dev",
    status: "BLOCKED_CREDENTIALS",
    evidence: "GET /api/dev/check → 404 · POST /api/dev/login → 404",
    lastCertified: "Blocked in Preview",
    block: "Requires DEV_PASSWORD + dev endpoint gate",
  },
  {
    route: "/admin/trench-safety/assets/:assetId",
    status: "IN_PROGRESS",
    evidence: "Shared trench shell/nav convergence active",
    lastCertified: "Pending current batch",
    block: "Needs full responsive + QA certification",
  },
  {
    route: "/safety/trench-safety/assets/:assetId",
    status: "IN_PROGRESS",
    evidence: "Shared trench shell/nav convergence active",
    lastCertified: "Pending current batch",
    block: "Needs full responsive + QA certification",
  },
  {
    route: "/admin/trench-safety/reports",
    status: "IN_PROGRESS",
    evidence: "Canonical shell/nav now staged through shared trench shell",
    lastCertified: "Pending current batch",
    block: "Needs route-level visual certification",
  },
];

const BLOCKERS = [
  {
    title: "DevHub authentication unavailable",
    detail: "Authenticated certification cannot continue in Preview because backend dev endpoints fail closed.",
    evidence: ["GET /api/dev/check → 404", "POST /api/dev/login → 404", "backend requires DEV_PASSWORD + enabled dev gate"],
  },
];

const BATCHES = [
  {
    title: "Admin Safety Aliases + Admin Libraries",
    status: "CLOSED",
    timestamp: "2026-08-01 16:26 UTC",
    evidence: "Four admin routes certified with responsive screenshots and focused frontend QA.",
  },
  {
    title: "Safety Records + JHA Convergence",
    status: "CLOSED",
    timestamp: "2026-08-01",
    evidence: "Public/admin safety record views and JHA hub reconciled onto canonical shell/data-table architecture.",
  },
  {
    title: "DevHub Authenticated Certification",
    status: "BLOCKED_CREDENTIALS",
    timestamp: "2026-08-01",
    evidence: "Login surface handled gracefully; authenticated `/dev` remains inaccessible until env is corrected.",
  },
];

function CountCard({ label, count, detail, testId }) {
  return (
    <div className="wp17-panel p-4 sm:p-5" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">{label}</div>
      <div className="mt-3 font-display text-4xl font-black tracking-tight text-slate-900">{count}</div>
      <p className="mt-2 text-sm leading-6 text-slate-600">{detail}</p>
    </div>
  );
}

function statusChip(status) {
  const map = {
    CERTIFIED: "border-emerald-200 bg-emerald-50 text-emerald-900",
    IN_PROGRESS: "border-amber-200 bg-amber-50 text-amber-900",
    BLOCKED_CREDENTIALS: "border-red-200 bg-red-50 text-red-900",
  };
  return <span className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${map[status] || "border-slate-200 bg-white text-slate-700"}`}>{status.replaceAll("_", " ")}</span>;
}

export default function Wp17dCertificationDashboard() {
  const survivorsRemaining = useMemo(() => SURVIVOR_COUNTS.reduce((sum, item) => sum + item.count, 0), []);
  const completionPct = useMemo(() => Math.max(0, Number((((INVENTORY_TOTAL - survivorsRemaining) / INVENTORY_TOTAL) * 100).toFixed(1))), [survivorsRemaining]);
  const certifiedRoutes = ROUTE_STATUS.filter((route) => route.status === "CERTIFIED").length;
  const blockedRoutes = ROUTE_STATUS.filter((route) => route.status === "BLOCKED_CREDENTIALS").length;
  const goNoGo = blockedRoutes > 0 || survivorsRemaining > 0 ? "NO-GO" : "GO";

  const columns = [
    { key: "route", header: "Route", wrap: true, render: (row) => <span className="font-mono text-xs text-slate-800">{row.route}</span> },
    { key: "status", header: "Status", render: (row) => statusChip(row.status) },
    { key: "evidence", header: "Screenshot / QA evidence", wrap: true },
    { key: "lastCertified", header: "Last certification", wrap: true },
    { key: "block", header: "Blocking issue", wrap: true },
  ];

  return (
    <AdminRouteShell
      pageTitle="WP-17D Certification Dashboard"
      subtitle="Executive convergence operations"
      portalRole="Admin · WP-17D Certification"
      crumbs={[{ label: "Admin OS" }, { label: "Governance & Trust" }, { label: "WP-17D Certification" }]}
      showShellHeader={false}
      showBreadcrumbs={false}
      contentClassName="px-0 py-0"
      testId="wp17d-certification-shell"
    >
      <div className="min-h-screen bg-slate-50">
        <div className="caution-stripe print:hidden" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="wp17d-certification-page">
          <DetailPageHero
            backHref="/admin/governance-trust"
            backLabel="Governance & Trust"
            kicker="Executive operations tool"
            title="WP-17D Certification Dashboard"
            description="One operating view for remaining survivor counts, route certification status, evidence posture, blocker visibility, and executive GO / NO-GO readiness."
            actions={(
              <>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-bold text-red-900" data-testid="wp17d-readiness-chip"><ShieldAlert className="h-3.5 w-3.5" /> {goNoGo}</span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900" data-testid="wp17d-progress-chip"><BarChart3 className="h-3.5 w-3.5" /> {completionPct}% complete</span>
              </>
            )}
            toolbar={(
              <Link to="/admin/trench-safety/assets" className="inline-flex h-11 items-center gap-2 rounded-full border border-slate-300 bg-white px-4 text-xs font-bold uppercase tracking-[0.18em] text-slate-800 transition-colors hover:border-red-500 hover:text-red-700" data-testid="wp17d-open-active-batch-link">
                Open active batch <ArrowRight className="h-4 w-4" />
              </Link>
            )}
            testId="wp17d-certification-hero"
          />

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" data-testid="wp17d-survivor-counts-grid">
            {SURVIVOR_COUNTS.map((item) => (
              <CountCard key={item.key} label={item.label} count={item.count} detail={item.detail} testId={`wp17d-count-${item.key}`} />
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr),22rem]" data-testid="wp17d-readiness-layout">
            <div className="wp17-panel p-5 sm:p-6" data-testid="wp17d-route-status-panel">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Route-by-route certification status</div>
                  <h2 className="mt-2 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">Current WP-17D certification board</h2>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-600">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-certified-routes-chip"><ShieldCheck className="h-3.5 w-3.5 text-emerald-700" /> {certifiedRoutes} certified</span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-blocked-routes-chip"><Ban className="h-3.5 w-3.5 text-red-700" /> {blockedRoutes} blocked</span>
                </div>
              </div>
              <div className="mt-5">
                <DataTable columns={columns} rows={ROUTE_STATUS} rowKey={(row) => row.route} density="compact" tableMinWidth={980} data-testid="wp17d-route-status-table" />
              </div>
            </div>

            <div className="space-y-6">
              <section className="wp17-panel p-5" data-testid="wp17d-readiness-summary-panel">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Executive readiness</div>
                <div className="mt-3 flex items-end justify-between gap-3">
                  <div>
                    <div className="font-display text-4xl font-black tracking-tight text-slate-900" data-testid="wp17d-completion-pct">{completionPct}%</div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Calculated from the tracked survivor inventory against the 1,190-surface convergence ledger.</p>
                  </div>
                  {goNoGo === "GO" ? <ShieldCheck className="h-10 w-10 text-emerald-700" /> : <ShieldAlert className="h-10 w-10 text-red-700" />}
                </div>
                <div className="mt-4 h-3 rounded-full bg-slate-200" data-testid="wp17d-progress-bar-track">
                  <div className="h-3 rounded-full bg-gradient-to-r from-red-700 to-emerald-600" style={{ width: `${completionPct}%` }} data-testid="wp17d-progress-bar-fill" />
                </div>
                <div className="mt-4 rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900" data-testid="wp17d-go-no-go-panel">
                  <strong>Executive {goNoGo}</strong> · route survivors and/or blocker states remain open, so final WP-17D closeout cannot be certified yet.
                </div>
              </section>

              <section className="wp17-panel p-5" data-testid="wp17d-blockers-panel">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Blocking issues</div>
                <div className="mt-4 space-y-4">
                  {BLOCKERS.map((blocker) => (
                    <div key={blocker.title} className="rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-4">
                      <div className="font-display text-lg font-black text-red-950">{blocker.title}</div>
                      <p className="mt-2 text-sm leading-6 text-red-900">{blocker.detail}</p>
                      <ul className="mt-3 space-y-1 text-xs text-red-900">
                        {blocker.evidence.map((item) => <li key={item}>• {item}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </section>

          <section className="wp17-panel p-5 sm:p-6" data-testid="wp17d-batch-evidence-panel">
            <div className="flex items-center gap-2 text-red-700">
              <Camera className="h-4 w-4" />
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold">Certification evidence ledger</div>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              {BATCHES.map((batch) => (
                <article key={batch.title} className="rounded-[1.35rem] border border-slate-200 bg-white px-4 py-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)]" data-testid={`wp17d-batch-${batch.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-display text-lg font-black text-slate-900 leading-tight">{batch.title}</div>
                    {statusChip(batch.status)}
                  </div>
                  <div className="mt-3 text-xs font-mono uppercase tracking-[0.14em] text-slate-500">{batch.timestamp}</div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{batch.evidence}</p>
                </article>
              ))}
            </div>
          </section>
        </main>
      </div>
    </AdminRouteShell>
  );
}