import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  MapPin,
  Plus,
  X,
  CloudSun,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import { Section } from "@/components/Section";
import { YesNo } from "@/components/YesNo";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { JobPicker } from "@/components/JobPicker";
import { LangToggle } from "@/components/LangToggle";
import { useT, getLang } from "@/lib/i18n";
import { buildDailyReportDefaults } from "@/lib/dailyReportSchema";
import { fetchDailyWeather } from "@/lib/weather";
import { api } from "@/lib/api";
import { translateUserInput } from "@/lib/translateOnSubmit";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";
const inputClsTall =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

// Generic add/remove/update helpers for repeating sections
const useList = (data, set, key) => ({
  add: (defaults = {}) =>
    set((p) => ({ ...p, [key]: [...p[key], { ...defaults }] })),
  remove: (i) =>
    set((p) => ({ ...p, [key]: p[key].filter((_, idx) => idx !== i) })),
  update: (i, field, value) =>
    set((p) => ({
      ...p,
      [key]: p[key].map((row, idx) =>
        idx === i ? { ...row, [field]: value } : row
      ),
    })),
});

export default function NewDailyReport({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(buildDailyReportDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [fetchingWeather, setFetchingWeather] = useState(false);

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));

  const applyJob = (job) => {
    setData((p) => ({
      ...p,
      project_name: job ? job.project_name : "",
      project_number: job ? job.project_number : "",
      location: p.location || (job && job.location) || "",
    }));
    if (job) toast.success(`Job loaded: #${job.project_number}`);
  };

  const useGps = async () => {
    setLocating(true);
    try {
      const pos = await getCurrentPosition();
      const { latitude, longitude, accuracy } = pos.coords;
      setData((p) => ({
        ...p,
        gps_lat: latitude,
        gps_lng: longitude,
        gps_accuracy: accuracy,
      }));
      try {
        const r = await reverseGeocode(latitude, longitude);
        setData((p) => ({ ...p, location: r.display }));
      } catch {
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
      }
      toast.success("GPS captured — fetching weather…");
      // Auto-fetch weather right after GPS lock
      try {
        setFetchingWeather(true);
        const w = await fetchDailyWeather(latitude, longitude, data.report_date);
        setData((p) => ({
          ...p,
          weather_summary: w.summary,
          weather_snapshots: w.snapshots,
        }));
        toast.success("Weather loaded");
      } catch (we) {
        console.error(we);
        toast.warning("GPS got, but weather lookup failed — fill manually");
      } finally {
        setFetchingWeather(false);
      }
    } catch (e) {
      toast.error(e?.message || "Could not get GPS location");
    } finally {
      setLocating(false);
    }
  };

  const refreshWeather = async () => {
    if (data.gps_lat == null) {
      toast.error("Capture GPS first");
      return;
    }
    setFetchingWeather(true);
    try {
      const w = await fetchDailyWeather(
        data.gps_lat,
        data.gps_lng,
        data.report_date
      );
      setData((p) => ({
        ...p,
        weather_summary: w.summary,
        weather_snapshots: w.snapshots,
      }));
      toast.success("Weather updated");
    } catch (e) {
      toast.error("Weather fetch failed");
    } finally {
      setFetchingWeather(false);
    }
  };

  const crews = useList(data, setData, "masci_crews");
  const subs = useList(data, setData, "subcontractors");
  const vis = useList(data, setData, "visitors");
  const eq = useList(data, setData, "equipment");
  const mat = useList(data, setData, "materials");
  const act = useList(data, setData, "activities");

  const validate = () => {
    if (!data.project_name.trim()) {
      toast.error("Project Name is required");
      return false;
    }
    if (!data.location.trim()) {
      toast.error("Location is required");
      return false;
    }
    if (!data.prepared_by.trim()) {
      toast.error("Prepared By is required");
      return false;
    }
    // Safety-escalation gate runs BEFORE photos/signature so a stop-the-line
    // event can never be hidden behind a missing-photos toast.
    const hasAccidentOrInjury =
      data.safety_incidents_today === "Yes" ||
      data.injuries_reported === "Yes";
    if (hasAccidentOrInjury) {
      if (data.safety_notified !== "Yes") {
        toast.error(
          "Safety must be notified before this Daily Report can be submitted"
        );
        return false;
      }
      if (!data.safety_contact_person.trim()) {
        toast.error("Who Was Contacted is required");
        return false;
      }
      if (!data.safety_contact_time.trim()) {
        toast.error("Time of Contact is required");
        return false;
      }
      if (data.incident_report_filled !== "Yes") {
        toast.error(
          "An Accident/Incident Report must be filed before this Daily Report can be submitted"
        );
        return false;
      }
      if (!data.incident_report_time.trim()) {
        toast.error("Time the Incident Report was filed is required");
        return false;
      }
    }
    if ((data.photos || []).length < (data.photo_min || 6)) {
      toast.error(
        `At least ${data.photo_min || 6} photos are required (you have ${
          (data.photos || []).length
        })`
      );
      return false;
    }
    if (!data.prepared_by_signature) {
      toast.error("Signature is required");
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const lang = getLang();
      let payload = data;
      if (lang === "es") {
        toast.info("Translating to English…");
        payload = await translateUserInput(data, "es");
      }
      const res = await api.post("/daily-reports", payload);
      toast.success("Daily report saved");
      if (publicMode) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            formType: "Daily Report",
            returnTo: "/daily/submit",
          },
          replace: true,
        });
      } else {
        navigate(`/daily/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error("Could not save daily report");
    } finally {
      setSaving(false);
    }
  };

  // Reusable repeat-row renderer
  const RepeatBlock = ({ title, list, helpers, defaults, fields, testIdBase }) => (
    <div className="space-y-3">
      {data[list].map((row, i) => (
        <div
          key={i}
          className="border-2 border-slate-200 rounded-md p-3 sm:p-4 space-y-2"
          data-testid={`${testIdBase}-row-${i}`}
        >
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
              {title} {i + 1}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => helpers.remove(i)}
              className="text-slate-500 hover:text-red-600"
              data-testid={`${testIdBase}-remove-${i}`}
            >
              <X className="w-4 h-4 mr-1" /> {t("Remove")}
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {fields.map((f) => (
              <div
                key={f.key}
                className={f.full ? "sm:col-span-2" : ""}
                style={f.style}
              >
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                  {t(f.label)}
                </Label>
                {f.type === "textarea" ? (
                  <Textarea
                    value={row[f.key] || ""}
                    onChange={(e) => helpers.update(i, f.key, e.target.value)}
                    className="min-h-[60px] text-base border-2 border-slate-300"
                    placeholder={f.placeholder}
                    data-testid={`${testIdBase}-${f.key}-${i}`}
                  />
                ) : (
                  <Input
                    type={f.type || "text"}
                    value={row[f.key] || ""}
                    onChange={(e) => helpers.update(i, f.key, e.target.value)}
                    className={inputCls}
                    placeholder={f.placeholder}
                    data-testid={`${testIdBase}-${f.key}-${i}`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        onClick={() => helpers.add(defaults)}
        className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
        data-testid={`${testIdBase}-add`}
      >
        <Plus className="w-4 h-4 mr-2" /> {t("Add")} {title}
      </Button>
    </div>
  );

  const photosCount = (data.photos || []).length;
  const photoMin = data.photo_min || 6;

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          {publicMode ? (
            <MasciLogo variant="lockup" size="lg" className="hidden sm:block" onDark />
          ) : (
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
            </Link>
          )}
          <MasciLogo
            variant="mark"
            size="md"
            className={publicMode ? "sm:hidden" : ""}
          />
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={submit}
              disabled={saving}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="submit-top-btn"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-1" />
              )}
              {t("Submit")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
        <div className="mb-2">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            {t("New Report")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("Daily Job Report")}
          </h1>
        </div>

        {/* 01 — Report info */}
        <Section number="01" title={t("Report Information")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("MASCI Job")}
            </Label>
            <div className="mt-2">
              <JobPicker
                projectName={data.project_name}
                projectNumber={data.project_number}
                onSelect={applyJob}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1.5">
              {t("Pick a current job to auto-fill name + number — or choose Custom Job to type your own.")}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Project Name *")}
              </Label>
              <Input
                value={data.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                className={inputClsTall}
                data-testid="input-project-name"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Project Number")}
              </Label>
              <Input
                value={data.project_number}
                onChange={(e) => set("project_number", e.target.value)}
                className={inputClsTall}
                data-testid="input-project-number"
              />
            </div>
            <div className="sm:col-span-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Location *")}
                </Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={useGps}
                  disabled={locating}
                  className="h-9 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
                  data-testid="use-gps-btn"
                >
                  {locating ? (
                    <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                  ) : (
                    <MapPin className="w-3.5 h-3.5 mr-1" />
                  )}
                  {t("Use GPS")}
                </Button>
              </div>
              <Input
                value={data.location}
                onChange={(e) => set("location", e.target.value)}
                className={inputClsTall}
                data-testid="input-location"
              />
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Date *")}
              </Label>
              <Input
                type="date"
                value={data.report_date}
                onChange={(e) => set("report_date", e.target.value)}
                className={inputClsTall}
                data-testid="input-report-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Report #")}
              </Label>
              <Input
                value={data.report_number}
                onChange={(e) => set("report_number", e.target.value)}
                className={inputClsTall}
                placeholder="optional"
                data-testid="input-report-number"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Prepared By *")}
              </Label>
              <Input
                value={data.prepared_by}
                onChange={(e) => set("prepared_by", e.target.value)}
                className={inputClsTall}
                placeholder={t("Foreman / Superintendent")}
                data-testid="input-prepared-by"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Superintendent")}
              </Label>
              <Input
                value={data.superintendent}
                onChange={(e) => set("superintendent", e.target.value)}
                className={inputClsTall}
                data-testid="input-superintendent"
              />
            </div>
          </div>
        </Section>

        {/* 02 — Weather (auto from GPS) */}
        <Section
          number="02"
          title={t("Weather")}
          aside={
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={refreshWeather}
              disabled={fetchingWeather || data.gps_lat == null}
              className="h-9 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
              data-testid="refresh-weather-btn"
            >
              {fetchingWeather ? (
                <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              ) : (
                <CloudSun className="w-3.5 h-3.5 mr-1" />
              )}
              {t("Refresh Weather")}
            </Button>
          }
        >
          <p className="text-xs text-slate-500">
            {t("Capture GPS to auto-load today's weather. Refresh anytime.")}
          </p>
          {data.weather_snapshots.length === 0 ? (
            <div className="text-sm text-slate-500 italic py-2">
              {t("No weather data yet — tap Use GPS above.")}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {data.weather_snapshots.map((s, i) => (
                <div
                  key={i}
                  className="border-2 border-slate-200 rounded-md p-3"
                  data-testid={`weather-snap-${i}`}
                >
                  <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold">
                    {s.time}
                  </div>
                  <div className="font-display font-bold text-2xl text-slate-900 mt-1">
                    {s.temp_f != null ? `${s.temp_f}°F` : "—"}
                  </div>
                  <div className="text-sm text-slate-700 mt-0.5">
                    {s.condition || "—"}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {s.precip_in ?? 0}″ · {s.humidity_pct ?? "—"}% ·{" "}
                    {s.wind_mph ?? "—"} mph
                  </div>
                </div>
              ))}
            </div>
          )}
          {data.weather_summary && (
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600 mt-2">
              {data.weather_summary}
            </div>
          )}
        </Section>

        {/* 03 — General Info / Flags */}
        <Section number="03" title={t("General Information")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Schedule Delays Today?")}
              </Label>
              <YesNo
                value={data.schedule_delays}
                onChange={(v) => set("schedule_delays", v)}
                testId="schedule-delays"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Weather Impact?")}
              </Label>
              <YesNo
                value={data.weather_impact}
                onChange={(v) => set("weather_impact", v)}
                testId="weather-impact"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Any Accidents on Site?")}
              </Label>
              <YesNo
                value={data.safety_incidents_today}
                onChange={(v) => set("safety_incidents_today", v)}
                testId="safety-incidents"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Any Injuries Reported?")}
              </Label>
              <YesNo
                value={data.injuries_reported}
                onChange={(v) => set("injuries_reported", v)}
                testId="injuries-reported"
              />
            </div>
          </div>
          {(data.schedule_delays === "Yes" ||
            data.weather_impact === "Yes" ||
            data.safety_incidents_today === "Yes" ||
            data.injuries_reported === "Yes") && (
            <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-3">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-amber-800 font-bold">
                <AlertTriangle className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
                {t("Detail any 'Yes' answers")}
              </Label>
              <Textarea
                value={data.incident_notes}
                onChange={(e) => set("incident_notes", e.target.value)}
                className="min-h-[80px] text-base border-2 border-amber-300 mt-1"
                placeholder={t("Describe delays, weather impact, accidents, injuries...")}
                data-testid="input-incident-notes"
              />
            </div>
          )}
          {/* Safety-escalation gate — fires whenever accident or injury is Yes */}
          {(data.safety_incidents_today === "Yes" ||
            data.injuries_reported === "Yes") && (
            <div
              className="bg-red-50 border-2 border-red-600 rounded-md p-4 space-y-4"
              data-testid="safety-escalation-block"
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-700 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                    {t("Safety Escalation Required")}
                  </div>
                  <div className="text-sm text-slate-800 mt-1">
                    {t(
                      "An accident or injury was reported today. Complete the safety escalation steps before submitting this report."
                    )}
                  </div>
                </div>
              </div>

              {/* Step 1: Was Safety Notified? */}
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800 font-bold">
                  {t("Was Safety notified? *")}
                </Label>
                <YesNo
                  value={data.safety_notified}
                  onChange={(v) => set("safety_notified", v)}
                  testId="safety-notified"
                />
              </div>

              {/* Stop-the-line: Safety must be contacted */}
              {data.safety_notified === "No" && (
                <div
                  className="bg-red-700 text-white rounded-md p-4 border-b-4 border-red-900"
                  data-testid="safety-not-notified-warning"
                >
                  <div className="font-display font-black text-lg leading-tight">
                    {t("STOP — Contact Safety immediately.")}
                  </div>
                  <div className="text-sm mt-1 text-red-100">
                    {t(
                      "You cannot submit this Daily Report until Safety has been notified. Call your Safety Manager now, then return and mark Yes above."
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Who and when? */}
              {data.safety_notified === "Yes" && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Who Was Contacted? *")}
                    </Label>
                    <Input
                      value={data.safety_contact_person}
                      onChange={(e) =>
                        set("safety_contact_person", e.target.value)
                      }
                      placeholder={t("Name + role (e.g. Jaymn Judd, Safety Mgr)")}
                      className={inputCls}
                      data-testid="input-safety-contact-person"
                    />
                  </div>
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Time of Contact *")}
                    </Label>
                    <Input
                      type="time"
                      value={data.safety_contact_time}
                      onChange={(e) =>
                        set("safety_contact_time", e.target.value)
                      }
                      className={inputCls}
                      data-testid="input-safety-contact-time"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Was the Incident Report filed? */}
              {data.safety_notified === "Yes" && (
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800 font-bold">
                    {t("Has the Accident/Incident Report been filled out? *")}
                  </Label>
                  <YesNo
                    value={data.incident_report_filled}
                    onChange={(v) => set("incident_report_filled", v)}
                    testId="incident-report-filled"
                  />
                </div>
              )}

              {/* Stop-the-line: Incident report must be filed */}
              {data.safety_notified === "Yes" &&
                data.incident_report_filled === "No" && (
                  <div
                    className="bg-red-700 text-white rounded-md p-4 border-b-4 border-red-900"
                    data-testid="incident-report-required-warning"
                  >
                    <div className="font-display font-black text-lg leading-tight">
                      {t("STOP — File the Incident Report first.")}
                    </div>
                    <div className="text-sm mt-1 text-red-100">
                      {t(
                        "An Accident/Incident Report MUST be filed before this Daily Report can be submitted."
                      )}
                    </div>
                    <Link
                      to="/incidents/new"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-3 px-3 py-2 bg-white text-red-800 hover:bg-red-100 font-mono text-xs uppercase tracking-[0.2em] font-bold rounded"
                      data-testid="open-incident-form-link"
                    >
                      {t("Open Incident Report Form")}
                    </Link>
                  </div>
                )}

              {/* Step 4: Time the Incident Report was filed */}
              {data.safety_notified === "Yes" &&
                data.incident_report_filled === "Yes" && (
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Time Incident Report Was Filed *")}
                    </Label>
                    <Input
                      type="time"
                      value={data.incident_report_time}
                      onChange={(e) =>
                        set("incident_report_time", e.target.value)
                      }
                      className={inputCls}
                      data-testid="input-incident-report-time"
                    />
                  </div>
                )}
            </div>
          )}
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("General Notes")}
            </Label>
            <Textarea
              value={data.general_notes}
              onChange={(e) => set("general_notes", e.target.value)}
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder={t("Anything else worth noting from today...")}
              data-testid="input-general-notes"
            />
          </div>
        </Section>

        {/* 04 — MASCI Crews */}
        <Section number="04" title={t("MASCI Crews on Site")}>
          <RepeatBlock
            title={t("Crew")}
            list="masci_crews"
            helpers={crews}
            defaults={{
              trade: "",
              foreman: "",
              count: "",
              hours: "",
              work_performed: "",
            }}
            fields={[
              { key: "trade", label: "Trade", placeholder: "Earthwork, Concrete, MOT..." },
              { key: "foreman", label: "Foreman" },
              { key: "count", label: "# of Workers", type: "number" },
              { key: "hours", label: "Hours Worked", type: "number" },
              {
                key: "work_performed",
                label: "Work Performed",
                full: true,
                type: "textarea",
              },
            ]}
            testIdBase="crew"
          />
        </Section>

        {/* 05 — Subcontractors */}
        <Section number="05" title={t("Subcontractors on Site")}>
          <RepeatBlock
            title={t("Subcontractor")}
            list="subcontractors"
            helpers={subs}
            defaults={{
              company: "",
              trade: "",
              foreman: "",
              count: "",
              hours: "",
              work_performed: "",
            }}
            fields={[
              { key: "company", label: "Company" },
              { key: "trade", label: "Trade" },
              { key: "foreman", label: "Foreman / Lead" },
              { key: "count", label: "# of Workers", type: "number" },
              { key: "hours", label: "Hours Worked", type: "number" },
              {
                key: "work_performed",
                label: "Work Performed",
                full: true,
                type: "textarea",
              },
            ]}
            testIdBase="sub"
          />
        </Section>

        {/* 06 — Visitors */}
        <Section number="06" title={t("Site Visitors")}>
          <RepeatBlock
            title={t("Visitor")}
            list="visitors"
            helpers={vis}
            defaults={{
              name: "",
              company: "",
              time_in: "",
              time_out: "",
              purpose: "",
            }}
            fields={[
              { key: "name", label: "Name" },
              { key: "company", label: "Company / Agency" },
              { key: "time_in", label: "Time In", type: "time" },
              { key: "time_out", label: "Time Out", type: "time" },
              { key: "purpose", label: "Purpose / Notes", full: true },
            ]}
            testIdBase="visitor"
          />
        </Section>

        {/* 07 — Equipment */}
        <Section number="07" title={t("Equipment Log")}>
          <RepeatBlock
            title={t("Equipment")}
            list="equipment"
            helpers={eq}
            defaults={{
              description: "",
              hours_used: "",
              time_delivered: "",
              time_removed: "",
              notes: "",
            }}
            fields={[
              { key: "description", label: "Description / ID", full: true },
              { key: "hours_used", label: "Hours Used", type: "number" },
              { key: "time_delivered", label: "Time Delivered", type: "time" },
              { key: "time_removed", label: "Time Removed", type: "time" },
              { key: "notes", label: "Notes", full: true, type: "textarea" },
            ]}
            testIdBase="equipment"
          />
        </Section>

        {/* 08 — Materials */}
        <Section number="08" title={t("Material Deliveries")}>
          <RepeatBlock
            title={t("Material")}
            list="materials"
            helpers={mat}
            defaults={{
              description: "",
              quantity: "",
              unit: "",
              supplier: "",
              ticket_number: "",
              notes: "",
            }}
            fields={[
              { key: "description", label: "Description", full: true },
              { key: "quantity", label: "Quantity" },
              { key: "unit", label: "Unit", placeholder: "ton, cy, ea, lf" },
              { key: "supplier", label: "Supplier" },
              { key: "ticket_number", label: "Ticket #" },
              { key: "notes", label: "Notes", full: true, type: "textarea" },
            ]}
            testIdBase="material"
          />
        </Section>

        {/* 09 — Activity Log */}
        <Section number="09" title={t("Activity / Production Log")}>
          <RepeatBlock
            title={t("Activity")}
            list="activities"
            helpers={act}
            defaults={{
              activity: "",
              percent_complete: "",
              station_from: "",
              station_to: "",
              notes: "",
            }}
            fields={[
              { key: "activity", label: "Activity", full: true },
              { key: "percent_complete", label: "% Complete", type: "number" },
              { key: "station_from", label: "Station / Loc From" },
              { key: "station_to", label: "Station / Loc To" },
              { key: "notes", label: "Notes", full: true, type: "textarea" },
            ]}
            testIdBase="activity"
          />
        </Section>

        {/* 10 — Photos (min 6) */}
        <Section
          number="10"
          title={`${t("Photos")} (${photosCount}/${photoMin}${
            photosCount > photoMin ? "+" : ""
          })`}
        >
          <div
            className={`px-3 py-2 rounded-md border-2 ${
              photosCount >= photoMin
                ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                : "border-amber-300 bg-amber-50 text-amber-900"
            } font-mono text-xs uppercase tracking-[0.15em] font-bold`}
            data-testid="photos-status"
          >
            {photosCount >= photoMin
              ? t("Photo minimum met. Add more if helpful.")
              : `${t("Add at least")} ${photoMin - photosCount} ${t("more photo(s)")}`}
          </div>
          <PhotoUpload
            photos={data.photos}
            onChange={(photos) => set("photos", photos)}
          />
        </Section>

        {/* 11 — Sign-off */}
        <Section number="11" title={t("Sign-Off")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Prepared By Signature")} *
            </Label>
            <SignaturePad
              value={data.prepared_by_signature}
              onChange={(v) => set("prepared_by_signature", v)}
              label={t("Prepared By")}
              testId="prepared-by-sig"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Superintendent Signature")}
            </Label>
            <SignaturePad
              value={data.superintendent_signature}
              onChange={(v) => set("superintendent_signature", v)}
              label={t("Superintendent")}
              testId="superintendent-sig"
            />
          </div>
        </Section>

        <div className="pt-4">
          <Button
            onClick={submit}
            disabled={saving}
            className="w-full h-16 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-base sm:text-lg border-b-4 border-red-900"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />{" "}
                {t("Saving Report...")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" /> {t("Submit Daily Report")}
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}
