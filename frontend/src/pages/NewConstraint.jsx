// NewConstraint.jsx — Phase V-Prelude · Wave 1 · Substrate.
//
// One-screen mobile-safe create form for an operational constraint.
// Calm, text-first, no rich-text editor.
// Read OPERATIONAL_CONSTRAINT_FOUNDATION.md before changes.

import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { createConstraint } from "@/lib/operationalApi";
import { getConstraintCapabilities } from "@/lib/constraintCapabilities";

const DISCIPLINES = [
  "utilities", "access", "MOT", "survey",
  "QC", "FAA", "subcontractor", "other",
];

const KINDS = [
  "utility-conflict", "owner-hold", "access", "MOT",
  "survey", "QC-fail", "FAA-closure", "sub-delay", "other",
];

const SEVERITIES = ["low", "medium", "high"];

export default function NewConstraint() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const caps = React.useMemo(() => getConstraintCapabilities(), []);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState("");
  const [form, setForm] = React.useState({
    project_id: params.get("project_id") || "",
    title: "",
    discipline: "utilities",
    kind: "utility-conflict",
    severity: "medium",
    owner: "",
    operational_impact: "",
    notes: "",
  });

  if (!caps["constraint.create"]) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-slate-700">
        <h1 className="text-xl font-semibold mb-2">File a constraint</h1>
        <p className="text-sm text-slate-500">
          Your role does not include filing constraints.
        </p>
      </div>
    );
  }

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.project_id.trim() || !form.title.trim()) {
      setErr("Project and title are required.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const c = await createConstraint({
        project_id: form.project_id.trim(),
        title: form.title.trim(),
        discipline: form.discipline,
        kind: form.kind,
        severity: form.severity,
        owner: form.owner.trim(),
        operational_impact: form.operational_impact.trim(),
        notes: form.notes.trim(),
      });
      navigate(`/constraints/${c.id}`);
    } catch (e2) {
      setErr(e2.message || "Could not file constraint");
      setBusy(false);
    }
  };

  return (
    <div data-testid="new-constraint-page" className="max-w-2xl mx-auto p-4 sm:p-6 text-slate-800">
      <h1 className="text-xl sm:text-2xl font-semibold mb-1">File a constraint</h1>
      <p className="text-xs text-slate-500 mb-5">
        Capture a real operational blocker. Calm, text-only — no scheduling,
        no CPM logic.
      </p>

      <form onSubmit={submit} className="space-y-3" data-testid="new-constraint-form">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <label className="text-xs text-slate-600">
            Project
            <input
              data-testid="field-project_id"
              value={form.project_id}
              onChange={set("project_id")}
              required
              className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
            />
          </label>
          <label className="text-xs text-slate-600">
            Severity
            <select
              data-testid="field-severity"
              value={form.severity}
              onChange={set("severity")}
              className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>

        <label className="text-xs text-slate-600 block">
          Title
          <input
            data-testid="field-title"
            value={form.title}
            onChange={set("title")}
            placeholder="What is blocking work?"
            required
            maxLength={140}
            className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
          />
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <label className="text-xs text-slate-600">
            Discipline
            <select
              data-testid="field-discipline"
              value={form.discipline}
              onChange={set("discipline")}
              className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
            >
              {DISCIPLINES.map((d) => (<option key={d} value={d}>{d}</option>))}
            </select>
          </label>
          <label className="text-xs text-slate-600">
            Kind
            <select
              data-testid="field-kind"
              value={form.kind}
              onChange={set("kind")}
              className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
            >
              {KINDS.map((k) => (<option key={k} value={k}>{k}</option>))}
            </select>
          </label>
        </div>

        <label className="text-xs text-slate-600 block">
          Responsible party (optional)
          <input
            data-testid="field-owner"
            value={form.owner}
            onChange={set("owner")}
            placeholder="FPL · GC · Owner · sub name…"
            maxLength={200}
            className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
          />
        </label>

        <label className="text-xs text-slate-600 block">
          Operational impact
          <textarea
            data-testid="field-operational_impact"
            value={form.operational_impact}
            onChange={set("operational_impact")}
            placeholder="What stops working? Crew idle? Single lane? Pause cure time?"
            rows={2}
            maxLength={500}
            className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
          />
        </label>

        <label className="text-xs text-slate-600 block">
          Notes
          <textarea
            data-testid="field-notes"
            value={form.notes}
            onChange={set("notes")}
            placeholder="Additional context"
            rows={4}
            maxLength={4000}
            className="mt-1 block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
          />
        </label>

        {err && (
          <div data-testid="new-constraint-error" className="text-sm text-rose-700">
            {err}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={busy}
            data-testid="new-constraint-submit"
            className="text-sm font-medium px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
          >
            {busy ? "Filing…" : "File constraint"}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            data-testid="new-constraint-cancel"
            className="text-sm font-medium px-3 py-1.5 rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
