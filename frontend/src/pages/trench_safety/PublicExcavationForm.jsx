// Phase 10A · Public Excavation Operations Form (G-1 closure)
//
// Sprint: Phase 10A Core — Public Excavation Operations Workflow.
//
// Public field-safe submit · EN / ES · all 14 sections.
//
// UI Parity (Public Trench Safety standard):
//   • <PublicTrenchHeader> — back nav · MASCI logo · HOME · LangToggle
//   • caution-stripe banner
//   • Standard title block (icon · eyebrow · h1 · description)
//   • Red Stop-Work + Amber Competent-Person coaching strips
//   • Same section card styling as other public forms
//   • Footer matches /trench-safety dashboard
//
// Route: /trench-safety/excavation/new  (public, no auth)
import React, { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Loader2, CheckCircle2, AlertTriangle, HardHat, OctagonAlert, ShieldAlert, ScanLine, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import PublicTrenchHeader from "@/components/trench/PublicTrenchHeader";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const WORK_TYPES = ["Utility Work", "Storm Drain", "Sanitary Sewer", "Water Main", "Electrical / Communication", "Roadway Excavation", "Structure / Box Culvert", "Drainage", "Other"];
const SOILS = ["Type A", "Type B", "Type C", "Stable Rock", "Unknown / Needs Review"];
const PROTECT = ["Trench Box / Shielding", "Shoring", "Sloping", "Benching", "Combination", "Not Required", "Needs Safety Review"];
const LOCATE = ["Complete", "Pending", "Not Required", "Conflict / Needs Review"];

function Bool({ value, onChange, testId }) {
  const { t } = useT();
  return (
    <div className="flex gap-1.5" data-testid={testId}>
      {[{ v: true, l: t("Yes") }, { v: false, l: t("No") }, { v: null, l: t("N/A") }].map(({ v, l }) => (
        <button
          key={String(v)}
          type="button"
          onClick={() => onChange(v)}
          className={"px-3 h-9 rounded border text-xs font-bold uppercase tracking-[0.08em] transition " +
            (value === v
              ? "border-cyan-700 bg-cyan-700 text-white"
              : "border-slate-300 bg-white text-slate-700 hover:border-cyan-500")}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

function Section({ num, title, children, testId }) {
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4 mt-3" data-testid={testId || `exc-section-${num}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
        {num} · {title}
      </div>
      {children}
    </section>
  );
}

export default function PublicExcavationForm() {
  const { t, lang } = useT();
  const currentLang = lang || "en";

  const [sp] = useSearchParams();
  const [f, setF] = useState(() => ({
    project_name: sp.get("project_name") || "",
    project_number: sp.get("project_number") || "",
    location: sp.get("location") || "",
    work_area: "",
    date_of_work: sp.get("date") || new Date().toISOString().slice(0, 10),
    supervisor_name: sp.get("supervisor") || "",
    crew: sp.get("crew") || "",
    submitted_by: "",
    contact_phone: "",
    length_ft: "", width_ft: "", depth_ft: "", depth_unit: "ft",
    depth_ge_4ft: null, depth_ge_5ft: null, cave_in_hazard_under_5ft: null,
    work_type: "Other",
    soil_classification: "Unknown / Needs Review",
    protective_system: "Needs Safety Review",
    no_protective_system_reason: "",
    assigned_asset_ids: "",
    access_egress_required: null, access_egress_installed: null, access_egress_within_25ft: null,
    ladder_extends_above_landing: null, access_egress_secure: null,
    utility_locate_required: null, locate_ticket_number: "", locate_status: "Not Required",
    utility_conflicts_observed: null, utility_notes: "",
    spoils_2ft_from_edge: null, equipment_near_edge: null, barricades_in_place: null, stop_logs_used: null,
    water_present: null, seepage_present: null, dewatering_required: null, dewatering_active: null, water_needs_review: null,
    deep_or_confined_concern: null, hazardous_atmosphere_concern: null,
    atmospheric_testing_required: null, atmospheric_testing_completed: null, atmospheric_notes: "",
    competent_person_name: "", competent_person_confirmed: false,
    inspection_before_entry_completed: null, reinspection_required: null, reinspection_completed: null,
    field_notes: "",
    source: sp.get("source") || "public_tile",
  }));
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(null);
  const [err, setErr] = useState("");

  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const onText = (k) => (e) => set(k, e.target.value);

  async function submit() {
    setErr("");
    if (!f.project_name.trim() || !f.supervisor_name.trim() || !f.submitted_by.trim()) {
      setErr(t("Project, Supervisor, and Submitted By are required."));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...f,
        length_ft: f.length_ft ? Number(f.length_ft) : null,
        width_ft: f.width_ft ? Number(f.width_ft) : null,
        depth_ft: f.depth_ft ? Number(f.depth_ft) : null,
        assigned_asset_ids: f.assigned_asset_ids.split(/[, \n]+/).map((s) => s.trim().toUpperCase()).filter(Boolean),
        language: currentLang,
      };
      const r = await api.post("/trench-safety/excavations/public/submit", payload);
      setDone(r.data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setErr(t("Submission failed.") + " " + (e?.response?.data?.detail || e?.message || ""));
    } finally {
      setSaving(false);
    }
  }

  // ── Success shell ──────────────────────────────────────────────
  if (done) {
    return (
      <div className="min-h-screen bg-slate-50" data-testid="public-excavation-page">
        <div className="caution-stripe" />
        <PublicTrenchHeader
          backTo="/trench-safety"
          backLabel="Back to Trench Safety"
          testIdPrefix="public-excavation"
          accent="cyan"
        />
        <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
          <div className="text-center mb-4">
            <CheckCircle2 className="w-7 h-7 mx-auto text-emerald-700" />
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold mt-1">
              {t("MASCI Trench Safety")} · {t("Field Submission")}
            </div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-excavation-success-title">
              {t("Excavation Record Submitted")}
            </h1>
          </div>
          <div className="bg-white border-2 border-emerald-300 rounded-md p-4" data-testid="excavation-success">
            <div className="font-mono text-2xl font-black text-slate-900" data-testid="public-excavation-success-id">{done.id}</div>
            <div className="mt-1 text-sm text-slate-700">
              {t("Status")}: <b className="text-cyan-900">{t(done.status)}</b>
            </div>
            {done.flags?.length > 0 && (
              <div className="mt-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800 font-bold">
                  {t("Coaching Flags")}
                </div>
                <ul className="mt-1 space-y-1">
                  {done.flags.map((fl, i) => (
                    <li key={i} className="text-xs text-amber-900 flex gap-2" data-testid={`exc-flag-${fl.code}`}>
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      <span><b>{t(fl.level)}</b> — {t(fl.message)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-4 text-xs text-slate-600 leading-relaxed">
              {t("Safety has been notified. A competent person will follow up on any coaching flag above. The job site is not changed by this submission — keep working safely.")}
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between gap-2">
            <Link to="/trench-safety" className="inline-flex items-center gap-1 text-cyan-800 underline text-xs font-bold uppercase tracking-[0.12em]" data-testid="public-excavation-back-link">
              {t("Back to Trench Safety")} <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <button
              type="button"
              onClick={() => { setDone(null); window.scrollTo({ top: 0 }); }}
              className="bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-[0.12em] text-xs px-4 py-2 rounded"
              data-testid="public-excavation-new-record"
            >
              {t("Submit Another Record")}
            </button>
          </div>
          <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
            {t("MASCI Operations Platform")} · {t("Field-safe view")}
          </footer>
        </main>
      </div>
    );
  }

  // ── Main form shell (matches PublicTrenchSafetyDashboard / Report) ──
  return (
    <div className="min-h-screen bg-slate-50" data-testid="public-excavation-page">
      <div className="caution-stripe" />
      <PublicTrenchHeader
        backTo="/trench-safety"
        backLabel="Back to Trench Safety"
        testIdPrefix="public-excavation"
        accent="cyan"
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
        {/* Title block */}
        <div className="text-center mb-4">
          <ScanLine className="w-7 h-7 mx-auto text-cyan-700" />
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold mt-1">
            {t("MASCI Trench Safety")} · {t("Field Excavation Record")}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1" data-testid="public-excavation-title">
            {t("Excavation Operations")}
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto mt-2" data-testid="public-excavation-purpose">
            {t("Coaching first — if unsure on any field, select 'Needs Review' and Safety will follow up. This record does not move assets or change job-site status.")}
          </p>
        </div>

        {/* Stop-Work + Competent-Person coaching strip — same pattern as dashboard */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4" data-testid="public-excavation-coaching-row">
          <div className="bg-red-50 border-2 border-red-300 rounded-md p-3 flex items-start gap-2" data-testid="public-excavation-stopwork">
            <OctagonAlert className="w-4 h-4 text-red-700 mt-0.5 shrink-0" />
            <p className="text-xs text-red-900 leading-snug">
              <strong className="uppercase tracking-[0.08em]">{t("Stop-Work Authority.")}</strong>{" "}
              {t("If anything looks wrong, stop the job. You will never be punished for keeping a crew alive.")}
            </p>
          </div>
          <div className="bg-amber-50 border border-amber-300 rounded-md p-3 flex items-start gap-2" data-testid="public-excavation-coaching">
            <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-900 leading-snug">
              <strong>{t("Coaching, not punishment.")}</strong>{" "}
              {t("Flags mean Safety will follow up — not that you did anything wrong.")}
            </p>
          </div>
        </div>

        {/* Form sections */}
        <Section num="1" title={t("Project / Job Information")} testId="exc-section-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div><Label className="text-xs font-bold">{t("Project")} *</Label><Input value={f.project_name} onChange={onText("project_name")} data-testid="exc-project" /></div>
            <div><Label className="text-xs font-bold">{t("Project Number")}</Label><Input value={f.project_number} onChange={onText("project_number")} data-testid="exc-projno" /></div>
            <div><Label className="text-xs font-bold">{t("Location")}</Label><Input value={f.location} onChange={onText("location")} data-testid="exc-location" /></div>
            <div><Label className="text-xs font-bold">{t("Work Area")}</Label><Input value={f.work_area} onChange={onText("work_area")} data-testid="exc-workarea" /></div>
            <div><Label className="text-xs font-bold">{t("Date of Work")}</Label><Input type="date" value={f.date_of_work} onChange={onText("date_of_work")} data-testid="exc-date" /></div>
            <div><Label className="text-xs font-bold">{t("Supervisor / Foreman")} *</Label><Input value={f.supervisor_name} onChange={onText("supervisor_name")} data-testid="exc-supervisor" /></div>
            <div><Label className="text-xs font-bold">{t("Crew")}</Label><Input value={f.crew} onChange={onText("crew")} data-testid="exc-crew" /></div>
            <div><Label className="text-xs font-bold">{t("Submitted By")} *</Label><Input value={f.submitted_by} onChange={onText("submitted_by")} data-testid="exc-submittedby" /></div>
            <div><Label className="text-xs font-bold">{t("Contact Phone")}</Label><Input value={f.contact_phone} onChange={onText("contact_phone")} data-testid="exc-phone" /></div>
          </div>
        </Section>

        <Section num="2" title={t("Excavation Dimensions")} testId="exc-section-2">
          <div className="grid grid-cols-3 gap-2">
            <div><Label className="text-xs font-bold">{t("Length (ft)")}</Label><Input type="number" value={f.length_ft} onChange={onText("length_ft")} data-testid="exc-length" /></div>
            <div><Label className="text-xs font-bold">{t("Width (ft)")}</Label><Input type="number" value={f.width_ft} onChange={onText("width_ft")} data-testid="exc-width" /></div>
            <div><Label className="text-xs font-bold">{t("Depth (ft)")}</Label><Input type="number" value={f.depth_ft} onChange={onText("depth_ft")} data-testid="exc-depth" /></div>
          </div>
          <div className="mt-2 space-y-2">
            <div><Label className="text-xs">{t("Is excavation 4 feet or deeper?")}</Label><Bool value={f.depth_ge_4ft} onChange={(v) => set("depth_ge_4ft", v)} testId="exc-ge4" /></div>
            <div><Label className="text-xs">{t("Is excavation 5 feet or deeper?")}</Label><Bool value={f.depth_ge_5ft} onChange={(v) => set("depth_ge_5ft", v)} testId="exc-ge5" /></div>
            <div><Label className="text-xs">{t("Cave-in hazard under 5 ft?")}</Label><Bool value={f.cave_in_hazard_under_5ft} onChange={(v) => set("cave_in_hazard_under_5ft", v)} testId="exc-cavein" /></div>
          </div>
        </Section>

        <Section num="3" title={t("Work Type")} testId="exc-section-3">
          <Select value={f.work_type} onValueChange={(v) => set("work_type", v)}>
            <SelectTrigger data-testid="exc-worktype"><SelectValue /></SelectTrigger>
            <SelectContent>{WORK_TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
          </Select>
        </Section>

        <Section num="4" title={t("Soil / Ground Conditions")} testId="exc-section-4">
          <Select value={f.soil_classification} onValueChange={(v) => set("soil_classification", v)}>
            <SelectTrigger data-testid="exc-soil"><SelectValue /></SelectTrigger>
            <SelectContent>{SOILS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
          </Select>
          <p className="text-xs text-slate-500 mt-1">{t("If unsure, select Unknown / Needs Review — Safety will follow up.")}</p>
        </Section>

        <Section num="5" title={t("Protective System")} testId="exc-section-5">
          <Select value={f.protective_system} onValueChange={(v) => set("protective_system", v)}>
            <SelectTrigger data-testid="exc-protective"><SelectValue /></SelectTrigger>
            <SelectContent>{PROTECT.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
          </Select>
          {f.protective_system === "Not Required" && (f.depth_ge_5ft === true) && (
            <div className="mt-2">
              <Label className="text-xs font-bold">{t("Explain (required when 5 ft+ and Not Required)")}</Label>
              <Textarea value={f.no_protective_system_reason} onChange={onText("no_protective_system_reason")} rows={2} data-testid="exc-noprotect-reason" />
            </div>
          )}
        </Section>

        <Section num="6" title={t("Assigned Trench Safety Assets")} testId="exc-section-6">
          <Label className="text-xs">{t("Enter asset IDs (TB-XX, RP-XXX, EP-XXX...). Comma-separated.")}</Label>
          <Input value={f.assigned_asset_ids} onChange={onText("assigned_asset_ids")} placeholder="TB-01, RP-002" className="font-mono uppercase" data-testid="exc-assets" />
        </Section>

        <Section num="7" title={t("Access / Egress")} testId="exc-section-7">
          {[
            ["access_egress_required", "Access/egress required?"],
            ["access_egress_installed", "Access/egress installed?"],
            ["access_egress_within_25ft", "Within 25 ft lateral travel?"],
            ["ladder_extends_above_landing", "Ladder extends above landing?"],
            ["access_egress_secure", "Access/egress secure?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
        </Section>

        <Section num="8" title={t("Utility Locate")} testId="exc-section-8">
          <div className="mt-1"><Label className="text-xs">{t("Utility locate required?")}</Label><Bool value={f.utility_locate_required} onChange={(v) => set("utility_locate_required", v)} testId="exc-locate-req" /></div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div><Label className="text-xs font-bold">{t("Ticket Number")}</Label><Input value={f.locate_ticket_number} onChange={onText("locate_ticket_number")} data-testid="exc-locate-ticket" /></div>
            <div>
              <Label className="text-xs font-bold">{t("Locate Status")}</Label>
              <Select value={f.locate_status} onValueChange={(v) => set("locate_status", v)}>
                <SelectTrigger data-testid="exc-locate-status"><SelectValue /></SelectTrigger>
                <SelectContent>{LOCATE.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-2"><Label className="text-xs">{t("Utility conflicts observed?")}</Label><Bool value={f.utility_conflicts_observed} onChange={(v) => set("utility_conflicts_observed", v)} testId="exc-locate-conflict" /></div>
          <div className="mt-2"><Label className="text-xs font-bold">{t("Utility Notes")}</Label><Textarea value={f.utility_notes} onChange={onText("utility_notes")} rows={2} data-testid="exc-utility-notes" /></div>
        </Section>

        <Section num="9" title={t("Spoils / Edge Protection")} testId="exc-section-9">
          {[
            ["spoils_2ft_from_edge", "Spoils ≥ 2 ft from edge?"],
            ["equipment_near_edge", "Equipment / materials near edge?"],
            ["barricades_in_place", "Barricades in place?"],
            ["stop_logs_used", "Stop logs / warning system?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
        </Section>

        <Section num="10" title={t("Water Conditions")} testId="exc-section-10">
          {[
            ["water_present", "Water present?"],
            ["seepage_present", "Seepage present?"],
            ["dewatering_required", "Dewatering required?"],
            ["dewatering_active", "Dewatering active?"],
            ["water_needs_review", "Needs Safety review?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
        </Section>

        <Section num="11" title={t("Atmosphere / Hazard Conditions")} testId="exc-section-11">
          {[
            ["deep_or_confined_concern", "Deep / confined hazard concern?"],
            ["hazardous_atmosphere_concern", "Hazardous atmosphere concern?"],
            ["atmospheric_testing_required", "Atmospheric testing required?"],
            ["atmospheric_testing_completed", "Atmospheric testing completed?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
          <div className="mt-2"><Label className="text-xs font-bold">{t("Notes")}</Label><Textarea value={f.atmospheric_notes} onChange={onText("atmospheric_notes")} rows={2} data-testid="exc-atm-notes" /></div>
        </Section>

        <Section num="12" title={t("Competent Person")} testId="exc-section-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div><Label className="text-xs font-bold">{t("Competent Person Name")}</Label><Input value={f.competent_person_name} onChange={onText("competent_person_name")} data-testid="exc-cp-name" /></div>
            <div className="flex items-end gap-2">
              <input id="cp-conf" type="checkbox" checked={f.competent_person_confirmed} onChange={(e) => set("competent_person_confirmed", e.target.checked)} data-testid="exc-cp-confirmed" />
              <Label htmlFor="cp-conf" className="text-xs">{t("I confirm CP role for this excavation")}</Label>
            </div>
          </div>
          {[
            ["inspection_before_entry_completed", "Pre-entry inspection completed?"],
            ["reinspection_required", "Reinspection required (rain / change)?"],
            ["reinspection_completed", "Reinspection completed?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
        </Section>

        <Section num="13" title={t("Photos")} testId="exc-section-13">
          <p className="text-xs text-slate-500">
            {t("Photos can be uploaded after submission via the asset photo workflow.")}
          </p>
        </Section>

        <Section num="14" title={t("Field Notes")} testId="exc-section-14">
          <Textarea
            value={f.field_notes}
            onChange={onText("field_notes")}
            rows={3}
            placeholder={t("Notes can be English or Spanish — both are preserved.")}
            data-testid="exc-fieldnotes"
          />
        </Section>

        {/* Competent-person reminder — mirrors dashboard */}
        <section className="mt-4 p-3 border border-slate-200 bg-white rounded" data-testid="public-excavation-competent">
          <div className="flex items-start gap-2">
            <HardHat className="w-4 h-4 text-cyan-700 mt-0.5 shrink-0" />
            <div className="text-xs text-slate-700 leading-relaxed">
              <strong className="text-slate-900 uppercase tracking-[0.06em]">{t("Competent Person Required.")}</strong>{" "}
              {t("Every trench 5 ft or deeper needs a designated competent person on-site — trained to identify hazards, authorized to correct them, and present before crews enter. No competent person, no entry.")}
            </div>
          </div>
        </section>

        {err && (
          <div className="mt-3 text-sm text-red-900 bg-red-50 border border-red-300 rounded p-3" data-testid="public-excavation-error">
            {err}
          </div>
        )}

        <div className="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
          <Link
            to="/trench-safety"
            className="inline-flex items-center justify-center gap-1 text-cyan-800 underline text-xs font-bold uppercase tracking-[0.12em] py-2"
            data-testid="public-excavation-cancel-link"
          >
            {t("Cancel · Back to Trench Safety")}
          </Link>
          <Button
            onClick={submit}
            disabled={saving}
            className="bg-cyan-700 hover:bg-cyan-800 h-12 px-6 text-sm font-bold uppercase tracking-[0.12em]"
            data-testid="exc-submit"
          >
            {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : t("Submit Excavation Record")}
          </Button>
        </div>

        <footer className="mt-8 text-center text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono">
          {t("MASCI Operations Platform")} · {t("Field-safe view")}
        </footer>
      </main>
    </div>
  );
}
