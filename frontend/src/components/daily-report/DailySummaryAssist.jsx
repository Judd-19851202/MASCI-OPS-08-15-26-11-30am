import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Sparkles,
  RefreshCw,
  Check,
  Loader2,
  FileWarning,
  PencilLine,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

function buildDeterministicFallback(data) {
  const bits = [];
  if (data?.masci_crews?.length) {
    const total = data.masci_crews.reduce((s, r) => s + (Number(r.hours_worked) || 0), 0);
    bits.push(`Crew reported ${data.masci_crews.length} entries, ${total.toFixed(1)} labor hours.`);
  }
  const acts = data?.activity_cards || data?.activities || [];
  if (acts.length) bits.push(`${acts.length} activity card(s) recorded.`);
  const equip = data?.equipment_used || data?.equipment || [];
  if (equip.length) bits.push(`${equip.length} equipment entries.`);
  const mats = data?.materials || [];
  if (mats.length) bits.push(`${mats.length} material deliveries.`);
  const delays = data?.delays || data?.delay_events || [];
  if (delays.length) bits.push(`${delays.length} delay/issue note(s).`);
  const safety = data?.safety_quality?.notes || data?.safety_notes || "";
  if (safety?.trim()) bits.push("Safety notes present.");
  const weather = data?.weather_summary || data?.day_setup?.weather_summary || "";
  if (weather) bits.push(`Weather: ${weather}.`);
  return bits.join(" ") || "Daily activity recorded. No AI summary generated (assist disabled or unavailable).";
}

function toEvidenceDraft(reportId, data, photoObservations = []) {
  return {
    report_id: reportId,
    project_number: data.project_number || "unknown",
    project_name: data.project_name || "",
    client: data.client || "",
    project_manager: data.project_manager || "",
    location: data.location || "",
    report_date: data.report_date || "",
    day_setup: {
      weather_summary: data.weather_summary || data.day_setup?.weather_summary || "",
      supervisor_name: data.supervisor_name || data.foreman || data.prepared_by || "",
      temperature_f: data.temperature_f ?? data.weather_temp ?? null,
      precipitation: data.precipitation ?? null,
      conditions: data.weather_conditions || "",
    },
    activity_cards: (data.activity_cards || data.activities || []).slice(0, 25),
    masci_crews: (data.masci_crews || []).slice(0, 40),
    equipment_used: (data.equipment_used || data.equipment || []).slice(0, 40),
    materials: (data.materials || []).slice(0, 40),
    outbound_materials: (data.outbound_materials || []).slice(0, 40),
    subcontractors: (data.subcontractors || data.subs_vendors || []).slice(0, 20),
    vendors: (data.vendors || []).slice(0, 20),
    visitors: (data.visitors || []).slice(0, 15),
    production: (data.production || []).slice(0, 25),
    constraint_cards: (data.constraint_cards || data.constraints_cards || data.constraints || data.delays || []).slice(0, 15),
    day_impacts: {
      schedule_delays: data.schedule_delays || "",
      schedule_delays_notes: data.schedule_delays_notes || "",
      weather_impact: data.weather_impact || "",
      weather_impact_notes: data.weather_impact_notes || "",
    },
    safety_quality: {
      notes: data.safety_quality?.notes || data.safety_notes || data.incident_notes || "",
      incidents_today: data.safety_quality?.incidents_today
        ?? (data.safety_incidents_today === "Yes" ? true : (data.incidents_today ?? false)),
      injuries_today: data.safety_quality?.injuries_today
        ?? (data.injuries_reported === "Yes" ? true : (data.injuries_today ?? false)),
      near_misses: (data.safety_quality?.near_misses || data.near_misses || []).slice(0, 10),
    },
    excavation: data.excavation || data.excavation_section || null,
    competent_person: data.competent_person
      || (data.excavation ? data.excavation.competent_person : null)
      || null,
    work_stoppage: data.work_stoppage || data.work_hold || null,
    tomorrow_readiness: {
      ...(data.tomorrow_readiness || {}),
      tomorrow_plan: (data.narrative_sections || {}).tomorrow_plan || "",
      pm_needs: (data.narrative_sections || {}).follow_ups || "",
    },
    general_notes: data.general_notes || "",
    photos: (data.photos || []).slice(0, 10),
    photo_captions: (data.photo_captions || []).slice(0, 10),
    photo_observations: (photoObservations || []).slice(0, 30),
    attachments: (data.attachments || []).slice(0, 20).map((a) => ({
      filename: a.filename || "",
      category: a.category || "",
      extension: a.extension || "",
      file_size: a.file_size || 0,
    })),
  };
}

