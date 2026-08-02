// Shared chrome for /safety/trench-safety/*, /admin/trench-safety/*,
// and /pm/trench-safety/* pages.
//
// Reuses SafetyShell (cyan-700 accent) for safety/admin contexts and
// PmShell (PM red chrome) for the PM-portal entry so PMs stay in their
// own shell instead of shell-hopping into Safety.
//
// Phase 3 · MASCI Trench Safety Operations System.
// TRACK 14.0-PLATFORM-DISCOVERABILITY · Wave B-P1 (D-A13) — PM context
// detection added so the new /pm/trench-safety route renders PmShell
// (PM-red chrome + PM sidebar) instead of forcing a shell hop.
import React from "react";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Boxes, BookOpen, BarChart3 } from "lucide-react";
import SafetyShell from "@/components/SafetyShell";
import PmShell from "@/components/PmShell";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { useT } from "@/lib/i18n";

const TABS = [
  { key: "hub",         slug: "",                icon: LayoutDashboard, label: "Dashboard" },
  { key: "assets",      slug: "/assets",         icon: Boxes,           label: "Trench Equipment" },
  { key: "excavations", slug: "/excavations",    icon: BarChart3,       label: "Excavations" },
  { key: "reports",     slug: "/reports",        icon: BarChart3,       label: "Reports" },
  { key: "tabulated",   slug: "/tabulated-data", icon: BookOpen,        label: "Tabulated Data" },
];

export default function TrenchSafetyShell({ active, title, kicker, description, children }) {
  const { t } = useT();
  const loc = useLocation();
  // Detect whether we're under /admin/..., /pm/..., or /safety/... so
  // the tab links stay inside the current portal (parity).
  const isPm = loc.pathname.startsWith("/pm/trench-safety");
  const isAdmin = loc.pathname.startsWith("/admin/trench-safety");
  const portalBase = isPm
    ? "/pm/trench-safety"
    : isAdmin
      ? "/admin/trench-safety"
      : "/safety/trench-safety";

  const portalLabel = isPm ? t("Project Management") : isAdmin ? t("Admin OS") : t("Safety Operations");
  const accentKicker = isPm ? "text-amber-700" : isAdmin ? "text-red-700" : "text-cyan-700";
  const activeCard = isPm
    ? "border-amber-300 bg-amber-50/90 text-amber-950"
    : isAdmin
      ? "border-red-300 bg-red-50/90 text-red-950"
      : "border-cyan-300 bg-cyan-50/90 text-cyan-950";
  const idleCard = "border-slate-200 bg-white/92 text-slate-700 hover:border-slate-300 hover:text-slate-950";

  const tabsNav = (
    <section className="wp17-panel p-4 sm:p-5" data-testid="trench-safety-tabs-shell">
      <div className={`font-mono text-[10px] uppercase tracking-[0.22em] font-bold ${accentKicker}`}>
        {portalLabel} · {t("Trench Safety")}
      </div>
      <div className="mt-2 text-sm text-slate-600 max-w-3xl">
        {t("Use one standard navigation strip for trench equipment, excavations, reports, and tabulated data across every portal context.")}
      </div>
      <nav className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-5" data-testid="trench-safety-tabs">
        {TABS.map(({ key, slug, icon: Icon, label }) => {
          const to = `${portalBase}${slug}`;
          const isHub = key === "hub" && loc.pathname === portalBase;
          const isActive =
            active === key ||
            (active == null && slug && loc.pathname.startsWith(to));
          const on = isActive || isHub;
          return (
            <Link
              key={key}
              to={to}
              data-testid={`trench-tab-${key}`}
              className={`rounded-[1.15rem] border px-4 py-3 transition-colors ${on ? activeCard : idleCard}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2 text-sm font-semibold">
                  <Icon className="h-4 w-4" />
                  {t(label)}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{on ? t("Active") : t("Open")}</span>
              </div>
            </Link>
          );
        })}
      </nav>
    </section>
  );

  const shellIntro = title ? (
    <section className="wp17-public-hero" data-testid="trench-safety-shell-intro">
      <div className={`font-mono text-[10px] uppercase tracking-[0.22em] font-bold ${accentKicker}`}>{portalLabel} · {t("Trench Safety")}</div>
      <h1 className="mt-3 font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900">{title}</h1>
      <p className="mt-3 max-w-3xl text-sm sm:text-base leading-6 text-slate-600">{description || kicker || t("Field visibility, trench asset oversight, and compliance reporting in one shared operating surface.")}</p>
    </section>
  ) : null;

  const body = (
    <div className="space-y-5" data-testid="trench-safety-shell-body">
      {shellIntro}
      {tabsNav}
      <div data-testid="trench-safety-shell-content">{children}</div>
    </div>
  );

  if (isPm) {
    return (
      <PmShell
        title={title || "Trench Safety"}
        section="trench-safety"
        showPageHeader={false}
        showMissionBanner={false}
      >
        {body}
      </PmShell>
    );
  }

  if (isAdmin) {
    return (
      <AdminRouteShell
        pageTitle={title || "Trench Safety"}
        subtitle={kicker || t("Company-wide trench safety operations and field review.")}
        portalRole="Admin · Trench Safety"
        crumbs={[
          { label: "Field Operations" },
          { label: "Trench Safety" },
        ]}
        showShellHeader={false}
        showBreadcrumbs={false}
        contentClassName="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 overflow-x-hidden"
        testId="admin-trench-safety-shell"
      >
        {body}
      </AdminRouteShell>
    );
  }

  return (
    <SafetyShell
      title={title}
      kicker={kicker}
      showPageHeader={false}
      showMissionBanner={false}
    >
      {body}
    </SafetyShell>
  );
}
