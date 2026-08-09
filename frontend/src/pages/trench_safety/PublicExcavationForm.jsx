// Phase 10A · Public Excavation Operations Form (G-1 closure)
// Phase 10A-B · Integration Hardening (OMEGA Correction Directive)
//
// Public field-safe submit · EN / ES · 14 sections.
// Now pinned to certified MASCI platform sources:
//   • Project   → JobPicker (jobs_master)
//   • Personnel → EmployeePicker (employees roster)
//   • Assets    → TrenchAssetPicker (trench_safety_assets registry)
//   • Road Plates → TrenchAssetPicker filtered by asset_type=Road Plate
//   • OSHA coaching blocks embedded inline at every decision point
//   • Smart OSHA triggers expand sections automatically
//
// Route: /trench-safety/excavation/new  (public, no auth)
// Also accepts query params (?project_number=… &source=daily_report
// &daily_report_id=… &supervisor=…) when triggered FROM a Daily Report.
import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import {
  Loader2, CheckCircle2, AlertTriangle, HardHat, OctagonAlert, ShieldAlert, ScanLine, ArrowRight, Briefcase, Users, Package, Layers, Camera,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import OshaCoachingBlock from "@/components/trench/OshaCoachingBlock";
import EmployeePicker from "@/components/trench/EmployeePicker";
import TrenchAssetPicker from "@/components/trench/TrenchAssetPicker";
import ExcavationComplianceCard from "@/components/trench/ExcavationComplianceCard";
import { JobPicker } from "@/components/JobPicker";
import { Section as BaseSection } from "@/components/Section";
import { computeExcavationCompliance } from "@/lib/excavationCompliance";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { translateUserInput, persistBilingualSidecar } from "@/lib/translateOnSubmit";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";

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
            (value === v ? "border-cyan-700 bg-cyan-700 text-white" : "border-slate-300 bg-white text-slate-700 hover:border-cyan-500")}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

function Section({ num, title, children, highlight, testId }) {
  // Track 14.0-F1 · delegate to canonical Section primitive with cyan accent
  // + dense mode (legacy public-form density preserved). Adds print-break,
  // smart-trigger badge translation, and ring-on-highlight consistency.
  return (
    <BaseSection
      number={num}
      title={title}
      accent="cyan"
      dense
      highlight={!!highlight}
      testId={testId || `exc-section-${num}`}
    >
      {children}
    </BaseSection>
  );
}

