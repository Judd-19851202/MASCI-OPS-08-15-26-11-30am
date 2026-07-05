/*
 * DR-ROI-001 · Daily Report V2 shell.
 *
 * DR-ROI-001F Phase 1-2 pass: fully platform-aligned. Light theme,
 * platform primitives, no dark AI-looking chrome, no PM-dashboard
 * content inside the field form.
 *
 * V1 route at /daily/new is untouched. This surface is behind
 * `isDailyReportV2Enabled()` and posts ONLY to /api/dr-v2/* — never to
 * the V1 /api/daily-reports submit path.
 */
import React from "react";
import { isDailyReportV2Enabled } from "@/lib/dailyReportV2Flag";
import DaySetupSection from "./sections/DaySetupSection";
import CrewTimeSection from "./sections/CrewTimeSection";
import EquipmentSection from "./sections/EquipmentSection";
import ActivityCardsSection from "./sections/ActivityCardsSection";
import ConstraintChipsSection from "./sections/ConstraintChipsSection";
import TomorrowReadinessSection from "./sections/TomorrowReadinessSection";
import SafetyQualitySection from "./sections/SafetyQualitySection";
import PhotosSection from "./sections/PhotosSection";
import AISummarySection from "./sections/AISummarySection";
import SignatureSubmitSection from "./sections/SignatureSubmitSection";
import ConfidencePanel from "./panels/ConfidencePanel";
import PhotoIntelligencePanel from "./panels/PhotoIntelligencePanel";
import SupervisorApprovalPanel from "./panels/SupervisorApprovalPanel";
import { useDrV2Draft, useDrV2Ai, useDrV2Approvals } from "./hooks/useDrV2";
import { secondaryBtn, ghostBtn, StatusChip } from "./_ui";
import { Save, FileText, Download, Loader2 } from "lucide-react";

export default function DailyReportV2() {
  const enabled = isDailyReportV2Enabled();
  const [draft, setDraft] = React.useState({
    day_setup: {},
    masci_crews: [],
    equipment_used: [],
    activity_cards: [],
    constraint_cards: [],
    tomorrow_readiness: {},
    safety: {},
    photos: [],
    weather: {},
  });

  // Debounced autosave + narrative synthesis + approvals.
  const { reportId, evidenceHash, savedAt, saving } = useDrV2Draft(draft);
  const ai = useDrV2Ai(reportId, evidenceHash);
  const approvals = useDrV2Approvals(reportId);

  if (!enabled) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-3xl mx-auto p-8 space-y-4" data-testid="dr-v2-disabled">
          <h1 className="text-2xl font-semibold text-slate-900">
            Daily Report V2 · preview only
          </h1>
          <p className="text-sm text-slate-600">
            The next-generation Daily Report is not enabled for your account
            yet. Your team continues to use the current Daily Report until
            this feature is rolled out. Nothing here submits data.
          </p>
          <a
            href="/new-daily-report"
            className="inline-flex items-center rounded-md bg-red-700 hover:bg-red-600 px-4 h-11 text-sm font-semibold text-white"
            data-testid="dr-v2-back-to-v1"
          >
            Go to the current Daily Report
          </a>
        </div>
      </div>
    );
  }

  const pdfReady = false; // PDF renderer lands in the DR-ROI-001F PDF session.
  const pdfDisabledHint = pdfReady
    ? undefined
    : "PDF preview arrives in the next session · submit and download stay on schedule.";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900" data-testid="dr-v2-shell">
      {/* ------------- Sticky save/PDF status bar ---------------------- */}
      <div
        className="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-slate-200"
        data-testid="dr-v2-savebar"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
              Daily Report
            </span>
            <span
              className="text-sm font-semibold text-slate-900 truncate"
              data-testid="dr-v2-report-id"
            >
              {reportId ? `Report ${reportId}` : "New Daily Report"}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600 ml-auto">
            {saving ? (
              <span className="inline-flex items-center gap-1" data-testid="dr-v2-status-saving">
                <Loader2 className="w-3 h-3 animate-spin" /> Saving…
              </span>
            ) : savedAt ? (
              <StatusChip tone="green" testid="dr-v2-status-saved">
                <Save className="w-3 h-3 mr-1" /> Draft saved
              </StatusChip>
            ) : (
              <StatusChip tone="slate" testid="dr-v2-status-idle">Not saved yet</StatusChip>
            )}
            <button
              className={secondaryBtn}
              disabled={!pdfReady}
              title={pdfDisabledHint}
              data-testid="dr-v2-preview-pdf-btn"
            >
              <FileText className="w-4 h-4" /> Preview PDF
            </button>
            <button
              className={secondaryBtn}
              disabled={!pdfReady}
              title={pdfDisabledHint}
              data-testid="dr-v2-download-pdf-btn"
            >
              <Download className="w-4 h-4" /> Download PDF
            </button>
          </div>
        </div>
      </div>

      {/* ------------- Main content ------------------------------------ */}
      <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
        <header className="space-y-2" data-testid="dr-v2-header">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            Operational Intelligence Report · V2
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold text-slate-900">
            New Daily Report
          </h1>
          <p className="text-sm text-slate-600 max-w-2xl">
            Enter structured field facts. A short daily operational summary
            is drafted from your evidence. You remain the source of truth —
            you accept, edit, or regenerate before submit.
          </p>
        </header>

        <main className="space-y-5" data-testid="dr-v2-sections">
          <DaySetupSection draft={draft} setDraft={setDraft} />
          <CrewTimeSection draft={draft} setDraft={setDraft} />
          <EquipmentSection draft={draft} setDraft={setDraft} />
          <ActivityCardsSection draft={draft} setDraft={setDraft} />
          <ConstraintChipsSection draft={draft} setDraft={setDraft} />
          <TomorrowReadinessSection draft={draft} setDraft={setDraft} />
          <SafetyQualitySection draft={draft} setDraft={setDraft} />
          <PhotosSection draft={draft} setDraft={setDraft} />
          <PhotoIntelligencePanel draft={draft} />
          <AISummarySection ai={ai} approvals={approvals} />
          <ConfidencePanel ai={ai} />
          <SupervisorApprovalPanel ai={ai} approvals={approvals} />
          <SignatureSubmitSection draft={draft} setDraft={setDraft} />
        </main>

        <footer className="pt-4 pb-8 border-t border-slate-200">
          <p className="text-xs text-slate-500">
            Draft autosaves as you work. Refreshing this page restores your
            entries. Submit is enabled once required sections are complete.
          </p>
        </footer>
      </div>
    </div>
  );
}
