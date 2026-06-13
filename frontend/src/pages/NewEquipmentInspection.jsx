import React, { useEffect, useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Save, Loader2, AlertOctagon, Plus, Wrench, Search, Camera } from "lucide-react";
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
import { EquipmentCombo } from "@/components/EquipmentCombo";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import SmartUnitClassificationChip from "@/components/SmartUnitClassificationChip";
import CanonicalInspectionSections from "@/components/CanonicalInspectionSections";
import { useT, getLang } from "@/lib/i18n";
import { formatApiError } from "@/lib/apiErrors";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { WhyItMattersPanel } from "@/components/guidance";
import { HelpTipBlock } from "@/components/HelpTip";
import { toast } from "sonner";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2";

// Critical fluid items — failing any of these means the unit physically can't
// safely operate until the fluid is corrected. Block the inspection from being
// submitted and show a stop-work dialog the moment FAIL is tapped.
const CRITICAL_FLUID_ITEMS = new Set([
  // Engine / coolant / hydraulic / transmission
  "Engine oil level",
  "Engine coolant level",
  "Hydraulic fluid level",
  "Transmission fluid",
  "Transmission fluid level",
  "Transmission / drivetrain fluid",
  // Drivetrain & axles
  "Tandem drive oil",
  "Front axle / differential oil",
  "Rear axle oil",
  "Differential / final drive oil (front & rear)",
  // Swing / circle / boom
  "Swing drive / slew gear oil",
  "Circle drive lubrication",
  "Boom extension / chain lubrication",
  // Pump / water / heat
  "Water pump oil / lubrication",
  "Screed heat system fluid (if applicable)",
  // Gearboxes (auger / conveyor / cutter / mixer / broom)
  "Auger & conveyor gearbox oil",
  "Auger / extruder gearbox oil",
  "Auger gearbox oil",
  "Conveyor / drag chain gearbox oil",
  "Conveyor gearbox oil",
  "Cutter drum drive gearbox oil",
  "Mixing rotor gearbox oil",
  "Broom drive motor / gearbox oil",
]);

/**
 * MAJOR_OUT_OF_SERVICE_ITEMS — safety-critical items that, when marked FAIL,
 * trigger the same "stop work, get supervisor" modal as a critical fluid
 * failure and put the unit OUT OF SERVICE. Anything else marked FAIL is
 * "needs attention" (yellow) — important to log + photograph, but the unit
 * stays operable until shop reviews it.
 *
 * Strings here MUST exactly match the items emitted by checklists.py.
 */
const MAJOR_OUT_OF_SERVICE_ITEMS = new Set([
  // User-specified safety basics
  "Steps, grab handles, ladders secure & clean",
  "Air filter / pre-cleaner condition",
  "ROPS / FOPS structure - no cracks or damage",
  "Seat & seat belt - functional, not torn",
  "Horn operational",
  "Backup alarm operational",
  "Service brakes - firm pedal, holds machine",
  "Parking brake - holds machine on grade",
  "Steering - responsive, no excessive play",
  "Emergency / kill switch operational",

  // Active leaks
  "Visible fluid leaks (engine, hydraulic, fuel, coolant)",
  "Belts and hoses - no cracks, fraying, or leaks",

  // Tires / tracks (per equipment-type variants from checklists.py)
  "Tires - inflation, cuts, sidewall damage, tread wear",
  "Tires - inflation, cuts, tread wear",
  "Tires - inflation, condition, no cuts (front & rear)",
  "Tires - inflation, cuts, tread",
  "Tires - inflation, cuts, tread depth (all positions)",
  "Tires - inflation, cuts, tread (front & rear)",
  "Tires (rear, if smooth-drum) - inflation, wear",
  "Tires / tracks - condition & wear",
  "Tracks or tires - condition & wear",
  "Tracks / undercarriage - tension, wear, no missing pads",
  "Tracks / undercarriage - tension, wear",
  "Tracks / undercarriage - tension & wear",
  "Tracks / undercarriage - condition & wear",
  "Tracks - tension, drive sprockets, idlers",

  // Strobe / beacon (FDOT-required)
  "Strobe / beacon light (Required)",

  // Fire extinguisher (FDOT-required)
  "Fire extinguisher present, charged & inspected",

  // Hydraulic hoses / cylinders
  "Hydraulic hoses - no chafing or bulges",
  "Hydraulic cylinders - rod condition, no leaks",
  "Hydraulic cylinders & hoses",
  "Hydraulic couplers / auxiliary lines - no leaks",
  "Hydraulic hoses & cylinders",

  // Boom / arm / pivot pins (excavator, backhoe, loader, telehandler)
  "Boom, stick, bucket - no cracks at pivot points",
  "Backhoe boom, dipper, bucket - no cracks at pivots",
  "Lift arms & linkage - no cracks",
  "Lift arms - no cracks, pivot pins secure",
  "Loader arms, pins, retainers secure",
  "Tow arms / tow points - no cracks",
  "Boom sections - no cracks, wear pads in place",

  // Outriggers / stabilizers
  "Stabilizer pads / outriggers - operate, no leaks",
  "Stabilizer / outrigger controls",
  "Stabilizer / outrigger pads (if equipped) operate freely",
  "Stabilizer / frame-level controls",
]);

