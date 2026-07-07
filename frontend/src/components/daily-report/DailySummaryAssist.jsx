// TRACK 22.9A · V1 Daily Report AI Summary Assist
//
// One calm, non-blocking summary section. Lives inside the V1
// NewDailyReport form. Never blocks typing, never blocks submit.
// If AI unavailable, a deterministic fallback appears. Supervisor
// can Accept · Edit · Regenerate · Ignore. Accepted summary is
// carried back to the parent form via onAccept() so it becomes
// part of the DR payload at submit time.
//
// No V2 shell resurrection — this reuses /api/dr-v2/ai/synthesize
// with an ephemeral draft keyed on the current DR's report_number.
// If the DR is never submitted, the ephemeral draft is orphaned in
// the drafts collection (30-day TTL cleans it up).
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Sparkles, RefreshCw, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// Deterministic fallback — used when AI is disabled OR the request
// times out OR the provider returns an unhelpful envelope. Grounded
// purely in the evidence bundle: no invention, no assumption.
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
  if (safety?.trim()) bits.push(`Safety notes present.`);
  const weather = data?.weather_summary || data?.day_setup?.weather_summary || "";
  if (weather) bits.push(`Weather: ${weather}.`);
  return bits.join(" ") || "Daily activity recorded. No AI summary generated (assist disabled or unavailable).";
}

// Compact evidence bundle sent to the AI backend. Only the fields
// the strict prompt actually cites are included — keeps prompt
// tokens (and latency) down.
function toEvidenceDraft(reportId, data, photoObservations = []) {
  return {
    report_id: reportId,
    project_number: data.project_number || "unknown",
    project_name: data.project_name || "",
    // TRACK 24.11B · include full project metadata snapshot so the
    // synthesizer can reference client / PM in narrative without
    // hitting jobs_master.
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
    // TRACK 24.11B · Missing evidence categories the previous
    // bundle silently dropped — the AI must see visitors, safety
    // observations (structured + note), tomorrow plan, excavation
    // + Competent Person snapshot, and work-stoppage / hold info.
    visitors: (data.visitors || []).slice(0, 15),
    constraints_cards: (data.constraints_cards || data.delays || []).slice(0, 15),
    safety_quality: {
      notes: data.safety_quality?.notes || data.safety_notes || "",
      incidents_today: data.safety_quality?.incidents_today ?? data.incidents_today ?? false,
      injuries_today: data.safety_quality?.injuries_today ?? data.injuries_today ?? false,
      near_misses: (data.safety_quality?.near_misses || data.near_misses || []).slice(0, 10),
    },
    excavation: data.excavation || data.excavation_section || null,
    competent_person: data.competent_person
      || (data.excavation ? data.excavation.competent_person : null)
      || null,
    work_stoppage: data.work_stoppage || data.work_hold || null,
    tomorrow_readiness: data.tomorrow_readiness || {},
    general_notes: data.general_notes || "",
    photos: (data.photos || []).slice(0, 10),
    // TRACK 22.9B · Grounded photo observations from the async
    // photo intelligence pipeline. Empty when analysis has not yet
    // completed or when photo intel is disabled — never blocks the
    // summary.
    photo_observations: (photoObservations || []).slice(0, 30),
    // TRACK 24.11B · Document attachment metadata (filename +
    // category + size) so the AI can reference "user uploaded a
    // permit PDF" without hallucinating the file contents.
    // Extraction (OCR / PDF text) is not currently implemented —
    // metadata only. AI must NOT claim to have read file contents.
    attachments: (data.attachments || []).slice(0, 20).map((a) => ({
      filename: a.filename || "",
      category: a.category || "",
      extension: a.extension || "",
      file_size: a.file_size || 0,
    })),
  };
}

// Small guard: is there enough content to bother synthesizing?
function hasEnoughEvidence(data) {
  const acts = (data.activity_cards || data.activities || []).length;
  const crew = (data.masci_crews || []).length;
  const notes = (data.safety_quality?.notes || data.safety_notes || "").trim();
  return acts > 0 || crew > 0 || notes.length > 20;
}

const DEBOUNCE_MS = 1200;
const REQUEST_TIMEOUT_MS = 15000; // hard timeout · > this → deterministic fallback

