// Shared chrome for /safety/trench-safety/* pages.
//
// Reuses SafetyShell (cyan-700 accent) and provides a small tab strip
// so navigation between Dashboard / Trench Equipment / Tabulated Data
// is consistent across the module.
//
// Phase 3 · MASCI Trench Safety Operations System.
import React from "react";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Boxes, BookOpen, BarChart3 } from "lucide-react";
import SafetyShell from "@/components/SafetyShell";
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
  // Detect whether we're under /admin/... or /safety/... so the tab
  // links stay inside the current portal (parity).
  const portalBase = loc.pathname.startsWith("/admin/trench-safety")
    ? "/admin/trench-safety"
    : "/safety/trench-safety";

  return (
    <SafetyShell title={title} kicker={kicker}>
      <div className="mb-6" data-testid="trench-safety-tabs">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold">
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
            return (
              <Link
                key={key}
                to={to}
                data-testid={`trench-tab-${key}`}
                className={
                  "inline-flex items-center gap-1.5 px-3 py-2 -mb-px border-b-2 text-xs font-bold uppercase tracking-[0.12em] " +
                  (on
                    ? "border-cyan-700 text-cyan-900"
                    : "border-transparent text-slate-500 hover:text-cyan-800 hover:border-cyan-300")
                }
              >
                <Icon className="w-3.5 h-3.5" />
                {t(label)}
              </Link>
            );
          })}
        </nav>
      </div>
      {children}
    </SafetyShell>
  );
}
