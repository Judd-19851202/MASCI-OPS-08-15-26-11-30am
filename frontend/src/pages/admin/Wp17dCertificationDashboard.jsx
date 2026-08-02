import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, ShieldAlert, Ban, Camera, BarChart3, ArrowRight } from "lucide-react";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { DataTable } from "@/design-system";
import { useT } from "@/lib/i18n";

const INVENTORY_TOTAL = 1190;
const SURVIVOR_COUNTS = [
  { key: "workflow-reviews", label: "Open workflow reviews", count: 102, detail: "Screens still awaiting the latest navigation and layout standard." },
  { key: "navigation", label: "Navigation reviews", count: 62, detail: "Back / home / workflow hierarchy items still being reconciled." },
  { key: "tables", label: "Records & tables", count: 100, detail: "Structured records still being aligned to the shared reading pattern." },
  { key: "dialogs", label: "Dialogs & overlays", count: 89, detail: "Shared modal and overlay experiences still being standardized." },
  { key: "forms", label: "Forms", count: 38, detail: "Input-heavy workflows still moving to the shared field system." },
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
    route: "Protected workspace",
    status: "BLOCKED_ACCESS",
    evidence: "Protected workspace access is still unavailable in this environment.",
    lastCertified: "Blocked",
    block: "Secure workspace access still needs to be restored before this review can continue.",
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
    evidence: "Shared trench shell now carries the shared navigation pattern.",
    lastCertified: "Pending this review cycle",
    block: "Needs final visual signoff.",
  },
];

