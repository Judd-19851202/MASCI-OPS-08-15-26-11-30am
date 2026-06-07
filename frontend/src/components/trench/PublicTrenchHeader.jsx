// Public Trench Safety header — contextual back navigation + HOME.
//
// Sprint: Public Trench Safety UX Correction (post Phase 6, pre Phase 7).
//
// Pattern:
//   [ ← back to <context> ]   [ MASCI mark ]   [ HOME · LangToggle ]
//
// The contextual back link lets crews step one level out of the
// trench-safety stack without being yanked all the way to the
// MASCI landing page. HOME is preserved as an explicit, separate
// affordance per directive.
import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Home } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

export default function PublicTrenchHeader({
  backTo = "/trench-safety",
  backLabel = "Back to Trench Safety",
  testIdPrefix = "trench-public",
  accent = "cyan", // cyan | amber | red
}) {
  const { t } = useT();
  const accentBorder = {
    cyan: "border-cyan-700",
    amber: "border-amber-500",
    red: "border-red-700",
  }[accent] || "border-cyan-700";

  return (
    <header className={`bg-slate-900 border-b-4 ${accentBorder}`} data-testid={`${testIdPrefix}-header`}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
        <Link
          to={backTo}
          className="inline-flex items-center text-white hover:text-cyan-300 text-xs font-bold uppercase tracking-wide"
          data-testid={`${testIdPrefix}-back`}
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          <span>{t(backLabel)}</span>
        </Link>

        <MasciLogo variant="mark" size="md" homeLink="/" />

        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-white hover:text-cyan-300 text-[10px] font-bold uppercase tracking-[0.14em] border border-white/20 hover:border-cyan-400 rounded px-2 py-1"
            data-testid={`${testIdPrefix}-home`}
            title={t("MASCI Home")}
          >
            <Home className="w-3 h-3" />
            <span className="hidden sm:inline">{t("Home")}</span>
          </Link>
          <LangToggle />
        </div>
      </div>
    </header>
  );
}
