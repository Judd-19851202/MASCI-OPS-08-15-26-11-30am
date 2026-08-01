import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, ShieldAlert, Ban, Camera, BarChart3, ArrowRight } from "lucide-react";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { DataTable } from "@/design-system";

const INVENTORY_TOTAL = 1190;
const SURVIVOR_COUNTS = [
  { key: "workflow-reviews", label: "Open workflow reviews", count: 102, detail: "Screens still awaiting the latest navigation and layout standard." },
  { key: "navigation", label: "Navigation reviews", count: 62, detail: "Back / home / workflow hierarchy items still being reconciled." },
  { key: "tables", label: "Records & tables", count: 100, detail: "Structured records still being aligned to the governed reading pattern." },
  { key: "dialogs", label: "Dialogs & overlays", count: 89, detail: "Shared modal and overlay experiences still being standardized." },
  { key: "forms", label: "Forms", count: 38, detail: "Input-heavy workflows still moving to the governed field system." },
  { key: "coaching", label: "Guidance", count: 10, detail: "Helper copy still being simplified for field readability." },
];

const ROUTE_STATUS = [
  {
    route: "Admin Safety Issuance Record",
    status: "READY",
    evidence: "Responsive review at 390 / 430 / 768 / 1024 / 1440 plus focused QA.",
    lastCertified: "2026-08-01 16:18 UTC",
    block: "—",
  },
  {
    route: "Admin Safety Training Record",
    status: "READY",
    evidence: "Responsive review at 390 / 430 / 768 / 1024 / 1440 plus focused QA.",
    lastCertified: "2026-08-01 16:18 UTC",
    block: "—",
  },
  {
    route: "Admin JHA Library",
    status: "READY",
    evidence: "Responsive review at 390 / 430 / 768 / 1024 / 1440 plus focused QA.",
    lastCertified: "2026-08-01 16:24 UTC",
    block: "—",
  },
  {
    route: "Admin Trench Box Library",
    status: "READY",
    evidence: "Responsive review at 390 / 430 / 768 / 1024 / 1440 plus focused QA.",
    lastCertified: "2026-08-01 16:26 UTC",
    block: "—",
  },
  {
    route: "Protected preview workspace",
    status: "BLOCKED_ACCESS",
    evidence: "GET /api/dev/check → 404 · POST /api/dev/login → 404",
    lastCertified: "Blocked in Preview",
    block: "Access environment still needs the protected DevHub credentials and endpoint enablement.",
  },
  {
    route: "Admin trench asset detail",
    status: "IN_REVIEW",
    evidence: "Shared trench shell and navigation update is active.",
    lastCertified: "Pending this review cycle",
    block: "Needs full responsive review and final QA.",
  },
  {
    route: "Safety trench asset detail",
    status: "IN_REVIEW",
    evidence: "Shared trench shell and navigation update is active.",
    lastCertified: "Pending this review cycle",
    block: "Needs full responsive review and final QA.",
  },
  {
    route: "Admin trench reports",
    status: "IN_REVIEW",
    evidence: "Shared trench shell now carries the governed navigation pattern.",
    lastCertified: "Pending this review cycle",
    block: "Needs final visual signoff.",
  },
];

const BLOCKERS = [
  {
    title: "Protected preview workspace unavailable",
    detail: "Readiness review cannot continue in Preview because the protected workspace still fails closed.",
    evidence: ["GET /api/dev/check → 404", "POST /api/dev/login → 404", "backend requires DEV_PASSWORD + enabled dev gate"],
  },
];

