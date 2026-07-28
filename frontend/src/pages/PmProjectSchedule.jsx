import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CalendarRange, Download, Save, RefreshCw, AlertTriangle } from "lucide-react";
import PmShell from "@/components/PmShell";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";

const toInput = (v) => String(v || "").slice(0, 10);

function buildWindow(window) {
  const start = new Date(`${window.start_date}T00:00:00`);
  return Array.from({ length: window.visible_days || 15 }, (_, idx) => {
    const d = new Date(start);
    d.setDate(d.getDate() + idx);
    return { key: d.toISOString().slice(0, 10), label: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) };
  });
}

function TaskRow({ task, days, editable, onChange }) {
  const start = Number(task.window_start_offset || 0);
  const end = Number(task.window_end_offset || 0);
  const width = Math.max(1, end - start + 1);
  return (
    <div className="grid grid-cols-[260px_minmax(220px,1fr)] gap-4 items-center py-4 border-t border-white/20" data-testid={`pm-project-schedule-row-${task.code}`}>
      <div className="glass-blur glass-bg rounded-2xl border border-white/40 p-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="text-sm font-black glass-text-dark">{task.code}</div>
            <div className="text-xs glass-text-muted-dark">{task.item_name}</div>
          </div>
          <div className={`text-[10px] uppercase tracking-[0.18em] font-bold ${task.critical ? "text-red-700" : "text-slate-700"}`}>{task.critical ? "Critical" : "Float"}</div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <label className="glass-text-muted-dark">Start
            <input data-testid={`pm-project-schedule-start-${task.code}`} type="date" value={toInput(task.baseline_start_date)} disabled={!editable} onChange={(e) => onChange(task.code, "schedule_start_date", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 bg-white/90 px-2 py-1 text-slate-900" />
          </label>
          <label className="glass-text-muted-dark">Days
            <input data-testid={`pm-project-schedule-duration-${task.code}`} type="number" min="1" value={task.duration_days || 1} disabled={!editable} onChange={(e) => onChange(task.code, "duration_days", Number(e.target.value || 1))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white/90 px-2 py-1 text-slate-900" />
          </label>
          <label className="col-span-2 glass-text-muted-dark">Predecessors
            <input data-testid={`pm-project-schedule-predecessors-${task.code}`} type="text" value={(task.predecessor_codes || []).join(", ")} disabled={!editable} onChange={(e) => onChange(task.code, "predecessor_codes", e.target.value.split(",").map(x => x.trim()).filter(Boolean))} className="mt-1 w-full rounded-xl border border-slate-300 bg-white/90 px-2 py-1 text-slate-900" />
          </label>
        </div>
        <div className="mt-3">
          <div className="flex items-center justify-between text-[11px] glass-text-muted-dark"><span>% Complete</span><span>{Number(task.progress_percent || 0).toFixed(1)}%</span></div>
          <div className="mt-1 h-2 rounded-full bg-slate-200 overflow-hidden">
            <div className={`h-full ${task.critical ? "bg-red-600" : "bg-emerald-500"}`} style={{ width: `${Math.max(0, Math.min(100, task.progress_percent || 0))}%` }} />
          </div>
        </div>
        {task.planning_readiness?.status !== "ready" ? (
          <div className="mt-3 rounded-2xl border border-amber-300 bg-amber-50/90 px-3 py-2 text-[11px] text-amber-900" data-testid={`pm-project-schedule-readiness-${task.code}`}>
            Missing: {(task.planning_readiness?.missing_required || []).join(", ") || "Planning fields"}
          </div>
        ) : (
          <div className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50/90 px-3 py-2 text-[11px] text-emerald-800" data-testid={`pm-project-schedule-readiness-${task.code}`}>
            OPPC plan foundation ready
          </div>
        )}
      </div>
      <div className="glass-blur glass-bg glass-dark elite-glass-panel rounded-2xl border border-white/20 p-4 overflow-x-auto">
        <div className="grid" style={{ gridTemplateColumns: `repeat(${days.length}, minmax(52px, 1fr))` }}>
          {days.map((day) => <div key={day.key} className="text-[10px] glass-text-muted-light text-center pb-2">{day.label}</div>)}
        </div>
        <div className="relative mt-1 h-12 rounded-2xl bg-slate-950/30 border border-white/10">
          <div className="absolute inset-0 grid" style={{ gridTemplateColumns: `repeat(${days.length}, minmax(52px, 1fr))` }}>
            {days.map((day) => <div key={day.key} className="border-r last:border-r-0 border-white/10" />)}
          </div>
          <div className={`absolute top-2 bottom-2 rounded-2xl ${task.critical ? "bg-red-500/85" : "bg-cyan-400/80"} border border-white/30`} style={{ left: `calc(${(Math.max(0, start) / days.length) * 100}% + 4px)`, width: `calc(${(Math.min(days.length, width) / days.length) * 100}% - 8px)` }} data-testid={`pm-project-schedule-bar-${task.code}`}>
            <div className="absolute inset-0 rounded-2xl overflow-hidden">
              <div className="h-full bg-white/35" style={{ width: `${Math.max(0, Math.min(100, task.progress_percent || 0))}%` }} />
            </div>
            <div className="relative z-10 h-full px-3 flex items-center justify-between text-[11px] font-semibold glass-text-light">
              <span>{task.cpm_activity_id || task.code}</span>
              <span>{task.forecast_start_date} → {task.forecast_finish_date}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PmProjectSchedule() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState(null);
  const [draft, setDraft] = useState({});
  const [rolloverPreview, setRolloverPreview] = useState(null);
  const [mondayReviewSummary, setMondayReviewSummary] = useState(null);

  useEffect(() => {
    const pn = params.get("project_number") || "";
    setProjectNumber(pn);
  }, [params]);

  const load = async (pn) => {
    if (!pn) return;
    setLoading(true);
    try {
      const [scheduleResponse, reviewResponse] = await Promise.all([
        api.get(`/cost-codes/projects/${encodeURIComponent(pn)}/schedule`),
        api.get(`/oppc/projects/${encodeURIComponent(pn)}/execution-workspace`).catch(() => ({ data: null })),
      ]);
      const r = scheduleResponse;
      setPayload(r.data || null);
      setMondayReviewSummary(reviewResponse?.data?.monday_review || null);
      setRolloverPreview(null);
      const next = {};
      for (const task of r.data?.schedule?.tasks || []) {
        next[task.code] = {
          code: task.code,
          schedule_start_date: task.baseline_start_date || "",
          duration_days: task.duration_days || 1,
          predecessor_codes: task.predecessor_codes || [],
          cpm_activity_id: task.cpm_activity_id || "",
          cpm_activity_name: task.cpm_activity_name || "",
          schedule_phase: task.schedule_phase || "",
          planned_performer: task.planned_performer || "",
          notes: task.notes || "",
        };
      }
      setDraft(next);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load Project Schedule.");
      setPayload(null);
      setMondayReviewSummary(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (projectNumber) load(projectNumber); }, [projectNumber]);

  const days = useMemo(() => payload?.schedule?.window ? buildWindow(payload.schedule.window) : [], [payload]);
  const tasks = payload?.schedule?.tasks || [];
  const editable = !!payload?.can_edit;

  const onSelectProject = (pn) => {
    const next = new URLSearchParams(params);
    if (pn) next.set("project_number", pn); else next.delete("project_number");
    setParams(next, { replace: true });
  };

  const onChangeTask = (code, field, value) => {
    setDraft((prev) => ({ ...prev, [code]: { ...(prev[code] || { code }), [field]: value } }));
  };

  const save = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.put(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/schedule`, { tasks: Object.values(draft) });
      setPayload(r.data || null);
      setMondayReviewSummary(null);
      setRolloverPreview(null);
      toast.success("Project Schedule updated.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save Project Schedule.");
    }
  };

  const publish = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.post(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/planning-lifecycle/publish`, { note: "Published from PM Project Schedule" });
      setPayload(r.data || null);
      setMondayReviewSummary(null);
      setRolloverPreview(null);
      toast.success("14-day plan published.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not publish the 14-day plan.");
    }
  };

  const previewRollover = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.get(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/weekly-rollover/preview`);
      setRolloverPreview(r.data?.weekly_rollover || null);
      toast.success("Weekly rollover preview ready.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not build weekly rollover preview.");
    }
  };

  const applyRollover = async () => {
    if (!projectNumber) return;
    try {
      const r = await api.post(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/weekly-rollover/apply`, {
        confirm: "APPLY_WEEKLY_ROLLOVER",
        note: "Applied from PM Project Schedule",
      });
      setPayload(r.data || null);
      setMondayReviewSummary(null);
      setRolloverPreview(r.data?.weekly_rollover || null);
      toast.success("Weekly rollover applied.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not apply weekly rollover.");
    }
  };

  return (
    <PmShell title="Project Schedule" section="jobs" intro={<p className="text-xs text-slate-500">14-day rolling CPM schedule with cost-code progress and Monday Look-Behind readiness.</p>}>
      <div className="space-y-4" data-testid="pm-project-schedule-page">
        <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-5">
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-black glass-text-dark"><CalendarRange className="w-4 h-4" /> Project Schedule</div>
              <div className="text-xs glass-text-muted-dark">Single-project 14-day rolling calendar · 7 days back and 7 days forward.</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <PmProjectSelector value={projectNumber} onChange={onSelectProject} />
              <Button variant="outline" onClick={() => load(projectNumber)} data-testid="pm-project-schedule-refresh"><RefreshCw className="w-4 h-4 mr-2" />Refresh</Button>
              <Button variant="outline" onClick={() => window.open(`${process.env.REACT_APP_BACKEND_URL}/api/cost-codes/projects/${encodeURIComponent(projectNumber)}/schedule/dot-report.pdf`, "_blank")} disabled={!projectNumber} data-testid="pm-project-schedule-dot-export"><Download className="w-4 h-4 mr-2" />DOT Schedule Report</Button>
              <Button variant="outline" onClick={previewRollover} disabled={!projectNumber || !payload?.planning_readiness?.supports_weekly_rollover} data-testid="pm-project-schedule-rollover-preview"><CalendarRange className="w-4 h-4 mr-2" />Preview Weekly Rollover</Button>
              <Button variant="outline" onClick={applyRollover} disabled={!projectNumber || !rolloverPreview?.supports_apply} data-testid="pm-project-schedule-rollover-apply"><CalendarRange className="w-4 h-4 mr-2" />Apply Weekly Rollover</Button>
              <Button variant="outline" onClick={publish} disabled={!projectNumber || !payload?.planning_lifecycle?.supports_publish} data-testid="pm-project-schedule-publish"><CalendarRange className="w-4 h-4 mr-2" />Publish 14-Day Plan</Button>
              <Button onClick={save} disabled={!projectNumber || !editable} data-testid="pm-project-schedule-save"><Save className="w-4 h-4 mr-2" />Save Schedule</Button>
              {projectNumber ? <Link to={`/pm/monday-review?project_number=${encodeURIComponent(projectNumber)}`} className="text-xs font-semibold text-amber-700 hover:underline" data-testid="pm-project-schedule-open-monday-review">Open Monday Review</Link> : null}
            </div>
          </div>
          {payload?.schedule?.warnings?.length ? (
            <div className="mt-4 rounded-2xl border border-amber-300 bg-amber-50/90 px-4 py-3 text-sm text-amber-900 flex gap-2" data-testid="pm-project-schedule-warning">
              <AlertTriangle className="w-4 h-4 mt-0.5" />
              <div>{payload.schedule.warnings.join(" ")}</div>
            </div>
          ) : null}
          {payload ? (
            <div className="mt-4 grid gap-3 md:grid-cols-5">
              <div className="rounded-2xl bg-white/70 border border-slate-200 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Projected Finish</div><div className="text-lg font-black glass-text-dark" data-testid="pm-project-schedule-projected-finish">{payload.schedule.projected_finish_date || "—"}</div></div>
              <div className="rounded-2xl bg-white/70 border border-slate-200 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Critical Path</div><div className="text-lg font-black glass-text-dark" data-testid="pm-project-schedule-critical-path-count">{(payload.schedule.critical_path || []).length}</div></div>
              <div className="rounded-2xl bg-white/70 border border-slate-200 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">% Complete</div><div className="text-lg font-black glass-text-dark" data-testid="pm-project-schedule-overall-progress">{Number(payload.progress?.overall_percent_complete || 0).toFixed(2)}%</div></div>
              <div className="rounded-2xl bg-white/70 border border-slate-200 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Monday Look-Behind</div><div className={`text-lg font-black ${mondayReviewSummary?.ready ? "text-emerald-700" : "text-amber-700"}`} data-testid="pm-project-schedule-look-behind-ready">{mondayReviewSummary?.ready ? "Ready" : `${Number(mondayReviewSummary?.completion_percent || 0).toFixed(0)}%`}</div><div className="text-[11px] glass-text-muted-dark mt-1" data-testid="pm-project-schedule-look-behind-blockers">{(mondayReviewSummary?.blocking_items || []).slice(0, 2).join(", ") || "Open the workspace"}</div></div>
              <div className="rounded-2xl bg-white/70 border border-slate-200 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">OPPC Foundation</div><div className={`text-lg font-black ${payload.planning_readiness?.status === "ready" ? "text-emerald-700" : "text-amber-700"}`} data-testid="pm-project-schedule-foundation-status">{payload.planning_readiness?.status === "ready" ? "Hardened" : "Needs fields"}</div><div className="text-[11px] glass-text-muted-dark mt-1" data-testid="pm-project-schedule-foundation-summary">{payload.planning_readiness?.ready_assignments || 0}/{payload.planning_readiness?.assignment_count || 0} ready</div></div>
            </div>
          ) : null}
        </div>

        {payload?.planning_lifecycle ? (
          <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-5" data-testid="pm-project-schedule-lifecycle-panel">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-sm font-black glass-text-dark">Rolling Two-Week Planning Lifecycle</div>
                <div className="text-xs glass-text-muted-dark" data-testid="pm-project-schedule-lifecycle-window">{payload.planning_lifecycle.window_start_date || "—"} → {payload.planning_lifecycle.window_end_date || "—"}</div>
              </div>
              <div className={`rounded-full px-3 py-1 text-xs font-bold ${payload.planning_lifecycle.status === "published" ? "bg-emerald-100 text-emerald-800" : payload.planning_lifecycle.status === "ready_to_publish" ? "bg-sky-100 text-sky-800" : payload.planning_lifecycle.status === "needs_attention" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`} data-testid="pm-project-schedule-lifecycle-status">{payload.planning_lifecycle.status}</div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3">
                <div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Publish readiness</div>
                <div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-lifecycle-publish-ready">{payload.planning_lifecycle.supports_publish ? "Ready" : "Blocked"}</div>
              </div>
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3">
                <div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Published at</div>
                <div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-lifecycle-published-at">{payload.planning_lifecycle.published_at || "Not yet published"}</div>
              </div>
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3">
                <div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Unpublished changes</div>
                <div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-lifecycle-dirty">{payload.planning_lifecycle.has_unpublished_changes ? "Yes" : "No"}</div>
              </div>
            </div>
          </div>
        ) : null}

        {rolloverPreview ? (
          <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-5" data-testid="pm-project-schedule-rollover-panel">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-sm font-black glass-text-dark">Weekly Rollover Preview</div>
                <div className="text-xs glass-text-muted-dark" data-testid="pm-project-schedule-rollover-anchor">{rolloverPreview.current_anchor_date || "—"} → {rolloverPreview.rollover_anchor_date || "—"}</div>
              </div>
              <div className={`rounded-full px-3 py-1 text-xs font-bold ${rolloverPreview.status === "ready" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`} data-testid="pm-project-schedule-rollover-status">{rolloverPreview.status}</div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Changed tasks</div><div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-rollover-changed-count">{rolloverPreview.changed_count || 0}</div></div>
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Actions reviewed</div><div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-rollover-action-count">{rolloverPreview.action_count || 0}</div></div>
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Rolled forward</div><div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-rollover-forward-count">{rolloverPreview.summary?.rolled_forward || 0}</div></div>
              <div className="rounded-2xl border border-white/40 bg-white/70 px-4 py-3"><div className="text-[10px] uppercase tracking-[0.18em] glass-text-muted-dark">Next projected finish</div><div className="text-base font-black glass-text-dark" data-testid="pm-project-schedule-rollover-finish">{rolloverPreview.next_schedule?.projected_finish_date || "—"}</div></div>
            </div>
          </div>
        ) : null}

        {payload?.planning_readiness?.status && payload.planning_readiness.status !== "ready" ? (
          <div className="rounded-[2rem] border border-amber-300 bg-amber-50/90 px-5 py-4 text-sm text-amber-950" data-testid="pm-project-schedule-foundation-alert">
            OPPC hardening found missing planning fields across this project. Fill schedule phase, planned performer, dates, and quantities before rollover and Monday look-behind workflows rely on it.
          </div>
        ) : null}

        {!projectNumber ? (
          <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-6 text-sm glass-text-muted-dark" data-testid="pm-project-schedule-empty">Choose one assigned project to open its rolling schedule dashboard.</div>
        ) : loading ? (
          <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-6 text-sm glass-text-muted-dark" data-testid="pm-project-schedule-loading">Loading Project Schedule…</div>
        ) : (
          <div className="elite-glass-panel glass-blur glass-bg rounded-[2rem] border border-white/40 p-5" data-testid="pm-project-schedule-board">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-black glass-text-dark">Rolling 14-Day Schedule</div>
                <div className="text-xs glass-text-muted-dark">Dependent tasks auto-slide when predecessors are delayed by field production quantities.</div>
              </div>
              {projectNumber ? <Link to={`/pm/project/${encodeURIComponent(projectNumber)}`} className="text-xs font-semibold text-amber-700 hover:underline" data-testid="pm-project-schedule-job-setup-link">Open Job Setup</Link> : null}
            </div>
            <div>
              {tasks.map((task) => <TaskRow key={task.code} task={{ ...task, ...(draft[task.code] || {}) }} days={days} editable={editable} onChange={onChangeTask} />)}
            </div>
          </div>
        )}
      </div>
    </PmShell>
  );
}