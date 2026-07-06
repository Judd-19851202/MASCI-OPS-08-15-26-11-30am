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
function toEvidenceDraft(reportId, data) {
  return {
    report_id: reportId,
    project_number: data.project_number || "unknown",
    report_date: data.report_date || "",
    day_setup: {
      weather_summary: data.weather_summary || data.day_setup?.weather_summary || "",
      supervisor_name: data.supervisor_name || data.foreman || "",
      temperature_f: data.temperature_f ?? null,
      precipitation: data.precipitation ?? null,
    },
    activity_cards: (data.activity_cards || data.activities || []).slice(0, 25),
    masci_crews: (data.masci_crews || []).slice(0, 40),
    equipment_used: (data.equipment_used || data.equipment || []).slice(0, 40),
    materials: (data.materials || []).slice(0, 40),
    subcontractors: (data.subcontractors || []).slice(0, 20),
    constraints_cards: (data.constraints_cards || data.delays || []).slice(0, 15),
    safety_quality: {
      notes: data.safety_quality?.notes || data.safety_notes || "",
    },
    tomorrow_readiness: data.tomorrow_readiness || {},
    photos: (data.photos || []).slice(0, 10),
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
  const reportId = useMemo(
    () => (reportNumber ? `dr-${reportNumber}` : `dr-draft-${Date.now()}`),
    [reportNumber],
  );

  const [status, setStatus] = useState("idle"); // idle · building · ready · error · disabled
  const [narrative, setNarrative] = useState("");
  const [edited, setEdited] = useState("");
  const [confidence, setConfidence] = useState(null);
  const [uncertainties, setUncertainties] = useState([]);
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

    try {
      const bundle = toEvidenceDraft(reportId, data);
      // Save ephemeral V2 draft first (backend requires a draft to synthesize against).
      await api.post(`/dr-v2/drafts`, bundle, { signal: controller.signal }).catch(() => null);
      const { data: resp } = await api.post(
        `/dr-v2/ai/synthesize`,
        { report_id: reportId, agents: ["day_narrative"], force },
        { signal: controller.signal },
      );
      if (mySeq !== requestSeqRef.current) return; // stale
      const out = (resp?.outputs || {}).day_narrative || {};
      if (out.ai_available === false) {
        setAiAvailable(false);
        const fb = buildDeterministicFallback(data);
        setNarrative(fb);
        setEdited(fb);
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
    setAccepted(true);
    onAccept?.(text);
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
        <h3 className="text-sm font-semibold text-slate-800">Draft Summary</h3>
        {status === "building" && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-500" data-testid={`${testId}-status`}>
            <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
            building…
          </span>
        )}
        {status === "ready" && !accepted && (
          <span className="ml-2 text-xs text-emerald-700" data-testid={`${testId}-status`}>ready</span>
        )}
        {accepted && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-emerald-700" data-testid={`${testId}-status`}>
            <Check className="w-3 h-3" aria-hidden="true" />accepted
          </span>
        )}
        {!aiAvailable && status !== "building" && (
          <span className="ml-2 text-xs text-slate-500" data-testid={`${testId}-fallback`}>using deterministic summary</span>
        )}
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Grounded in the fields you&apos;ve entered. Never invents facts. Optional — you can accept, edit, regenerate, or ignore.
      </p>

      {status === "idle" && !narrative && (
        <p className="text-sm text-slate-500 italic" data-testid={`${testId}-empty`}>
          Add activities, crew, or notes to see a draft summary here.
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
              <RefreshCw className="w-3 h-3 mr-1" />Regenerate
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={handleClear}
              data-testid={`${testId}-clear`}
            >
              Ignore
            </Button>
          </div>
          {error && (
            <p className="mt-2 text-xs text-slate-500" data-testid={`${testId}-error`}>
              Summary assist unavailable — you can still submit normally.
            </p>
          )}
        </>
      )}
    </div>
  );
}
