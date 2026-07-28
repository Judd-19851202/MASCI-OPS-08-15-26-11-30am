import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CalendarRange, CheckCircle2, RefreshCw } from "lucide-react";
import PmShell from "@/components/PmShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const DEFAULT_REVIEW = {
  primary_cause: "",
  contributing_causes: "",
  controllability: "",
  evidence: "",
  recovery_strategy: "",
  recovery_owner_role: "pm",
  recovery_owner_name: "",
  recovery_date: "",
  forecast_impact: "",
  critical_path_impact: "",
  executive_escalation: false,
  executive_actions: "",
  notes: "",
  link_existing_task_id: "",
};

const DEFAULT_VARIANCE_REVIEW = {
  status: "under_review",
  primary_cause: "",
  contributing_causes: "",
  controllability: "",
  cause_notes: "",
  recovery_strategy: "",
  recovery_priority: "high",
  recovery_owner_role: "pm",
  recovery_due_date: "",
  requires_executive_review: false,
  executive_notes: "",
};

function ActivityReviewCard({ activity, causes, controllability, draft, onChange, onSave, saving }) {
  const review = draft || DEFAULT_REVIEW;
  return (
    <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid={`pm-monday-review-activity-${activity.code}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-lg font-black text-slate-900">{activity.code} · {activity.item_name}</div>
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500" data-testid={`pm-monday-review-status-${activity.code}`}>{activity.status}</div>
        </div>
        <div className={`rounded-full px-3 py-1 text-xs font-bold ${activity.requires_review ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-700"}`} data-testid={`pm-monday-review-requires-${activity.code}`}>
          {activity.requires_review ? "Review required" : "No review required"}
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4 text-sm">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2" data-testid={`pm-monday-review-planned-qty-${activity.code}`}>Planned Qty: {activity.planned_quantity}</div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2" data-testid={`pm-monday-review-actual-qty-${activity.code}`}>Actual Qty: {activity.actual_quantity}</div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2" data-testid={`pm-monday-review-labor-${activity.code}`}>Labor Hrs: {activity.actual_labor_hours}</div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2" data-testid={`pm-monday-review-productivity-${activity.code}`}>Prod Eff: {activity.production_efficiency_percent}%</div>
      </div>
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600" data-testid={`pm-monday-review-timeline-${activity.code}`}>
        <div>Timeline entries: {activity.timeline?.length || 0}</div>
        {(activity.timeline || []).slice(0, 4).map((event, idx) => (
          <div key={`${activity.code}-${idx}`} className="mt-1 text-[11px] text-slate-500" data-testid={`pm-monday-review-timeline-event-${activity.code}-${idx}`}>
            {event.event_name} · {event.stage} · {event.at || "pending"}
          </div>
        ))}
      </div>
      {activity.requires_review ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="text-xs font-semibold text-slate-600">Primary cause
            <select data-testid={`pm-monday-review-primary-cause-${activity.code}`} value={review.primary_cause} onChange={(e) => onChange(activity.code, "primary_cause", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
              <option value="">Select cause</option>
              {causes.map((cause) => <option key={cause} value={cause}>{cause}</option>)}
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-600">Controllability
            <select data-testid={`pm-monday-review-controllability-${activity.code}`} value={review.controllability} onChange={(e) => onChange(activity.code, "controllability", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
              <option value="">Select controllability</option>
              {controllability.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Contributing causes (comma separated)
            <input data-testid={`pm-monday-review-contributing-causes-${activity.code}`} value={review.contributing_causes} onChange={(e) => onChange(activity.code, "contributing_causes", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Evidence
            <textarea data-testid={`pm-monday-review-evidence-${activity.code}`} value={review.evidence} onChange={(e) => onChange(activity.code, "evidence", e.target.value)} rows={2} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Recovery strategy
            <textarea data-testid={`pm-monday-review-recovery-strategy-${activity.code}`} value={review.recovery_strategy} onChange={(e) => onChange(activity.code, "recovery_strategy", e.target.value)} rows={2} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600">Recovery owner role
            <input data-testid={`pm-monday-review-recovery-owner-role-${activity.code}`} value={review.recovery_owner_role} onChange={(e) => onChange(activity.code, "recovery_owner_role", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600">Recovery date
            <input data-testid={`pm-monday-review-recovery-date-${activity.code}`} type="date" value={review.recovery_date} onChange={(e) => onChange(activity.code, "recovery_date", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Forecast impact
            <input data-testid={`pm-monday-review-forecast-impact-${activity.code}`} value={review.forecast_impact} onChange={(e) => onChange(activity.code, "forecast_impact", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Critical path impact
            <input data-testid={`pm-monday-review-critical-impact-${activity.code}`} value={review.critical_path_impact} onChange={(e) => onChange(activity.code, "critical_path_impact", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Executive actions
            <textarea data-testid={`pm-monday-review-executive-actions-${activity.code}`} value={review.executive_actions} onChange={(e) => onChange(activity.code, "executive_actions", e.target.value)} rows={2} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
          </label>
          <label className="md:col-span-2 flex items-center gap-2 text-xs font-semibold text-slate-600">
            <input data-testid={`pm-monday-review-executive-escalation-${activity.code}`} type="checkbox" checked={review.executive_escalation} onChange={(e) => onChange(activity.code, "executive_escalation", e.target.checked)} />
            Executive escalation required
          </label>
          <div className="md:col-span-2 flex justify-end">
            <Button onClick={() => onSave(activity.code)} disabled={saving} data-testid={`pm-monday-review-save-${activity.code}`}>{saving ? "Saving…" : "Save review"}</Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function PmMondayReviewWorkspace() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [weekEnding, setWeekEnding] = useState(params.get("week_ending") || "");
  const [loading, setLoading] = useState(false);
  const [workspace, setWorkspace] = useState(null);
  const [reviewDrafts, setReviewDrafts] = useState({});
  const [varianceDrafts, setVarianceDrafts] = useState({});
  const [metaDraft, setMetaDraft] = useState({ critical_path_reviewed: false, executive_actions: "", notes: "" });
  const [savingCode, setSavingCode] = useState("");
  const [savingVarianceKey, setSavingVarianceKey] = useState("");

  const load = async (pn, we = weekEnding) => {
    if (!pn) return;
    setLoading(true);
    try {
      const r = await api.get(`/oppc/projects/${encodeURIComponent(pn)}/execution-workspace`, { params: { week_ending: we || undefined } });
      setWorkspace(r.data || null);
      setMetaDraft({
        critical_path_reviewed: !!r.data?.monday_review?.workspace?.critical_path_reviewed_at,
        executive_actions: (r.data?.monday_review?.workspace?.executive_actions || []).join("\n"),
        notes: r.data?.monday_review?.workspace?.notes || "",
      });
      const nextDrafts = {};
      const nextVarianceDrafts = {};
      for (const activity of r.data?.monday_review?.activities || []) {
        const review = activity.review || {};
        nextDrafts[activity.code] = {
          ...DEFAULT_REVIEW,
          primary_cause: review.primary_cause || "",
          contributing_causes: (review.contributing_causes || []).join(", "),
          controllability: review.controllability || "",
          evidence: (review.evidence || []).join("\n"),
          recovery_strategy: review.recovery_strategy || "",
          recovery_owner_role: review.recovery_owner_role || "pm",
          recovery_owner_name: review.recovery_owner_name || "",
          recovery_date: review.recovery_date || "",
          forecast_impact: review.forecast_impact || "",
          critical_path_impact: review.critical_path_impact || "",
          executive_escalation: !!review.executive_escalation,
          executive_actions: (review.executive_actions || []).join("\n"),
          notes: review.notes || "",
          link_existing_task_id: review.recovery_task_id || "",
        };
      }
      for (const variance of r.data?.variance_intelligence?.variances || []) {
        nextVarianceDrafts[variance.variance_key] = {
          ...DEFAULT_VARIANCE_REVIEW,
          status: variance.status || "under_review",
          primary_cause: variance.primary_cause || "",
          contributing_causes: (variance.contributing_causes || []).join(", "),
          controllability: variance.controllability || "",
          cause_notes: variance.supporting_review?.notes || "",
          recovery_strategy: variance.supporting_review?.recovery_strategy || "",
          recovery_priority: variance.supporting_review?.recovery_priority || "high",
          recovery_owner_role: variance.supporting_review?.recovery_owner_role || "pm",
          recovery_due_date: variance.supporting_review?.recovery_date || "",
          requires_executive_review: !!variance.requires_executive_review,
          executive_notes: (variance.supporting_review?.executive_actions || []).join("\n"),
        };
      }
      setReviewDrafts(nextDrafts);
      setVarianceDrafts(nextVarianceDrafts);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load the Monday review workspace.");
      setWorkspace(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setProjectNumber(params.get("project_number") || "");
    setWeekEnding(params.get("week_ending") || "");
  }, [params]);

  useEffect(() => { if (projectNumber) load(projectNumber, weekEnding); }, [projectNumber, weekEnding]);

  const updateSearch = (nextProject, nextWeek) => {
    const next = new URLSearchParams(params);
    if (nextProject) next.set("project_number", nextProject); else next.delete("project_number");
    if (nextWeek) next.set("week_ending", nextWeek); else next.delete("week_ending");
    setParams(next, { replace: true });
  };

  const startReview = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.post(`/oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/start`, { week_ending: weekEnding || undefined });
      setWorkspace(r.data || null);
      toast.success("Monday review started.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start Monday review.");
    }
  };

  const saveMeta = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.put(`/oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/meta`, {
        week_ending: weekEnding || undefined,
        critical_path_reviewed: metaDraft.critical_path_reviewed,
        executive_actions: metaDraft.executive_actions.split("\n").map((x) => x.trim()).filter(Boolean),
        notes: metaDraft.notes,
      });
      setWorkspace(r.data || null);
      toast.success("Monday review metadata updated.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not update Monday review metadata.");
    }
  };

  const saveActivity = async (code) => {
    if (!projectNumber) return;
    const draft = reviewDrafts[code] || DEFAULT_REVIEW;
    setSavingCode(code);
    try {
      const r = await api.put(`/oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/activities/${encodeURIComponent(code)}`, {
        week_ending: weekEnding || undefined,
        primary_cause: draft.primary_cause,
        contributing_causes: draft.contributing_causes.split(",").map((x) => x.trim()).filter(Boolean),
        controllability: draft.controllability,
        evidence: draft.evidence.split("\n").map((x) => x.trim()).filter(Boolean),
        recovery_strategy: draft.recovery_strategy,
        recovery_owner_role: draft.recovery_owner_role,
        recovery_owner_name: draft.recovery_owner_name,
        recovery_date: draft.recovery_date,
        forecast_impact: draft.forecast_impact,
        critical_path_impact: draft.critical_path_impact,
        executive_escalation: draft.executive_escalation,
        executive_actions: draft.executive_actions.split("\n").map((x) => x.trim()).filter(Boolean),
        notes: draft.notes,
        link_existing_task_id: draft.link_existing_task_id,
      });
      setWorkspace(r.data || null);
      toast.success(`${code} review saved.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Could not save ${code} review.`);
    } finally {
      setSavingCode("");
    }
  };

  const completeReview = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.post(`/oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/complete`, { week_ending: weekEnding || undefined });
      setWorkspace(r.data || null);
      toast.success("Monday review completed.");
    } catch (e) {
      toast.error(e?.response?.data?.detail?.code || e?.response?.data?.detail || "Monday review is not ready yet.");
    }
  };

  const saveVariance = async (varianceKey) => {
    if (!projectNumber) return;
    const draft = varianceDrafts[varianceKey] || DEFAULT_VARIANCE_REVIEW;
    setSavingVarianceKey(varianceKey);
    try {
      await api.put(`/oppc/projects/${encodeURIComponent(projectNumber)}/variances/${encodeURIComponent(varianceKey)}`, {
        status: draft.status,
        primary_cause: draft.primary_cause,
        contributing_causes: draft.contributing_causes.split(",").map((x) => x.trim()).filter(Boolean),
        controllability: draft.controllability,
        cause_notes: draft.cause_notes,
        recovery_strategy: draft.recovery_strategy,
        recovery_priority: draft.recovery_priority,
        recovery_owner_role: draft.recovery_owner_role,
        recovery_due_date: draft.recovery_due_date,
        requires_executive_review: draft.requires_executive_review,
        executive_notes: draft.executive_notes.split("\n").map((x) => x.trim()).filter(Boolean),
        recovery_plan: { planning_cycle: workspace?.review_week?.week_ending, strategy: draft.recovery_strategy },
      });
      toast.success("Variance review saved.");
      await load(projectNumber, weekEnding);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save variance review.");
    } finally {
      setSavingVarianceKey("");
    }
  };

  const activities = workspace?.monday_review?.activities || [];
  const health = workspace?.project_health || {};
  const readiness = workspace?.monday_review || {};
  const causes = workspace?.root_cause_types || [];
  const controllability = workspace?.controllability_options || [];
  const canComplete = !!workspace?.monday_review?.ready;
  const varianceItems = workspace?.variance_intelligence?.variances || [];

  const summaryCards = useMemo(() => ([
    { key: "health", label: "Project Health", value: health.status || "—" },
    { key: "production", label: "Actual Qty", value: workspace?.production_summary?.actual_quantity ?? "—" },
    { key: "payroll", label: "Payroll Status", value: workspace?.payroll_summary?.lifecycle_state || "—" },
    { key: "readiness", label: "Monday Readiness", value: `${readiness.completion_percent || 0}%` },
  ]), [health, workspace, readiness]);

  return (
    <PmShell title="Monday Review Workspace" section="jobs" intro={<p className="text-xs text-slate-500">Canonical plan vs actual vs payroll workflow. No duplicate engines.</p>}>
      <div className="space-y-4" data-testid="pm-monday-review-page">
        <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-sm font-black text-slate-900"><CalendarRange className="h-4 w-4" /> Monday Look-Behind</div>
              <div className="text-xs text-slate-500">Integrated PM workflow for production, payroll, variance, recovery, forecast, and readiness.</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <PmProjectSelector value={projectNumber} onChange={(pn) => updateSearch(pn, weekEnding)} />
              <input data-testid="pm-monday-review-week-ending" type="date" value={weekEnding} onChange={(e) => updateSearch(projectNumber, e.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
              <Button variant="outline" onClick={() => load(projectNumber, weekEnding)} data-testid="pm-monday-review-refresh"><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button>
              <Button variant="outline" onClick={startReview} disabled={!projectNumber} data-testid="pm-monday-review-start">Start Review</Button>
              <Button onClick={completeReview} disabled={!projectNumber || !canComplete} data-testid="pm-monday-review-complete"><CheckCircle2 className="mr-2 h-4 w-4" />Complete Review</Button>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            {summaryCards.map((card) => (
              <div key={card.key} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3" data-testid={`pm-monday-review-card-${card.key}`}>
                <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500">{card.label}</div>
                <div className="text-lg font-black text-slate-900">{card.value}</div>
              </div>
            ))}
          </div>
        </div>

        {workspace ? (
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-4">
              <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid="pm-monday-review-readiness-panel">
                <div className="text-sm font-black text-slate-900">Readiness</div>
                <div className="mt-3 text-sm text-slate-700" data-testid="pm-monday-review-ready-flag">{workspace.monday_review.ready ? "Ready" : "Not ready"}</div>
                <div className="mt-3 text-xs text-slate-500" data-testid="pm-monday-review-blocking-items">Blocking items: {(workspace.monday_review.blocking_items || []).join(", ") || "None"}</div>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-600">
                    <input data-testid="pm-monday-review-critical-path-reviewed" type="checkbox" checked={metaDraft.critical_path_reviewed} onChange={(e) => setMetaDraft((prev) => ({ ...prev, critical_path_reviewed: e.target.checked }))} />
                    Critical path reviewed
                  </label>
                  <div className="text-xs text-slate-500" data-testid="pm-monday-review-open-variances">Open variances: {workspace.monday_review.open_variances}</div>
                  <label className="md:col-span-2 text-xs font-semibold text-slate-600">Executive actions
                    <textarea data-testid="pm-monday-review-meta-executive-actions" value={metaDraft.executive_actions} onChange={(e) => setMetaDraft((prev) => ({ ...prev, executive_actions: e.target.value }))} rows={3} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                  </label>
                  <label className="md:col-span-2 text-xs font-semibold text-slate-600">Notes
                    <textarea data-testid="pm-monday-review-meta-notes" value={metaDraft.notes} onChange={(e) => setMetaDraft((prev) => ({ ...prev, notes: e.target.value }))} rows={2} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                  </label>
                </div>
                <div className="mt-4 flex justify-end"><Button variant="outline" onClick={saveMeta} data-testid="pm-monday-review-save-meta">Save readiness context</Button></div>
              </div>

              <div className="space-y-4" data-testid="pm-monday-review-activities-list">
                {activities.map((activity) => (
                  <ActivityReviewCard
                    key={activity.code}
                    activity={activity}
                    causes={causes}
                    controllability={controllability}
                    draft={reviewDrafts[activity.code]}
                    onChange={(code, field, value) => setReviewDrafts((prev) => ({ ...prev, [code]: { ...(prev[code] || DEFAULT_REVIEW), [field]: value } }))}
                    onSave={saveActivity}
                    saving={savingCode === activity.code}
                  />
                ))}
              </div>

              <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid="pm-monday-review-variance-panel">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-black text-slate-900">Canonical Variance Intelligence</div>
                    <div className="text-xs text-slate-500">One reusable variance engine across production, labor, schedule, and recovery.</div>
                  </div>
                  <div className="text-xs text-slate-500" data-testid="pm-monday-review-variance-count">{varianceItems.length} tracked variances</div>
                </div>
                <div className="mt-4 space-y-3">
                  {varianceItems.slice(0, 8).map((variance) => {
                    const draft = varianceDrafts[variance.variance_key] || DEFAULT_VARIANCE_REVIEW;
                    const suffix = `${variance.activity}-${variance.variance_type}`;
                    return (
                      <div key={variance.variance_key} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4" data-testid={`pm-monday-review-variance-${suffix}`}>
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-black text-slate-900">{variance.activity} · {variance.variance_type}</div>
                            <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{variance.severity} · {variance.status}</div>
                          </div>
                          <div className="text-right text-xs text-slate-500">
                            <div data-testid={`pm-monday-review-variance-percent-${suffix}`}>{variance.variance_percent}%</div>
                            <div>{variance.primary_cause || "unknown"}</div>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 md:grid-cols-2">
                          <label className="text-xs font-semibold text-slate-600">Status
                            <select data-testid={`pm-monday-review-variance-status-${suffix}`} value={draft.status} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), status: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
                              {(workspace?.variance_intelligence?.taxonomy?.statuses || []).map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Primary cause
                            <select data-testid={`pm-monday-review-variance-primary-${suffix}`} value={draft.primary_cause} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), primary_cause: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
                              <option value="">Select cause</option>
                              {(workspace?.variance_intelligence?.taxonomy?.root_causes || []).map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                          </label>
                          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Contributing causes
                            <input data-testid={`pm-monday-review-variance-contributing-${suffix}`} value={draft.contributing_causes} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), contributing_causes: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Controllability
                            <select data-testid={`pm-monday-review-variance-controllability-${suffix}`} value={draft.controllability} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), controllability: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
                              <option value="">Select</option>
                              {(workspace?.variance_intelligence?.taxonomy?.controllability || []).map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Recovery strategy
                            <select data-testid={`pm-monday-review-variance-strategy-${suffix}`} value={draft.recovery_strategy} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), recovery_strategy: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
                              <option value="">Select strategy</option>
                              {[
                                "crew_increase","equipment_increase","equipment_substitution","weekend_work","night_work","additional_shift","sequence_revision","material_acceleration","supplier_change","survey_acceleration","inspection_acceleration","qa_acceleration","subcontract_supplementation","owner_decision","engineer_decision","approved_extension","approved_deferment","custom"
                              ].map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Recovery due date
                            <input data-testid={`pm-monday-review-variance-due-${suffix}`} type="date" value={draft.recovery_due_date} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), recovery_due_date: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Recovery priority
                            <select data-testid={`pm-monday-review-variance-priority-${suffix}`} value={draft.recovery_priority} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), recovery_priority: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
                              {["low","medium","high","critical"].map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                          </label>
                          <label className="text-xs font-semibold text-slate-600">Recovery owner role
                            <input data-testid={`pm-monday-review-variance-owner-role-${suffix}`} value={draft.recovery_owner_role} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), recovery_owner_role: e.target.value } }))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                          </label>
                          <label className="md:col-span-2 text-xs font-semibold text-slate-600">Cause / action notes
                            <textarea data-testid={`pm-monday-review-variance-notes-${suffix}`} value={draft.cause_notes} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), cause_notes: e.target.value } }))} rows={2} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" />
                          </label>
                          <label className="md:col-span-2 flex items-center gap-2 text-xs font-semibold text-slate-600">
                            <input data-testid={`pm-monday-review-variance-executive-${suffix}`} type="checkbox" checked={draft.requires_executive_review} onChange={(e) => setVarianceDrafts((prev) => ({ ...prev, [variance.variance_key]: { ...(prev[variance.variance_key] || DEFAULT_VARIANCE_REVIEW), requires_executive_review: e.target.checked } }))} />
                            Requires executive review
                          </label>
                          <div className="md:col-span-2 flex justify-end">
                            <Button onClick={() => saveVariance(variance.variance_key)} disabled={savingVarianceKey === variance.variance_key} data-testid={`pm-monday-review-variance-save-${suffix}`}>{savingVarianceKey === variance.variance_key ? "Saving…" : "Save variance"}</Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid="pm-monday-review-production-panel">
                <div className="text-sm font-black text-slate-900">Daily Production</div>
                <div className="mt-3 grid gap-3 md:grid-cols-2 text-sm">
                  <div data-testid="pm-monday-review-production-planned">Planned Qty: {workspace.production_summary.planned_quantity}</div>
                  <div data-testid="pm-monday-review-production-actual">Actual Qty: {workspace.production_summary.actual_quantity}</div>
                  <div data-testid="pm-monday-review-production-reports">Reports: {workspace.production_summary.report_count}</div>
                  <div data-testid="pm-monday-review-production-latest">Latest DR: {workspace.production_summary.latest_report_date || "—"}</div>
                  <div data-testid="pm-monday-review-production-open-variances">Open Variances: {workspace.monday_review.open_variances}</div>
                  <div data-testid="pm-monday-review-production-outstanding-recovery">Outstanding Recovery: {workspace.monday_review.outstanding_recovery}</div>
                </div>
              </div>

              <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid="pm-monday-review-payroll-panel">
                <div className="text-sm font-black text-slate-900">Payroll Reconciliation</div>
                <div className="mt-3 space-y-2 text-sm">
                  <div data-testid="pm-monday-review-payroll-status">Lifecycle: {workspace.payroll_summary.lifecycle_state}</div>
                  <div data-testid="pm-monday-review-payroll-field-hours">Field hours: {workspace.payroll_summary.field_labor_hours}</div>
                  <div data-testid="pm-monday-review-payroll-payroll-hours">Payroll hours: {workspace.payroll_summary.payroll_labor_hours}</div>
                  <div data-testid="pm-monday-review-payroll-difference">Difference: {workspace.payroll_summary.labor_difference_hours}</div>
                </div>
              </div>

              <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-sm" data-testid="pm-monday-review-links-panel">
                <div className="text-sm font-black text-slate-900">Related workflows</div>
                <div className="mt-3 flex flex-col gap-2 text-sm">
                  <Link to={`/pm/project-schedule?project_number=${encodeURIComponent(projectNumber || "")}`} className="text-amber-700 hover:underline" data-testid="pm-monday-review-link-schedule">Open Project Schedule</Link>
                </div>
              </div>
            </div>
          </div>
        ) : loading ? (
          <div className="rounded-[2rem] border border-white/40 bg-white/80 p-6 text-sm text-slate-500" data-testid="pm-monday-review-loading">Loading Monday review workspace…</div>
        ) : (
          <div className="rounded-[2rem] border border-white/40 bg-white/80 p-6 text-sm text-slate-500" data-testid="pm-monday-review-empty">Choose a PM project to open the operational execution workspace.</div>
        )}
      </div>
    </PmShell>
  );
}