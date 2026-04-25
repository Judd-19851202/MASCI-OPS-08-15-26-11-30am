import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Save, Loader2, MapPin, UserPlus, X, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { MasciLogo } from "@/components/MasciLogo";
import { Section } from "@/components/Section";
import { YesNo } from "@/components/YesNo";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { JobPicker } from "@/components/JobPicker";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import {
  PPE_OPTIONS,
  PERMIT_OPTIONS,
  buildJhaDefaults,
} from "@/lib/jhaSchema";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export default function NewJha({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(buildJhaDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));
  const setMap = (mapKey, key, value) =>
    setData((p) => ({ ...p, [mapKey]: { ...p[mapKey], [key]: value } }));

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
      setData((p) => ({ ...p, gps_lat: latitude, gps_lng: longitude, gps_accuracy: accuracy }));
      try {
        const r = await reverseGeocode(latitude, longitude);
        setData((p) => ({ ...p, location: r.display }));
        toast.success("Location captured from GPS");
      } catch {
        setData((p) => ({ ...p, location: formatCoords(latitude, longitude, accuracy) }));
        toast.warning("Got GPS coordinates, but couldn't look up address");
      }
    } catch (e) {
      toast.error(e?.message || "Could not get GPS location");
    } finally {
      setLocating(false);
    }
  };

  // Task steps
  const addStep = () =>
    setData((p) => ({
      ...p,
      task_steps: [...p.task_steps, { step: "", hazards: "", controls: "" }],
    }));
  const updateStep = (i, k, v) =>
    setData((p) => ({
      ...p,
      task_steps: p.task_steps.map((s, idx) => (idx === i ? { ...s, [k]: v } : s)),
    }));
  const removeStep = (i) =>
    setData((p) => ({
      ...p,
      task_steps: p.task_steps.filter((_, idx) => idx !== i),
    }));

  // Crew sign-offs
  const addSignoff = () =>
    setData((p) => ({
      ...p,
      crew_signoffs: [...p.crew_signoffs, { name: "", signature: "" }],
    }));
  const updateSignoff = (i, k, v) =>
    setData((p) => ({
      ...p,
      crew_signoffs: p.crew_signoffs.map((s, idx) => (idx === i ? { ...s, [k]: v } : s)),
    }));
  const removeSignoff = (i) =>
    setData((p) => ({
      ...p,
      crew_signoffs: p.crew_signoffs.filter((_, idx) => idx !== i),
    }));

  const validate = () => {
    const required = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["jha_date", "Date"],
      ["job_title", "Job / Task Title"],
      ["crew_lead", "Crew Lead / Foreman"],
    ];
    for (const [k, l] of required) {
      if (!String(data[k] || "").trim()) {
        toast.error(`${l} is required`);
        return false;
      }
    }
    if (data.task_steps.filter((s) => s.step.trim()).length === 0) {
      toast.error("Add at least one task step");
      return false;
    }
    if (!data.foreman_signature) {
      toast.error("Foreman approval signature is required");
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const res = await api.post("/jhas", data);
      toast.success("JHA saved");
      if (publicMode) {
        navigate("/thank-you", {
          state: {
            projectName: data.project_name,
            formType: "Job Hazard Analysis",
            returnTo: "/jha/submit",
          },
          replace: true,
        });
      } else {
        navigate(`/jha/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error("Could not save JHA");
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
            <MasciLogo variant="lockup" size="lg" className="hidden sm:block" />
          ) : (
            <Link
              to="/jha"
              className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> JHAs
            </Link>
          )}
          <MasciLogo variant="mark" size="md" className={publicMode ? "sm:hidden" : ""} />
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button
              onClick={submit}
              disabled={saving}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
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
            {t("Job Hazard Analysis")}
          </h1>
        </div>

        <Section number="01" title={t("Job / Task Information")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              MASCI Job
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
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Project Name *</Label>
              <Input value={data.project_name} onChange={(e) => set("project_name", e.target.value)} className={inputCls} data-testid="input-project-name" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Project Number</Label>
              <Input value={data.project_number} onChange={(e) => set("project_number", e.target.value)} className={inputCls} data-testid="input-project-number" />
            </div>
            <div className="sm:col-span-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Location *</Label>
                <Button type="button" variant="outline" size="sm" onClick={useGps} disabled={locating} className="h-9 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs" data-testid="use-gps-btn">
                  {locating ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <MapPin className="w-3.5 h-3.5 mr-1" />}
                  Use GPS
                </Button>
              </div>
              <Input value={data.location} onChange={(e) => set("location", e.target.value)} className={inputCls} data-testid="input-location" />
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Date *</Label>
              <Input type="date" value={data.jha_date} onChange={(e) => set("jha_date", e.target.value)} className={inputCls} data-testid="input-date" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Crew Lead / Foreman *</Label>
              <Input value={data.crew_lead} onChange={(e) => set("crew_lead", e.target.value)} className={inputCls} data-testid="input-crew-lead" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Job / Task Title *</Label>
              <Input value={data.job_title} onChange={(e) => set("job_title", e.target.value)} className={inputCls} placeholder="e.g. Install 24-inch RCP - Station 12+50" data-testid="input-job-title" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Job Description</Label>
              <Textarea value={data.job_description} onChange={(e) => set("job_description", e.target.value)} className="min-h-[100px] text-base border-2 border-slate-300" data-testid="input-job-description" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Crew Members</Label>
              <Textarea value={data.crew_members} onChange={(e) => set("crew_members", e.target.value)} className="min-h-[80px] text-base border-2 border-slate-300" placeholder="List all crew members performing the task" data-testid="input-crew-members" />
            </div>
          </div>
        </Section>

        <Section number="02" title={t("Required PPE")}>
          <p className="text-sm text-slate-600">Check every PPE item required for this task.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PPE_OPTIONS.map((opt) => (
              <label
                key={opt.key}
                className="flex items-center gap-3 p-3 border-2 border-slate-200 rounded-md hover:border-red-500 cursor-pointer"
                data-testid={`ppe-${opt.key}`}
              >
                <Checkbox
                  checked={!!data.ppe_required[opt.key]}
                  onCheckedChange={(v) => setMap("ppe_required", opt.key, !!v)}
                />
                <span className="text-base text-slate-800">{opt.label}</span>
              </label>
            ))}
          </div>
        </Section>

        <Section number="03" title={t("Required Permits")}>
          <p className="text-sm text-slate-600">Check any permits required before this work begins.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PERMIT_OPTIONS.map((opt) => (
              <label
                key={opt.key}
                className="flex items-center gap-3 p-3 border-2 border-slate-200 rounded-md hover:border-red-500 cursor-pointer"
                data-testid={`permit-${opt.key}`}
              >
                <Checkbox
                  checked={!!data.permits_required[opt.key]}
                  onCheckedChange={(v) => setMap("permits_required", opt.key, !!v)}
                />
                <span className="text-base text-slate-800">{opt.label}</span>
              </label>
            ))}
          </div>
        </Section>

        <Section number="04" title={t("Tools & Equipment")}>
          <Textarea
            value={data.tools_equipment}
            onChange={(e) => set("tools_equipment", e.target.value)}
            className="min-h-[100px] text-base border-2 border-slate-300"
            placeholder="List tools, equipment, and machinery needed"
            data-testid="input-tools"
          />
        </Section>

        <Section number="05" title={t("Hazard Analysis")}>
          <p className="text-sm text-slate-600">
            Walk through each step of the task. For every step, list the potential hazards and the controls / safe practices to mitigate them.
          </p>
          {data.task_steps.map((s, i) => (
            <div
              key={i}
              className="border-2 border-slate-200 rounded-md p-4 space-y-3"
              data-testid={`step-${i}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Step {i + 1}
                </span>
                {data.task_steps.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeStep(i)}
                    className="text-slate-500 hover:text-red-600"
                    data-testid={`step-remove-${i}`}
                  >
                    <X className="w-4 h-4 mr-1" /> Remove
                  </Button>
                )}
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">Step Description</Label>
                <Textarea
                  value={s.step}
                  onChange={(e) => updateStep(i, "step", e.target.value)}
                  className="min-h-[60px] text-base border-2 border-slate-300"
                  placeholder="What is the crew doing in this step?"
                  data-testid={`step-desc-${i}`}
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">Potential Hazards</Label>
                <Textarea
                  value={s.hazards}
                  onChange={(e) => updateStep(i, "hazards", e.target.value)}
                  className="min-h-[60px] text-base border-2 border-slate-300"
                  placeholder="What could go wrong? What hazards are present?"
                  data-testid={`step-hazards-${i}`}
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-green-700 font-bold">Controls / Safe Practices</Label>
                <Textarea
                  value={s.controls}
                  onChange={(e) => updateStep(i, "controls", e.target.value)}
                  className="min-h-[60px] text-base border-2 border-slate-300"
                  placeholder="What are we doing to eliminate or control the hazard?"
                  data-testid={`step-controls-${i}`}
                />
              </div>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={addStep}
            className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
            data-testid="step-add"
          >
            <Plus className="w-4 h-4 mr-2" /> Add Task Step
          </Button>
        </Section>

        <Section number="06" title="Emergency & Stop Work">
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Stop Work Authority Acknowledged *
            </Label>
            <YesNo
              value={data.stop_work_acknowledged}
              onChange={(v) => set("stop_work_acknowledged", v)}
              testId="stop-work-ack"
              size="lg"
            />
            <p className="text-xs text-slate-500 mt-1">
              Every crew member has the authority and responsibility to stop work for any safety concern, no questions asked.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Nearest Hospital / ER</Label>
              <Input value={data.nearest_hospital} onChange={(e) => set("nearest_hospital", e.target.value)} className={inputCls} data-testid="input-hospital" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Emergency Contact #</Label>
              <Input value={data.emergency_contact} onChange={(e) => set("emergency_contact", e.target.value)} className={inputCls} data-testid="input-emergency" />
            </div>
          </div>
        </Section>

        <Section number="07" title={t("Crew Sign-Off")}>
          <p className="text-sm text-slate-600">
            Each crew member signs to confirm they understand the hazards and the safe work plan.
          </p>
          {data.crew_signoffs.map((c, i) => (
            <div
              key={i}
              className="border-2 border-slate-200 rounded-md p-4 space-y-3"
              data-testid={`signoff-${i}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Crew Member {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSignoff(i)}
                  className="text-slate-500 hover:text-red-600"
                  data-testid={`signoff-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
              <Input
                value={c.name}
                onChange={(e) => updateSignoff(i, "name", e.target.value)}
                className={inputCls}
                placeholder="Typed name"
                data-testid={`signoff-name-${i}`}
              />
              <SignaturePad
                value={c.signature}
                onChange={(v) => updateSignoff(i, "signature", v)}
                label="Signature"
                testId={`signoff-sig-${i}`}
              />
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={addSignoff}
            className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
            data-testid="signoff-add"
          >
            <UserPlus className="w-4 h-4 mr-2" /> Add Crew Member
          </Button>
        </Section>

        <Section number="08" title={t("Photos")}>
          <PhotoUpload photos={data.photos} onChange={(photos) => set("photos", photos)} />
        </Section>

        <Section number="09" title={t("Foreman Approval")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">Foreman / Crew Lead (Typed)</Label>
            <Input
              value={data.crew_lead}
              onChange={(e) => set("crew_lead", e.target.value)}
              className={inputCls}
              data-testid="input-foreman-typed"
            />
          </div>
          <SignaturePad
            value={data.foreman_signature}
            onChange={(v) => set("foreman_signature", v)}
            label="Foreman Approval Signature *"
            testId="foreman-sig"
          />
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
                <Loader2 className="w-5 h-5 mr-2 animate-spin" /> {t("Saving JHA...")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" /> {t("Submit JHA")}
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}
