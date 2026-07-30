// Tasks.jsx — Iter150 (Phase A). Universal task list page. Role-aware
// filtering happens server-side; this page just renders.
//
// Visible from every protected portal. Route: /tasks
//
// MVP scope intentionally tight:
//   * Tabs: Open / In Progress / Closed
//   * Filters: priority, source module, free-text search
//   * Click row → drawer with description, comments, history, status switcher
//   * Mark-as-status quick action

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ClipboardList, AlertOctagon, CheckCircle2, Clock, ChevronRight,
  ArrowLeft, Home, Filter, Search, X, MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { PortalShell } from "@/design-system";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
import NotificationBell from "@/components/NotificationBell";
import { listTasks, getTaskSummary, getTask, patchTask, commentTask } from "@/lib/tasksApi";
import { isSignedInAnywhere, homePortalUrl } from "@/lib/permissions";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { toast } from "sonner";
import AccessDenied from "@/pages/AccessDenied";

const TAB_TO_STATUSES = {
  open: ["Open", "In Progress", "Pending Review", "Overdue"],
  closed: ["Completed", "Closed", "Cancelled"],
};

import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import GlobalSearch from "@/components/GlobalSearch";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const ALL_STATUSES = [
  "Open", "In Progress", "Pending Review", "Completed", "Closed", "Cancelled",
];

