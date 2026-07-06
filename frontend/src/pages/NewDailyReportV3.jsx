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
import {
  extractSetupSnapshot, saveCrewSetup, loadCrewSetup, applySetupSnapshotToData,
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
import { CheckCircle2, History } from "lucide-react";

// Form key MUST match V1 so that a mid-flight draft written in V1 can
// still restore when the pilot flag flips the operator into V3 (and
// vice versa on rollback). One draft. Two shells.
const FORM_KEY = "daily-report";

export default function NewDailyReportV3({ publicMode = false }) {
  const navigate = useNavigate();
  const [data, setData] = useState(() => buildDailyReportDefaults());
  const [reportId, setReportId] = useState("");
  const [saving, setSaving] = useState(false);
  const [isFetchingGps, setFetchingGps] = useState(false);
  const [isFetchingWeather, setFetchingWeather] = useState(false);
  const [costCodes, setCostCodes] = useState([]);
  const [reportNumberPreview, setReportNumberPreview] = useState("");
  const [crewSetupOffer, setCrewSetupOffer] = useState(null);
  const idempotencyKeyRef = useRef(null);

  const patch = useCallback((delta) => {
    setData((prev) => ({ ...prev, ...delta }));
  }, []);

  // ── Field resiliency (autosave / draft restore / archive) ────
  const {
    pendingDraft, pendingSavedAt, loaded: draftLoaded,
    draftStatus, restore: restoreDraft, discard: discardDraft,
    commit: commitDraft,
  } = useFormDraft(FORM_KEY, data);
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

  const onUseCrewSetup = useCallback(() => {
    if (!crewSetupOffer) return;
    if (isProjectChange(crewSetupOffer, data.project_number)) {
      const ok = window.confirm(
        "Your saved setup is from a different project. Bring it in anyway?",
      );
      if (!ok) return;
    }
    setData((prev) => applySetupSnapshotToData(prev, crewSetupOffer));
    setCrewSetupOffer(null);
    toast.success("Loaded yesterday's crew setup. Review before submit.");
  }, [crewSetupOffer, data.project_number]);

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
      toast.error("GPS is not available on this device");
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
      patch({ gps_lat: latitude, gps_lng: longitude, gps_accuracy: accuracy });
      try {
        const rev = await reverseGeocode(latitude, longitude);
        if (rev) patch({ location: rev });
      } catch { /* silent */ }
      try {
        const wx = await fetchDailyWeather(latitude, longitude);
        if (wx?.summary) patch({ weather_summary: wx.summary, weather_snapshots: wx.snapshots || [] });
      } catch { /* silent */ }
    } catch (e) {
      toast.error("GPS unavailable — you can enter location manually");
    } finally {
      setFetchingGps(false);
    }
  }, [patch]);

  const refreshWeather = useCallback(async () => {
    if (!data.gps_lat || !data.gps_lng) return;
    setFetchingWeather(true);
    try {
      const wx = await fetchDailyWeather(data.gps_lat, data.gps_lng);
      if (wx?.summary) patch({ weather_summary: wx.summary, weather_snapshots: wx.snapshots || [] });
    } catch {
      toast.error("Weather refresh failed");
    } finally {
      setFetchingWeather(false);
    }
  }, [data.gps_lat, data.gps_lng, patch]);

  // ── Submit-readiness derivation ────────────────────────────
  const photoMin = data.photo_min || 6;
  const readiness = useMemo(() => {
    const items = [
      { key: "project", ok: !!data.project_name, label: "Project" },
      { key: "location", ok: !!data.location, label: "Location" },
      { key: "prepared_by", ok: !!data.prepared_by, label: "Prepared By" },
      {
        key: "photos",
        ok: (data.photos || []).length >= photoMin,
        label: `${photoMin} photos`,
      },
      { key: "signature", ok: !!data.prepared_by_signature, label: "Signature" },
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
        label: "Safety event type",
      });
      items.push({
        key: "safety_notified",
        ok: data.safety_notified === "Yes",
        label: "Safety contacted",
      });
      if (data.safety_notified === "Yes") {
        items.push({
          key: "safety_contact_person",
          ok: !!(data.safety_contact_person || "").trim(),
          label: "Who at Safety",
        });
        items.push({
          key: "safety_contact_time",
          ok: !!(data.safety_contact_time || "").trim(),
          label: "Time Safety contacted",
        });
      }
      items.push({
        key: "incident_report",
        ok: data.incident_report_filled === "Yes",
        label: "Incident report filed",
      });
      if (data.incident_report_filled === "Yes") {
        items.push({
          key: "incident_report_time",
          ok: !!(data.incident_report_time || "").trim(),
          label: "Time incident report filed",
        });
      }
    }
    const completed = items.filter((i) => i.ok).length;
    const missing = items.filter((i) => !i.ok).map((i) => i.label);
    return { items, total: items.length, completed, missing };
  }, [data, photoMin]);

  const canSubmit = readiness.completed === readiness.total;

  // ── Submit — same contract as V1, offline-safe via enqueueUpload ──
  const onSubmit = useCallback(async () => {
    if (saving) return;
    if (!canSubmit) {
      toast.error(`Missing: ${readiness.missing.join(", ")}`);
      return;
    }
    setSaving(true);
    const idem = idempotencyKeyRef.current || mintIdempotencyKey();
    const payload = { ...data, submit_language: "en", ui_shell: "v3" };
    try {
      if (online) {
        // Online: submit inline and commit the draft on success.
        const { data: saved } = await api.post("/daily-reports", payload, {
          headers: { "Idempotency-Key": idem },
        });
        try { saveCrewSetup(extractSetupSnapshot(payload)); } catch { /* silent */ }
        await commitDraft();
        toast.success("Daily report submitted.");
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
        toast("Queued — will send when connection returns.");
        navigate(publicMode ? "/thank-you?queued=1" : "/admin/daily");
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Submit failed. Please retry.");
    } finally {
      setSaving(false);
    }
  }, [saving, canSubmit, data, online, publicMode, navigate, readiness.missing, commitDraft]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* TRACK 23.4A · MASCI platform banner restored on V3 to match
          V1 / V2 field surfaces (bg-slate-900 · red-700 bottom border ·
          sticky). Keeps the "field form belongs to the platform" grammar. */}
      <DailyReportTopBanner backLink="/" showBackLink={!publicMode}>
        <div className="flex items-center gap-2" data-testid="dr-v3-header-chips">
          {!online && (
            <span
              data-testid="dr-v3-offline-chip"
              className="rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900"
            >
              Offline
            </span>
          )}
          <div data-testid="dr-v3-draft-pill-slot">
            <DraftStatusPill
              status={draftStatus}
              lastSavedAt={pendingSavedAt}
              testId="dr-v3-draft-pill"
            />
            {(draftStatus === "idle" && !pendingSavedAt) && (
              <span
                data-testid="dr-v3-draft-pill"
                className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-100 border border-slate-700"
              >
                Autosave on
              </span>
            )}
          </div>
        </div>
      </DailyReportTopBanner>

      <div className="mx-auto max-w-3xl px-4 py-6 sm:py-10">
        <header className="mb-6 sm:mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-600">
            <CheckCircle2 className="h-4 w-4" />
            MASCI · Daily Job Report
          </div>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Today&apos;s report
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Nine short steps. Dropdowns first. AI drafts your summary.
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
                <div className="font-medium">Use yesterday&apos;s crew setup?</div>
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
                Use setup
              </button>
              <button
                type="button"
                onClick={onDismissCrewSetup}
                data-testid="dr-v3-crew-setup-dismiss"
                className="rounded-md px-3 py-1.5 text-xs text-emerald-800 hover:bg-emerald-100"
              >
                Not today
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
            weatherLabel={data.weather_summary ? "Auto-loaded from GPS." : ""}
            reportNumberPreview={reportNumberPreview}
          />
          <SectionCrewEquipment data={data} patch={patch} costCodes={costCodes} />
          <SectionWorkProduction data={data} patch={patch} costCodes={costCodes} />
          <SectionMaterials data={data} patch={patch} costCodes={costCodes} />
          <SectionPhotos data={data} patch={patch} photoMin={photoMin} />
          <SectionImpactSafety data={data} patch={patch} />
          <SectionTomorrow data={data} patch={patch} />
          <SectionAiSummary
            data={data}
            reportId={reportId}
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
          />
        </div>
      </div>
    </div>
  );
}