/** Combined set: any FAIL of either of these = OUT OF SERVICE (red). */
const isOutOfServiceItem = (item) =>
  CRITICAL_FLUID_ITEMS.has(item) || MAJOR_OUT_OF_SERVICE_ITEMS.has(item);

const todayIso = () => {
  // Local date — NOT UTC. A foreman in Eastern time after ~7 PM gets
  // "tomorrow" from toISOString(), which is wrong. Use local components.
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};
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
  operator_id: "",
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
    className={`flex-1 min-w-0 h-10 rounded font-mono text-[10px] sm:text-xs font-black uppercase tracking-tight sm:tracking-[0.15em] border-2 transition-colors truncate px-1 ${
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
  const [tallyCollapsed, setTallyCollapsed] = useState(false);
  // Track 13.31B-D5.4 · structured canonical section capture
  const [canonicalCapture, setCanonicalCapture] = useState(null);
  const canonicalAvailable =
    canonicalCapture?.template_status === "available" && !!canonicalCapture?.asset_type;

  // Auto-set legacy equipment_type from canonical asset_type (backward compat).
  // Operator never has to pick — canonical is the authority.
  useEffect(() => {
    if (
      canonicalCapture?.template_status === "available" &&
      canonicalCapture?.asset_type &&
      !data.equipment_type
    ) {
      setData((p) => ({ ...p, equipment_type: canonicalCapture.asset_type }));
    }
  }, [canonicalCapture, data.equipment_type]);

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

  // iter135: removed dead /equipment-units autocomplete fetch (endpoint
  // was retired in iter22 and the 404 was being silently swallowed). The
  // saved-units dropdown is now always empty — operator types the unit
  // number directly. Keeps the network tab clean.
  useEffect(() => {
    setSavedUnits([]);
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
      // Recompute tallies + out-of-service status. The unit is OUT OF SERVICE
      // only if a critical-fluid OR a major-safety item is failing. Other
      // FAILs are "needs attention" (yellow) and don't lock the unit out.
      let pass = 0,
        fail = 0,
        na = 0,
        oos = false;
      Object.entries(next.checklist).forEach(([secTitle, sec]) => {
        Object.entries(sec).forEach(([itemName, res]) => {
          if (res?.status === "pass") pass += 1;
          else if (res?.status === "fail") {
            fail += 1;
            if (isOutOfServiceItem(itemName)) oos = true;
          } else if (res?.status === "na") na += 1;
        });
      });
      next.pass_count = pass;
      next.fail_count = fail;
      next.na_count = na;
      next.out_of_service = oos ? "Yes" : "No";
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

  // Live gating: every FAIL needs a 10-char description AND a photo.
  // Surface the count so the Submit button can disable itself + tell
  // the user exactly what's missing instead of a post-tap toast error.
  const failGating = useMemo(() => {
    let failCount = 0;
    let needPhoto = 0;
    let needNote = 0;
    Object.entries(data.checklist || {}).forEach(([, items]) => {
      Object.entries(items || {}).forEach(([, res]) => {
        if (res?.status === "fail") {
          failCount += 1;
          if (!res.photo) needPhoto += 1;
          const note = (res.note || "").trim();
          if (note.length < 10) needNote += 1;
        }
      });
    });
    return {
      failCount,
      needPhoto,
      needNote,
      blocked: needPhoto > 0 || needNote > 0,
    };
  }, [data.checklist]);

  const submit = async () => {
    if (saving) return;
    if (!data.project_name) return toast.error("Project name is required");
    if (!data.operator_name) return toast.error("Operator name is required");
    // D5.4 · equipment_type required only when canonical authority is NOT in play.
    if (!canonicalAvailable && !data.equipment_type) return toast.error("Equipment type is required");
    if (!data.equipment_unit) return toast.error("Unit number / label is required");
    if (!String(data.hour_meter || "").trim()) {
      return toast.error("Hour Meter / Odometer reading is required");
    }
    if (!data.operator_signature) return toast.error("Operator signature is required");

    // Make sure every checklist item has a status — fail-fast helps OSHA records
    const missing = [];
    const failNoNote = [];
    const failShortNote = [];
    const failNoPhoto = [];
    const oosFails = [];
    Object.entries(data.checklist).forEach(([sec, items]) => {
      Object.entries(items).forEach(([item, res]) => {
        if (!res?.status) {
          missing.push(`${sec} → ${item}`);
        } else if (res.status === "fail") {
          if (isOutOfServiceItem(item)) {
            oosFails.push(item);
          }
          const note = (res.note || "").trim();
          if (!note) failNoNote.push(`${sec} → ${item}`);
          else if (note.length < 10) failShortNote.push(`${sec} → ${item}`);
          if (!res.photo) failNoPhoto.push(`${sec} → ${item}`);
        }
      });
    });
    if (oosFails.length > 0) {
      // Determine if any are critical fluids vs major safety items
      const fluidFails = oosFails.filter((i) => CRITICAL_FLUID_ITEMS.has(i));
      setCriticalFluidAlert({
        section: fluidFails.length > 0 ? "Fluids & Leaks" : "Major Safety",
        item: oosFails[0],
        atSubmit: true,
        all: oosFails,
        kind: fluidFails.length > 0 ? "fluid" : "major",
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
    // D5.4 · attach structured canonical capture (additive · backend stores it
    // alongside legacy `checklist` so existing routing keeps firing).
    if (canonicalCapture && canonicalCapture.template_status === "available") {
      payload.inspection_sections = {
        template_key: canonicalCapture.template_key,
        template_label: canonicalCapture.template_label,
        asset_type: canonicalCapture.asset_type,
        applies_to: canonicalCapture.applies_to || "pre_op",
        sections: canonicalCapture.sections,
        pass_count: canonicalCapture.pass_count,
        fail_count: canonicalCapture.fail_count,
        na_count: canonicalCapture.na_count,
        total_count: canonicalCapture.total_count,
      };
      // Roll canonical fails into fail_count if legacy checklist is empty (so
      // existing defect routing fires for canonical-only submissions).
      const legacyFailTotal = Object.values(data.checklist || {}).reduce(
        (acc, items) =>
          acc +
          Object.values(items || {}).filter((r) => r?.status === "fail").length,
        0,
      );
      if (legacyFailTotal === 0 && canonicalCapture.fail_count > 0) {
        payload.fail_count = canonicalCapture.fail_count;
        payload.pass_count = canonicalCapture.pass_count;
        payload.na_count = canonicalCapture.na_count;
      }
    }
    try {
      const lang = getLang();
      if (lang === "es") {
        toast.info("Translating to English…");
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
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
            recordId: res.data?.inspection_number || res.data?.id || "",
          },
          replace: true,
        });
      } else {
        navigate(`/equipment/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error(formatApiError(e, "Could not save inspection"), { duration: 7000 });
    } finally {
      setSaving(false);
    }
  };

  const failCount = data.fail_count || 0;

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      {/* Critical-fluid / major-safety stop-work modal */}
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
                  {criticalFluidAlert.kind === "major"
                    ? t("Stop — Major Safety Failure")
                    : t("Stop — Critical Fluid Failure")}
                </div>
                <h2 className="font-display text-2xl font-black tracking-tight mt-1">
                  {t("Unit is OUT OF SERVICE")}
                </h2>
              </div>
            </div>
            <div className="p-5 sm:p-6 space-y-4">
              <p className="text-base text-slate-900 font-bold">
                {criticalFluidAlert.atSubmit
                  ? `${
                      criticalFluidAlert.kind === "major"
                        ? t("Major safety items failing:")
                        : t("Critical fluid failure:")
                    } ${criticalFluidAlert.all.join(", ")}.`
                  : `${criticalFluidAlert.item} ${t("is marked FAIL.")}`}
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">
                {criticalFluidAlert.kind === "major"
                  ? t(
                      "Do NOT operate this machine. Get with your supervisor immediately and advise that the unit is unsafe. Shop must be notified so the issue can be repaired before the unit goes back in service."
                    )
                  : t(
                      "Get with your supervisor immediately to refill the fluid before continuing this inspection. The inspection cannot be submitted while a critical fluid level is failing — running this unit could cause severe damage or injury."
                    )}
              </p>
              <div className="bg-amber-50 border-2 border-amber-300 rounded p-3 text-sm text-amber-900">
                {criticalFluidAlert.kind === "major" ? (
                  <>
                    <b>{t("Required actions:")}</b>
                    <ul className="list-disc ml-5 mt-1 space-y-0.5">
                      <li>{t("Tell your supervisor — do not operate.")}</li>
                      <li>{t("Notify shop so unit can be repaired.")}</li>
                      <li>{t("Tag-out the machine.")}</li>
                    </ul>
                  </>
                ) : (
                  <>
                    <b>{t("Once the fluid is filled:")}</b>{" "}
                    {t("change the item from FAIL to PASS, then continue the inspection.")}
                  </>
                )}
              </div>
            </div>
            <div className="px-5 sm:px-6 pb-5 sm:pb-6 flex flex-col sm:flex-row gap-2">
              <Button
                onClick={() => setCriticalFluidAlert(null)}
                className="flex-1 h-12 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-sm"
                data-testid="critical-fluid-acknowledge"
              >
                {t("I'll get my supervisor")}
              </Button>
            </div>
          </div>
        </div>
      )}

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
            <Button
              onClick={submit}
              disabled={saving || failGating.blocked}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:border-slate-400"
              data-testid="submit-top-btn"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : failGating.blocked ? (
                <Camera className="w-4 h-4 mr-1" />
              ) : (
                <Save className="w-4 h-4 mr-1" />
              )}
              {failGating.blocked ? t("Fix FAILs") : t("Submit")}
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

        <HelpTipBlock formKey="preop" className="mb-3" showCounter />
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Project Name *")}</Label>
              <Input value={data.project_name} onChange={(e) => set("project_name", e.target.value)} className={inputCls} data-testid="input-project-name" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Project Number")}</Label>
              <Input value={data.project_number} onChange={(e) => set("project_number", e.target.value)} className={inputCls} data-testid="input-project-number" />
            </div>
            <div className="lg:col-span-2">
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
            <div className="lg:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Operator Name *")}</Label>
              <EmployeeCombo
                value={data.operator_name}
                onChange={(v) => {
                  set("operator_name", v);
                  // iter362 · clear stale linkage if name is edited after pick.
                  if (data.operator_id && v !== data.operator_name) set("operator_id", "");
                }}
                onPick={(emp) => {
                  // iter362 · capture canonical employee_id atomically.
                  if (emp.id || emp.employee_id) set("operator_id", emp.id || emp.employee_id);
                }}
                placeholder={t("Type or pick from roster…")}
                testId="input-operator-name"
              />
              {(data.operator_name || "").trim() ? (
                data.operator_id ? (
                  <div className="mt-1 text-[10px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid="operator-linked">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    {t("Linked to roster")}
                  </div>
                ) : (
                  <div className="mt-1 text-[10px] text-amber-700 font-mono inline-flex items-center gap-1" data-testid="operator-unlinked">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    {t("Not in roster — will create governance finding")}
                  </div>
                )
              ) : null}
            </div>
          </div>
        </Section>

        <Section number="02" title={t("Equipment")}>
          <div>
            <Label
              className={`font-mono text-xs uppercase tracking-[0.2em] ${
                canonicalAvailable ? "text-slate-400" : "text-slate-700"
              }`}
            >
              {canonicalAvailable
                ? t("Equipment Type (legacy compat · auto-set from canonical record)")
                : t("Equipment Type *")}
            </Label>
            <Select value={data.equipment_type} onValueChange={applyEquipmentType}>
              <SelectTrigger
                className={`${inputCls} mt-2 ${canonicalAvailable ? "opacity-60" : ""}`}
                data-testid="select-equipment-type"
              >
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
            {canonicalAvailable && (
              <p
                className="mt-1 text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500"
                data-testid="legacy-select-demoted"
              >
                {t("Canonical asset_type is authoritative · this dropdown is retained for backward compatibility only.")}
              </p>
            )}
          </div>

          {/* D5.4 · Unit picker + canonical sections are always visible.
              Legacy equipment_type is no longer the gate — canonical asset_type
              is the authority for known assets. */}
          <>
              {savedUnits.length > 0 && (
                <div className="bg-slate-100 border border-slate-200 rounded-md p-3">
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

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                <div className="lg:col-span-2">
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Unit # / Label *")}</Label>
                  <EquipmentCombo
                    value={data.equipment_unit}
                    onChange={(v) => set("equipment_unit", v)}
                    onPick={(it) => {
                      setData((p) => ({
                        ...p,
                        equipment_unit: it.display_label || it.make_model || "",
                        equipment_make: it.make_model || p.equipment_make,
                        equipment_serial: it.vin_serial_number || p.equipment_serial,
                      }));
                    }}
                    placeholder="Type or pick from MASCI fleet (e.g. EXC020, Cat 308)…"
                    testId="equipment-unit"
                  />
                  <SmartUnitClassificationChip unitNumber={data.equipment_unit} testidPrefix="preop-smart-class" />
                  <CanonicalInspectionSections
                    unitNumber={data.equipment_unit}
                    appliesTo="pre_op"
                    onChange={setCanonicalCapture}
                    testidPrefix="preop-canonical-sections"
                  />
                  {canonicalAvailable && (
                    <div
                      className="mt-2 text-[10px] font-mono uppercase tracking-[0.16em] text-emerald-700"
                      data-testid="preop-canonical-authority-note"
                    >
                      Canonical authority · asset_type = {canonicalCapture?.asset_type}
                    </div>
                  )}
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Make")}</Label>
                  <Input value={data.equipment_make} onChange={(e) => set("equipment_make", e.target.value)} className={inputCls} placeholder="Caterpillar" data-testid="input-make" />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Model")}</Label>
                  <Input value={data.equipment_model} onChange={(e) => set("equipment_model", e.target.value)} className={inputCls} placeholder="320 GC" data-testid="input-model" />
                </div>
                <div className="lg:col-span-2">
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Serial #")}</Label>
                  <Input value={data.equipment_serial} onChange={(e) => set("equipment_serial", e.target.value)} className={inputCls} data-testid="input-serial" />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Hour Meter / Odometer *")}</Label>
                  <Input
                    value={data.hour_meter}
                    onChange={(e) => set("hour_meter", e.target.value)}
                    className={inputCls}
                    placeholder="e.g. 4523 hrs or 87,432 mi"
                    inputMode="decimal"
                    required
                    data-testid="input-hour-meter"
                  />
                  <p className="text-xs text-slate-500 mt-1">{t("Required — enter hours OR miles.")}</p>
                </div>
              </div>
            </>
        </Section>

        {/* Checklist sections (one per OSHA category) */}
        <HelpTipBlock formKey="preop.defects" className="mb-3" />
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
                const isMajorOos = isFail && isOutOfServiceItem(item);
                const noteLen = (result.note || "").trim().length;
                const noteShort = isFail && noteLen > 0 && noteLen < 10;
                const noteEmpty = isFail && noteLen === 0;
                const photoMissing = isFail && !result.photo;
                return (
                  <div
                    key={item}
                    className={`border-2 rounded-md p-3 ${
                      isMajorOos
                        ? "border-red-700 bg-red-50"
                        : isFail
                        ? "border-amber-500 bg-amber-50"
                        : result.status === "pass"
                        ? "border-emerald-300 bg-emerald-50"
                        : result.status === "na"
                        ? "border-slate-300 bg-slate-50"
                        : "border-slate-200 bg-white"
                    }`}
                    data-testid={`checklist-item-${safeId}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-sm text-slate-900 font-medium">{item}</div>
                      {isFail && (
                        <span
                          className={`shrink-0 font-mono text-[9px] uppercase tracking-[0.18em] font-bold px-2 py-0.5 rounded ${
                            isMajorOos
                              ? "bg-red-700 text-white"
                              : "bg-amber-400 text-amber-900"
                          }`}
                          data-testid={`flag-${safeId}`}
                        >
                          {isMajorOos ? t("Out of Service") : t("Needs Attention")}
                        </span>
                      )}
                    </div>
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
                          if (isOutOfServiceItem(item)) {
                            setCriticalFluidAlert({
                              section: sec.title,
                              item,
                              kind: CRITICAL_FLUID_ITEMS.has(item) ? "fluid" : "major",
                            });
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
                              className="hidden"
                              onChange={(e) => onFailPhoto(sec.title, item, e.target.files?.[0])}
                            />
                            📷 {t("Add photo (camera or gallery, required for FAIL)")}
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

        {/* Tally bar — sticky at bottom while the user fills out the
            inspection so they can see running counts. Dismissible:
              • Tap the × to collapse to a small floating chip.
              • Tap the chip to re-expand. */}
        {data.equipment_type && !tallyCollapsed && (
          <div
            className="bg-white border border-slate-200 rounded-md px-3 py-2 sm:p-4 flex items-center justify-between gap-2 sm:gap-3 sticky bottom-24 sm:bottom-4 shadow-md z-20"
            data-testid="equip-tally-bar"
          >
            <button
              type="button"
              onClick={() => setTallyCollapsed(true)}
              aria-label={t("Hide tally")}
              className="shrink-0 w-7 h-7 rounded-full border border-slate-300 text-slate-500 hover:text-slate-900 hover:border-slate-500 flex items-center justify-center text-lg leading-none"
              data-testid="equip-tally-dismiss"
            >
              ×
            </button>
            <div className="hidden sm:block font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              {t("Tally")}
            </div>
            <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm font-bold ml-auto">
              <span className="text-emerald-700" data-testid="tally-pass">{data.pass_count} PASS</span>
              <span className="text-red-700" data-testid="tally-fail">{data.fail_count} FAIL</span>
              <span className="text-slate-600" data-testid="tally-na">{data.na_count} N/A</span>
            </div>
          </div>
        )}
        {data.equipment_type && tallyCollapsed && (
          <button
            type="button"
            onClick={() => setTallyCollapsed(false)}
            className="sticky bottom-24 sm:bottom-4 ml-auto mr-44 sm:mr-0 flex items-center gap-2 bg-slate-900 text-white rounded-full px-3 py-1.5 shadow-md text-xs font-mono uppercase tracking-[0.15em] z-20 hover:bg-slate-800"
            data-testid="equip-tally-restore"
          >
            <span>{t("Tally")}</span>
            <span className="text-emerald-400">{data.pass_count}</span>
            <span className="text-red-400">{data.fail_count}</span>
            <span className="text-slate-300">{data.na_count}</span>
          </button>
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
          <HelpTipBlock formKey="preop.signoff" className="mb-3" />
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

        <div className="flex flex-col items-end gap-2">
          {failGating.blocked && (
            <p
              className="text-sm text-red-700 font-bold text-right"
              data-testid="equip-submit-fail-hint"
            >
              <Camera className="w-4 h-4 inline-block mr-1 -mt-0.5" />
              {failGating.needPhoto > 0 && failGating.needNote > 0 ? (
                <>
                  {failGating.needPhoto} {failGating.needPhoto === 1 ? t("FAIL needs photo") : t("FAILs need photos")}
                  {" · "}
                  {failGating.needNote} {failGating.needNote === 1 ? t("FAIL needs description") : t("FAILs need descriptions")}
                </>
              ) : failGating.needPhoto > 0 ? (
                <>
                  {failGating.needPhoto} {failGating.needPhoto === 1 ? t("FAIL needs photo") : t("FAILs need photos")}
                </>
              ) : (
                <>
                  {failGating.needNote} {failGating.needNote === 1 ? t("FAIL needs description") : t("FAILs need descriptions")}
                </>
              )}
            </p>
          )}
          <Button
            onClick={submit}
            disabled={saving || failGating.blocked}
            className="h-12 px-6 bg-red-700 hover:bg-red-800 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:border-slate-400"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin mr-1" />
            ) : failGating.blocked ? (
              <Camera className="w-4 h-4 mr-1" />
            ) : (
              <Save className="w-4 h-4 mr-1" />
            )}
            {failGating.blocked
              ? t("Complete FAIL items to submit")
              : t("Submit Inspection")}
          </Button>
        </div>
      </main>
    </div>
  );
}
