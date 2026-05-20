// NewFleetDVIR.jsx — iter251 Phase 2 · Driver-facing Daily Vehicle Inspection.
//
// Operator philosophy (per SEVERITY_RULINGS_iter251.md + 2026-05-19 brief):
//   • Native to MASCI Operations Platform — inherits Section, ChecklistRow,
//     HelpTip, SignaturePad, PhotoUpload, EquipmentCombo, paletteFor()
//   • Driver-respectful · calm · operational · NOT punitive
//   • Severity calculated server-side · driver picks PASS / FAIL / NA only
//   • Confirmation page distinguishes 🟢 Available · 🟡 Defect Logged · 🔴 OOS
//   • Mobile-first · ≥ 44px tap targets · h-14 inputs · large fonts
//   • Bilingual via useT() · zero EN leakage in ES mode
//   • Offline-tolerant: meta + units pre-fetched + cached · retry on submit
//   • Public submission path (driver_name + signature) OR signed-in driver
//
// EXPLICITLY OUT OF SCOPE in Phase 2 (do NOT drift):
//   • Dispatch / Shop / Safety dashboards (Phase 3) — landed in Phase 3
//   • Repair lifecycle hardening (Phase 4) — landed in Phase 4
//   • Motive / MaintainX integration (Phase 6)
//
// Phase 5 reuse · iter251 2026-05-19
//   This component now accepts a `kind` prop so the same form can power
//   "dvir" (daily driver), "weekly_lead" (lead driver / fleet lead
//   recurring), and "weekly_emergency" (emergency-equipment audit).
//   The server's `/api/fleet/_meta` advertises the checklist + whether
//   trailers are allowed for that kind. The form adapts copy, hides
//   trailers when `allows_trailers === false`, and re-labels the
//   submitter (Driver vs Lead vs Inspector).
//   NOTHING about defect severity, audit trail, or repair lifecycle
//   changes — those continue to flow through the same Phase 1/4 paths.

