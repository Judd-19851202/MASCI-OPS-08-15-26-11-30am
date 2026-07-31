// NewConstraint.jsx — Phase V-Prelude · Wave 1 · Substrate.
//
// One-screen mobile-safe create form for an operational constraint.
// Calm, text-first, no rich-text editor.
// Read OPERATIONAL_CONSTRAINT_FOUNDATION.md before changes.

import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AlertTriangle, Workflow } from "lucide-react";
import { createConstraint } from "@/lib/operationalApi";
import { getConstraintCapabilities } from "@/lib/constraintCapabilities";
import FormShell from "@/components/FormShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";

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
      <FormShell
        kicker="MASCI · Constraints"
        title="File a constraint"
        subtitle="Operational blockers are tracked through the shared constraint workflow."
        backLabel="Constraints"
        backLink="/constraints"
        containerTestId="new-constraint-shell"
      >
        <div className="mx-auto max-w-2xl">
          <Card className="wp17-form-frame border-rose-200 bg-rose-50/80 p-5" data-testid="new-constraint-access-denied">
            <div className="flex items-start gap-3">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-rose-600 text-white">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-display text-xl font-black text-slate-900">File a constraint</h2>
                <p className="mt-2 text-sm text-slate-600">Your role does not include filing constraints.</p>
              </div>
            </div>
          </Card>
        </div>
      </FormShell>
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
    <FormShell
      kicker="MASCI · Constraints"
      title="File a constraint"
      subtitle="Capture a real operational blocker in the shared constraint workflow."
      backLabel="Constraints"
      backLink="/constraints"
      stickyFooter={(
        <div className="flex gap-3" data-testid="new-constraint-actions">
          <Button type="button" variant="outline" onClick={() => navigate(-1)} data-testid="new-constraint-cancel">
            Cancel
          </Button>
          <Button type="submit" form="new-constraint-form" disabled={busy} className="flex-1 bg-slate-900 text-white hover:bg-slate-800" data-testid="new-constraint-submit">
            {busy ? "Filing…" : "File constraint"}
          </Button>
        </div>
      )}
      containerTestId="new-constraint-shell"
    >
      <div data-testid="new-constraint-page" className="mx-auto max-w-2xl text-slate-800">
        <Card className="wp17-form-frame p-5 sm:p-6">
          <div className="mb-5 flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4" data-testid="new-constraint-summary">
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-slate-900 text-white">
              <Workflow className="h-5 w-5" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">Operational blocker</div>
              <p className="mt-1 text-sm text-slate-600">Log the blocker, who owns it, and how it affects work in the field.</p>
            </div>
          </div>

          <form id="new-constraint-form" onSubmit={submit} className="space-y-5" data-testid="new-constraint-form">
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Project</Label>
                <Input
                  data-testid="field-project_id"
                  value={form.project_id}
                  onChange={set("project_id")}
                  required
                  className="mt-2 h-11 border-2 border-slate-300"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Severity</Label>
                <select
                  data-testid="field-severity"
                  value={form.severity}
                  onChange={set("severity")}
                  className="mt-2 block h-11 w-full rounded-md border-2 border-slate-300 bg-white px-3 text-sm text-slate-900"
                >
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Title</Label>
              <Input
                data-testid="field-title"
                value={form.title}
                onChange={set("title")}
                placeholder="What is blocking work?"
                required
                maxLength={140}
                className="mt-2 h-11 border-2 border-slate-300"
              />
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Discipline</Label>
                <select
                  data-testid="field-discipline"
                  value={form.discipline}
                  onChange={set("discipline")}
                  className="mt-2 block h-11 w-full rounded-md border-2 border-slate-300 bg-white px-3 text-sm text-slate-900"
                >
                  {DISCIPLINES.map((d) => (<option key={d} value={d}>{d}</option>))}
                </select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Kind</Label>
                <select
                  data-testid="field-kind"
                  value={form.kind}
                  onChange={set("kind")}
                  className="mt-2 block h-11 w-full rounded-md border-2 border-slate-300 bg-white px-3 text-sm text-slate-900"
                >
                  {KINDS.map((k) => (<option key={k} value={k}>{k}</option>))}
                </select>
              </div>
            </div>

            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Responsible party (optional)</Label>
              <Input
                data-testid="field-owner"
                value={form.owner}
                onChange={set("owner")}
                placeholder="FPL · GC · Owner · sub name…"
                maxLength={200}
                className="mt-2 h-11 border-2 border-slate-300"
              />
            </div>

            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Operational impact</Label>
              <Textarea
                data-testid="field-operational_impact"
                value={form.operational_impact}
                onChange={set("operational_impact")}
                placeholder="What stops working? Crew idle? Single lane? Pause cure time?"
                rows={3}
                maxLength={500}
                className="mt-2 min-h-[96px] border-2 border-slate-300"
              />
            </div>

            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">Notes</Label>
              <Textarea
                data-testid="field-notes"
                value={form.notes}
                onChange={set("notes")}
                placeholder="Additional context"
                rows={5}
                maxLength={4000}
                className="mt-2 min-h-[140px] border-2 border-slate-300"
              />
            </div>

            {err && (
              <div data-testid="new-constraint-error" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {err}
              </div>
            )}
          </form>
        </Card>
      </div>
    </FormShell>
  );
}
