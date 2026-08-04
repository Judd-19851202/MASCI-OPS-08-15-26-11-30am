// TRACK 23.1 · V3 Daily Report page shell.
// TRACK 23.3 · Field resiliency + smart prefill wired in.
//
// Elite, field-first replacement for `NewDailyReport.jsx`. Composes
// the 9 section components and the same shared resiliency stack V1
// uses (`useFormDraft`, `enqueueUpload`, `mintIdempotencyKey`,
// `saveCrewSetup` / `loadCrewSetup`, `markPriorUsage`). Submits via
// the same canonical endpoint (`POST /api/daily-reports`) with the
// same payload contract — so PM/ODS/Trust Spine/email/PDF continue
// to work byte-identically.
//
// DR-03 canonical shell. AppRoutes now sends all Daily Report creation
// traffic to `/daily/submit`, which renders this component only.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { buildDailyReportDefaults } from "@/lib/dailyReportSchema";
import { reverseGeocode } from "@/lib/geolocation";
import { fetchDailyWeather } from "@/lib/weather";
import {
  useFormDraft,
  persistIdempotencyKey,
  loadIdempotencyKey,
  mintIdempotencyKey,
  enqueueUpload,
  onQueueItemSettled,
  useOnlineStatus,
  DraftStatusPill,
  DraftRestorePrompt,
  DraftRecoveryNotice,
  recoverArchivedDraft,
  findDraftEntriesForBase,
  discardDraft as discardStoredDraft,
  emitDraftEvent,
  DAILY_REPORT_FORM_BASE,
  buildDailyReportInstanceScope,
  buildDailyReportScopedFormKey,
} from "@/lib/resiliency";
import DraftScopeChip from "@/lib/resiliency/DraftScopeChip";
import { getDeviceId } from "@/lib/resiliency/deviceId";
import { getDeviceScopedActorId } from "@/lib/resiliency";
import {
  extractSetupSnapshot, saveCrewSetup, loadCrewSetup, applySetupSnapshotToData,
  refreshCrewFromEmployeeMaster,
  isProjectChange,
} from "@/lib/crewMemory";
import { SectionProjectConditions } from "@/components/daily-report-v3/SectionProjectConditions";
import {
  SectionCrewEquipment,
  SectionWorkProduction,
  SectionMaterials,
  SectionPhotos,
  SectionImpactSafety,
  SectionTomorrow,
  SectionAiSummary,
  SectionSignoff,
} from "@/components/daily-report-v3/sections";
import DailyReportV3ExcavationSection from "@/components/daily-report-v3/DailyReportV3ExcavationSection";
import { History } from "lucide-react";
import { useT } from "@/lib/i18n";
import { hasAnyPortalAuthToken } from "@/lib/authHeaders";
import FormShell from "@/components/FormShell";
import { Button } from "@/components/ui/button";
import { translateDrV3PayloadEsToEn } from "@/lib/drV3Translation";
import { useRememberedFormValue } from "@/lib/useRememberedFilter";
import { classifyApiError } from "@/lib/errorClassification";
import { publishSessionStatus } from "@/lib/sessionStatusBus";

const GEO_TIMEOUT_MS = 12000;
const GEO_MAX_AGE_MS = 30000;
const LEGACY_DRAFT_PREFIXES = ["daily-report-new", "daily-report"];

function detectEmbeddedPreviewRestriction() {
  try {
    const previewSuffix = ["preview", "emergentagent", "com"].join(".");
    const hostname = String(window.location.hostname || "").toLowerCase();
    const isManagedNonProductionHost = hostname === previewSuffix || hostname.endsWith(`.${previewSuffix}`);
    return window.self !== window.top && isManagedNonProductionHost;
  } catch {
    return true;
  }
}

function classifyGeolocationFailure(err, isEmbeddedPreview = false) {
  const msg = String(err?.message || "").toLowerCase();
  if (isEmbeddedPreview && (msg.includes("permissions policy") || msg.includes("permission denied") || err?.code === 1)) {
    return "PREVIEW_IFRAME_PERMISSION_BLOCK";
  }
  if (!("geolocation" in navigator)) return "GEOLOCATION_API_UNAVAILABLE";
  if (!window.isSecureContext) return "INSECURE_CONTEXT";
  if (err?.code === 1) return msg.includes("dismiss") ? "PERMISSION_PROMPT_DISMISSED" : "PERMISSION_DENIED";
  if (err?.code === 2) return "POSITION_UNAVAILABLE";
  if (err?.code === 3) return "LOCATION_TIMEOUT";
  if (msg.includes("permissions policy") || msg.includes("policy")) return "BROWSER_POLICY_RESTRICTION";
  return "UNKNOWN";
}

function operatorGpsMessage(code, t) {
  switch (code) {
    case "PERMISSION_DENIED":
      return t("Location permission is blocked. Allow location access for this site in your browser settings, then try again.");
    case "PERMISSION_PROMPT_DISMISSED":
      return t("Location permission was not completed. Tap Use My Location and approve the browser prompt.");
    case "LOCATION_TIMEOUT":
      return t("Your location could not be captured in time. Move to an open area or improve signal, then retry.");
    case "POSITION_UNAVAILABLE":
      return t("Your device could not determine its location. Check Location Services and cellular/Wi-Fi availability.");
    case "PREVIEW_IFRAME_PERMISSION_BLOCK":
      return t("Location access is blocked inside the embedded non-production frame. Open this page in a new tab to test GPS.");
    case "GEOLOCATION_API_UNAVAILABLE":
      return t("This browser does not support device location. Select the project location or enter coordinates manually.");
    case "INSECURE_CONTEXT":
      return t("This page is not running in a secure HTTPS context, so device location is unavailable.");
    default:
      return t("Location could not be captured. You can use project coordinates, a saved draft location, or enter coordinates manually.");
  }
}

function buildLocationPatch({ latitude, longitude, accuracy, capturedAt, locationSource, permissionStatus, captureResult, captureOrigin }) {
  return {
    gps_lat: latitude,
    gps_lng: longitude,
    gps_accuracy: accuracy,
    location_captured_at: capturedAt,
    location_source: locationSource,
    location_permission_status: permissionStatus,
    location_capture_result: captureResult,
    location_capture_origin: captureOrigin,
    location_error_code: "",
    location_error_message: "",
  };
}

function formatDailyReportNumberPreview(nextNumber) {
  if (nextNumber === null || nextNumber === undefined || nextNumber === "") return "";
  return `Report #${String(nextNumber).trim()}`;
}