export default function Tasks() {
  const nav = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useRememberedFilter("tasks.tab", "open");
  const [priority, setPriority] = useRememberedFilter("tasks.priority", "all");
  const [sourceModule, setSourceModule] = useRememberedFilter("tasks.source", "all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({});
  const [openTaskId, setOpenTaskId] = useState(searchParams.get("id"));
  const signedIn = isSignedInAnywhere();

  const fetchData = useCallback(async () => {
    if (!signedIn) { setLoading(false); return; }
    setLoading(true);
    try {
      const statuses = TAB_TO_STATUSES[tab] || [];
      // The API only filters one status at a time; query all then filter.
      const r = await listTasks({
        limit: 200,
        ...(priority !== "all" ? { priority } : {}),
        ...(sourceModule !== "all" ? { source_module: sourceModule } : {}),
        ...(q ? { q } : {}),
      });
      const filtered = (r.items || []).filter((t) =>
        statuses.includes(t.status || "Open"));
      setItems(filtered);
      const s = await getTaskSummary().catch(() => ({}));
      setSummary(s);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load tasks"));
    } finally {
      setLoading(false);
    }
  }, [tab, priority, sourceModule, q, signedIn]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const sourceModules = useMemo(() => {
    const set = new Set();
    items.forEach((t) => t.source_module && set.add(t.source_module));
    return Array.from(set).sort();
  }, [items]);

  // Guard — must be signed into some portal. Done AFTER all hooks
  // so React's hook-order rule isn't violated.
  if (!signedIn) {
    return <AccessDenied attemptedPortal="tasks" />;
  }

  return (
    <PortalShell
      portalName="MASCI" portalRole="Admin · Tasks & Actions"
      pageTitle="Operational Accountability"
      subtitle="Open tasks · overdue items · operational follow-through"
      sideNav={renderAdminRouteSideNav()}
    >
    <div className="min-h-screen" data-testid="tasks-page">
      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        {/* Summary strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-6">
          <SummaryTile label="Open" value={summary.open_total ?? 0} icon={ClipboardList} accent="blue" />
          <SummaryTile label="Overdue" value={summary.overdue ?? 0} icon={AlertOctagon} accent="red" />
          <SummaryTile label="In Progress" value={summary.by_status?.["In Progress"] ?? 0} icon={Clock} accent="amber" />
          <SummaryTile label="Completed" value={summary.by_status?.Completed ?? 0} icon={CheckCircle2} accent="emerald" />
        </div>

        {/* Filters bar */}
        <div className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mb-4 flex flex-wrap items-center gap-2.5">
          <Tabs value={tab} onValueChange={setTab} className="min-w-0">
            <TabsList>
              <TabsTrigger value="open" data-testid="tasks-tab-open">Open</TabsTrigger>
              <TabsTrigger value="closed" data-testid="tasks-tab-closed">Closed</TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="flex-1" />
          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger className="w-[140px] h-9 text-xs" data-testid="tasks-priority-filter">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priorities</SelectItem>
                <SelectItem value="Critical">Critical</SelectItem>
                <SelectItem value="High">High</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="Low">Low</SelectItem>
              </SelectContent>
            </Select>
            {sourceModules.length > 0 && (
              <Select value={sourceModule} onValueChange={setSourceModule}>
                <SelectTrigger className="w-[180px] h-9 text-xs" data-testid="tasks-source-filter">
                  <SelectValue placeholder="Source module" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All modules</SelectItem>
                  {sourceModules.map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <div className="relative flex-1 min-w-[160px]">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search title or description…"
                className="pl-8 h-9 text-xs w-full"
                data-testid="tasks-search-input"
              />
            </div>
          </div>
        </div>

        {/* List */}
        {loading ? (
          <div className="bg-white border border-slate-200 rounded-md py-10 text-center text-slate-500 text-sm">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No tasks here"
            hint={tab === "open" ? "You're all caught up — nice." : "Nothing's been closed yet."}
            testId="tasks-empty"
          />
        ) : (
          <ul className="bg-white border border-slate-200 rounded-md divide-y divide-slate-100">
            {items.map((t) => (
              <li
                key={t.id}
                onClick={() => setOpenTaskId(t.id)}
                className="px-4 sm:px-5 py-4 hover:bg-slate-50 cursor-pointer flex items-start gap-3"
                data-testid={`task-row-${t.id}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge kind="priority" value={t.priority || "Medium"} size="sm" />
                    <StatusBadge kind="task" value={t.status || "Open"} size="sm" />
                    {t.assignee_role && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-slate-100 text-slate-700">
                        → {t.assignee_role}
                      </span>
                    )}
                  </div>
                  <div className="font-bold text-sm text-slate-900 mt-1.5 truncate">{t.title}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                    {t.source_module} · created {formatPlatformTime(t.created_at)}
                    {t.due_at && ` · due ${formatPlatformDate(t.due_at)}`}
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300 mt-1" />
              </li>
            ))}
          </ul>
        )}
      </main>

      {/* Drawer for selected task */}
      <TaskDrawer
        taskId={openTaskId}
        onClose={() => { setOpenTaskId(null); fetchData(); searchParams.delete("id"); setSearchParams(searchParams); }}
      />
    </div>
    </PortalShell>
  );
}

function SummaryTile({ label, value, icon: Icon, accent }) {
  const palette = {
    blue: "border-blue-300 text-blue-900",
    red: "border-red-400 text-red-900",
    amber: "border-amber-300 text-amber-900",
    emerald: "border-emerald-300 text-emerald-900",
  }[accent] || "border-slate-300 text-slate-900";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-3`} data-testid={`tasks-summary-${label.toLowerCase()}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-80 font-bold">{label}</span>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

function TaskDrawer({ taskId, onClose }) {
  const [task, setTask] = useState(null);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!taskId) { setTask(null); return; }
    getTask(taskId).then(setTask).catch(() => setTask(null));
  }, [taskId]);

  const setStatus = async (status) => {
    setSaving(true);
    try {
      const updated = await patchTask(taskId, { status });
      setTask(updated);
      toast.success(`Marked ${status}`);
    } catch (e) {
      toast.error(friendlyError(e, "Could not update task"));
    } finally { setSaving(false); }
  };

  const onAddComment = async () => {
    if (!comment.trim()) return;
    setSaving(true);
    try {
      const updated = await commentTask(taskId, comment);
      setTask(updated);
      setComment("");
      toast.success("Comment added");
    } catch (e) {
      toast.error(friendlyError(e, "Could not add comment"));
    } finally { setSaving(false); }
  };

  return (
    <Sheet open={!!taskId} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-lg p-0 flex flex-col" data-testid="task-drawer">
        {!task ? (
          <div className="p-6 text-slate-500 text-sm">Loading…</div>
        ) : (
          <>
            <SheetHeader className="px-5 pt-5 pb-3 border-b border-slate-200">
              <SheetTitle className="font-display text-base leading-snug">{task.title}</SheetTitle>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <StatusBadge kind="priority" value={task.priority || "Medium"} size="sm" />
                <StatusBadge kind="task" value={task.status} size="sm" />
                {task.assignee_role && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-slate-100 text-slate-700">
                    → {task.assignee_role}
                  </span>
                )}
              </div>
            </SheetHeader>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 text-sm">
              {task.description && (
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1">Description</div>
                  <div className="text-slate-700">{task.description}</div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">Source</div>
                  <div className="text-slate-700">{task.source_module}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">Created</div>
                  <div className="text-slate-700">{formatPlatformTime(task.created_at)}</div>
                </div>
                {task.due_at && (
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">Due</div>
                    <div className="text-slate-700">{formatPlatformTime(task.due_at)}</div>
                  </div>
                )}
                {task.linked_project_number && (
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">Project</div>
                    <div className="text-slate-700">{task.linked_project_number}</div>
                  </div>
                )}
              </div>

              {/* Status switcher */}
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">Change status</div>
                <div className="flex flex-wrap gap-2">
                  {ALL_STATUSES.filter((s) => s !== task.status).map((s) => (
                    <Button
                      key={s}
                      size="sm"
                      variant="outline"
                      onClick={() => setStatus(s)}
                      disabled={saving}
                      className="text-xs"
                      data-testid={`task-status-${s.replace(/\s+/g, "-").toLowerCase()}`}
                    >
                      {s}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Comments */}
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5 flex items-center gap-1.5">
                  <MessageSquare className="w-3.5 h-3.5" /> Comments ({(task.comments || []).length})
                </div>
                <ul className="space-y-2 mb-3">
                  {(task.comments || []).map((c, idx) => (
                    <li key={idx} className="bg-slate-50 rounded-md px-3 py-2 text-xs" data-testid={`task-comment-${idx}`}>
                      <div className="font-bold text-slate-800">{c.by?.name || c.by?.role || "system"}</div>
                      <div className="text-slate-700 mt-0.5">{c.body}</div>
                      <div className="font-mono text-[10px] text-slate-400 mt-0.5">{formatPlatformTime(c.at)}</div>
                    </li>
                  ))}
                </ul>
                <div className="flex items-start gap-2">
                  <Input
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Add a comment…"
                    className="text-xs h-9"
                    data-testid="task-comment-input"
                  />
                  <Button size="sm" onClick={onAddComment} disabled={saving || !comment.trim()} data-testid="task-comment-submit">Post</Button>
                </div>
              </div>

              {/* Audit history */}
              {(task.audit || []).length > 0 && (
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">History</div>
                  <ul className="text-[11px] text-slate-600 space-y-1">
                    {(task.audit || []).slice().reverse().map((a, idx) => (
                      <li key={idx}>
                        <span className="font-mono">{formatPlatformTime(a.at)}</span>
                        {" · "}
                        <span className="font-bold">{a.action}</span>
                        {a.by?.name && ` by ${a.by.name}`}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
