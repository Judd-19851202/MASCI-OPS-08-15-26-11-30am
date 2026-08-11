// Public Trench Safety · Report a Problem (standalone page)
//
// Sprint: Public Trench Safety UX Correction.
//
// Lets a crew member open a damage / unsafe-condition / missing-pins /
// missing-labels report from a direct URL (or from the dashboard tile)
// while keeping contextual back navigation to /trench-safety.
//
// The actual form is the existing PublicReportModal — the modal is held
// open by default on this route and closes back to /trench-safety.
//
// Route: /trench-safety/report  (public, no auth)
import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import PublicReportModal from "@/pages/trench_safety/PublicReportModal";
import { useT } from "@/lib/i18n";

export default function PublicTrenchSafetyReport() {
  const { t } = useT();
  const navigate = useNavigate();
  const [search] = useSearchParams();
  const defaultAssetId = (search.get("asset_id") || "").toUpperCase();
  const [open, setOpen] = useState(true);

  function handleClose() {
    setOpen(false);
    // Bounce back to the dashboard so crews aren't left on a blank page
    navigate("/trench-safety");
  }

  return (
    <OperationalPageFrame
      testId="public-report-page"
      backTo="/trench-safety"
      backLabel={t("Back to Trench Safety")}
      accent="amber"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-4xl"
      heroIcon={AlertTriangle}
      kicker={t("MASCI Trench Safety · Field Report")}
      title={t("Report a Problem")}
      description={t("Escalate damage, unsafe conditions, missing pins, or missing labels to Safety immediately. Reports create follow-up work. They do not change the asset status automatically.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="amber" testId="public-report-meta-safety">{t("Safety alerted")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="red" testId="public-report-meta-no-status">{t("No auto status change")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="public-report-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold mb-2">{t("When to use this")}</div>
          <p className="text-sm text-slate-600 mb-3">
            {t("Use this route when the issue needs Safety eyes now and the crew should not keep working through uncertainty.")}
          </p>
          <p className="mb-3 text-sm font-medium text-slate-700" data-testid="public-report-routing-coaching">
            {t("Reports are routed to the Safety team immediately.")}
          </p>
          <p className="mb-3 text-sm text-slate-600" data-testid="public-report-status-coaching">
            {t("They do not change the asset status automatically.")}
          </p>
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-full bg-amber-600 px-4 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white hover:bg-amber-700"
            data-testid="public-report-open-primary"
          >
            {t("Open Report Form")} <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Safety escalation workflow")}
    >
      <div className="space-y-5">

        {!open && (
          <div className="wp17-panel p-5 text-center text-sm text-slate-600" data-testid="public-report-closed">
            <p>{t("Report closed.")}</p>
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="mt-3 inline-flex items-center gap-1 rounded-full bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold uppercase tracking-[0.12em] px-4 py-2"
              data-testid="public-report-reopen"
            >
              {t("Open Report Form Again")} <ArrowRight className="w-3 h-3" />
            </button>
            <div className="mt-3">
              <Link to="/trench-safety" className="text-cyan-800 underline text-xs font-bold" data-testid="public-report-back-link">
                {t("Back to Trench Safety")}
              </Link>
            </div>
          </div>
        )}

        <PublicReportModal
          open={open}
          onClose={handleClose}
          defaultAssetId={defaultAssetId}
          lockAssetId={false}
        />
      </div>
    </OperationalPageFrame>
  );
}
