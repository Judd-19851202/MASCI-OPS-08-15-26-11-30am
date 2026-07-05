import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";

/**
 * DR-ROI-001F-FINAL-REPAIR · Amendment.
 *
 * MASCI Daily Job Report top banner — restored across V1 + V2 without
 * mutating the V1 file. This component is intentionally byte-equivalent
 * to the V1 banner at NewDailyReport.jsx:1260–1307 in structure and
 * Tailwind class list (bg-slate-900 · border-b-4 border-red-700 · sticky
 * top-0 · z-10 · max-w-4xl inner). The right-hand cluster accepts
 * children so each caller can inject its own status + toggle + submit.
 *
 * V1 will continue to render its inline banner. V2 renders this one.
 * Both pages carry the same navy MASCI top identity.
 */
export function DailyReportTopBanner({ children, backLink = "/", showBackLink = true }) {
  return (
    <header
      className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10"
      data-testid="dr-top-banner"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
        {showBackLink ? (
          <Link
            to={backLink}
            className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="dr-top-banner-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Home
          </Link>
        ) : (
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
        )}
        <MasciLogo
          variant="mark"
          size="md"
          className={showBackLink ? "" : "sm:hidden"}
          homeLink={backLink}
        />
        <div
          className="flex items-center gap-2"
          data-testid="dr-top-banner-actions"
        >
          {children}
        </div>
      </div>
    </header>
  );
}

export default DailyReportTopBanner;
