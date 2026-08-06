import React from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Clock3, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { OperationalOutcomeFrame } from "@/components/public/OperationalOutcomeFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { formatLocalDateTime } from "@/lib/dateUtils";
import { useT } from "@/lib/i18n";

function ActionButton({ action, variant = "default", testId }) {
  if (!action) return null;
  const className = variant === "outline"
    ? "w-full h-12 border-2 border-slate-300 bg-white text-slate-900 hover:bg-slate-50 font-bold uppercase tracking-[0.12em] text-xs"
    : "w-full h-12 bg-slate-950 hover:bg-slate-800 text-white font-bold uppercase tracking-[0.12em] text-xs";

  if (action.onClick) {
    return (
      <Button type="button" onClick={action.onClick} className={className} data-testid={testId} variant={variant}>
        {action.label}
      </Button>
    );
  }

  return (
    <Button asChild className={className} data-testid={testId} variant={variant}>
      <Link to={action.to || "/"}>{action.label}</Link>
    </Button>
  );
}

function MetaRow({ label, value, testId, mono = false }) {
  const { t } = useT();
  if (!value) return null;
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t(label)}</div>
      <div className={mono ? "mt-1 font-mono text-base font-black text-slate-950" : "mt-1 text-sm font-semibold text-slate-900"}>{value}</div>
    </div>
  );
}

function ListCard({ title, items, testId }) {
  const { t } = useT();
  const safeItems = (items || []).filter(Boolean);
  if (!safeItems.length) return null;
  return (
    <div className="rounded-[1.5rem] border-2 border-slate-200 bg-white p-5" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t(title)}</div>
      <ul className="mt-3 space-y-2 text-sm text-slate-800">
        {safeItems.map((item, index) => (
          <li key={`${testId}-${index}`} className="flex gap-2">
            <span className="mt-[5px] h-1.5 w-1.5 rounded-full bg-slate-900 shrink-0" />
            <span>{t(item)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ToneConfig({ tone }) {
  if (tone === "amber") {
    return {
      icon: WifiOff,
      badge: "Queued",
      badgeTone: "amber",
      cardBorder: "border-amber-300",
      cardBg: "bg-amber-50",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-800",
    };
  }
  if (tone === "slate") {
    return {
      icon: Clock3,
      badge: "Pending",
      badgeTone: "slate",
      cardBorder: "border-slate-300",
      cardBg: "bg-slate-50",
      iconBg: "bg-slate-200",
      iconColor: "text-slate-800",
    };
  }
  return {
    icon: CheckCircle2,
    badge: "Filed",
    badgeTone: "emerald",
    cardBorder: "border-emerald-300",
    cardBg: "bg-emerald-50",
    iconBg: "bg-emerald-100",
    iconColor: "text-emerald-700",
  };
}

function ConfirmationBody({ confirmation }) {
  const { t } = useT();
  const tone = ToneConfig({ tone: confirmation.statusTone || confirmation.accent });
  const Icon = tone.icon;
  const submittedAt = confirmation.submittedAt ? formatLocalDateTime(confirmation.submittedAt) : "";

  return (
    <div className="space-y-5" data-testid="submission-confirmation-root">
      <div className={`rounded-[1.75rem] border-2 ${tone.cardBorder} ${tone.cardBg} p-5 sm:p-6 shadow-[0_20px_50px_rgba(15,23,42,0.08)]`}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${tone.iconBg}`}>
              <Icon className={`h-7 w-7 ${tone.iconColor}`} />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500" data-testid="submission-confirmation-kicker">
                {t("Filed Confirmation")}
              </div>
              <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950" data-testid="submission-confirmation-title">
                {t(confirmation.title)}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-700" data-testid="submission-confirmation-description">
                {t(confirmation.description)}
              </p>
            </div>
          </div>
          <OperationalStatusBadge tone={tone.badgeTone} testId="submission-confirmation-status-badge">
            {t(confirmation.successStatus || tone.badge)}
          </OperationalStatusBadge>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <MetaRow label="Success Status" value={t(confirmation.successStatus)} testId="submission-confirmation-success-status" />
          <MetaRow label="Document Number" value={`${t(confirmation.documentTypeLabel)} ${confirmation.documentNumber}`.trim()} testId="submission-confirmation-document-number" mono />
          <MetaRow label="Submitted Date & Time" value={submittedAt} testId="submission-confirmation-submitted-at" />
          <MetaRow label="Submitted By" value={confirmation.submittedBy} testId="submission-confirmation-submitted-by" />
          <MetaRow label="Project" value={confirmation.project} testId="submission-confirmation-project" />
          {confirmation.contextItems?.map((item) => (
            <MetaRow key={item.testId} label={item.label} value={item.value} testId={item.testId} />
          ))}
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <ListCard title="Routed To" items={confirmation.routedTo} testId="submission-confirmation-routed-to" />
        <ListCard title="What Happens Next" items={confirmation.whatHappensNext} testId="submission-confirmation-what-next" />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-[1.5rem] border-2 border-slate-200 bg-white p-5" data-testid="submission-confirmation-follow-up">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Follow-up Required")}</div>
          <p className="mt-3 text-sm leading-6 text-slate-800">{t(confirmation.followUpRequired)}</p>
        </div>
        <div className="rounded-[1.5rem] border-2 border-slate-200 bg-white p-5" data-testid="submission-confirmation-processing-status">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Expected Processing Status")}</div>
          <p className="mt-3 text-sm leading-6 text-slate-800">{t(confirmation.expectedProcessingStatus)}</p>
        </div>
      </div>

      {confirmation.note ? (
        <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700" data-testid="submission-confirmation-note">
          {t(confirmation.note)}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="submission-confirmation-actions">
        <ActionButton action={confirmation.startAnother} testId="submission-confirmation-start-another" />
        <ActionButton action={confirmation.returnToPortal} variant="outline" testId="submission-confirmation-return-to-portal" />
        <ActionButton action={confirmation.openRecord} variant="outline" testId="submission-confirmation-open-record" />
        <ActionButton action={confirmation.viewFiledCopy} variant="outline" testId="submission-confirmation-view-filed-copy" />
        <ActionButton action={confirmation.printFiledCopy} variant="outline" testId="submission-confirmation-print-filed-copy" />
      </div>
    </div>
  );
}

export function SubmissionConfirmation({ confirmation, embedded = false }) {
  const { t } = useT();
  if (embedded) {
    return <ConfirmationBody confirmation={confirmation} />;
  }

  return (
    <OperationalOutcomeFrame
      testId="submission-confirmation-screen"
      accent={confirmation.accent || "emerald"}
      familyLabel={t(confirmation.familyLabel || "Operations")}
      familyMeta={t(confirmation.familyMeta || "Submission workflow")}
      backTo={confirmation.backTo || confirmation.returnToPortal?.to || "/"}
      backLabel={t(confirmation.backLabel || confirmation.returnToPortal?.label || "Return to Portal")}
      heroIcon={CheckCircle2}
      kicker={t("MASCI · Submitted Successfully")}
      title={t(confirmation.title)}
      description={t(confirmation.description)}
      heroMeta={<OperationalStatusBadge tone={confirmation.statusTone || confirmation.accent || "emerald"} testId="submission-confirmation-hero-badge">{t(confirmation.successStatus)}</OperationalStatusBadge>}
      footerText={t(confirmation.footerText || "MASCI Operations Platform · Submission filing standard")}
    >
      <ConfirmationBody confirmation={confirmation} />
    </OperationalOutcomeFrame>
  );
}

export default SubmissionConfirmation;