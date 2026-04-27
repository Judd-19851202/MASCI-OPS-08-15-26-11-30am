import React, { useEffect, useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Save, Loader2, AlertOctagon, Plus, Wrench, Search } from "lucide-react";
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
import { JobPicker } from "@/components/JobPicker";
import { LangToggle } from "@/components/LangToggle";
import { useT, getLang } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2";

// Critical fluid items — failing any of these means the unit physically can't
// safely operate until the fluid is corrected. Block the inspection from being
// submitted and show a stop-work dialog the moment FAIL is tapped.
const CRITICAL_FLUID_ITEMS = new Set([
  "Engine oil level",
  "Engine coolant level",
  "Hydraulic fluid level",
  "Transmission fluid",
  "Transmission fluid level",
]);

const todayIso = () => new Date().toISOString().slice(0, 10);
const nowHm = () => {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(
    d.getMinutes()
  ).padStart(2, "0")}`;
};

const buildDefaults = () => ({
  project_name: "",
  project_number: "",
  location: "",
  inspection_date: todayIso(),
  inspection_time: nowHm(),
  operator_name: "",
  equipment_type: "",
  equipment_unit: "",
  equipment_make: "",
  equipment_model: "",
  equipment_serial: "",
  hour_meter: "",
  odometer: "",
  checklist: {},
  fail_count: 0,
  pass_count: 0,
  na_count: 0,
  deficiency_notes: "",
  corrective_actions: "",
  out_of_service: "No",
  photos: [],
  operator_signature: "",
});

const StatusBtn = ({ active, color, label, onClick, testId }) => (
  <button
    type="button"
    onClick={onClick}
    data-testid={testId}
    className={`flex-1 h-10 rounded font-mono text-xs font-black uppercase tracking-[0.15em] border-2 transition-colors ${
      active
        ? `${color} text-white border-transparent`
        : "bg-white text-slate-500 border-slate-300 hover:border-slate-500"
    }`}
  >
    {label}
  </button>
);

export default function NewEquipmentInspection({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(buildDefaults());
  const [equipmentTypes, setEquipmentTypes] = useState([]);
  const [checklists, setChecklists] = useState({});
  const [savedUnits, setSavedUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [unitSearch, setUnitSearch] = useState("");
  const [criticalFluidAlert, setCriticalFluidAlert] = useState(null); // {section, item} when blocking

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));

  // Load equipment types + checklists on mount (public endpoint)
  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/equipment-types");
        setEquipmentTypes(r.data?.types || []);
        setChecklists(r.data?.checklists || {});
      } catch {
        toast.error("Could not load equipment types");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Load saved units for the chosen equipment type
  useEffect(() => {
    if (!data.equipment_type) {
      setSavedUnits([]);
      return;
    }
    (async () => {
      try {
        const r = await api.get(
          `/equipment-units?equipment_type=${encodeURIComponent(data.equipment_type)}`
        );
        setSavedUnits(r.data || []);
      } catch {
        setSavedUnits([]);
      }
    })();
  }, [data.equipment_type]);

  const sections = useMemo(() => {
    return checklists[data.equipment_type] || [];
  }, [checklists, data.equipment_type]);

  // When equipment type changes, seed the checklist structure with empty status entries
  const applyEquipmentType = (typ) => {
    const tplSections = checklists[typ] || [];
    const cl = {};
    tplSections.forEach((s) => {
      cl[s.title] = {};
      s.items.forEach((item) => {
        cl[s.title][item] = { status: "", note: "" };
      });
    });
    setData((p) => ({
      ...p,
      equipment_type: typ,
      equipment_unit: "",
      equipment_make: "",
      equipment_model: "",
      equipment_serial: "",
      checklist: cl,
      fail_count: 0,
      pass_count: 0,
      na_count: 0,
      out_of_service: "No",
    }));
  };

  const setItem = (sectionTitle, item, patch) => {
    setData((p) => {
      const next = JSON.parse(JSON.stringify(p));
      next.checklist[sectionTitle] = next.checklist[sectionTitle] || {};
      next.checklist[sectionTitle][item] = {
        ...(next.checklist[sectionTitle][item] || { status: "", note: "", photo: "" }),
        ...patch,
      };
      // If the user moved status away from FAIL, clear the photo (optional clean-up)
      if (patch.status && patch.status !== "fail") {
        next.checklist[sectionTitle][item].photo = "";
      }
      // Recompute tallies
      let pass = 0,
        fail = 0,
        na = 0;
      Object.values(next.checklist).forEach((sec) => {
        Object.values(sec).forEach((res) => {
          if (res?.status === "pass") pass += 1;
          else if (res?.status === "fail") fail += 1;
          else if (res?.status === "na") na += 1;
        });
      });
      next.pass_count = pass;
      next.fail_count = fail;
      next.na_count = na;
      next.out_of_service = fail > 0 ? "Yes" : "No";
      return next;
    });
  };

  // Compress + read a file → data URL (≤1024px wide, JPEG q=0.78)
  const readPhoto = (file) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = reject;
      reader.onload = () => {
        const img = new Image();
        img.onload = () => {
          const maxW = 1024;
          const scale = Math.min(1, maxW / img.width);
          const w = Math.round(img.width * scale);
          const h = Math.round(img.height * scale);
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, w, h);
          resolve(canvas.toDataURL("image/jpeg", 0.78));
        };
        img.onerror = reject;
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    });

  const onFailPhoto = async (sectionTitle, item, file) => {
    if (!file) return;
    try {
      const dataUrl = await readPhoto(file);
      setItem(sectionTitle, item, { photo: dataUrl });
    } catch {
      toast.error("Could not read photo");
    }
  };

  const applyJob = (job) => {
    setData((p) => ({
      ...p,
      project_name: job ? job.project_name : "",
      project_number: job ? job.project_number : "",
      location: p.location || (job && job.location) || "",
    }));
    if (job) toast.success(`Job loaded: #${job.project_number}`);
  };

  const filteredUnits = useMemo(() => {
    const q = unitSearch.trim().toLowerCase();
    if (!q) return savedUnits;
    return savedUnits.filter((u) => u.unit_label.toLowerCase().includes(q));
  }, [savedUnits, unitSearch]);

  const pickUnit = (u) => {
    setData((p) => ({
      ...p,
      equipment_unit: u.unit_label,
      equipment_make: u.make || p.equipment_make,
      equipment_model: u.model || p.equipment_model,
      equipment_serial: u.serial || p.equipment_serial,
    }));
    toast.success(`Unit loaded: ${u.unit_label}`);
  };

  const submit = async () => {
    if (saving) return;
    if (!data.project_name) return toast.error("Project name is required");
    if (!data.operator_name) return toast.error("Operator name is required");
    if (!data.equipment_type) return toast.error("Equipment type is required");
    if (!data.equipment_unit) return toast.error("Unit number / label is required");
    if (!data.operator_signature) return toast.error("Operator signature is required");

    // Make sure every checklist item has a status — fail-fast helps OSHA records
    const missing = [];
    const failNoNote = [];
    const failShortNote = [];
    const failNoPhoto = [];
    const criticalFluidFails = [];
    Object.entries(data.checklist).forEach(([sec, items]) => {
      Object.entries(items).forEach(([item, res]) => {
        if (!res?.status) {
          missing.push(`${sec} → ${item}`);
        } else if (res.status === "fail") {
          if (CRITICAL_FLUID_ITEMS.has(item)) {
            criticalFluidFails.push(item);
          }
          const note = (res.note || "").trim();
          if (!note) failNoNote.push(`${sec} → ${item}`);
          else if (note.length < 10) failShortNote.push(`${sec} → ${item}`);
          if (!res.photo) failNoPhoto.push(`${sec} → ${item}`);
        }
      });
    });
    if (criticalFluidFails.length > 0) {
      setCriticalFluidAlert({
        section: "Fluids & Leaks",
        item: criticalFluidFails[0],
        atSubmit: true,
        all: criticalFluidFails,
      });
      return;
    }
    if (missing.length > 0) {
      toast.error(
        `${missing.length} item(s) still need PASS / FAIL / N/A — first: ${missing[0]}`
      );
      return;
    }
    if (failNoNote.length > 0) {
      toast.error(`FAIL needs a description — first: ${failNoNote[0]}`);
      return;
    }
    if (failShortNote.length > 0) {
      toast.error(
        `FAIL description must be at least 10 characters — first: ${failShortNote[0]}`
      );
      return;
    }
    if (failNoPhoto.length > 0) {
      toast.error(`FAIL needs a photo — first: ${failNoPhoto[0]}`);
      return;
    }

    setSaving(true);
    let payload = { ...data };
    try {
      const lang = getLang();
      if (lang === "es") {
        toast.info("Translating to English…");
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      const res = await api.post("/equipment-inspections", payload);
      toast.success(
        payload.fail_count > 0
          ? `Submitted — ${payload.fail_count} FAIL flagged. Tag out the unit.`
          : "Submitted"
      );
      if (publicMode || !isAdmin()) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            formType: "Equipment Pre-Op Inspection",
            returnTo: "/equipment/submit",
          },
          replace: true,
        });
      } else {
        navigate(`/equipment/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error("Could not save inspection");
    } finally {
      setSaving(false);
    }
  };

  const failCount = data.fail_count || 0;

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      {/* Critical-fluid stop-work modal */}
      {criticalFluidAlert && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center px-4"
          data-testid="critical-fluid-modal"
        >
          <div className="max-w-md w-full bg-white rounded-md border-4 border-red-700 shadow-2xl">
            <div className="bg-red-700 text-white p-5 flex items-start gap-3">
              <AlertOctagon className="w-8 h-8 shrink-0" />
              <div>
                <div className="font-mono text-xs uppercase tracking-[0.25em] font-bold opacity-80">
                  Stop — Critical Fluid Failure
                </div>
                <h2 className="font-display text-2xl font-black tracking-tight mt-1">
                  Do Not Continue
                </h2>
              </div>
            </div>
            <div className="p-5 sm:p-6 space-y-4">
              <p className="text-base text-slate-900 font-bold">
                {criticalFluidAlert.atSubmit
                  ? `Critical fluid failure: ${criticalFluidAlert.all.join(", ")}.`
                  : `${criticalFluidAlert.item} is marked FAIL.`}
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">
                Get with your supervisor immediately to refill the fluid before continuing
                this inspection. The inspection cannot be submitted while a critical fluid
                level is failing — running this unit could cause severe damage or injury.
              </p>
              <div className="bg-amber-50 border-2 border-amber-300 rounded p-3 text-sm text-amber-900">
                <b>Once the fluid is filled:</b> change the item from FAIL to PASS,
                then continue the inspection.
              </div>
            </div>
            <div className="px-5 sm:px-6 pb-5 sm:pb-6 flex flex-col sm:flex-row gap-2">
              <Button
                onClick={() => setCriticalFluidAlert(null)}
                className="flex-1 h-12 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-sm"
                data-testid="critical-fluid-acknowledge"
              >
                I'll get my supervisor
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          {publicMode ? (
            <MasciLogo variant="lockup" size="lg" className="hidden sm:block" />
          ) : (
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Hub
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
            {t("Equipment Pre-Op Inspection")}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {t(
              "OSHA daily walk-around for the unit you're operating. Mark every item — anything FAIL tags the machine OUT OF SERVICE until shop verifies."
            )}
          </p>
        </div>

        {failCount > 0 && (
          <div
            className="bg-red-50 border-2 border-red-700 rounded-md p-4 flex items-start gap-3"
            data-testid="oos-banner"
          >
            <AlertOctagon className="w-6 h-6 text-red-700 shrink-0 mt-0.5" />
            <div>
              <div className="font-display font-black text-red-700 text-lg leading-tight">
                {t("FAIL — DO NOT OPERATE")}
              </div>
              <div className="text-sm text-red-900 mt-1">
                {failCount} {t("item(s) failed inspection. This unit will be tagged OUT OF SERVICE on the report.")}
              </div>
            </div>
          </div>
        )}

        <Section number="01" title={t("Project & Operator")}>
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
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Project Name *")}</Label>
              <Input value={data.project_name} onChange={(e) => set("project_name", e.target.value)} className={inputCls} data-testid="input-project-name" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Project Number")}</Label>
              <Input value={data.project_number} onChange={(e) => set("project_number", e.target.value)} className={inputCls} data-testid="input-project-number" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Location *")}</Label>
              <Input value={data.location} onChange={(e) => set("location", e.target.value)} className={inputCls} data-testid="input-location" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Date *")}</Label>
              <Input type="date" value={data.inspection_date} onChange={(e) => set("inspection_date", e.target.value)} className={inputCls} data-testid="input-date" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Time *")}</Label>
              <Input type="time" value={data.inspection_time} onChange={(e) => set("inspection_time", e.target.value)} className={inputCls} data-testid="input-time" />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Operator Name *")}</Label>
              <Input value={data.operator_name} onChange={(e) => set("operator_name", e.target.value)} className={inputCls} placeholder={t("Your full name")} data-testid="input-operator-name" />
            </div>
          </div>
        </Section>

        <Section number="02" title={t("Equipment")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Equipment Type *")}</Label>
            <Select value={data.equipment_type} onValueChange={applyEquipmentType}>
              <SelectTrigger className={`${inputCls} mt-2`} data-testid="select-equipment-type">
                <SelectValue placeholder={loading ? t("Loading…") : t("Select equipment type")} />
              </SelectTrigger>
              <SelectContent className="max-h-72">
                {equipmentTypes.map((typ) => (
                  <SelectItem key={typ} value={typ} data-testid={`opt-equipment-${typ.replace(/[^a-z0-9]/gi, "-").toLowerCase()}`}>
                    {typ}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {data.equipment_type && (
            <>
              {savedUnits.length > 0 && (
                <div className="bg-slate-100 border-2 border-slate-200 rounded-md p-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2 flex items-center gap-2">
                    <Wrench className="w-3 h-3" /> {t("Saved units")} ({savedUnits.length})
                  </div>
                  <div className="relative mb-2">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <Input
                      value={unitSearch}
                      onChange={(e) => setUnitSearch(e.target.value)}
                      placeholder={t("Search saved units…")}
                      className="h-9 pl-9 text-sm border-slate-300"
                      data-testid="input-unit-search"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                    {filteredUnits.map((u) => {
                      const sub = [u.make, u.model].filter(Boolean).join(" ");
                      return (
                        <button
                          key={u.id}
                          type="button"
                          onClick={() => pickUnit(u)}
                          className="px-3 py-1.5 rounded border border-slate-300 bg-white hover:border-red-700 hover:text-red-700 text-sm text-left"
                          data-testid={`btn-saved-unit-${u.id}`}
                        >
                          <div className="font-mono font-bold">{u.unit_label}</div>
                          {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
                        </button>
                      );
                    })}
                    {filteredUnits.length === 0 && (
                      <span className="text-sm text-slate-500 italic">{t("No matches.")}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Unit # / Label *")}</Label>
                  <Input value={data.equipment_unit} onChange={(e) => set("equipment_unit", e.target.value)} className={inputCls} placeholder="e.g. CAT 320 — Unit #7" data-testid="input-equipment-unit" />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Make")}</Label>
                  <Input value={data.equipment_make} onChange={(e) => set("equipment_make", e.target.value)} className={inputCls} placeholder="Caterpillar" data-testid="input-make" />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Model")}</Label>
                  <Input value={data.equipment_model} onChange={(e) => set("equipment_model", e.target.value)} className={inputCls} placeholder="320 GC" data-testid="input-model" />
                </div>
                <div className="sm:col-span-2">
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Serial #")}</Label>
                  <Input value={data.equipment_serial} onChange={(e) => set("equipment_serial", e.target.value)} className={inputCls} data-testid="input-serial" />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Hour Meter")}</Label>
                  <Input value={data.hour_meter} onChange={(e) => set("hour_meter", e.target.value)} className={inputCls} placeholder="e.g. 4523" data-testid="input-hour-meter" />
                  <p className="text-xs text-slate-500 mt-1">{t("Leave blank if no hour meter.")}</p>
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Odometer")}</Label>
                  <Input value={data.odometer} onChange={(e) => set("odometer", e.target.value)} className={inputCls} placeholder="e.g. 87,432 mi" data-testid="input-odometer" />
                  <p className="text-xs text-slate-500 mt-1">{t("Leave blank if no odometer.")}</p>
                </div>
              </div>
            </>
          )}
        </Section>

        {/* Checklist sections (one per OSHA category) */}
        {sections.map((sec, idx) => (
          <Section
            key={sec.title}
            number={String(idx + 3).padStart(2, "0")}
            title={sec.title}
          >
            <div className="space-y-3">
              {sec.items.map((item) => {
                const result = data.checklist?.[sec.title]?.[item] || { status: "", note: "", photo: "" };
                const safeId = (sec.title + "-" + item).replace(/[^a-z0-9]/gi, "-").toLowerCase();
                const isFail = result.status === "fail";
                const noteLen = (result.note || "").trim().length;
                const noteShort = isFail && noteLen > 0 && noteLen < 10;
                const noteEmpty = isFail && noteLen === 0;
                const photoMissing = isFail && !result.photo;
                return (
                  <div
                    key={item}
                    className={`border-2 rounded-md p-3 ${
                      isFail
                        ? "border-red-700 bg-red-50"
                        : result.status === "pass"
                        ? "border-emerald-300 bg-emerald-50"
                        : result.status === "na"
                        ? "border-slate-300 bg-slate-50"
                        : "border-slate-200 bg-white"
                    }`}
                    data-testid={`checklist-item-${safeId}`}
                  >
                    <div className="text-sm text-slate-900 font-medium">{item}</div>
                    <div className="flex gap-2 mt-2">
                      <StatusBtn
                        active={result.status === "pass"}
                        color="bg-emerald-600"
                        label={t("Pass")}
                        onClick={() => setItem(sec.title, item, { status: "pass" })}
                        testId={`btn-pass-${safeId}`}
                      />
                      <StatusBtn
                        active={isFail}
                        color="bg-red-700"
                        label={t("Fail")}
                        onClick={() => {
                          setItem(sec.title, item, { status: "fail" });
                          if (CRITICAL_FLUID_ITEMS.has(item)) {
                            setCriticalFluidAlert({ section: sec.title, item });
                          }
                        }}
                        testId={`btn-fail-${safeId}`}
                      />
                      <StatusBtn
                        active={result.status === "na"}
                        color="bg-slate-700"
                        label={t("N/A")}
                        onClick={() => setItem(sec.title, item, { status: "na" })}
                        testId={`btn-na-${safeId}`}
                      />
                    </div>
                    {(isFail || result.note) && (
                      <>
                        <Textarea
                          value={result.note || ""}
                          onChange={(e) => setItem(sec.title, item, { note: e.target.value })}
                          placeholder={t("Describe the issue (required for FAIL — min 10 characters)")}
                          spellCheck={true}
                          className={`mt-2 text-sm border-2 ${
                            noteEmpty || noteShort ? "border-red-500" : "border-slate-300"
                          }`}
                          data-testid={`note-${safeId}`}
                        />
                        {isFail && (
                          <div className="text-xs mt-1 flex items-center justify-between gap-2">
                            <span className={noteEmpty || noteShort ? "text-red-700 font-bold" : "text-slate-500"}>
                              {noteEmpty
                                ? t("Description required for FAIL")
                                : noteShort
                                ? t("At least 10 characters required")
                                : t("Description")}
                            </span>
                            <span className={noteShort ? "text-red-700 font-mono font-bold" : "text-slate-400 font-mono"}>
                              {noteLen}/10
                            </span>
                          </div>
                        )}
                      </>
                    )}
                    {isFail && (
                      <div className="mt-2">
                        {result.photo ? (
                          <div className="flex items-start gap-2">
                            <img
                              src={result.photo}
                              alt="Failure evidence"
                              className="w-24 h-24 object-cover rounded border-2 border-red-300"
                            />
                            <button
                              type="button"
                              onClick={() => setItem(sec.title, item, { photo: "" })}
                              className="text-xs text-red-700 font-bold underline"
                              data-testid={`remove-photo-${safeId}`}
                            >
                              {t("Replace photo")}
                            </button>
                          </div>
                        ) : (
                          <label
                            className={`inline-flex items-center gap-2 h-10 px-3 rounded border-2 cursor-pointer text-sm font-bold ${
                              photoMissing
                                ? "border-red-700 bg-red-100 text-red-700"
                                : "border-slate-300 bg-white text-slate-700 hover:border-red-700"
                            }`}
                            data-testid={`add-photo-${safeId}`}
                          >
                            <input
                              type="file"
                              accept="image/*"
                              capture="environment"
                              className="hidden"
                              onChange={(e) => onFailPhoto(sec.title, item, e.target.files?.[0])}
                            />
                            📷 {t("Add photo (required for FAIL)")}
                          </label>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </Section>
        ))}

        {/* Tally bar */}
        {data.equipment_type && (
          <div className="bg-white border-2 border-slate-300 rounded-md p-4 flex items-center justify-between gap-3 sticky bottom-4 shadow-md">
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              {t("Tally")}
            </div>
            <div className="flex items-center gap-3 text-sm font-bold">
              <span className="text-emerald-700" data-testid="tally-pass">{data.pass_count} PASS</span>
              <span className="text-red-700" data-testid="tally-fail">{data.fail_count} FAIL</span>
              <span className="text-slate-600" data-testid="tally-na">{data.na_count} N/A</span>
            </div>
          </div>
        )}

        <Section number="98" title={t("Notes & Photos")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Deficiency notes")}</Label>
            <Textarea value={data.deficiency_notes} onChange={(e) => set("deficiency_notes", e.target.value)} className="mt-2 border-2 border-slate-300" placeholder={t("What's wrong — be specific")} data-testid="input-deficiency-notes" />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Corrective actions")}</Label>
            <Textarea value={data.corrective_actions} onChange={(e) => set("corrective_actions", e.target.value)} className="mt-2 border-2 border-slate-300" placeholder={t("What's being done about it")} data-testid="input-corrective-actions" />
          </div>
          <PhotoUpload
            photos={data.photos}
            onChange={(p) => set("photos", p)}
            label={t("Equipment Photos")}
          />
        </Section>

        <Section number="99" title={t("Operator Sign-Off")}>
          <p className="text-sm text-slate-700 leading-relaxed">
            {t(
              "I certify that I performed this pre-shift inspection of the listed equipment and that the conditions noted above are true and accurate. I will not operate this unit if any item is marked FAIL."
            )}
          </p>
          <SignaturePad
            label={t("Operator Signature *")}
            value={data.operator_signature}
            onChange={(v) => set("operator_signature", v)}
            testId="signature-operator"
          />
        </Section>

        <div className="flex items-center justify-end gap-3">
          <Button onClick={submit} disabled={saving} className="h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900" data-testid="submit-bottom-btn">
            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Save className="w-4 h-4 mr-1" />}
            {t("Submit Inspection")}
          </Button>
        </div>
      </main>
    </div>
  );
}
