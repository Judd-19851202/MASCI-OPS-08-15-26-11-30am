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
import PublicTrenchHeader from "@/components/trench/PublicTrenchHeader";
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
    <div className="min-h-screen bg-slate-50" data-testid="public-report-page">
      <div className="caution-stripe" />
      <PublicTrenchHeader
        backTo="/trench-safety"
        backLabel="Back to Trench Safety"
        testIdPrefix="public-report"
        accent="amber"
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        <div className="text-center mb-4">
          <AlertTriangle className="w-7 h-7 mx-auto text-amber-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Field Report")}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-report-title">
            {t("Report a Problem")}
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto mt-2">
            {t("Tell Safety what you're seeing — damage, an unsafe condition, missing pins, or missing labels. Reports are routed to the Safety team immediately. They do not change the asset status automatically.")}
          </p>
        </div>

        {!open && (
          <div className="bg-white border border-slate-200 rounded-md p-4 text-center text-sm text-slate-600" data-testid="public-report-closed">
            <p>{t("Report closed.")}</p>
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="mt-3 inline-flex items-center gap-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold uppercase tracking-[0.12em] rounded px-3 py-2"
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

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>
    </div>
  );
}
