import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CalendarClock, GitBranch, RefreshCw, ShieldCheck, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/lib/i18n";

const STATUS_TONE = {
  ready: "bg-emerald-50 text-emerald-700 border-emerald-200",
  complete: "bg-emerald-50 text-emerald-700 border-emerald-200",
  insufficient_evidence: "bg-amber-50 text-amber-700 border-amber-200",
  review_required: "bg-amber-50 text-amber-700 border-amber-200",
  committed: "bg-blue-50 text-blue-700 border-blue-200",
  proposed: "bg-slate-100 text-slate-700 border-slate-200",
  at_risk: "bg-orange-50 text-orange-700 border-orange-200",
  missed: "bg-red-50 text-red-700 border-red-200",
  met: "bg-emerald-50 text-emerald-700 border-emerald-200",
  revised: "bg-violet-50 text-violet-700 border-violet-200",
  cancelled: "bg-slate-100 text-slate-600 border-slate-200",
};

function badgeTone(status) {
  return STATUS_TONE[status] || "bg-slate-100 text-slate-700 border-slate-200";
}

function fmtNumber(value, digits = 2) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString(undefined, { maximumFractionDigits: digits }) : "—";
}

function fmtMoney(value) {
  return Number.isFinite(Number(value)) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "—";
}

function SummaryCard({ icon: Icon, label, value, note, status, testId }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</div>
            <div className="mt-3 text-3xl font-semibold text-slate-900">{value}</div>
            <div className="mt-2 text-sm text-slate-600">{note}</div>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-slate-700">
            <Icon className="h-5 w-5" />
          </div>
        </div>
        {status ? <Badge className={`mt-4 border ${badgeTone(status)}`}>{String(status).replaceAll("_", " ")}</Badge> : null}
      </CardContent>
    </Card>
  );
}

