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
import { StatusChip } from "./_ui";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { Save, FileText, Download, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

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
            this feature is rolled out.
          </p>
          <Link
            to="/new-daily-report"
            className="inline-flex items-center rounded-md bg-red-700 hover:bg-red-600 px-4 h-11 text-sm font-semibold text-white"
            data-testid="dr-v2-back-to-v1"
          >
            Go to the current Daily Report
          </Link>
        </div>
      </div>
    );
  }

  const pdfReady = false;
  const pdfHint = "PDF preview arrives in the next session · submit and download stay on schedule.";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900" data-testid="dr-v2-shell">
      {/* Platform-native header — same shape as V1 NewDailyReport. */}
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <MasciLogo className="h-10 w-auto" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
                Operational Intelligence Report
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900" data-testid="dr-v2-header">
                New Daily Report
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap" data-testid="dr-v2-savebar">
            <span data-testid="dr-v2-report-id" className="font-mono text-xs text-slate-600">
              {reportId ? `#${reportId}` : "Draft"}
            </span>
            {saving ? (
              <span className="inline-flex items-center gap-1 text-xs text-slate-600" data-testid="dr-v2-status-saving">
                <Loader2 className="w-3 h-3 animate-spin" /> Saving…
              </span>
            ) : savedAt ? (
              <StatusChip tone="green" testid="dr-v2-status-saved">
                <Save className="w-3 h-3 mr-1" /> Draft saved
              </StatusChip>
            ) : (
              <StatusChip tone="slate" testid="dr-v2-status-idle">Not saved yet</StatusChip>
            )}
            <Button
              type="button"
              variant="outline"
              className="h-11 border-2 border-slate-300"
              disabled={!pdfReady}
              title={pdfHint}
              data-testid="dr-v2-preview-pdf-btn"
            >
              <FileText className="w-4 h-4 mr-1" /> Preview PDF
            </Button>
            <Button
              type="button"
              variant="outline"
              className="h-11 border-2 border-slate-300"
              disabled={!pdfReady}
              title={pdfHint}
              data-testid="dr-v2-download-pdf-btn"
            >
              <Download className="w-4 h-4 mr-1" /> Download PDF
            </Button>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-2xl">
          Enter structured field facts. A short daily operational summary
          is drafted from your evidence · you remain the source of truth.
        </p>

        <main className="space-y-4" data-testid="dr-v2-sections">
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

        <p className="text-xs text-slate-500 pt-4 border-t border-slate-200">
          Draft autosaves as you work · refreshing this page restores your
          entries · minimum six field photos required before submit.
        </p>
      </div>
    </div>
  );
}
