// Generic Field Leadership form page — schema-driven.
// Renders ANY of the 10 kinds via `useParams().kind`. Single component
// covers Job picker, Employee picker (with inline-create), all field
// types from the schema, photos, signatures, refusal-with-witness, and
// EN/ES toggle. On submit it sends ES→EN translations alongside the raw
// Spanish text so admins always have a legible English copy.

import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ArrowLeft, FileText, Save, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { PhotoUpload } from "@/components/PhotoUpload";
import { SignaturePad } from "@/components/SignaturePad";
import { EquipmentLines } from "@/components/EquipmentLines";
import { EquipmentReturnLines } from "@/components/EquipmentReturnLines";
import { OutstandingEquipmentLookup } from "@/components/OutstandingEquipmentLookup";
import { getFormByKind } from "@/lib/fieldLeadershipSchemas";
import { translateUserInput } from "@/lib/translateOnSubmit";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { WhyItMattersPanel } from "@/components/guidance";
import { HelpTipBlock } from "@/components/HelpTip";

// iter212 — map FL form-kind ↔ HelpTip form_key.
// Only kinds with a fully authored HelpTip registry are listed here.
// Other kinds continue to render the legacy <WhyItMattersPanel>.
const FL_KIND_HELPTIP_FORMKEY = {
  equipment_checkout: "checkout",
  // iter214 — Write-Ups: facts-not-feelings disciplinary documentation.
  write_up: "writeup",
  // iter218 — Crew Eval: migrated from legacy WhyItMattersPanel.
  // Voice anchor: calibration beats scoring; specific examples beat generalizations.
  crew_eval: "crew_eval",
  // iter291 — Field-Leadership umbrella coaching density lift.
  // Each kind gets a focused 2-tip operational discipline family;
  // the existing mount at line ~712 of this file picks them up
  // automatically via this map. No new UI components.
  verbal_coaching: "verbal_coaching",
  attendance: "attendance",
  recognition: "recognition",
  new_employee_eval: "new_employee_eval",
  promotion_recommendation: "promotion_recommendation",
  training_deficiency: "training_deficiency",
  supervisor_notes: "supervisor_notes",
};

// Phase C · contextual guidance map per FL form kind (iter194).
// Keeps the embed lightweight: one inline WHY callout linking to the
// authoritative article. No popup spam, no clutter, mobile-first.
const FL_KIND_GUIDANCE = {
  equipment_checkout: {
    title: "Why Equipment Checkout matters",
    article: "field-equipment-checkout",
    body: "Equipment Checkout records who has what. It's the feeder for Shop (asset whereabouts) and HR (employee accountability).",
  },
  equipment_return: {
    title: "Why a clean return matters",
    article: "shop-equipment-return",
    body: "Returns close the accountability loop opened at checkout. Photograph the condition at return; note any damage discovered.",
  },
  verbal_coaching: {
    title: "Why coaching documentation matters",
    article: "field-coaching-documentation",
    body: "A 30-second record now becomes the basis for a write-up if the pattern repeats. Record date, what was discussed, what was agreed.",
  },
  write_up: {
    title: "Why this write-up matters",
    article: "field-writeup-authoring",
    body: "Defensible write-ups record facts, the conversation, and the agreed next step. Vague write-ups protect nobody.",
  },
  // Pass 4 — complete the contextual-help map for the remaining kinds.
  attendance: {
    title: "Why attendance documentation matters",
    article: "field-coaching-documentation",
    body: "Attendance patterns are the early-warning system for performance issues. Date, time, what happened, who was told.",
  },
  recognition: {
    title: "Why recognition is part of the record",
    article: "portal-leadership-identity",
    body: "Recognition documents strong performance the same way write-ups document weak performance — both feed HR career path decisions.",
  },
  new_employee_eval: {
    title: "Why the first evaluation matters",
    article: "portal-leadership-identity",
    body: "A new-employee evaluation is the baseline the rest of the career documentation gets compared against. Honest > generous.",
  },
  crew_eval: {
    title: "Why crew evaluations matter",
    article: "portal-leadership-identity",
    body: "Crew evaluations feed PM project staffing and HR career path. Comment on the crew dynamic, not just the individuals.",
  },
  training_deficiency: {
    title: "Why training-gap notes matter",
    article: "safety-training-compliance",
    body: "A training-deficiency note converts a vague 'this guy needs OSHA-10' into a scheduled, tracked, signed-off training event. Specifics > vibes.",
  },
  supervisor_notes: {
    title: "Why supervisor notes matter",
    article: "portal-leadership-identity",
    body: "Confidential operational notes — context that doesn't belong on a write-up but you'll want when reviewing later.",
  },
  promotion_recommendation: {
    title: "Why promotion recommendations matter",
    article: "portal-leadership-identity",
    body: "Formal recommendation that feeds HR career-path review. Specific examples + measurable observations > 'good guy'.",
  },
};
import {
  useDraftSync, getActorId, mintIdempotencyKey, enqueueUpload,
  persistIdempotencyKey, loadIdempotencyKey,
  DraftStatusPill,
} from "@/lib/resiliency";