export default function PublicExcavationForm() {
  const { t, lang } = useT();
  const currentLang = lang || "en";
  const [sp] = useSearchParams();

  const [f, setF] = useState(() => ({
    // Job (Correction 2)
    job_id: "",
    project_name: sp.get("project_name") || "",
    project_number: sp.get("project_number") || "",
    customer: "",
    project_manager: "",
    pm_email: "",
    location: sp.get("location") || "",
    work_area: "",
    date_of_work: sp.get("date") || new Date().toISOString().slice(0, 10),
    // Personnel (Correction 3)
    prepared_by_id: "", prepared_by_name: "",
    foreman_id: "", foreman_name: sp.get("supervisor") || "",
    leadman_id: "", leadman_name: "",
    superintendent_id: "", superintendent_name: "",
    supervisor_name: sp.get("supervisor") || "",
    crew: sp.get("crew") || "",
    submitted_by: "", contact_phone: "",
    // Dimensions
    length_ft: "", width_ft: "", depth_ft: "", depth_unit: "ft",
    depth_ge_4ft: null, depth_ge_5ft: null, cave_in_hazard_under_5ft: null,
    work_type: "Other", soil_classification: "Unknown / Needs Review",
    protective_system: "Needs Safety Review", no_protective_system_reason: "",
    // Assets (Corrections 4 + 5)
    assigned_asset_ids: [],
    road_plates_used: null, road_plate_ids: [],
    // Access / Egress
    access_egress_required: null, access_egress_installed: null, access_egress_within_25ft: null,
    ladder_extends_above_landing: null, access_egress_secure: null,
    // Utility locate
    utility_locate_required: null, locate_ticket_number: "", locate_status: "Not Required",
    utility_conflicts_observed: null, utility_notes: "",
    // Spoils / Edge
    spoils_2ft_from_edge: null, equipment_near_edge: null, barricades_in_place: null, stop_logs_used: null,
    // Water
    water_present: null, seepage_present: null, dewatering_required: null, dewatering_active: null, water_needs_review: null,
    // Atmosphere
    deep_or_confined_concern: null, hazardous_atmosphere_concern: null,
    atmospheric_testing_required: null, atmospheric_testing_completed: null, atmospheric_notes: "",
    // Competent Person + reinspection
    competent_person_id: "", competent_person_name: "", competent_person_confirmed: false,
    inspection_before_entry_completed: null, reinspection_required: null, reinspection_completed: null,
    rain_event_observed: null,
    // Photos (Correction 8)
    photos: [],
    // Field notes (Correction 9)
    field_notes: "",
    field_notes_original_language: currentLang,
    field_notes_original_text: "",
    source: sp.get("source") || "public_tile",
    triggered_from_daily_report_id: sp.get("daily_report_id") || "",
    // FV-7.1 · Rated-depth acknowledgement (foreman-side)
    rated_depth_acknowledged: null,
    rated_depth_acknowledgement_reason: "",
    rated_depth_tabulated_data_exception: false,
    // FV-7.5 · Emergency excavation flag
    emergency_excavation: null,
  }));
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(null);
  const [err, setErr] = useState("");
  // FV-7.1 · in-form roster cache so the rated-depth check is deterministic
  // without an extra round-trip. Roster items already include rated_depth_ft.
  const [assetRoster, setAssetRoster] = useState([]);
  useEffect(() => {
    let alive = true;
    api.get("/trench-safety/excavations/public/asset-roster")
      .then((r) => { if (alive) setAssetRoster(Array.isArray(r.data?.items) ? r.data.items : []); })
      .catch(() => { if (alive) setAssetRoster([]); });
    return () => { alive = false; };
  }, []);

  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const onText = (k) => (e) => set(k, e.target.value);

  // Phase 10C · Live compliance state — single source of truth for the
  // operational decision-support panel AND for which sections render.
  const compliance = useMemo(() => computeExcavationCompliance(f), [f]);
  const visible = compliance.visibleSections;
  const triggers = {
    access:     visible.has("7"),
    protective: (Number(f.depth_ft) || 0) >= 5,
    cp:         (Number(f.depth_ft) || 0) >= 5,
    soilC:      f.soil_classification === "Type C",
    water:      visible.has("10"),
    atmos:      visible.has("11"),
    rain:       f.rain_event_observed === true,
    utility:    visible.has("8"),
  };

  // FV-7.1 · Compute rated-depth gap from selected trench-box assets.
  // The roster items carry rated_depth_ft + asset_type; the foreman
  // sees a red ACTION REQUIRED panel only when there is a real gap.
  const ratedDepthGap = useMemo(() => {
    const depthN = Number(f.depth_ft) || 0;
    if (!depthN) return null;
    const ids = f.assigned_asset_ids || [];
    if (!ids.length) return null;
    const offenders = [];
    for (const id of ids) {
      const a = assetRoster.find((x) => x.asset_id === id);
      if (!a) continue;
      if (!["Trench Box", "Shielding"].includes(a.asset_type)) continue;
      if (a.rated_depth_ft != null && Number(a.rated_depth_ft) < depthN) {
        offenders.push({ asset_id: a.asset_id, rated_depth_ft: Number(a.rated_depth_ft) });
      }
    }
    return offenders.length ? { depth: depthN, offenders } : null;
  }, [f.depth_ft, f.assigned_asset_ids, assetRoster]);

  function onJobSelect(job) {
    if (!job) {
      // Custom job — clear bound fields
      setF((p) => ({ ...p, job_id: "", project_name: "", project_number: "", location: "", customer: "", project_manager: "", pm_email: "" }));
      return;
    }
    setF((p) => ({
      ...p,
      job_id: job.id || "",
      project_name: job.project_name || "",
      project_number: job.project_number || "",
      location: job.location || p.location,
      customer: job.client || job.customer || "",
      project_manager: job.project_manager || "",
      pm_email: job.pm_email || "",
    }));
  }

  async function submit() {
    setErr("");
    if (!f.job_id && !f.project_name.trim()) {
      setErr(t("Pick a Job (or type a custom project name) before submitting."));
      return;
    }
    if (!f.foreman_name.trim() && !f.supervisor_name.trim()) {
      setErr(t("Select a Foreman / Supervisor from the roster."));
      return;
    }
    if (!f.submitted_by.trim()) {
      setErr(t("Submitted By is required."));
      return;
    }
    // FV-7.1 · Soft-gate: if a rated-depth gap is present, foreman must
    // acknowledge with a reason (or tick the tabulated-data exception).
    // We never hard-block — we require deliberate acknowledgement.
    if (ratedDepthGap && !f.rated_depth_acknowledged) {
      setErr(t("Acknowledge the trench-box rated-depth gap with a reason before submitting."));
      return;
    }
    if (ratedDepthGap && f.rated_depth_acknowledged &&
        !(f.rated_depth_acknowledgement_reason || "").trim() &&
        !f.rated_depth_tabulated_data_exception) {
      setErr(t("Add a reason or check the tabulated-data exception."));
      return;
    }
    setSaving(true);
    try {
      const depthNum = Number(f.depth_ft) || 0;
      const rawPayload = {
        ...f,
        length_ft: f.length_ft ? Number(f.length_ft) : null,
        width_ft: f.width_ft ? Number(f.width_ft) : null,
        depth_ft: f.depth_ft ? Number(f.depth_ft) : null,
        // Phase 10C · Auto-derive depth flags. The form no longer asks
        // the foreman to do this arithmetic.
        depth_ge_4ft: depthNum > 0 ? depthNum >= 4 : f.depth_ge_4ft,
        depth_ge_5ft: depthNum > 0 ? depthNum >= 5 : f.depth_ge_5ft,
        // ensure supervisor_name mirror for backwards compat
        supervisor_name: f.supervisor_name || f.foreman_name,
        language: currentLang,
        field_notes_original_text: f.field_notes,
        field_notes_original_language: currentLang,
      };
      // TRACK 14.0-S1-B5 — translate Spanish free-text to English BEFORE the
      // canonical excavation record is stored. Office PDFs / notifications /
      // search / exports must read clean English. The original field_notes
      // are also kept verbatim in `field_notes_original_text` (existing
      // backend convention) for fast inline rendering on the trench portal,
      // and the full sidecar is persisted below for audit.
      const translated = await translateUserInput(rawPayload, currentLang);
      const payload = { ...translated };
      delete payload._originals;
      delete payload._original_language;
      delete payload._translated_at;
      delete payload._translation_source;
      const r = await api.post("/trench-safety/excavations/public/submit", payload);
      // Best-effort: write the bilingual sidecar so the original Spanish is
      // preserved for audit while the canonical record stays English.
      const newId = r?.data?.id || r?.data?.excavation_id;
      if (newId) {
        await persistBilingualSidecar("trench_excavation", newId, translated);
      }
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
    return <SuccessScreen done={done} setDone={setDone} t={t} />;
  }

  // ── Main form shell ─────────────────────────────────────────────
  return (
    <OperationalPageFrame
      testId="public-excavation-page"
      backTo="/trench-safety"
      backLabel={t("Back to Trench Safety")}
      accent="cyan"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-5xl"
      heroIcon={ScanLine}
      kicker={t("Trench Safety · Field Excavation Record")}
      title={t("Excavation Operations")}
      description={t("The platform thinks first and the crew verifies. Compliance is calculated live so only the sections that apply to this trench show up below.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="cyan" testId="public-excavation-meta-live">{t("Live compliance")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="amber" testId="public-excavation-meta-dynamic">{t("Dynamic sections")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="red" testId="public-excavation-meta-stop">{t("Stop-work authority")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="public-excavation-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">{t("What this record does")}</div>
          <p className="text-sm text-slate-600 mb-3">
            {t("Use this route when crews need the field-safe excavation workflow with OSHA coaching, roster picks, trench-asset matching, and direct Safety follow-up.")}
          </p>
          <div className="space-y-2 text-xs text-slate-700">
            <div>{t("• Pulls jobs, roster, and trench assets from certified sources")}</div>
            <div>{t("• Expands only the sections your conditions trigger")}</div>
            <div>{t("• Preserves bilingual field notes with an approved English copy for reporting")}</div>
          </div>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Excavation workflow")}
    >
      <div className="space-y-5">

        {/* Phase 10C · Live operational decision-support panel */}
        <ExcavationComplianceCard result={compliance} />

        {/* Stop-Work + Coaching */}
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

        {/* Section 1 — Job (JobPicker) */}
        <Section num="1" title={t("Job · Project Information")} testId="exc-section-1">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-600">
            <Briefcase className="w-4 h-4 text-cyan-700" />
            <span>{t("Same job source as Daily Reports.")}</span>
          </div>
          <JobPicker
            projectName={f.project_name}
            projectNumber={f.project_number}
            publicFallback
            onSelect={onJobSelect}
            data-testid="exc-jobpicker"
          />
          {/* Auto-populated read-only display */}
          {(f.project_number || f.customer || f.project_manager || f.location) && (
            <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs" data-testid="exc-job-autofill">
              {f.project_number && <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5"><span className="font-bold uppercase tracking-[0.08em] text-slate-500 mr-1">{t("Project #")}</span><span className="font-mono">{f.project_number}</span></div>}
              {f.customer && <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5"><span className="font-bold uppercase tracking-[0.08em] text-slate-500 mr-1">{t("Customer")}</span>{f.customer}</div>}
              {f.project_manager && <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5"><span className="font-bold uppercase tracking-[0.08em] text-slate-500 mr-1">{t("PM")}</span>{f.project_manager}</div>}
              {f.location && <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5"><span className="font-bold uppercase tracking-[0.08em] text-slate-500 mr-1">{t("Location")}</span>{f.location}</div>}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-2">
            <div className="min-w-0"><Label className="text-xs font-bold">{t("Work Area")}</Label><Input value={f.work_area} onChange={onText("work_area")} data-testid="exc-workarea" /></div>
            <div className="min-w-0"><Label className="text-xs font-bold">{t("Date of Work")}</Label><Input type="date" value={f.date_of_work} onChange={onText("date_of_work")} data-testid="exc-date" /></div>
            <div className="min-w-0"><Label className="text-xs font-bold">{t("Crew")}</Label><Input value={f.crew} onChange={onText("crew")} data-testid="exc-crew" /></div>
          </div>
          {/* FV-7.5 · Emergency excavation toggle (surfaces on Superintendent chip) */}
          <div className="mt-3 bg-red-50 border border-red-200 rounded p-2" data-testid="exc-emergency-block">
            <Label className="text-xs font-bold text-red-900">{t("Emergency Excavation?")}</Label>
            <p className="text-[10px] text-red-800 leading-snug mb-1">
              {t("Unscheduled, life-safety, utility-strike, water-main break, or after-hours excavation. Yes routes this to the Superintendent's Emergency chip immediately.")}
            </p>
            <Bool value={f.emergency_excavation} onChange={(v) => set("emergency_excavation", v)} testId="exc-emergency" />
          </div>
        </Section>

        {/* Section 1b — Personnel (EmployeePicker) */}
        <Section num="1b" title={t("Field Leadership Roster")} testId="exc-section-1b">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-600">
            <Users className="w-4 h-4 text-cyan-700" />
            <span>{t("Pull from the certified roster — no manual typing.")}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div><Label className="text-xs font-bold">{t("Prepared By")}</Label>
              <EmployeePicker value={f.prepared_by_id} placeholder="Pick from roster…" testId="exc-prepared-by"
                onSelect={(e) => setF((p) => ({ ...p, prepared_by_id: e.id, prepared_by_name: e.name }))} />
            </div>
            <div><Label className="text-xs font-bold">{t("Foreman / Supervisor")} *</Label>
              <EmployeePicker value={f.foreman_id} placeholder="Pick from roster…" testId="exc-foreman" role="foreman"
                onSelect={(e) => setF((p) => ({ ...p, foreman_id: e.id, foreman_name: e.name, supervisor_name: e.name }))} />
            </div>
            <div><Label className="text-xs font-bold">{t("Leadman")}</Label>
              <EmployeePicker value={f.leadman_id} placeholder="Pick from roster…" testId="exc-leadman" role="leadman"
                onSelect={(e) => setF((p) => ({ ...p, leadman_id: e.id, leadman_name: e.name }))} />
            </div>
            <div><Label className="text-xs font-bold">{t("Superintendent")}</Label>
              <EmployeePicker value={f.superintendent_id} placeholder="Pick from roster…" testId="exc-superintendent" role="superintendent"
                onSelect={(e) => setF((p) => ({ ...p, superintendent_id: e.id, superintendent_name: e.name }))} />
            </div>
            <div><Label className="text-xs font-bold">{t("Submitted By")} *</Label>
              <Input value={f.submitted_by} onChange={onText("submitted_by")} placeholder={t("Your email or name")} data-testid="exc-submittedby" /></div>
            <div><Label className="text-xs font-bold">{t("Contact Phone")}</Label>
              <Input value={f.contact_phone} onChange={onText("contact_phone")} data-testid="exc-phone" /></div>
          </div>
        </Section>

        {/* Section 2 — Dimensions */}
        <Section num="2" title={t("Excavation Dimensions")} testId="exc-section-2" highlight={(Number(f.depth_ft) || 0) >= 4}>
          <div className="grid grid-cols-3 gap-2">
            <div><Label className="text-xs font-bold">{t("Length (ft)")}</Label><Input type="number" value={f.length_ft} onChange={onText("length_ft")} data-testid="exc-length" /></div>
            <div><Label className="text-xs font-bold">{t("Width (ft)")}</Label><Input type="number" value={f.width_ft} onChange={onText("width_ft")} data-testid="exc-width" /></div>
            <div><Label className="text-xs font-bold">{t("Depth (ft)")}</Label><Input type="number" value={f.depth_ft} onChange={onText("depth_ft")} data-testid="exc-depth" /></div>
          </div>
          {/* Phase 10C · Depth flags are now auto-derived. Show as a read-only chip. */}
          {(Number(f.depth_ft) || 0) > 0 && (
            <div className="mt-2 inline-flex flex-wrap items-center gap-1.5 text-[10px] font-mono uppercase tracking-[0.12em]" data-testid="exc-depth-derived">
              <span className={(Number(f.depth_ft) || 0) >= 4 ? "bg-cyan-700 text-white px-2 py-0.5 rounded" : "bg-slate-200 text-slate-700 px-2 py-0.5 rounded"}>
                {t(((Number(f.depth_ft) || 0) >= 4) ? "≥ 4 ft (access required)" : "< 4 ft")}
              </span>
              <span className={(Number(f.depth_ft) || 0) >= 5 ? "bg-red-700 text-white px-2 py-0.5 rounded" : "bg-slate-200 text-slate-700 px-2 py-0.5 rounded"}>
                {t(((Number(f.depth_ft) || 0) >= 5) ? "≥ 5 ft (protective system required)" : "< 5 ft")}
              </span>
              <span className="text-slate-500">{t("Auto-derived from depth — no toggle needed.")}</span>
            </div>
          )}
        </Section>

        {/* Section 3 — Work type */}
        <Section num="3" title={t("Work Type")} testId="exc-section-3">
          <Select value={f.work_type} onValueChange={(v) => set("work_type", v)}>
            <SelectTrigger data-testid="exc-worktype"><SelectValue /></SelectTrigger>
            <SelectContent>{WORK_TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
          </Select>
        </Section>

        {/* Section 4 — Soil */}
        <Section num="4" title={t("Soil / Ground Conditions")} testId="exc-section-4" highlight={triggers.soilC || f.soil_classification === "Unknown / Needs Review"}>
          <Select value={f.soil_classification} onValueChange={(v) => set("soil_classification", v)}>
            <SelectTrigger data-testid="exc-soil"><SelectValue /></SelectTrigger>
            <SelectContent>{SOILS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
          </Select>
          <OshaCoachingBlock
            testId="coach-soil"
            title="Soil Classification"
            why="Soil type determines what protective system you need. Misclassifying soil is the #1 cause of fatal trench collapses."
            requirement="29 CFR 1926.652(b) — Soil must be classified by a competent person before crews enter a 5 ft+ excavation."
            example="Sandy gravel that crumbles easily = Type C. Dry, fissured clay = Type B. Solid stable rock = Stable Rock."
            mistakes="Assuming the same soil as last week. Soil changes with rain, freeze/thaw, and depth. Reclassify when conditions change."
            escalate="If you see layered soils, water seepage, or recent disturbance — stop and call Safety."
            ifUnsure="Pick 'Unknown / Needs Review'. Safety will dispatch a competent person."
            defaultOpen={triggers.soilC}
            tone={triggers.soilC ? "red" : "amber"}
          />
        </Section>

        {/* Section 5 — Protective system */}
        <Section num="5" title={t("Protective System")} testId="exc-section-5" highlight={triggers.protective}>
          {/* Phase 10C · Smart suggestion based on soil + depth */}
          {compliance.suggestedPs && f.protective_system !== compliance.suggestedPs && (
            <button
              type="button"
              onClick={() => set("protective_system", compliance.suggestedPs)}
              className="mb-2 inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-[0.10em] bg-cyan-50 hover:bg-cyan-100 border border-cyan-300 text-cyan-900 rounded px-2 py-1"
              data-testid="exc-protective-suggest"
            >
              💡 {t("Suggested:")} {t(compliance.suggestedPs)} <span className="opacity-70 ml-1">→ {t("apply")}</span>
            </button>
          )}
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
          <OshaCoachingBlock
            testId="coach-protective"
            title="Protective Systems"
            why="At 5 ft and deeper, an unprotected trench can collapse without warning. A cubic yard of soil weighs roughly 3,000 pounds."
            requirement="29 CFR 1926.652(a)(1) — Each crew member must be protected from cave-ins by sloping, benching, shoring, or shielding (trench box)."
            example="6 ft deep utility trench in Type B soil → use a Trench Box rated for ≥ 6 ft, OR slope 1H:1V on each side."
            mistakes="Mixing systems incorrectly. Trench box that doesn't extend to the bottom. Sloping less than what the soil type requires."
            escalate="If the chosen system doesn't match the soil type or rated depth — stop and call the Safety competent person."
            ifUnsure="Pick 'Needs Safety Review'. Safety will reach out before crew descent."
            defaultOpen={triggers.protective}
            tone={triggers.protective ? "red" : "amber"}
          />
        </Section>

        {/* Section 6 — Trench assets */}
        <Section num="6" title={t("Assigned Trench Safety Assets")} testId="exc-section-6">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-600">
            <Package className="w-4 h-4 text-cyan-700" />
            <span>{t("Multi-select from the certified trench registry. Status / serial / open holds shown.")}</span>
          </div>
          <TrenchAssetPicker
            selected={f.assigned_asset_ids}
            onChange={(arr) => set("assigned_asset_ids", arr)}
            testId="exc-assets"
          />
          {/* FV-7.1 · Rated-depth gap — never blocks submit, requires acknowledgement */}
          {ratedDepthGap && (
            <div className="mt-3 bg-red-50 border-2 border-red-400 rounded-md p-3" data-testid="exc-rated-depth-gap">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-800 font-bold mb-1 inline-flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> {t("Action Required · Trench Box Rated Depth")}
              </div>
              <p className="text-[12px] text-red-900 leading-snug">
                {t("Your excavation depth")} <b>{ratedDepthGap.depth} ft</b> {t("exceeds the rated depth of:")}
              </p>
              <ul className="text-[11px] text-red-900 font-mono mt-1 mb-2 list-disc list-inside">
                {ratedDepthGap.offenders.map((o) => (
                  <li key={o.asset_id} data-testid={`exc-rated-depth-offender-${o.asset_id}`}>
                    {o.asset_id} · {t("rated")} {o.rated_depth_ft} ft
                  </li>
                ))}
              </ul>
              <p className="text-[11px] text-red-900 leading-snug mb-2">
                {t("Stacked boxes, engineered systems, or approved tabulated-data exceptions can legitimately exceed a simple rated-depth check. Acknowledge with a reason — Safety will verify.")}
              </p>
              <Label className="text-[11px] font-bold text-red-900">{t("Acknowledgement Reason")} *</Label>
              <Textarea
                value={f.rated_depth_acknowledgement_reason}
                onChange={onText("rated_depth_acknowledgement_reason")}
                placeholder={t("e.g. Stacked TB-04 over TB-06, engineered shoring per PE-stamped drawing 23-A4, manufacturer tabulated data ref…")}
                rows={2}
                data-testid="exc-rated-depth-ack-reason"
              />
              <label className="flex items-center gap-2 mt-1 text-[11px] text-red-900">
                <input type="checkbox" checked={!!f.rated_depth_tabulated_data_exception}
                  onChange={(e) => set("rated_depth_tabulated_data_exception", e.target.checked)}
                  data-testid="exc-rated-depth-ack-tabulated" />
                {t("Approved tabulated-data exception (manufacturer or PE-stamped engineering)")}
              </label>
              <label className="flex items-start gap-2 mt-2 text-[12px] font-bold text-red-900 cursor-pointer">
                <input type="checkbox" checked={!!f.rated_depth_acknowledged}
                  onChange={(e) => set("rated_depth_acknowledged", e.target.checked)}
                  data-testid="exc-rated-depth-ack-confirm" />
                {t("I acknowledge the rated-depth gap and the justification above is accurate.")}
              </label>
            </div>
          )}
        </Section>

        {/* Section 6b — Road Plates (Phase 10C: only when relevant) */}
        {visible.has("6b") && (
        <Section num="6b" title={t("Road Plates")} testId="exc-section-6b">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-600">
            <Layers className="w-4 h-4 text-cyan-700" />
            <span>{t("Pull from the certified Road Plate registry.")}</span>
          </div>
          <div><Label className="text-xs">{t("Road Plates Used?")}</Label>
            <Bool value={f.road_plates_used} onChange={(v) => set("road_plates_used", v)} testId="exc-road-plates-used" />
          </div>
          {f.road_plates_used === true && (
            <div className="mt-2">
              <TrenchAssetPicker
                selected={f.road_plate_ids}
                onChange={(arr) => set("road_plate_ids", arr)}
                assetType="Road Plate"
                testId="exc-road-plates"
              />
            </div>
          )}
        </Section>
        )}

        {/* Section 7 — Access / Egress */}
        {visible.has("7") && (
        <Section num="7" title={t("Access / Egress")} testId="exc-section-7" highlight={triggers.access}>
          {[
            ["access_egress_required", "Access/egress required?"],
            ["access_egress_installed", "Access/egress installed?"],
            ["access_egress_within_25ft", "Within 25 ft lateral travel?"],
            ["ladder_extends_above_landing", "Ladder extends above landing?"],
            ["access_egress_secure", "Access/egress secure?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
          <OshaCoachingBlock
            testId="coach-access"
            title="Access / Egress"
            why="When a trench collapses, you have seconds to get out. A ladder placed too far away is the same as no ladder at all."
            requirement="29 CFR 1926.651(c)(2) — At 4 ft or deeper, a ladder/ramp/stairway must be within 25 ft of lateral travel."
            example="50 ft long trench at 5 ft depth → need a ladder near each end (≤25 ft from any crew member)."
            mistakes="One ladder for a long trench. Ladder rungs not extending 3 ft above the landing. Aluminum ladders in soft soil."
            escalate="If a single ladder is missing or insecure — stop work until it's installed."
            ifUnsure="If the answer to 'Within 25 ft lateral travel?' is No or unknown — flip it to No and Safety will follow up."
            defaultOpen={triggers.access}
            tone={triggers.access ? "red" : "amber"}
          />
        </Section>
        )}

        {/* Section 8 — Utility locate */}
        {visible.has("8") && (
        <Section num="8" title={t("Utility Locate")} testId="exc-section-8" highlight={triggers.utility}>
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
          <OshaCoachingBlock
            testId="coach-utility"
            title="Utility Locate"
            why="Striking a live gas, electric, or fiber line can kill crew members and shut down a region for days."
            requirement="29 CFR 1926.651(b) — Estimated location of utilities must be determined BEFORE digging. State One-Call (811) ticket required for most public utility work."
            example="Ticket dated more than 14 days ago = expired in most states. Re-call before resuming."
            mistakes="Trusting old paint marks. Digging within tolerance zone (typically 18-24 in.) without hand-digging."
            escalate="If marks conflict with as-builts, or if you uncover an unmarked utility — stop and call Safety + 811."
            ifUnsure="Set Locate Status to 'Conflict / Needs Review'. Safety will validate before crew exposure."
            defaultOpen={triggers.utility && f.locate_status === "Pending"}
            tone="amber"
          />
        </Section>
        )}

        {/* Section 9 — Spoils / Edge */}
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

        {/* Section 10 — Water (Phase 10C: only when applicable) */}
        {visible.has("10") && (
        <Section num="10" title={t("Water Conditions")} testId="exc-section-10" highlight={triggers.water}>
          {[
            ["water_present", "Water present?"],
            ["seepage_present", "Seepage present?"],
            ["dewatering_required", "Dewatering required?"],
            ["dewatering_active", "Dewatering active?"],
            ["water_needs_review", "Needs Safety review?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
          <OshaCoachingBlock
            testId="coach-water"
            title="Water Conditions"
            why="Water reduces soil cohesion fast. A stable wall yesterday can collapse this afternoon after rain or upstream pumping."
            requirement="29 CFR 1926.651(h) — Crews must not work in standing water or accumulating water without special protection (dewatering, breathing equipment, safety harness)."
            example="Rain ≥ 0.5 inch = treat the soil as Type C until reclassified."
            mistakes="Pumping at the bottom of the trench without monitoring the surrounding soil. Ignoring seepage."
            escalate="If water rises faster than dewatering can manage — stop, evacuate, and call Safety."
            ifUnsure="Set 'Needs Safety review' to Yes — Safety will dispatch a competent person."
            defaultOpen={triggers.water}
            tone="amber"
          />
        </Section>
        )}

        {/* Section 11 — Atmosphere */}
        {visible.has("11") && (
        <Section num="11" title={t("Atmosphere / Hazard Conditions")} testId="exc-section-11" highlight={triggers.atmos}>
          {[
            ["deep_or_confined_concern", "Deep / confined hazard concern?"],
            ["hazardous_atmosphere_concern", "Hazardous atmosphere concern?"],
            ["atmospheric_testing_required", "Atmospheric testing required?"],
            ["atmospheric_testing_completed", "Atmospheric testing completed?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
          <div className="mt-2"><Label className="text-xs font-bold">{t("Notes")}</Label><Textarea value={f.atmospheric_notes} onChange={onText("atmospheric_notes")} rows={2} data-testid="exc-atm-notes" /></div>
          <OshaCoachingBlock
            testId="coach-atmos"
            title="Atmospheric Hazards"
            why="Sewer, fuel station, and landfill work can release methane, H2S, CO, or oxygen-deficient air. You can't see it or smell it until it's too late."
            requirement="29 CFR 1926.651(g)(1) — In 4 ft+ excavations where hazardous atmosphere could exist, testing must be done BEFORE entry and continuously while crew is working."
            example="Near a gas main or old sanitary line — assume the atmosphere is hazardous until tested."
            mistakes="Testing once and walking away. Trusting your nose. Using an expired 4-gas monitor."
            escalate="If readings exceed the meter's alarm thresholds — evacuate and ventilate immediately."
            ifUnsure="Set 'Atmospheric testing required' to Yes. A 4-gas monitor takes minutes; a fatality takes seconds."
            defaultOpen={triggers.atmos}
            tone={triggers.atmos ? "red" : "amber"}
          />
        </Section>
        )}

        {/* Section 12 — Competent Person */}
        <Section num="12" title={t("Competent Person")} testId="exc-section-12" highlight={triggers.cp}>
          <Label className="text-xs font-bold">{t("Competent Person Name")}</Label>
          <EmployeePicker value={f.competent_person_id} placeholder="Pick from roster…" testId="exc-cp-picker" role="competent"
            onSelect={(e) => setF((p) => ({ ...p, competent_person_id: e.id, competent_person_name: e.name }))} />
          <div className="flex items-end gap-2 mt-2">
            <input id="cp-conf" type="checkbox" checked={f.competent_person_confirmed} onChange={(e) => set("competent_person_confirmed", e.target.checked)} data-testid="exc-cp-confirmed" />
            <Label htmlFor="cp-conf" className="text-xs">{t("I confirm CP role for this excavation")}</Label>
          </div>
          {[
            ["inspection_before_entry_completed", "Pre-entry inspection completed?"],
            ["reinspection_required", "Reinspection required (rain / change)?"],
            ["reinspection_completed", "Reinspection completed?"],
            ["rain_event_observed", "Rain event observed since last inspection?"],
          ].map(([k, l]) => (
            <div key={k} className="mt-2"><Label className="text-xs">{t(l)}</Label><Bool value={f[k]} onChange={(v) => set(k, v)} testId={`exc-${k}`} /></div>
          ))}
          <OshaCoachingBlock
            testId="coach-cp"
            title="Competent Person"
            why="A competent person is trained to recognize hazards AND authorized to fix them on the spot. Without one on-site, no entry."
            requirement="29 CFR 1926.32(f) — Person capable of identifying existing and predictable hazards in the surroundings, or working conditions which are unsanitary, hazardous, or dangerous to employees, and who has authorization to take prompt corrective measures."
            example="Daily inspection before crew descent. Reinspection after rain, soil disturbance, or any change."
            mistakes="A general foreman with no trench-specific competent-person training. Same person doing the work as 'inspecting' it."
            escalate="If no qualified CP is on-site — stop work until one arrives."
            ifUnsure="Leave the field blank and Safety will dispatch a CP."
            defaultOpen={triggers.cp}
            tone={triggers.cp ? "red" : "amber"}
          />
        </Section>

        {/* Section 13 — Photos */}
        <Section num="13" title={t("Photos")} testId="exc-section-13">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-600">
            <Camera className="w-4 h-4 text-cyan-700" />
            <span>{t("Required photo kinds — capture each before crew descent.")}</span>
          </div>
          <ul className="text-xs space-y-1" data-testid="exc-photo-requirements">
            {[
              ["Overall Excavation", true],
              ["Protective System", true],
              ["Access/Egress", true],
              ["Utility Markings", true],
              ["Soil Condition", false],
              ["Water Condition", false],
              ["Traffic Control", false],
            ].map(([kind, required]) => (
              <li key={kind} className="flex items-center gap-2" data-testid={`exc-photo-req-${kind.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
                <span className={"inline-block w-2 h-2 rounded-full " + (required ? "bg-red-600" : "bg-slate-400")} />
                <span className="font-mono uppercase tracking-[0.08em]">{t(kind)}</span>
                <span className="text-[10px] text-slate-500">{required ? t("Required") : t("Optional")}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-slate-500 mt-2">{t("Upload photos after submission via the asset photo workflow on the success page.")}</p>
        </Section>

        {/* Section 14 — Field notes (Spanish preservation) */}
        <Section num="14" title={t("Field Notes")} testId="exc-section-14">
          <div className="flex items-center justify-between mb-1">
            <Label className="text-xs">{t("Write in English or Spanish — your original text is preserved.")}</Label>
            <span className="text-[10px] uppercase tracking-[0.12em] font-mono text-slate-500" data-testid="exc-notes-lang">
              {t("Original Language")}: <b>{currentLang === "es" ? "ES" : "EN"}</b>
            </span>
          </div>
          <Textarea value={f.field_notes} onChange={onText("field_notes")} rows={3}
            placeholder={t("Notes can be English or Spanish — both are preserved.")}
            data-testid="exc-fieldnotes" />
        </Section>

        {/* Competent-person reminder */}
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
          <Link to="/trench-safety" className="inline-flex items-center justify-center gap-1 text-cyan-800 underline text-xs font-bold uppercase tracking-[0.12em] py-2"
            data-testid="public-excavation-cancel-link">
            {t("Cancel · Back to Trench Safety")}
          </Link>
          <Button onClick={submit} disabled={saving} aria-busy={saving}
            className="bg-cyan-700 hover:bg-cyan-800 h-12 px-6 text-sm font-bold uppercase tracking-[0.12em]"
            data-testid="exc-submit">
            {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : t("Submit Excavation Record")}
          </Button>
        </div>

      </div>
    </OperationalPageFrame>
  );
}

// FV-7.3 · Foreman reinspection-request reasons (directive list)
const FV73_REASONS = [
  "Rain Event",
  "Water Intrusion",
  "Cave-In",
  "Protective System Changed",
  "Utility Conflict",
  "Near Miss",
  "Other",
];

function SuccessScreen({ done, setDone, t }) {
  const [showReinspect, setShowReinspect] = useState(false);
  const [reason, setReason] = useState("Rain Event");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [reinspectResult, setReinspectResult] = useState(null);
  const confirmation = buildSubmissionConfirmation({
    workflowKey: "excavation",
    documentNumber: done.doc_id || done.id || "",
    submittedAt: done.created_at || new Date().toISOString(),
    submittedBy: done.submitted_by || done.foreman_name || done.supervisor_name || "",
    project: done.project_name || done.project_number || "",
    followUpRequired: done.flags?.length > 0
      ? "A competent person must follow up on the flagged items shown below."
      : "No further action is required from you at this time.",
    note: done.daily_report_links?.length > 0
      ? `Linked Daily Report(s): ${done.daily_report_links.map((l) => l.report_number || l.daily_report_id).join(", ")}`
      : "",
    startAnother: {
      label: "Start Another",
      onClick: () => {
        setDone(null);
        window.scrollTo({ top: 0 });
      },
    },
    returnToPortal: { label: "Return to Portal", to: "/trench-safety" },
  });

  async function triggerReinspect() {
    setSubmitting(true);
    try {
      const r = await api.post(`/trench-safety/excavations/${done.id}/public/reinspection-request`,
        { reason, note });
      setReinspectResult({ ok: true, data: r.data });
      setShowReinspect(false);
    } catch (e) {
      setReinspectResult({ ok: false, msg: e?.response?.data?.detail || e?.message || "Failed" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <OperationalPageFrame
      testId="public-excavation-page"
      backTo="/trench-safety"
      backLabel={t("Back to Trench Safety")}
      accent="emerald"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-4xl"
      heroIcon={CheckCircle2}
      kicker={t("Trench Safety · Field Submission")}
      title={t("Excavation Record Submitted")}
      description={t("Safety has the record, the follow-up queue is live, and crews can request a reinspection immediately if conditions change.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="emerald" testId="public-excavation-success-status">{t(done.status)}</OperationalStatusBadge>
          {done.daily_report_links?.length > 0 ? <OperationalStatusBadge tone="cyan" testId="public-excavation-success-linked">{t("Daily report linked")}</OperationalStatusBadge> : null}
        </>
      )}
      footerText={t("MASCI Operations Platform · Excavation submission workflow")}
    >
      <div className="space-y-4">
        <SubmissionConfirmation confirmation={confirmation} embedded />
        {done.flags?.length > 0 && (
          <div className="bg-white border-2 border-amber-300 rounded-md p-4" data-testid="excavation-success-flags">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800 font-bold">{t("Coaching Flags")}</div>
            <ul className="mt-2 space-y-1">
              {done.flags.map((fl, i) => (
                <li key={i} className="text-xs text-amber-900 flex gap-2" data-testid={`exc-flag-${fl.code}`}>
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span><b>{t(fl.level)}</b> — {t(fl.message)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* FV-7.3 · Foreman reinspection trigger — no Safety approval needed */}
        <div className="mt-4 bg-white border-2 border-amber-300 rounded-md p-4" data-testid="exc-success-reinspect">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800 font-bold mb-1 inline-flex items-center gap-1">
            <OctagonAlert className="w-3.5 h-3.5" /> {t("Condition Changed? Request Reinspection.")}
          </div>
          <p className="text-xs text-amber-900 leading-snug mb-2">
            {t("Rain, water, cave-in, protective system change, utility conflict, near miss — request a reinspection. No approval needed. Safety and the Superintendent are notified immediately.")}
          </p>
          {reinspectResult?.ok ? (
            <div className="text-xs text-emerald-800 font-bold inline-flex items-center gap-1" data-testid="exc-success-reinspect-confirm">
              <CheckCircle2 className="w-3.5 h-3.5" /> {t("Reinspection requested — Safety and Superintendent notified.")}
            </div>
          ) : !showReinspect ? (
            <Button onClick={() => setShowReinspect(true)} variant="outline"
              className="border-amber-400 text-amber-900 hover:bg-amber-50"
              data-testid="exc-success-reinspect-open">
              {t("Request Reinspection")}
            </Button>
          ) : (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-1.5" data-testid="exc-success-reinspect-reasons">
                {FV73_REASONS.map((r) => (
                  <button key={r} type="button" onClick={() => setReason(r)}
                    className={"px-2.5 h-8 rounded-full border text-[11px] font-bold uppercase tracking-[0.08em] transition " +
                      (reason === r ? "border-amber-700 bg-amber-700 text-white" : "border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100")}
                    data-testid={`exc-success-reinspect-reason-${r.toLowerCase().replace(/[^a-z]+/g, "-")}`}>
                    {t(r)}
                  </button>
                ))}
              </div>
              <Textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2}
                placeholder={t("What changed? (Optional but helpful)")}
                data-testid="exc-success-reinspect-note" />
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={triggerReinspect} disabled={submitting}
                  className="bg-amber-700 hover:bg-amber-800 text-white"
                  data-testid="exc-success-reinspect-submit">
                  {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : t("Send Reinspection Request")}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowReinspect(false)} data-testid="exc-success-reinspect-cancel">
                  {t("Cancel")}
                </Button>
              </div>
              {reinspectResult && !reinspectResult.ok && (
                <div className="text-xs text-red-800">{reinspectResult.msg}</div>
              )}
            </div>
          )}
        </div>

      </div>
    </OperationalPageFrame>
  );
}
