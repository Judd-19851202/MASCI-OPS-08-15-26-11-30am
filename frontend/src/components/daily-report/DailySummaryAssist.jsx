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
import { saveDraft } from "@/lib/resiliency/draftStore";
import { getDeviceScopedActorId } from "@/lib/resiliency/actorId";

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

const DEBOUNCE_MS = 1000;
const REQUEST_TIMEOUT_MS = 60000;
const JOB_POLL_MS = 1400;
const JOB_NOT_FOUND_RETRY_WINDOW_MS = 15000;
const buildDeterministicFallback = buildDeterministicSummaryFallback;

const TERMINAL_PHOTO_INTEL_STATUSES = new Set([
  "no_photos",
  "cited",
  "complete",
  "complete_with_observations",
  "complete_with_some_failures",
  "complete_zero_observations",
  "analysis_unavailable",
  "unavailable",
  "suppressed",
]);

function normalizePhotoIntelStatus(rawStatus, totalPhotos) {
  const status = String(rawStatus || "").trim();
  if (totalPhotos > 0 && (!status || status === "no_photos" || status === "not_requested")) {
    return "queued";
  }
  if (status) return status;
  return totalPhotos > 0 ? "queued" : "no_photos";
}

export default function DailySummaryAssist({
  data,
  reportId,
  reportNumber,
  formKey,
  photoUploadState,
  onAccept,
  onPhotoIntelChange,
  onStateChange,
  testId = "daily-summary-assist",
}) {
  const { t } = useT();
  const draftDeviceId = getDeviceScopedActorId();
  const summaryReportId = useMemo(
    () => formKey || reportId || (reportNumber ? `dr-${reportNumber}` : "dr-draft"),
    [formKey, reportId, reportNumber],
  );

  const [status, setStatus] = useState("idle");
  const [narrative, setNarrative] = useState("");
  const [edited, setEdited] = useState("");
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
  const [activeJob, setActiveJob] = useState(null);

  const abortRef = useRef(null);
  const debounceRef = useRef(null);
  const requestSeqRef = useRef(0);
  const dataRef = useRef(data);
  const photoIntelKeyRef = useRef("");
  const photoIntelValueRef = useRef(null);
  const latestPhotoIntelRef = useRef(null);
  const narrativeRef = useRef("");
  const activeJobRef = useRef(null);
  const completedSummaryKeyRef = useRef("");
  const pendingSummaryKeyRef = useRef("");
  const acceptedSummaryKeyRef = useRef("");
  const rerunAfterCurrentJobRef = useRef(false);
  const previousUploadInFlightRef = useRef(false);
  const pendingPostUploadRefreshRef = useRef(false);
  const jobPollRef = useRef(null);

  const visibleSummary = useMemo(() => (edited || narrative || "").trim(), [edited, narrative]);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  useEffect(() => {
    latestPhotoIntelRef.current = latestPhotoIntel;
  }, [latestPhotoIntel]);

  useEffect(() => {
    activeJobRef.current = activeJob;
  }, [activeJob]);

  useEffect(() => {
    onPhotoIntelChange?.(latestPhotoIntel || null);
  }, [latestPhotoIntel, onPhotoIntelChange]);

  useEffect(() => {
    narrativeRef.current = narrative;
  }, [narrative]);

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
  const generalNotes = data?.general_notes;
  const location = data?.location;
  const preparedBy = data?.prepared_by;
  const superintendent = data?.superintendent;

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

  const effectivePhotoIntelStatus = useMemo(
    () => normalizePhotoIntelStatus(latestPhotoIntel?.status || photoIntelStatus || "", photoCount),
    [latestPhotoIntel?.status, photoIntelStatus, photoCount],
  );

  const summaryRequestKey = useMemo(() => JSON.stringify({
    project_number: data?.project_number || "",
    project_name: data?.project_name || "",
    report_date: data?.report_date || "",
    prepared_by: preparedBy || "",
    superintendent: superintendent || "",
    location: location || "",
    weather_summary: weatherSummary || "",
    general_notes: generalNotes || "",
    incident_notes: incidentNotes || "",
    safety_notes: safetyNotes || "",
    tomorrow_plan: tomorrowPlan || "",
    follow_ups: followUps || "",
    activities: activityCardsJson,
    crews: crewsJson,
    equipment: equipmentJson,
    materials: materialsJson,
    constraints: constraintsJson,
    production: productionJson,
    subcontractors: subcontractorsJson,
    photo_signature: compactPhotoSignature,
  }), [
    activityCardsJson,
    compactPhotoSignature,
    constraintsJson,
    crewsJson,
    data?.project_name,
    data?.project_number,
    data?.report_date,
    equipmentJson,
    followUps,
    generalNotes,
    incidentNotes,
    location,
    materialsJson,
    preparedBy,
    productionJson,
    safetyNotes,
    subcontractorsJson,
    superintendent,
    tomorrowPlan,
    weatherSummary,
  ]);

  const missingDetails = useMemo(() => {
    const items = [];
    const hasWorkEvidence = Boolean((data?.production || []).length || (data?.activity_cards || data?.activities || []).length);
    const hasCrewEvidence = Boolean((data?.masci_crews || []).length || (data?.subcontractors || []).length);
    if (!data?.project_name && !data?.project_number) items.push("project identification");
    if (!location) items.push("work location");
    if (!preparedBy && !superintendent) items.push("superintendent or preparer");
    if (!weatherSummary) items.push("weather conditions");
    if (!hasWorkEvidence) items.push("work performed or production quantities");
    if (!hasCrewEvidence) items.push("crew or subcontractor labor");
    if (!(data?.photos || []).length) items.push("photo evidence");
    if (!tomorrowPlan && !followUps) items.push("tomorrow plan or follow-up");
    return items;
  }, [
    data?.activity_cards,
    data?.activities,
    data?.masci_crews,
    data?.photos,
    data?.production,
    data?.project_name,
    data?.project_number,
    data?.subcontractors,
    followUps,
    location,
    preparedBy,
    superintendent,
    tomorrowPlan,
    weatherSummary,
  ]);

  const completenessLabel = useMemo(() => {
    if (photoUploadState?.inFlight || status === "building") return "Updating from new report information";
    if (!hasEnoughEvidence(data)) return "More information needed";
    if (missingDetails.length > 0) return "Summary ready — some details missing";
    return "Summary ready";
  }, [data, missingDetails.length, photoUploadState?.inFlight, status]);

  const completenessTone = useMemo(() => {
    if (photoUploadState?.inFlight || status === "building") return "border-sky-200 bg-sky-50 text-sky-800";
    if (!hasEnoughEvidence(data)) return "border-amber-200 bg-amber-50 text-amber-900";
    if (missingDetails.length > 0) return "border-amber-200 bg-amber-50 text-amber-900";
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }, [data, missingDetails.length, photoUploadState?.inFlight, status]);

  const syncPhotoIntel = useCallback(async ({ force = false } = {}) => {
    const currentData = dataRef.current || {};
    const currentPhotos = currentData?.photos || [];
    if (typeof window !== "undefined") {
      window.__DR_ACTIVE_DRAFT__ = {
        formKey,
        photoCount: currentPhotos.length,
        photos: currentPhotos.map((item, idx) => ({
          idx,
          type: typeof item,
          prefix: typeof item === "string" ? item.slice(0, 40) : JSON.stringify(item || {}).slice(0, 80),
          length: typeof item === "string" ? item.length : 0,
        })),
      };
    }
    if (reportNumber) {
      try {
        const { data: response } = await api.get(
          `/daily-reports/${encodeURIComponent(reportNumber)}/photo-intelligence`,
          { skipSessionStatus: true },
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
      const fallbackStatus = normalizePhotoIntelStatus("", currentPhotos.length);
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
    const cachedStatus = normalizePhotoIntelStatus(photoIntelValueRef.current?.status || "", currentPhotos.length);
    if (!force && photoIntelKeyRef.current === compactPhotoSignature && photoIntelValueRef.current && TERMINAL_PHOTO_INTEL_STATUSES.has(cachedStatus)) {
      return photoIntelValueRef.current;
    }
    const { data: response } = await api.post(
      "/daily-reports/photo-intelligence/draft",
      {
        form_key: formKey,
        payload: currentData,
        force,
      },
      { skipSessionStatus: true },
    );
    photoIntelKeyRef.current = compactPhotoSignature;
    photoIntelValueRef.current = response || null;
    setLatestPhotoIntel(response || null);
    setPhotoIntelStatus(
      normalizePhotoIntelStatus(response?.status || response?.lifecycle_status || "", currentPhotos.length),
    );
    return response || null;
  }, [compactPhotoSignature, formKey, reportNumber]);

  const clearJobPoll = useCallback(() => {
    if (jobPollRef.current) {
      window.clearTimeout(jobPollRef.current);
      jobPollRef.current = null;
    }
  }, []);

  const applyCompletedSummary = useCallback((resp, tElapsed, requestKey, summaryPhotoIntel, payload) => {
    setProviderMasked(null);
    setModelMasked(null);
    setGeneratedAt(new Date().toISOString());
    setLatencyMs(tElapsed);
    setLatestPhotoIntel(summaryPhotoIntel || null);
    const returnedSummaryInput = resp?.summary_input?.photos || null;
    const statusFromPhotoIntel =
      summaryPhotoIntel?.status
      || returnedSummaryInput?.lifecycle_status
      || returnedSummaryInput?.status
      || payload?.summary_input?.photos?.lifecycle_status
      || payload?.summary_input?.photos?.status
      || "no_photos";
    const totalPhotos = Array.isArray(payload?.photos) ? payload.photos.length : ((dataRef.current?.photos || []).length);
    setPhotoIntelStatus(normalizePhotoIntelStatus(statusFromPhotoIntel, totalPhotos));
    setAiAvailable(Boolean(resp?.enabled));
    const text = (resp?.summary_text || "").trim();
    const fb = text || buildDeterministicFallback(dataRef.current, summaryPhotoIntel);
    setNarrative(fb);
    setEdited(fb);
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
    setActiveJob(null);
    completedSummaryKeyRef.current = requestKey;
  }, []);

  const pollSummaryJob = useCallback(async ({ jobId, startedAt, requestKey, payload, mySeq }) => {
    try {
      const { data: state } = await api.get(`/jobs/${encodeURIComponent(jobId)}/status`, {
        skipSessionStatus: true,
      });
      if (mySeq !== requestSeqRef.current) return;
      setActiveJob(state || null);
      if (state?.status === "completed") {
        clearJobPoll();
        const elapsed = Math.round(performance.now() - startedAt);
        const summaryPhotoIntel = state?.result?.photo_intelligence || latestPhotoIntelRef.current || null;
        applyCompletedSummary(state?.result || {}, elapsed, requestKey, summaryPhotoIntel, payload);
        return;
      }
      if (state?.status === "failed") {
        clearJobPoll();
        const fb = buildDeterministicFallback(dataRef.current, latestPhotoIntelRef.current || null);
        if (!narrativeRef.current.trim()) {
          setNarrative(fb);
          setEdited(fb);
        }
        setAiAvailable(false);
        setError(state?.error?.message || "Summary assist is unavailable right now. You can approve the generated summary or write a manual summary.");
        setErrorCode(state?.error?.code || "summary_job_failed");
        setStatus("ready");
        setActiveJob(null);
        completedSummaryKeyRef.current = requestKey;
        return;
      }
      clearJobPoll();
      jobPollRef.current = window.setTimeout(() => {
        pollSummaryJob({ jobId, startedAt, requestKey, payload, mySeq }).catch(() => undefined);
      }, Number(state?.poll_after_ms || JOB_POLL_MS));
    } catch (err) {
      if (mySeq !== requestSeqRef.current) return;
      const transient404 = Number(err?.response?.status || 0) === 404;
      const elapsed = Math.round(performance.now() - startedAt);
      if (transient404 && elapsed <= JOB_NOT_FOUND_RETRY_WINDOW_MS) {
        clearJobPoll();
        jobPollRef.current = window.setTimeout(() => {
          pollSummaryJob({ jobId, startedAt, requestKey, payload, mySeq }).catch(() => undefined);
        }, JOB_POLL_MS);
        return;
      }
      clearJobPoll();
      const normalized = normalizeOperatorError(err, {
        fallbackMessage: "Summary assist is unavailable right now. You can approve the generated summary or write a manual summary.",
      });
      const fb = buildDeterministicFallback(dataRef.current, latestPhotoIntelRef.current || null);
      if (!narrativeRef.current.trim()) {
        setNarrative(fb);
        setEdited(fb);
      }
      setAiAvailable(false);
      setPhotoIntelStatus(
        normalizePhotoIntelStatus(
          latestPhotoIntelRef.current?.status || latestPhotoIntelRef.current?.lifecycle_status || "",
          (dataRef.current?.photos || []).length,
        ),
      );
      setError(normalized.message);
      setErrorCode(normalized.code);
      setStatus("ready");
      setActiveJob(null);
      completedSummaryKeyRef.current = requestKey;
    }
  }, [applyCompletedSummary, clearJobPoll]);

  useEffect(() => {
    if (accepted) return undefined;
    const status = effectivePhotoIntelStatus;
    if (!["queued", "analyzing", "partially_analyzed", "uploading", "processing", "not_requested"].includes(status)) {
      return undefined;
    }
    const timer = setTimeout(async () => {
      try {
        await syncPhotoIntel({ force: false });
      } catch {
        // best effort only
      }
    }, 2200);
    return () => clearTimeout(timer);
  }, [accepted, effectivePhotoIntelStatus, latestPhotoIntel, photoUploadState?.inFlight, syncPhotoIntel]);

  useEffect(() => () => clearJobPoll(), [clearJobPoll]);

  useEffect(() => {
    if (!regenerateCooldownUntil) return undefined;
    const timer = setInterval(() => setCooldownNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, [regenerateCooldownUntil]);

  const synthesize = useCallback(async (force = false, overrideKey = null) => {
    const currentData = dataRef.current || {};
    const requestKey = overrideKey || summaryRequestKey;
    if (!hasEnoughEvidence(currentData) || photoUploadState?.inFlight) {
      setStatus("idle");
      return;
    }
    if (!force && (pendingSummaryKeyRef.current || activeJobRef.current?.job_id)) {
      rerunAfterCurrentJobRef.current = true;
      return;
    }
    if (!force && (pendingSummaryKeyRef.current === requestKey || completedSummaryKeyRef.current === requestKey)) {
      return;
    }
    pendingSummaryKeyRef.current = requestKey;
    if (abortRef.current) {
      try { abortRef.current.abort(); } catch (e) { void e; }
    }
    const controller = new AbortController();
    abortRef.current = controller;
    const mySeq = ++requestSeqRef.current;
    setStatus("building");
    setError(null);
    setActiveJob(null);

    const timeoutId = setTimeout(() => {
      try { controller.abort(); } catch (e) { void e; }
    }, REQUEST_TIMEOUT_MS);
    const tStart = performance.now();

    try {
      if (formKey) {
        try {
          await saveDraft(draftDeviceId, formKey, dataRef.current || {}, { savedByActor: draftDeviceId });
        } catch {
          // best-effort local draft guard
        }
      }
      let photoIntel = null;
      try {
        photoIntel = await syncPhotoIntel({ force });
      } catch {
        photoIntel = null;
      }
      const payload = buildDailyReportSummaryPayload(currentData, photoIntel, { formKey });
      const { data: resp } = await api.post(
        `/daily-reports/summary/draft`,
        { payload, form_key: formKey, force },
        { signal: controller.signal, skipSessionStatus: true },
      );
      if (mySeq !== requestSeqRef.current) return;
      if (resp?.job_id) {
        setActiveJob(resp);
        await pollSummaryJob({ jobId: resp.job_id, startedAt: tStart, requestKey, payload, mySeq });
        return;
      }
      const tElapsed = Math.round(performance.now() - tStart);
      const summaryPhotoIntel = resp?.photo_intelligence || photoIntel;
      applyCompletedSummary(resp, tElapsed, requestKey, summaryPhotoIntel, payload);
    } catch (err) {
      if (mySeq !== requestSeqRef.current) return;
      if (err?.name === "CanceledError" || err?.name === "AbortError") return;
      const normalized = normalizeOperatorError(err, {
        fallbackMessage: "Summary assist is unavailable right now. You can approve the generated summary or write a manual summary.",
      });
      const fb = buildDeterministicFallback(dataRef.current, latestPhotoIntelRef.current || null);
      if (!narrativeRef.current.trim()) {
        setNarrative(fb);
        setEdited(fb);
      }
      setAiAvailable(false);
      setPhotoIntelStatus(
        normalizePhotoIntelStatus(
          latestPhotoIntelRef.current?.status || latestPhotoIntelRef.current?.lifecycle_status || "",
          (dataRef.current?.photos || []).length,
        ),
      );
      setError(normalized.message);
      setErrorCode(normalized.code);
      setStatus("ready");
      setActiveJob(null);
      completedSummaryKeyRef.current = requestKey;
    } finally {
      pendingSummaryKeyRef.current = "";
      clearTimeout(timeoutId);
    }
  }, [applyCompletedSummary, draftDeviceId, formKey, photoUploadState?.inFlight, pollSummaryJob, summaryRequestKey, syncPhotoIntel]);

  const queueSynthesis = useCallback((force = false, debounceMs = DEBOUNCE_MS) => {
    if (acceptedSummaryKeyRef.current && acceptedSummaryKeyRef.current !== summaryRequestKey) {
      acceptedSummaryKeyRef.current = "";
      setAccepted(false);
      setDecision("pending");
      onAccept?.("", null);
    }
    if (photoUploadState?.inFlight) {
      setStatus("building");
      return;
    }
    if (!force && (pendingSummaryKeyRef.current || activeJobRef.current?.job_id)) {
      rerunAfterCurrentJobRef.current = true;
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      synthesize(force, summaryRequestKey);
    }, debounceMs);
  }, [onAccept, photoUploadState?.inFlight, summaryRequestKey, synthesize]);

  useEffect(() => {
    if (accepted || status === "building" || activeJob?.job_id || !rerunAfterCurrentJobRef.current) {
      return;
    }
    rerunAfterCurrentJobRef.current = false;
    queueSynthesis(false, 150);
  }, [accepted, activeJob?.job_id, queueSynthesis, status, summaryRequestKey]);

  useEffect(() => {
    if (accepted) return undefined;
    if (!formKey || photoCount === 0 || reportNumber) {
      if (photoCount === 0) setPhotoIntelStatus("no_photos");
      return undefined;
    }
    setPhotoIntelStatus((prev) => (prev === "no_photos" ? "queued" : prev));
    const timer = setTimeout(() => {
      syncPhotoIntel({ force: false }).catch(() => undefined);
    }, 50);
    return () => clearTimeout(timer);
  }, [accepted, formKey, photoCount, reportNumber, compactPhotoSignature, syncPhotoIntel]);

  useEffect(() => {
    if (accepted && acceptedSummaryKeyRef.current === summaryRequestKey) return undefined;
    queueSynthesis(false, DEBOUNCE_MS);
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
    queueSynthesis,
    summaryRequestKey,
  ]);

  useEffect(() => {
    const wasUploading = previousUploadInFlightRef.current;
    const isUploading = Boolean(photoUploadState?.inFlight);
    const completedUploads = Number(photoUploadState?.completed || 0);
    if (!wasUploading && isUploading) {
      pendingPostUploadRefreshRef.current = true;
    }
    if (wasUploading && !isUploading && !accepted) {
      pendingPostUploadRefreshRef.current = true;
    }
    if (!isUploading && !accepted && pendingPostUploadRefreshRef.current && photoCount > 0) {
      setPhotoIntelStatus((prev) => (prev === "no_photos" ? "queued" : prev));
      queueSynthesis(false, 150);
      pendingPostUploadRefreshRef.current = false;
    }
    if (isUploading && completedUploads > 0 && photoCount > 0 && formKey && !accepted) {
      syncPhotoIntel({ force: false }).catch(() => undefined);
    }
    previousUploadInFlightRef.current = isUploading;
  }, [accepted, formKey, photoCount, photoUploadState?.completed, photoUploadState?.inFlight, queueSynthesis, syncPhotoIntel]);

  useEffect(() => {
    const frozen = (data?.ai_accepted_summary || "").trim();
    const meta = data?.ai_accepted_summary_meta || {};
    if (!frozen) return;
    setAccepted(true);
    setEdited(frozen);
    setDecision(meta?.source === "manual" ? "manual_accepted" : "ai_accepted");
    acceptedSummaryKeyRef.current = String(meta?.report_state_signature || summaryRequestKey || "");
  }, [data?.ai_accepted_summary, data?.ai_accepted_summary_meta, summaryRequestKey]);

  useEffect(() => {
    const hasFrozen = !!(data?.ai_accepted_summary || "").trim();
    onStateChange?.({
      decision,
      accepted,
      hasFrozen,
      manualNeeded: decision === "manual_required",
      manualReady: decision === "manual_required" && !!edited.trim(),
      canSubmit: hasFrozen && (!acceptedSummaryKeyRef.current || acceptedSummaryKeyRef.current === summaryRequestKey),
    });
  }, [accepted, data?.ai_accepted_summary, decision, edited, onStateChange, summaryRequestKey]);

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
      evidence_refs: evidenceRefs,
      latency_ms: latencyMs,
      report_state_signature: summaryRequestKey,
      report_identity: {
        report_id: summaryReportId || "",
        report_number: data?.report_number || reportNumber || "",
        report_instance: data?.report_instance || "primary",
      },
      photo_intelligence_status: effectivePhotoIntelStatus,
      photo_observations: Array.isArray(latestPhotoIntel?.observations) ? latestPhotoIntel.observations.slice(0, 60) : [],
      error_code: errorCode,
    };
    setAccepted(true);
    setDecision("ai_accepted");
    acceptedSummaryKeyRef.current = summaryRequestKey;
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
    const terminalFailures = Number(intel.terminal_failures || 0) + Number(intel.unavailable || 0);
    const state = normalizePhotoIntelStatus(effectivePhotoIntelStatus, total || photoCount || 0);
    const activeDetails = activeJob?.details || {};
    const activeTotal = Number(activeDetails?.total_photos || total || 0);
    const activeCited = Number(activeDetails?.cited_photos || 0);
    if (status === "building" && activeJob?.job_id && activeTotal > 0) {
      return `AI is citing ${Math.min(activeCited, activeTotal)} of ${activeTotal} photos...`;
    }
    if (photoUploadState?.inFlight) {
      const totalUploads = Number(photoUploadState?.total || total || 0);
      const completed = Number(photoUploadState?.completed || 0);
      return completed > 0
        ? `Uploading ${completed} of ${totalUploads} photos — pre-warming AI now...`
        : `Uploading ${completed} of ${totalUploads} photos…`;
    }
    if (state === "no_photos") return "No photos attached yet.";
    if (state === "uploading") return `Uploading ${total} photos…`;
    if (state === "queued") return `Queued ${total} photos for analysis.`;
    if (state === "analyzing") return `Analyzing ${reviewed} of ${total} photos…`;
    if (state === "partially_analyzed") return `Analyzed ${reviewed} of ${total} photos so far.`;
    if (state === "cited") return `Photo analysis complete — ${reviewed || total} photos reviewed.`;
    if (state === "complete") return `Photo analysis complete — ${total} photos reviewed.`;
    if (state === "complete_with_some_failures") return `${reviewed} of ${total} photos analyzed — ${terminalFailures} could not be processed.`;
    if (state === "complete_with_observations") return `Photo analysis complete — ${total} photos reviewed.`;
    return "Photo analysis unavailable — your report data is safe.";
  }, [activeJob, effectivePhotoIntelStatus, latestPhotoIntel, photoCount, photoUploadState, status]);

  const showSummaryError = Boolean(error && !visibleSummary);
  const showInlineSummaryNotice = Boolean(error && visibleSummary);

  const cooldownSeconds = Math.max(0, Math.ceil((regenerateCooldownUntil - cooldownNow) / 1000));

  function handleRejectToManual() {
    setAccepted(false);
    setDecision("manual_required");
    onAccept?.("", null);
  }

  function handleClearApprovedSummary() {
    acceptedSummaryKeyRef.current = "";
    setAccepted(false);
    setDecision("pending");
    setEdited("");
    setNarrative("");
    setUncertainties([]);
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
      evidence_refs: [],
      latency_ms: null,
      report_state_signature: summaryRequestKey,
      report_identity: {
        report_id: summaryReportId || "",
        report_number: data?.report_number || reportNumber || "",
        report_instance: data?.report_instance || "primary",
      },
      photo_intelligence_status: effectivePhotoIntelStatus,
      photo_observations: Array.isArray(latestPhotoIntel?.observations) ? latestPhotoIntel.observations.slice(0, 60) : [],
      error_code: errorCode,
    };
    setAccepted(true);
    setDecision("manual_accepted");
    acceptedSummaryKeyRef.current = summaryRequestKey;
    onAccept?.(text, meta);
  }

  return (
    <div data-testid={testId} className={`elite-glass-panel rounded-[1.2rem] border border-white/60 p-4 ${status === "building" ? "elite-processing-glow" : ""}`}>
      <div className="mb-2 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-slate-600" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-slate-800">{t("Draft Summary")}</h3>
        {status === "building" && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-500" data-testid={`${testId}-status`}>
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
            {(activeJob?.message || ((data?.photos || []).length > 0 ? t("analyzing photos & writing summary…") : t("writing summary…")))}
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

      <div
        className={`mb-3 rounded-lg border px-3 py-2 text-xs font-semibold backdrop-blur-sm ${completenessTone}`}
        data-testid={`${testId}-completeness-state`}
      >
        {completenessLabel}
      </div>

      <p className="mb-3 text-xs text-slate-500">
        {t("Grounded in the fields you've entered. Before submit, you must accept the AI summary, regenerate and then accept it, or reject it and approve a manual summary.")}
      </p>

      <div className="mb-3 rounded-lg border border-white/60 bg-white/60 p-3 text-xs text-slate-700 backdrop-blur-sm" data-testid={`${testId}-gate-note`}>
        {decision === "manual_required"
          ? t("AI summary rejected. Write the final supervisor summary below, then approve it to unlock submit.")
          : accepted
            ? t("Summary locked for submission. If you change it, you must approve it again.")
            : t("Submission is blocked until one approved executive summary exists.")}
      </div>

      <div
        className="mb-3 rounded-lg border border-white/60 bg-white/60 p-3 text-xs text-slate-700 backdrop-blur-sm"
        data-testid={`${testId}-photo-status`}
      >
        {operatorPhotoStatus}
      </div>

      {missingDetails.length > 0 && (
        <div
          className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"
          data-testid={`${testId}-missing-details`}
        >
          <div className="font-semibold">Missing report details</div>
          <ul className="mt-1 list-disc pl-4">
            {missingDetails.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}

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
            className="min-h-[110px] text-sm leading-[1.65]"
            placeholder={status === "building" ? "Building…" : ""}
            disabled={status === "building" && !narrative}
          />

          {uncertainties.length > 0 && (
            <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-3" data-testid={`${testId}-uncertainties`}>
              <div className="mb-1 text-xs font-semibold text-slate-800">Summary notes</div>
              <ul className="list-disc pl-4 text-xs text-slate-700">
                {uncertainties.map((u, i) => <li key={i}>{u}</li>)}
              </ul>
            </div>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="default"
              onClick={handleAccept}
              disabled={!visibleSummary || accepted || decision === "manual_required"}
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
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={handleClearApprovedSummary}
              data-testid={`${testId}-clear`}
            >
              {t("Clear draft summary")}
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
                className="min-h-[130px] bg-white text-sm leading-[1.65]"
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

          {showInlineSummaryNotice && (
            <div
              className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"
              data-testid={`${testId}-notice`}
              role="status"
            >
              <div className="mb-0.5 font-semibold">{t("Summary assist unavailable right now")}</div>
              <div>{t("The visible summary is still available to approve. You can also regenerate after cooldown or switch to a manual summary.")}</div>
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