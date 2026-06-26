/**
 * OMEGA · iter452.5 Tier 1 · Field Submitter Identity Form
 *
 * Shared component embedded by public-gate submission forms (Daily
 * Report · Incident Report; QA/QC + Site Inspection inherit via
 * iter453). Captures the minimum eight-field identity contract so
 * kickback emails reach the responsible field user.
 *
 * Tier 1 (operator authorization 2026-06-01):
 *  - Required: employee dropdown + per-submit email + consent checkbox
 *  - NOT in Tier 1: phone, device binding, push opt-in, PWA install messaging
 *
 * Props:
 *   projectNumber : string · used to scope the team picker
 *   value         : { submitter_employee_id, submitter_email_at_submit,
 *                     submitter_consent_at }
 *   onChange      : (next_value) => void
 *   disabled      : boolean
 *
 * The component never POSTs by itself — the host form bundles these
 * fields into its existing submission payload.
 */
import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const CONSENT_TEXT =
  "I confirm the email address provided belongs to me. I agree to receive correction requests for the submission I am about to make.";

export const FieldSubmitterIdentityForm = ({
  projectNumber = "",
  value = {},
  onChange,
  disabled = false,
}) => {
  const [team, setTeam] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");

  const employeeId = value.submitter_employee_id || "";
  const email = value.submitter_email_at_submit || "";
  const consented = !!value.submitter_consent_at;

  // Fetch the project team roster once on mount / when project changes.
  useEffect(() => {
    let cancelled = false;
    const base = process.env.REACT_APP_BACKEND_URL;
    if (!base) return;
    setLoading(true);
    axios
      .get(
        `${base}/api/projects/${encodeURIComponent(projectNumber || "")}/team`,
        { validateStatus: () => true }
      )
      .then((r) => {
        if (cancelled) return;
        const d = r?.data || { team: [] };
        setTeam(Array.isArray(d.team) ? d.team : []);
      })
      .catch(() => {
        if (!cancelled) setTeam([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectNumber]);

  const filteredTeam = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return team;
    return team.filter((t) => {
      const hay = `${t.name || ""} ${t.employee_id || ""} ${t.role || ""} ${t.trade || ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [team, filter]);

  const setField = (k, v) => {
    onChange?.({ ...value, [k]: v });
  };

  const setConsent = (checked) => {
    onChange?.({
      ...value,
      submitter_consent_at: checked ? new Date().toISOString() : "",
    });
  };

  return (
    <div
      className="rounded-lg border border-slate-300 bg-slate-50 p-4 space-y-3"
      data-testid="fsi-form-block"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">
          Who is submitting this?
        </h3>
        <span className="text-xs text-slate-500" data-testid="fsi-form-tier">
          Tier 1 · email-only
        </span>
      </div>
      <p className="text-xs text-slate-600">
        Pick yourself from the directory and confirm a working email so
        the office can send corrections directly to you if needed.
      </p>

      {/* Employee picker */}
      <div className="space-y-1">
        <label
          htmlFor="fsi-employee-filter"
          className="block text-xs font-medium text-slate-700"
        >
          Filter directory
        </label>
        <input
          id="fsi-employee-filter"
          type="text"
          className="block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="Type name, role, or trade…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          disabled={disabled || loading}
          data-testid="fsi-employee-filter-input"
        />
      </div>

      <div className="space-y-1">
        <label
          htmlFor="fsi-employee-select"
          className="block text-xs font-medium text-slate-700"
        >
          Select your name {loading ? <em>(loading…)</em> : null}
        </label>
        <select
          id="fsi-employee-select"
          className="block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
          value={employeeId}
          onChange={(e) => setField("submitter_employee_id", e.target.value)}
          disabled={disabled || loading}
          data-testid="fsi-employee-select"
        >
          <option value="">-- choose yourself --</option>
          {filteredTeam.map((t) => (
            <option key={t.id || t.employee_id || t.name} value={t.id || t.employee_id}>
              {`${t.name}${t.role ? ` · ${t.role}` : ""}${t.trade ? ` · ${t.trade}` : ""}`}
            </option>
          ))}
        </select>
        {filteredTeam.length === 0 && !loading && (
          <p className="text-xs text-slate-500" data-testid="fsi-no-team">
            No matches. You can still submit without selecting — the
            report will be flagged as a legacy submission.
          </p>
        )}
      </div>

      {/* Email */}
      <div className="space-y-1">
        <label
          htmlFor="fsi-email-input"
          className="block text-xs font-medium text-slate-700"
        >
          Your email (where corrections will be sent)
        </label>
        <input
          id="fsi-email-input"
          type="email"
          className="block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="you@example.com"
          value={email}
          onChange={(e) =>
            setField("submitter_email_at_submit", e.target.value.trim())
          }
          disabled={disabled}
          autoComplete="email"
          data-testid="fsi-email-input"
        />
      </div>

      {/* Consent */}
      <label
        className="flex items-start gap-2 text-xs text-slate-700"
        data-testid="fsi-consent-label"
      >
        <input
          type="checkbox"
          className="mt-0.5"
          checked={consented}
          onChange={(e) => setConsent(e.target.checked)}
          disabled={disabled}
          data-testid="fsi-consent-checkbox"
        />
        <span>{CONSENT_TEXT}</span>
      </label>
    </div>
  );
};

export default FieldSubmitterIdentityForm;