const BLOCKERS = [
  {
    title: "Protected workspace unavailable",
    detail: "Readiness review cannot continue because the protected workspace is still unavailable in this environment.",
    evidence: ["Protected workspace sign-in is unavailable", "Secure access still needs to be restored"],
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
    evidence: "Safety record views and the JHA workspace now share the same reading and navigation pattern.",
  },
  {
    title: "Protected workspace access review",
    status: "BLOCKED_ACCESS",
    timestamp: "2026-08-01",
    evidence: "The login surface stays stable, but secure workspace access remains unavailable until the environment is corrected.",
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

function statusChip(status, t) {
  const map = {
    READY: "border-emerald-200 bg-emerald-50 text-emerald-900",
    IN_REVIEW: "border-amber-200 bg-amber-50 text-amber-900",
    BLOCKED_ACCESS: "border-red-200 bg-red-50 text-red-900",
  };
  const labelMap = {
    READY: t("Ready"),
    IN_REVIEW: t("In review"),
    BLOCKED_ACCESS: t("Blocked"),
  };
  return <span className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${map[status] || "border-slate-200 bg-white text-slate-700"}`}>{labelMap[status] || status}</span>;
}

export default function Wp17dCertificationDashboard() {
  const { t } = useT();
  const survivorsRemaining = useMemo(() => SURVIVOR_COUNTS.reduce((sum, item) => sum + item.count, 0), []);
  const completionPct = useMemo(() => Math.max(0, Number((((INVENTORY_TOTAL - survivorsRemaining) / INVENTORY_TOTAL) * 100).toFixed(1))), [survivorsRemaining]);
  const readyScreens = ROUTE_STATUS.filter((route) => route.status === "READY").length;
  const blockedScreens = ROUTE_STATUS.filter((route) => route.status === "BLOCKED_ACCESS").length;
  const isReady = blockedScreens === 0 && survivorsRemaining === 0;
  const readinessVerdict = blockedScreens > 0 || survivorsRemaining > 0 ? t("Not ready") : t("Ready");

  const columns = [
    { key: "route", header: t("Screen"), wrap: true, render: (row) => <span className="font-mono text-xs text-slate-800">{t(row.route)}</span> },
    { key: "status", header: t("Readiness"), render: (row) => statusChip(row.status, t) },
    { key: "evidence", header: t("Review evidence"), wrap: true, render: (row) => t(row.evidence) },
    { key: "lastCertified", header: t("Last review"), wrap: true, render: (row) => t(row.lastCertified) },
    { key: "block", header: t("Blocking issue"), wrap: true, render: (row) => t(row.block) },
  ];

  return (
    <AdminRouteShell
      pageTitle={t("Operations Readiness Center")}
      subtitle={t("Operations review and release readiness")}
      portalRole={t("Admin · Standards & Readiness")}
      crumbs={[{ label: t("Admin OS") }, { label: t("Standards & Readiness") }, { label: t("Operations Readiness") }]}
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
            backLabel={t("Standards & Readiness")}
            kicker={t("Operations readiness")}
            title={t("Operations Readiness Center")}
            description={t("One shared view for open experience reviews, progress, blocker visibility, and release readiness.")}
            actions={(
              <>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-bold text-red-900" data-testid="wp17d-readiness-chip"><ShieldAlert className="h-3.5 w-3.5" /> {readinessVerdict}</span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900" data-testid="wp17d-progress-chip"><BarChart3 className="h-3.5 w-3.5" /> {t("{pct}% aligned").replace("{pct}", completionPct)}</span>
              </>
            )}
            toolbar={(
              <Link to="/admin/trench-safety/assets" className="inline-flex h-11 items-center gap-2 rounded-full border border-slate-300 bg-white px-4 text-xs font-bold uppercase tracking-[0.18em] text-slate-800 transition-colors hover:border-red-500 hover:text-red-700" data-testid="wp17d-open-active-batch-link">
                {t("Open current review")} <ArrowRight className="h-4 w-4" />
              </Link>
            )}
            testId="wp17d-certification-hero"
          />

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" data-testid="wp17d-survivor-counts-grid">
            {SURVIVOR_COUNTS.map((item) => (
              <CountCard key={item.key} label={t(item.label)} count={item.count} detail={t(item.detail)} testId={`wp17d-count-${item.key}`} />
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr),22rem]" data-testid="wp17d-readiness-layout">
            <div className="wp17-panel p-5 sm:p-6" data-testid="wp17d-route-status-panel">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">{t("Screen-by-screen review status")}</div>
                  <h2 className="mt-2 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">{t("Current readiness board")}</h2>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-600">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-certified-routes-chip"><ShieldCheck className="h-3.5 w-3.5 text-emerald-700" /> {t("{count} ready").replace("{count}", readyScreens)}</span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1" data-testid="wp17d-blocked-routes-chip"><Ban className="h-3.5 w-3.5 text-red-700" /> {t("{count} blocked").replace("{count}", blockedScreens)}</span>
                </div>
              </div>
              <div className="mt-5">
                <DataTable columns={columns} rows={ROUTE_STATUS} rowKey={(row) => row.route} density="compact" tableMinWidth={980} data-testid="wp17d-route-status-table" />
              </div>
            </div>

            <div className="space-y-6">
              <section className="wp17-panel p-5" data-testid="wp17d-readiness-summary-panel">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">{t("Release readiness")}</div>
                <div className="mt-3 flex items-end justify-between gap-3">
                  <div>
                    <div className="font-display text-4xl font-black tracking-tight text-slate-900" data-testid="wp17d-completion-pct">{completionPct}%</div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{t("Calculated from the active platform review inventory.")}</p>
                  </div>
                  {isReady ? <ShieldCheck className="h-10 w-10 text-emerald-700" /> : <ShieldAlert className="h-10 w-10 text-red-700" />}
                </div>
                <div className="mt-4 h-3 rounded-full bg-slate-200" data-testid="wp17d-progress-bar-track">
                  <div className="h-3 rounded-full bg-gradient-to-r from-red-700 to-emerald-600" style={{ width: `${completionPct}%` }} data-testid="wp17d-progress-bar-fill" />
                </div>
                <div className="mt-4 rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900" data-testid="wp17d-go-no-go-panel">
                  <strong>{readinessVerdict}</strong> · {t("open review items and/or access blockers still remain before release signoff.")}
                </div>
              </section>

              <section className="wp17-panel p-5" data-testid="wp17d-blockers-panel">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">{t("Blocking issues")}</div>
                <div className="mt-4 space-y-4">
                  {BLOCKERS.map((blocker) => (
                    <div key={blocker.title} className="rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-4">
                      <div className="font-display text-lg font-black text-red-950">{t(blocker.title)}</div>
                      <p className="mt-2 text-sm leading-6 text-red-900">{t(blocker.detail)}</p>
                      <ul className="mt-3 space-y-1 text-xs text-red-900">
                        {blocker.evidence.map((item) => <li key={item}>• {t(item)}</li>)}
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
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold">{t("Review evidence log")}</div>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              {BATCHES.map((batch) => (
                <article key={batch.title} className="rounded-[1.35rem] border border-slate-200 bg-white px-4 py-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)]" data-testid={`wp17d-batch-${batch.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-display text-lg font-black text-slate-900 leading-tight">{t(batch.title)}</div>
                    {statusChip(batch.status, t)}
                  </div>
                  <div className="mt-3 text-xs font-mono uppercase tracking-[0.14em] text-slate-500">{batch.timestamp}</div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{t(batch.evidence)}</p>
                </article>
              ))}
            </div>
          </section>
        </main>
      </div>
    </AdminRouteShell>
  );
}