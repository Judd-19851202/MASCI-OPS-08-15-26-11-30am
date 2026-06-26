/**
 * AssignmentCreateDrawer.jsx · iter408 · Phase 14.1 + 14.2.
 *
 * Refined dispatch issuance drawer. Phase 14.1 made every dropdown
 * searchable with seeded defaults + historical recents. Phase 14.2
 * added Haul Type continuity so the same drawer issues material
 * hauls AND equipment moves through one DLS.
 *
 * Doctrine
 * --------
 *   - Haul Type drives conditional fields.
 *   - Truck stays required regardless of haul type.
 *   - Driver remains optional — self-start can claim later.
 *   - All comboboxes use seeded + historical + master records.
 *     "Add temporary" preserved for off-roster work.
 *   - 0 new collections. 0 new write endpoints.
 *     Reuses iter392 POST /api/dispatch/assignments (now accepts
 *     haul_type + equipment_id + equipment_label + pickup/dropoff).
 *
 * Endpoint used (no new endpoints):
 *   - GET  /api/dispatch/driver/assignment-lookups   (iter408 contract)
 *   - POST /api/dispatch/assignments                 (extended in iter408)
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { X, Send, Plus, Truck as TruckIcon, Wrench, ArrowRight, Package, Droplet, Building2, Container } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { DraftRestorePrompt } from "@/lib/resiliency";
import { JobPicker } from "@/components/JobPicker";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders(tenantOverride) {
  const headers = { "Content-Type": "application/json" };
  const admin = getAdminToken();
  const disp = getDispatchToken();
  if (admin) headers["X-Admin-Token"] = admin;
  if (disp) headers["X-Dispatch-Token"] = disp;
  if (tenantOverride) headers["X-Tenant-Id"] = tenantOverride;
  return headers;
}

// ─────────────────────────────────────────────────────────────────────
// ComboboxField · platform-consistent searchable combobox with
// "Add temporary" path. Mirrors ShiftStart's SearchableSelect contract.
// ─────────────────────────────────────────────────────────────────────
function ComboboxField({
  testId, label, optionalHint, placeholder, required,
  value, onChange, options, emptyHint, tempPrefix,
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("touchstart", handler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
    };
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options.slice(0, 40);
    return options
      .filter((o) => {
        const lbl = (o.label || "").toLowerCase();
        const hint = (o.hint || "").toLowerCase();
        const cat = (o.category || "").toLowerCase();
        return lbl.includes(q) || hint.includes(q) || cat.includes(q);
      })
      .slice(0, 40);
  }, [query, options]);

  const canAddTemp =
    query.trim().length > 0 &&
    !options.some((o) => (o.label || "").toLowerCase() === query.trim().toLowerCase());

  const choose = (opt) => {
    onChange({
      label: opt.label,
      refId: opt.refId || "",
      hint: opt.hint || "",
      category: opt.category || "",
      isTemp: false,
    });
    setQuery("");
    setOpen(false);
  };

  const addTemp = () => {
    const v = query.trim();
    if (!v) return;
    onChange({ label: v, refId: "", hint: "", category: "", isTemp: true });
    setQuery("");
    setOpen(false);
  };

  const clear = () => {
    onChange(null);
    setQuery("");
    inputRef.current?.focus();
  };

  return (
    <div ref={containerRef}>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
          {label}{required ? <span className="text-rose-600 ml-1">*</span> : null}
        </span>
        {optionalHint ? (
          <span className="text-[10px] uppercase tracking-[0.22em] text-slate-400">
            {optionalHint}
          </span>
        ) : null}
      </div>
      {value?.label ? (
        <button
          type="button"
          onClick={clear}
          data-testid={`${testId}-selected`}
          className="w-full min-h-[48px] rounded-md bg-slate-50 border border-orange-400 px-3 flex items-center justify-between text-left"
        >
          <span className="text-sm font-bold text-slate-900 truncate pr-2">
            {value.label}
            {value.hint ? (
              <span className="ml-2 text-[11px] font-normal text-slate-500">
                {value.hint}
              </span>
            ) : null}
            {value.isTemp ? (
              <span className="ml-2 text-[10px] uppercase tracking-[0.22em] text-amber-700 font-bold">
                {t("temp")}
              </span>
            ) : null}
          </span>
          <span className="text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("change")}
          </span>
        </button>
      ) : (
        <>
          <input
            ref={inputRef}
            type="text"
            data-testid={testId}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            placeholder={placeholder}
            required={!!required}
            autoComplete="off"
            spellCheck={false}
            className="w-full min-h-[48px] rounded-md bg-white border border-slate-300 px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-orange-400 focus:ring-1 focus:ring-orange-400"
          />
          {open ? (
            <div
              data-testid={`${testId}-panel`}
              className="mt-1.5 max-h-60 overflow-y-auto rounded-md bg-white border border-slate-300 divide-y divide-slate-100 shadow-lg"
            >
              {filtered.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-500" data-testid={`${testId}-empty`}>
                  {emptyHint || t("No matches yet.")}
                </div>
              ) : (
                filtered.map((opt, idx) => (
                  <button
                    type="button"
                    key={`${opt.refId || ""}-${opt.label}-${idx}`}
                    onClick={() => choose(opt)}
                    data-testid={`${testId}-option`}
                    className="w-full min-h-[44px] px-3 py-1.5 text-left flex items-center justify-between hover:bg-slate-50 active:bg-slate-100"
                  >
                    <span className="text-sm text-slate-900 truncate pr-2">{opt.label}</span>
                    <span className="text-[10px] uppercase tracking-widest text-slate-500 shrink-0 flex items-center gap-2">
                      {opt.category ? <span>{opt.category}</span> : null}
                      {opt.hint ? <span className="text-slate-400">{opt.hint}</span> : null}
                      {opt.source === "seed" ? <span className="text-emerald-700">seed</span> : null}
                      {opt.source === "history" ? <span className="text-slate-600">recent</span> : null}
                    </span>
                  </button>
                ))
              )}
              {canAddTemp ? (
                <button
                  type="button"
                  onClick={addTemp}
                  data-testid={`${testId}-add-temp`}
                  className="w-full min-h-[44px] px-3 py-1.5 text-left text-amber-700 hover:bg-amber-50"
                >
                  {(tempPrefix || t("Add temporary:")) + " "}
                  <span className="font-bold">{query.trim()}</span>
                </button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// HaulTypePicker · segmented selector at the top of the drawer.
// ─────────────────────────────────────────────────────────────────────
function HaulTypePicker({ value, onChange, types }) {
  const { t } = useT();
  const iconFor = (h) => {
    if (h === "Equipment Move") return Wrench;
    if (h === "Tanker / Liquid Asphalt") return Droplet;
    if (h === "Spoils / Dump") return Package;
    if (h === "Support / Misc") return ArrowRight;
    // TRACK 15.82B — Roll-Off uses Container icon to mirror the
    // dispatch home Issue Work card.
    if (h === "Roll-Off") return Container;
    return TruckIcon;
  };
  return (
    <div data-testid="ac-haul-type-group">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-700 font-bold mb-1.5">
        {t("Haul type")} <span className="text-rose-600 ml-1">*</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {(types || []).map((h) => {
          const Icon = iconFor(h);
          const active = value === h;
          return (
            <button
              key={h}
              type="button"
              data-testid={`ac-haul-type-${h.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
              onClick={() => onChange(h)}
              className={`min-h-[56px] rounded-md border px-3 py-2 text-left flex items-center gap-2 transition-shadow ${
                active
                  ? "bg-orange-50 border-orange-400 shadow-sm"
                  : "bg-white border-slate-300 hover:border-orange-300"
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? "text-orange-700" : "text-slate-600"}`} />
              <span className={`text-sm font-bold ${active ? "text-orange-900" : "text-slate-800"}`}>
                {t(h)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Main drawer
// ─────────────────────────────────────────────────────────────────────
export default function AssignmentCreateDrawer({
  open, onClose, onCreated, tenantOverride,
  initialHaulType,                              // iter411 · Phase 16 · preselect from dispatch hub
}) {
  const { t } = useT();
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Lookup payload (single round-trip)
  const [L, setL] = useState({
    haul_types: [], drivers: [], trucks: [], trailers: [], equipment: [],
    carriers: [], projects: [],
    sources: [], destinations: [],
    pickup_locations: [], dropoff_locations: [],
    materials: [],
    equipment_examples: [],
    // iter410 · Phase 15.1 · Tanker / Liquid Asphalt lookups
    tanker_sources: [], tanker_destinations: [], liquid_products: [],
  });

  // Form state
  const [haulType, setHaulType] = useState("Material");
  const [truck, setTruck] = useState(null);
  const [driver, setDriver] = useState(null);
  const [trailer, setTrailer] = useState(null);
  const [carrier, setCarrier] = useState({ label: "MASCI", refId: "", isTemp: false });
  // Track 15.68B · resolve tenant-aware default carrier label on mount.
  useEffect(() => {
    try {
      const cn = window.sessionStorage.getItem("branding.companyName");
      if (cn && cn !== "MASCI") setCarrier((c) => ({ ...c, label: cn }));
    } catch { /* noop */ }
  }, []);
  const [project, setProject] = useState(null);
  const [source, setSource] = useState(null);
  const [destination, setDestination] = useState(null);
  const [material, setMaterial] = useState(null);
  const [equipment, setEquipment] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [dropoff, setDropoff] = useState(null);
  // iter410 · Phase 15.1 · Tanker fields
  const [tankerSource, setTankerSource] = useState(null);
  const [tankerDestination, setTankerDestination] = useState(null);
  const [liquidProduct, setLiquidProduct] = useState(null);
  const [note, setNote] = useState("");

  // iter438 · Phase 31 · Pass C · text-only draft protection for the
  // assignment-create drawer. Stored in localStorage at
  // `masci.draft.dispatch-assignment-new` · NEVER auto-applies on
  // open · restore prompt is the only path back into a half-typed
  // assignment. Lookups (truck/driver/etc.) are stored as
  // {label, refId} so the live form reattaches them after reload.
  const DRAFT_KEY = "masci.draft.dispatch-assignment-new";
  const DRAFT_TTL_MS = 14 * 24 * 60 * 60 * 1000;
  const [pendingDraft, setPendingDraft] = useState(null);
  const draftTimerRef = useRef(null);

  const _readDraft = useCallback(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return null;
      const d = JSON.parse(raw);
      if (!d || !d.savedAt) return null;
      if (Date.now() - d.savedAt > DRAFT_TTL_MS) {
        localStorage.removeItem(DRAFT_KEY);
        return null;
      }
      return d;
    } catch { return null; }
  }, []);
  const _writeDraft = useCallback((payload) => {
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({
        ...payload, savedAt: Date.now(),
      }));
    } catch { /* localStorage unavailable · operational continuity */ }
  }, []);
  const _clearDraft = useCallback(() => {
    try { localStorage.removeItem(DRAFT_KEY); } catch { /* noop */ }
  }, []);


  // Reset on open
  useEffect(() => {
    if (!open) return;
    setHaulType(initialHaulType || "Material");
    setTruck(null);
    setDriver(null);
    setTrailer(null);
    setCarrier({ label: "MASCI", refId: "", isTemp: false });
    setProject(null);
    setSource(null);
    setDestination(null);
    setMaterial(null);
    setEquipment(null);
    setPickup(null);
    setDropoff(null);
    setTankerSource(null);
    setTankerDestination(null);
    setLiquidProduct(null);
    setNote("");
    setErrorMsg("");
  }, [open, initialHaulType]);

  // iter438 · Phase 31 · Pass C · hydrate pendingDraft from localStorage
  // AFTER the reset effect so the form is pristine before we offer
  // restore. NEVER auto-applies · the prompt is the only path back in.
  useEffect(() => {
    if (!open) {
      setPendingDraft(null);
      return;
    }
    setPendingDraft(_readDraft());
  }, [open, _readDraft]);

  // Load lookups
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${API}/api/dispatch/driver/assignment-lookups`, {
          headers: authHeaders(tenantOverride),
        });
        const j = await r.json().catch(() => ({}));
        if (cancelled) return;
        setL({
          haul_types: j.haul_types || ["Material", "Equipment Move", "Roll-Off", "Tanker / Liquid Asphalt", "Spoils / Dump", "Support / Misc"],
          drivers: j.drivers || [],
          trucks: j.trucks || [],
          trailers: j.trailers || [],
          equipment: j.equipment || [],
          carriers: j.carriers || [],
          projects: j.projects || [],
          sources: j.sources || [],
          destinations: j.destinations || [],
          pickup_locations: j.pickup_locations || [],
          dropoff_locations: j.dropoff_locations || [],
          materials: j.materials || [],
          equipment_examples: j.equipment_examples || [],
          tanker_sources: j.tanker_sources || [],
          tanker_destinations: j.tanker_destinations || [],
          liquid_products: j.liquid_products || [],
        });
      } catch {
        /* non-fatal */
      }
    })();
    return () => { cancelled = true; };
  }, [open, tenantOverride]);

  // iter438 · debounced autosave on any meaningful state change while
  // drawer is open. Captures everything except local UI flags (busy,
  // error). Selected lookups persist as {label, refId} so the form
  // re-attaches cleanly on restore.
  useEffect(() => {
    if (!open) return;
    const isEmptyFresh =
      haulType === (initialHaulType || "Material") && !truck && !driver
      && !trailer && !project && !source && !destination && !material
      && !equipment && !pickup && !dropoff && !tankerSource
      && !tankerDestination && !liquidProduct && !note.trim()
      && (!carrier || carrier.label === "MASCI");
    if (isEmptyFresh) return;
    if (draftTimerRef.current) clearTimeout(draftTimerRef.current);
    draftTimerRef.current = setTimeout(() => {
      _writeDraft({
        haulType, truck, driver, trailer, carrier, project, source,
        destination, material, equipment, pickup, dropoff,
        tankerSource, tankerDestination, liquidProduct, note,
      });
    }, 700);
    return () => { if (draftTimerRef.current) clearTimeout(draftTimerRef.current); };
  }, [open, haulType, truck, driver, trailer, carrier, project, source,
      destination, material, equipment, pickup, dropoff, tankerSource,
      tankerDestination, liquidProduct, note, initialHaulType]);

  const onRestoreDraft = useCallback(() => {
    if (!pendingDraft) return;
    if (pendingDraft.haulType) setHaulType(pendingDraft.haulType);
    if (pendingDraft.truck) setTruck(pendingDraft.truck);
    if (pendingDraft.driver) setDriver(pendingDraft.driver);
    if (pendingDraft.trailer) setTrailer(pendingDraft.trailer);
    if (pendingDraft.carrier) setCarrier(pendingDraft.carrier);
    if (pendingDraft.project) setProject(pendingDraft.project);
    if (pendingDraft.source) setSource(pendingDraft.source);
    if (pendingDraft.destination) setDestination(pendingDraft.destination);
    if (pendingDraft.material) setMaterial(pendingDraft.material);
    if (pendingDraft.equipment) setEquipment(pendingDraft.equipment);
    if (pendingDraft.pickup) setPickup(pendingDraft.pickup);
    if (pendingDraft.dropoff) setDropoff(pendingDraft.dropoff);
    if (pendingDraft.tankerSource) setTankerSource(pendingDraft.tankerSource);
    if (pendingDraft.tankerDestination) setTankerDestination(pendingDraft.tankerDestination);
    if (pendingDraft.liquidProduct) setLiquidProduct(pendingDraft.liquidProduct);
    if (typeof pendingDraft.note === "string") setNote(pendingDraft.note);
    setPendingDraft(null);
    toast.success(t("Draft restored"));
  }, [pendingDraft, t]);

  const onDiscardDraft = useCallback(() => {
    _clearDraft();
    setPendingDraft(null);
    toast.message(t("Draft discarded"));
  }, [t]);

  // ── Option projections ─────────────────────────────────────────
  const truckOptions = useMemo(() => L.trucks.map((x) => ({
    label: x.unit_number, refId: x.unit_pk || "", hint: x.company || "", source: "master",
  })), [L.trucks]);

  const driverOptions = useMemo(() => L.drivers.map((x) => ({
    label: x.name,
    refId: x.employee_id || "",
    hint: x.cdl ? "CDL" : (x.approved ? "approved" : ""),
    source: "master",
  })), [L.drivers]);

  const trailerOptions = useMemo(() => L.trailers.map((x) => ({
    label: x.unit_number, refId: x.unit_pk || "", hint: x.company || "", source: "master",
  })), [L.trailers]);

  const equipmentOptions = useMemo(() => L.equipment.map((x) => ({
    label: x.unit_number,
    refId: x.unit_pk || "",
    hint: x.label || x.category || "",
    category: x.category || "",
    source: "master",
  })), [L.equipment]);

  const carrierOptions = useMemo(() => L.carriers.map((x) => ({
    label: x.name, refId: "", source: "master",
  })), [L.carriers]);

  const projectOptions = useMemo(() => L.projects.map((p) => ({
    label: p.project_number,
    refId: p.project_number,
    hint: p.project_name || "",
    project_name: p.project_name || "",
    source: "master",
  })), [L.projects]);

  const sourceOptions = useMemo(() => L.sources.map((s) => ({
    label: s.label, source: s.source,
  })), [L.sources]);

  const destinationOptions = useMemo(() => L.destinations.map((s) => ({
    label: s.label, source: s.source,
  })), [L.destinations]);

  const pickupOptions = useMemo(() => L.pickup_locations.map((s) => ({
    label: s.label, source: s.source,
  })), [L.pickup_locations]);

  const dropoffOptions = useMemo(() => L.dropoff_locations.map((s) => ({
    label: s.label, source: s.source,
  })), [L.dropoff_locations]);

  const materialOptions = useMemo(() => L.materials.map((m) => ({
    label: m.label, category: m.category || "", source: m.source || "seed",
  })), [L.materials]);

  // iter410 · Phase 15.1 · Tanker option projections
  const tankerSourceOptions = useMemo(() => L.tanker_sources.map((s) => ({
    label: s.label, source: s.source,
  })), [L.tanker_sources]);

  const tankerDestinationOptions = useMemo(() => L.tanker_destinations.map((s) => ({
    label: s.label, source: s.source,
  })), [L.tanker_destinations]);

  const liquidProductOptions = useMemo(() => L.liquid_products.map((p) => ({
    label: p.label, category: p.category || "", source: p.source || "seed",
  })), [L.liquid_products]);

  // ── Submit ──────────────────────────────────────────────────────
  const submit = useCallback(async () => {
    if (!truck?.label) {
      setErrorMsg(t("Truck is required to issue an assignment."));
      return;
    }
    setSubmitting(true);
    setErrorMsg("");

    const isEquipMove = haulType === "Equipment Move";
    const isTanker = haulType === "Tanker / Liquid Asphalt";
    // D-1.2 · project carries its own name now (JobPicker payload).
    // Fall back to projectOptions only for legacy paths.
    const projectName =
      project?.project_name
      || (projectOptions.find((o) => o.refId === project?.refId)?.project_name)
      || "";

    // For Equipment Move we map pickup/dropoff into the canonical
    // source/destination fields ALSO — so iter392's existing board
    // rendering, governance, and CSV exports show meaningful values
    // without any downstream code change. The dedicated pickup/dropoff
    // fields are also persisted for cycle intelligence.
    const body = {
      haul_type: haulType,
      truck_id: truck.label,
      driver_id: driver?.refId || null,
      driver_name: driver?.label || "",
      trailer_id: trailer?.refId || "",
      trailer_label: trailer?.label || "",
      carrier: carrier?.label || "",
      project_number: project?.project_number || project?.label || "",
      project_name: projectName,
      note: note || "",
    };

    if (isEquipMove) {
      body.equipment_id = equipment?.refId || "";
      body.equipment_label = equipment?.label || "";
      body.pickup_location = pickup?.label || "";
      body.dropoff_location = dropoff?.label || "";
      body.source_location = pickup?.label || "";
      body.destination = dropoff?.label || "";
      body.material = "Equipment Move";
    } else if (isTanker) {
      // iter410 · Phase 15.1 · Tanker continuity uses the canonical
      // source/destination fields so the operational board, governance,
      // CSV exports, and haul_cycles surface tanker hauls without any
      // downstream code change. liquid_product is the new tanker-only
      // wire field; material is set for backward-compat tooling.
      body.source_location = tankerSource?.label || "";
      body.destination = tankerDestination?.label || "";
      body.liquid_product = liquidProduct?.label || "";
      body.material = liquidProduct?.label || "Tanker / Liquid Asphalt";
    } else {
      body.material = material?.label || "";
      body.source_location = source?.label || "";
      body.destination = destination?.label || "";
    }

    try {
      const r = await fetch(`${API}/api/dispatch/assignments`, {
        method: "POST",
        headers: authHeaders(tenantOverride),
        body: JSON.stringify(body),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        const msg = j.detail || j.message || `${t("Issuance failed")} (${r.status})`;
        setErrorMsg(typeof msg === "string" ? msg : t("Issuance failed"));
        return;
      }
      toast.success(
        isEquipMove
          ? t("Equipment move issued · truck on the board")
          : isTanker
            ? t("Tanker haul issued · truck on the board")
            : t("Assignment issued · truck on the board"),
      );
      if (onCreated) onCreated(j.assignment || null);
      // iter438 · clear draft on confirmed creation.
      _clearDraft();
      onClose && onClose();
    } catch {
      setErrorMsg(t("Connection failed — try again."));
    } finally {
      setSubmitting(false);
    }
  }, [haulType, truck, driver, trailer, carrier, project, projectOptions, source, destination, material, equipment, pickup, dropoff, tankerSource, tankerDestination, liquidProduct, note, tenantOverride, onCreated, onClose, t]);

  if (!open) return null;

  const isEquipMove = haulType === "Equipment Move";
  const isTanker = haulType === "Tanker / Liquid Asphalt";

  return (
    <div
      className="fixed inset-0 z-50 flex"
      data-testid="assignment-create-drawer"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="flex-1 bg-slate-900/40"
        onClick={onClose}
        data-testid="assignment-create-backdrop"
      />
      <aside className="w-full max-w-md bg-white shadow-2xl flex flex-col h-full overflow-y-auto">
        {/* Header */}
        <header className="px-5 py-4 border-b border-slate-200 sticky top-0 bg-white z-10 flex items-center gap-3">
          <Send className="w-5 h-5 text-orange-600 shrink-0" />
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-orange-700 font-bold">
              {t("Dispatch issuance")}
            </div>
            <h2 className="font-display text-lg font-black tracking-tight">
              {t("Create assignment")}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="assignment-create-close"
            className="h-10 w-10 flex items-center justify-center rounded-md hover:bg-slate-100"
            aria-label={t("Close")}
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </header>

        {/* Inline coaching */}
        <div className="px-5 py-3 bg-orange-50 border-b border-orange-200 text-xs text-slate-700 leading-snug">
          {isEquipMove
            ? t("Equipment Move: dispatch picks the truck/lowboy, the piece of equipment being hauled, pickup, drop-off. Same lifecycle, same board — completed counts as an Equipment Move on operational memory.")
            : isTanker
              ? t("Tanker / Liquid Asphalt: dispatch picks the truck, tanker trailer, terminal/source, destination plant or tank, and the liquid product. Same lifecycle, same board — feeds plant continuity and supply truth.")
              : t("Truck is required. Driver is optional — self-start can claim later. Pick a project, source, and material so operational memory stays accurate. Wait reasons stay canonical (set later via the driver lifecycle).")}
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-4 flex-1">
          {/* iter438 · Phase 31 · Pass C · calm draft restore prompt.
              Mounts at the top of the body so it never collides with
              the haul-type picker · auto-dismisses on Restore/Discard. */}
          <DraftRestorePrompt
            pendingDraft={pendingDraft}
            onRestore={onRestoreDraft}
            onDiscard={onDiscardDraft}
            testId="assignment-create-draft-restore-prompt"
          />

          {/* Haul Type */}
          <HaulTypePicker
            value={haulType}
            onChange={setHaulType}
            types={L.haul_types}
          />

          {/* Truck — always required */}
          <ComboboxField
            testId="ac-truck"
            label={t("Truck")}
            required
            placeholder={t("Type or pick a truck number")}
            value={truck}
            onChange={setTruck}
            options={truckOptions}
            tempPrefix={t("Add temporary truck:")}
            emptyHint={t("No matching truck. Type the unit number to add a temporary one.")}
          />

          {/* Driver */}
          <ComboboxField
            testId="ac-driver"
            label={t("Driver")}
            optionalHint={t("optional")}
            placeholder={t("Type or pick a driver")}
            value={driver}
            onChange={setDriver}
            options={driverOptions}
            tempPrefix={t("Add temporary driver:")}
            emptyHint={t("No matching driver. Leave blank for self-start.")}
          />

          {/* Trailer / lowboy / tanker */}
          <ComboboxField
            testId="ac-trailer"
            label={
              isEquipMove
                ? t("Lowboy / Trailer")
                : isTanker
                  ? t("Tanker trailer")
                  : t("Trailer")
            }
            optionalHint={t("optional")}
            placeholder={t("Type or pick a trailer")}
            value={trailer}
            onChange={setTrailer}
            options={trailerOptions}
            tempPrefix={t("Add temporary trailer:")}
            emptyHint={t("No matching trailer.")}
          />

          {/* Carrier */}
          <ComboboxField
            testId="ac-carrier"
            label={t("Carrier")}
            optionalHint={t("optional")}
            placeholder="MASCI"
            value={carrier}
            onChange={setCarrier}
            options={carrierOptions}
            tempPrefix={t("Add carrier:")}
            emptyHint={t("Add a one-time carrier.")}
          />

          {/* D-1.2 · Project — uses the same JobPicker as Daily
              Reports and Excavations so the dispatcher gets the same
              certified job library, custom-job escape hatch, and
              autofill behaviour. */}
          <div data-testid="ac-job-picker-row">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold uppercase tracking-[0.08em] text-slate-600">
                {isEquipMove
                  ? t("Receiving job / project")
                  : isTanker
                    ? t("Plant / job / project")
                    : t("Project")}
              </label>
              <span className="text-[10px] uppercase tracking-wider text-slate-400">
                {t("optional")}
              </span>
            </div>
            <JobPicker
              projectNumber={project?.project_number || project?.label || ""}
              projectName={project?.project_name || ""}
              onSelect={(job) => {
                if (!job) {
                  setProject(null);
                  return;
                }
                // Adapt JobPicker payload → ComboboxField-compatible
                // shape so existing form code (label, refId, isTemp)
                // continues to work alongside the richer metadata.
                const next = {
                  label: job.project_number || "",
                  refId: job.project_number || "",
                  isTemp: !!job.isCustom,
                  project_number: job.project_number || "",
                  project_name: job.project_name || "",
                  location: job.location || "",
                  customer: job.customer || job.client || "",
                  project_manager: job.project_manager || job.pm || "",
                };
                setProject(next);
                // Source-location autofill — Material haul only, and
                // only when the dispatcher has not yet picked a plant.
                if (!isEquipMove && !isTanker && !source?.label && job.location) {
                  setSource({ label: job.location, refId: job.location, isTemp: true });
                }
              }}
              allowCustom={true}
              emptyHint={t("Pick a MASCI job — auto-fills number, name, location, customer, PM.")}
            />
            {(project?.project_name
              || project?.customer
              || project?.project_manager
              || project?.location) && (
              <div
                data-testid="ac-job-autofill"
                className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px]"
              >
                {project.project_name && (
                  <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <Building2 className="inline w-3 h-3 mr-1 text-slate-500" />
                    <span className="font-semibold uppercase tracking-wider text-slate-500 mr-1">{t("Name")}</span>
                    <span>{project.project_name}</span>
                  </div>
                )}
                {project.customer && (
                  <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <span className="font-semibold uppercase tracking-wider text-slate-500 mr-1">{t("Customer")}</span>
                    <span>{project.customer}</span>
                  </div>
                )}
                {project.project_manager && (
                  <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <span className="font-semibold uppercase tracking-wider text-slate-500 mr-1">{t("PM")}</span>
                    <span>{project.project_manager}</span>
                  </div>
                )}
                {project.location && (
                  <div className="bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <span className="font-semibold uppercase tracking-wider text-slate-500 mr-1">{t("Location")}</span>
                    <span>{project.location}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Conditional · Material / Equipment Move / Tanker */}
          {isEquipMove ? (
            <>
              <ComboboxField
                testId="ac-equipment"
                label={t("Equipment being hauled")}
                optionalHint={t("from equipment master")}
                placeholder={t("Type or pick equipment (e.g. EX-12)")}
                value={equipment}
                onChange={setEquipment}
                options={equipmentOptions}
                tempPrefix={t("Add temporary equipment:")}
                emptyHint={t("No matching equipment. Type a label to add a temporary one.")}
              />
              <ComboboxField
                testId="ac-pickup"
                label={t("Pickup location")}
                placeholder={t("e.g. 415 Yard, Vendor")}
                value={pickup}
                onChange={setPickup}
                options={pickupOptions}
                tempPrefix={t("Add pickup location:")}
                emptyHint={t("Pick from seeded or recent locations.")}
              />
              <ComboboxField
                testId="ac-dropoff"
                label={t("Drop-off location")}
                placeholder={t("e.g. Job Site, Shop")}
                value={dropoff}
                onChange={setDropoff}
                options={dropoffOptions}
                tempPrefix={t("Add drop-off location:")}
                emptyHint={t("Pick from seeded or recent locations.")}
              />
            </>
          ) : isTanker ? (
            <>
              <ComboboxField
                testId="ac-tanker-source"
                label={t("Terminal / source")}
                placeholder={t("e.g. Asphalt Terminal, Port")}
                value={tankerSource}
                onChange={setTankerSource}
                options={tankerSourceOptions}
                tempPrefix={t("Add terminal / source:")}
                emptyHint={t("Pick from seeded terminals or recent values.")}
              />
              <ComboboxField
                testId="ac-tanker-destination"
                label={t("Destination plant / tank")}
                placeholder={t("e.g. MASCI Hot Plant 1, Storage Tank")}
                value={tankerDestination}
                onChange={setTankerDestination}
                options={tankerDestinationOptions}
                tempPrefix={t("Add destination plant / tank:")}
                emptyHint={t("Pick from seeded plants/tanks or recent values.")}
              />
              <ComboboxField
                testId="ac-liquid-product"
                label={t("Liquid product")}
                optionalHint={t("optional")}
                placeholder={t("e.g. PG 64-22, CRS-2, Diesel")}
                value={liquidProduct}
                onChange={setLiquidProduct}
                options={liquidProductOptions}
                tempPrefix={t("Add liquid product:")}
                emptyHint={t("Pick from the seeded liquid catalog or recent values.")}
              />
            </>
          ) : (
            <>
              <ComboboxField
                testId="ac-source"
                label={t("Source / load point")}
                placeholder={t("e.g. MASCI Hot Plant 1, 415 Yard")}
                value={source}
                onChange={setSource}
                options={sourceOptions}
                tempPrefix={t("Add source:")}
                emptyHint={t("Pick from seeded or recent load points.")}
              />
              <ComboboxField
                testId="ac-destination"
                label={t("Destination")}
                placeholder={t("e.g. Job Site, Dump")}
                value={destination}
                onChange={setDestination}
                options={destinationOptions}
                tempPrefix={t("Add destination:")}
                emptyHint={t("Pick from seeded or recent destinations.")}
              />
              <ComboboxField
                testId="ac-material"
                label={t("Material")}
                optionalHint={t("optional")}
                placeholder={t("Type or pick a material")}
                value={material}
                onChange={setMaterial}
                options={materialOptions}
                tempPrefix={t("Add material:")}
                emptyHint={t("Pick from the seeded material catalog or recent values.")}
              />
            </>
          )}

          {/* Note */}
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-700 font-bold mb-1.5">
              {t("Note")} <span className="text-slate-400 font-normal normal-case">({t("optional")})</span>
            </div>
            <textarea
              data-testid="ac-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              maxLength={240}
              placeholder={t("Anything the driver needs to know before they roll.")}
              className="w-full rounded-md bg-white border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:border-orange-400 focus:ring-1 focus:ring-orange-400"
            />
          </div>

          {errorMsg ? (
            <div
              className="text-sm rounded-md bg-rose-50 border border-rose-200 px-3 py-2 text-rose-800"
              data-testid="assignment-create-error"
            >
              {errorMsg}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <footer className="px-5 py-4 border-t border-slate-200 sticky bottom-0 bg-white">
          <Button
            type="button"
            onClick={submit}
            disabled={submitting || !truck?.label}
            data-testid="assignment-create-submit"
            className="w-full min-h-[56px] bg-orange-600 hover:bg-orange-500 text-white text-base font-black tracking-wide"
          >
            <Plus className="w-5 h-5 mr-2" />
            {submitting
              ? t("Issuing…")
              : isEquipMove
                ? t("Issue equipment move")
                : isTanker
                  ? t("Issue tanker haul")
                  : t("Issue assignment")}
          </Button>
          <p className="text-[11px] text-slate-500 mt-2 text-center">
            {t("Truck appears on the board immediately. Driver lifecycle stays the source of operational truth.")}
          </p>
        </footer>
      </aside>
    </div>
  );
}
