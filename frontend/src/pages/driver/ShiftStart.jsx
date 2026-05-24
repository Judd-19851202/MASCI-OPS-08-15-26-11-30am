/**
 * ShiftStart.jsx · iter401 · Phase 12.8 · Driver Self-Start Operational Entry.
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
 * - Inherits platform typography / spacing / colors / tone — radically
 *   simplified for the field.
 */
import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearDriverSession,
  getDriverToken,
  persistDriverSession,
} from "@/lib/driverAuth";

const API = process.env.REACT_APP_BACKEND_URL;

export default function ShiftStart() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    driver_name: "",
    truck_id: "",
    company: "",
    trailer_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // If somebody lands on /shift with an existing token, send them
  // straight to their shift screen — no re-entry required.
  useEffect(() => {
    if (getDriverToken()) {
      navigate("/driver", { replace: true });
    }
  }, [navigate]);

  const update = useCallback(
    (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value })),
    [],
  );

  const canSubmit =
    !!form.driver_name.trim() && !!form.truck_id.trim() && !submitting;

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
            driver_name: form.driver_name.trim(),
            truck_id: form.truck_id.trim(),
            company: form.company.trim(),
            trailer_id: form.trailer_id.trim(),
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data?.driver_token) {
          throw new Error(data?.detail || "Could not start shift. Try again.");
        }
        // Clear any stale session before persisting the fresh one.
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
    [API, canSubmit, form, navigate],
  );

  return (
    <div
      className="min-h-screen bg-slate-950 text-slate-50 flex flex-col"
      data-testid="shift-start-page"
    >
      {/* Top strip · platform identity, calm and quiet */}
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
          Tell us who's driving and which truck. That's all you need —
          assignments will appear once dispatch posts them.
        </p>

        <form className="mt-8 space-y-5" onSubmit={onSubmit} noValidate>
          <Field
            id="driver-name"
            testId="shift-start-driver-name"
            label="Driver name"
            value={form.driver_name}
            onChange={update("driver_name")}
            placeholder="First and last"
            autoFocus
            required
            autoCapitalize="words"
            autoComplete="name"
          />
          <Field
            id="truck-id"
            testId="shift-start-truck-id"
            label="Truck number"
            value={form.truck_id}
            onChange={update("truck_id")}
            placeholder="e.g. T-42"
            required
            autoCapitalize="characters"
            autoCorrect="off"
            spellCheck={false}
          />
          <Field
            id="company"
            testId="shift-start-company"
            label="Company / Hauler"
            optionalHint="optional"
            value={form.company}
            onChange={update("company")}
            placeholder="Your company name"
            autoCapitalize="words"
          />
          <Field
            id="trailer-id"
            testId="shift-start-trailer-id"
            label="Trailer number"
            optionalHint="optional"
            value={form.trailer_id}
            onChange={update("trailer_id")}
            placeholder="If you're pulling one"
            autoCapitalize="characters"
            autoCorrect="off"
            spellCheck={false}
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

function Field({
  id,
  testId,
  label,
  optionalHint,
  value,
  onChange,
  placeholder,
  required,
  autoFocus,
  autoCapitalize,
  autoCorrect,
  autoComplete,
  spellCheck,
}) {
  return (
    <label htmlFor={id} className="block">
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
      <input
        id={id}
        data-testid={testId}
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={!!required}
        autoFocus={!!autoFocus}
        autoCapitalize={autoCapitalize}
        autoCorrect={autoCorrect}
        autoComplete={autoComplete}
        spellCheck={spellCheck}
        className={
          "w-full min-h-[56px] rounded-xl bg-slate-900 border border-slate-700 " +
          "px-4 text-lg text-slate-50 placeholder:text-slate-600 " +
          "focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
        }
      />
    </label>
  );
}