function hasEnoughEvidence(data) {
  const acts = (data.activity_cards || data.activities || []).length;
  const crew = (data.masci_crews || []).length;
  const notes = (data.safety_quality?.notes || data.safety_notes || "").trim();
  const photos = (data.photos || []).length;
  const mats = (data.materials || []).length;
  const subs = (data.subcontractors || data.subs_vendors || []).length;
  const prod = (data.production || []).length;
  return acts > 0 || crew > 0 || photos > 0 || mats > 0 || subs > 0 || prod > 0 || notes.length > 20;
}

const DEBOUNCE_MS = 1200;
const REQUEST_TIMEOUT_MS = 60000;

export default function DailySummaryAssist({
  data,
  reportNumber,
  onAccept,
  onStateChange,
  testId = "daily-summary-assist",
}) {
  const { t } = useT();
  const reportId = useMemo(
    () => (reportNumber ? `dr-${reportNumber}` : `dr-draft-${Date.now()}`),
    [reportNumber],
  );

  const [status, setStatus] = useState("idle");
  const [narrative, setNarrative] = useState("");
  const [edited, setEdited] = useState("");
  const [confidence, setConfidence] = useState(null);
  const [uncertainties, setUncertainties] = useState([]);
  const [evidenceRefs, setEvidenceRefs] = useState([]);
  const [providerMasked, setProviderMasked] = useState(null);
  const [modelMasked, setModelMasked] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [accepted, setAccepted] = useState(false);
  const [aiAvailable, setAiAvailable] = useState(true);
  const [error, setError] = useState(null);
  const [decision, setDecision] = useState("pending");

  const abortRef = useRef(null);
  const debounceRef = useRef(null);
  const requestSeqRef = useRef(0);

  async function synthesize(force = false) {
    if (!hasEnoughEvidence(data)) {
      setStatus("idle");
      return;
    }
    if (abortRef.current) {
      try { abortRef.current.abort(); } catch (e) { void e; }
    }
    const controller = new AbortController();
    abortRef.current = controller;
    const mySeq = ++requestSeqRef.current;
    setStatus("building");
    setError(null);

    const timeoutId = setTimeout(() => {
      try { controller.abort(); } catch (e) { void e; }
    }, REQUEST_TIMEOUT_MS);
    const tStart = performance.now();

    try {
      let photoObservations = [];
      if (reportNumber) {
        try {
          const { data: photoIntel } = await api.get(
            `/daily-reports/${encodeURIComponent(reportNumber)}/photo-intelligence`,
            { signal: controller.signal },
          );
          photoObservations = photoIntel?.observations || [];
        } catch {
          photoObservations = [];
        }
      }
      const bundle = toEvidenceDraft(reportId, data, photoObservations);
      await api.post(`/dr-v2/drafts`, bundle, { signal: controller.signal }).catch(() => null);
      const { data: resp } = await api.post(
        `/dr-v2/ai/synthesize`,
        { report_id: reportId, agents: ["day_narrative"], force },
        { signal: controller.signal },
      );
      const tElapsed = Math.round(performance.now() - tStart);
      if (mySeq !== requestSeqRef.current) return;
      const out = (resp?.outputs || {}).day_narrative || {};
      const provider = resp?.provider || out.provider || null;
      const model = resp?.model || out.model || null;
      setProviderMasked(provider ? String(provider).slice(0, 20) : null);
      setModelMasked(model ? String(model).slice(0, 40) : null);
      setGeneratedAt(new Date().toISOString());
      setLatencyMs(tElapsed);

      if (out.ai_available === false) {
        setAiAvailable(false);
        const reason = (out.fallback_reason || "").toString();
        const uns = Array.isArray(out.uncertainties) ? out.uncertainties.slice(0, 5) : [];
        setUncertainties(uns);
        const fb = buildDeterministicFallback(data);
        setNarrative(fb);
        setEdited(fb);
        setEvidenceRefs([]);
        if (reason && reason !== "flag_off_or_missing_key") {
          setError(`AI provider unavailable — reason: ${reason}${uns[0] ? ` (${uns[0]})` : ""}`);
        }
        setStatus("ready");
        return;
      }

      setAiAvailable(true);
      const text = (out.narrative || "").trim();
      const fb = text || buildDeterministicFallback(data);
      setNarrative(fb);
      setEdited(fb);
      setConfidence(typeof out.confidence === "number" ? out.confidence : null);
      setUncertainties(Array.isArray(out.uncertainties) ? out.uncertainties.slice(0, 5) : []);
      setEvidenceRefs(Array.isArray(out.evidence_refs) ? out.evidence_refs.slice(0, 20) : []);
      setStatus("ready");
    } catch (err) {
      if (mySeq !== requestSeqRef.current) return;
      if (err?.name === "CanceledError" || err?.name === "AbortError") return;
      const fb = buildDeterministicFallback(data);
      setNarrative(fb);
      setEdited(fb);
      setAiAvailable(false);
      setError(err?.response?.data?.detail || err?.message || "assist_unavailable");
      setStatus("error");
    } finally {
      clearTimeout(timeoutId);
    }
  }

  useEffect(() => {
    if (accepted) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { synthesize(false); }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [
    JSON.stringify(data?.activity_cards || data?.activities || []),
    JSON.stringify(data?.masci_crews || []),
    JSON.stringify(data?.equipment_used || data?.equipment || []),
    JSON.stringify((data?.materials || []).map((m) => ({ ...m, ticket_photos: (m?.ticket_photos || []).length }))),
    JSON.stringify(data?.constraint_cards || data?.constraints || data?.delays || []),
    JSON.stringify(data?.production || []),
    JSON.stringify(data?.subcontractors || []),
    (data?.photos || []).length,
    (data?.narrative_sections || {}).tomorrow_plan,
    (data?.narrative_sections || {}).follow_ups,
    data?.safety_quality?.notes,
    data?.incident_notes,
    data?.weather_summary,
    accepted,
  ]);

  useEffect(() => {
    const frozen = (data?.ai_accepted_summary || "").trim();
    const meta = data?.ai_accepted_summary_meta || {};
    if (!frozen) return;
    setAccepted(true);
    setEdited(frozen);
    setDecision(meta?.source === "manual" ? "manual_accepted" : "ai_accepted");
  }, [data?.ai_accepted_summary, data?.ai_accepted_summary_meta]);

  useEffect(() => {
    const hasFrozen = !!(data?.ai_accepted_summary || "").trim();
    onStateChange?.({
      decision,
      accepted,
      hasFrozen,
      manualNeeded: decision === "manual_required",
      manualReady: decision === "manual_required" && !!edited.trim(),
      canSubmit: hasFrozen,
    });
  }, [accepted, data?.ai_accepted_summary, decision, edited, onStateChange]);

  function handleAccept() {
    const text = (edited || narrative || "").trim();
    if (!text) return;
    const editedByUser = text.trim() !== (narrative || "").trim();
    const source = !aiAvailable ? "fallback" : (editedByUser ? "edited" : "ai");
    const meta = {
      source,
      approved_by: data?.prepared_by || data?.superintendent || "",
      provider_masked: providerMasked,
      model_masked: modelMasked,
      generated_at: generatedAt,
      accepted_at: new Date().toISOString(),
      edited_by_user: editedByUser,
      edited_by_supervisor: editedByUser,
      confidence,
      evidence_refs: evidenceRefs,
      latency_ms: latencyMs,
    };
    setAccepted(true);
    setDecision("ai_accepted");
    onAccept?.(text, meta);
  }

  function handleRegenerate() {
    setAccepted(false);
    setDecision("pending");
    onAccept?.("", null);
    synthesize(true);
  }

  function handleRejectToManual() {
    setAccepted(false);
    setDecision("manual_required");
    onAccept?.("", null);
  }

  function handleManualAccept() {
    const text = edited.trim();
    if (!text) return;
    const meta = {
      source: "manual",
      approved_by: data?.prepared_by || data?.superintendent || "",
      provider_masked: null,
      model_masked: null,
      generated_at: null,
      accepted_at: new Date().toISOString(),
      edited_by_user: true,
      edited_by_supervisor: true,
      confidence: null,
      evidence_refs: [],
      latency_ms: null,
    };
    setAccepted(true);
    setDecision("manual_accepted");
    onAccept?.(text, meta);
  }

  return (
    <div data-testid={testId} className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-slate-600" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-slate-800">{t("Draft Summary")}</h3>
        {status === "building" && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-500" data-testid={`${testId}-status`}>
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
            {(data?.photos || []).length > 0 ? t("analyzing photos & writing summary…") : t("writing summary…")}
          </span>
        )}
        {status === "ready" && !accepted && (
          <span className="ml-2 text-xs text-emerald-700" data-testid={`${testId}-status`}>{t("ready")}</span>
        )}
        {accepted && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-emerald-700" data-testid={`${testId}-status`}>
            <Check className="h-3 w-3" aria-hidden="true" />{t("accepted")}
          </span>
        )}
      </div>

      <p className="mb-3 text-xs text-slate-500">
        {t("Grounded in the fields you've entered. Before submit, you must accept the AI summary, regenerate and then accept it, or reject it and approve a manual summary.")}
      </p>

      <div className="mb-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700" data-testid={`${testId}-gate-note`}>
        {decision === "manual_required"
          ? t("AI summary rejected. Write the final supervisor summary below, then approve it to unlock submit.")
          : accepted
            ? t("Summary locked for submission. If you change it, you must approve it again.")
            : t("Submission is blocked until one approved executive summary exists.")}
      </div>

      {status === "idle" && !narrative && (
        <p className="text-sm italic text-slate-500" data-testid={`${testId}-empty`}>
          {t("Add activities, crew, or notes to see a draft summary here.")}
        </p>
      )}

      {(narrative || status === "building" || decision === "manual_required" || decision === "manual_accepted") && (
        <>
          <Textarea
            data-testid={`${testId}-textarea`}
            value={edited}
            onChange={(e) => {
              if (accepted || (data?.ai_accepted_summary || "").trim()) {
                onAccept?.("", null);
              }
              setAccepted(false);
              if (decision !== "manual_required" && decision !== "manual_accepted") setDecision("pending");
              setEdited(e.target.value);
            }}
            className="min-h-[110px] text-sm"
            placeholder={status === "building" ? "Building…" : ""}
            disabled={status === "building" && !narrative}
          />

          {typeof confidence === "number" && (
            <p className="mt-1 text-xs text-slate-400" data-testid={`${testId}-confidence`}>
              confidence: {(confidence * 100).toFixed(0)}%
            </p>
          )}

          {uncertainties.length > 0 && (
            <ul className="mt-2 list-disc pl-4 text-xs text-amber-700" data-testid={`${testId}-uncertainties`}>
              {uncertainties.map((u, i) => <li key={i}>{u}</li>)}
            </ul>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="default"
              onClick={handleAccept}
              disabled={!edited.trim() || accepted || decision === "manual_required"}
              data-testid={`${testId}-accept`}
            >
              <Check className="mr-1 h-3 w-3" />
              {accepted && decision === "ai_accepted" ? t("Accepted") : t("Accept AI summary")}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleRegenerate}
              disabled={status === "building"}
              data-testid={`${testId}-regenerate`}
            >
              <RefreshCw className="mr-1 h-3 w-3" />{t("Regenerate")}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleRejectToManual}
              data-testid={`${testId}-reject-manual`}
            >
              <FileWarning className="mr-1 h-3 w-3" />{t("Reject AI & write manual")}
            </Button>
          </div>

          {(decision === "manual_required" || decision === "manual_accepted") && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3" data-testid={`${testId}-manual-block`}>
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-900">
                <PencilLine className="h-4 w-4" />{t("Supervisor manual summary")}
              </div>
              <Textarea
                data-testid={`${testId}-manual-textarea`}
                value={edited}
                onChange={(e) => {
                  if (accepted || (data?.ai_accepted_summary || "").trim()) {
                    onAccept?.("", null);
                  }
                  setAccepted(false);
                  setDecision("manual_required");
                  setEdited(e.target.value);
                }}
                className="min-h-[130px] bg-white text-sm"
                placeholder={t("Write the final approved executive summary exactly as it should appear on the permanent record.")}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="default"
                  onClick={handleManualAccept}
                  disabled={!edited.trim()}
                  data-testid={`${testId}-manual-accept`}
                >
                  <Check className="mr-1 h-3 w-3" />
                  {accepted && decision === "manual_accepted" ? t("Manual summary accepted") : t("Approve manual summary")}
                </Button>
              </div>
            </div>
          )}

          {error && (
            <div
              className="mt-3 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800"
              data-testid={`${testId}-error`}
              role="alert"
            >
              <div className="mb-0.5 font-semibold">{t("Summary assist unavailable")}</div>
              <div className="text-rose-700">{String(error)}</div>
              <div className="mt-1 text-rose-600/80">
                {t("Submission still requires an approved summary. Try Regenerate, or reject AI and approve a manual summary.")}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}