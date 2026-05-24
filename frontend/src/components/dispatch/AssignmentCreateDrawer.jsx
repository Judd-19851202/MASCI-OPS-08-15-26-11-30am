/**
 * AssignmentCreateDrawer.jsx · iter407 · Phase 14 · Dispatch Assignment Issuance.
 *
 * Right-side slide-over that powers the dispatcher's "Create Assignment"
 * action on the Operational Board. Mirrors ShiftStart.jsx's combobox
 * pattern so issuance and self-start feel like one operational family.
 *
 * Doctrine
 * --------
 *   - One drawer · ~8 fields · fast operational issuance.
 *   - Truck = required (operational continuity follows the truck).
 *   - Driver, trailer, carrier, source, destination, project, material,
 *     notes = optional. Self-start sessions can claim later.
 *   - "Add temporary" preserved for off-roster trucks / one-off projects.
 *   - Recent-value comboboxes are fed by operational memory itself —
 *     the more dispatch issues, the more useful the dropdowns get.
 *   - 0 new collections, 0 master-list management surface.
 *
 * Endpoints used (no new endpoints):
 *   - GET  /api/dispatch/driver/shift-lookups          (drivers/trucks/trailers/haulers)
 *   - GET  /api/dispatch/driver/assignment-lookups     (recent operational memory)
 *   - POST /api/dispatch/assignments                   (iter392 create — unchanged)
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { X, Send, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

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
// ComboboxField · searchable single-select with "Add temporary" path.
// Mirrors ShiftStart's SearchableSelect contract so operations feel
// identical across the platform.
// ─────────────────────────────────────────────────────────────────────
function ComboboxField({
  testId,
  label,
  optionalHint,
  placeholder,
  value,            // { label, refId, isTemp } | null
  onChange,
  options,          // [{ label, refId, hint? }]
  emptyHint,
  tempPrefix,
  required,
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
    if (!q) return options.slice(0, 25);
    return options
      .filter((o) => (o.label || "").toLowerCase().includes(q))
      .slice(0, 25);
  }, [query, options]);

  const canAddTemp =
    query.trim().length > 0 &&
    !options.some((o) => (o.label || "").toLowerCase() === query.trim().toLowerCase());

  const choose = (opt) => {
    onChange({ label: opt.label, refId: opt.refId || "", isTemp: false });
    setQuery("");
    setOpen(false);
  };

  const addTemp = () => {
    const v = query.trim();
    if (!v) return;
    onChange({ label: v, refId: "", isTemp: true });
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
              className="mt-1.5 max-h-56 overflow-y-auto rounded-md bg-white border border-slate-300 divide-y divide-slate-100 shadow-lg"
            >
              {filtered.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-500" data-testid={`${testId}-empty`}>
                  {emptyHint || t("No matches yet.")}
                </div>
              ) : (
                filtered.map((opt) => (
                  <button
                    type="button"
                    key={`${opt.refId || ""}-${opt.label}`}
                    onClick={() => choose(opt)}
                    data-testid={`${testId}-option`}
                    className="w-full min-h-[40px] px-3 py-1.5 text-left flex items-center justify-between hover:bg-slate-50 active:bg-slate-100"
                  >
                    <span className="text-sm text-slate-900 truncate pr-2">{opt.label}</span>
                    {opt.hint ? (
                      <span className="text-[10px] uppercase tracking-widest text-slate-500 shrink-0">
                        {opt.hint}
                      </span>
                    ) : null}
                  </button>
                ))
              )}
              {canAddTemp ? (
                <button
                  type="button"
                  onClick={addTemp}
                  data-testid={`${testId}-add-temp`}
                  className="w-full min-h-[40px] px-3 py-1.5 text-left text-amber-700 hover:bg-amber-50"
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
// AssignmentCreateDrawer
// ─────────────────────────────────────────────────────────────────────
export default function AssignmentCreateDrawer({
  open,
  onClose,
  onCreated,
  tenantOverride,
}) {
  const { t } = useT();
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Live lookup state
  const [lookups, setLookups] = useState({
    drivers: [], trucks: [], trailers: [], haulers: [],
  });
  const [recents, setRecents] = useState({
    recent_projects: [], recent_materials: [], recent_sources: [], recent_destinations: [],
  });

  // Form state
  const [truck, setTruck] = useState(null);
  const [driver, setDriver] = useState(null);
  const [trailer, setTrailer] = useState(null);
  const [carrier, setCarrier] = useState({ label: "MASCI", refId: "", isTemp: false });
  const [project, setProject] = useState(null);
  const [source, setSource] = useState(null);
  const [destination, setDestination] = useState(null);
  const [material, setMaterial] = useState(null);
  const [note, setNote] = useState("");

  // Reset on open close so each issuance starts clean.
  useEffect(() => {
    if (!open) return;
    setTruck(null);
    setDriver(null);
    setTrailer(null);
    setCarrier({ label: "MASCI", refId: "", isTemp: false });
    setProject(null);
    setSource(null);
    setDestination(null);
    setMaterial(null);
    setNote("");
    setErrorMsg("");
  }, [open]);

  // Load lookups when drawer opens.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      try {
        const [r1, r2] = await Promise.all([
          fetch(`${API}/api/dispatch/driver/shift-lookups?limit=50`, {
            headers: authHeaders(tenantOverride),
          }),
          fetch(`${API}/api/dispatch/driver/assignment-lookups`, {
            headers: authHeaders(tenantOverride),
          }),
        ]);
        const j1 = await r1.json().catch(() => ({}));
        const j2 = await r2.json().catch(() => ({}));
        if (cancelled) return;
        setLookups({
          drivers: Array.isArray(j1.drivers) ? j1.drivers : [],
          trucks: Array.isArray(j1.trucks) ? j1.trucks : [],
          trailers: Array.isArray(j1.trailers) ? j1.trailers : [],
          haulers: Array.isArray(j1.haulers) ? j1.haulers : [],
        });
        setRecents({
          recent_projects: Array.isArray(j2.recent_projects) ? j2.recent_projects : [],
          recent_materials: Array.isArray(j2.recent_materials) ? j2.recent_materials : [],
          recent_sources: Array.isArray(j2.recent_sources) ? j2.recent_sources : [],
          recent_destinations: Array.isArray(j2.recent_destinations) ? j2.recent_destinations : [],
        });
      } catch {
        // Non-fatal — comboboxes still accept "Add temporary" values.
      }
    })();
    return () => { cancelled = true; };
  }, [open, tenantOverride]);

  // Project options have an attached project_name we want to recover on
  // submit, so we key by project_number.
  const projectOptions = useMemo(
    () => recents.recent_projects.map((p) => ({
      label: p.project_number,
      refId: p.project_number,
      hint: p.project_name || "",
      project_name: p.project_name || "",
    })),
    [recents.recent_projects],
  );

  const driverOptions = useMemo(
    () => lookups.drivers.map((x) => ({
      label: x.name,
      refId: x.employee_id || "",
      hint: x.employee_id || "",
    })),
    [lookups.drivers],
  );

  const truckOptions = useMemo(
    () => lookups.trucks.map((x) => ({
      label: x.unit_number,
      refId: x.unit_pk || "",
      hint: x.company || "",
    })),
    [lookups.trucks],
  );

  const trailerOptions = useMemo(
    () => lookups.trailers.map((x) => ({
      label: x.unit_number,
      refId: x.unit_pk || "",
      hint: x.company || "",
    })),
    [lookups.trailers],
  );

  const carrierOptions = useMemo(
    () => lookups.haulers.map((x) => ({ label: x.name, refId: "" })),
    [lookups.haulers],
  );

  const sourceOptions = useMemo(
    () => recents.recent_sources.map((x) => ({ label: x.label, refId: "" })),
    [recents.recent_sources],
  );

  const destinationOptions = useMemo(
    () => recents.recent_destinations.map((x) => ({ label: x.label, refId: "" })),
    [recents.recent_destinations],
  );

  const materialOptions = useMemo(
    () => recents.recent_materials.map((x) => ({ label: x.label, refId: "" })),
    [recents.recent_materials],
  );

  // ── Submit handler ──────────────────────────────────────────────
  const submit = useCallback(async () => {
    if (!truck?.label) {
      setErrorMsg(t("Truck is required to issue an assignment."));
      return;
    }
    setSubmitting(true);
    setErrorMsg("");

    // Recover project_name when the picked project carried one.
    const pickedProjectOpt = projectOptions.find((o) => o.refId === project?.refId);
    const projectName = pickedProjectOpt?.project_name || "";

    const body = {
      truck_id: truck.label,
      driver_id: driver?.refId || null,
      driver_name: driver?.label || "",
      project_number: project?.label || "",
      project_name: projectName,
      material: material?.label || "",
      source_location: source?.label || "",
      destination: destination?.label || "",
      loader_operator_name: "",
      note: note || "",
    };

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
      toast.success(t("Assignment issued · truck on the board"));
      if (onCreated) onCreated(j.assignment || null);
      onClose && onClose();
    } catch {
      setErrorMsg(t("Connection failed — try again."));
    } finally {
      setSubmitting(false);
    }
  }, [truck, driver, trailer, carrier, project, source, destination, material, note, projectOptions, tenantOverride, onCreated, onClose, t]);

  if (!open) return null;

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

        {/* Inline coaching — keeps the drawer doctrine-honest */}
        <div className="px-5 py-3 bg-orange-50 border-b border-orange-200 text-xs text-slate-700 leading-snug">
          {t("Truck is required. Driver is optional — self-start can claim later. Pick a project and source so operational memory stays accurate. Wait reasons stay canonical (set later via the driver lifecycle).")}
        </div>

        {/* Body · form */}
        <div className="px-5 py-4 space-y-4 flex-1">
          <ComboboxField
            testId="ac-truck"
            label={t("Truck")}
            required
            placeholder={t("Type a truck number")}
            value={truck}
            onChange={setTruck}
            options={truckOptions}
            tempPrefix={t("Add temporary truck:")}
            emptyHint={t("No matching truck. Type the unit number to add a temporary one.")}
          />

          <ComboboxField
            testId="ac-driver"
            label={t("Driver")}
            optionalHint={t("optional")}
            placeholder={t("Type a driver name")}
            value={driver}
            onChange={setDriver}
            options={driverOptions}
            tempPrefix={t("Add temporary driver:")}
            emptyHint={t("No matching driver. Leave blank for self-start.")}
          />

          <ComboboxField
            testId="ac-trailer"
            label={t("Trailer")}
            optionalHint={t("optional")}
            placeholder={t("Type a trailer number")}
            value={trailer}
            onChange={setTrailer}
            options={trailerOptions}
            tempPrefix={t("Add temporary trailer:")}
            emptyHint={t("No matching trailer.")}
          />

          <ComboboxField
            testId="ac-carrier"
            label={t("Carrier")}
            optionalHint={t("optional")}
            placeholder="MASCI"
            value={carrier}
            onChange={setCarrier}
            options={carrierOptions}
            tempPrefix={t("Add temporary carrier:")}
            emptyHint={t("Add a one-time carrier.")}
          />

          <ComboboxField
            testId="ac-project"
            label={t("Project")}
            optionalHint={t("optional")}
            placeholder={t("Project number")}
            value={project}
            onChange={setProject}
            options={projectOptions}
            tempPrefix={t("Add temporary project:")}
            emptyHint={t("Recent projects appear here as operations build memory.")}
          />

          <ComboboxField
            testId="ac-source"
            label={t("Source / load point")}
            optionalHint={t("optional")}
            placeholder={t("e.g. Plant 04, Pit 12")}
            value={source}
            onChange={setSource}
            options={sourceOptions}
            tempPrefix={t("Add temporary source:")}
            emptyHint={t("Recent load points appear here as operations build memory.")}
          />

          <ComboboxField
            testId="ac-destination"
            label={t("Destination")}
            optionalHint={t("optional")}
            placeholder={t("Job site or stockpile")}
            value={destination}
            onChange={setDestination}
            options={destinationOptions}
            tempPrefix={t("Add temporary destination:")}
            emptyHint={t("Recent destinations appear here as operations build memory.")}
          />

          <ComboboxField
            testId="ac-material"
            label={t("Material")}
            optionalHint={t("optional")}
            placeholder={t("e.g. Base Rock, RAP, Hot Mix")}
            value={material}
            onChange={setMaterial}
            options={materialOptions}
            tempPrefix={t("Add temporary material:")}
            emptyHint={t("Recent materials appear here as operations build memory.")}
          />

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

        {/* Footer · single action */}
        <footer className="px-5 py-4 border-t border-slate-200 sticky bottom-0 bg-white">
          <Button
            type="button"
            onClick={submit}
            disabled={submitting || !truck?.label}
            data-testid="assignment-create-submit"
            className="w-full min-h-[56px] bg-orange-600 hover:bg-orange-500 text-white text-base font-black tracking-wide"
          >
            <Plus className="w-5 h-5 mr-2" />
            {submitting ? t("Issuing…") : t("Issue assignment")}
          </Button>
          <p className="text-[11px] text-slate-500 mt-2 text-center">
            {t("Truck appears on the board immediately. Driver lifecycle stays the source of operational truth.")}
          </p>
        </footer>
      </aside>
    </div>
  );
}
