/**
 * ShiftStart.jsx · iter402 · Phase 12.9 · Driver Self-Start Operational Entry.
 *
 * Route: /shift
 *
 * Doctrine
 * --------
 * - Drivers should NEVER feel they are "using the MASCI platform".
 *   They are simply checking operational status.
 * - 0 passwords. 0 accounts. 0 enrollment.
 * - 4 inputs maximum (two required, two optional).
 * - One button: Start Shift.
 * - Tap targets ≥ 44 px. Sunlight-readable. Glove-friendly.
 *
 * iter402 refinement
 * ------------------
 * - Free-text fields replaced with searchable dropdowns sourced from
 *   the platform's canonical records (employees + equipment_master)
 *   via `GET /api/dispatch/driver/shift-lookups`.
 * - "Add temporary" fallback preserves operational continuity for
 *   subs / rentals / off-roster drivers — no roster gating.
 * - Picking from the dropdown attaches canonical IDs (employee_id /
 *   truck_unit_pk / trailer_unit_pk) so the shift session links back
 *   to the platform records when possible. Temp entries omit them.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearDriverSession,
  getDriverToken,
  persistDriverSession,
} from "@/lib/driverAuth";

const API = process.env.REACT_APP_BACKEND_URL;

// ─────────────────────────────────────────────────────────────────────
// SearchableSelect · mobile-first single-select with typeahead + "Add temp"
// ─────────────────────────────────────────────────────────────────────
function SearchableSelect({
  testId,
  label,
  optionalHint,
  placeholder,
  required,
  value,            // { label, refId } | null
  onChange,         // ({ label, refId, isTemp }) | null
  loadOptions,      // async (query) => [{ label, refId, hint? }]
  emptyHint,        // text shown when no matches
  tempPrefix,       // e.g. "Add temporary driver:"
  autoFocus,
  prefetch,         // boolean — load options on mount with empty query
  minQuery,         // typically 0 (trucks/trailers/haulers) or 2 (drivers)
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  const refresh = useCallback(
    async (q) => {
      if ((q || "").length < (minQuery || 0)) {
        setOptions([]);
        return;
      }
      setLoading(true);
      try {
        const opts = await loadOptions(q);
        setOptions(Array.isArray(opts) ? opts : []);
      } catch {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    },
    [loadOptions, minQuery],
  );

  useEffect(() => {
    if (prefetch) refresh("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => refresh(query), 180);
    return () => clearTimeout(t);
  }, [query, open, refresh]);

  // Click-outside to close
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

  const display = value?.label || "";
  const canAddTemp = query.trim().length > 0 && !options.some((o) => o.label.toLowerCase() === query.trim().toLowerCase());

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
    <div ref={containerRef} className="block">
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs uppercase tracking-[0.2em] text-slate-300 font-bold">
          {label}
        </span>
        {optionalHint ? (
          <span className="text-[10px] uppercase tracking-[0.25em] text-slate-500">
            {optionalHint}
          </span>
        ) : null}
      </div>

      {value?.label ? (
        // Selected state — calm pill + tap-to-clear
        <button
          type="button"
          data-testid={`${testId}-selected`}
          onClick={clear}
          className="w-full min-h-[56px] rounded-xl bg-slate-900 border border-amber-400 px-4 flex items-center justify-between text-left"
        >
          <span className="text-lg text-slate-50 truncate pr-3">
            {display}
            {value.isTemp ? (
              <span className="ml-2 text-[10px] uppercase tracking-[0.25em] text-amber-400">
                temp
              </span>
            ) : null}
          </span>
          <span className="text-[11px] uppercase tracking-[0.25em] text-slate-400">
            change
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
            autoFocus={!!autoFocus}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="words"
            spellCheck={false}
            className="w-full min-h-[56px] rounded-xl bg-slate-900 border border-slate-700 px-4 text-lg text-slate-50 placeholder:text-slate-600 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
          />
          {open ? (
            <div
              data-testid={`${testId}-panel`}
              className="mt-2 max-h-60 overflow-y-auto rounded-xl bg-slate-900 border border-slate-700 divide-y divide-slate-800"
            >
              {loading ? (
                <div className="px-4 py-3 text-sm text-slate-400" data-testid={`${testId}-loading`}>
                  Looking…
                </div>
              ) : options.length === 0 ? (
                <div className="px-4 py-3 text-sm text-slate-500" data-testid={`${testId}-empty`}>
                  {query.trim().length < (minQuery || 0)
                    ? emptyHint || `Type at least ${minQuery} letters to search.`
                    : "No matches yet."}
                </div>
              ) : (
                options.map((opt) => (
                  <button
                    type="button"
                    key={`${opt.refId || ""}-${opt.label}`}
                    onClick={() => choose(opt)}
                    data-testid={`${testId}-option`}
                    className="w-full min-h-[48px] px-4 py-2 text-left flex items-center justify-between hover:bg-slate-800 active:bg-slate-800"
                  >
                    <span className="text-base text-slate-50 truncate pr-3">{opt.label}</span>
                    {opt.hint ? (
                      <span className="text-[11px] uppercase tracking-widest text-slate-500 shrink-0">
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
                  className="w-full min-h-[48px] px-4 py-2 text-left text-amber-400 active:bg-slate-800"
                >
                  {(tempPrefix || "Add temporary:") + " "}
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
// ShiftStart page
// ─────────────────────────────────────────────────────────────────────
export default function ShiftStart() {
  const navigate = useNavigate();
  const [driver, setDriver] = useState(null);          // {label, refId, isTemp}
  const [truck, setTruck] = useState(null);            // ditto
  const [trailer, setTrailer] = useState(null);        // ditto (optional)
  const [hauler, setHauler] = useState({ label: "MASCI", refId: "", isTemp: false });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Skip the form if already in a shift session.
  useEffect(() => {
    if (getDriverToken()) {
      navigate("/driver", { replace: true });
    }
  }, [navigate]);

  // ─── lookup loaders (memoized so SearchableSelect can debounce) ──
  const lookupDrivers = useCallback(async (q) => {
    const r = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=15`,
    );
    const d = await r.json().catch(() => ({}));
    return (d.drivers || []).map((x) => ({
      label: x.name,
      refId: x.employee_id || "",
      hint: x.employee_id || "",
    }));
  }, []);

  const lookupTrucks = useCallback(async (q) => {
    const r = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const d = await r.json().catch(() => ({}));
    return (d.trucks || []).map((x) => ({
      label: x.unit_number,
      refId: x.unit_pk || "",
      hint: x.company || "",
    }));
  }, []);

  const lookupTrailers = useCallback(async (q) => {
    const r = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const d = await r.json().catch(() => ({}));
    return (d.trailers || []).map((x) => ({
      label: x.unit_number,
      refId: x.unit_pk || "",
      hint: x.company || "",
    }));
  }, []);

  const lookupHaulers = useCallback(async (q) => {
    const r = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const d = await r.json().catch(() => ({}));
    return (d.haulers || [])
      .map((x) => ({ label: x.name, refId: "" }))
      .filter((x) => x.label);
  }, []);

  const canSubmit = !!driver?.label && !!truck?.label && !submitting;

  const onSubmit = useCallback(
    async (e) => {
      e?.preventDefault?.();
      if (!canSubmit) return;
      setSubmitting(true);
      setError("");
      try {
        const r = await fetch(`${API}/api/dispatch/driver/start-shift`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            driver_name: driver.label,
            truck_id: truck.label,
            company: hauler?.label || "",
            trailer_id: trailer?.label || "",
            employee_id: driver.refId || "",
            truck_unit_pk: truck.refId || "",
            trailer_unit_pk: trailer?.refId || "",
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data?.driver_token) {
          throw new Error(data?.detail || "Could not start shift. Try again.");
        }
        clearDriverSession();
        persistDriverSession({
          driver_token: data.driver_token,
          session_id: data.session_id,
          expires_at: data.expires_at,
          tenant_id: data.tenant_id,
          driver: data.driver,
        });
        navigate("/driver", { replace: true });
      } catch (err) {
        setError(err?.message || "Could not start shift. Try again.");
        setSubmitting(false);
      }
    },
    [API, canSubmit, driver, truck, trailer, hauler, navigate],
  );

  return (
    <div
      className="min-h-screen bg-slate-950 text-slate-50 flex flex-col"
      data-testid="shift-start-page"
    >
      <div className="px-5 sm:px-8 pt-6 pb-2 text-[11px] uppercase tracking-[0.3em] text-amber-400">
        Operational check-in
      </div>

      <main className="flex-1 px-5 sm:px-8 pt-4 pb-10 max-w-md w-full mx-auto">
        <h1
          className="font-display text-3xl sm:text-4xl font-bold tracking-tight"
          data-testid="shift-start-title"
        >
          Start your shift
        </h1>
        <p className="mt-3 text-sm text-slate-400 leading-relaxed">
          Pick who's driving and which truck. Subs and rentals aren't in the
          system yet — tap <span className="text-amber-400">Add temporary</span> if needed.
        </p>

        <form className="mt-8 space-y-5" onSubmit={onSubmit} noValidate>
          <SearchableSelect
            testId="shift-start-driver-name"
            label="Driver name"
            placeholder="Type a name to search"
            required
            autoFocus
            value={driver}
            onChange={setDriver}
            loadOptions={lookupDrivers}
            minQuery={2}
            emptyHint="Type at least 2 letters to search."
            tempPrefix="Add temporary driver:"
          />
          <SearchableSelect
            testId="shift-start-truck-id"
            label="Truck number"
            placeholder="Pick a truck or type unit number"
            required
            value={truck}
            onChange={setTruck}
            loadOptions={lookupTrucks}
            minQuery={0}
            prefetch
            tempPrefix="Add temporary truck:"
          />
          <SearchableSelect
            testId="shift-start-trailer-id"
            label="Trailer number"
            optionalHint="optional"
            placeholder="If you're pulling one"
            value={trailer}
            onChange={setTrailer}
            loadOptions={lookupTrailers}
            minQuery={0}
            tempPrefix="Add temporary trailer:"
          />
          <SearchableSelect
            testId="shift-start-company"
            label="Company / Hauler"
            placeholder="Search or add"
            value={hauler}
            onChange={(v) => setHauler(v || { label: "MASCI", refId: "", isTemp: false })}
            loadOptions={lookupHaulers}
            minQuery={0}
            prefetch
            tempPrefix="Add carrier / hauler:"
          />

          {error ? (
            <div
              data-testid="shift-start-error"
              className="rounded-xl bg-rose-900/40 border border-rose-700 text-rose-100 px-4 py-3 text-sm"
              role="alert"
            >
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            data-testid="shift-start-submit"
            disabled={!canSubmit}
            className={
              "w-full inline-flex items-center justify-center min-h-[64px] " +
              "rounded-2xl text-lg font-bold tracking-wide uppercase " +
              "transition-colors " +
              (canSubmit
                ? "bg-amber-400 text-slate-950 active:bg-amber-300"
                : "bg-slate-800 text-slate-500")
            }
          >
            {submitting ? "Starting…" : "Start shift"}
          </button>

          <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500 pt-2">
            No password. No app. Just check in.
          </p>
        </form>
      </main>
    </div>
  );
}
