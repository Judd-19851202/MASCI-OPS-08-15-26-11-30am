import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Info } from "lucide-react";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { adaptLegacyThankYouState } from "@/lib/submissionConfirmation";

// A confirmation may only be shown when there is REAL submission
// evidence in the navigation state. Direct navigation to /thank-you
// (typed URL, refresh, back-button after state was cleared) carries an
// empty `location.state`, which previously fabricated a green
// "Submitted Successfully" with a blank "Record #" — a false-green
// truth defect (BP-0024). With no evidence we render an honest
// "nothing to confirm" state instead.
function hasSubmissionEvidence(state) {
  if (!state || typeof state !== "object") return false;
  return Boolean(
    state.documentNumber ||
      state.recordId ||
      state.reference ||
      state.queued === true ||
      state.workflowKey ||
      state.formType ||
      state.submittedAt ||
      state.createdAt,
  );
}

export default function ThankYou() {
  const location = useLocation();
  const rawState = location.state || {};
  const evidenced = hasSubmissionEvidence(rawState);

  const confirmation = React.useMemo(
    () => adaptLegacyThankYouState(rawState),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [location.state],
  );

  if (!evidenced) {
    return (
      <div
        className="min-h-screen bg-slate-50 flex items-center justify-center px-5 py-16"
        data-testid="submission-confirmation-none"
      >
        <div className="max-w-md w-full bg-white border-2 border-slate-200 rounded-[1.5rem] p-8 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-100 text-slate-500 mb-5">
            <Info className="w-7 h-7" />
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
            No submission to confirm
          </div>
          <h1 className="font-display text-2xl font-black tracking-tight text-slate-900 mt-2">
            Nothing was submitted in this session
          </h1>
          <p className="text-sm text-slate-600 mt-3 leading-relaxed">
            This page confirms a record right after you submit it. There is no
            submission attached to this visit, so there is nothing to show. Open
            a form to file a new record.
          </p>
          <Link
            to="/"
            data-testid="submission-confirmation-none-home"
            className="mt-6 inline-flex items-center justify-center h-12 w-full rounded-md bg-slate-950 hover:bg-slate-800 text-white font-bold uppercase tracking-[0.12em] text-xs"
          >
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return <SubmissionConfirmation confirmation={confirmation} />;
}
