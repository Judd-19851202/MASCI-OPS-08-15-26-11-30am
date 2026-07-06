// TRACK 23.1 · V3 Daily Report page shell.
//
// Elite, field-first replacement for `NewDailyReport.jsx`. Composes
// the 9 section components. Submits via the same canonical endpoint
// (`POST /api/daily-reports`) with the same payload contract — so
// PM/ODS/Trust Spine/email/PDF continue to work byte-identically.
//
// The flag hook (`useDailyReportV3Flag`) is consulted by AppRoutes
// to decide whether this shell or the V1 shell renders at
// `/daily/new`. This file itself never checks the flag — it's already
// running.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { buildDailyReportDefaults } from "@/lib/dailyReportSchema";
import { reverseGeocode } from "@/lib/geolocation";
import { fetchDailyWeather } from "@/lib/weather";
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
import { CheckCircle2 } from "lucide-react";

export default function NewDailyReportV3({ publicMode = false }) {
  const navigate = useNavigate();
  const [data, setData] = useState(() => buildDailyReportDefaults());
  const [reportId, setReportId] = useState("");
  const [saving, setSaving] = useState(false);
  const [isFetchingGps, setFetchingGps] = useState(false);
  const [isFetchingWeather, setFetchingWeather] = useState(false);
  const [costCodes, setCostCodes] = useState([]);
  const [reportNumberPreview, setReportNumberPreview] = useState("");

  const patch = useCallback((delta) => {
    setData((prev) => ({ ...prev, ...delta }));
  }, []);

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
    // Safety escalation hard blockers if safety_present=Yes
    if (data.safety_present === "Yes") {
      items.push({ key: "safety_notified", ok: data.safety_notified === "Yes", label: "Safety contacted" });
      items.push({
        key: "incident_report",
        ok: data.incident_report_filled === "Yes",
        label: "Incident report",
      });
    }
    const completed = items.filter((i) => i.ok).length;
    const missing = items.filter((i) => !i.ok).map((i) => i.label);
    return { items, total: items.length, completed, missing };
  }, [data, photoMin]);

  const canSubmit = readiness.completed === readiness.total;

  // ── Submit — same contract as V1 (`POST /api/daily-reports`) ──
  const onSubmit = useCallback(async () => {
    if (saving) return;
    if (!canSubmit) {
      toast.error(`Missing: ${readiness.missing.join(", ")}`);
      return;
    }
    setSaving(true);
    // Preserve payload keys that V1 sends but V3 UI doesn't collect.
    const payload = { ...data, submit_language: "en", ui_shell: "v3" };
    try {
      const { data: saved } = await api.post("/daily-reports", payload);
      toast.success("Daily report submitted.");
      if (publicMode) {
        navigate("/thank-you");
      } else if (saved?.id) {
        navigate(`/daily/${saved.id}`);
      } else {
        navigate("/admin/daily");
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Submit failed. Please retry.");
    } finally {
      setSaving(false);
    }
  }, [saving, canSubmit, data, publicMode, navigate, readiness.missing]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-4 py-6 sm:py-10">
        <header className="mb-6 sm:mb-8">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-600">
            <CheckCircle2 className="h-4 w-4" />
            MASCI · Daily Job Report · V3
          </div>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Today&apos;s report
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Nine short steps. Dropdowns first. AI drafts your summary.
          </p>
        </header>

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
