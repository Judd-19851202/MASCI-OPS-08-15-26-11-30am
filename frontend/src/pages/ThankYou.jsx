import React from "react";
import { Link, useLocation } from "react-router-dom";
import { CheckCircle2, ClipboardCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

// iter334 · Public Submission Thank-You Continuity Refinement
// ────────────────────────────────────────────────────────────
// Per-formType continuity messaging that matches the iter327
// homepage capability voice: calm, direct, field-proven, no fake
// positivity, no corporate SaaS phrasing. The user lands here after
// public form submission and should feel: filed correctly, the right
// people have visibility, you're done unless contacted.
//
// The HEADLINE collapses to one word ("Filed.") which lets the
// continuity sub-line carry the operational specifics.
//
// Both EN and ES strings live in i18n.js and translate via t().

const CONTINUITY_LINE = {
  "Incident Report":              "Safety has it. If additional information is needed, the team will follow up.",
  "Daily Report":                 "Operations, payroll, and project leadership can now review today's activity.",
  "Inspection":                   "Findings and corrective actions are now visible in Safety Review.",
  "Equipment Issuance":           "Issuance recorded. Equipment accountability and return status are now tracked.",
  "Equipment Training":           "Training recorded. Use and care accountability is now tracked.",
  "Equipment Pre-Op Inspection":  "Pre-op log filed. Shop and supervision have visibility for the day's run.",
  "Site Safety Meeting":          "Meeting recorded. Attendance and topics are now on file.",
  "DVIR":                         "Defect log filed. Shop has visibility for tomorrow's planning.",
  "Toolbox Meeting":              "Meeting recorded. Attendance and topics are now on file.",
  "JHA":                          "JHA filed. The plan is available for the crew and Safety review.",
};

export default function ThankYou() {
  const { t } = useT();
  const { state } = useLocation();
  const projectName = state?.projectName || "";
  const formType = state?.formType || "Inspection";
  const returnTo = state?.returnTo || "/submit";
  // iter335 · Submission tracking reference. Forms pass the canonical
  // identifier (report_number / incident_number / id fallback). If none
  // is present, the reference line is gracefully omitted — no
  // placeholder, no fake/random client-side ID.
  const recordId = state?.recordId || "";

  const continuityLine = CONTINUITY_LINE[formType]
    || "The right people have visibility. You're done unless contacted.";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div
          className="max-w-xl w-full bg-white border border-slate-200 rounded-md p-8 sm:p-12 text-center"
          data-testid="thank-you-card"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-700 mb-6">
            <CheckCircle2 className="w-12 h-12 text-white" />
          </div>
          <span
            className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold"
            data-testid="thank-you-kicker"
          >
            {t(formType)} · {t("On file")}
          </span>
          <h1
            className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2"
            data-testid="thank-you-headline"
          >
            {t("Filed.")}
          </h1>
          {projectName && (
            <p className="text-slate-700 text-base mt-3" data-testid="thank-you-project">
              {projectName}
            </p>
          )}
          <p
            className="text-slate-600 text-sm mt-4 leading-relaxed max-w-md mx-auto"
            data-testid="thank-you-continuity"
          >
            {t(continuityLine)}
          </p>

          {/* iter335 · subdued tracking reference · field crews can
              screenshot this for proof-of-submission. Only renders when
              a stable identifier was passed by the form. */}
          {recordId && (
            <p
              className="mt-4 font-mono text-xs uppercase tracking-[0.18em] text-slate-500"
              data-testid="thank-you-reference"
            >
              <span className="text-slate-400">{t("Ref")} · </span>
              <span className="text-slate-700 font-bold select-all">{recordId}</span>
            </p>
          )}

          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <Button
              asChild
              className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
              data-testid="another-inspection-btn"
            >
              <Link to={returnTo}>
                <ClipboardCheck className="w-4 h-4 mr-2" />
                {t("File Another")}
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide"
              data-testid="close-btn"
            >
              <a href="#" onClick={(e) => { e.preventDefault(); window.close(); }}>
                {t("Close Window")}
              </a>
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
