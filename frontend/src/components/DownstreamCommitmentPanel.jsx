import React from "react";
import { useT } from "@/lib/i18n";

/**
 * TRACK 19.09 · Phase 8 · Submit-Time Downstream Commitment Confirmation.
 *
 * Non-technical by default (5:30-AM foreman friendly) with an
 * expand-for-IDs affordance for auditors. Bilingual via useT().
 *
 * Renders after a successful submit — the caller passes:
 *   - open:        boolean · controls visibility
 *   - onClose:     () => void
 *   - kind:        "daily-report" | "equipment-inspection" | "dvir" | ...
 *                  Used to tailor the non-technical bullet list. Free-form
 *                  string; unknown values fall back to a generic bundle.
 *   - docId:       string (optional)
 *   - correlationId: string (optional)
 *   - pdfId:       string (optional)
 *   - defects:     number  (optional) · triggers OOS wording
 *   - extraBullets: string[] (optional) · additional non-technical lines
 *
 * Reusable across forms. Pure UI — no API calls, no schema change.
 */
export function DownstreamCommitmentPanel({
  open,
  onClose,
  kind = "generic",
  docId = "",
  correlationId = "",
  pdfId = "",
  defects = 0,
  extraBullets = [],
}) {
  const { t } = useT();
  const [showTech, setShowTech] = React.useState(false);

  if (!open) return null;

  const bullets = [
    t("PDF is being rendered and stored."),
    t("Auto-emails have been queued."),
  ];
  if (kind === "equipment-inspection" || kind === "dvir" || defects > 0) {
    bullets.push(t("Shop and Dispatch will see any defects immediately."));
  }
  bullets.push(t("Safety and the PM will be notified per project routing."));
  extraBullets.forEach((b) => b && bullets.push(b));

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center bg-slate-900/50 p-3"
      data-testid="downstream-commitment-panel"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-t-2xl sm:rounded-2xl w-full sm:max-w-md shadow-2xl border border-slate-200 overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200 bg-emerald-50">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-900">
            {t("Submitted — here's what happens next")}
          </div>
        </div>
        <div className="p-4 sm:p-5 space-y-2 text-sm text-slate-800">
          <ul className="list-disc list-inside space-y-1.5">
            {bullets.map((b, i) => (
              <li key={i} data-testid={`commitment-bullet-${i}`}>
                {b}
              </li>
            ))}
          </ul>

          <button
            type="button"
            className="mt-3 text-xs font-mono uppercase tracking-[0.15em] text-slate-500 hover:text-slate-800"
            onClick={() => setShowTech((v) => !v)}
            data-testid="commitment-toggle-tech"
          >
            {showTech ? t("Hide technical details") : t("Show technical details")}
          </button>

          {showTech && (
            <div
              className="mt-2 rounded-md bg-slate-50 border border-slate-200 p-3 text-xs font-mono text-slate-700 break-all"
              data-testid="commitment-technical-details"
            >
              {docId && (
                <div>
                  <span className="text-slate-500">ID: </span>
                  {docId}
                </div>
              )}
              {correlationId && (
                <div>
                  <span className="text-slate-500">{t("Correlation ID")}: </span>
                  {correlationId}
                </div>
              )}
              {pdfId && (
                <div>
                  <span className="text-slate-500">{t("PDF ID")}: </span>
                  {pdfId}
                </div>
              )}
              {!docId && !correlationId && !pdfId && (
                <div className="text-slate-400">—</div>
              )}
            </div>
          )}
        </div>
        <div className="p-3 border-t border-slate-200 flex justify-end">
          <button
            type="button"
            className="rounded-md bg-slate-900 text-white px-4 py-2 text-sm font-mono uppercase tracking-[0.15em] hover:bg-slate-700"
            onClick={onClose}
            data-testid="commitment-done-btn"
          >
            {t("Done")}
          </button>
        </div>
      </div>
    </div>
  );
}
