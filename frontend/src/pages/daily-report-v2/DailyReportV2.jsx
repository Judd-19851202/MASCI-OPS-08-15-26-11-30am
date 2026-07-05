/*
 * DR-ROI-001 · Daily Report V2 shell (Track B expanded · Track C wired).
 *
 * Progressive workflow with 10 sections and 4 sticky intelligence panels.
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
import PmIntelligencePanel from "./panels/PmIntelligencePanel";
import PhotoIntelligencePanel from "./panels/PhotoIntelligencePanel";
import SupervisorApprovalPanel from "./panels/SupervisorApprovalPanel";
import { useDrV2Draft, useDrV2Ai, useDrV2Approvals } from "./hooks/useDrV2";

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

  // Debounced autosave + AI + approvals.
  const { reportId, evidenceHash, savedAt, saving } = useDrV2Draft(draft);
  const ai = useDrV2Ai(reportId, evidenceHash);
  const approvals = useDrV2Approvals(reportId);

  if (!enabled) {
    return (
      <div className="max-w-3xl mx-auto p-8 space-y-4" data-testid="dr-v2-disabled">
        <h1 className="text-2xl font-semibold">Daily Report V2 · preview only</h1>
        <p className="text-sm opacity-70">
          The Operational Intelligence Report is not enabled for your account
          yet. Your team is using the current Daily Report until this feature
          is rolled out. Nothing here submits data.
        </p>
        <a
          href="/new-daily-report"
          className="inline-flex items-center rounded-md bg-red-700 px-3 py-2 text-sm text-white"
          data-testid="dr-v2-back-to-v1"
        >
          Go to the current Daily Report
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100" data-testid="dr-v2-shell">
      <div className="max-w-[1400px] mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-6">
        <main className="space-y-6" data-testid="dr-v2-sections">
          <header className="border-b border-neutral-800 pb-4">
            <div className="text-xs uppercase tracking-widest opacity-60">DR-ROI-001 · V2 preview</div>
            <h1 className="text-3xl font-semibold mt-1">Operational Intelligence Report</h1>
            <p className="text-sm opacity-70 mt-2 max-w-2xl">
              Enter structured field facts. A short operational narrative is
              drafted from your evidence. You remain the source of truth · you
              accept, edit, or regenerate before submit.
            </p>
            <div className="mt-3 flex items-center gap-3 text-xs opacity-70" data-testid="dr-v2-savebar">
              <span data-testid="dr-v2-report-id">{reportId ? `Report ${reportId}` : "Draft not yet saved"}</span>
              {saving ? <span className="opacity-80">· saving…</span> : savedAt ? <span>· saved</span> : null}
              {ai.meta?.ai_available ? (
                <span className="ml-auto opacity-60">Operational summary: on</span>
              ) : null}
            </div>
          </header>

          <DaySetupSection draft={draft} setDraft={setDraft} />
          <CrewTimeSection draft={draft} setDraft={setDraft} />
          <EquipmentSection draft={draft} setDraft={setDraft} />
          <ActivityCardsSection draft={draft} setDraft={setDraft} />
          <ConstraintChipsSection draft={draft} setDraft={setDraft} />
          <TomorrowReadinessSection draft={draft} setDraft={setDraft} />
          <SafetyQualitySection draft={draft} setDraft={setDraft} />
          <PhotosSection draft={draft} setDraft={setDraft} />
          <AISummarySection ai={ai} approvals={approvals} />
          <SignatureSubmitSection draft={draft} setDraft={setDraft} />
        </main>

        <aside className="lg:sticky lg:top-4 h-fit space-y-4" data-testid="dr-v2-panels">
          <ConfidencePanel ai={ai} />
          <PmIntelligencePanel draft={draft} />
          <PhotoIntelligencePanel draft={draft} />
          <SupervisorApprovalPanel ai={ai} approvals={approvals} />
        </aside>
      </div>
    </div>
  );
}
