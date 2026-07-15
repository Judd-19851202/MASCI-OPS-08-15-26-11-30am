import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { buildDailyReportSummaryPayload, buildDeterministicSummaryFallback } from "@/lib/dailyReportSummaryPayload";
import { useT } from "@/lib/i18n";
import { normalizeOperatorError } from "@/lib/operatorError";

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
  reportId,
  reportNumber,
  formKey,
  onAccept,
  onStateChange,
  testId = "daily-summary-assist",
}) {
  const { t } = useT();
  const summaryReportId = useMemo(
    () => formKey || reportId || (reportNumber ? `dr-${reportNumber}` : "dr-draft"),
    [formKey, reportId, reportNumber],
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
  const [errorCode, setErrorCode] = useState(null);
  const [decision, setDecision] = useState("pending");
  const [photoIntelStatus, setPhotoIntelStatus] = useState("no_photos");
  const [latestPhotoIntel, setLatestPhotoIntel] = useState(null);
  const [regenerateCooldownUntil, setRegenerateCooldownUntil] = useState(0);
  const [cooldownNow, setCooldownNow] = useState(Date.now());

  const abortRef = useRef(null);
  const debounceRef = useRef(null);
  const requestSeqRef = useRef(0);
  const dataRef = useRef(data);
  const photoIntelKeyRef = useRef("");
  const photoIntelValueRef = useRef(null);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  const activityCardsJson = useMemo(() => JSON.stringify(data?.activity_cards || data?.activities || []), [data?.activity_cards, data?.activities]);
  const crewsJson = useMemo(() => JSON.stringify(data?.masci_crews || []), [data?.masci_crews]);
  const equipmentJson = useMemo(() => JSON.stringify(data?.equipment_used || data?.equipment || []), [data?.equipment_used, data?.equipment]);
  const materialsJson = useMemo(() => JSON.stringify((data?.materials || []).map((m) => ({ ...m, ticket_photos: (m?.ticket_photos || []).length }))), [data?.materials]);
  const constraintsJson = useMemo(() => JSON.stringify(data?.constraint_cards || data?.constraints || data?.delays || []), [data?.constraint_cards, data?.constraints, data?.delays]);
  const productionJson = useMemo(() => JSON.stringify(data?.production || []), [data?.production]);
  const subcontractorsJson = useMemo(() => JSON.stringify(data?.subcontractors || []), [data?.subcontractors]);
  const photoCount = (data?.photos || []).length;
  const tomorrowPlan = (data?.narrative_sections || {}).tomorrow_plan;
  const followUps = (data?.narrative_sections || {}).follow_ups;
  const safetyNotes = data?.safety_quality?.notes;
  const incidentNotes = data?.incident_notes;
  const weatherSummary = data?.weather_summary;

  const compactPhotoSignature = useMemo(() => {
    const sig = [];
    const digest = (entry, idx, prefix) => {
      if (typeof entry === "string") {
        sig.push(`${prefix}${idx}:${entry.length}:${entry.slice(0, 40)}`);
        return;
      }
      if (entry && typeof entry === "object") {
        const raw = entry.dataUrl || entry.data_url || entry.data || entry.base64 || entry.ref || entry.url || entry.key || "";
        sig.push(`${prefix}${idx}:${String(raw).length}:${String(raw).slice(0, 40)}`);
      }
    };
    (data?.photos || []).forEach((entry, idx) => digest(entry, idx, "p"));
    (data?.materials || []).forEach((row, rowIdx) => {
      (row?.ticket_photos || []).forEach((entry, idx) => digest(entry, `${rowIdx}-${idx}`, "m"));
    });
    (data?.subcontractors || []).forEach((row, rowIdx) => {
      (row?.photos || []).forEach((entry, idx) => digest(entry, `${rowIdx}-${idx}`, "s"));
    });
    return `${formKey || ""}::${sig.join("|")}`;
  }, [data?.photos, data?.materials, data?.subcontractors, formKey]);

  const syncPhotoIntel = useCallback(async ({ force = false } = {}) => {
    const currentData = dataRef.current || {};
    const currentPhotos = currentData?.photos || [];
    if (reportNumber) {
      try {
        const { data: response } = await api.get(
          `/daily-reports/${encodeURIComponent(reportNumber)}/photo-intelligence`,
        );
        photoIntelValueRef.current = response || null;
        setLatestPhotoIntel(response || null);
        setPhotoIntelStatus(response?.status || (currentPhotos.length > 0 ? "queued" : "no_photos"));
        return response || null;
      } catch {
        return null;
      }
    }
    if (!formKey) {
      const fallbackStatus = currentPhotos.length > 0 ? "queued" : "no_photos";
      setPhotoIntelStatus(fallbackStatus);
      return null;
    }
    if (currentPhotos.length === 0) {
      photoIntelKeyRef.current = compactPhotoSignature;
      photoIntelValueRef.current = {
        photo_count: 0,
        analyzed: 0,
        pending: 0,
        queued: 0,
        processing: 0,
        failed: 0,
        observations: [],
        status: "no_photos",
        lifecycle_status: "no_photos",
      };
      setPhotoIntelStatus("no_photos");
      setLatestPhotoIntel(photoIntelValueRef.current);
      return photoIntelValueRef.current;
    }
    if (!force && photoIntelKeyRef.current === compactPhotoSignature && photoIntelValueRef.current) {
      return photoIntelValueRef.current;
    }
    const { data: response } = await api.post("/daily-reports/photo-intelligence/draft", {
      form_key: formKey,
      payload: currentData,
      force,
    });
    photoIntelKeyRef.current = compactPhotoSignature;
    photoIntelValueRef.current = response || null;
    setLatestPhotoIntel(response || null);
    setPhotoIntelStatus(response?.status || (currentPhotos.length > 0 ? "queued" : "no_photos"));
    return response || null;
  }, [compactPhotoSignature, formKey, reportNumber]);

  useEffect(() => {
    if (!regenerateCooldownUntil) return undefined;
    const timer = setInterval(() => setCooldownNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, [regenerateCooldownUntil]);

  const synthesize = useCallback(async (force = false) => {
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
      let photoIntel = null;
      try {
        photoIntel = await syncPhotoIntel({ force });
      } catch {
        photoIntel = null;
      }
      const payload = buildDailyReportSummaryPayload(dataRef.current, photoIntel, { formKey });
      const { data: resp } = await api.post(
        `/daily-reports/summary/draft`,
        { payload, form_key: formKey, force },
        { signal: controller.signal },
      );
      const tElapsed = Math.round(performance.now() - tStart);
      if (mySeq !== requestSeqRef.current) return;
      setProviderMasked(null);
      setModelMasked(null);
      setGeneratedAt(new Date().toISOString());
      setLatencyMs(tElapsed);

      const summaryPhotoIntel = resp?.photo_intelligence || photoIntel;
      setLatestPhotoIntel(summaryPhotoIntel || null);
      const returnedSummaryInput = resp?.summary_input?.photos || null;
      const statusFromPhotoIntel =
        summaryPhotoIntel?.status
        || returnedSummaryInput?.lifecycle_status
        || returnedSummaryInput?.status
        || payload.summary_input?.photos?.lifecycle_status
        || payload.summary_input?.photos?.status
        || "no_photos";
      setPhotoIntelStatus(statusFromPhotoIntel);
      setAiAvailable(Boolean(resp?.enabled));
      const text = (resp?.summary_text || "").trim();
      const fb = text || buildDeterministicSummaryFallback(dataRef.current, summaryPhotoIntel);
      setNarrative(fb);
      setEdited(fb);
      setConfidence(typeof resp?.confidence === "number" ? resp.confidence : null);
      const notes = [];
      if (summaryPhotoIntel?.classification) notes.push(summaryPhotoIntel.classification);
      if (!resp?.enabled && resp?.provider_state?.code) {
        notes.push("Summary generated from typed report facts while live assist is unavailable.");
      }
      if (Array.isArray(resp?.warnings)) {
        resp.warnings.forEach((item) => {
          if (typeof item === "string" && item.trim()) notes.push(item.trim());
        });
      }
      setUncertainties([...new Set(notes)].slice(0, 5));
      setEvidenceRefs(Array.isArray(resp?.evidence_refs) ? resp.evidence_refs.slice(0, 20) : []);
      setError(null);
      setErrorCode(null);
      setStatus("ready");
    } catch (err) {
      if (mySeq !== requestSeqRef.current) return;
      if (err?.name === "CanceledError" || err?.name === "AbortError") return;
      const normalized = normalizeOperatorError(err, {
        fallbackMessage: "Summary assist is unavailable right now. You can approve the generated summary or write a manual summary.",
      });
      const fb = buildDeterministicSummaryFallback(dataRef.current, latestPhotoIntel || null);
      if (!narrative.trim()) {
        setNarrative(fb);
        setEdited(fb);
      }
      setAiAvailable(false);
      setPhotoIntelStatus((latestPhotoIntel?.status) || ((data?.photos || []).length > 0 ? "queued" : "no_photos"));
      setError(normalized.message);
      setErrorCode(normalized.code);
      setStatus("ready");
    } finally {
      clearTimeout(timeoutId);
    }
  }, [data, formKey, latestPhotoIntel?.status, narrative, syncPhotoIntel]);

  useEffect(() => {
    if (accepted) return undefined;
    if (!formKey || photoCount === 0 || reportNumber) {
      if (photoCount === 0) setPhotoIntelStatus("no_photos");
      return undefined;
    }
    const timer = setTimeout(() => {
      syncPhotoIntel({ force: false }).catch(() => undefined);
    }, 450);
    return () => clearTimeout(timer);
  }, [accepted, formKey, photoCount, reportNumber, compactPhotoSignature, syncPhotoIntel]);

  useEffect(() => {
    if (accepted) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { synthesize(false); }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [
    activityCardsJson,
    crewsJson,
    equipmentJson,
    materialsJson,
    constraintsJson,
    productionJson,
    subcontractorsJson,
    photoCount,
    compactPhotoSignature,
    tomorrowPlan,
    followUps,
    safetyNotes,
    incidentNotes,
    weatherSummary,
    accepted,
    synthesize,
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
      accepted_by: data?.prepared_by || data?.superintendent || "",
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
      report_identity: {
        report_id: summaryReportId || "",
        report_number: data?.report_number || reportNumber || "",
        report_instance: data?.report_instance || "primary",
      },
      photo_intelligence_status: photoIntelStatus,
      photo_observations: Array.isArray(latestPhotoIntel?.observations) ? latestPhotoIntel.observations.slice(0, 60) : [],
      error_code: errorCode,
    };
    setAccepted(true);
    setDecision("ai_accepted");
    onAccept?.(text, meta);
  }

  function handleRegenerate() {
    if (Date.now() < regenerateCooldownUntil) return;
    setAccepted(false);
    setDecision("pending");
    onAccept?.("", null);
    setRegenerateCooldownUntil(Date.now() + 3000);
    synthesize(true);
  }

  const operatorPhotoStatus = useMemo(() => {
    const intel = latestPhotoIntel || {};
    const total = Number(intel.photo_count || photoCount || 0);
    const reviewed = Number(intel.reviewed || intel.analyzed || 0);
    const queued = Number(intel.queued || 0);
    const processing = Number(intel.processing || 0);
    const terminalFailures = Number(intel.terminal_failures || 0) + Number(intel.unavailable || 0);
    const state = String(photoIntelStatus || "no_photos");
    if (state === "no_photos") return "No photos attached yet.";
    if (state === "uploading") return `Uploading ${total} photos…`;
    if (state === "queued") return `Queued ${total} photos for analysis.`;
    if (state === "analyzing") return `Analyzing ${reviewed} of ${total} photos…`;
    if (state === "partially_analyzed") return `Analyzed ${reviewed} of ${total} photos so far.`;
    if (state === "complete") return `Photo analysis complete — ${total} photos reviewed.`;
    if (state === "complete_with_some_failures") return `${reviewed} of ${total} photos analyzed — ${terminalFailures} could not be processed.`;
    if (state === "complete_with_observations") return `Photo analysis complete — ${total} photos reviewed.`;
    return "Photo analysis unavailable — your report data is safe.";
  }, [latestPhotoIntel, photoCount, photoIntelStatus]);

  const showSummaryError = Boolean(error && !(edited || narrative || "").trim());

  const cooldownSeconds = Math.max(0, Math.ceil((regenerateCooldownUntil - cooldownNow) / 1000));

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
      accepted_by: data?.prepared_by || data?.superintendent || "",
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
      report_identity: {
        report_id: summaryReportId || "",
        report_number: data?.report_number || reportNumber || "",
        report_instance: data?.report_instance || "primary",
      },
      photo_intelligence_status: photoIntelStatus,
      photo_observations: Array.isArray(latestPhotoIntel?.observations) ? latestPhotoIntel.observations.slice(0, 60) : [],
      error_code: errorCode,
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

      <div
        className="mb-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600"
        data-testid={`${testId}-photo-status`}
      >
        {operatorPhotoStatus}
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
              {accepted && decision === "ai_accepted" ? t("Accepted") : !aiAvailable ? t("Accept generated summary") : t("Accept AI summary")}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleRegenerate}
              disabled={status === "building" || cooldownSeconds > 0}
              data-testid={`${testId}-regenerate`}
            >
              <RefreshCw className="mr-1 h-3 w-3" />{cooldownSeconds > 0 ? `${t("Regenerate")} (${cooldownSeconds}s)` : t("Regenerate")}
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

          {showSummaryError && (
            <div
              className="mt-3 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800"
              data-testid={`${testId}-error`}
              role="alert"
            >
              <div className="mb-0.5 font-semibold">{t("Summary assist unavailable")}</div>
              <div className="text-rose-700" data-code={errorCode || "summary_unavailable"}>{error}</div>
              <div className="mt-1 text-rose-600/80">
                {t("Submission still requires an approved summary. You can keep the last valid summary, try Regenerate after cooldown, or reject AI and approve a manual summary.")}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}