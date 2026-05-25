import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Save, Loader2, MapPin, Camera } from "lucide-react";
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
import { Section, ChecklistRow } from "@/components/Section";
import { YesNo } from "@/components/YesNo";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { JobPicker } from "@/components/JobPicker";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { LangToggle } from "@/components/LangToggle";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT, getLang } from "@/lib/i18n";
import { formatApiError } from "@/lib/apiErrors";
import {
  PPE_ITEMS,
  SITE_HAZARD_ITEMS,
  CONDITIONAL_SECTIONS,
  buildDefaults,
} from "@/lib/inspectionSchema";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import { computeGrade } from "@/lib/grading";
import { GradeBanner } from "@/components/Grade";
import { getCurrentPosition, reverseGeocode, formatCoords } from "@/lib/geolocation";
import {
  useFormDraft, getActorId, DraftStatusPill, DraftRestorePrompt,
  enqueueOffline, replayOfflineQueue, registerOfflineAutoReplay,
} from "@/lib/resiliency";

// iter438 · Phase 31 · Pass C · offline queue formKey for inspection
// submits. Lets a foreman file from a dead zone and the report
// catches up automatically when signal returns.
const INSPECTION_QUEUE_KEY = "inspection-submit";
registerOfflineAutoReplay(INSPECTION_QUEUE_KEY);

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export default function NewInspection({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(buildDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);

  // iter434 · Phase 31 · Part 2 — manual draft recovery via calm prompt
  // (do NOT auto-overwrite the form). Autosave continues silently.
  const actorId = React.useMemo(() => getActorId(), []);
  const {
    pendingDraft, draftStatus, restore, discard, commit,
  } = useFormDraft("inspection-new", data, actorId);

  const onRestoreDraft = React.useCallback(() => {
    const d = restore();
    if (d) {
      setData(d);
      toast.success(t("Draft restored"));
    }
  }, [restore, t]);

  const onDiscardDraft = React.useCallback(() => {
    discard();
    toast.message(t("Draft discarded"));
  }, [discard, t]);

  // iter438 · attempt to replay any queued inspection submits on mount
  // and on the `online` event. Silent · operational continuity.
  useEffect(() => {
    replayOfflineQueue(INSPECTION_QUEUE_KEY).catch(() => { /* silent */ });
    const onOnline = () => {
      replayOfflineQueue(INSPECTION_QUEUE_KEY).catch(() => { /* silent */ });
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, []);

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
      // Save coords immediately even if reverse geocode fails
      setData((p) => ({
        ...p,
        gps_lat: latitude,
        gps_lng: longitude,
        gps_accuracy: accuracy,
      }));
      try {
        const r = await reverseGeocode(latitude, longitude);
        setData((p) => ({ ...p, location: r.display }));
        toast.success("Location captured from GPS");
      } catch {
        // Couldn't reverse geocode — fall back to coordinates as the location
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
        toast.warning("Got GPS coordinates, but couldn't look up address");
      }
    } catch (e) {
      const msg =
        e?.code === 1
          ? "Location permission denied — enable it in your browser settings"
          : e?.code === 2
          ? "Could not determine your location. Try moving to an open area."
          : e?.code === 3
          ? "Location lookup timed out. Try again."
          : e?.message || "Could not get GPS location";
      toast.error(msg);
    } finally {
      setLocating(false);
    }
  };

  const set = (field, value) => setData((p) => ({ ...p, [field]: value }));
  const setNested = (section, key, value) =>
    setData((p) => ({ ...p, [section]: { ...p[section], [key]: value } }));
  const setCondTop = (section, field, value) =>
    setData((p) => ({ ...p, [section]: { ...p[section], [field]: value } }));
  const setCondItem = (section, key, value) =>
    setData((p) => ({
      ...p,
      [section]: {
        ...p[section],
        items: { ...p[section].items, [key]: value },
      },
    }));

  const validate = () => {
    const required = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["inspection_date", "Date"],
      ["inspection_time", "Time"],
      ["inspector_name", "Inspector Name"],
      ["foreman_name", "Foreman / Supervisor"],
      ["work_activity", "Work Activity"],
    ];
    for (const [key, label] of required) {
      if (!String(data[key] || "").trim()) {
        toast.error(`${label} is required`);
        return false;
      }
    }
    if (!data.inspector_signature) {
      toast.error("Inspector signature is required");
      return false;
    }
    if (!data.foreman_signature) {
      toast.error("Foreman / Supervisor signature is required");
      return false;
    }
    if ((data.photos || []).length < 4) {
      toast.error(t("Minimum 4 photos required."));
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const grade = computeGrade(data);
      let payload = {
        ...data,
        score: grade.score,
        status: grade.status,
        auto_fail_count: grade.auto_fail_count,
        graded_yes: grade.yes,
        graded_no: grade.no,
        graded_total: grade.total,
      };
      const lang = getLang();
      if (lang === "es") {
        toast.info("Translating to English…");
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
      let res;
      try {
        res = await api.post("/inspections", payload);
      } catch (netErr) {
        // iter438 · Phase 31 · Pass C · offline / network failure →
        // queue the submission so it replays on `online` event. The
        // operator sees a calm "Saved · will send when online" toast
        // instead of an error · doctrine matches the Daily Report
        // queued-offline path.
        const isNetwork = !netErr?.response ||
          netErr.code === "ERR_NETWORK" ||
          netErr.message?.toLowerCase().includes("network");
        if (isNetwork) {
          enqueueOffline(INSPECTION_QUEUE_KEY, {
            method: "POST",
            url: "/api/inspections",
            body: payload,
            meta: { project_name: payload.project_name },
          });
          // iter438 · clear the draft once we've queued — the queued
          // copy is the durable copy from this point.
          await commit();
          toast.message(t("Saved · will send when online."), {
            description: t("This inspection is on this device and will upload automatically."),
            duration: 6000,
          });
          if (publicMode || !isAdmin()) {
            navigate("/thank-you", {
              state: {
                projectName: payload.project_name,
                formType: "Inspection",
                queued: true,
              },
              replace: true,
            });
          } else {
            navigate(`/audits`);
          }
          return;
        }
        throw netErr;
      }
      // iter434 · Phase 31 · clear the draft on confirmed submission.
      await commit();
      toast.success(t("Inspection filed · graded · visible under Audits & Inspections"));
      if (publicMode || !isAdmin()) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            grade,
            formType: "Inspection",
            recordId: res.data?.inspection_number || res.data?.id || "",
          },
          replace: true,
        });
      } else {
        navigate(`/inspect/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error(formatApiError(e, "Could not save inspection"), { duration: 7000 });
    } finally {
      setSaving(false);
    }
  };

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
              className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Home
            </Link>
          )}
          <MasciLogo variant="mark" size="md" className={publicMode ? "sm:hidden" : ""} homeLink="/" />
          <div className="flex items-center gap-2">
            <DraftStatusPill status={draftStatus} testId="inspection-draft-pill" />
            <LangToggle />
            <Button
              onClick={submit}
              disabled={saving || (data.photos || []).length < 4}
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
            {t("Job Site Safety Inspection")}
          </h1>
          {/* iter333 · operational sub-header · iter327 voice */}
          <p className="text-sm text-slate-600 mt-1.5 max-w-2xl leading-snug">
            {t("A walking record of what's safe, what isn't, and what was fixed today. Honest grades drive better jobs.")}
          </p>
        </div>

        {/* Live grade banner */}
        <GradeBanner grade={computeGrade(data)} label={t("Live Grade")} />

        {/* iter434 · Phase 31 · Part 2 — calm draft recovery prompt. */}
        <DraftRestorePrompt
          pendingDraft={pendingDraft}
          onRestore={onRestoreDraft}
          onDiscard={onDiscardDraft}
          testId="inspection-draft-restore-prompt"
        />

        {/* Section 1: Project / Inspection Information */}
        <Section number="01" title={t("Project / Inspection Information")}>
          {/* iter273 · form-root + Section 01 coaching */}
          <HelpTipBlock formKey="inspection" className="mb-3" showCounter />
          <HelpTipBlock formKey="inspection.context" className="mb-3" />
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
              Pick a current job to auto-fill name + number — or choose Custom Job to type your own.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Project Name *
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
                Project Number
              </Label>
              <Input
                value={data.project_number}
                onChange={(e) => set("project_number", e.target.value)}
                className={inputCls}
                placeholder="Optional"
                data-testid="input-project-number"
              />
            </div>
            <div className="sm:col-span-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Location *
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
                  Use GPS
                </Button>
              </div>
              <Input
                value={data.location}
                onChange={(e) => set("location", e.target.value)}
                className={inputCls}
                placeholder="Address, intersection, station, or GPS"
                data-testid="input-location"
              />
              {data.gps_lat != null && data.gps_lng != null && (
                <div
                  className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5 flex items-center gap-1"
                  data-testid="gps-coords-display"
                >
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Date *
              </Label>
              <Input
                type="date"
                value={data.inspection_date}
                onChange={(e) => set("inspection_date", e.target.value)}
                className={inputCls}
                data-testid="input-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Time *
              </Label>
              <Input
                type="time"
                value={data.inspection_time}
                onChange={(e) => set("inspection_time", e.target.value)}
                className={inputCls}
                data-testid="input-time"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Operation *
              </Label>
              <Select value={data.operation} onValueChange={(v) => set("operation", v)}>
                <SelectTrigger className={inputCls} data-testid="select-operation">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Day">Day</SelectItem>
                  <SelectItem value="Night">Night</SelectItem>
                  <SelectItem value="Weekend">Weekend</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Inspector Name *
              </Label>
              <EmployeeCombo
                value={data.inspector_name}
                onChange={(v) => set("inspector_name", v)}
                placeholder="Type or pick inspector"
                testId="input-inspector-name"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Foreman / Supervisor *
              </Label>
              <EmployeeCombo
                value={data.foreman_name}
                onChange={(v) => set("foreman_name", v)}
                placeholder="Type or pick foreman / supervisor"
                testId="input-foreman-name"
              />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Crew / MASCI Personnel Onsite
              </Label>
              <Textarea
                value={data.crew_personnel}
                onChange={(e) => set("crew_personnel", e.target.value)}
                className="min-h-[80px] text-base border-2 border-slate-300"
                placeholder="List crew members or crew lead"
                data-testid="input-crew"
              />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Subcontractors Onsite
              </Label>
              <Textarea
                value={data.subcontractors}
                onChange={(e) => set("subcontractors", e.target.value)}
                className="min-h-[80px] text-base border-2 border-slate-300"
                placeholder="Company / activity / manpower"
                data-testid="input-subs"
              />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Weather Conditions
              </Label>
              <Input
                value={data.weather_conditions}
                onChange={(e) => set("weather_conditions", e.target.value)}
                className={inputCls}
                placeholder="Sunny 78°F, light wind…"
                data-testid="input-weather"
              />
            </div>
          </div>
        </Section>

        {/* Section 2: Work Activity */}
        <Section number="02" title={t("Work Activity Taking Place Onsite")}>
          <Textarea
            value={data.work_activity}
            onChange={(e) => set("work_activity", e.target.value)}
            className="min-h-[100px] text-base border-2 border-slate-300"
            placeholder="Earthwork, pipe, paving, concrete, MOT setup, etc."
            data-testid="input-work-activity"
          />
        </Section>

        {/* Section 3: PPE Compliance */}
        <Section number="03" title="PPE Compliance">
          {/* iter273 · Section 03 PPE coaching */}
          <HelpTipBlock formKey="inspection.ppe" className="mb-3" />
          {PPE_ITEMS.map((item) => (
            <ChecklistRow
              key={item.key}
              label={item.label}
              testId={`ppe-row-${item.key}`}
            >
              <YesNo
                value={data.ppe_compliance[item.key] || ""}
                onChange={(v) => setNested("ppe_compliance", item.key, v)}
                testId={`ppe-${item.key}`}
              />
            </ChecklistRow>
          ))}
        </Section>

        {/* Conditional sections 4-10 */}
        {CONDITIONAL_SECTIONS.map((sec, idx) => {
          const sectionNum = String(4 + idx).padStart(2, "0");
          const block = data[sec.key];
          const expanded = block.applies === "Yes";
          return (
            <Section key={sec.key} number={sectionNum} title={sec.title}>
              <div>
                <Label className="text-base text-slate-800 leading-snug block mb-3">
                  {sec.trigger}
                </Label>
                <YesNo
                  value={block.applies}
                  onChange={(v) => setCondTop(sec.key, "applies", v)}
                  options={["No", "Yes"]}
                  testId={`cond-${sec.key}`}
                  size="lg"
                />
              </div>
              {expanded && (
                <div className="mt-3 pt-4 border-t-2 border-dashed border-red-600 space-y-1">
                  {sec.items.map((item) => (
                    <ChecklistRow
                      key={item.key}
                      label={item.label}
                      autoFail={item.autoFail}
                      testId={`${sec.key}-row-${item.key}`}
                    >
                      <YesNo
                        value={block.items[item.key] || ""}
                        onChange={(v) => setCondItem(sec.key, item.key, v)}
                        testId={`${sec.key}-${item.key}`}
                      />
                    </ChecklistRow>
                  ))}
                  <div className="pt-3">
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                      Notes
                    </Label>
                    <Textarea
                      value={block.notes}
                      onChange={(e) => setCondTop(sec.key, "notes", e.target.value)}
                      className="min-h-[80px] text-base border-2 border-slate-300"
                      placeholder="Optional notes for this section"
                      data-testid={`${sec.key}-notes`}
                    />
                  </div>
                </div>
              )}
            </Section>
          );
        })}

        {/* Section 11: Site Hazards & Housekeeping */}
        <Section number="11" title={t("General Site Hazards & Housekeeping")}>
          {SITE_HAZARD_ITEMS.map((item) => (
            <ChecklistRow
              key={item.key}
              label={item.label}
              testId={`hazard-row-${item.key}`}
            >
              <YesNo
                value={data.site_hazards[item.key] || ""}
                onChange={(v) => setNested("site_hazards", item.key, v)}
                testId={`hazard-${item.key}`}
              />
            </ChecklistRow>
          ))}
        </Section>

        {/* Section 12: Corrective Actions */}
        <Section number="12" title={t("Safety Issues / Corrective Actions")}>
          {/* iter273 · Section 12 findings coaching · the densest surface */}
          <HelpTipBlock formKey="inspection.findings" className="mb-3" />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Hazards Observed *
              </Label>
              <YesNo
                value={data.hazards_observed}
                onChange={(v) => set("hazards_observed", v)}
                testId="hazards-observed"
                size="lg"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Stop Work Issued *
              </Label>
              <YesNo
                value={data.stop_work_issued}
                onChange={(v) => set("stop_work_issued", v)}
                testId="stop-work"
                size="lg"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Corrected On Site *
              </Label>
              <YesNo
                value={data.corrected_on_site}
                onChange={(v) => set("corrected_on_site", v)}
                options={["Yes", "No", "N/A"]}
                testId="corrected-onsite"
                size="lg"
              />
            </div>
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Responsible Party / Follow-Up Owner
            </Label>
            <Input
              value={data.responsible_party}
              onChange={(e) => set("responsible_party", e.target.value)}
              className={inputCls}
              data-testid="input-responsible-party"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Description / Corrective Action Notes
            </Label>
            <Textarea
              value={data.corrective_action_notes}
              onChange={(e) => set("corrective_action_notes", e.target.value)}
              className="min-h-[120px] text-base border-2 border-slate-300"
              placeholder={t("What was the issue, where on site, what was done about it, and who owns the follow-up. Specific beats general — name the location, the trade, the action.")}
              data-testid="input-corrective-notes"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 block mb-2">
              {t("Photo Documentation")}
            </Label>
            <PhotoUpload
              photos={data.photos}
              onChange={(photos) => set("photos", photos)}
            />
            <p className="text-[11px] text-slate-500 mt-1">
              {t("Uploaded:")}{" "}
              <span
                className={
                  (data.photos || []).length >= 4
                    ? "text-emerald-700 font-bold"
                    : "text-red-700 font-bold"
                }
                data-testid="inspection-photo-count"
              >
                {(data.photos || []).length}
              </span>
              {" / "}
              <span className="font-mono">{t("min 4 required")}</span>
            </p>
          </div>
        </Section>

        {/* Section 13: Signatures */}
        <Section number="13" title={t("Signatures")}>
          {/* iter273 · Section 13 sign-off coaching */}
          <HelpTipBlock formKey="inspection.signoff" className="mb-3" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Inspector Typed Name *
                </Label>
                <Input
                  value={data.inspector_name}
                  onChange={(e) => set("inspector_name", e.target.value)}
                  className={inputCls}
                  placeholder="Inspector name"
                  data-testid="input-inspector-typed"
                />
              </div>
              <SignaturePad
                value={data.inspector_signature}
                onChange={(v) => set("inspector_signature", v)}
                label="Inspector Signature *"
                testId="inspector-signature"
              />
            </div>
            <div className="space-y-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Foreman / Supervisor Typed Name *
                </Label>
                <Input
                  value={data.foreman_name}
                  onChange={(e) => set("foreman_name", e.target.value)}
                  className={inputCls}
                  placeholder="Supervisor name"
                  data-testid="input-foreman-typed"
                />
              </div>
              <SignaturePad
                value={data.foreman_signature}
                onChange={(v) => set("foreman_signature", v)}
                label="Foreman / Supervisor Signature *"
                testId="foreman-signature"
              />
            </div>
          </div>
        </Section>

        <div className="pt-4">
          {(data.photos || []).length < 4 && (
            <p
              className="text-center text-sm text-red-700 font-bold mb-2"
              data-testid="inspection-submit-photos-hint"
            >
              <Camera className="w-4 h-4 inline-block mr-1 -mt-0.5" />
              {t("Add")}{" "}
              <span className="font-mono">{4 - (data.photos || []).length}</span>{" "}
              {(data.photos || []).length === 3
                ? t("more photo to submit")
                : t("more photos to submit")}
            </p>
          )}
          <Button
            onClick={submit}
            disabled={saving || (data.photos || []).length < 4}
            className="w-full h-16 bg-red-700 hover:bg-red-800 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-base sm:text-lg border-b-4 border-red-900 disabled:border-slate-400"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {t("Saving Inspection...")}
              </>
            ) : (data.photos || []).length < 4 ? (
              <>
                <Camera className="w-5 h-5 mr-2" />
                {t("Need 4 photos to submit")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" />
                {t("Submit Inspection")}
              </>
            )}
          </Button>
          <p className="text-center text-xs text-slate-500 mt-2 font-mono uppercase tracking-[0.2em]">
            {t("All fields marked * are required")}
          </p>
        </div>
      </main>
    </div>
  );
}
