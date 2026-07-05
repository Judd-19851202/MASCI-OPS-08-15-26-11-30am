/*
 * DR-ROI-001F-FINAL-REPAIR · Daily Report V2 shell.
 *
 * MASCI Daily Job Report — same look, same workflow, same data sources,
 * plus one new bottom section: the Daily Operational Summary. Nothing
 * else changes for the supervisor.
 *
 * No PDF buttons in the field form (that lives in PM/Admin/Doc Center).
 * No PM/Admin/Executive dashboard content in the field form.
 * No AI-agent branding.
 */
import React from "react";
import { Link } from "react-router-dom";
import { isDailyReportV2Enabled } from "@/lib/dailyReportV2Flag";
import { DrV2LangProvider, useDrV2Lang, LangToggle } from "@/lib/dailyReportV2Lang";
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
import PhotoIntelligencePanel from "./panels/PhotoIntelligencePanel";
import { useDrV2Draft, useDrV2Ai, useDrV2Approvals } from "./hooks/useDrV2";
import { StatusChip } from "./_ui";
import { MasciLogo } from "@/components/MasciLogo";
import { Save, Loader2 } from "lucide-react";

export default function DailyReportV2() {
  return (
    <DrV2LangProvider>
      <DrV2Inner />
    </DrV2LangProvider>
  );
}

function DrV2Inner() {
  const { t, lang } = useDrV2Lang();
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
    field_language: lang,
  });

  // Keep field_language on the draft in sync with the toggle so it's
  // autosaved + persisted server-side.
  React.useEffect(() => {
    setDraft((d) => (d.field_language === lang ? d : { ...d, field_language: lang }));
  }, [lang]);

  const { reportId, evidenceHash, savedAt, saving } = useDrV2Draft(draft);
  const ai = useDrV2Ai(reportId, evidenceHash);
  const approvals = useDrV2Approvals(reportId);

  if (!enabled) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-3xl mx-auto p-8 space-y-4" data-testid="dr-v2-disabled">
          <div className="flex justify-end"><LangToggle /></div>
          <h1 className="text-2xl font-semibold text-slate-900">{t("preview.title")}</h1>
          <p className="text-sm text-slate-600">{t("preview.body")}</p>
          <Link
            to="/new-daily-report"
            className="inline-flex items-center rounded-md bg-red-700 hover:bg-red-600 px-4 h-11 text-sm font-semibold text-white"
            data-testid="dr-v2-back-to-v1"
          >
            {t("preview.back")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900" data-testid="dr-v2-shell">
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-5">
        {/* --- MASCI header block --- */}
        <header className="bg-white border-2 border-slate-200 rounded-md p-4 sm:p-5 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <MasciLogo className="h-12 w-auto" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">
                {t("header.eyebrow")}
              </div>
              <h1
                className="font-display text-2xl sm:text-3xl font-bold text-slate-900 leading-tight"
                data-testid="dr-v2-header"
              >
                {t("header.title")}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <LangToggle />
            <span data-testid="dr-v2-report-id" className="font-mono text-xs text-slate-600">
              {reportId ? `#${reportId}` : t("header.draft")}
            </span>
            {saving ? (
              <span className="inline-flex items-center gap-1 text-xs text-slate-600" data-testid="dr-v2-status-saving">
                <Loader2 className="w-3 h-3 animate-spin" /> {t("status.saving")}
              </span>
            ) : savedAt ? (
              <StatusChip tone="green" testid="dr-v2-status-saved">
                <Save className="w-3 h-3 mr-1" /> {t("status.saved")}
              </StatusChip>
            ) : (
              <StatusChip tone="slate" testid="dr-v2-status-idle">{t("status.idle")}</StatusChip>
            )}
          </div>
        </header>

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
          <SignatureSubmitSection draft={draft} setDraft={setDraft} />
        </main>

        <p className="text-xs text-slate-500 pt-4 border-t border-slate-200">
          {t("footer.autosave")}
        </p>
      </div>
    </div>
  );
}