const inputCls =
  "h-11 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";
const textareaCls = "border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";

function l(obj, lang) {
  return obj?.[lang] || obj?.en || "";
}

function FieldRenderer({ field, value, onChange, lang, t }) {
  if (field.type === "text") {
    return (
      <Input
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls}
        data-testid={`field-${field.name}`}
      />
    );
  }
  if (field.type === "number") {
    return (
      <Input
        type="number"
        step={field.step || "0.5"}
        min={field.min}
        max={field.max}
        value={value === undefined || value === null ? "" : value}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls}
        data-testid={`field-${field.name}`}
      />
    );
  }
  if (field.type === "textarea") {
    return (
      <Textarea
        rows={field.rows || 3}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className={textareaCls}
        data-testid={`field-${field.name}`}
      />
    );
  }
  if (field.type === "date" || field.type === "time" || field.type === "datetime") {
    const inputType = field.type === "datetime" ? "datetime-local" : field.type;
    return (
      <Input
        type={inputType}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls}
        data-testid={`field-${field.name}`}
      />
    );
  }
  if (field.type === "select") {
    const opts = (field.options || []).map((o) =>
      typeof o === "string" ? { en: o, es: o } : o
    );
    return (
      <Select value={value || ""} onValueChange={onChange}>
        <SelectTrigger className={inputCls} data-testid={`field-${field.name}`}>
          <SelectValue placeholder={t("Select…")} />
        </SelectTrigger>
        <SelectContent>
          {opts.map((o) => (
            <SelectItem key={o.en} value={o.en}>
              {l(o, lang)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }
  if (field.type === "yesno") {
    return (
      <div className="flex gap-2" data-testid={`field-${field.name}`}>
        {[
          { v: "yes", label_en: "Yes", label_es: "Sí" },
          { v: "no", label_en: "No", label_es: "No" },
        ].map((o) => (
          <button
            key={o.v}
            type="button"
            onClick={() => onChange(o.v)}
            className={`flex-1 h-11 rounded-md border-2 font-bold uppercase tracking-wide text-sm ${
              value === o.v
                ? "bg-red-700 text-white border-red-800"
                : "bg-white text-slate-700 border-slate-300 hover:border-red-400"
            }`}
            data-testid={`field-${field.name}-${o.v}`}
          >
            {lang === "es" ? o.label_es : o.label_en}
          </button>
        ))}
      </div>
    );
  }
  if (field.type === "ratings") {
    const ratings = (value && typeof value === "object") ? value : {};
    const ropts = (field.rating_options || []).map((o) => l(o, lang));
    return (
      <div className="space-y-2 border border-slate-200 rounded-md p-3 bg-slate-50">
        {field.items.map((it) => (
          <div key={it.key} className="grid grid-cols-1 md:grid-cols-5 gap-x-4 gap-y-3.5 items-center">
            <div className="sm:col-span-2 text-sm font-semibold text-slate-800">
              {l(it, lang)}
            </div>
            <div className="sm:col-span-3 flex flex-wrap gap-1">
              {ropts.map((opt, idx) => {
                const en_val = field.rating_options[idx].en;
                const active = ratings[it.key] === en_val;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => onChange({ ...ratings, [it.key]: en_val })}
                    className={`px-2 py-1 text-xs font-bold rounded border-2 ${
                      active
                        ? "bg-red-700 text-white border-red-800"
                        : "bg-white text-slate-700 border-slate-300 hover:border-red-400"
                    }`}
                    data-testid={`rating-${it.key}-${en_val.replace(/\s+/g, "_")}`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    );
  }
  if (field.type === "checkboxes") {
    // Checkbox group. `value` is a dict of {option_key: true|false}.
    // We also broadcast a flat `<name>__<key>` boolean so other fields
    // can use visible_if against a single option (e.g. show the "Other
    // description" only when property_returned__other is true).
    const current = (value && typeof value === "object") ? value : {};
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4.5 border border-slate-200 rounded-md p-3 bg-slate-50"
           data-testid={`field-${field.name}`}>
        {(field.options || []).map((opt) => {
          const key = opt.key || opt.en;
          const active = !!current[key];
          return (
            <label key={key} className={`flex items-center gap-2 px-2 py-1.5 rounded border-2 cursor-pointer text-sm font-bold ${
              active ? "bg-red-700 text-white border-red-800" : "bg-white text-slate-700 border-slate-300 hover:border-red-400"
            }`}>
              <input
                type="checkbox"
                checked={active}
                onChange={(e) => onChange({ ...current, [key]: e.target.checked })}
                data-testid={`field-${field.name}-${key}`}
                className="sr-only"
              />
              <span className={`w-4 h-4 inline-flex items-center justify-center rounded border-2 shrink-0 ${
                active ? "bg-white border-white" : "bg-white border-slate-400"
              }`}>
                {active && <span className="w-2 h-2 bg-red-700 rounded-sm" />}
              </span>
              <span>{l(opt, lang)}</span>
            </label>
          );
        })}
      </div>
    );
  }
  return <div className="text-xs text-red-600">Unknown field type: {field.type}</div>;
}

export default function FieldLeadershipFormPage() {
  const { kind } = useParams();
  const navigate = useNavigate();
  const { t, lang } = useT();
  const form = useMemo(() => getFormByKind(kind), [kind]);

  // Bail if no token (gate will redirect)
  useEffect(() => {
    if (!getLeadershipToken() && !isAdmin() && !getPmToken()) {
      navigate("/leadership", { replace: true });
    }
  }, [navigate]);

  const [jobs, setJobs] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [jobId, setJobId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [empSearch, setEmpSearch] = useState("");
  const [showInlineNewEmp, setShowInlineNewEmp] = useState(false);
  const [newEmpName, setNewEmpName] = useState("");
  const [employeeNameOverride, setEmployeeNameOverride] = useState("");
  const [employeePosition, setEmployeePosition] = useState("");
  const [supervisorName, setSupervisorName] = useState("");
  const [occurredAt, setOccurredAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [workArea, setWorkArea] = useState("");
  const [details, setDetails] = useState({});
  const [photos, setPhotos] = useState([]);
  const [supSig, setSupSig] = useState("");
  const [empSig, setEmpSig] = useState("");
  const [empRefused, setEmpRefused] = useState(false);
  const [empNotPresent, setEmpNotPresent] = useState(false);
  const [witnessName, setWitnessName] = useState("");
  const [witnessSig, setWitnessSig] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const idempotencyKeyRef = React.useRef(null);

  // TRUST-1 · TF-002 — hydrate any persisted idempotency key from IDB
  // so a reload mid-offline-queue does not mint a duplicate submission.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const k = await loadIdempotencyKey(`fl-${kind}-new`);
        if (!cancelled && k && !idempotencyKeyRef.current) {
          idempotencyKeyRef.current = k;
        }
      } catch { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [kind]);

  // Phase J — composite snapshot of all user-edited fields for autosave.
  const snapshot = useMemo(() => ({
    jobId, employeeId, empSearch, employeeNameOverride, employeePosition,
    supervisorName, occurredAt, workArea, details, photos,
    supSig, empSig, empRefused, empNotPresent, witnessName, witnessSig,
  }), [
    jobId, employeeId, empSearch, employeeNameOverride, employeePosition,
    supervisorName, occurredAt, workArea, details, photos,
    supSig, empSig, empRefused, empNotPresent, witnessName, witnessSig,
  ]);
  const actorId = useMemo(() => getActorId(), []);
  const { draftStatus, discard, commit } = useDraftSync(
    `fl-${kind}-new`, snapshot, actorId,
    (draft) => {
      try {
        if (draft.jobId !== undefined) setJobId(draft.jobId || "");
        if (draft.employeeId !== undefined) setEmployeeId(draft.employeeId || "");
        if (draft.empSearch !== undefined) setEmpSearch(draft.empSearch || "");
        if (draft.employeeNameOverride !== undefined) setEmployeeNameOverride(draft.employeeNameOverride || "");
        if (draft.employeePosition !== undefined) setEmployeePosition(draft.employeePosition || "");
        if (draft.supervisorName !== undefined) setSupervisorName(draft.supervisorName || "");
        if (draft.occurredAt !== undefined) setOccurredAt(draft.occurredAt || "");
        if (draft.workArea !== undefined) setWorkArea(draft.workArea || "");
        if (draft.details !== undefined) setDetails(draft.details || {});
        if (draft.photos !== undefined) setPhotos(draft.photos || []);
        if (draft.supSig !== undefined) setSupSig(draft.supSig || "");
        if (draft.empSig !== undefined) setEmpSig(draft.empSig || "");
        if (draft.empRefused !== undefined) setEmpRefused(!!draft.empRefused);
        if (draft.empNotPresent !== undefined) setEmpNotPresent(!!draft.empNotPresent);
        if (draft.witnessName !== undefined) setWitnessName(draft.witnessName || "");
        if (draft.witnessSig !== undefined) setWitnessSig(draft.witnessSig || "");
        toast.message("Draft recovered", {
          description: "Your unsent field leadership entry was restored.",
          duration: 6000,
        });
      } catch { /* ignore */ }
    },
  );

  useEffect(() => {
    api.get("/field-leadership/jobs").then((r) => setJobs(r.data?.items || [])).catch(() => {});
    api.get("/field-leadership/employees").then((r) => setEmployees(r.data?.items || [])).catch(() => {});
  }, []);

  const selectedJob = useMemo(
    () => jobs.find((j) => j.id === jobId) || null,
    [jobs, jobId]
  );
  const selectedEmp = useMemo(
    () => employees.find((e) => e.id === employeeId) || null,
    [employees, employeeId]
  );
  const filteredEmployees = useMemo(() => {
    const q = empSearch.trim().toLowerCase();
    if (!q) return employees.slice(0, 200);
    return employees
      .filter(
        (e) =>
          (e.name || "").toLowerCase().includes(q) ||
          (e.employee_id || "").toLowerCase().includes(q) ||
          (e.trade || "").toLowerCase().includes(q)
      )
      .slice(0, 200);
  }, [employees, empSearch]);

  const employeeNameFinal =
    selectedEmp?.name || employeeNameOverride.trim() || "";

  // Conditional returns AFTER all hooks (rules of hooks).
  if (!form) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <Card className="max-w-md w-full p-6 text-center">
          <h2 className="font-display text-xl font-black">Form not found</h2>
          <Button asChild className="mt-4"><Link to="/leadership">Back</Link></Button>
        </Card>
      </main>
    );
  }

  const updateField = (name, val) => {
    setDetails((p) => {
      const next = { ...p, [name]: val };
      // Special handling for `checkboxes` fields: broadcast a flat
      // `<name>__<optionKey>` boolean into details so other fields'
      // `visible_if` rules can target individual options (e.g. show
      // "Other description" only when property_returned__other is true).
      if (val && typeof val === "object" && !Array.isArray(val)) {
        // Drop any previous shadow keys for this field.
        for (const k of Object.keys(next)) {
          if (k.startsWith(`${name}__`)) delete next[k];
        }
        for (const [optKey, on] of Object.entries(val)) {
          if (typeof on === "boolean") {
            next[`${name}__${optKey}`] = on;
          }
        }
      }
      return next;
    });
  };

  const isFieldVisible = (f) => {
    if (!f.visible_if) return true;
    return details[f.visible_if.field] === f.visible_if.equals;
  };

  const validate = () => {
    if (!form.supervisor_signature_only && !supervisorName.trim()) {
      toast.error(t("Supervisor name required"));
      return false;
    }
    if (!form.supervisor_signature_only && !employeeNameFinal) {
      toast.error(t("Employee name required"));
      return false;
    }
    // Equipment Checkout: at least one line + EVERY line has all required
    // fields including 2 photos. Per spec: "all required fields not filled
    // or not 2 pictures per item checked out no submit".
    if (form.custom_renderer === "equipment_lines") {
      // Position is required at the top of the equipment checkout form.
      if (!(employeePosition || "").trim()) {
        toast.error(t("Employee position is required"));
        return false;
      }
      const lines = details.equipment_lines || [];
      if (lines.length === 0) {
        toast.error(t("Add at least one equipment item"));
        return false;
      }
      for (let i = 0; i < lines.length; i++) {
        const ln = lines[i];
        const itemNo = `#${i + 1}`;
        if (!(ln.name || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("equipment name is required")}`);
          return false;
        }
        const mfg = ln.manufacturer === "Other"
          ? (ln.manufacturer_custom || "").trim()
          : (ln.manufacturer || "").trim();
        if (!mfg) {
          toast.error(`${t("Item")} ${itemNo}: ${t("manufacturer is required")}`);
          return false;
        }
        if (!(ln.model || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("model is required")}`);
          return false;
        }
        if (!(ln.serial || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("serial / asset ID is required")}`);
          return false;
        }
        if (!Number(ln.qty) || Number(ln.qty) <= 0) {
          toast.error(`${t("Item")} ${itemNo}: ${t("quantity is required")}`);
          return false;
        }
        if (!Number(ln.replacement_value) || Number(ln.replacement_value) <= 0) {
          toast.error(`${t("Item")} ${itemNo}: ${t("replacement value is required")}`);
          return false;
        }
        if (!(ln.condition || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("condition is required")}`);
          return false;
        }
        if (!Array.isArray(ln.photos) || ln.photos.length < 2) {
          toast.error(`${t("Item")} ${itemNo}: ${t("at least 2 photos are required per item")}`);
          return false;
        }
      }
    }
    // Equipment Return: must have ≥1 line; each line must have a return
    // condition + 2 return photos. Other fields are pre-filled from the
    // matched checkout line (employee can edit but not blank).
    if (form.custom_renderer === "equipment_return_lines") {
      const lines = details.equipment_lines || [];
      if (lines.length === 0) {
        toast.error(t("Look up at least one item by serial or add it manually"));
        return false;
      }
      for (let i = 0; i < lines.length; i++) {
        const ln = lines[i];
        const itemNo = `#${i + 1}`;
        if (!(ln.serial || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("serial / asset ID is required")}`);
          return false;
        }
        if (!(ln.return_condition || "").trim()) {
          toast.error(`${t("Item")} ${itemNo}: ${t("return condition is required")}`);
          return false;
        }
        if (!Array.isArray(ln.return_photos) || ln.return_photos.length < 2) {
          toast.error(`${t("Item")} ${itemNo}: ${t("at least 2 return photos are required per item")}`);
          return false;
        }
      }
    }
    for (const f of form.fields) {
      if (!isFieldVisible(f)) continue;
      // Outstanding equipment lookup is informational — never required.
      if (f.type === "outstanding_equipment_lookup") continue;
      if (f.required) {
        const v = details[f.name];
        if (v === undefined || v === null || v === "" ||
            (typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0) ||
            (Array.isArray(v) && v.length === 0)) {
          toast.error(`${l(f.label, lang)} ${t("is required")}`);
          return false;
        }
        // `checkboxes` field with `min` option requires at least N keys
        // set to true. The detailed_explanation textarea uses min_length.
        if (f.type === "checkboxes" && f.min) {
          const onCount = Object.values(v || {}).filter(Boolean).length;
          if (onCount < f.min) {
            toast.error(`${l(f.label, lang)}: ${t("at least")} ${f.min} ${t("required")}`);
            return false;
          }
        }
        if (f.type === "textarea" && f.min_length) {
          if (String(v || "").trim().length < f.min_length) {
            toast.error(`${l(f.label, lang)}: ${t("must be at least")} ${f.min_length} ${t("characters")}`);
            return false;
          }
        }
      }
    }
    if (form.photos_required_when) {
      const cond = form.photos_required_when;
      const matched = (cond.equals_any || []).includes(details[cond.field]);
      if (matched && photos.length === 0) {
        toast.error(t("Photos are required for the selected condition."));
        return false;
      }
    }
    if (form.needs_signatures && !supSig) {
      toast.error(t("Supervisor signature required"));
      return false;
    }
    if (form.needs_signatures && !form.supervisor_signature_only && !form.employee_signature_optional) {
      if (!empSig && !empRefused && !empNotPresent) {
        toast.error(t("Employee signature, refusal, or 'not present' is required"));
        return false;
      }
      if (empRefused && form.allow_refusal && (!witnessName.trim() || !witnessSig)) {
        toast.error(t("Witness name and signature required when employee refuses to sign"));
        return false;
      }
      if (empNotPresent && !witnessName.trim()) {
        toast.error(t("Witness name required when employee is not present"));
        return false;
      }
    }
    return true;
  };

  const addInlineEmployee = async () => {
    const name = newEmpName.trim();
    if (!name) return;
    try {
      const r = await api.post("/field-leadership/employees", { name });
      const created = r.data;
      setEmployees((prev) => [...prev, created].sort((a, b) => (a.name || "").localeCompare(b.name || "")));
      setEmployeeId(created.id);
      setNewEmpName("");
      setShowInlineNewEmp(false);
      toast.success(t("Employee added"));
    } catch {
      toast.error(t("Could not add employee"));
    }
  };

  const submit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    try {
      // Normalize equipment_lines so manufacturer holds the final value
      // (custom string or dropdown name) — backend/PDF read a single field.
      let detailsToSend = details;
      if (form.custom_renderer === "equipment_lines") {
        const normLines = (details.equipment_lines || []).map((ln) => ({
          ...ln,
          manufacturer: ln.manufacturer === "Other"
            ? (ln.manufacturer_custom || "").trim()
            : (ln.manufacturer || ""),
          manufacturer_custom: undefined,
        }));
        detailsToSend = { ...details, equipment_lines: normLines };
      }
      const payload = {
        kind: form.kind,
        job_id: selectedJob?.id || null,
        project_number: selectedJob?.project_number || "",
        project_name: selectedJob?.project_name || "",
        location: selectedJob?.location || "",
        client: selectedJob?.client || "",
        assigned_pm: selectedJob?.project_manager || "",
        assigned_pm_email: selectedJob?.pm_email || "",
        employee_id: selectedEmp?.id || null,
        employee_name: employeeNameFinal,
        employee_position: employeePosition || selectedEmp?.role || selectedEmp?.trade || "",
        employee_email: selectedEmp?.email || "",
        supervisor_name: supervisorName,
        occurred_at: occurredAt ? new Date(occurredAt).toISOString() : null,
        work_area: workArea,
        details: detailsToSend,
        photos,
        supervisor_signature: supSig,
        employee_signature: (empRefused || empNotPresent) ? "" : empSig,
        employee_refused: empRefused,
        employee_not_present: empNotPresent,
        witness_name: (empRefused || empNotPresent) ? witnessName : "",
        witness_signature: empRefused ? witnessSig : "",
        language: lang,
      };
      // Auto-translate any Spanish freeform text → English so HR/PM/Admin
      // always see a legible English copy of the record. `submit_language`
      // is stamped on the saved payload so admin views can see what was
      // originally typed in Spanish.
      const finalPayload = await translateUserInput(payload, lang);
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = mintIdempotencyKey();
        // TRUST-1 · TF-002 — persist immediately.
        try { await persistIdempotencyKey(`fl-${kind}-new`, idempotencyKeyRef.current); }
        catch { /* ignore */ }
      }
      const up = await enqueueUpload({
        method: "POST",
        url: "/field-leadership",
        body: finalPayload,
        idempotencyKey: idempotencyKeyRef.current,
        formKey: `fl-${kind}-new`,
      });
      if (!up.ok && up.queued) {
        toast.message(t("Saved · will upload when reconnected"), {
          description: t("Your entry is queued and will send automatically."),
          duration: 6000,
        });
        await commit();
        idempotencyKeyRef.current = null;
        navigate("/leadership");
        return;
      }
      const r = { data: up.data };
      toast.success(t("Submitted — assigned PM, jaymn, and safety have been notified."));
      await commit();
      idempotencyKeyRef.current = null;
      navigate(`/leadership/records/${r.data.id}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Submit failed"));
    } finally {
      setSubmitting(false);
    }
  };

  const empLabel = l(form.employee_field_label || { en: "Employee", es: "Empleado" }, lang);

  return (
    <main className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          {/* Forms always show the M mark only (NOT the MASCI HUB lockup —
              that's internal product branding, not for documents that go to
              employees / HR / third parties). */}
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <DraftStatusPill status={draftStatus} testId="fl-draft-pill" />
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-5 sm:px-8 pt-8">
        <div className="mb-6">
          <Link
            to="/leadership"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="leadership-back"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Field Leadership")}
          </Link>
        </div>

        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">{t("Field Leadership")}</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1">{l(form.title, lang)}</h1>
        <p className="text-slate-600 mt-2 max-w-xl">{l(form.desc, lang)}</p>

        {FL_KIND_HELPTIP_FORMKEY[kind] ? (
          <div className="mt-4 max-w-2xl">
            <HelpTipBlock formKey={FL_KIND_HELPTIP_FORMKEY[kind]} showCounter />
          </div>
        ) : FL_KIND_GUIDANCE[kind] && (
          <div className="mt-4 max-w-2xl">
            <WhyItMattersPanel title={FL_KIND_GUIDANCE[kind].title}>
              <p>
                {FL_KIND_GUIDANCE[kind].body}{" "}
                <Link
                  to={`/guidance/${FL_KIND_GUIDANCE[kind].article}`}
                  className="font-medium underline"
                >
                  Read more →
                </Link>
              </p>
            </WhyItMattersPanel>
          </div>
        )}

        <Card className="mt-8 p-5 sm:p-6 space-y-5">
          {/* JOB */}
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Active Job")}</Label>
            <Select value={jobId} onValueChange={setJobId}>
              <SelectTrigger className={inputCls} data-testid="field-job"><SelectValue placeholder={t("Select a job…")} /></SelectTrigger>
              <SelectContent>
                {jobs.map((j) => (
                  <SelectItem key={j.id} value={j.id}>
                    {j.project_number} · {j.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedJob && (
              <div className="mt-2 text-xs font-mono text-slate-600 space-y-0.5">
                <div>{t("Location")}: {selectedJob.location || "—"}</div>
                <div>{t("Client")}: {selectedJob.client || "—"}</div>
                <div>
                  {t("Assigned PM")}: {selectedJob.project_manager || (
                    <span className="text-amber-700 font-bold">{t("None")}</span>
                  )} {selectedJob.pm_email ? `· ${selectedJob.pm_email}` : ""}
                </div>
              </div>
            )}
          </div>

          {/* EMPLOYEE picker — every kind needs it */}
          <>
            <>
              {/* EMPLOYEE */}
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{empLabel}</Label>
                <Input
                  placeholder={t("Search employee by name…")}
                  value={empSearch}
                  onChange={(e) => setEmpSearch(e.target.value)}
                  className={`${inputCls} mb-2`}
                  data-testid="field-employee-search"
                />
                <Select value={employeeId} onValueChange={(v) => { setEmployeeId(v); setEmployeeNameOverride(""); }}>
                  <SelectTrigger className={inputCls} data-testid="field-employee"><SelectValue placeholder={t("Select an employee…")} /></SelectTrigger>
                  <SelectContent>
                    {filteredEmployees.map((e) => (
                      <SelectItem key={e.id} value={e.id}>
                        {e.name}{e.trade ? ` · ${e.trade}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!showInlineNewEmp ? (
                  <button type="button" onClick={() => setShowInlineNewEmp(true)} className="mt-1 text-xs font-mono text-red-700 hover:underline" data-testid="leadership-add-emp-toggle">
                    + {t("Add new employee")}
                  </button>
                ) : (
                  <div className="mt-2 flex gap-2">
                    <Input
                      value={newEmpName}
                      onChange={(e) => setNewEmpName(e.target.value)}
                      placeholder={t("New employee name")}
                      className={`${inputCls} flex-1`}
                      data-testid="leadership-add-emp-name"
                    />
                    <Button type="button" onClick={addInlineEmployee} className="bg-red-700 hover:bg-red-800 text-white" data-testid="leadership-add-emp-save">{t("Add")}</Button>
                    <Button type="button" variant="outline" onClick={() => { setShowInlineNewEmp(false); setNewEmpName(""); }}>{t("Cancel")}</Button>
                  </div>
                )}
                {!selectedEmp && (
                  <div className="mt-2">
                    <Label className="text-xs text-slate-500">{t("Or type employee name (not in system)")}</Label>
                    <Input
                      value={employeeNameOverride}
                      onChange={(e) => setEmployeeNameOverride(e.target.value)}
                      className={inputCls}
                      placeholder={t("Manual employee name")}
                      data-testid="field-employee-manual"
                    />
                  </div>
                )}
                {/* iter364 · Uniform linkage status indicator — matches the
                    coaching pattern used on every other form's
                    EmployeeRosterField. No behavior change, no API change. */}
                {selectedEmp ? (
                  <div className="mt-1 text-[10px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid="field-employee-linked">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    {t("Linked to roster")}
                  </div>
                ) : employeeNameOverride.trim() ? (
                  <div className="mt-1 text-[11px] text-amber-700 leading-snug" data-testid="field-employee-unlinked">
                    <span className="font-mono font-bold uppercase tracking-wider">{t("Not in roster")}.</span>{" "}
                    {t("Saved as free-text. This will appear as an EMP_LINK_UNRESOLVABLE finding in Governance Health until you either pick from the roster or add this person to the employee master.")}{" "}
                    <a href="/admin/operational-language#roster_backed_selector" target="_blank" rel="noreferrer" className="underline">
                      {t("What does this mean?")}
                    </a>
                  </div>
                ) : null}
                <div className="mt-3">
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                    {t("Position")}
                    {(form.custom_renderer === "equipment_lines" || form.custom_renderer === "equipment_return_lines") && (
                      <span className="text-red-700 ml-1">*</span>
                    )}
                  </Label>
                  <Input value={employeePosition} onChange={(e) => setEmployeePosition(e.target.value)} className={inputCls} data-testid="field-employee-position" placeholder={selectedEmp?.role || selectedEmp?.trade || ""} />
                </div>
              </div>
            </>
          </>

          {/* SUPERVISOR + DATE */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Supervisor / Foreman / Superintendent")}</Label>
              <Input value={supervisorName} onChange={(e) => setSupervisorName(e.target.value)} className={inputCls} data-testid="field-supervisor" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Date / Time")}</Label>
              <Input type="datetime-local" value={occurredAt} onChange={(e) => setOccurredAt(e.target.value)} className={inputCls} data-testid="field-occurred-at" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Location / Work Area")}</Label>
              <Input value={workArea} onChange={(e) => setWorkArea(e.target.value)} className={inputCls} placeholder={selectedJob?.location || ""} data-testid="field-work-area" />
            </div>
          </div>

          {/* SCHEMA-DRIVEN FIELDS or CUSTOM RENDERER */}
          <div className="border-t-2 border-slate-200 pt-5 space-y-4">
            {form.custom_renderer === "equipment_lines" ? (
              <EquipmentLines
                value={details.equipment_lines || []}
                onChange={(v) => updateField("equipment_lines", v)}
                lang={lang}
                t={t}
              />
            ) : form.custom_renderer === "equipment_return_lines" ? (
              <EquipmentReturnLines
                value={details.equipment_lines || []}
                onChange={(v) => updateField("equipment_lines", v)}
                lang={lang}
                t={t}
              />
            ) : (
              form.fields.filter(isFieldVisible).map((f) => {
                if (f.type === "outstanding_equipment_lookup") {
                  return (
                    <div key={f.name}>
                      <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                        {l(f.label, lang)}
                      </Label>
                      <OutstandingEquipmentLookup
                        employeeName={employeeNameFinal}
                        value={details[f.name]}
                        onChange={(v) => updateField(f.name, v)}
                        lang={lang}
                        t={t}
                      />
                    </div>
                  );
                }
                return (
                  <div key={f.name}>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                      {l(f.label, lang)}{f.required && <span className="text-red-700 ml-1">*</span>}
                    </Label>
                    <FieldRenderer
                      field={f}
                      value={details[f.name]}
                      onChange={(v) => updateField(f.name, v)}
                      lang={lang}
                      t={t}
                    />
                    {f.help && (
                      <p className="text-[11px] text-slate-500 mt-1">{l(f.help, lang)}</p>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* ACKNOWLEDGEMENT */}
          {form.acknowledgement && (
            <div className="rounded-md bg-amber-50 border-2 border-amber-300 px-4 py-3 text-xs text-amber-900 leading-relaxed">
              {(() => {
                const ack = form.acknowledgement[lang] || form.acknowledgement.en;
                if (Array.isArray(ack)) {
                  return ack.map((p, i) => (
                    <p key={i} className={i === 0 ? "" : "mt-2"}>{p}</p>
                  ));
                }
                return ack;
              })()}
            </div>
          )}

          {/* PHOTOS */}
          {form.allows_photos && (
            <div className="border-t-2 border-slate-200 pt-5">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Photos / Documents")}
                {form.photos_required_when && (
                  <span className="text-amber-700 normal-case tracking-normal ml-2">
                    {t("(required if condition is Fair or Damaged)")}
                  </span>
                )}
              </Label>
              <PhotoUpload photos={photos} onChange={setPhotos} testIdBase="leadership-photos" />
            </div>
          )}

          {/* SIGNATURES */}
          {form.needs_signatures && (
            <div className="border-t-2 border-slate-200 pt-5 space-y-4">
              <p className="text-xs text-slate-600 italic">
                {t("Employee signature acknowledges receipt of this document and does not necessarily indicate agreement with its contents.")}
              </p>
              <SignaturePad value={supSig} onChange={setSupSig} label={t("Supervisor Signature")} testId="leadership-sup-sig" />
              {!form.supervisor_signature_only && (
                <>
                  {!empRefused && !empNotPresent && (
                    <SignaturePad
                      value={empSig}
                      onChange={setEmpSig}
                      label={form.employee_signature_optional ? t("Employee Signature (Optional)") : t("Employee Signature")}
                      testId="leadership-emp-sig"
                    />
                  )}
                  {form.allow_refusal && (
                    <div className="rounded-md border border-slate-200 p-3 bg-slate-50 space-y-2">
                      <label className="flex items-center gap-2 text-sm font-bold">
                        <input
                          type="checkbox"
                          checked={empRefused}
                          onChange={(e) => { setEmpRefused(e.target.checked); if (e.target.checked) setEmpNotPresent(false); }}
                          data-testid="leadership-refused"
                          disabled={empNotPresent}
                        />
                        {t("Employee refused to sign")}
                      </label>
                      <label className="flex items-center gap-2 text-sm font-bold">
                        <input
                          type="checkbox"
                          checked={empNotPresent}
                          onChange={(e) => { setEmpNotPresent(e.target.checked); if (e.target.checked) setEmpRefused(false); }}
                          data-testid="leadership-not-present"
                          disabled={empRefused}
                        />
                        {t("Employee not present (Quit / Abandonment / Discharged off-site)")}
                      </label>
                      {(empRefused || empNotPresent) && (
                        <div className="mt-3 space-y-3">
                          <div>
                            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Witness Name")}</Label>
                            <Input value={witnessName} onChange={(e) => setWitnessName(e.target.value)} className={inputCls} data-testid="leadership-witness-name" />
                          </div>
                          {empRefused && (
                            <SignaturePad value={witnessSig} onChange={setWitnessSig} label={t("Witness Signature")} testId="leadership-witness-sig" />
                          )}
                          {empNotPresent && (
                            <p className="text-[11px] text-slate-600 italic">
                              {t("Witness signature is optional when the employee is not present — the witness name is sufficient documentation.")}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          <div className="border-t-2 border-slate-200 pt-5 flex gap-3">
            <Button type="button" variant="outline" onClick={() => navigate("/leadership")} data-testid="leadership-cancel">
              {t("Cancel")}
            </Button>
            <Button
              type="button"
              disabled={submitting}
              onClick={submit}
              className="flex-1 h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
              data-testid="leadership-submit"
            >
              {submitting ? <FileText className="w-4 h-4 mr-2 animate-pulse" /> : <Save className="w-4 h-4 mr-2" />}
              {submitting ? t("Submitting…") : t("Submit & Email PDF")}
            </Button>
          </div>
        </Card>
      </div>
    </main>
  );
}
