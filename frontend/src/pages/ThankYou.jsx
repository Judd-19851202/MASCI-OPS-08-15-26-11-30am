import React, { useState, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle2, ClipboardCheck, Home, Cloud, RefreshCw, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

// iter334 · Public Submission Thank-You Continuity Refinement
// DR-BLOCKER-001B · R-BL-1 + R-BL-5 · 3-state submission completion.
//   • delivered → green · "Filed." · backend confirmed persistence
//   • queued    → amber · "Saved Locally — Not Yet Delivered" · IDB queue
//                 with auto-retry + manual Retry Now button
//   • failed    → red   · "Daily Report Not Submitted"

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
  const navigate = useNavigate();
  const projectName = state?.projectName || "";
  const formType = state?.formType || "Inspection";
  const returnTo = state?.returnTo || "/submit";
  const recordId = state?.recordId || "";
  // DR-BLOCKER-001B · submission state — defaults to "delivered" for
  // backward compatibility with the dozens of other forms that route
  // through this page on success without passing the flag.
  const submissionState = state?.submissionState || "delivered";
  const lastError = state?.lastError || "";

  const homeHref = (returnTo && returnTo.startsWith("/daily/submit"))
    ? "/submit"
    : "/";

  const continuityLine = CONTINUITY_LINE[formType]
    || "The right people have visibility. You're done unless contacted.";

  const [retrying, setRetrying] = useState(false);
  const [retryNote, setRetryNote] = useState("");

  const onRetryNow = useCallback(async () => {
    setRetrying(true);
    setRetryNote("");
    try {
      const mod = await import("@/lib/resiliency/resiliencyQueue");
      await mod.drainQueue();
      // Brief grace period for the drain to attempt + resolve.
      setTimeout(() => {
        setRetrying(false);
        setRetryNote(t("Retry attempted · check your Daily Reports list to confirm delivery."));
      }, 1500);
    } catch (e) {
      setRetrying(false);
      setRetryNote(t("Retry could not be triggered — please return to the form."));
    }
  }, [t]);

  // ──────────────────────────────────────────────────────────────────
  // Variant assembly
  // ──────────────────────────────────────────────────────────────────
  const VARIANTS = {
    delivered: {
      iconBg: "bg-green-700",
      Icon: CheckCircle2,
      kicker: `${t(formType)} · ${t("On file")}`,
      kickerColor: "text-red-700",
      headline: t("Filed."),
      message: continuityLine,
      showRecordId: true,
      buttons: (
        <>
          <Button asChild className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900" data-testid="another-inspection-btn">
            <Link to={returnTo}><ClipboardCheck className="w-4 h-4 mr-2" />{t("File Another")}</Link>
          </Button>
          <Button asChild variant="outline" className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide" data-testid="done-btn">
            <Link to={homeHref}><Home className="w-4 h-4 mr-2" />{t("Done")}</Link>
          </Button>
        </>
      ),
    },
    queued: {
      iconBg: "bg-amber-600",
      Icon: Cloud,
      kicker: `${t(formType)} · ${t("Queued · Not Yet Delivered")}`,
      kickerColor: "text-amber-700",
      headline: t("Saved Locally."),
      message: (
        t("Your report is saved on this device and will retry automatically "
          + "when the connection is stable. Do not clear browser data until "
          + "delivery is confirmed.")
      ),
      showRecordId: false,
      buttons: (
        <>
          <Button
            onClick={onRetryNow}
            disabled={retrying}
            className="h-12 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide border-b-2 border-amber-800"
            data-testid="thank-you-retry-now"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? t("Retrying...") : t("Retry Now")}
          </Button>
          <Button
            onClick={() => navigate(returnTo, { replace: false })}
            variant="outline"
            className="h-12 border-2 border-amber-300 font-bold uppercase tracking-wide text-amber-800"
            data-testid="thank-you-stay-on-report"
          >
            {t("Stay On This Report")}
          </Button>
          <Button
            asChild
            variant="outline"
            className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide lg:col-span-2"
            data-testid="thank-you-return-to-start"
          >
            <Link to={homeHref}><Home className="w-4 h-4 mr-2" />{t("Return To Start")}</Link>
          </Button>
        </>
      ),
    },
    failed: {
      iconBg: "bg-red-700",
      Icon: AlertTriangle,
      kicker: `${t(formType)} · ${t("Not Delivered")}`,
      kickerColor: "text-red-700",
      headline: t("Submission Failed."),
      message: (
        t("Your report was not delivered. Please retry or contact support.")
        + (lastError ? `  (${lastError})` : "")
      ),
      showRecordId: false,
      buttons: (
        <>
          <Button
            onClick={onRetryNow}
            disabled={retrying}
            className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
            data-testid="thank-you-retry-failed"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? t("Retrying...") : t("Retry")}
          </Button>
          <Button
            onClick={() => navigate(returnTo, { replace: false })}
            variant="outline"
            className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide"
            data-testid="thank-you-stay-on-report-failed"
          >
            {t("Stay On This Report")}
          </Button>
        </>
      ),
    },
  };

  const v = VARIANTS[submissionState] || VARIANTS.delivered;
  const IconEl = v.Icon;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid={`thank-you-${submissionState}`}>
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
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${v.iconBg} mb-6`}>
            <IconEl className="w-12 h-12 text-white" />
          </div>
          <span
            className={`font-mono text-xs uppercase tracking-[0.25em] font-bold ${v.kickerColor}`}
            data-testid="thank-you-kicker"
          >
            {v.kicker}
          </span>
          <h1
            className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2"
            data-testid="thank-you-headline"
          >
            {v.headline}
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
            {t(v.message)}
          </p>

          {v.showRecordId && recordId && (
            <p
              className="mt-4 font-mono text-xs uppercase tracking-[0.18em] text-slate-500"
              data-testid="thank-you-reference"
            >
              <span className="text-slate-400">{t("Ref")} · </span>
              <span className="text-slate-700 font-bold select-all">{recordId}</span>
            </p>
          )}

          {retryNote && (
            <p
              className="mt-4 text-xs text-slate-600"
              data-testid="thank-you-retry-note"
            >
              {retryNote}
            </p>
          )}

          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-x-4 gap-y-4">
            {v.buttons}
          </div>
        </div>
      </main>
    </div>
  );
}
