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
import { getFormByKind } from "@/lib/fieldLeadershipSchemas";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";

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
      <div className="space-y-2 border-2 border-slate-200 rounded-md p-3 bg-slate-50">
        {field.items.map((it) => (
          <div key={it.key} className="grid grid-cols-1 sm:grid-cols-5 gap-1.5 items-center">
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
  const [witnessName, setWitnessName] = useState("");
  const [witnessSig, setWitnessSig] = useState("");
  const [submitting, setSubmitting] = useState(false);

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

  const updateField = (name, val) =>
    setDetails((p) => ({ ...p, [name]: val }));

  const isFieldVisible = (f) => {
    if (!f.visible_if) return true;
    return details[f.visible_if.field] === f.visible_if.equals;
  };

  const validate = () => {
    if (!form.supervisor_signature_only && !supervisorName.trim()) {
      toast.error(t("Supervisor name required"));
      return false;
    }
    if (!form.supervisor_signature_only && !employeeNameFinal && form.kind !== "supervisor_notes") {
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
      if (f.required) {
        const v = details[f.name];
        if (v === undefined || v === null || v === "" ||
            (typeof v === "object" && Object.keys(v).length === 0)) {
          toast.error(`${l(f.label, lang)} ${t("is required")}`);
          return false;
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
      if (!empSig && !empRefused) {
        toast.error(t("Employee signature OR refusal required"));
        return false;
      }
      if (empRefused && form.allow_refusal && (!witnessName.trim() || !witnessSig)) {
        toast.error(t("Witness name and signature required when employee refuses to sign"));
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
        employee_signature: empRefused ? "" : empSig,
        employee_refused: empRefused,
        witness_name: empRefused ? witnessName : "",
        witness_signature: empRefused ? witnessSig : "",
        language: lang,
      };
      const r = await api.post("/field-leadership", payload);
      toast.success(t("Submitted — assigned PM, jaymn, and safety have been notified."));
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
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
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

          {form.kind !== "supervisor_notes" && (
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
          )}

          {/* SUPERVISOR + DATE */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              form.fields.filter(isFieldVisible).map((f) => (
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
                </div>
              ))
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
                  {!empRefused && (
                    <SignaturePad
                      value={empSig}
                      onChange={setEmpSig}
                      label={form.employee_signature_optional ? t("Employee Signature (Optional)") : t("Employee Signature")}
                      testId="leadership-emp-sig"
                    />
                  )}
                  {form.allow_refusal && (
                    <div className="rounded-md border-2 border-slate-200 p-3 bg-slate-50">
                      <label className="flex items-center gap-2 text-sm font-bold">
                        <input type="checkbox" checked={empRefused} onChange={(e) => setEmpRefused(e.target.checked)} data-testid="leadership-refused" />
                        {t("Employee refused to sign")}
                      </label>
                      {empRefused && (
                        <div className="mt-3 space-y-3">
                          <div>
                            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Witness Name")}</Label>
                            <Input value={witnessName} onChange={(e) => setWitnessName(e.target.value)} className={inputCls} data-testid="leadership-witness-name" />
                          </div>
                          <SignaturePad value={witnessSig} onChange={setWitnessSig} label={t("Witness Signature")} testId="leadership-witness-sig" />
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