export default function DailySummaryAssist({ data, reportNumber, onAccept, testId = "daily-summary-assist" }) {
  const { t } = useT();
  const reportId = useMemo(
    () => (reportNumber ? `dr-${reportNumber}` : `dr-draft-${Date.now()}`),
    [reportNumber],
  );

  const [status, setStatus] = useState("idle"); // idle · building · ready · error · disabled
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

  const abortRef = useRef(null);
  const debounceRef = useRef(null);
  const requestSeqRef = useRef(0);

  // Cancel in-flight, start a fresh synthesize call.
  async function synthesize(force = false) {
    if (!hasEnoughEvidence(data)) {
      setStatus("idle");
      return;
    }
    // Cancel prior request
    if (abortRef.current) {
      try { abortRef.current.abort(); } catch { /* ignore */ }
    }
    const controller = new AbortController();
    abortRef.current = controller;
    const mySeq = ++requestSeqRef.current;
    setStatus("building");
    setError(null);

    const timeoutId = setTimeout(() => {
      try { controller.abort(); } catch { /* ignore */ }
    }, REQUEST_TIMEOUT_MS);
    const tStart = performance.now();

    try {
      // TRACK 22.9B · Best-effort fetch of grounded photo observations
      // from the async pipeline. Empty on failure; never blocks.
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
      // Save ephemeral V2 draft first (backend requires a draft to synthesize against).
      await api.post(`/dr-v2/drafts`, bundle, { signal: controller.signal }).catch(() => null);
      const { data: resp } = await api.post(
        `/dr-v2/ai/synthesize`,
        { report_id: reportId, agents: ["day_narrative"], force },
        { signal: controller.signal },
      );
      const tElapsed = Math.round(performance.now() - tStart);
      if (mySeq !== requestSeqRef.current) return; // stale
      const out = (resp?.outputs || {}).day_narrative || {};
      // Capture provider metadata for provenance (masked only — never raw keys)
      const provider = resp?.provider || out.provider || null;
      const model = resp?.model || out.model || null;
      setProviderMasked(provider ? String(provider).slice(0, 20) : null);
      setModelMasked(model ? String(model).slice(0, 40) : null);
      setGeneratedAt(new Date().toISOString());
      setLatencyMs(tElapsed);
      if (out.ai_available === false) {
        setAiAvailable(false);
        const fb = buildDeterministicFallback(data);
        setNarrative(fb);
        setEdited(fb);
        setEvidenceRefs([]);
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
      if (mySeq !== requestSeqRef.current) return; // stale
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

  // Debounced auto-synthesize when evidence changes.
  useEffect(() => {
    if (accepted) return; // once accepted, do not overwrite
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { synthesize(false); }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [
    JSON.stringify(data?.activity_cards || data?.activities || []),
    JSON.stringify(data?.masci_crews || []),
    JSON.stringify(data?.equipment_used || data?.equipment || []),
    JSON.stringify(data?.materials || []),
    JSON.stringify(data?.constraints_cards || data?.delays || []),
    data?.safety_quality?.notes,
    data?.weather_summary,
    accepted,
  ]);

  function handleAccept() {
    const text = (edited || narrative || "").trim();
    if (!text) return;
    const editedByUser = text.trim() !== (narrative || "").trim();
    const source = !aiAvailable ? "fallback" : (editedByUser ? "edited" : "ai");
    const meta = {
      source,
      provider_masked: providerMasked,
      model_masked: modelMasked,
      generated_at: generatedAt,
      accepted_at: new Date().toISOString(),
      edited_by_user: editedByUser,
      confidence,
      evidence_refs: evidenceRefs,
      latency_ms: latencyMs,
    };
    setAccepted(true);
    onAccept?.(text, meta);
  }

  function handleRegenerate() {
    setAccepted(false);
    synthesize(true);
  }

  function handleClear() {
    setAccepted(false);
    setNarrative("");
    setEdited("");
  }

  return (
    <div data-testid={testId} className="border border-slate-200 rounded-lg bg-white p-4">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-4 h-4 text-slate-600" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-slate-800">{t("Draft Summary")}</h3>
        {status === "building" && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-500" data-testid={`${testId}-status`}>
            <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
            {t("building…")}
          </span>
        )}
        {status === "ready" && !accepted && (
          <span className="ml-2 text-xs text-emerald-700" data-testid={`${testId}-status`}>{t("ready")}</span>
        )}
        {accepted && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-emerald-700" data-testid={`${testId}-status`}>
            <Check className="w-3 h-3" aria-hidden="true" />{t("accepted")}
          </span>
        )}
        {!aiAvailable && status !== "building" && (
          <span className="ml-2 text-xs text-slate-500" data-testid={`${testId}-fallback`}>{t("using deterministic summary")}</span>
        )}
      </div>
      <p className="text-xs text-slate-500 mb-3">
        {t("Grounded in the fields you've entered. Never invents facts. Optional — you can accept, edit, regenerate, or ignore.")}
      </p>

      {status === "idle" && !narrative && (
        <p className="text-sm text-slate-500 italic" data-testid={`${testId}-empty`}>
          {t("Add activities, crew, or notes to see a draft summary here.")}
        </p>
      )}

      {(narrative || status === "building") && (
        <>
          <Textarea
            data-testid={`${testId}-textarea`}
            value={edited}
            onChange={(e) => { setAccepted(false); setEdited(e.target.value); }}
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
            <ul className="mt-2 text-xs text-amber-700 list-disc pl-4" data-testid={`${testId}-uncertainties`}>
              {uncertainties.map((u, i) => <li key={i}>{u}</li>)}
            </ul>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="default"
              onClick={handleAccept}
              disabled={!edited?.trim() || accepted}
              data-testid={`${testId}-accept`}
            >
              <Check className="w-3 h-3 mr-1" />
              {accepted ? "Accepted" : "Accept & attach"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleRegenerate}
              disabled={status === "building"}
              data-testid={`${testId}-regenerate`}
            >
              <RefreshCw className="w-3 h-3 mr-1" />{t("Regenerate")}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={handleClear}
              data-testid={`${testId}-clear`}
            >
              {t("Ignore")}
            </Button>
          </div>
          {error && (
            <p className="mt-2 text-xs text-slate-500" data-testid={`${testId}-error`}>
              {t("Summary assist unavailable — you can still submit normally.")}
            </p>
          )}
        </>
      )}
    </div>
  );
}
