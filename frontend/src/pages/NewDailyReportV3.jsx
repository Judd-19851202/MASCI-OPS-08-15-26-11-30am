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
// The flag hook (`useDailyReportV3Flag`) is consulted by AppRoutes
// to decide whether this shell or the V1 shell renders at
// `/daily/new`. This file itself never checks the flag — it's already
// running.
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
} from "@/lib/resiliency";
import DraftScopeChip from "@/lib/resiliency/DraftScopeChip";
import { getDeviceId } from "@/lib/resiliency/deviceId";
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
import { DailyReportTopBanner } from "@/components/DailyReportTopBanner";
import DailyReportV3ExcavationSection from "@/components/daily-report-v3/DailyReportV3ExcavationSection";
import { CheckCircle2, History } from "lucide-react";
import { useT } from "@/lib/i18n";
import { LangToggle } from "@/components/LangToggle";
import { translateDrV3PayloadEsToEn } from "@/lib/drV3Translation";

// Form key MUST match V1 so that a mid-flight draft written in V1 can
// still restore when the pilot flag flips the operator into V3 (and
// vice versa on rollback). One draft. Two shells.
const FORM_KEY = "daily-report";

export default function NewDailyReportV3({ publicMode = false }) {
  const navigate = useNavigate();
  const { t, lang } = useT();
  const [data, setData] = useState(() => buildDailyReportDefaults());
  const [reportId, setReportId] = useState("");
  const [saving, setSaving] = useState(false);
  const [isFetchingGps, setFetchingGps] = useState(false);
  const [isFetchingWeather, setFetchingWeather] = useState(false);
  const [costCodes, setCostCodes] = useState([]);
  const [reportNumberPreview, setReportNumberPreview] = useState("");
  const [crewSetupOffer, setCrewSetupOffer] = useState(null);
  const [summaryGate, setSummaryGate] = useState({ canSubmit: false, manualNeeded: false });
  const idempotencyKeyRef = useRef(null);

  const patch = useCallback((delta) => {
    setData((prev) => ({ ...prev, ...delta }));
  }, []);

  // ── Field resiliency (autosave / draft restore / archive) ────
  // TRACK 26.11 · scope the draft key to (project, report_date) when
  // both are populated so a multi-project supervisor can carry an
  // in-progress DR on project 26-07 for 2026-07-08 without it being
  // overwritten by their DR on project 24-99 for the same day.
  // Empty scope falls back to the ambient single-slot behaviour, so
  // pre-project prelude drafts still work exactly as before.
  const draftScope = ((data.project_number || "").trim() && (data.report_date || "").trim())
    ? `${data.project_number.trim()}::${data.report_date.trim()}`
    : "";
  const {
    pendingDraft, pendingSavedAt, loaded: draftLoaded,
    draftStatus, restore: restoreDraft, discard: discardDraft,
    commit: commitDraft,
  } = useFormDraft(FORM_KEY, data, undefined, { scope: draftScope });
  const online = useOnlineStatus();

  // Idempotency key: load once from IDB (survives reload) or mint fresh.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let key = await loadIdempotencyKey(FORM_KEY);
      if (!key) {
        key = mintIdempotencyKey();
        await persistIdempotencyKey(FORM_KEY, key);
      }
      if (!cancelled) idempotencyKeyRef.current = key;
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Restore Yesterday Setup (smart crew memory) ──────────────
  useEffect(() => {
    if (!draftLoaded || pendingDraft) return;
    try {
      const snap = loadCrewSetup();
      if (!snap) return;
      setCrewSetupOffer(snap);
    } catch { /* silent */ }
  }, [draftLoaded, pendingDraft]);

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
      const { data: empRes } = await api.get("/employees");
      const list = empRes?.items || empRes || [];
      setData((prev) => ({
        ...prev,
        masci_crews: refreshCrewFromEmployeeMaster(prev.masci_crews || [], list),
      }));
    } catch { /* HR fetch failure is silent — form is still usable */ }
    toast.success(t("Loaded yesterday's crew. HR fields refreshed."));
  }, [crewSetupOffer, data.project_number, t]);

  const onDismissCrewSetup = useCallback(() => setCrewSetupOffer(null), []);

  // ── Cost code fetch (CostCodeProvider) ─────────────────────
  useEffect(() => {
    let cancelled = false;
    if (!data.project_number) {
      setCostCodes([]);
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
    return () => {
      cancelled = true;
    };
  }, [data.project_number]);

  // ── Report-number preview ─────────────────────────────────
  useEffect(() => {
    if (!data.report_date) return;
    let cancelled = false;
    api
      .get(`/daily-reports/next-number?report_date=${encodeURIComponent(data.report_date)}`)
      .then(({ data: res }) => {
        if (cancelled) return;
        if (res?.next_number) setReportNumberPreview(res.next_number);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [data.report_date]);

  // ── GPS + weather ─────────────────────────────────────────
  const useGps = useCallback(async () => {
    if (!navigator.geolocation) {
      toast.error(t("GPS is not available on this device"));
      return;
    }
    setFetchingGps(true);
    try {
      const pos = await new Promise((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, {
          enableHighAccuracy: true,
          timeout: 12000,
        }),
      );
      const { latitude, longitude, accuracy } = pos.coords;
      // TRACK 23.4B · Always fill Location with a STRING. reverseGeocode
      // returns an object `{ display, lat, lng, raw }` — never spread it
      // into the text input directly. Fall back to a plain coord string
      // if reverse geocode fails or has no usable label.
      const coordFallback = `${Number(latitude).toFixed(6)}, ${Number(longitude).toFixed(6)}`;
      patch({
        gps_lat: latitude,
        gps_lng: longitude,
        gps_accuracy: accuracy,
        location: coordFallback,
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
              fetched_at_iso: wx?.fetched_at_iso || new Date().toISOString(),
            },
          });
        }
      } catch (e) {
        // Graceful: no red toast on GPS path. Location + coords already set.
        // Operator can retry via the explicit Refresh Weather button.
      }
    } catch (e) {
      toast.error(t("GPS unavailable — you can enter location manually"));
    } finally {
      setFetchingGps(false);
    }
  }, [patch, data.report_date, t]);

  const refreshWeather = useCallback(async () => {
    if (!data.gps_lat || !data.gps_lng) {
      toast.error(t("Tap GPS first so we know where to check the forecast."));
      return;
    }
    setFetchingWeather(true);
    try {
      const wx = await fetchDailyWeather(
        data.gps_lat,
        data.gps_lng,
        data.report_date || new Date().toISOString().slice(0, 10),
      );
      if (wx?.summary) {
        patch({
          weather_summary: wx.summary,
          weather_snapshots: wx.snapshots || [],
          weather_snapshot_meta: {
            ...(wx?.meta || {}),
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
  }, [data.gps_lat, data.gps_lng, data.report_date, patch, t]);

  // ── Submit-readiness derivation ────────────────────────────
  const photoMin = data.photo_min || 6;
  const readiness = useMemo(() => {
    const items = [
      { key: "project", ok: !!data.project_name, label: t("Project") },
      { key: "location", ok: !!data.location, label: t("Location") },
      { key: "prepared_by", ok: !!data.prepared_by, label: t("Prepared By") },
      {
        key: "photos",
        ok: (data.photos || []).length >= photoMin,
        label: `${photoMin} ${t("photos")}`,
      },
      {
        key: "approved_summary",
        ok: !!(data.ai_accepted_summary || "").trim() && !!(data.ai_accepted_summary_meta?.accepted_at || "").trim(),
        label: t("Approved executive summary"),
      },
      { key: "signature", ok: !!data.prepared_by_signature, label: t("Signature") },
    ];
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
  const submitLabel = useMemo(() => {
    if ((data.ai_accepted_summary || "").trim()) return t("Submit Daily Report");
    if (summaryGate.manualNeeded) return t("Approve manual summary to unlock submit");
    return t("Approve the executive summary to unlock submit");
  }, [data.ai_accepted_summary, summaryGate.manualNeeded, t]);

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
        const { data: dup } = await api.get(`/daily-reports/duplicate-check?${q.toString()}`);
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
    let payload = { ...data, submit_language: lang, ui_shell: "v3" };

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
        toast.success(t("Daily report submitted."));
        if (publicMode) navigate("/thank-you");
        else if (saved?.id) navigate(`/daily/${saved.id}`);
        else navigate("/admin/daily");
      } else {
        // Offline: hand to the shared queue. The queue re-tries with
        // the same Idempotency-Key so a mid-flight reconnect never
        // creates a duplicate DR.
        const item = enqueueUpload({
          endpoint: "/daily-reports",
          method: "POST",
          payload,
          idempotencyKey: idem,
          formKey: FORM_KEY,
        });
        onQueueItemSettled(item?.id, async (res) => {
          if (res?.ok) {
            try { saveCrewSetup(extractSetupSnapshot(payload)); } catch { /* silent */ }
            await commitDraft();
          }
        });
        toast(t("Queued — will send when connection returns."));
        navigate(publicMode ? "/thank-you?queued=1" : "/admin/daily");
      }
    } catch (err) {
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
  }, [saving, canSubmit, data, online, publicMode, navigate, readiness.missing, commitDraft, lang, t]);

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      {/* TRACK 23.4B · Visual consistency · V3 now shares the same
          `blueprint-bg` engineering-grid background used by QA/QC,
          Safety Audits, Field Safety, JHP, Excavation. One design
          system across every MASCI field form. Do not swap for a
          plain slate-50 — that produced the visual drift the operator
          flagged. */}
      <DailyReportTopBanner backLink="/" showBackLink={!publicMode}>
        <div className="flex items-center gap-2" data-testid="dr-v3-header-chips">
          <LangToggle variant="dark" testId="dr-v3-lang-toggle" />
          {!online && (
            <span
              data-testid="dr-v3-offline-chip"
              className="rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900"
            >
              {t("Offline")}
            </span>
          )}
          <div data-testid="dr-v3-draft-pill-slot">
            {/* TRACK 26.08 · seven contract states. Priority order:
                submitted > saving > offline > ready > saved > draft.
                `saving`, `saved`, `failed` come straight from the
                autosave hook; `offline`, `ready`, `draft` are derived
                from the current form context. */}
            <DraftStatusPill
              status={(() => {
                if (saving) return "syncing";
                if (draftStatus === "saving") return "saving";
                if (draftStatus === "failed") return "failed";
                if (!online) return "offline";
                if (canSubmit) return "ready";
                if (draftStatus === "saved" || pendingSavedAt) return "saved";
                return "draft";
              })()}
              lastSavedAt={pendingSavedAt}
              testId="dr-v3-draft-pill"
            />
            {(draftStatus === "idle" && !pendingSavedAt && online && !canSubmit) && (
              <span
                data-testid="dr-v3-draft-pill"
                className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-100 border border-slate-700"
              >
                {t("Autosave on")}
              </span>
            )}
          </div>
        </div>
      </DailyReportTopBanner>

      <div className="mx-auto max-w-3xl px-4 py-6 sm:py-10">
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
              if (draftStatus === "saved" || pendingSavedAt) return "saved";
              return "draft";
            })()}
            lastSavedAt={pendingSavedAt}
          />
        </div>
        <header className="mb-6 sm:mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-600">
            <CheckCircle2 className="h-4 w-4" />
            {t("MASCI · Daily Job Report")}
          </div>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            {t("Today's report")}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {t("Nine short steps. Dropdowns first. AI drafts your summary.")}
          </p>
        </header>

        {/* Draft restore prompt — never silently overwrites work. */}
        {pendingDraft && (
          <div className="mb-4" data-testid="dr-v3-draft-restore-prompt">
            <DraftRestorePrompt
              savedAt={pendingSavedAt}
              onRestore={() => {
                const d = restoreDraft();
                if (d) setData((prev) => ({ ...prev, ...d }));
              }}
              onDiscard={discardDraft}
            />
          </div>
        )}

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
              <button
                type="button"
                onClick={onUseCrewSetup}
                data-testid="dr-v3-crew-setup-use"
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
              >
                {t("Use setup")}
              </button>
              <button
                type="button"
                onClick={onDismissCrewSetup}
                data-testid="dr-v3-crew-setup-dismiss"
                className="rounded-md px-3 py-1.5 text-xs text-emerald-800 hover:bg-emerald-100"
              >
                {t("Not today")}
              </button>
            </div>
          </div>
        )}

        <div className="space-y-4 sm:space-y-5" data-testid="dr-v3-form">
          <SectionProjectConditions
            data={data}
            patch={patch}
            onUseGps={useGps}
            onRefreshWeather={refreshWeather}
            isFetchingGps={isFetchingGps}
            isFetchingWeather={isFetchingWeather}
            weatherLabel={data.weather_summary ? t("Auto-loaded from GPS.") : ""}
            reportNumberPreview={reportNumberPreview}
          />
          <SectionCrewEquipment data={data} patch={patch} costCodes={costCodes} />
          <SectionWorkProduction data={data} patch={patch} costCodes={costCodes} />
          <SectionMaterials data={data} patch={patch} costCodes={costCodes} />
          <SectionPhotos data={data} patch={patch} photoMin={photoMin} />
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
            onStateChange={setSummaryGate}
            onAccepted={(payload) =>
              patch({
                ai_accepted_summary: payload?.summary || "",
                ai_accepted_summary_meta: payload?.meta || null,
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
          />
        </div>
      </div>
    </div>
  );
}
