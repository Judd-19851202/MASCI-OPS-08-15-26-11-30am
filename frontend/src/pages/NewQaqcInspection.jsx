import React, { useMemo, useState } from "react";
import { useNavigate, useParams, Link, Navigate } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  ClipboardCheck,
  AlertTriangle,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { JobPicker } from "@/components/JobPicker";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { SupplierCombo } from "@/components/SupplierCombo";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { findKind, buildChecklist, hasConcreteFields } from "@/lib/qaqcSchema";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2";

/**
 * NewQaqcInspection — single form component for all 3 QA/QC kinds.
 *
 * Submit flow:
 *   1. Validate required fields (job, location, work area/station,
 *      inspector, ≥3 photos, inspector signature, every checklist
 *      item answered, every fail has a deficiency note). Concrete-Form
 *      additionally requires Mix Design + Yards Ordered + Concrete Vendor.
 *   2. If lang is `es`, run translate-on-submit so notes store as English.
 *   3. POST to `/api/qaqc-inspections`. Backend persists + auto-emails
 *      the assigned PM with the PDF attached.
 *   4. Redirect to `/qaqc/:id` for the print/download view.
 */
export default function NewQaqcInspection() {
  const { slug } = useParams();
  const kindMeta = findKind(slug);
  const navigate = useNavigate();
  const { t, lang } = useT();
  const isConcrete = hasConcreteFields(slug);

  const [data, setData] = useState(() => ({
    inspection_kind: kindMeta?.api_kind || "concrete_form",
    project_name: "",
    project_number: "",
    location: "",
    client: "",
    pm_name: "",
    pm_email: "",
    subcontractor_name: "",
    crew_company: "",
    inspection_date: new Date().toISOString().slice(0, 10),
    inspection_time: new Date().toTimeString().slice(0, 5),
    inspector_name: "",
    work_activity: "",
    work_area: "",
    weather_conditions: "",
    // Concrete-Form-only fields
    mix_design: "",
    yards_ordered: "",
    concrete_vendor: "",
    checklist: buildChecklist(slug),
    inspection_notes: "",
    deficiencies: "",
    corrective_actions: "",
    photos: [],
    inspector_signature: "",
    sub_rep_name: "",
    sub_rep_signature: "",
  }));
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);

  const counts = useMemo(() => {
    const ps = data.checklist.filter((c) => c.result === "pass").length;
    const fs = data.checklist.filter((c) => c.result === "fail").length;
    const na = data.checklist.filter((c) => c.result === "na").length;
    return { ps, fs, na };
  }, [data.checklist]);

  const failsWithoutNotes = useMemo(
    () => data.checklist.filter((c) => c.result === "fail" && !c.note.trim()),
    [data.checklist],
  );

  if (!kindMeta) {
    return <Navigate to="/qaqc" replace />;
  }

  const update = (patch) => setData((p) => ({ ...p, ...patch }));

  const setItem = (idx, patch) =>
    setData((p) => ({
      ...p,
      checklist: p.checklist.map((c, i) => (i === idx ? { ...c, ...patch } : c)),
    }));

  // The /api/jobs payload exposes `project_manager` (name) and `pm_email`.
  // We map both onto the form so the PM section auto-fills the moment a
  // job is picked, and we persist pm_email on submit so the auto-email
  // pipeline can dispatch directly to the assigned PM without re-resolving.
  const applyJob = (job) => {
    if (!job) {
      // "Custom Job" path — clear job-derived fields but keep typed values.
      update({
        project_name: "",
        project_number: "",
        client: "",
      });
      return;
    }
    update({
      project_name: job.project_name || "",
      project_number: job.project_number || "",
      location: job.location || data.location,
      client: job.client || "",
      pm_name: job.project_manager || "",
      pm_email: job.pm_email || "",
    });
    if (job.project_manager) {
      toast.success(`PM set: ${job.project_manager}`);
    }
  };

  const useGps = async () => {
    setLocating(true);
    try {
      const pos = await getCurrentPosition();
      const { latitude, longitude, accuracy } = pos.coords;
      try {
        const r = await reverseGeocode(latitude, longitude);
        update({ location: r.display });
        toast.success(t("Location captured from GPS"));
      } catch {
        update({ location: formatCoords(latitude, longitude, accuracy) });
        toast.warning(t("Got GPS coordinates, but couldn't look up address"));
      }
    } catch (e) {
      toast.error(e?.message || t("Could not get GPS location"));
    } finally {
      setLocating(false);
    }
  };

  async function onSubmit(e) {
    e.preventDefault();
    if (saving) return;

    // ── Validation ────────────────────────────────────────────────────────
    const fails = [];
    if (!data.project_name) fails.push(t("Select a job."));
    if (!data.location) fails.push(t("Enter the work location."));
    if (!data.work_area.trim()) fails.push(t("Work Area / Station required."));
    if (!data.inspector_name) fails.push(t("Inspector name required."));
    if (!data.inspection_notes.trim()) fails.push(t("Inspection notes required."));
    if (data.photos.length < 3) fails.push(t("Minimum 3 photos required."));
    if (!data.inspector_signature) fails.push(t("Inspector signature required."));
    if (failsWithoutNotes.length > 0)
      fails.push(t("Every Fail item needs a deficiency note."));
    if (isConcrete) {
      if (!data.mix_design.trim()) fails.push(t("Mix Design required."));
      if (!String(data.yards_ordered).trim())
        fails.push(t("Yards Ordered required."));
      if (!data.concrete_vendor.trim())
        fails.push(t("Concrete Vendor required."));
    }
    if (fails.length) {
      toast.error(fails[0]);
      return;
    }

    setSaving(true);
    try {
      let payload = { ...data };
      if (lang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
      const res = await api.post("/qaqc-inspections", payload);
      toast.success(t("Submitted. Routing to assigned PM…"));
      navigate(`/qaqc/${res.data.id}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not submit. Try again."));
    } finally {
      setSaving(false);
    }
  }

  const titleLabel = lang === "es" ? kindMeta.title_es : kindMeta.title;
  const isSubcontractor = slug === "subcontractor-work";

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-emerald-600">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        <Link
          to="/qaqc"
          className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-emerald-700 font-bold mb-4"
          data-testid="qaqc-form-back"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> {t("QA / QC")}
        </Link>

        <div className="flex items-start gap-3 mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-emerald-600 text-white shrink-0">
            <ClipboardCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold">
              {t("QA / QC")}
            </span>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight">
              {titleLabel}
            </h1>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-5" data-testid="qaqc-form">
          <Section title={t("Job")}>
            <JobPicker
              projectName={data.project_name}
              projectNumber={data.project_number}
              onSelect={applyJob}
            />
            <Row>
              <Field label={t("Location")} required>
                <div className="flex gap-2">
                  <Input
                    className={inputCls + " flex-1"}
                    value={data.location}
                    onChange={(e) => update({ location: e.target.value })}
                    data-testid="qaqc-location"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={useGps}
                    disabled={locating}
                    title={t("Use GPS")}
                    className="h-12 border-2 border-slate-300 hover:border-emerald-600 hover:text-emerald-700 shrink-0"
                    data-testid="qaqc-gps-btn"
                  >
                    {locating ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <MapPin className="w-4 h-4" />
                    )}
                    <span className="ml-1 hidden sm:inline">GPS</span>
                  </Button>
                </div>
              </Field>
              <Field label={t("Project Manager")}>
                <Input
                  className={inputCls + " bg-slate-50"}
                  value={data.pm_name}
                  onChange={(e) => update({ pm_name: e.target.value })}
                  placeholder={t("Auto-filled from job")}
                  data-testid="qaqc-pm-name"
                />
              </Field>
            </Row>
          </Section>

          <Section title={t("Subcontractor / Crew")}>
            <Row>
              <Field label={t("Subcontractor")}>
                <SupplierCombo
                  value={data.subcontractor_name}
                  onChange={(v) => update({ subcontractor_name: v })}
                  testId="qaqc-sub-name"
                  placeholder={t("Search or add a subcontractor / vendor…")}
                />
              </Field>
              <Field label={t("Crew / Company")}>
                <Input
                  className={inputCls}
                  value={data.crew_company}
                  onChange={(e) => update({ crew_company: e.target.value })}
                  data-testid="qaqc-crew"
                />
              </Field>
            </Row>
          </Section>

          <Section title={t("Inspection")}>
            <Row>
              <Field label={t("Date")} required>
                <Input
                  type="date"
                  className={inputCls}
                  value={data.inspection_date}
                  onChange={(e) => update({ inspection_date: e.target.value })}
                  data-testid="qaqc-date"
                />
              </Field>
              <Field label={t("Time")} required>
                <Input
                  type="time"
                  className={inputCls}
                  value={data.inspection_time}
                  onChange={(e) => update({ inspection_time: e.target.value })}
                  data-testid="qaqc-time"
                />
              </Field>
            </Row>
            <Row>
              <Field label={t("Inspector Name")} required>
                <Input
                  className={inputCls}
                  value={data.inspector_name}
                  onChange={(e) => update({ inspector_name: e.target.value })}
                  data-testid="qaqc-inspector"
                />
              </Field>
              <Field label={t("Work Area / Station")} required>
                <Input
                  className={inputCls}
                  value={data.work_area}
                  onChange={(e) => update({ work_area: e.target.value })}
                  data-testid="qaqc-work-area"
                />
              </Field>
            </Row>
            {isSubcontractor && (
              <Field label={t("Work Activity")}>
                <Input
                  className={inputCls}
                  value={data.work_activity}
                  onChange={(e) => update({ work_activity: e.target.value })}
                  data-testid="qaqc-work-activity"
                />
              </Field>
            )}
            <Field label={t("Weather / Site Conditions")}>
              <Input
                className={inputCls}
                value={data.weather_conditions}
                onChange={(e) => update({ weather_conditions: e.target.value })}
                placeholder={t("e.g. 78°F, clear, light wind")}
                data-testid="qaqc-weather"
              />
            </Field>
          </Section>

          {isConcrete && (
            <Section
              title={t("Concrete Placement")}
              desc={t("Required for every concrete-form inspection.")}
            >
              <Row>
                <Field label={t("Mix Design")} required>
                  <Input
                    className={inputCls}
                    value={data.mix_design}
                    onChange={(e) => update({ mix_design: e.target.value })}
                    placeholder={t("e.g. 4000 PSI Class IV")}
                    data-testid="qaqc-mix-design"
                  />
                </Field>
                <Field label={t("Yards Ordered (CY)")} required>
                  <Input
                    type="number"
                    inputMode="decimal"
                    step="0.5"
                    min="0"
                    className={inputCls}
                    value={data.yards_ordered}
                    onChange={(e) => update({ yards_ordered: e.target.value })}
                    placeholder="0"
                    data-testid="qaqc-yards-ordered"
                  />
                </Field>
              </Row>
              <Field label={t("Concrete Vendor")} required>
                <SupplierCombo
                  value={data.concrete_vendor}
                  onChange={(v) => update({ concrete_vendor: v })}
                  testId="qaqc-concrete-vendor"
                  placeholder={t("Search or add the concrete supplier…")}
                />
              </Field>
            </Section>
          )}

          <Section title={t("Checklist")}>
            <p className="text-xs text-slate-500 mb-2">
              {t("Mark each item Pass, Fail, or N/A. Fails require a note.")}
            </p>
            <div className="space-y-2">
              {data.checklist.map((item, idx) => (
                <ChecklistRow
                  key={item.key}
                  item={item}
                  onChange={(patch) => setItem(idx, patch)}
                  testid={`qaqc-item-${item.key}`}
                  t={t}
                />
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-2 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
              <span className="px-2 py-1 rounded bg-emerald-100 text-emerald-900 border border-emerald-300">
                {t("Pass")} {counts.ps}
              </span>
              <span className="px-2 py-1 rounded bg-red-100 text-red-900 border border-red-300">
                {t("Fail")} {counts.fs}
              </span>
              <span className="px-2 py-1 rounded bg-slate-100 text-slate-700 border border-slate-300">
                {t("N/A")} {counts.na}
              </span>
            </div>
            {counts.fs > 0 && (
              <div className="mt-3 flex items-start gap-2 bg-red-50 border-2 border-red-300 rounded p-3">
                <AlertTriangle className="w-4 h-4 text-red-700 mt-0.5 shrink-0" />
                <p className="text-xs text-red-900 font-medium">
                  {t("One or more items failed. Document deficiencies and corrective actions before submitting.")}
                </p>
              </div>
            )}
          </Section>

          <Section title={t("Notes & Corrective Action")}>
            <Field label={t("Inspection Notes / Description")} required>
              <Textarea
                className="min-h-[110px] border-2 border-slate-300"
                value={data.inspection_notes}
                onChange={(e) => update({ inspection_notes: e.target.value })}
                data-testid="qaqc-notes"
              />
            </Field>
            <Field label={t("Deficiencies")}>
              <Textarea
                className="min-h-[80px] border-2 border-slate-300"
                value={data.deficiencies}
                onChange={(e) => update({ deficiencies: e.target.value })}
                data-testid="qaqc-deficiencies"
              />
            </Field>
            <Field label={t("Corrective Actions Required")}>
              <Textarea
                className="min-h-[80px] border-2 border-slate-300"
                value={data.corrective_actions}
                onChange={(e) => update({ corrective_actions: e.target.value })}
                data-testid="qaqc-corrective"
              />
            </Field>
          </Section>

          <Section title={t("Photos")} desc={t("Upload at least 3 photos of the work area.")}>
            <PhotoUpload
              value={data.photos}
              onChange={(photos) => update({ photos })}
              max={20}
            />
            <p className="text-[11px] text-slate-500 mt-1">
              {t("Uploaded:")}{" "}
              <span
                className={
                  data.photos.length >= 3
                    ? "text-emerald-700 font-bold"
                    : "text-red-700 font-bold"
                }
                data-testid="qaqc-photo-count"
              >
                {data.photos.length}
              </span>
              {" / "}
              <span className="font-mono">{t("min 3 required")}</span>
            </p>
          </Section>

          <Section title={t("Sign-Off")}>
            <Field label={t("Inspector Signature")} required>
              <SignaturePad
                value={data.inspector_signature}
                onChange={(v) => update({ inspector_signature: v })}
              />
            </Field>
            <Row>
              <Field label={t("Sub. Rep. Name (optional)")}>
                <Input
                  className={inputCls}
                  value={data.sub_rep_name}
                  onChange={(e) => update({ sub_rep_name: e.target.value })}
                  data-testid="qaqc-rep-name"
                />
              </Field>
            </Row>
            <Field label={t("Sub. Rep. Signature (optional)")}>
              <SignaturePad
                value={data.sub_rep_signature}
                onChange={(v) => update({ sub_rep_signature: v })}
              />
            </Field>
          </Section>

          <div className="sticky bottom-0 bg-white border-t-2 border-emerald-600 -mx-5 sm:-mx-8 px-5 sm:px-8 py-3 flex justify-end shadow-lg">
            <Button
              type="submit"
              disabled={saving}
              className="bg-emerald-600 hover:bg-emerald-700 h-12 px-6 font-bold"
              data-testid="qaqc-submit"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  {t("Submitting…")}
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  {t("Submit Inspection")}
                </>
              )}
            </Button>
          </div>
        </form>
      </main>
    </div>
  );
}

/* --- Internal small components --- */

function Section({ title, children, desc }) {
  return (
    <section className="bg-white border-2 border-slate-300 rounded-md p-4 sm:p-5">
      <h2 className="font-display text-lg sm:text-xl font-black text-slate-900 mb-1">
        {title}
      </h2>
      {desc && <p className="text-xs text-slate-500 mb-3">{desc}</p>}
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Row({ children }) {
  return <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{children}</div>;
}

function Field({ label, children, required }) {
  return (
    <div>
      <Label className="block font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1">
        {label} {required && <span className="text-red-700">*</span>}
      </Label>
      {children}
    </div>
  );
}

function ChecklistRow({ item, onChange, testid, t }) {
  return (
    <div
      className="border-2 border-slate-200 rounded p-3"
      data-testid={testid}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0 text-sm font-medium text-slate-900">
          {t(item.label)}
        </div>
        <div className="inline-flex rounded border-2 border-slate-300 overflow-hidden text-xs">
          {[
            ["pass", t("PASS"), "bg-emerald-600 text-white"],
            ["fail", t("FAIL"), "bg-red-600 text-white"],
            ["na", t("N/A"), "bg-slate-700 text-white"],
          ].map(([v, label, on]) => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ result: v })}
              className={
                "px-2 h-9 font-mono font-bold uppercase tracking-[0.1em] " +
                (item.result === v ? on : "bg-white text-slate-600")
              }
              data-testid={`${testid}-${v}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {item.result === "fail" && (
        <Textarea
          className="mt-2 min-h-[60px] border-2 border-red-300 text-sm"
          placeholder={t("Deficiency note (required for Fail)")}
          value={item.note}
          onChange={(e) => onChange({ note: e.target.value })}
          data-testid={`${testid}-note`}
        />
      )}
    </div>
  );
}
