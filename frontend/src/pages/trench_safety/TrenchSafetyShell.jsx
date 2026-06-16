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
import { useT } from "@/lib/i18n";

const TABS = [
  { key: "hub",         slug: "",                icon: LayoutDashboard, label: "Dashboard" },
  { key: "assets",      slug: "/assets",         icon: Boxes,           label: "Trench Equipment" },
  { key: "excavations", slug: "/excavations",    icon: BarChart3,       label: "Excavations" },
  { key: "reports",     slug: "/reports",        icon: BarChart3,       label: "Reports" },
  { key: "tabulated",   slug: "/tabulated-data", icon: BookOpen,        label: "Tabulated Data" },
];

export default function TrenchSafetyShell({ active, title, kicker, children }) {
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

  const tabsNav = (
    <div className="mb-6" data-testid="trench-safety-tabs">
      <span className={
        "font-mono text-[10px] uppercase tracking-[0.25em] font-bold " +
        (isPm ? "text-amber-700" : "text-cyan-700")
      }>
        {t("Safety")} · {t("Trench Safety")}
      </span>
      <nav className="mt-2 flex flex-wrap gap-2 border-b border-slate-200 pb-px">
        {TABS.map(({ key, slug, icon: Icon, label }) => {
          const to = `${portalBase}${slug}`;
          const isHub = key === "hub" && loc.pathname === portalBase;
          const isActive =
            active === key ||
            (active == null && slug && loc.pathname.startsWith(to));
          const on = isActive || isHub;
          const onClasses = isPm
            ? "border-amber-700 text-amber-900"
            : "border-cyan-700 text-cyan-900";
          const offHoverClasses = isPm
            ? "border-transparent text-slate-500 hover:text-amber-800 hover:border-amber-300"
            : "border-transparent text-slate-500 hover:text-cyan-800 hover:border-cyan-300";
          return (
            <Link
              key={key}
              to={to}
              data-testid={`trench-tab-${key}`}
              className={
                "inline-flex items-center gap-1.5 px-3 py-2 -mb-px border-b-2 text-xs font-bold uppercase tracking-[0.12em] " +
                (on ? onClasses : offHoverClasses)
              }
            >
              <Icon className="w-3.5 h-3.5" />
              {t(label)}
            </Link>
          );
        })}
      </nav>
    </div>
  );

  if (isPm) {
    return (
      <PmShell title={title || "Trench Safety"} section="trench-safety">
        {tabsNav}
        {children}
      </PmShell>
    );
  }

  return (
    <SafetyShell title={title} kicker={kicker}>
      {tabsNav}
      {children}
    </SafetyShell>
  );
}