const BATCHES = [
  {
    title: "Admin safety and library review",
    status: "READY",
    timestamp: "2026-08-01 16:26 UTC",
    evidence: "Four admin workflows cleared responsive review and focused QA.",
  },
  {
    title: "Safety records and JHA review",
    status: "READY",
    timestamp: "2026-08-01",
    evidence: "Safety record views and the JHA workspace now share the governed reading and navigation pattern.",
  },
  {
    title: "DevHub access review",
    status: "BLOCKED_ACCESS",
    timestamp: "2026-08-01",
    evidence: "The login surface stays stable, but authenticated DevHub access remains unavailable until the environment is corrected.",
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
    READY: "border-emerald-200 bg-emerald-50 text-emerald-900",
    IN_REVIEW: "border-amber-200 bg-amber-50 text-amber-900",
    BLOCKED_ACCESS: "border-red-200 bg-red-50 text-red-900",
  };
  const labelMap = {
    READY: "Ready",
    IN_REVIEW: "In review",
    BLOCKED_ACCESS: "Blocked",
  };
  return <span className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${map[status] || "border-slate-200 bg-white text-slate-700"}`}>{labelMap[status] || status}</span>;
}

export default function Wp17dCertificationDashboard() {
  const survivorsRemaining = useMemo(() => SURVIVOR_COUNTS.reduce((sum, item) => sum + item.count, 0), []);
  const completionPct = useMemo(() => Math.max(0, Number((((INVENTORY_TOTAL - survivorsRemaining) / INVENTORY_TOTAL) * 100).toFixed(1))), [survivorsRemaining]);
  const readyScreens = ROUTE_STATUS.filter((route) => route.status === "READY").length;
  const blockedScreens = ROUTE_STATUS.filter((route) => route.status === "BLOCKED_ACCESS").length;
  const readinessVerdict = blockedScreens > 0 || survivorsRemaining > 0 ? "Not ready" : "Ready";

  const columns = [
    { key: "route", header: "Screen", wrap: true, render: (row) => <span className="font-mono text-xs text-slate-800">{row.route}</span> },
    { key: "status", header: "Readiness", render: (row) => statusChip(row.status) },
    { key: "evidence", header: "Review evidence", wrap: true },
    { key: "lastCertified", header: "Last review", wrap: true },
    { key: "block", header: "Blocking issue", wrap: true },
  ];

  return (
    <AdminRouteShell
      pageTitle="Operations Readiness Center"
      subtitle="Governance review and release readiness"
      portalRole="Admin · Governance & Trust"
      crumbs={[{ label: "Admin OS" }, { label: "Governance & Trust" }, { label: "Operations Readiness" }]}
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
            kicker="Governance operations"
            title="Operations Readiness Center"
            description="One governed view for open experience reviews, evidence posture, blocker visibility, and release readiness."
            actions={(
              <>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-bold text-red-900" data-testid="wp17d-readiness-chip"><ShieldAlert className="h-3.5 w-3.5" /> {readinessVerdict}</span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900" data-testid="wp17d-progress-chip"><BarChart3 className="h-3.5 w-3.5" /> {completionPct}% aligned</span>
              </>
            )}
            toolbar={(
              <Link to="/admin/trench-safety/assets" className="inline-flex h-11 items-center gap-2 rounded-full border border-slate-300 bg-white px-4 text-xs font-bold uppercase tracking-[0.18em] text-slate-800 transition-colors hover:border-red-500 hover:text-red-700" data-testid="wp17d-open-active-batch-link">
                Open current review <ArrowRight className="h-4 w-4" />
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
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Screen-by-screen review status</div>
                  <h2 className="mt-2 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">Current readiness board</h2>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-600">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-certified-routes-chip"><ShieldCheck className="h-3.5 w-3.5 text-emerald-700" /> {readyScreens} ready</span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-blocked-routes-chip"><Ban className="h-3.5 w-3.5 text-red-700" /> {blockedScreens} blocked</span>
                </div>
              </div>
              <div className="mt-5">
                <DataTable columns={columns} rows={ROUTE_STATUS} rowKey={(row) => row.route} density="compact" tableMinWidth={980} data-testid="wp17d-route-status-table" />
              </div>
            </div>

            <div className="space-y-6">
              <section className="wp17-panel p-5" data-testid="wp17d-readiness-summary-panel">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Release readiness</div>
                <div className="mt-3 flex items-end justify-between gap-3">
                  <div>
                    <div className="font-display text-4xl font-black tracking-tight text-slate-900" data-testid="wp17d-completion-pct">{completionPct}%</div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Calculated from the governed experience review inventory.</p>
                  </div>
                  {readinessVerdict === "Ready" ? <ShieldCheck className="h-10 w-10 text-emerald-700" /> : <ShieldAlert className="h-10 w-10 text-red-700" />}
                </div>
                <div className="mt-4 h-3 rounded-full bg-slate-200" data-testid="wp17d-progress-bar-track">
                  <div className="h-3 rounded-full bg-gradient-to-r from-red-700 to-emerald-600" style={{ width: `${completionPct}%` }} data-testid="wp17d-progress-bar-fill" />
                </div>
                <div className="mt-4 rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900" data-testid="wp17d-go-no-go-panel">
                  <strong>{readinessVerdict}</strong> · open review items and/or access blockers still remain before release signoff.
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
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold">Review evidence log</div>
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