import React, { useEffect, useMemo, useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft, Truck, AlertOctagon, Save, Loader2, Plus, X, Camera, Wifi, WifiOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import { Section, ChecklistRow } from "@/components/Section";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { LangToggle } from "@/components/LangToggle";
import { HelpTip } from "@/components/HelpTip";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL || "";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2";

// PASS / FAIL / NA button group — large tap targets · gloves-friendly.
function PassFailNaButtons({ value, onChange, testId, t }) {
  const opts = [
    { v: "pass", label: t("PASS"), bg: "bg-emerald-600 hover:bg-emerald-700", text: "text-white" },
    { v: "fail", label: t("FAIL"), bg: "bg-amber-600 hover:bg-amber-700", text: "text-white" },
    { v: "na",   label: t("N/A"),  bg: "bg-slate-500 hover:bg-slate-600",   text: "text-white" },
  ];
  return (
    <div className="grid grid-cols-3 gap-1.5" data-testid={testId}>
      {opts.map((o) => {
        const active = value === o.v;
        return (
          <button
            key={o.v}
            type="button"
            onClick={() => onChange(o.v)}
            data-testid={`${testId}-${o.v}`}
            className={`h-11 sm:h-12 px-1 rounded-md text-sm font-bold uppercase tracking-wide transition-colors border-2 ${
              active
                ? `${o.bg} ${o.text} border-transparent shadow-sm`
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

// Per-item "Why this matters" rationale — pulled from severity_table_meta
// returned by /api/fleet/_meta. Collapsed by default · matches HelpTip
// kind="why" tone exactly (amber accent, lightbulb icon). Optional.
function SeverityRationale({ rationale, regulationRef, severity, t }) {
  if (!rationale) return null;
  const sevLabel = severity === "oos"
    ? t("Out of Service if failed")
    : t("Monitor — shop will see this");
  const body = (
    <div className="space-y-1.5">
      <div className="text-[12px] font-semibold text-slate-800">{sevLabel}</div>
      <div>{rationale}</div>
      {regulationRef && (
        <div className="text-[11px] text-slate-500 font-mono">
          {t("Reference")}: {regulationRef}
        </div>
      )}
    </div>
  );
  return (
    <HelpTip
      kind="why"
      title={t("Why this matters")}
      body={body}
      title_es={t("Why this matters") === "Why this matters" ? "Por qué importa" : null}
      testId="severity-rationale"
    />
  );
}

export default function NewFleetDVIR({ kind = "dvir" } = {}) {
  const nav = useNavigate();
  const { t, lang } = useT();

  // Phase 5 · kind-specific copy. Defaults preserve Phase 2 behavior.
  const isWeeklyLead = kind === "weekly_lead";
  const isWeeklyEmergency = kind === "weekly_emergency";
  const formCopy = {
    kicker: isWeeklyLead
      ? t("Fleet · Weekly Lead Inspection")
      : isWeeklyEmergency
      ? t("Fleet · Weekly Emergency Equipment")
      : t("Fleet · Driver Vehicle Inspection"),
    pageTitle: isWeeklyLead
      ? t("Weekly Lead Inspection")
      : isWeeklyEmergency
      ? t("Weekly Emergency Equipment")
      : t("Daily Vehicle Inspection"),
    submitterLabel: isWeeklyLead
      ? t("Lead inspector")
      : isWeeklyEmergency
      ? t("Inspector")
      : t("Driver name"),
    submitterTestId: isWeeklyLead
      ? "fleet-weekly-lead-name"
      : isWeeklyEmergency
      ? "fleet-weekly-emergency-name"
      : "fleet-dvir-driver-name",
    submitButton: isWeeklyLead
      ? t("Submit Lead Inspection")
      : isWeeklyEmergency
      ? t("Submit Emergency Check")
      : t("Submit DVIR"),
    helpHeader: isWeeklyLead
      ? t("Quick weekly check by the lead. High-signal items only — operational hygiene, recurring issues, critical safety items the daily DVIR also covers.")
      : isWeeklyEmergency
      ? t("Emergency equipment & safety systems check. Verify each item is present, charged, and within date.")
      : null,
  };

  // ─── Meta + units (pre-fetched + cached for offline tolerance) ───
  const [meta, setMeta] = useState(null);
  const [units, setUnits] = useState([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [metaError, setMetaError] = useState("");
  const [online, setOnline] = useState(typeof navigator !== "undefined" ? navigator.onLine : true);

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [mRes, uRes] = await Promise.all([
          fetch(`${API}/api/fleet/_meta`),
          fetch(`${API}/api/fleet/units?limit=400`),
        ]);
        if (!mRes.ok || !uRes.ok) throw new Error("meta-fetch-failed");
        const m = await mRes.json();
        const u = await uRes.json();
        if (!alive) return;
        setMeta(m);
        setUnits(u.units || []);
        try {
          sessionStorage.setItem("fleet.dvir.meta", JSON.stringify(m));
          sessionStorage.setItem("fleet.dvir.units", JSON.stringify(u.units || []));
        } catch (_e) { /* ignore quota */ }
      } catch (_e) {
        // Fall back to cached snapshot if available
        try {
          const cm = sessionStorage.getItem("fleet.dvir.meta");
          const cu = sessionStorage.getItem("fleet.dvir.units");
          if (cm && cu) {
            setMeta(JSON.parse(cm));
            setUnits(JSON.parse(cu));
            setMetaError(t("Loaded from cache · live data unavailable. Submit when signal returns."));
          } else {
            setMetaError(t("Could not load truck list. Check your signal and reload."));
          }
        } catch (_e2) {
          setMetaError(t("Could not load truck list. Check your signal and reload."));
        }
      } finally {
        if (alive) setLoadingMeta(false);
      }
    })();
    return () => { alive = false; };
  }, [t]);

  const dvir = useMemo(() => meta?.kinds?.[kind] || null, [meta, kind]);
  const truckItems = dvir?.truck_items || [];
  const trailerItems = dvir?.trailer_items || [];
  const allowsTrailers = !!dvir?.allows_trailers;

  // ─── Form state ──────────────────────────────────────────────────
  const today = new Date();
  const [driverName, setDriverName] = useState("");
  const [date, setDate] = useState(today.toISOString().slice(0, 10));
  const [time, setTime] = useState(today.toTimeString().slice(0, 5));
  const [truckUnit, setTruckUnit] = useState("");
  const [truckPlate, setTruckPlate] = useState("");
  const [truckVin, setTruckVin] = useState("");
  const [odo, setOdo] = useState("");
  const [hours, setHours] = useState("");
  const [trailers, setTrailers] = useState([]);  // [{ trailer_unit_number, checklist }]
  const [truckChecklist, setTruckChecklist] = useState({});
  const [defectDetails, setDefectDetails] = useState({});  // { item: {note, photos[]} }
  const [notes, setNotes] = useState("");
  const [signature, setSignature] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const errRef = useRef(null);

  // Auto-fill truck plate + vin when unit chosen
  const onPickTruck = (unitNumber) => {
    setTruckUnit(unitNumber);
    const u = units.find((x) => x.unit_number === unitNumber);
    if (u) {
      setTruckPlate(u.plate || "");
      setTruckVin(u.vin || "");
    }
  };

  const truckSelectable = useMemo(
    () => units.filter((u) => u.unit_type === "truck" && (u.unit_number || "").trim()),
    [units]
  );
  const trailerSelectable = useMemo(
    () => units.filter((u) => u.unit_type === "trailer" && (u.unit_number || "").trim()),
    [units]
  );

  // ─── Severity lookup · server SOT via /api/fleet/_meta ──────────
  // The server returns severity_by_item: {item_text: {severity, category,
  // rationale, regulation_ref}} so the "Why this matters" panel always
  // mirrors the v1-approved-2026-05-19 table verbatim. No client-side
  // drift surface · no string-includes heuristic.
  const severityByItem = meta?.severity_by_item || {};
  const severityHintFor = (item) => severityByItem[item] || null;

  // ─── Validation ─────────────────────────────────────────────────
  const failedItems = useMemo(() => {
    const truckFails = Object.entries(truckChecklist)
      .filter(([, v]) => v === "fail")
      .map(([k]) => k);
    const trailerFails = trailers.flatMap((tr, i) =>
      Object.entries(tr.checklist || {})
        .filter(([, v]) => v === "fail")
        .map(([k]) => ({ item: k, trailer: i }))
    );
    return { truckFails, trailerFails };
  }, [truckChecklist, trailers]);

  const allFails = [
    ...failedItems.truckFails,
    ...failedItems.trailerFails.map((f) => f.item),
  ];
  const failsMissingDetail = allFails.filter((item) => {
    const d = defectDetails[item];
    return !d || !(d.note && d.note.trim().length >= 10);
  });

  const truckProgress = useMemo(() => {
    const total = truckItems.length;
    const answered = truckItems.filter((it) => truckChecklist[it]).length;
    return { answered, total };
  }, [truckItems, truckChecklist]);

  const allTruckAnswered = truckItems.length > 0 &&
    truckProgress.answered === truckProgress.total;
  const allTrailersAnswered = !allowsTrailers || trailers.every((tr) =>
    trailerItems.every((it) => tr.checklist?.[it])
  );

  const blockReason = useMemo(() => {
    if (!driverName.trim()) return t("Please enter your name.");
    if (!truckUnit.trim()) return t("Please pick your truck.");
    if (!signature) return t("Please sign before submitting.");
    if (!allTruckAnswered) return t("Mark every truck item PASS, FAIL, or N/A.");
    if (allowsTrailers && !allTrailersAnswered) return t("Mark every trailer item PASS, FAIL, or N/A.");
    if (failsMissingDetail.length > 0) {
      return t("Each FAIL needs a short note (10+ characters).");
    }
    return "";
  }, [driverName, truckUnit, signature, allTruckAnswered, allTrailersAnswered, allowsTrailers, failsMissingDetail, t]);

  // ─── Trailer ops ────────────────────────────────────────────────
  const addTrailer = () => {
    setTrailers((arr) => [...arr, { trailer_unit_number: "", checklist: {} }]);
  };
  const removeTrailer = (idx) => {
    setTrailers((arr) => arr.filter((_, i) => i !== idx));
  };
  const setTrailerUnit = (idx, num) => {
    setTrailers((arr) => arr.map((t, i) => i === idx ? { ...t, trailer_unit_number: num } : t));
  };
  const setTrailerItem = (idx, item, val) => {
    setTrailers((arr) => arr.map((t, i) =>
      i === idx ? { ...t, checklist: { ...(t.checklist || {}), [item]: val } } : t
    ));
  };

  // ─── Defect detail (note + photos per item) ─────────────────────
  const setDefectNote = (item, note) => {
    setDefectDetails((d) => ({ ...d, [item]: { ...(d[item] || { photos: [] }), note } }));
  };
  const setDefectPhotos = (item, photos) => {
    setDefectDetails((d) => ({ ...d, [item]: { ...(d[item] || { note: "" }), photos } }));
  };

  // ─── Submit ─────────────────────────────────────────────────────
  const submit = async () => {
    if (blockReason) {
      toast.error(blockReason);
      if (errRef.current) errRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    setSubmitting(true);
    const payload = {
      kind,
      driver_name: driverName.trim(),
      inspection_date: date,
      inspection_time: time,
      truck_unit_number: truckUnit,
      truck_plate: truckPlate,
      truck_vin: truckVin,
      odometer_miles: odo,
      hour_meter: hours,
      truck_checklist: truckChecklist,
      trailers: trailers.map((tr) => ({
        trailer_unit_number: tr.trailer_unit_number,
        checklist: tr.checklist || {},
      })).filter((tr) => tr.trailer_unit_number),
      defect_details: defectDetails,
      driver_signature: signature,
      notes,
      submitted_via: "public_tile",
    };

    let attempts = 0;
    let lastErr = "";
    // Up to 3 attempts with backoff — bad-signal tolerance.
    while (attempts < 3) {
      attempts += 1;
      try {
        const r = await fetch(`${API}/api/fleet/inspections`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!r.ok) {
          const detail = await r.text().catch(() => "");
          lastErr = detail || r.statusText;
          if (r.status === 400) break;  // don't retry on validation errors
        } else {
          const result = await r.json();
          setSubmitting(false);
          nav(`/fleet/dvir/submitted/${result.inspection_id}`, {
            replace: true,
            state: {
              result,
              truckUnit,
              defectCount: result.defect_count,
              outOfService: result.out_of_service,
              truckStatusAfter: result.truck_status_after,
              defectDetails,
              failedItems: allFails,
              driverName: driverName.trim(),
            },
          });
          return;
        }
      } catch (e) {
        lastErr = e?.message || String(e);
      }
      // backoff: 1s, 3s
      await new Promise((res) => setTimeout(res, attempts * 1000));
    }
    setSubmitting(false);
    toast.error(t("Submission failed — please try again."), {
      description: lastErr.slice(0, 120),
    });
  };

  // ─── Render ─────────────────────────────────────────────────────
  if (loadingMeta) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center">
        <div className="text-slate-600 font-mono text-sm uppercase tracking-widest">
          <Loader2 className="w-5 h-5 inline-block animate-spin mr-2" />
          {t("Loading DVIR form…")}
        </div>
      </div>
    );
  }

  if (!dvir) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center p-6">
        <div className="max-w-md bg-white border-2 border-red-300 rounded-md p-6 text-center">
          <AlertOctagon className="w-10 h-10 text-red-600 mx-auto mb-3" />
          <h2 className="font-display text-xl font-bold text-slate-900 mb-2">
            {t("DVIR form unavailable")}
          </h2>
          <p className="text-sm text-slate-700 mb-4">{metaError || t("Please reload.")}</p>
          <Button asChild className="bg-amber-600 hover:bg-amber-700 text-white">
            <Link to="/field">{t("Back to Field")}</Link>
          </Button>
        </div>
      </div>
    );
  }

  const approvalVersion = meta?.severity_table_approval?.version || meta?.severity_table_version;

  return (
    <div className="min-h-screen blueprint-bg" data-testid="fleet-dvir-form">
      <div className="caution-stripe" />

      <header className="bg-slate-900 border-b-4 border-amber-600">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex items-center gap-2">
            {!online && (
              <span
                className="inline-flex items-center gap-1 text-amber-300 text-[11px] font-mono uppercase tracking-wider"
                data-testid="dvir-offline-indicator"
              >
                <WifiOff className="w-3.5 h-3.5" />
                {t("Offline")}
              </span>
            )}
            {online && (
              <span className="hidden sm:inline-flex items-center gap-1 text-emerald-300 text-[11px] font-mono uppercase tracking-wider">
                <Wifi className="w-3.5 h-3.5" />
                {t("Online")}
              </span>
            )}
            <LangToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-10 pb-32">
        <div className="mb-4">
          <Link
            to="/field"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-amber-600 font-bold"
            data-testid="dvir-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Field")}
          </Link>
        </div>

        <div className="mb-6 sm:mb-8 flex items-start gap-3 sm:gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-md bg-amber-600 text-white shrink-0">
            <Truck className="w-6 h-6 sm:w-7 sm:h-7" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] text-amber-700 font-bold">
              {formCopy.kicker}
            </span>
            <h1 className="font-display text-2xl sm:text-4xl font-black tracking-tight text-slate-900 mt-0.5 leading-tight">
              {formCopy.pageTitle}
            </h1>
            <p className="text-slate-600 text-sm sm:text-base mt-1.5">
              {formCopy.helpHeader || t("Walk around your truck before you roll. Mark every item. Anything FAIL gets logged so Shop can keep us on the road.")}
            </p>
          </div>
        </div>

        {metaError && (
          <div
            className="mb-5 rounded-md bg-amber-50 border-2 border-amber-300 text-amber-900 px-4 py-3 text-sm"
            data-testid="dvir-cache-banner"
          >
            {metaError}
          </div>
        )}

        {/* SECTION 01 — Driver & Truck */}
        <Section number="01" title={t("Driver & Truck")}>
          <HelpTip
            kind="why"
            title={t("Why we ask for your name")}
            body={t("Accountability — Shop and Dispatch need to know who walked this truck. Drivers who report defects honestly keep the whole crew safe.")}
            testId="dvir-tip-driver"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-semibold text-slate-800">{formCopy.submitterLabel}</Label>
              <EmployeeCombo
                value={driverName}
                onChange={setDriverName}
                placeholder={t("Type or pick name…")}
                testId={formCopy.submitterTestId + "-combo"}
                className="mt-1"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                {t("If you're new to MASCI, type your full name and tap '+ Add to roster'. Future inspections will autocomplete.")}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-sm font-semibold text-slate-800">{t("Date")}</Label>
                <Input
                  type="date"
                  className={inputCls + " mt-1"}
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  data-testid="dvir-date"
                />
              </div>
              <div>
                <Label className="text-sm font-semibold text-slate-800">{t("Time")}</Label>
                <Input
                  type="time"
                  className={inputCls + " mt-1"}
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  data-testid="dvir-time"
                />
              </div>
            </div>
          </div>

          <div>
            <Label className="text-sm font-semibold text-slate-800">{t("Truck unit")}</Label>
            <select
              className={inputCls + " mt-1 w-full bg-white px-3"}
              value={truckUnit}
              onChange={(e) => onPickTruck(e.target.value)}
              data-testid="dvir-truck-select"
            >
              <option value="">{t("— Pick your truck —")}</option>
              {truckSelectable.map((u) => (
                <option key={u.id || u.unit_number} value={u.unit_number}>
                  {u.unit_number} — {u.make_model || u.category}
                </option>
              ))}
            </select>
          </div>

          {truckUnit && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div>
                <Label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{t("Plate")}</Label>
                <Input className="h-11 mt-1" value={truckPlate} onChange={(e) => setTruckPlate(e.target.value)} data-testid="dvir-plate" />
              </div>
              <div>
                <Label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{t("VIN")}</Label>
                <Input className="h-11 mt-1" value={truckVin} onChange={(e) => setTruckVin(e.target.value)} data-testid="dvir-vin" />
              </div>
              <div>
                <Label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{t("Odometer")}</Label>
                <Input className="h-11 mt-1" inputMode="numeric" value={odo} onChange={(e) => setOdo(e.target.value)} data-testid="dvir-odo" />
              </div>
              <div>
                <Label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{t("Hour meter")}</Label>
                <Input className="h-11 mt-1" inputMode="numeric" value={hours} onChange={(e) => setHours(e.target.value)} data-testid="dvir-hours" />
              </div>
            </div>
          )}
        </Section>

        {/* SECTION 02 — Truck Walk-Around (or kind-appropriate checklist) */}
        <Section
          number="02"
          title={isWeeklyEmergency ? t("Emergency Equipment Check")
                 : isWeeklyLead ? t("Lead Walk-Around")
                 : t("Truck Walk-Around")}
          className="mt-5"
        >
          <HelpTip
            kind="example"
            title={t("How to walk a truck")}
            body={t("Front · driver side · rear · passenger side. Look for leaks under the engine, listen for air, check lights with the 4-ways on, look at every tire's tread.")}
            testId="dvir-tip-walkaround"
          />
          <HelpTip
            kind="why"
            title={t("Air brakes · what to listen for")}
            body={t("Build to 95 psi · listen for leaks at gladhands and chambers · then engine off and watch the gauge for 2 minutes · should not drop more than ~4 psi/min. If it bleeds faster, it's a real defect — not driver error.")}
            testId="dvir-tip-airbrakes"
          />
          <HelpTip
            kind="next"
            title={t("Tires · quick check")}
            body={t("Tread depth gauge if you have one · otherwise eyeball the wear bars. Walk every tire and run your hand along the sidewall — bulges and cuts feel obvious. Note any audible hiss.")}
            testId="dvir-tip-tires"
          />
          <div className="text-[12px] font-mono uppercase tracking-widest text-slate-500 mt-2 mb-1">
            {t("Progress")}: {truckProgress.answered} / {truckProgress.total}
          </div>
          <div className="divide-y divide-slate-100 -mt-2">
            {truckItems.map((item) => (
              <DVIRItem
                key={item}
                item={item}
                value={truckChecklist[item] || ""}
                onChange={(v) => setTruckChecklist((c) => ({ ...c, [item]: v }))}
                detail={defectDetails[item]}
                onDetailNote={(n) => setDefectNote(item, n)}
                onDetailPhotos={(p) => setDefectPhotos(item, p)}
                severityHint={severityHintFor(item)}
                t={t}
              />
            ))}
          </div>
        </Section>

        {/* SECTION 03 — Trailer Walk-Around (only when kind allows trailers) */}
        {allowsTrailers && (
        <Section
          number="03"
          title={t("Trailer Walk-Around")}
          className="mt-5"
          aside={
            <Button
              type="button"
              variant="outline"
              className="border-amber-600 text-amber-700 hover:bg-amber-50 h-10"
              onClick={addTrailer}
              data-testid="dvir-add-trailer"
            >
              <Plus className="w-4 h-4 mr-1" />
              {t("Add trailer")}
            </Button>
          }
        >
          {trailers.length === 0 ? (
            <div className="text-sm text-slate-600 italic">
              {t("No trailer today? Skip this section.")}
            </div>
          ) : (
            <>
              <HelpTip
                kind="why"
                title={t("Coupling · the most common roadside finding")}
                body={t("Confirm the kingpin is fully seated in the fifth wheel · jaws closed · safety pin in place. Tug-test forward in low gear. A bad coupling will drop the trailer · always worth the extra 10 seconds.")}
                testId="dvir-tip-coupling"
              />
              {trailers.map((tr, idx) => (
              <div key={idx} className="border-2 border-slate-200 rounded-md p-4 bg-slate-50/40 mb-4 last:mb-0" data-testid={`dvir-trailer-${idx}`}>
                <div className="flex items-end justify-between gap-3 mb-3">
                  <div className="flex-1">
                    <Label className="text-sm font-semibold text-slate-800">
                      {t("Trailer")} #{idx + 1}
                    </Label>
                    <select
                      className={inputCls + " mt-1 w-full bg-white px-3"}
                      value={tr.trailer_unit_number}
                      onChange={(e) => setTrailerUnit(idx, e.target.value)}
                      data-testid={`dvir-trailer-${idx}-select`}
                    >
                      <option value="">{t("— Pick trailer —")}</option>
                      {trailerSelectable.map((u) => (
                        <option key={u.id || u.unit_number} value={u.unit_number}>
                          {u.unit_number} — {u.make_model || u.category}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    className="h-11 text-slate-500 hover:text-red-700"
                    onClick={() => removeTrailer(idx)}
                    data-testid={`dvir-trailer-${idx}-remove`}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>

                {tr.trailer_unit_number && (
                  <div className="divide-y divide-slate-100">
                    {trailerItems.map((item) => (
                      <DVIRItem
                        key={item}
                        item={item}
                        value={tr.checklist?.[item] || ""}
                        onChange={(v) => setTrailerItem(idx, item, v)}
                        detail={defectDetails[item]}
                        onDetailNote={(n) => setDefectNote(item, n)}
                        onDetailPhotos={(p) => setDefectPhotos(item, p)}
                        severityHint={severityHintFor(item)}
                        t={t}
                        testIdPrefix={`dvir-trailer-${idx}`}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
            </>
          )}
        </Section>
        )}

        {/* SECTION 04 — Sign & Submit */}
        <Section number="04" title={t("Sign & Submit")} className="mt-5">
          <HelpTip
            kind="next"
            title={t("What happens next")}
            body={t("Submit and you'll see your truck's status. If anything is Out of Service, Shop is notified automatically and Dispatch will reassign. If it's a Monitor item, Shop sees it and schedules a repair window.")}
            testId="dvir-tip-next"
          />
          <div>
            <Label className="text-sm font-semibold text-slate-800">{t("Notes for Shop / Dispatch (optional)")}</Label>
            <Textarea
              className="mt-1 min-h-[80px] text-base border-2 border-slate-300"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t("Anything else worth flagging — sound, smell, vibration, recent fix?")}
              data-testid="dvir-notes"
            />
          </div>
          <div>
            <Label className="text-sm font-semibold text-slate-800">
              {isWeeklyLead ? t("Lead inspector signature")
                : isWeeklyEmergency ? t("Inspector signature")
                : t("Driver signature")}
            </Label>
            <div className="mt-1">
              <SignaturePad value={signature} onChange={setSignature} testId="dvir-signature" />
            </div>
          </div>

          {blockReason && (
            <div
              ref={errRef}
              className="rounded-md bg-amber-50 border-2 border-amber-400 px-4 py-3 text-amber-900 text-sm"
              data-testid="dvir-block-reason"
            >
              {blockReason}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button
              type="button"
              onClick={submit}
              disabled={!!blockReason || submitting}
              className="h-14 px-8 text-base font-bold bg-amber-600 hover:bg-amber-700 text-white disabled:bg-slate-300 disabled:text-slate-500"
              data-testid="dvir-submit"
            >
              {submitting ? (
                <><Loader2 className="w-5 h-5 mr-2 animate-spin" />{t("Submitting…")}</>
              ) : (
                <><Save className="w-5 h-5 mr-2" />{formCopy.submitButton}</>
              )}
            </Button>
            {approvalVersion && (
              <span
                className="text-[10px] font-mono uppercase tracking-widest text-slate-400"
                data-testid="dvir-severity-version"
                title={t("Severity table version")}
              >
                {approvalVersion}
              </span>
            )}
          </div>
        </Section>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Trucking · DVIR")}
      </footer>
    </div>
  );
}

// ─── Individual checklist row · PASS/FAIL/NA + per-FAIL detail ─────
function DVIRItem({ item, value, onChange, detail, onDetailNote, onDetailPhotos, severityHint, t, testIdPrefix }) {
  const safeId = item.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 60);
  const tid = `${testIdPrefix || "dvir-item"}-${safeId}`;
  const isFail = value === "fail";

  return (
    <div className="py-3" data-testid={tid}>
      <ChecklistRow label={item} testId={`${tid}-row`}>
        <PassFailNaButtons
          value={value}
          onChange={onChange}
          testId={`${tid}-pfn`}
          t={t}
        />
      </ChecklistRow>
      {isFail && (
        <div className="ml-0 sm:ml-2 mt-2 space-y-2" data-testid={`${tid}-defect`}>
          <Input
            className="h-12 text-base border-2 border-amber-300 bg-amber-50/40"
            placeholder={t("Describe the defect — what you saw / heard / felt (10+ chars)")}
            value={detail?.note || ""}
            onChange={(e) => onDetailNote(e.target.value)}
            data-testid={`${tid}-note`}
          />
          <PhotoUpload
            photos={detail?.photos || []}
            onChange={onDetailPhotos}
            label={t("Photos (optional but helpful)")}
            testId={`${tid}-photos`}
          />
          <div className="pt-1">
            <SeverityRationale
              severity={severityHint?.severity}
              rationale={
                severityHint?.rationale ||
                (severityHint?.severity === "oos"
                  ? t("Safety-critical for road operation or worker protection. Shop will be notified and the truck will be tagged Out of Service for this defect.")
                  : t("Shop will see this on their queue and schedule a repair window. Truck stays available."))
              }
              regulationRef={severityHint?.regulation_ref}
              t={t}
            />
          </div>
        </div>
      )}
    </div>
  );
}
