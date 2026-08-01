import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  clearDriverSession,
  getDriverToken,
  persistDriverSession,
} from "@/lib/driverAuth";
import { useT } from "@/lib/i18n";
import FormShell from "@/components/FormShell";
import { AsyncSearchableSelect } from "@/components/AsyncSearchableSelect";

const API = process.env.REACT_APP_BACKEND_URL;

export default function ShiftStart() {
  const navigate = useNavigate();
  const { t } = useT();
  const [driver, setDriver] = useState(null);
  const [truck, setTruck] = useState(null);
  const [trailer, setTrailer] = useState(null);
  const [hauler, setHauler] = useState({ label: "MASCI", refId: "", isTemp: false });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getDriverToken()) {
      navigate("/driver", { replace: true });
    }
  }, [navigate]);

  const lookupDrivers = useCallback(async (q) => {
    const response = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=15`,
    );
    const data = await response.json().catch(() => ({}));
    return (data.drivers || []).map((entry) => ({
      label: entry.name,
      refId: entry.employee_id || "",
      hint: entry.employee_id || "",
    }));
  }, []);

  const lookupTrucks = useCallback(async (q) => {
    const response = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const data = await response.json().catch(() => ({}));
    return (data.trucks || []).map((entry) => ({
      label: entry.unit_number,
      refId: entry.unit_pk || "",
      hint: entry.company || "",
    }));
  }, []);

  const lookupTrailers = useCallback(async (q) => {
    const response = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const data = await response.json().catch(() => ({}));
    return (data.trailers || []).map((entry) => ({
      label: entry.unit_number,
      refId: entry.unit_pk || "",
      hint: entry.company || "",
    }));
  }, []);

  const lookupHaulers = useCallback(async (q) => {
    const response = await fetch(
      `${API}/api/dispatch/driver/shift-lookups?q=${encodeURIComponent(q || "")}&limit=25`,
    );
    const data = await response.json().catch(() => ({}));
    return (data.haulers || [])
      .map((entry) => ({ label: entry.name, refId: "" }))
      .filter((entry) => entry.label);
  }, []);

  const canSubmit = !!driver?.label && !!truck?.label && !submitting;

  const onSubmit = useCallback(
    async (event) => {
      event?.preventDefault?.();
      if (!canSubmit) return;
      setSubmitting(true);
      setError("");
      try {
        const response = await fetch(`${API}/api/dispatch/driver/start-shift`, {
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
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data?.driver_token) {
          throw new Error(data?.detail || t("Could not start shift. Try again."));
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
        setError(err?.message || t("Could not start shift. Try again."));
        setSubmitting(false);
      }
    },
    [canSubmit, driver, hauler, navigate, t, trailer, truck],
  );

  return (
    <FormShell
      kicker={t("MASCI · Driver Shift Start")}
      title={t("Start your shift")}
      subtitle={t("Pick who's driving and which truck. Subs and rentals aren't in the system yet — use Add temporary if needed.")}
      backLink="/field"
      backLabel={t("Field")}
      widthClass="max-w-md"
      containerTestId="shift-start-page"
      headerRightSlot={(
        <Link
          to="/guidance/dls-driver-shift-start"
          data-testid="shift-start-help"
          className="inline-flex min-h-[2.75rem] items-center rounded-full border border-slate-200 bg-white px-3.5 py-2 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
        >
          {t("Open guide")}
        </Link>
      )}
      stickyFooter={(
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500" data-testid="shift-start-footer-note">
            {t("No password. No app. Just check in.")}
          </p>
          <button
            type="button"
            data-testid="shift-start-submit"
            disabled={!canSubmit}
            onClick={onSubmit}
            className={
              "inline-flex min-h-[3.25rem] items-center justify-center rounded-full px-5 text-sm font-semibold transition-colors " +
              (canSubmit
                ? "bg-[color:var(--brand-primary)] text-white hover:bg-[color:var(--brand-primary-hover)]"
                : "bg-slate-200 text-slate-400")
            }
          >
            {submitting ? t("Starting…") : t("Start shift")}
          </button>
        </div>
      )}
    >
      <section className="wp17-panel p-5 sm:p-6" data-testid="shift-start-card">
        <div className="mb-4 inline-flex rounded-full border border-amber-200 bg-amber-50 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-amber-800">
          {t("Operational check-in")}
        </div>

        <form className="space-y-5" onSubmit={onSubmit} noValidate>
          <AsyncSearchableSelect
            testId="shift-start-driver-name"
            label={t("Driver name")}
            placeholder={t("Type a name to search")}
            required
            autoFocus
            value={driver}
            onChange={setDriver}
            loadOptions={lookupDrivers}
            minQuery={2}
            emptyHint={t("Type at least 2 letters to search.")}
            tempPrefix={t("Add temporary driver:")}
          />
          <AsyncSearchableSelect
            testId="shift-start-truck-id"
            label={t("Truck number")}
            placeholder={t("Pick a truck or type unit number")}
            required
            value={truck}
            onChange={setTruck}
            loadOptions={lookupTrucks}
            minQuery={0}
            prefetch
            tempPrefix={t("Add temporary truck:")}
          />
          <AsyncSearchableSelect
            testId="shift-start-trailer-id"
            label={t("Trailer number")}
            optionalHint={t("optional")}
            placeholder={t("If you're pulling one")}
            value={trailer}
            onChange={setTrailer}
            loadOptions={lookupTrailers}
            minQuery={0}
            tempPrefix={t("Add temporary trailer:")}
          />
          <AsyncSearchableSelect
            testId="shift-start-company"
            label={t("Company / Hauler")}
            placeholder={t("Search or add")}
            value={hauler}
            onChange={(nextValue) => setHauler(nextValue || { label: "MASCI", refId: "", isTemp: false })}
            loadOptions={lookupHaulers}
            minQuery={0}
            prefetch
            tempPrefix={t("Add carrier / hauler:")}
          />

          {error ? (
            <div
              data-testid="shift-start-error"
              className="rounded-[1rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
              role="alert"
            >
              {error}
            </div>
          ) : null}
        </form>
      </section>
    </FormShell>
  );
}