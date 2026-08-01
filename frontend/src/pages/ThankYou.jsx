import React, { useState, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle2, ClipboardCheck, Home, Cloud, RefreshCw, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
import { OperationalOutcomeFrame } from "@/components/public/OperationalOutcomeFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";

const CONTINUITY_LINE = {
  "Incident Report": "Safety has it. If additional information is needed, the team will follow up.",
  "Daily Report": "Operations, payroll, and project leadership can now review today's activity.",
  "Inspection": "Findings and corrective actions are now visible in Safety Review.",
  "Equipment Issuance": "Issuance recorded. Equipment accountability and return status are now tracked.",
  "Equipment Training": "Training recorded. Use and care accountability is now tracked.",
  "Equipment Pre-Op Inspection": "Pre-op log filed. Shop and supervision have visibility for the day's run.",
  "Site Safety Meeting": "Meeting recorded. Attendance and topics are now on file.",
  DVIR: "Defect log filed. Shop has visibility for tomorrow's planning.",
  "Toolbox Meeting": "Meeting recorded. Attendance and topics are now on file.",
  JHA: "JHA filed. The plan is available for the crew and Safety review.",
};

export default function ThankYou() {
  const { t } = useT();
  const { state } = useLocation();
  const navigate = useNavigate();
  const projectName = state?.projectName || "";
  const formType = state?.formType || "Inspection";
  const returnTo = state?.returnTo || "/submit";
  const recordId = state?.recordId || "";
  const notificationState = state?.notificationState || "";
  const notificationDeliveryMode = state?.notificationDeliveryMode || "";
  const notificationCaptureAvailable = !!state?.notificationCaptureAvailable;
  const submissionState = state?.submissionState || "delivered";
  const lastError = state?.lastError || "";

  const homeHref = returnTo && returnTo.startsWith("/daily/submit") ? "/submit" : "/";
  const continuityLine = CONTINUITY_LINE[formType] || "The right people have visibility. You're done unless contacted.";
  const isPreviewNotificationCapture = submissionState === "delivered" && (
    notificationState === "captured_preview" || notificationDeliveryMode === "SAFE_CAPTURE" || notificationCaptureAvailable
  );

  const [retrying, setRetrying] = useState(false);
  const [retryNote, setRetryNote] = useState("");

  const onRetryNow = useCallback(async () => {
    setRetrying(true);
    setRetryNote("");
    try {
      const mod = await import("@/lib/resiliency/resiliencyQueue");
      await mod.drainQueue();
      setTimeout(() => {
        setRetrying(false);
        setRetryNote(t("Retry attempted · check your Daily Reports list to confirm delivery."));
      }, 1500);
    } catch {
      setRetrying(false);
      setRetryNote(t("Retry could not be triggered — please return to the form."));
    }
  }, [t]);

  const variants = {
    delivered: {
      iconBg: "bg-green-700",
      Icon: CheckCircle2,
      kicker: `${t(formType)} · ${t("On file")}`,
      title: t("Filed."),
      description: isPreviewNotificationCapture
        ? t("This preview submission was stored successfully. Notification was safely captured for certification and no operational email was sent.")
        : t(continuityLine),
      tone: "emerald",
      showRecordId: true,
      buttons: (
        <>
          <Button asChild className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="another-inspection-btn">
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
      title: t("Saved Locally."),
      description: t("Your report is saved on this device and will retry automatically when the connection is stable. Do not clear browser data until delivery is confirmed."),
      tone: "amber",
      showRecordId: false,
      buttons: (
        <>
          <Button onClick={onRetryNow} disabled={retrying} className="h-12 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide" data-testid="thank-you-retry-now">
            <RefreshCw className={`w-4 h-4 mr-2 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? t("Retrying...") : t("Retry Now")}
          </Button>
          <Button onClick={() => navigate(returnTo, { replace: false })} variant="outline" className="h-12 border-2 border-amber-300 font-bold uppercase tracking-wide text-amber-800" data-testid="thank-you-stay-on-report">
            {t("Stay On This Report")}
          </Button>
          <Button asChild variant="outline" className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide lg:col-span-2" data-testid="thank-you-return-to-start">
            <Link to={homeHref}><Home className="w-4 h-4 mr-2" />{t("Return To Start")}</Link>
          </Button>
        </>
      ),
    },
    failed: {
      iconBg: "bg-red-700",
      Icon: AlertTriangle,
      kicker: `${t(formType)} · ${t("Not Delivered")}`,
      title: t("Submission Failed."),
      description: t("Your report was not delivered. Please retry or contact support.") + (lastError ? ` (${lastError})` : ""),
      tone: "red",
      showRecordId: false,
      buttons: (
        <>
          <Button onClick={onRetryNow} disabled={retrying} className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="thank-you-retry-failed">
            <RefreshCw className={`w-4 h-4 mr-2 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? t("Retrying...") : t("Retry")}
          </Button>
          <Button onClick={() => navigate(returnTo, { replace: false })} variant="outline" className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide" data-testid="thank-you-stay-on-report-failed">
            {t("Stay On This Report")}
          </Button>
        </>
      ),
    },
  };

  const current = variants[submissionState] || variants.delivered;
  const IconEl = current.Icon;
  const accent = submissionState === "queued" ? "amber" : submissionState === "failed" ? "red" : "emerald";

  return (
    <OperationalOutcomeFrame
      testId={`thank-you-${submissionState}`}
      accent={accent}
      familyLabel={t("MASCI Operations Platform")}
      familyMeta={t("Submission outcome")}
      backTo={homeHref}
      backLabel={t("Back to start")}
      heroIcon={IconEl}
      kicker={current.kicker}
      title={current.title}
      description={current.description}
      heroMeta={(
        <>
          <OperationalStatusBadge tone={current.tone} testId="thank-you-status-badge">
            {submissionState === "queued" ? t("Queued") : submissionState === "failed" ? t("Needs retry") : t("Delivered")}
          </OperationalStatusBadge>
          {projectName ? <OperationalStatusBadge tone="cyan" testId="thank-you-project-badge">{projectName}</OperationalStatusBadge> : null}
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="thank-you-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("What happens next")}</div>
          <div className="text-sm text-slate-700 leading-6">{t(continuityLine)}</div>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Submission continuity")}
    >
      <div className="max-w-xl mx-auto w-full bg-white border border-slate-200 rounded-[1.5rem] p-8 sm:p-10 text-center shadow-[0_20px_50px_rgba(15,23,42,0.08)]" data-testid="thank-you-card">
        <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${current.iconBg} mb-6`}>
          <IconEl className="w-12 h-12 text-white" />
        </div>
        <span className="font-mono text-xs uppercase tracking-[0.25em] font-bold text-slate-600" data-testid="thank-you-kicker">
          {current.kicker}
        </span>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2" data-testid="thank-you-headline">
          {current.title}
        </h1>
        {projectName ? <p className="text-slate-700 text-base mt-3" data-testid="thank-you-project">{projectName}</p> : null}
        <p className="text-slate-600 text-sm mt-4 leading-relaxed max-w-md mx-auto" data-testid="thank-you-continuity">
          {current.description}
        </p>

        {current.showRecordId && recordId ? (
          <p className="mt-4 font-mono text-xs uppercase tracking-[0.18em] text-slate-500" data-testid="thank-you-reference">
            <span className="text-slate-400">{t("Ref")} · </span>
            <span className="text-slate-700 font-bold select-all">{recordId}</span>
          </p>
        ) : null}

        {retryNote ? <p className="mt-4 text-xs text-slate-600" data-testid="thank-you-retry-note">{retryNote}</p> : null}

        {current.showRecordId ? (
          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-left max-w-md mx-auto" data-testid="thank-you-downstream-commitments">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-900 font-bold mb-2">{t("Submitted — here's what happens next")}</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-800">
              <li data-testid="commitment-pdf">{t("PDF is being rendered and stored.")}</li>
              <li data-testid="commitment-email">{isPreviewNotificationCapture ? t("Preview only: notification was safely captured and no external email was sent.") : t("Auto-emails have been queued.")}</li>
              <li data-testid="commitment-shop">{t("Shop and Dispatch will see any defects immediately.")}</li>
              <li data-testid="commitment-safety-pm">{t("Safety and the PM will be notified per project routing.")}</li>
            </ul>
          </div>
        ) : null}

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-x-4 gap-y-4">
          {current.buttons}
        </div>
      </div>
    </OperationalOutcomeFrame>
  );
}