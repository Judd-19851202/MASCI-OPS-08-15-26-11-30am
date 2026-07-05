// DailyOperationalSummarySection.jsx — DR-CUTOVER-002
//
// A single, additive section rendered inside the existing Daily Job
// Report form (NewDailyReport.jsx) — never a separate form.
//
// Contract (see /app/memory/DR_CUTOVER_002_DAILY_SUMMARY_ARCHITECTURE.md):
//   - Never surfaces AI/model/provider/token/cost language.
//   - Never blocks Daily Report submit.
//   - Uses only fields already in the form's `data` state.
//   - Gracefully degrades when AI is off — a single non-alarming line.
//   - The supervisor is the source of truth: they can accept, edit,
//     regenerate, or clear. The last "accepted" text flows onto the
//     final submit payload via the daily_operational_summary field.
import React, { useCallback, useMemo, useState } from "react";
import {
  ClipboardEdit,
  RefreshCw,
  Check,
  Undo2,
  Loader2,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";

/** @typedef {import('react').ChangeEvent} ChangeEvent */

export default function DailyOperationalSummarySection({ data, set, t }) {
  const translate = t || ((s) => s);
  const [drafting, setDrafting] = useState(false);
  const [availability, setAvailability] = useState(/** @type {null|{enabled:boolean, reason:string|null}} */ (null));

  const summary = data?.daily_operational_summary ?? "";
  const status = data?.daily_operational_summary_status ?? "empty"; // empty | drafted | accepted
  const hasSummary = Boolean(summary && summary.trim().length > 0);

  // Prepare the sanitised subset of `data` we send to the draft endpoint.
  const buildPayload = useCallback(() => {
    const allow = [
      "project_name", "project_number", "location", "report_date",
      "prepared_by", "superintendent", "shift",
      "weather_summary", "schedule_delays", "schedule_delays_notes",
      "weather_impact", "weather_impact_notes",
      "safety_incidents_today", "injuries_reported", "incident_notes",
      "general_notes", "masci_crews", "subcontractors", "visitors",
      "equipment", "materials", "outbound_materials", "activities",
      "production", "constraints", "photos", "photo_captions",
      "narrative_sections",
    ];
    const out = {};
    for (const k of allow) if (k in (data || {})) out[k] = data[k];
    return out;
  }, [data]);

  const draftSummary = useCallback(async () => {
    setDrafting(true);
    try {
      const { data: resp } = await api.post(
        "/daily-reports/summary/draft",
        {
          payload: buildPayload(),
          language: data?.dr_language === "es" ? "es" : "en",
        },
      );
      setAvailability({ enabled: !!resp?.enabled, reason: resp?.reason_disabled || null });
      if (!resp?.enabled) {
        // Non-alarming, no AI vocabulary.
        toast.message(translate("Summary assistance is not enabled. You may submit the report normally."));
        return;
      }
      const text = (resp?.summary_text || "").trim();
      if (!text) {
        toast.message(translate("Not enough details yet to draft a summary. Fill in more sections and try again."));
        return;
      }
      set("daily_operational_summary", text);
      set("daily_operational_summary_status", "drafted");
      set("daily_operational_summary_source", "draft");
      set("daily_operational_summary_language",
          data?.dr_language === "es" ? "es" : "en");
      set("daily_operational_summary_evidence_refs", resp?.evidence_refs || []);
      toast.success(translate("Draft summary ready — review and edit before submitting."));
    } catch (e) {
      // Never block the form. Report a graceful, non-technical message.
      setAvailability({ enabled: false, reason: "unavailable" });
      toast.message(translate("Summary assistance is not available right now. You may submit the report normally."));
    } finally {
      setDrafting(false);
    }
  }, [buildPayload, data, set, translate]);

  const acceptSummary = useCallback(() => {
    if (!hasSummary) return;
    set("daily_operational_summary_status", "accepted");
    set("daily_operational_summary_source",
        data?.daily_operational_summary_source === "draft" ? "draft" : "user_edited");
    toast.success(translate("Summary accepted."));
  }, [hasSummary, data, set, translate]);

  const clearSummary = useCallback(() => {
    set("daily_operational_summary", "");
    set("daily_operational_summary_status", "empty");
    set("daily_operational_summary_source", null);
    set("daily_operational_summary_evidence_refs", []);
  }, [set]);

  const isAccepted = status === "accepted";
  const helper = useMemo(() => {
    if (availability && availability.enabled === false) {
      return translate("Summary assistance is not enabled. You may submit the report normally.");
    }
    if (isAccepted) return translate("Summary accepted. You can still edit it before submitting.");
    if (hasSummary) return translate("Review the summary before submitting. Edit anything that needs corrected.");
    return translate("Optional. Draft a professional summary of today's work, then review and edit before submitting.");
  }, [availability, isAccepted, hasSummary, translate]);

  return (
    <section
      className="border border-slate-200 bg-white rounded-md p-4 sm:p-5 mt-6"
      data-testid="daily-operational-summary-section"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-md bg-slate-900 text-white inline-flex items-center justify-center shrink-0">
          <ClipboardEdit className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
            {translate("Optional")}
          </div>
          <h3 className="font-display text-lg font-black tracking-tight" data-testid="daily-summary-title">
            {translate("Daily Operational Summary")}
          </h3>
          <p className="text-xs text-slate-600 mt-1 leading-relaxed" data-testid="daily-summary-helper">
            {helper}
          </p>
        </div>
      </div>

      <div className="mt-4">
        <Textarea
          data-testid="daily-summary-textarea"
          value={summary}
          onChange={(e) => {
            set("daily_operational_summary", e.target.value);
            if (status === "accepted") set("daily_operational_summary_status", "drafted");
            if (status === "empty") set("daily_operational_summary_status", "drafted");
            set("daily_operational_summary_source", "user_edited");
          }}
          rows={hasSummary ? 8 : 4}
          placeholder={translate("The summary will appear here after you Draft, or you can type your own.")}
          className={hasSummary ? "font-serif" : ""}
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            size="sm"
            variant={hasSummary ? "outline" : "default"}
            onClick={draftSummary}
            disabled={drafting}
            data-testid="daily-summary-draft-btn"
          >
            {drafting
              ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
              : hasSummary
                ? <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                : <ClipboardEdit className="w-3.5 h-3.5 mr-1.5" />}
            {drafting
              ? translate("Drafting…")
              : hasSummary
                ? translate("Regenerate")
                : translate("Draft Summary")}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="default"
            onClick={acceptSummary}
            disabled={!hasSummary || isAccepted}
            data-testid="daily-summary-accept-btn"
          >
            <Check className="w-3.5 h-3.5 mr-1.5" />
            {isAccepted ? translate("Accepted") : translate("Accept Summary")}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={clearSummary}
            disabled={!hasSummary}
            data-testid="daily-summary-clear-btn"
          >
            <Undo2 className="w-3.5 h-3.5 mr-1.5" />
            {translate("Clear")}
          </Button>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {isAccepted && (
            <span
              data-testid="daily-summary-accepted-badge"
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 border border-emerald-300 bg-emerald-50 text-emerald-800 font-semibold"
            >
              <Check className="w-3 h-3" />
              {translate("Accepted")}
            </span>
          )}
          {availability && availability.enabled === false && (
            <span
              data-testid="daily-summary-disabled-note"
              className="inline-flex items-center gap-1 text-slate-500"
            >
              <Info className="w-3 h-3" />
              {translate("Optional feature not enabled for this account.")}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