export default function NewDailyReportV3({ publicMode = false }) {
  const navigate = useNavigate();
  const { t, lang } = useT();
  const [lastProject, rememberLastProject] = useRememberedFormValue(
    "NewDailyReport.last_project_number",
    "",
  );
  const [data, setData] = useState(() => {
    const defaults = buildDailyReportDefaults();
    if (!publicMode && lastProject && !defaults.project_number) defaults.project_number = lastProject;
    if (!defaults.report_instance) defaults.report_instance = "primary";
    return defaults;
  });
  const [reportId, setReportId] = useState("");
  const [saving, setSaving] = useState(false);
  const [isFetchingGps, setFetchingGps] = useState(false);
  const [isFetchingWeather, setFetchingWeather] = useState(false);
  const [costCodes, setCostCodes] = useState([]);
  const [projectCostAssignments, setProjectCostAssignments] = useState([]);
  const [projectCostProgress, setProjectCostProgress] = useState(null);
  const [reportNumberPreview, setReportNumberPreview] = useState("");
  const [crewSetupOffer, setCrewSetupOffer] = useState(null);
  const [smartPrefillOffer, setSmartPrefillOffer] = useState(null);
  const [smartPrefillLoadedKey, setSmartPrefillLoadedKey] = useState("");
  const [smartPrefillError, setSmartPrefillError] = useState("");
  const [smartPrefillFailureKind, setSmartPrefillFailureKind] = useState("");
  const [smartPrefillLoading, setSmartPrefillLoading] = useState(false);
  const [smartPrefillRetryNonce, setSmartPrefillRetryNonce] = useState(0);
  const [prefillNotice, setPrefillNotice] = useState(null);
  const [archivedDraft, setArchivedDraft] = useState(null);
  const [fallbackDraftOffer, setFallbackDraftOffer] = useState(null);
  const [summaryGate, setSummaryGate] = useState({ canSubmit: false, manualNeeded: false });
  const [photoBatchState, setPhotoBatchState] = useState({
    inFlight: false,
    total: 0,
    completed: 0,
    failed: 0,
    phase: "idle",
  });
  const [photoWarmHint, setPhotoWarmHint] = useState(null);
  const [photoIntelStatusState, setPhotoIntelStatusState] = useState(null);
  const idempotencyKeyRef = useRef(null);
  const submitRetryRef = useRef(() => {});
  const deviceId = getDeviceScopedActorId();
  const draftScope = useMemo(() => buildDailyReportInstanceScope(data), [data]);
  const scopedFormKey = useMemo(() => buildDailyReportScopedFormKey(data), [data]);

  const patch = useCallback((delta) => {
    setData((prev) => ({ ...prev, ...delta }));
  }, []);

  const {
    pendingDraft, pendingSavedAt, pendingIsCrossToken, loaded: draftLoaded,
    draftStatus, restore: restoreDraft, discard: discardDraft,
    lastSavedAt,
    commit: commitDraft,
  } = useFormDraft(DAILY_REPORT_FORM_BASE, data, deviceId, {
    scope: draftScope,
    publicAnonymous: true,
  });
  const online = useOnlineStatus();
  const preferFallbackDraft = useMemo(() => {
    if (!fallbackDraftOffer?.form) return false;
    if (!pendingDraft) return true;
    const pendingProject = String(pendingDraft?.project_number || "").trim();
    return !pendingProject;
  }, [fallbackDraftOffer, pendingDraft]);

  // Idempotency key: load once from IDB (survives reload) or mint fresh.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let key = await loadIdempotencyKey(scopedFormKey);
      if (!key) {
        key = mintIdempotencyKey();
        await persistIdempotencyKey(scopedFormKey, key);
      }
      if (!cancelled) idempotencyKeyRef.current = key;
    })();
    return () => {
      cancelled = true;
    };
  }, [scopedFormKey]);

  useEffect(() => {
    if (!draftLoaded) return undefined;
    if (pendingDraft) {
      setArchivedDraft(null);
      setFallbackDraftOffer(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const arc = await recoverArchivedDraft(getDeviceScopedActorId(), scopedFormKey);
        if (!cancelled && arc?.form) setArchivedDraft(arc);
      } catch {
        // ignore
      }
    })();
    return () => { cancelled = true; };
  }, [draftLoaded, pendingDraft, scopedFormKey]);

  useEffect(() => {
    if (!draftLoaded || pendingDraft) return undefined;
    const isUnscopedPrelude = !(data.project_number || "").trim();
    if (!isUnscopedPrelude) {
      setFallbackDraftOffer(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const matches = await findDraftEntriesForBase(getDeviceScopedActorId(), DAILY_REPORT_FORM_BASE, {
          excludeFormKey: scopedFormKey,
          limit: 4,
          filter: ({ form }) => (
            String(form?.report_date || "") === String(data.report_date || "")
            && String(form?.report_instance || "primary") === String(data.report_instance || "primary")
          ),
        });
        if (!cancelled) setFallbackDraftOffer(matches[0] || null);
      } catch {
        if (!cancelled) setFallbackDraftOffer(null);
      }
    })();
    return () => { cancelled = true; };
  }, [draftLoaded, pendingDraft, scopedFormKey, data.project_number, data.report_date, data.report_instance]);

  const onRecoverArchive = useCallback(() => {
    if (!archivedDraft?.form) return;
    setData(archivedDraft.form);
    setArchivedDraft(null);
    toast.success(t("Draft restored"));
  }, [archivedDraft, t]);

  // ── Restore Yesterday Setup (smart crew memory) ──────────────
  useEffect(() => {
    if (!draftLoaded || pendingDraft) return;
    if (!String(data.project_number || "").trim()) {
      setCrewSetupOffer(null);
      return;
    }
    try {
      const snap = loadCrewSetup({
        projectNumber: data.project_number,
        preparedBy: data.prepared_by,
        superintendent: data.superintendent,
      });
      if (!snap) return;
      setCrewSetupOffer(snap);
    } catch { /* silent */ }
  }, [draftLoaded, pendingDraft, data.project_number, data.prepared_by, data.superintendent]);

  const onUseCrewSetup = useCallback(async () => {
    if (!crewSetupOffer) return;
    if (isProjectChange(crewSetupOffer, data.project_number)) {
      const ok = window.confirm(
        "Your saved setup is from a different project. Bring it in anyway?",
      );
      if (!ok) return;
    }
    // Apply the snapshot first (fills people back into the row).
    setData((prev) => applySetupSnapshotToData(prev, crewSetupOffer));
    setCrewSetupOffer(null);
    // TRACK 23.4B / HR autofill · re-hydrate trade / crew / supervisor
    // from the CURRENT Employee Master, never yesterday's snapshot.
    try {
      const { data: empRes } = await api.get("/employees", { skipSessionStatus: true });
      const list = empRes?.items || empRes || [];
      setData((prev) => ({
        ...prev,
        masci_crews: refreshCrewFromEmployeeMaster(prev.masci_crews || [], list),
      }));
    } catch { /* HR fetch failure is silent — form is still usable */ }
    toast.success(t("Loaded yesterday's crew. HR fields refreshed."));
  }, [crewSetupOffer, data.project_number, t]);

  const onDismissCrewSetup = useCallback(() => setCrewSetupOffer(null), []);

  useEffect(() => {
    if (publicMode) {
      setSmartPrefillOffer(null);
      setSmartPrefillError("");
      setSmartPrefillFailureKind("");
      return undefined;
    }
    if (!draftLoaded || pendingDraft) return undefined;
    const projectNumber = String(data.project_number || "").trim();
    if (!projectNumber) {
      setSmartPrefillOffer(null);
      setSmartPrefillError("");
      setSmartPrefillFailureKind("");
      return undefined;
    }
    const foreman = String(data.prepared_by || "").trim();
    const superintendent = String(data.superintendent || "").trim();
    if (!foreman && !superintendent) {
      setSmartPrefillOffer(null);
      setSmartPrefillError("");
      setSmartPrefillFailureKind("");
      return undefined;
    }
    const requestKey = `${projectNumber}::${data.report_date || ""}::${foreman}::${superintendent}`;
    if (requestKey === smartPrefillLoadedKey && smartPrefillRetryNonce === 0) return undefined;
    let cancelled = false;
    setSmartPrefillLoading(true);
    emitDraftEvent("draft.lifecycle", { formKey: scopedFormKey, trigger: "smart_prefill.requested" });
    (async () => {
      try {
        const { data: res } = await api.get(`/jobs/${encodeURIComponent(projectNumber)}/recent-context`, {
          params: { foreman, superintendent },
          skipSessionStatus: true,
        });
        if (cancelled) return;
        const priorCrews = Array.isArray(res?.masci_crews) ? res.masci_crews : [];
        const priorEquipment = Array.isArray(res?.equipment) ? res.equipment : [];
        const hasReusable = Boolean(priorCrews.length || priorEquipment.length);
        setSmartPrefillOffer(hasReusable ? {
          actor_scoped: Boolean(res?.actor_scoped),
          superintendent: res?.superintendent || data.superintendent || "",
          priorCrews,
          priorEquipment,
          sourceDate: String(res?.source_report_date || "").trim(),
          sourceProject: projectNumber,
        } : null);
        setSmartPrefillError(hasReusable ? "" : t("No previous setup found for this project yet."));
        setSmartPrefillFailureKind(hasReusable ? "" : "no_prior_report");
      } catch (error) {
        if (cancelled) return;
        setSmartPrefillOffer(null);
        const status = Number(error?.response?.status || 0);
        const failureKind = status === 403 ? "permission" : (status >= 500 ? "request_failed" : (status ? "malformed_response" : "request_failed"));
        setSmartPrefillFailureKind(failureKind);
        setSmartPrefillError(
          failureKind === "permission"
            ? t("Previous setup is not available for this account. You can continue manually.")
            : failureKind === "malformed_response"
              ? t("Previous setup returned incomplete data. You can continue manually or try again.")
              : t("Previous setup could not be loaded. You can continue manually or try again."),
        );
        emitDraftEvent("draft.lifecycle", {
          formKey: scopedFormKey,
          trigger: "smart_prefill.failed",
          errorName: error?.name || "Error",
          error: error?.message || "request failed",
        });
      } finally {
        if (!cancelled) {
          setSmartPrefillLoadedKey(requestKey);
          setSmartPrefillLoading(false);
          setSmartPrefillRetryNonce(0);
        }
      }
    })();
    return () => { cancelled = true; };
  }, [publicMode, draftLoaded, pendingDraft, data.project_number, data.report_date, data.prepared_by, data.superintendent, smartPrefillLoadedKey, smartPrefillRetryNonce, scopedFormKey, t]);

  const onApplySmartPrefill = useCallback(() => {
    if (!smartPrefillOffer) return;
    const hasCrewData = Array.isArray(data.masci_crews) && data.masci_crews.some((row) => row?.name || row?.employee_id || row?.hours || row?.start_time || row?.stop_time);
    const hasEquipmentData = Array.isArray(data.equipment) && data.equipment.some((row) => row?.description || row?.hours_used || row?.notes);
    if ((hasCrewData || hasEquipmentData) && !window.confirm(t("Your current setup already has values. Replace the reusable setup fields?"))) {
      emitDraftEvent("draft.restore.action", { formKey: scopedFormKey, trigger: "smart_prefill.apply_rejected" });
      return;
    }
    const { priorCrews = [], priorEquipment = [], sourceDate } = smartPrefillOffer;
    setData((prev) => ({
      ...prev,
      masci_crews: priorCrews.map((c) => ({
        name: c.name || "",
        trade: c.trade || "",
        employee_id: c.employee_id || "",
        start_time: c.start_time || "",
        lunch_minutes: (c.lunch_minutes === 0 || c.lunch_minutes) ? c.lunch_minutes : "",
        stop_time: c.stop_time || "",
        hours: c.hours || "",
        work_performed: "",
        _prefilled: true,
      })),
      equipment: priorEquipment.map((e) => ({
        description: e.description || "",
        hours_used: e.hours_used || "",
        time_delivered: "",
        time_removed: "",
        notes: e.notes || "",
      })),
    }));
    setPrefillNotice({
      sourceDate: sourceDate || "",
      crewCount: priorCrews.length,
      equipCount: priorEquipment.length,
    });
    setSmartPrefillOffer(null);
    setSmartPrefillError("");
    emitDraftEvent("draft.restore.action", { formKey: scopedFormKey, trigger: "smart_prefill.applied" });
    toast.success(
      t("Prefilled from {d} — review and adjust before submit").replace("{d}", sourceDate || t("previous report")),
    );
  }, [smartPrefillOffer, data.masci_crews, data.equipment, scopedFormKey, t]);

  const onDismissSmartPrefill = useCallback(() => {
    setSmartPrefillOffer(null);
    emitDraftEvent("draft.restore.action", { formKey: scopedFormKey, trigger: "smart_prefill.skipped" });
  }, [scopedFormKey]);

  const onRetrySmartPrefill = useCallback(() => {
    if (smartPrefillLoading) return;
    setSmartPrefillOffer(null);
    setSmartPrefillLoadedKey("");
    setSmartPrefillRetryNonce((n) => n + 1);
    emitDraftEvent("draft.lifecycle", { formKey: scopedFormKey, trigger: "smart_prefill.retry" });
  }, [smartPrefillLoading, scopedFormKey]);

  // ── Cost code fetch (CostCodeProvider) ─────────────────────
  useEffect(() => {
    let cancelled = false;
    const hasPortalToken = hasAnyPortalAuthToken();
    if (!data.project_number) {
      setCostCodes([]);
      setProjectCostAssignments([]);
      setProjectCostProgress(null);
      return;
    }
    api
      .get(`/cost-codes/for-project?project_number=${encodeURIComponent(data.project_number)}`)
      .then(({ data: res }) => {
        if (cancelled) return;
        setCostCodes(Array.isArray(res?.codes) ? res.codes : []);
      })
      .catch(() => {
        if (!cancelled) setCostCodes([]);
      });
    if (!hasPortalToken) {
      setProjectCostAssignments([]);
      setProjectCostProgress(null);
      return () => {
        cancelled = true;
      };
    }
    api
      .get(`/cost-codes/projects/${encodeURIComponent(data.project_number)}/assignments`)
      .then(({ data: res }) => {
        if (cancelled) return;
        const assignments = Array.isArray(res?.assignments) ? res.assignments : [];
        setProjectCostAssignments(assignments);
        setProjectCostProgress(res?.progress || null);
        setData((prev) => {
          const existing = Array.isArray(prev.cost_code_quantities) ? prev.cost_code_quantities : [];
          const nextRows = assignments.map((assignment, index) => {
            const found = existing.find((row) => String(row?.cost_code || row?.code || "") === String(assignment?.code || ""));
            return {
              row_id: found?.row_id || `${assignment.code}-${index}`,
              cost_code: assignment.code || "",
              item_name: assignment.item_name || assignment.description || "",
              unit_of_measure: assignment.unit_of_measure || assignment.unit || "",
              installed_quantity: found?.installed_quantity ?? "",
              actual_performer: found?.actual_performer || "",
              planned_performer: assignment.planned_performer || found?.planned_performer || "",
              location: found?.location || prev.location || "",
              work_area: found?.work_area || "",
              notes: found?.notes || "",
              evidence_links: Array.isArray(found?.evidence_links) ? found.evidence_links : [],
              cpm_activity_id: assignment.cpm_activity_id || "",
              cpm_activity_name: assignment.cpm_activity_name || "",
              schedule_phase: assignment.schedule_phase || "",
            };
          });
          return { ...prev, cost_code_quantities: nextRows };
        });
      })
      .catch(() => {
        if (cancelled) return;
        setProjectCostAssignments([]);
        setProjectCostProgress(null);
      });
    return () => {
      cancelled = true;
    };
  }, [data.project_number]);

  // ── Report-number preview ─────────────────────────────────
  useEffect(() => {
    if (!data.report_date) return;
    let cancelled = false;
    api
      .get(`/daily-reports/next-number?report_date=${encodeURIComponent(data.report_date)}`, { skipSessionStatus: true })
      .then(({ data: res }) => {
        if (cancelled) return;
        const nextNumber = res?.next_number ?? res?.report_number ?? "";
        setReportNumberPreview(formatDailyReportNumberPreview(nextNumber));
      })
      .catch(() => {
        if (!cancelled) setReportNumberPreview("");
      });
    return () => {
      cancelled = true;
    };
  }, [data.report_date]);

  // ── GPS + weather ─────────────────────────────────────────
  const useGps = useCallback(async () => {
    const isEmbeddedPreview = detectEmbeddedPreviewRestriction();
    if (!("geolocation" in navigator)) {
      patch({
        location_permission_status: "unsupported",
        location_capture_result: "unsupported",
        location_error_code: "GEOLOCATION_API_UNAVAILABLE",
        location_error_message: "navigator.geolocation unavailable",
        location_capture_origin: window.location.origin,
      });
      toast.error(operatorGpsMessage("GEOLOCATION_API_UNAVAILABLE", t));
      return;
    }
    setFetchingGps(true);
    try {
      patch({
        location_capture_result: "locating",
        location_permission_status: "prompt",
        location_error_code: "",
        location_error_message: "",
        location_capture_origin: window.location.origin,
        location_capture_attempts: (data.location_capture_attempts || 0) + 1,
      });
      const getPosition = (options) => new Promise((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, options),
      );
      let pos;
      try {
        pos = await getPosition({ enableHighAccuracy: true, timeout: GEO_TIMEOUT_MS, maximumAge: GEO_MAX_AGE_MS });
      } catch (firstErr) {
        const code = classifyGeolocationFailure(firstErr, isEmbeddedPreview);
        if (code === "POSITION_UNAVAILABLE" || code === "LOCATION_TIMEOUT") {
          pos = await getPosition({ enableHighAccuracy: true, timeout: GEO_TIMEOUT_MS, maximumAge: 0 });
        } else {
          throw firstErr;
        }
      }
      const { latitude, longitude, accuracy } = pos.coords;
      const capturedAt = new Date().toISOString();
      const coordFallback = `${Number(latitude).toFixed(6)}, ${Number(longitude).toFixed(6)}`;
      patch({
        ...buildLocationPatch({
          latitude,
          longitude,
          accuracy,
          capturedAt,
          locationSource: "device_gps",
          permissionStatus: "granted",
          captureResult: "success",
          captureOrigin: window.location.origin,
        }),
        location: coordFallback,
        weather_snapshot_meta: data.weather_snapshot_meta
          ? { ...data.weather_snapshot_meta, stale_for_location_change: true }
          : null,
      });
      try {
        const rev = await reverseGeocode(latitude, longitude);
        const label = (typeof rev === "string" ? rev : rev?.display || "").trim();
        if (label) patch({ location: label });
      } catch { /* silent — coord fallback stands */ }
      try {
        const wx = await fetchDailyWeather(
          latitude,
          longitude,
          data.report_date || new Date().toISOString().slice(0, 10),
        );
        if (wx?.summary) {
          patch({
            weather_summary: wx.summary,
            weather_snapshots: wx.snapshots || [],
            weather_snapshot_meta: {
              ...(wx?.meta || {}),
              location_source: "device_gps",
              location_captured_at: capturedAt,
              location_accuracy_meters: accuracy,
              weather_coordinates_match_report: true,
              weather_fetch_status: "success",
              fetched_at_iso: wx?.fetched_at_iso || new Date().toISOString(),
            },
          });
          toast.success(t("Location captured · weather refreshed from captured coordinates"));
        }
      } catch (e) {
        patch({
          weather_snapshot_meta: {
            ...(data.weather_snapshot_meta || {}),
            location_source: "device_gps",
            location_captured_at: capturedAt,
            location_accuracy_meters: accuracy,
            weather_fetch_status: "failed",
            weather_fetch_error: String(e?.message || "weather fetch failed"),
            gps_lat: latitude,
            gps_lng: longitude,
          },
        });
        toast(t("Location captured · weather unavailable. Retry weather when signal improves."));
      }
    } catch (e) {
      const code = classifyGeolocationFailure(e, isEmbeddedPreview);
      patch({
        location_permission_status: code === "PERMISSION_DENIED" ? "denied" : (data.location_permission_status || "unknown"),
        location_capture_result: "failed",
        location_error_code: code,
        location_error_message: String(e?.message || code),
        location_capture_origin: window.location.origin,
      });
      toast.error(operatorGpsMessage(code, t));
    } finally {
      setFetchingGps(false);
    }
  }, [patch, data.report_date, data.location_capture_attempts, data.weather_snapshot_meta, data.location_permission_status, t]);

  const refreshWeather = useCallback(async () => {
    const lat = data.gps_lat;
    const lng = data.gps_lng;
    if (lat == null || lng == null) {
      toast.error(t("Capture a location first so we know where to check the forecast."));
      return;
    }
    setFetchingWeather(true);
    try {
      const wx = await fetchDailyWeather(
        lat,
        lng,
        data.report_date || new Date().toISOString().slice(0, 10),
      );
      if (wx?.summary) {
        patch({
          weather_summary: wx.summary,
          weather_snapshots: wx.snapshots || [],
          weather_snapshot_meta: {
            ...(wx?.meta || {}),
            location_source: data.location_source || "",
            location_captured_at: data.location_captured_at || "",
            location_accuracy_meters: data.gps_accuracy,
            weather_coordinates_match_report: Number(wx?.meta?.gps_lat) === Number(lat) && Number(wx?.meta?.gps_lng) === Number(lng),
            weather_fetch_status: "success",
            fetched_at_iso: wx?.fetched_at_iso || new Date().toISOString(),
          },
        });
      } else {
        toast(t("Weather unavailable — enter conditions manually."));
      }
    } catch {
      toast(t("Weather unavailable — enter conditions manually."));
    } finally {
      setFetchingWeather(false);
    }
  }, [data.gps_lat, data.gps_lng, data.location_source, data.location_captured_at, data.gps_accuracy, data.report_date, patch, t]);

  // ── Submit-readiness derivation ────────────────────────────
  const photoMin = data.photo_min || 6;
  const readiness = useMemo(() => {
    const items = [
      { key: "project", ok: !!data.project_name, label: t("Project") },
      { key: "location", ok: !!data.location, label: t("Location") },
      { key: "location_source", ok: !!data.location_source, label: t("Location source") },
      { key: "prepared_by", ok: !!data.prepared_by, label: t("Prepared By") },
      {
        key: "photos",
        ok: (data.photos || []).length >= photoMin,
        label: `${photoMin} ${t("photos")}`,
      },
      {
        key: "approved_summary",
        ok: !!(data.ai_accepted_summary || "").trim() && !!(data.ai_accepted_summary_meta?.accepted_at || "").trim(),
        label: t("Approved Executive Summary"),
      },
      { key: "signature", ok: !!data.prepared_by_signature, label: t("Signature") },
    ];
    if (data.weather_summary || (data.weather_snapshots || []).length > 0) {
      items.push({
        key: "weather_coordinate_parity",
        ok:
          data.gps_lat != null &&
          data.gps_lng != null &&
          !!(data.weather_snapshot_meta?.observation_timestamp || data.weather_snapshot_meta?.peak_timestamp) &&
          Number(data.weather_snapshot_meta?.gps_lat) === Number(data.gps_lat) &&
          Number(data.weather_snapshot_meta?.gps_lng) === Number(data.gps_lng),
        label: t("Weather coordinates match report location"),
      });
    }
    // TRACK 23.4A · Full V1 safety-escalation gate. When the supervisor
    // flags any safety event, Safety must be contacted, contact fields
    // must be populated, and an Incident/Accident report must be filed
    // (or the equivalent block acknowledged). Mirrors V1 submit-time
    // enforcement so operator instinct is preserved.
    if (data.safety_present === "Yes") {
      items.push({
        key: "safety_event_type",
        ok: !!(data.safety_event_type || "").trim(),
        label: t("Safety event type"),
      });
      items.push({
        key: "safety_notified",
        ok: data.safety_notified === "Yes",
        label: t("Safety contacted"),
      });
      if (data.safety_notified === "Yes") {
        items.push({
          key: "safety_contact_person",
          ok: !!(data.safety_contact_person || "").trim(),
          label: t("Who at Safety"),
        });
        items.push({
          key: "safety_contact_time",
          ok: !!(data.safety_contact_time || "").trim(),
          label: t("Time Safety contacted"),
        });
      }
      items.push({
        key: "incident_report",
        ok: data.incident_report_filled === "Yes",
        label: t("Incident report filed"),
      });
      if (data.incident_report_filled === "Yes") {
        items.push({
          key: "incident_report_time",
          ok: !!(data.incident_report_time || "").trim(),
          label: t("Time incident report filed"),
        });
      }
    }
    const completed = items.filter((i) => i.ok).length;
    const missing = items.filter((i) => !i.ok).map((i) => i.label);
    return { items, total: items.length, completed, missing };
  }, [data, photoMin, t]);

  const canSubmit = readiness.completed === readiness.total;
  const submitLabel = useMemo(() => t("Submit Daily Report"), [t]);

  // ── Submit — same contract as V1, offline-safe via enqueueUpload ──
  const onSubmit = useCallback(async () => {
    if (saving) return;
    if (!canSubmit) {
      toast.error(`${t("Missing:")} ${readiness.missing.join(", ")}`);
      return;
    }

    // TRACK 26.11 · pre-submit duplicate guard. If a report already
    // exists for (project_number, report_date, prepared_by), ask the
    // operator before minting a second doc_id. Non-blocking on
    // network error — the submit path continues if the check itself
    // fails, so a bad connection can never lock out a legitimate
    // submit. Admin override is implicit (they just confirm).
    if (online && (data.project_number || "").trim() && (data.report_date || "").trim()) {
      try {
        const preparedBy = (data.prepared_by || "").trim();
        const q = new URLSearchParams({
          project_number: data.project_number.trim(),
          report_date: data.report_date.trim(),
          ...(preparedBy ? { submitted_by: preparedBy } : {}),
        });
        const { data: dup } = await api.get(`/daily-reports/duplicate-check?${q.toString()}`, {
          skipSessionStatus: true,
        });
        if (dup && dup.exists) {
          const first = (dup.matches || [])[0] || {};
          const existing = first.report_number || first.doc_id || first.id || "another report";
          const ok = window.confirm(
            `${t("A Daily Report already exists for this project on this date")}\n\n` +
            `${existing} — ${first.prepared_by || t("unknown author")}\n\n` +
            `${t("Submit another one anyway?")}`
          );
          if (!ok) {
            toast(t("Submit cancelled."), { id: "dr-v3-dup-cancelled" });
            return;
          }
        }
      } catch { /* duplicate check is best-effort — never blocks submit */ }
    }

    setSaving(true);
    const idem = idempotencyKeyRef.current || mintIdempotencyKey();
    idempotencyKeyRef.current = idem;
    await persistIdempotencyKey(scopedFormKey, idem);
    const cleanCrews = Array.isArray(data.masci_crews)
      ? data.masci_crews.map((row) => {
          if (row && typeof row === "object" && "_prefilled" in row) {
            const { _prefilled, ...rest } = row;
            void _prefilled;
            return rest;
          }
          return row;
        })
      : data.masci_crews;
    let payload = {
      ...data,
      masci_crews: cleanCrews,
      submit_language: lang,
      ui_shell: "daily-report",
    };

    // ── TRACK 24.3 · ES → EN canonical translation ──
    // If the operator authored in Spanish, translate every natural-
    // language free-text field on the payload to English BEFORE any
    // backend consumer sees it. Fail-closed on translation failure.
    if (lang === "es") {
      try {
        toast.loading(t("Translating…"), { id: "dr-v3-translating" });
        const tr = await translateDrV3PayloadEsToEn(payload);
        toast.dismiss("dr-v3-translating");
        if (!tr.ok) {
          toast.error(
            t("Spanish text could not be translated for submission. Please try again or switch to English."),
            { id: "dr-v3-translation-error", duration: 8000 },
          );
          setSaving(false);
          return;
        }
        payload = tr.payload;
        // Backend now sees canonical English content.
        payload.submit_language = "en";
        payload.ui_submit_language = "es";
      } catch (e) {
        toast.dismiss("dr-v3-translating");
        toast.error(
          t("Spanish text could not be translated for submission. Please try again or switch to English."),
          { id: "dr-v3-translation-error", duration: 8000 },
        );
        setSaving(false);
        return;
      }
    }

    try {
      if (online) {
        // Online: submit inline and commit the draft on success.
        const { data: saved } = await api.post("/daily-reports", payload, {
          headers: { "Idempotency-Key": idem },
        });
        try { saveCrewSetup(extractSetupSnapshot(payload)); } catch { /* silent */ }
        await commitDraft();
        if (!publicMode && payload.project_number) rememberLastProject(String(payload.project_number));
        const notificationState = String(saved?.notification_state || "").toLowerCase();
        const reportRef = saved?.report_number || saved?.doc_id || saved?.id || "";
        const savedLabel = reportRef ? t("Daily report {{reportRef}} saved.", { reportRef }) : t("Daily report submitted.");
        if (notificationState === "captured_preview") {
          toast.success(t("{{savedLabel}} Email safely captured in Preview.", { savedLabel }), {
            id: "daily-report-preview-capture-toast",
          });
        } else if (notificationState === "provider_accepted") {
          toast.success(t("{{savedLabel}} Project team email accepted.", { savedLabel }), {
            id: "daily-report-provider-accepted-toast",
          });
        } else if (notificationState === "failed_action_required" || notificationState === "permanent_failure") {
          toast.success(t("{{savedLabel}} Delivery needs office follow-up, but the report is preserved.", { savedLabel }), {
            id: "daily-report-follow-up-toast",
            duration: 8000,
          });
        } else if (notificationState && notificationState !== "provider_accepted") {
          toast.success(t("{{savedLabel}} Delivery is being tracked separately.", { savedLabel }), {
            id: "daily-report-notification-recorded-toast",
          });
        } else {
          toast.success(savedLabel);
        }
        if (publicMode) {
          navigate("/thank-you", {
            state: {
              formType: "Daily Report",
              projectName: payload.project_name || payload.project_number || "",
              returnTo: "/daily/submit",
              recordId: saved?.report_number || saved?.doc_id || saved?.id || "",
              submissionState: notificationState === "provider_accepted" ? "delivered" : "saved",
              notificationState,
              notificationDeliveryMode: saved?.notification_delivery_mode || "",
              notificationCaptureAvailable: !!saved?.notification_capture_available,
              notificationFailureReason: saved?.notification_failure_reason || "",
            },
          });
        }
        else if (saved?.id) navigate(`/daily/${saved.id}`);
        else navigate("/admin/daily");
      } else {
        // Offline: hand to the shared queue. The queue re-tries with
        // the same Idempotency-Key so a mid-flight reconnect never
        // creates a duplicate DR.
        enqueueUpload({
          url: "/daily-reports",
          method: "POST",
          body: payload,
          idempotencyKey: idem,
          formKey: scopedFormKey,
          actorId: deviceId,
        });
        onQueueItemSettled(idem, async (res) => {
          if (res?.ok) {
            try { saveCrewSetup(extractSetupSnapshot(payload)); } catch { /* silent */ }
            await commitDraft();
          }
        });
        emitDraftEvent("draft.lifecycle", { formKey: scopedFormKey, trigger: "offline.queued" });
        if (!publicMode && payload.project_number) rememberLastProject(String(payload.project_number));
        toast(t("Offline — saved on this device and will send when connection returns."));
        if (publicMode) {
          navigate("/thank-you", {
            state: {
              formType: "Daily Report",
              projectName: payload.project_name || payload.project_number || "",
              returnTo: "/daily/submit",
              submissionState: "queued",
              notificationDeliveryMode: payload?.notification_delivery_mode || "",
            },
          });
        } else {
          navigate("/admin/daily");
        }
      }
    } catch (err) {
      const classified = classifyApiError(err);
      if (classified.kind === "network_unreachable" || classified.kind === "backend_unavailable") {
        publishSessionStatus({
          ...classified,
          meta: {
            endpoint: "/daily-reports",
            method: "POST",
            retry: () => submitRetryRef.current?.(),
          },
        });
      }
      // TRACK 26.02 · D-09 · Surface Pydantic 422 detail to the operator
      // instead of the generic "Submit failed. Please retry." fallback.
      // FastAPI returns `detail` as either a string (raise HTTPException)
      // or a list of `{loc, msg, type, input}` (Pydantic validation).
      // Both shapes render into a single field-level message the
      // operator can act on from the field.
      const detail = err?.response?.data?.detail;
      let msg;
      if (typeof detail === "string") {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length) {
        const first = detail[0];
        const loc = Array.isArray(first?.loc) ? first.loc.filter((l) => l !== "body").join(" → ") : "";
        const hint = first?.msg || first?.type || "";
        const badInput = first?.input != null ? ` (got: ${JSON.stringify(first.input).slice(0, 40)})` : "";
        msg = loc ? `${loc}: ${hint}${badInput}` : (hint || t("Submit failed. Please retry."));
      } else {
        msg = t("Submit failed. Please retry.");
      }
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  }, [saving, canSubmit, data, online, publicMode, navigate, readiness.missing, commitDraft, lang, t, scopedFormKey, rememberLastProject, deviceId]);

  useEffect(() => {
    submitRetryRef.current = () => onSubmit();
  }, [onSubmit]);

  return (
    <FormShell
      kicker={t("MASCI · Daily Job Report")}
      title={t("Today's report")}
      subtitle={t("Nine short steps. Dropdowns first. AI drafts your summary. Save state, scope, and next action stay visible the whole time.")}
      backLink={!publicMode ? "/" : null}
      draftSlot={(
        <div className="flex items-center gap-2" data-testid="dr-v3-draft-pill-slot">
          <DraftStatusPill
            status={(() => {
              if (saving) return "syncing";
              if (draftStatus === "saving") return "saving";
              if (draftStatus === "failed") return "failed";
              if (!online) return "offline";
              if (canSubmit) return "ready";
              if (draftStatus === "saved" || pendingSavedAt || lastSavedAt) return "saved";
              return "draft";
            })()}
            lastSavedAt={lastSavedAt || pendingSavedAt}
            testId="daily-report-draft-status"
          />
          {(draftStatus === "idle" && !pendingSavedAt && online && !canSubmit) && (
            <span
              data-testid="daily-report-autosave-status"
              className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-100 border border-slate-700"
            >
              {t("Autosave on")}
            </span>
          )}
        </div>
      )}
      headerRightSlot={
        !online ? (
          <span
            data-testid="dr-v3-offline-chip"
            className="rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900"
          >
            {t("Offline")}
          </span>
        ) : null
      }
      stickyFooter={(
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" data-testid="dr-v3-sticky-submit-bar">
          <div className="text-sm text-slate-600" data-testid="dr-v3-sticky-submit-status">
            {canSubmit
              ? t("Ready to submit")
              : `${t("Still needed:")} ${readiness.missing.join(" · ") || t("checking…")}`}
          </div>
          <Button
            type="button"
            className="h-11 rounded-full bg-emerald-600 px-5 text-sm font-semibold text-white hover:bg-emerald-700"
            disabled={!canSubmit || saving}
            onClick={onSubmit}
            data-testid="dr-v3-sticky-submit-btn"
          >
            {saving ? t("Submitting…") : (submitLabel || t("Submit Daily Report"))}
          </Button>
        </div>
      )}
      containerTestId="dr-v3-form-shell"
    >
      <div className="mx-auto max-w-3xl px-0 py-1 sm:py-4" data-testid="dr-v3-form-root">
        {/* TRACK 26.11 · always-on scope chip so the operator can see
            at a glance which project + date + device this draft
            belongs to. Rendered above the header so it's the first
            thing they land on when resuming a report from any tab.  */}
        <div className="mb-4">
          <DraftScopeChip
            projectNumber={data.project_number}
            projectName={data.project_name}
            reportDate={data.report_date}
            deviceId={getDeviceId()}
            status={(() => {
              if (saving) return "syncing";
              if (draftStatus === "saving") return "saving";
              if (draftStatus === "failed") return "failed";
              if (!online) return "offline";
              if (canSubmit) return "ready";
                if (draftStatus === "saved" || pendingSavedAt || lastSavedAt) return "saved";
              return "draft";
            })()}
            lastSavedAt={lastSavedAt || pendingSavedAt}
          />
        </div>
        {/* Draft restore prompt — never silently overwrites work. */}
        {(pendingDraft || fallbackDraftOffer?.form) && (
          <div className="mb-4" data-testid="dr-v3-draft-restore-prompt">
            <DraftRestorePrompt
              pendingDraft={preferFallbackDraft ? fallbackDraftOffer?.form : pendingDraft || fallbackDraftOffer?.form}
              savedAt={preferFallbackDraft ? fallbackDraftOffer?.savedAt : pendingSavedAt || fallbackDraftOffer?.savedAt}
              isCrossToken={pendingIsCrossToken}
              onRestore={() => {
                if (pendingDraft && !preferFallbackDraft) {
                  const d = restoreDraft();
                  if (d) setData((prev) => ({ ...prev, ...d }));
                  return;
                }
                if (fallbackDraftOffer?.form) {
                  setData((prev) => ({ ...prev, ...fallbackDraftOffer.form }));
                  setFallbackDraftOffer(null);
                }
              }}
              onDiscard={async () => {
                if (pendingDraft && !preferFallbackDraft) {
                  await discardDraft();
                  return;
                }
                if (fallbackDraftOffer?.formKey) {
                  await discardStoredDraft(getDeviceScopedActorId(), fallbackDraftOffer.formKey);
                  setFallbackDraftOffer(null);
                }
              }}
            />
          </div>
        )}

        <DraftRecoveryNotice
          archive={pendingDraft ? null : archivedDraft}
          onRecover={onRecoverArchive}
          onDismiss={() => setArchivedDraft(null)}
          testId="dr-v3-draft-recovery"
        />

        {!publicMode && smartPrefillOffer && !pendingDraft && !crewSetupOffer ? (
          <div
            data-testid="dr-v3-smart-prefill-offer"
            className="wp17-form-alert wp17-tone--amber mb-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-800">
                  {t("Use your previous submitted setup?")}
                </p>
                <p className="mt-1 text-sm text-slate-800">
                  {t("{crew} crew · {equip} equipment from {date}")
                    .replace("{crew}", String(smartPrefillOffer.priorCrews.length))
                    .replace("{equip}", String(smartPrefillOffer.priorEquipment.length))
                    .replace("{date}", smartPrefillOffer.sourceDate || t("the previous report"))}
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  {t("Hours and setup are editable before submit.")}
                </p>
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="outline" size="sm" onClick={onDismissSmartPrefill} data-testid="dr-v3-smart-prefill-dismiss">
                  {t("Start Fresh")}
                </Button>
                <Button type="button" size="sm" onClick={onApplySmartPrefill} data-testid="dr-v3-smart-prefill-apply">
                  {t("Restore Setup")}
                </Button>
              </div>
            </div>
          </div>
        ) : null}

        {smartPrefillError ? (
          <div
            data-testid="dr-v3-smart-prefill-error"
            className="wp17-form-alert wp17-tone--amber mb-4 text-sm text-amber-900"
          >
            <div>{smartPrefillError}</div>
            {smartPrefillFailureKind && smartPrefillFailureKind !== "no_prior_report" ? (
              <div className="mt-3 flex gap-2">
                <Button type="button" size="sm" onClick={onRetrySmartPrefill} disabled={smartPrefillLoading} data-testid="dr-v3-smart-prefill-retry">
                  {smartPrefillLoading ? t("Trying again…") : t("Try Again")}
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}

        {prefillNotice ? (
          <div
            data-testid="dr-v3-smart-prefill-notice"
            className="wp17-form-alert wp17-tone--cyan mb-4 text-sm text-sky-900"
          >
            {t("Restored from {d} · review and adjust hours before submit")
              .replace("{d}", prefillNotice.sourceDate || t("the previous report"))}
          </div>
        ) : null}

        {/* Restore Yesterday Setup — smart crew memory. */}
        {crewSetupOffer && !pendingDraft && (
          <div
            data-testid="dr-v3-crew-setup-offer"
            className="mb-4 flex items-center justify-between rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <History className="h-5 w-5 text-emerald-700" />
              <div className="text-sm text-emerald-900">
                <div className="font-medium">{t("Use yesterday's crew setup?")}</div>
                <div className="text-xs text-emerald-800">
                  {(crewSetupOffer.masci_crews?.length || 0)} crew ·{" "}
                  {(crewSetupOffer.equipment?.length || 0)} equipment · reviewable before submit.
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button type="button" size="sm" onClick={onUseCrewSetup} data-testid="dr-v3-crew-setup-use">
                {t("Use setup")}
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={onDismissCrewSetup} data-testid="dr-v3-crew-setup-dismiss">
                {t("Not today")}
              </Button>
            </div>
          </div>
        )}

        <div className="wp17-form-frame wp17-form-shell" data-testid="dr-v3-form-body-shell">
          <div className="space-y-4 sm:space-y-5" data-testid="dr-v3-form">
          <SectionProjectConditions
            data={data}
            patch={patch}
            onUseGps={useGps}
            onRefreshWeather={refreshWeather}
            isFetchingGps={isFetchingGps}
            isFetchingWeather={isFetchingWeather}
            weatherLabel={data.weather_summary
              ? t("Weather refreshed from the current verified location.")
              : data.location_error_code === "PREVIEW_IFRAME_PERMISSION_BLOCK"
                ? t("Embedded preview blocked location access. Open in a new tab to test GPS.")
                : ""}
            reportNumberPreview={reportNumberPreview}
          />
          <SectionCrewEquipment data={data} patch={patch} costCodes={costCodes} />
          <SectionWorkProduction
            data={data}
            patch={patch}
            costCodes={costCodes}
            projectCostAssignments={projectCostAssignments}
            projectCostProgress={projectCostProgress}
          />
          <SectionMaterials data={data} patch={patch} costCodes={costCodes} />
          <SectionPhotos
            data={data}
            patch={patch}
            photoMin={photoMin}
            photoIntelStatus={photoIntelStatusState}
            onPhotoBatchStateChange={setPhotoBatchState}
            onPhotoReady={({ completed, total }) => setPhotoWarmHint({ completed, total, at: Date.now() })}
          />
          <SectionImpactSafety data={data} patch={patch} />
          {/* TRACK 23.10-E · Excavation section — collapsed unless
              excavation today = Yes. Consumes Qualifications Engine. */}
          <DailyReportV3ExcavationSection
            value={data.excavation || {}}
            onChange={(exc) => patch({
              excavation: exc,
              excavation_activity_today: String(exc?.excavation_today || "").toLowerCase() === "yes" ? "Yes" : "No",
            })}
          />
          <SectionTomorrow data={data} patch={patch} />
          <SectionAiSummary
            data={data}
            reportId={reportId}
            formKey={scopedFormKey}
            photoUploadState={{ ...photoBatchState, warmHint: photoWarmHint }}
            onPhotoIntelChange={setPhotoIntelStatusState}
            onStateChange={setSummaryGate}
            onAccepted={(payload) =>
              patch({
                ai_accepted_summary: payload?.summary || "",
                ai_accepted_summary_meta: payload?.meta || null,
                photo_observations: Array.isArray(payload?.meta?.photo_observations) ? payload.meta.photo_observations : [],
                photo_intelligence_status: payload?.meta?.photo_intelligence_status || "",
              })
            }
          />
          <SectionSignoff
            data={data}
            patch={patch}
            readiness={readiness}
            canSubmit={canSubmit}
            saving={saving}
            onSubmit={onSubmit}
            submitLabel={submitLabel}
            showInlineSubmit={false}
          />
          </div>
        </div>
      </div>
    </FormShell>
  );
}