function TableCard({ title, rows, columns, testId, emptyLabel = "No rows yet." }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardHeader>
        <CardTitle className="text-lg text-slate-900">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {rows?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.18em] text-slate-500">
                  {columns.map((column) => <th key={column.key} className="px-3 py-2">{column.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id || row.unit || row.commitment_id || index} className="border-b border-slate-100 align-top" data-testid={`${testId}-row-${index}`}>
                    {columns.map((column) => <td key={column.key} className="px-3 py-3 text-slate-700">{column.render ? column.render(row, index) : (row[column.key] ?? "—")}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-sm text-slate-500">{emptyLabel}</div>
        )}
      </CardContent>
    </Card>
  );
}

function DriverList({ drivers }) {
  const items = Array.isArray(drivers) ? drivers : [];
  return (
    <Card className="border-slate-200 shadow-sm" data-testid="forecast-driver-list">
      <CardHeader>
        <CardTitle className="text-lg text-slate-900">Forecast drivers</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? <div className="text-sm text-slate-500">No governed drivers were preserved in this snapshot.</div> : null}
        {items.map((driver, index) => (
          <div key={driver.driver_id || index} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4" data-testid={`forecast-driver-${index}`}>
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-sm font-semibold text-slate-900">{driver.label || "Forecast driver"}</div>
              <Badge className={`border ${badgeTone(driver.family === "constraint" ? "at_risk" : "ready")}`}>{driver.family || "driver"}</Badge>
            </div>
            <div className="mt-2 text-sm text-slate-700">{driver.reason || "Evidence-backed driver preserved."}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function CommitmentForm({ canEdit, onCreate }) {
  const { t } = useT();
  const [form, setForm] = useState({
    family: "milestone_quantity",
    status: "proposed",
    title: "",
    description: "",
    due_date: "",
    linked_unit: "",
    linked_activity_id: "",
    linked_work_package_id: "",
    target_quantity: "",
    target_hours: "",
    target_amount: "",
    target_count: "",
    confidence: "medium",
    evidence_note: "",
    note: "",
  });
  const [saving, setSaving] = useState(false);

  if (!canEdit) return null;

  const submit = async () => {
    if (!form.title.trim()) {
      toast.error(t("Commitment title is required."));
      return;
    }
    setSaving(true);
    try {
      await onCreate?.({
        ...form,
        target_quantity: Number(form.target_quantity || 0),
        target_hours: Number(form.target_hours || 0),
        target_amount: Number(form.target_amount || 0),
        target_count: Number(form.target_count || 0),
      });
      setForm({
        family: "milestone_quantity",
        status: "proposed",
        title: "",
        description: "",
        due_date: "",
        linked_unit: "",
        linked_activity_id: "",
        linked_work_package_id: "",
        target_quantity: "",
        target_hours: "",
        target_amount: "",
        target_count: "",
        confidence: "medium",
        evidence_note: "",
        note: "",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="border-slate-200 shadow-sm" data-testid="forecast-commitment-form-card">
      <CardHeader>
        <CardTitle className="text-lg text-slate-900">Operator commitment</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-family">Family</label>
            <select id="commitment-family" className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" value={form.family} onChange={(e) => setForm((prev) => ({ ...prev, family: e.target.value }))} data-testid="forecast-commitment-family-input">
              <option value="milestone_quantity">Milestone / quantity</option>
              <option value="labor_crew">Labor / crew</option>
              <option value="equipment">Equipment</option>
              <option value="materials">Materials</option>
              <option value="vendor_subcontractor">Vendor / subcontractor</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-status">Lifecycle</label>
            <select id="commitment-status" className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" value={form.status} onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))} data-testid="forecast-commitment-status-input">
              <option value="proposed">Proposed</option>
              <option value="committed">Committed</option>
              <option value="at_risk">At risk</option>
              <option value="missed">Missed</option>
              <option value="met">Met</option>
              <option value="revised">Revised</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-due-date">Due date</label>
            <Input id="commitment-due-date" type="date" value={form.due_date} onChange={(e) => setForm((prev) => ({ ...prev, due_date: e.target.value }))} data-testid="forecast-commitment-due-date-input" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-confidence">Confidence</label>
            <select id="commitment-confidence" className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm" value={form.confidence} onChange={(e) => setForm((prev) => ({ ...prev, confidence: e.target.value }))} data-testid="forecast-commitment-confidence-input">
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="review_required">Review required</option>
            </select>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-title">Title</label>
            <Input id="commitment-title" value={form.title} onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))} data-testid="forecast-commitment-title-input" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-linked-unit">Linked unit</label>
            <Input id="commitment-linked-unit" value={form.linked_unit} onChange={(e) => setForm((prev) => ({ ...prev, linked_unit: e.target.value }))} placeholder="LF, CY, EA…" data-testid="forecast-commitment-linked-unit-input" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-target-quantity">Target quantity</label>
            <Input id="commitment-target-quantity" type="number" value={form.target_quantity} onChange={(e) => setForm((prev) => ({ ...prev, target_quantity: e.target.value }))} data-testid="forecast-commitment-target-quantity-input" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-target-hours">Target hours</label>
            <Input id="commitment-target-hours" type="number" value={form.target_hours} onChange={(e) => setForm((prev) => ({ ...prev, target_hours: e.target.value }))} data-testid="forecast-commitment-target-hours-input" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-target-amount">Target amount</label>
            <Input id="commitment-target-amount" type="number" value={form.target_amount} onChange={(e) => setForm((prev) => ({ ...prev, target_amount: e.target.value }))} data-testid="forecast-commitment-target-amount-input" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-description">Description</label>
            <Textarea id="commitment-description" value={form.description} onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))} data-testid="forecast-commitment-description-input" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="commitment-evidence">Evidence note</label>
            <Textarea id="commitment-evidence" value={form.evidence_note} onChange={(e) => setForm((prev) => ({ ...prev, evidence_note: e.target.value }))} data-testid="forecast-commitment-evidence-note-input" />
          </div>
        </div>
        <Button onClick={submit} disabled={saving} data-testid="forecast-commitment-save-button">{saving ? "Saving…" : "Save commitment"}</Button>
      </CardContent>
    </Card>
  );
}

export default function ForecastingCommitmentsWorkspace({ mode = "pm", projectNumber, selector, workspace, loading, working, onRefresh, onCaptureSnapshot, canEditCommitments = false, onCreateCommitment, onUpdateCommitment }) {
  const schedule = workspace?.schedule || {};
  const production = workspace?.production || {};
  const resources = workspace?.resources || {};
  const cost = workspace?.cost || {};
  const commitments = workspace?.commitments || {};
  const versions = workspace?.versioning?.recent_versions || [];
  const [drafts, setDrafts] = useState({});
  const [snapshotNote, setSnapshotNote] = useState("");

  const summaryCards = useMemo(() => ([
    { icon: CalendarClock, label: "Likely finish", value: schedule?.summary?.likely_finish_date || "Insufficient evidence", note: `Committed finish: ${schedule?.summary?.committed_finish_date || "—"}`, status: schedule?.status, testId: "forecast-summary-likely-finish" },
    { icon: TrendingUp, label: "Next 7 days", value: fmtNumber(production?.summary?.forecast_next_week_total, 2), note: `Required weekly pace: ${fmtNumber(production?.summary?.required_weekly_total, 2)}`, status: production?.status, testId: "forecast-summary-next-week" },
    { icon: AlertTriangle, label: "At-risk commitments", value: commitments?.lifecycle_counts?.at_risk ?? 0, note: `Missed: ${commitments?.lifecycle_counts?.missed ?? 0}`, status: commitments?.status, testId: "forecast-summary-at-risk-commitments" },
    { icon: ShieldCheck, label: mode === "field" ? "Open constraints" : "Projected remaining cost", value: mode === "field" ? (workspace?.constraints?.open_count ?? 0) : fmtMoney(cost?.summary?.projected_remaining_cost), note: mode === "field" ? "Constraint pressure carried into the field view." : `Commitment exposure: ${fmtMoney(cost?.summary?.commitment_exposure)}`, status: mode === "field" ? workspace?.constraints?.status : cost?.status, testId: "forecast-summary-constraints-or-cost" },
  ]), [commitments?.lifecycle_counts?.at_risk, commitments?.lifecycle_counts?.missed, commitments?.status, cost?.status, cost?.summary?.commitment_exposure, cost?.summary?.projected_remaining_cost, mode, production?.status, production?.summary?.forecast_next_week_total, production?.summary?.required_weekly_total, schedule?.status, schedule?.summary?.committed_finish_date, schedule?.summary?.likely_finish_date, workspace?.constraints?.open_count, workspace?.constraints?.status]);

  const setDraft = (commitmentId, key, value) => {
    setDrafts((prev) => ({
      ...prev,
      [commitmentId]: {
        status: key === "status" ? value : prev[commitmentId]?.status || "",
        note: key === "note" ? value : prev[commitmentId]?.note || "",
      },
    }));
  };

  const saveCommitment = async (row) => {
    const draft = drafts[row.commitment_id] || {};
    await onUpdateCommitment?.(row, draft);
  };

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 pb-10" data-testid={`forecasting-workspace-${mode}`}>
      <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(15,118,110,0.12),_transparent_38%),linear-gradient(135deg,#f8fafc_0%,#ffffff_58%,#eef2ff_100%)] p-6 shadow-sm sm:p-8" data-testid="forecasting-hero-panel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">WP-18C7 · Forecasting & Commitments</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">Evidence-backed forecast authority</h1>
            <p className="mt-4 max-w-2xl text-sm text-slate-600 sm:text-base" data-testid="forecasting-hero-description">One governed workspace for likely finish, pace, commitments, and explainable risk. Forecasts stay distinct from commitments and every visible number ties back to preserved operational evidence.</p>
          </div>
          <div className="flex w-full flex-col gap-3 lg:w-auto lg:min-w-[320px]">
            <div data-testid="forecasting-project-selector-wrap">{selector}</div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onRefresh} disabled={!projectNumber || loading || working} data-testid="forecasting-refresh-button"><RefreshCw className="mr-2 h-4 w-4" /> Refresh</Button>
              {mode !== "field" ? <Button variant="outline" onClick={() => onCaptureSnapshot?.(snapshotNote)} disabled={!projectNumber || loading || working} data-testid="forecasting-capture-snapshot-button"><GitBranch className="mr-2 h-4 w-4" /> Capture version</Button> : null}
            </div>
            {mode !== "field" ? <Input placeholder="Version note (optional)" value={snapshotNote} onChange={(e) => setSnapshotNote(e.target.value)} data-testid="forecasting-snapshot-note-input" /> : null}
          </div>
        </div>
      </div>

      {loading ? <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="forecasting-loading-state">Loading governed forecast workspace…</CardContent></Card> : null}
      {!loading && !projectNumber ? <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="forecasting-empty-project-state">Select a project to load the C7 forecast workspace.</CardContent></Card> : null}

      {!loading && projectNumber && workspace ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{summaryCards.map((card) => <SummaryCard key={card.testId} {...card} />)}</div>

          <Tabs defaultValue="forecasting" className="space-y-5" data-testid="forecasting-tabs-root">
            <TabsList className="flex w-full flex-wrap justify-start gap-2 rounded-2xl bg-slate-100 p-1" data-testid="forecasting-tabs-list">
              <TabsTrigger value="forecasting" data-testid="forecasting-tab-trigger">Forecasting</TabsTrigger>
              <TabsTrigger value="commitments" data-testid="commitments-tab-trigger">Commitments</TabsTrigger>
              <TabsTrigger value="governance" data-testid="governance-tab-trigger">Governance</TabsTrigger>
            </TabsList>

            <TabsContent value="forecasting" className="space-y-5" data-testid="forecasting-tab-panel">
              <div className="grid gap-5 xl:grid-cols-[1.3fr_0.9fr]">
                <TableCard title="Production forecast by unit" rows={production?.unit_rows || []} testId="forecast-production-table" columns={[{ key: "unit", label: "Unit" }, { key: "remaining_quantity", label: "Remaining", render: (row) => fmtNumber(row.remaining_quantity, 2) }, { key: "next_week_quantity", label: "Next 7d", render: (row) => fmtNumber(row.next_week_quantity, 2) }, { key: "required_pace_per_week", label: "Required pace", render: (row) => fmtNumber(row.required_pace_per_week, 2) }, { key: "confidence", label: "Confidence", render: (row) => <Badge className={`border ${badgeTone(row.confidence)}`}>{row.confidence}</Badge> }]} />
                <DriverList drivers={workspace?.drivers || []} />
              </div>
              <TableCard title="Schedule pressure" rows={(schedule?.top_slipped_tasks || []).map((row) => ({ id: row.task_id || row.code, name: row.name || row.activity_name || row.code, slip_days: row.slip_days, forecast_finish_date: row.forecast_finish_date, explanation: row.explanation || row.reason || "Governed schedule engine output" }))} testId="forecast-schedule-pressure-table" columns={[{ key: "name", label: "Activity" }, { key: "slip_days", label: "Slip days" }, { key: "forecast_finish_date", label: "Forecast finish" }, { key: "explanation", label: "Explainability" }]} emptyLabel="No slipped schedule activities are currently preserved." />
              <div className={`grid gap-5 ${mode === "field" ? "xl:grid-cols-1" : "xl:grid-cols-2"}`}>
                <TableCard title="Resource outlook" rows={mode === "field" ? [ ...(resources?.crews || []), ...(resources?.materials || []) ] : [ ...(resources?.crews || []), ...(resources?.equipment || []), ...(resources?.vendors || []) ]} testId="forecast-resource-table" columns={[{ key: "label", label: "Resource" }, { key: "unit", label: "Unit" }, { key: "likely_next_week_capacity", label: "Next 7d capacity", render: (row) => fmtNumber(row.likely_next_week_capacity, 2) }, { key: "required_weekly_support", label: "Required support", render: (row) => fmtNumber(row.required_weekly_support, 2) }, { key: "confidence", label: "Confidence", render: (row) => <Badge className={`border ${badgeTone(row.confidence)}`}>{row.confidence}</Badge> }]} />
                {mode !== "field" ? <TableCard title="Authorized cost forecast" rows={cost?.unit_rows || []} testId="forecast-cost-table" columns={[{ key: "unit", label: "Unit" }, { key: "remaining_quantity", label: "Remaining qty", render: (row) => fmtNumber(row.remaining_quantity, 2) }, { key: "budget_cost_per_unit", label: "Budget / unit", render: (row) => fmtMoney(row.budget_cost_per_unit) }, { key: "projected_remaining_cost", label: "Projected remaining", render: (row) => fmtMoney(row.projected_remaining_cost) }]} /> : null}
              </div>
            </TabsContent>

            <TabsContent value="commitments" className="space-y-5" data-testid="commitments-tab-panel">
              <CommitmentForm canEdit={canEditCommitments} onCreate={onCreateCommitment} />
              <TableCard title="Commitment register" rows={commitments?.items || []} testId="forecast-commitment-table" columns={[{ key: "title", label: "Commitment" }, { key: "family", label: "Family" }, { key: "due_date", label: "Due" }, { key: "derived_status", label: "Status", render: (row) => <Badge className={`border ${badgeTone(row.derived_status || row.status)}`}>{String(row.derived_status || row.status || "proposed").replaceAll("_", " ")}</Badge> }, { key: "target_amount", label: "Target", render: (row) => row.target_amount ? fmtMoney(row.target_amount) : row.target_quantity ? fmtNumber(row.target_quantity, 2) : row.target_hours ? `${fmtNumber(row.target_hours, 2)} hrs` : "—" }, { key: "actual_amount", label: "Actual", render: (row) => row.actual_amount ? fmtMoney(row.actual_amount) : row.actual_quantity ? fmtNumber(row.actual_quantity, 2) : row.actual_hours ? `${fmtNumber(row.actual_hours, 2)} hrs` : "—" }, { key: "actions", label: "Actions", render: (row, index) => row.editable && canEditCommitments ? <div className="flex min-w-[220px] flex-col gap-2" data-testid={`forecast-commitment-actions-${index}`}><select className="h-9 rounded-xl border border-slate-300 bg-white px-3 text-sm" value={drafts[row.commitment_id]?.status || row.status || "proposed"} onChange={(e) => setDraft(row.commitment_id, "status", e.target.value)} data-testid={`forecast-commitment-status-select-${index}`}><option value="proposed">Proposed</option><option value="committed">Committed</option><option value="at_risk">At risk</option><option value="missed">Missed</option><option value="met">Met</option><option value="revised">Revised</option><option value="cancelled">Cancelled</option></select><Input value={drafts[row.commitment_id]?.note || ""} onChange={(e) => setDraft(row.commitment_id, "note", e.target.value)} placeholder="Update note" data-testid={`forecast-commitment-note-input-${index}`} /><Button size="sm" onClick={() => saveCommitment(row)} data-testid={`forecast-commitment-update-button-${index}`}>Update</Button></div> : <div className="space-y-1 text-xs text-slate-500" data-testid={`forecast-commitment-readonly-${index}`}><div>{row.source === "po_candidate" ? "PO-preserved commitment" : "Read only"}</div>{Array.isArray(row.drivers) && row.drivers[0] ? <div>{row.drivers[0]}</div> : null}</div> }]} emptyLabel="No commitments have been captured for this project yet." />
            </TabsContent>

            <TabsContent value="governance" className="space-y-5" data-testid="governance-tab-panel">
              <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
                <TableCard title="Recent forecast versions" rows={versions} testId="forecast-version-table" columns={[{ key: "version_number", label: "Version" }, { key: "generated_at", label: "Generated" }, { key: "note", label: "Note" }, { key: "change_detection", label: "Change", render: (row) => row.change_detection?.summary?.[0] || "No material change" }]} emptyLabel="No forecast versions have been preserved yet." />
                <TableCard title="Constraint effects" rows={workspace?.constraints?.forecast_effects || []} testId="forecast-constraint-table" columns={[{ key: "title", label: "Constraint" }, { key: "status", label: "Status" }, { key: "impact", label: "Impact" }, { key: "reason", label: "Reason" }]} emptyLabel="No open constraints are currently preserved." />
              </div>
              <div className="grid gap-5 xl:grid-cols-2">
                <TableCard title="Forecast vs actual" rows={workspace?.forecast_vs_actual?.unit_rows || []} testId="forecast-vs-actual-table" columns={[{ key: "unit", label: "Unit" }, { key: "accepted_quantity", label: "Accepted", render: (row) => fmtNumber(row.accepted_quantity, 2) }, { key: "remaining_quantity", label: "Remaining", render: (row) => fmtNumber(row.remaining_quantity, 2) }, { key: "variance_reason", label: "Variance" }]} />
                <Card className="border-slate-200 shadow-sm" data-testid="forecast-governance-card"><CardHeader><CardTitle className="text-lg text-slate-900">Truth & governance</CardTitle></CardHeader><CardContent className="space-y-4 text-sm text-slate-700"><div data-testid="forecast-governance-authority">Schedule forecast authority: <span className="font-semibold">{workspace?.authority_boundaries?.schedule_forecast_authority || "—"}</span></div><div data-testid="forecast-governance-production-authority">Production authority: <span className="font-semibold">{workspace?.authority_boundaries?.production_authority || "—"}</span></div><div data-testid="forecast-governance-manual-commitment-authority">Manual commitment authority: <span className="font-semibold">{workspace?.authority_boundaries?.manual_commitment_authority || "—"}</span></div><div data-testid="forecast-governance-confidence">Overall confidence: <Badge className={`border ${badgeTone(workspace?.confidence?.overall)}`}>{workspace?.confidence?.overall || "review_required"}</Badge></div><div data-testid="forecast-governance-lineage">Lineage confidence: <Badge className={`border ${badgeTone(workspace?.confidence?.lineage_confidence)}`}>{workspace?.confidence?.lineage_confidence || "review_required"}</Badge></div><div className="flex flex-wrap gap-3 pt-2"><Link to={`/pm/project-controls/schedule?project_number=${encodeURIComponent(projectNumber || "")}`} className="text-sm font-semibold text-teal-700 underline-offset-4 hover:underline" data-testid="forecast-governance-schedule-link">Open project schedule</Link>{mode !== "field" ? <Link to={`/pm/operational-intelligence?project_number=${encodeURIComponent(projectNumber || "")}`} className="text-sm font-semibold text-teal-700 underline-offset-4 hover:underline" data-testid="forecast-governance-ops-link">Open project performance</Link> : null}</div><div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600" data-testid="forecast-governance-note">Forecasts never auto-create commitments. Confidence bands widen when upstream evidence is sparse, lineage is incomplete, or constraints remain unresolved.</div></CardContent></Card>
              </div>
            </TabsContent>
          </Tabs>
        </>
      ) : null}
    </div>
  );
}
