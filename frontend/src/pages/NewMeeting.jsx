import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Save, Loader2, MapPin, UserPlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import { Section } from "@/components/Section";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { TopicPicker } from "@/components/TopicPicker";
import { JobPicker } from "@/components/JobPicker";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { LangToggle } from "@/components/LangToggle";
import { BilingualConsent } from "@/components/BilingualConsent";
import { useT, getLang } from "@/lib/i18n";
import { formatApiError } from "@/lib/apiErrors";
import { TOPIC_CATEGORIES, SHIFT_OPTIONS, WEATHER_OPTIONS, buildMeetingDefaults } from "@/lib/meetingSchema";
import { TOPIC_LIBRARY, CUSTOM_TOPIC_KEY, findTopic } from "@/lib/topics";
import { TOPIC_LIBRARY_ES } from "@/lib/topics/index.es";
import { getDomainLabel } from "@/components/TopicPicker";
import { composeIncidentScaffold } from "@/lib/composeIncidentScaffold";
import { splitIncidentScaffold } from "@/lib/splitIncidentScaffold";
import { HelpTipBlock } from "@/components/HelpTip";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export default function NewMeeting({ publicMode = false }) {
  const navigate = useNavigate();
  const { t, lang } = useT();
  const [data, setData] = useState(buildMeetingDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [templateKey, setTemplateKey] = useState(CUSTOM_TOPIC_KEY);

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));

  const applyJob = (job) => {
    setData((p) => ({
      ...p,
      project_name: job ? job.project_name : "",
      project_number: job ? job.project_number : "",
      // Only prefill location if user hasn't entered one yet
      location: p.location || (job && job.location) || "",
    }));
    if (job) toast.success(t("Job loaded: #{n}").replace("{n}", job.project_number));
  };

  const applyTemplate = (key) => {
    setTemplateKey(key);
    if (key === CUSTOM_TOPIC_KEY) {
      // Clear prefilled fields so they can write their own
      setData((p) => ({
        ...p,
        topic: "",
        topic_category: "Hazard-Specific",
        hazards_reviewed: "",
        discussion_notes: "",
        references_cited: "",
        action_items: "",
        topic_template_key: CUSTOM_TOPIC_KEY,
      }));
      toast.info(t("Custom topic — all topic fields cleared."));
      return;
    }
    const tpl = findTopic(key);
    if (!tpl) return;
    // Use Spanish version if user is in ES, else English canonical.
    const es = lang === "es" ? TOPIC_LIBRARY_ES[key] : null;
    // If the topic carries an incident_pattern, prepend it to the
    // discussion notes as a labelled "real-world pattern" paragraph
    // so the driver/foreman reads the story before the bullets.
    // The field stays freely editable in the textarea below.
    const enNotes = composeIncidentScaffold(
      tpl.incident_pattern,
      tpl.discussion_notes,
      false
    );
    const esNotes = es
      ? composeIncidentScaffold(es.incident_pattern, es.discussion_notes, true)
      : null;
    setData((p) => ({
      ...p,
      topic: es?.title || tpl.title,
      topic_category: tpl.category,
      hazards_reviewed: es?.hazards_reviewed || tpl.hazards_reviewed,
      discussion_notes: esNotes || enNotes,
      references_cited: es?.references_cited || tpl.references_cited,
      action_items: es?.action_items || tpl.action_items,
      topic_template_key: tpl.key,
    }));
    toast.success(
      lang === "es" && es
        ? `Cargado "${es.title}" — todos los campos editables.`
        : `Loaded "${tpl.title}" — all fields are editable.`
    );
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
        toast.success(t("Location captured from GPS"));
      } catch {
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
        toast.warning(t("Got GPS coordinates, but couldn't look up address"));
      }
    } catch (e) {
      toast.error(e?.message || t("Could not get GPS location"));
    } finally {
      setLocating(false);
    }
  };

  const addAttendee = () => {
    // SAFETY-MEETING-CERT · block adding a new row until current row is complete.
    const last = data.attendees[data.attendees.length - 1];
    if (last) {
      const incomplete = isAttendeeIncomplete(last);
      if (incomplete) {
        toast.error(t("Complete the current attendee before adding another: {missing}").replace("{missing}", incomplete));
        return;
      }
    }
    setData((p) => ({
      ...p,
      attendees: [...p.attendees, {
        name: "", employee_id: "", non_masci: false,
        company: "", trade: "", signature: "",
        acknowledged: false, acknowledged_at: "",
      }],
    }));
  };
  const updateAttendee = (i, k, v) =>
    setData((p) => ({
      ...p,
      attendees: p.attendees.map((a, idx) => (idx === i ? { ...a, [k]: v } : a)),
    }));
  const removeAttendee = (i) =>
    setData((p) => ({
      ...p,
      attendees: p.attendees.filter((_, idx) => idx !== i),
    }));

  // SAFETY-MEETING-CERT · attendee completeness gate.
  // Returns "" when complete, otherwise the human-readable missing-field label.
  const isAttendeeIncomplete = (a) => {
    if (!a) return "";
    if (!String(a.name || "").trim()) return t("name");
    if (!String(a.company || "").trim()) return t("company");
    if (!a.signature) return t("signature");
    if (!a.acknowledged) return t("acknowledgement");
    return "";
  };

  const validate = () => {
    const required = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["meeting_date", "Date"],
      ["meeting_time", "Time"],
      ["conducted_by", "Conducted By"],
      ["topic", "Topic"],
    ];
    for (const [k, l] of required) {
      if (!String(data[k] || "").trim()) {
        toast.error(t("{field} is required").replace("{field}", t(l)));
        return false;
      }
    }
    if (!data.conductor_signature) {
      toast.error(t("Conductor signature is required"));
      return false;
    }
    if (data.attendees.length === 0) {
      toast.error(t("Add at least one attendee"));
      return false;
    }
    // SAFETY-MEETING-CERT · every attendee row must be complete.
    for (let i = 0; i < data.attendees.length; i += 1) {
      const missing = isAttendeeIncomplete(data.attendees[i]);
      if (missing) {
        toast.error(t("Attendee {n}: {field} required").replace("{n}", i + 1).replace("{field}", missing));
        return false;
      }
    }
    // Photos required — toolbox-talk photos confirm the meeting actually
    // happened (group shot + topic board). 2-photo minimum.
    if ((data.photos || []).length < 2) {
      toast.error(
        `${t("Minimum 2 photos required.")} (${(data.photos || []).length}/2)`
      );
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);

    // If a template is loaded AND user is in ES, swap unedited Spanish
    // template content back to the English canonical so the saved record
    // stays English. User-edited fields are preserved as typed.
    let payload = data;
    if (templateKey !== CUSTOM_TOPIC_KEY) {
      const tpl = findTopic(templateKey);
      const es = TOPIC_LIBRARY_ES[templateKey];
      if (tpl && es) {
        const swapIfPristine = (currentVal, esVal, enVal) =>
          currentVal === esVal ? enVal : currentVal;
        // Mirror the scaffold composition used at template-load time so
        // an unedited bilingual discussion_notes (with the incident
        // pattern header prepended) swaps cleanly back to the English
        // canonical composed form on submit.
        const esComposedNotes = composeIncidentScaffold(
          es.incident_pattern,
          es.discussion_notes,
          true
        );
        const enComposedNotes = composeIncidentScaffold(
          tpl.incident_pattern,
          tpl.discussion_notes,
          false
        );
        payload = {
          ...data,
          topic: swapIfPristine(data.topic, es.title, tpl.title),
          hazards_reviewed: swapIfPristine(
            data.hazards_reviewed,
            es.hazards_reviewed,
            tpl.hazards_reviewed
          ),
          discussion_notes: swapIfPristine(
            data.discussion_notes,
            esComposedNotes,
            enComposedNotes
          ),
          references_cited: swapIfPristine(
            data.references_cited,
            es.references_cited,
            tpl.references_cited
          ),
          action_items: swapIfPristine(
            data.action_items,
            es.action_items,
            tpl.action_items
          ),
        };
      }
    }

    try {
      const lang = getLang();
      if (lang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
      const res = await api.post("/meetings", payload);
      toast.success(t("Meeting saved"));
      if (publicMode || !isAdmin()) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            formType: "Site Safety Meeting",
            returnTo: "/meetings/submit",
            recordId: res.data?.meeting_number || res.data?.id || "",
          },
          replace: true,
        });
      } else {
        navigate(`/meetings/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error(formatApiError(e, t("Could not save meeting")), { duration: 7000 });
    } finally {
      setSaving(false);
    }
  };

  // 5:30 AM iPad rule · derive a short, human hint of what's blocking Submit
  // so the sticky top button and the bottom CTA never sit silently disabled.
  const missingHint = (() => {
    if (saving) return "";
    const need = [];
    const fields = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["meeting_date", "Date"],
      ["meeting_time", "Time"],
      ["conducted_by", "Conducted By"],
      ["topic", "Topic"],
    ];
    for (const [k, l] of fields) {
      if (!String(data[k] || "").trim()) need.push(t(l));
    }
    if (!data.conductor_signature) need.push(t("Conductor Signature"));
    if (!data.attendees || data.attendees.length === 0) need.push(t("Attendees"));
    const photoCount = (data.photos || []).length;
    if (photoCount < 2) need.push(`${t("Photos")} ${photoCount}/2`);
    if (need.length === 0) return "";
    return need.slice(0, 3).join(" · ") + (need.length > 3 ? ` +${need.length - 3}` : "");
  })();

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          {publicMode ? (
            <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          ) : (
            <Link
              to="/"
              className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Home
            </Link>
          )}
          <MasciLogo variant="mark" size="md" className={publicMode ? "sm:hidden" : ""} homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            {missingHint && (
              <span
                data-testid="meeting-submit-missing-hint"
                className="hidden sm:inline-block max-w-[260px] truncate px-2 py-1 text-[10px] font-mono uppercase tracking-wider bg-amber-100 text-amber-900 border border-amber-300 rounded"
                title={`${t("To submit, complete")}: ${missingHint}`}
              >
                {t("Missing")}: {missingHint}
              </span>
            )}
            <Button
              onClick={submit}
              disabled={saving}
              title={missingHint ? `${t("To submit, complete")}: ${missingHint}` : ""}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:opacity-60"
              data-testid="submit-top-btn"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
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
            {t("Site Safety Meeting")}
          </h1>
        </div>

        <Section number="01" title={t("Meeting Information")}>
          {/* iter270 · form-root coaching · counter shown above the meeting form */}
          <HelpTipBlock formKey="meeting" className="mb-3" showCounter />
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Project Name *")}
              </Label>
              <Input
                value={data.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                className={inputCls}
                placeholder="e.g. I-95 Resurfacing - Phase 2"
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
                className={inputCls}
                data-testid="input-project-number"
              />
            </div>
            <div className="lg:col-span-2">
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
                className={inputCls}
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
                value={data.meeting_date}
                onChange={(e) => set("meeting_date", e.target.value)}
                className={inputCls}
                data-testid="input-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Time *")}
              </Label>
              <Input
                type="time"
                value={data.meeting_time}
                onChange={(e) => set("meeting_time", e.target.value)}
                className={inputCls}
                data-testid="input-time"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Conducted By *")}
              </Label>
              <Input
                value={data.conducted_by}
                onChange={(e) => set("conducted_by", e.target.value)}
                className={inputCls}
                placeholder={t("Foreman / Supervisor")}
                data-testid="input-conducted-by"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Topic Category *")}
              </Label>
              <Select
                value={data.topic_category}
                onValueChange={(v) => set("topic_category", v)}
              >
                <SelectTrigger className={inputCls} data-testid="select-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TOPIC_CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {t(c)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[10px] font-mono text-slate-500 mt-1">
                {t("Auto-fills when you pick a topic below")}
              </p>
            </div>
          </div>

          {/* E1 · operational context captures (crew, shift, weather,
              subcontractor, high-risk flag). Lightweight, single-tap. */}
          {/* iter270 · Section 01 context coaching (crew/shift/weather/high-risk) */}
          <HelpTipBlock formKey="meeting.context" className="mt-6 mb-3" />
          <div
            className="mt-2 pt-6 border-t border-slate-200 grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4"
            data-testid="meeting-context-row"
          >
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Crew Size")}
              </Label>
              <Input
                type="number"
                min="0"
                inputMode="numeric"
                value={data.crew_size ?? ""}
                onChange={(e) => {
                  const v = e.target.value;
                  set("crew_size", v === "" ? null : Math.max(0, parseInt(v, 10) || 0));
                }}
                className={inputCls}
                placeholder={t("Total on crew today")}
                data-testid="input-crew-size"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Shift")}
              </Label>
              <Select value={data.shift || ""} onValueChange={(v) => set("shift", v)}>
                <SelectTrigger className={inputCls} data-testid="select-shift">
                  <SelectValue placeholder={t("Select shift")} />
                </SelectTrigger>
                <SelectContent>
                  {SHIFT_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {lang === "es"
                        ? { Day: "Día", Swing: "Tarde", Night: "Noche" }[s]
                        : s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-1 flex items-end">
              <label
                className="flex items-center gap-2 h-14 cursor-pointer select-none"
                data-testid="toggle-high-risk-label"
              >
                <input
                  type="checkbox"
                  checked={!!data.high_risk_activity}
                  onChange={(e) => set("high_risk_activity", e.target.checked)}
                  className="w-5 h-5 accent-red-700"
                  data-testid="toggle-high-risk"
                />
                <span className="text-sm font-medium text-slate-900">
                  {t("High-risk activity today")}
                </span>
              </label>
            </div>
          </div>

          {/* Weather chip row */}
          <div className="mt-4">
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Weather")}
            </Label>
            <div
              className="mt-2 flex flex-wrap gap-2"
              data-testid="meeting-weather-chips"
            >
              {WEATHER_OPTIONS.map((w) => {
                const active = (data.weather || []).includes(w.key);
                return (
                  <button
                    key={w.key}
                    type="button"
                    onClick={() => {
                      const cur = data.weather || [];
                      set(
                        "weather",
                        active
                          ? cur.filter((k) => k !== w.key)
                          : [...cur, w.key]
                      );
                    }}
                    className={
                      "px-3 py-1.5 rounded-full text-sm font-medium border transition-colors " +
                      (active
                        ? "bg-red-700 text-white border-red-700"
                        : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50")
                    }
                    data-testid={`weather-chip-${w.key}`}
                  >
                    {lang === "es" ? w.es : w.en}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subcontractor toggle + optional name */}
          <div className="mt-4">
            <label
              className="flex items-center gap-2 cursor-pointer select-none"
              data-testid="toggle-sub-label"
            >
              <input
                type="checkbox"
                checked={!!data.subcontractor_present}
                onChange={(e) => {
                  set("subcontractor_present", e.target.checked);
                  if (!e.target.checked) set("subcontractor_name", "");
                }}
                className="w-5 h-5 accent-red-700"
                data-testid="toggle-sub"
              />
              <span className="text-sm font-medium text-slate-900">
                {t("Subcontractor crew present")}
              </span>
            </label>
            {data.subcontractor_present && (
              <Input
                value={data.subcontractor_name}
                onChange={(e) => set("subcontractor_name", e.target.value)}
                className={inputCls + " mt-2"}
                placeholder={t("Subcontractor name (optional)")}
                data-testid="input-sub-name"
              />
            )}
          </div>
        </Section>

        <Section number="02" title={t("Topic & Discussion")}>
          {/* iter270 · Section 02 coaching family · supersedes the K6 strip */}
          <HelpTipBlock formKey="meeting.topic" className="mb-3" />
          <div className="bg-red-50 border-2 border-red-200 rounded-md p-4">
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold flex items-center gap-2">
              <span className="inline-flex w-5 h-5 items-center justify-center rounded bg-red-700 text-white text-[10px] font-black">
                1
              </span>
              {t("Pick a topic — Category & all fields below auto-fill")}
            </Label>
            <TopicPicker
              value={templateKey}
              onChange={applyTemplate}
              topics={TOPIC_LIBRARY}
              customKey={CUSTOM_TOPIC_KEY}
              placeholder={t("Search or pick a topic...")}
            />
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              {TOPIC_LIBRARY.length}+ {t("heavy civil / highway topics with prefilled hazards, key points, references, and action items. Type to search — or choose")}{" "}
              <span className="font-bold">{t("Custom Topic")}</span> {t("to write your own.")}
            </p>
            {/* iter270 · K6 coaching strip removed — `meeting.topic` HelpTipBlock above
                this Section already delivers the WHAT-HAPPENS-first coaching with
                richer kinds (why/mistake/example/next/escalate). */}
            {/* iter269 · Sprint 2 · K7 · domain breadcrumb (shown only when a library topic is loaded) */}
            {templateKey && templateKey !== CUSTOM_TOPIC_KEY && (() => {
              const tpl = findTopic(templateKey);
              if (!tpl?.domain) return null;
              return (
                <div
                  className="mt-3 inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] font-mono text-slate-500"
                  data-testid="meeting-domain-breadcrumb"
                >
                  <span>{t("Domain")}</span>
                  <span className="text-slate-900 font-bold">
                    {getDomainLabel(tpl.domain, lang)}
                  </span>
                </div>
              );
            })()}
          </div>

          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Topic / Subject *")}
            </Label>
            <Input
              value={data.topic}
              onChange={(e) => set("topic", e.target.value)}
              className={inputCls}
              placeholder="e.g. Heat Stress Prevention, Trench Safety, Silica Awareness"
              data-testid="input-topic"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Hazards Reviewed")}
            </Label>
            <Textarea
              value={data.hazards_reviewed}
              onChange={(e) => set("hazards_reviewed", e.target.value)}
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder={t("What specific hazards were discussed?")}
              data-testid="input-hazards-reviewed"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Discussion Notes / Minutes")}
            </Label>
            {/* iter269 · Sprint 2 · K4 · visual separation of CONTEXT (incident pattern)
                from ACTION (bullets). Read-only callout · the textarea below still
                holds the full scaffold for free editing. */}
            {(() => {
              const split = splitIncidentScaffold(data.discussion_notes);
              if (!split.header || !split.pattern) return null;
              return (
                <div
                  className="mt-2 mb-2 rounded-md border-2 border-red-200 bg-red-50/60 p-3"
                  data-testid="incident-context-block"
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold mb-1">
                    {split.header.trim()}
                  </div>
                  <p className="text-sm text-slate-900 leading-snug whitespace-pre-wrap">
                    {split.pattern}
                  </p>
                  <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-slate-500 mt-2">
                    {t("Context for the crew · the bullets below are the action drill")}
                  </div>
                </div>
              );
            })()}
            <Textarea
              value={data.discussion_notes}
              onChange={(e) => set("discussion_notes", e.target.value)}
              className="min-h-[140px] text-base border-2 border-slate-300"
              placeholder={t("Key points, questions, lessons learned...")}
              data-testid="input-discussion-notes"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("References Cited")}
            </Label>
            <Textarea
              value={data.references_cited}
              onChange={(e) => set("references_cited", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder={t("OSHA standards, SDS reviewed, MASCI procedures...")}
              data-testid="input-references"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Action Items / Follow-Up")}
            </Label>
            <Textarea
              value={data.action_items}
              onChange={(e) => set("action_items", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder={t("What needs to happen next? Who owns it?")}
              data-testid="input-action-items"
            />
          </div>
        </Section>

        <Section number="03" title={t("Attendees")}>
          {/* iter270 · Section 03 attendees coaching */}
          <HelpTipBlock formKey="meeting.attendees" className="mb-3" />
          <p className="text-sm text-slate-600">
            {t("Add every person who attended. Each attendee signs to confirm they were present and understood the topic.")}
          </p>
          {data.attendees.map((a, i) => (
            <div
              key={i}
              className="border border-slate-200 rounded-md p-4 space-y-3"
              data-testid={`attendee-${i}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  {t("Attendee")} {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeAttendee(i)}
                  className="text-slate-500 hover:text-red-600"
                  data-testid={`attendee-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> {t("Remove")}
                </Button>
              </div>

              {/* SAFETY-MEETING-CERT · MASCI vs Non-MASCI / Subcontractor toggle */}
              <div className="flex items-center gap-3 text-xs">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!a.non_masci}
                    onChange={(e) => {
                      const non = e.target.checked;
                      updateAttendee(i, "non_masci", non);
                      if (non) {
                        // Clear MASCI binding so HR roster is not polluted
                        updateAttendee(i, "employee_id", "");
                        // Don't auto-fill company; user must type it.
                        if (a.company === "MASCI") updateAttendee(i, "company", "");
                      } else {
                        // Returning to MASCI path — default company
                        if (!a.company) updateAttendee(i, "company", "MASCI");
                      }
                    }}
                    data-testid={`attendee-nonmasci-${i}`}
                  />
                  <span className="font-mono uppercase tracking-wide text-slate-600">
                    {t("Non-MASCI / Subcontractor")}
                  </span>
                </label>
              </div>

              {a.non_masci ? (
                <Input
                  value={a.name}
                  onChange={(e) => updateAttendee(i, "name", e.target.value)}
                  placeholder={t("Type subcontractor's full name")}
                  className={inputCls}
                  data-testid={`attendee-name-${i}`}
                />
              ) : (
                <EmployeeCombo
                  value={a.name}
                  onChange={(v) => {
                    updateAttendee(i, "name", v);
                    if (a.employee_id && v !== a.name) {
                      updateAttendee(i, "employee_id", "");
                    }
                  }}
                  onPick={(emp) => {
                    // iter362 + SAFETY-MEETING-CERT · capture canonical id +
                    // auto-fill company (MASCI) and trade from HR record.
                    if (emp.id || emp.employee_id) {
                      updateAttendee(i, "employee_id", emp.id || emp.employee_id);
                    }
                    updateAttendee(i, "company", "MASCI");
                    const trade = emp.trade || emp.role || emp.position || emp.job_title || "";
                    if (trade) updateAttendee(i, "trade", trade);
                  }}
                  placeholder={t("Type or pick an employee…")}
                  testId={`attendee-name-${i}`}
                />
              )}
              {(a.name || "").trim() && !a.non_masci ? (
                a.employee_id ? (
                  <div className="text-[10px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid={`attendee-linked-${i}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    {t("Linked to roster")}
                  </div>
                ) : (
                  <div className="text-[10px] text-amber-700 font-mono inline-flex items-center gap-1" data-testid={`attendee-unlinked-${i}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    {t("Not in roster — will create governance finding")}
                  </div>
                )
              ) : null}

              {/* SAFETY-MEETING-CERT · Company + Trade fields */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-xs font-mono uppercase tracking-wide text-slate-600">
                    {t("Company")} *
                  </Label>
                  <Input
                    value={a.company || ""}
                    onChange={(e) => updateAttendee(i, "company", e.target.value)}
                    disabled={!a.non_masci && !!a.employee_id}
                    placeholder={a.non_masci ? t("Subcontractor company") : "MASCI"}
                    className={inputCls}
                    data-testid={`attendee-company-${i}`}
                  />
                </div>
                <div>
                  <Label className="text-xs font-mono uppercase tracking-wide text-slate-600">
                    {t("Trade / Role")}
                  </Label>
                  <Input
                    value={a.trade || ""}
                    onChange={(e) => updateAttendee(i, "trade", e.target.value)}
                    placeholder={t("e.g. Foreman, Laborer, Pipe Layer")}
                    className={inputCls}
                    data-testid={`attendee-trade-${i}`}
                  />
                </div>
              </div>

              <BilingualConsent variant="meeting" />
              <SignaturePad
                value={a.signature}
                onChange={(v) => updateAttendee(i, "signature", v)}
                label={t("Signature") + " *"}
                testId={`attendee-sig-${i}`}
              />

              {/* SAFETY-MEETING-CERT · explicit acknowledgement */}
              <label className="flex items-start gap-2 cursor-pointer p-2 rounded-md border border-slate-200 bg-slate-50">
                <input
                  type="checkbox"
                  checked={!!a.acknowledged}
                  onChange={(e) => {
                    const v = e.target.checked;
                    updateAttendee(i, "acknowledged", v);
                    updateAttendee(i, "acknowledged_at", v ? new Date().toISOString() : "");
                  }}
                  className="mt-0.5 w-4 h-4"
                  data-testid={`attendee-ack-${i}`}
                />
                <span className="text-sm text-slate-700">
                  <strong>{t("I acknowledge")}</strong>{" — "}
                  {t("I was present, understood the topic and the hazards, and agree to the safe-work commitments discussed.")}
                </span>
              </label>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={addAttendee}
            disabled={data.attendees.length > 0 && !!isAttendeeIncomplete(data.attendees[data.attendees.length - 1])}
            className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="attendee-add"
          >
            <UserPlus className="w-4 h-4 mr-2" /> {t("Add Attendee")}
          </Button>
        </Section>

        <Section number="04" title={t("Photos")}>
          {/* iter270 · Section 04 photos coaching */}
          <HelpTipBlock formKey="meeting.photos" className="mb-3" />
          <p className="text-xs text-slate-600 -mt-2 mb-2">
            {t("Photos: ")}
            <span
              className={
                (data.photos || []).length >= 2
                  ? "text-emerald-700 font-bold"
                  : "text-red-700 font-bold"
              }
              data-testid="meeting-photo-count"
            >
              {(data.photos || []).length}
            </span>{" "}
            / <span className="font-mono">{t("min 2 required")}</span>
          </p>
          <PhotoUpload
            photos={data.photos}
            onChange={(photos) => set("photos", photos)}
          />
        </Section>

        <Section number="05" title={t("Conductor Signature")}>
          {/* iter270 · Section 05 conductor sign-off coaching */}
          <HelpTipBlock formKey="meeting.signoff" className="mb-3" />
          <p className="text-sm text-slate-600">
            {t("The person who ran the meeting signs to confirm the record is accurate.")}
          </p>
          {/* D1 · conducted_by is captured in Section 01. Show read-only
              here so foreman doesn't retype on mobile. */}
          <div
            className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
            data-testid="conducted-by-readonly"
          >
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              {t("Conducted By")}
            </div>
            <div className="mt-1 text-base font-medium text-slate-900">
              {data.conducted_by || (
                <span className="italic text-slate-400">
                  {t("— enter in Section 01 —")}
                </span>
              )}
            </div>
          </div>
          <BilingualConsent variant="meeting" />
          <SignaturePad
            value={data.conductor_signature}
            onChange={(v) => set("conductor_signature", v)}
            label={t("Conductor Signature") + " *"}
            testId="conductor-sig"
          />
        </Section>

        <div className="pt-4">
          {missingHint && (
            <p
              data-testid="meeting-submit-missing-hint-bottom"
              className="text-xs text-red-700 font-bold text-center mb-2 font-mono uppercase tracking-[0.15em]"
            >
              {t("To submit, complete")}: {missingHint}
            </p>
          )}
          <Button
            onClick={submit}
            disabled={saving}
            title={missingHint ? `${t("To submit, complete")}: ${missingHint}` : ""}
            className="w-full h-16 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-base sm:text-lg border-b-4 border-red-900 disabled:opacity-60"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {t("Saving Meeting...")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" />
                {t("Submit Meeting")}
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}
