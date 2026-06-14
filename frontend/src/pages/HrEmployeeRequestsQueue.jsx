// OMEGA · Employee Governance Phase Alpha · G-5 · HR Request Queue
//
// HR-only operator screen for reviewing pending Employee Lifecycle
// requests submitted by Field Leadership, public field forms, and
// (via the Termination Form addendum) FL Employee Termination forms.
// HR explicitly approves (writes to db.employees via canonical
// constructor or status state machine) or rejects (with a reason).
// db.employees is NEVER mutated outside of HR-approved actions.

import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, ClipboardList, CheckCircle2, XCircle, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { getHrToken } from "@/lib/hrAuth";
import { usePageTitle } from "@/lib/usePageTitle";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const KIND_LABEL = { new_hire: "New Hire", termination: "Termination" };
const KIND_PILL = {
  new_hire: "bg-emerald-100 text-emerald-900 border-emerald-400",
  termination: "bg-red-100 text-red-900 border-red-400",
};
const STATUS_PILL = {
  pending: "bg-amber-100 text-amber-900 border-amber-400",
  approved: "bg-emerald-100 text-emerald-900 border-emerald-400",
  rejected: "bg-slate-200 text-slate-800 border-slate-400",
};
const STATUS_LABEL = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Needs Revision",
};

function Pill({ cls, children, testId }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border-2 font-mono text-[10px] uppercase tracking-[0.15em] font-bold ${cls}`}
      data-testid={testId}
    >
      {children}
    </span>
  );
}

export default function HrEmployeeRequestsQueue() {
  usePageTitle("HR · Employee Requests Queue");
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const deepLinkRequestId = searchParams.get("id") || "";
  const [items, setItems] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [kindFilter, setKindFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [active, setActive] = useState(null);
  const [hrNotes, setHrNotes] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [busy, setBusy] = useState(false);

  const [editName, setEditName] = useState("");
  const [editEmployeeId, setEditEmployeeId] = useState("");
  const [editTrade, setEditTrade] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editCrew, setEditCrew] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editSupervisor, setEditSupervisor] = useState("");
  const [editHireDate, setEditHireDate] = useState("");
  const [editStatus, setEditStatus] = useState("Terminated");
  const [editLastDay, setEditLastDay] = useState("");

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const tok = getHrToken();
      if (!tok) { nav("/hr/login"); return; }
      const qs = new URLSearchParams();
      if (statusFilter) qs.set("status", statusFilter);
      if (kindFilter) qs.set("kind", kindFilter);
      qs.set("limit", "200");
      const r = await fetch(`${API}/hr/employee-requests?${qs}`, {
        headers: { "X-HR-Token": tok },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setItems(d.items || []);
      setPendingCount(d.pending_count || 0);
    } catch (e) {
      setError(e.message || "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, kindFilter, nav]);

  useEffect(() => { fetchList(); }, [fetchList]);

  // Track 14.0-HR-READINESS — when bell click-through lands on the
  // queue with ?id=<rid>, find the matching request, scroll it into
  // view, and auto-open the approval dialog so HR can act in one
  // click instead of hunting through the list.
  useEffect(() => {
    if (!deepLinkRequestId || items.length === 0) return;
    const target = items.find((r) => r.id === deepLinkRequestId);
    if (!target) return;
    // Auto-open the review/approve dialog only for pending requests.
    if (target.status === "pending" && !approveOpen) {
      openApprove(target);
    }
    // Scroll the card into view as a UX cue.
    requestAnimationFrame(() => {
      const el = document.getElementById(`hr-request-${target.id}`);
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
    // Only fire once per landing — subsequent re-fetches must not re-open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deepLinkRequestId, items.length]);

  const openApprove = (req) => {
    setActive(req);
    setHrNotes("");
    const p = req.payload || {};
    if (req.kind === "new_hire") {
      setEditName(p.name || "");
      setEditEmployeeId(p.employee_id || "");
      setEditTrade(p.trade || "");
      setEditRole(p.role || "");
      setEditCrew(p.crew || "");
      setEditEmail(p.email || "");
      setEditPhone(p.phone || "");
      setEditSupervisor("");
      setEditHireDate("");
    } else {
      setEditStatus(p.requested_status || "Terminated");
      setEditLastDay(p.last_day_worked || "");
    }
    setApproveOpen(true);
  };

  const openReject = (req) => {
    setActive(req);
    setRejectReason("");
    setRejectOpen(true);
  };

  const doApprove = async () => {
    if (!active || busy) return;
    setBusy(true);
    try {
      const tok = getHrToken();
      const body = active.kind === "new_hire"
        ? {
            name: editName.trim() || undefined,
            employee_id: editEmployeeId.trim() || undefined,
            trade: editTrade.trim() || undefined,
            role: editRole.trim() || undefined,
            crew: editCrew.trim() || undefined,
            email: editEmail.trim() || undefined,
            phone: editPhone.trim() || undefined,
            supervisor: editSupervisor.trim() || undefined,
            hire_date: editHireDate || undefined,
            hr_notes: hrNotes.trim() || undefined,
          }
        : {
            requested_status: editStatus,
            last_day_worked: editLastDay || undefined,
            hr_notes: hrNotes.trim() || undefined,
          };
      const r = await fetch(`${API}/hr/employee-requests/${active.id}/approve`, {
        method: "POST",
        headers: { "X-HR-Token": tok, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        const msg = (d?.detail?.message) || (typeof d?.detail === "string" ? d.detail : `HTTP ${r.status}`);
        throw new Error(msg);
      }
      const d = await r.json();
      toast.success(
        active.kind === "new_hire" ? "Employee added by HR" : "Employee terminated",
        { description: `Resulting employee id: ${(d.resulting_employee_id || "").slice(0, 8)}…` },
      );
      setApproveOpen(false);
      await fetchList();
    } catch (e) {
      toast.error("Could not approve this request. Try again, or contact your administrator if it keeps failing.");
    } finally {
      setBusy(false);
    }
  };

  const doReject = async () => {
    if (!active || busy) return;
    if (rejectReason.trim().length < 5) {
      toast.error("Reason must be at least 5 characters.");
      return;
    }
    setBusy(true);
    try {
      const tok = getHrToken();
      const r = await fetch(`${API}/hr/employee-requests/${active.id}/reject`, {
        method: "POST",
        headers: { "X-HR-Token": tok, "Content-Type": "application/json" },
        body: JSON.stringify({ reason: rejectReason.trim() }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d?.detail || `HTTP ${r.status}`);
      }
      toast.success("Sent back to submitter for revision.");
      setRejectOpen(false);
      await fetchList();
    } catch (e) {
      toast.error("Could not record the revision request. Try again, or contact your administrator if it keeps failing.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 pb-16" data-testid="hr-employee-requests-page">
      <header className="bg-slate-900 border-b-4 border-emerald-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/hr" className="text-slate-300 hover:text-white inline-flex items-center gap-1"
                data-testid="hr-requests-back">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to HR Hub</span>
          </Link>
          <div className="flex items-center gap-2 text-white ml-auto">
            <ClipboardList className="w-5 h-5 text-emerald-400" />
            <span className="font-display text-lg font-black tracking-tight">
              Employee Requests Queue
            </span>
            <Pill cls="bg-emerald-100 text-emerald-900 border-emerald-400"
                  testId="hr-requests-pending-badge">
              {pendingCount} pending
            </Pill>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 space-y-4">
        <div className="rounded border border-emerald-200 bg-emerald-50/60 px-3 py-2 text-[12px] text-emerald-900 flex items-start gap-2" data-testid="hr-requests-coaching">
          <ClipboardList className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold">Review pending employee requests.</span>{" "}
            Approve to create or update the employee record. Send back for revision if anything is unclear or incomplete — the submitter and the audit log both get your note.
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap" data-testid="hr-requests-filters">
          {["pending", "approved", "rejected"].map(s => (
            <Button key={s} size="sm"
                    variant={statusFilter === s ? "default" : "outline"}
                    onClick={() => setStatusFilter(s)}
                    className={`h-8 px-3 text-xs uppercase tracking-wide font-bold ${
                      statusFilter === s ? "bg-slate-800 text-white" : "bg-white"
                    }`}
                    data-testid={`hr-requests-filter-${s}`}>
              {STATUS_LABEL[s] || s}
            </Button>
          ))}
          <span className="mx-2 h-5 w-px bg-slate-300" />
          {["", "new_hire", "termination"].map(k => (
            <Button key={k || "all"} size="sm"
                    variant={kindFilter === k ? "default" : "outline"}
                    onClick={() => setKindFilter(k)}
                    className={`h-8 px-3 text-xs uppercase tracking-wide font-bold ${
                      kindFilter === k ? "bg-slate-800 text-white" : "bg-white"
                    }`}
                    data-testid={`hr-requests-kind-${k || "all"}`}>
              {k ? KIND_LABEL[k] : "All kinds"}
            </Button>
          ))}
          <Button size="sm" variant="outline" onClick={() => fetchList()}
                  className="h-8 px-3 text-xs ml-auto" data-testid="hr-requests-refresh">
            <RotateCcw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>

        {loading && (
          <Card className="p-6 text-center text-slate-500" data-testid="hr-requests-loading">
            <Loader2 className="w-5 h-5 inline animate-spin mr-2" /> Loading queue…
          </Card>
        )}
        {!loading && error && (
          <Card className="p-6 bg-rose-50 border-rose-300 text-rose-900" data-testid="hr-requests-error">
            {error}
          </Card>
        )}
        {!loading && !error && items.length === 0 && (
          <Card className="p-8 text-center text-slate-500" data-testid="hr-requests-empty">
            <ClipboardList className="w-8 h-8 mx-auto mb-2 text-slate-400" />
            No {statusFilter} requests{kindFilter ? ` of kind "${KIND_LABEL[kindFilter]}"` : ""}.
          </Card>
        )}
        {!loading && !error && items.length > 0 && (
          <div className="space-y-2" data-testid="hr-requests-list">
            {items.map(req => {
              const p = req.payload || {};
              const isPending = req.status === "pending";
              return (
                <Card key={req.id}
                      id={`hr-request-${req.id}`}
                      className={`p-4 bg-white border-2 ${deepLinkRequestId === req.id ? "border-amber-500 ring-4 ring-amber-200" : "border-slate-200 hover:border-slate-300"}`}
                      data-testid="hr-requests-row">
                  <div className="flex items-start gap-3 flex-wrap">
                    <div className="flex flex-col gap-1 min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Pill cls={KIND_PILL[req.kind] || "bg-slate-100 text-slate-800 border-slate-300"}
                              testId={`hr-requests-kind-pill-${req.kind}`}>
                          {KIND_LABEL[req.kind] || req.kind}
                        </Pill>
                        <Pill cls={STATUS_PILL[req.status] || "bg-slate-100 text-slate-800 border-slate-300"}
                              testId={`hr-requests-status-pill-${req.status}`}>
                          {STATUS_LABEL[req.status] || req.status}
                        </Pill>
                        <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider">
                          {new Date(req.requested_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="font-bold text-slate-900 truncate">
                        {req.kind === "new_hire"
                          ? (p.name || "(no name)")
                          : `${p.target_employee_name || "(unknown)"} → ${p.requested_status || "Terminated"}`}
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-2 flex-wrap">
                        <span>Submitted by <strong className="font-mono uppercase">{req.requested_by_role}</strong></span>
                        {req.submitter_name && <span>· {req.submitter_name}</span>}
                        {req.submitted_via && <span>· via {req.submitted_via}</span>}
                        {req.linked_fl_record_id && (
                          <span>· FL record <span className="font-mono">{req.linked_fl_record_id.slice(0, 8)}…</span></span>
                        )}
                      </div>
                      {req.kind === "new_hire" && (p.trade || p.role || p.crew || p.employee_id) && (
                        <div className="text-xs text-slate-600 mt-1">
                          {[p.employee_id ? `#${p.employee_id}` : null, p.trade, p.role, p.crew]
                            .filter(Boolean).join(" · ")}
                        </div>
                      )}
                      {req.kind === "termination" && p.reason && (
                        <div className="text-xs text-slate-700 italic mt-1">"{p.reason}"</div>
                      )}
                      {req.status === "rejected" && req.rejection_reason && (
                        <div className="text-xs text-amber-700 italic mt-1">
                          Sent back: "{req.rejection_reason}"
                        </div>
                      )}
                      {req.status === "approved" && req.resulting_employee_id && (
                        <div className="text-xs text-emerald-700 mt-1">
                          Employee: <span className="font-mono">{req.resulting_employee_id.slice(0, 8)}…</span>
                        </div>
                      )}
                    </div>
                    {isPending && (
                      <div className="flex items-center gap-2 shrink-0">
                        <Button size="sm" onClick={() => openApprove(req)}
                                className="h-9 px-3 bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-emerald-900"
                                data-testid={`hr-requests-approve-${req.id}`}>
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => openReject(req)}
                                className="h-9 px-3 border-2 border-amber-400 text-amber-700 hover:bg-amber-50 font-bold uppercase tracking-wide text-xs"
                                data-testid={`hr-requests-reject-${req.id}`}>
                          <XCircle className="w-3.5 h-3.5 mr-1" /> Needs Revision
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <Dialog open={approveOpen} onOpenChange={setApproveOpen}>
        <DialogContent className="sm:max-w-lg" data-testid="hr-requests-approve-modal">
          <DialogHeader>
            <DialogTitle>Approve {active ? KIND_LABEL[active.kind] : ""} Request</DialogTitle>
            <DialogDescription>
              {active?.kind === "new_hire"
                ? "HR may edit any field before creating the employee."
                : "Confirm the target status and last-day-worked."}
            </DialogDescription>
          </DialogHeader>
          {active?.kind === "new_hire" && (
            <div className="space-y-2 py-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Name *</Label>
                  <Input value={editName} onChange={e => setEditName(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-name" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Employee ID</Label>
                  <Input value={editEmployeeId} onChange={e => setEditEmployeeId(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-employee-id" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Trade</Label>
                  <Input value={editTrade} onChange={e => setEditTrade(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-trade" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Role</Label>
                  <Input value={editRole} onChange={e => setEditRole(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-role" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Crew</Label>
                  <Input value={editCrew} onChange={e => setEditCrew(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-crew" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Supervisor</Label>
                  <Input value={editSupervisor} onChange={e => setEditSupervisor(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-supervisor" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Email</Label>
                  <Input value={editEmail} onChange={e => setEditEmail(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-email" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Phone</Label>
                  <Input value={editPhone} onChange={e => setEditPhone(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-phone" />
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Hire Date</Label>
                  <Input type="date" value={editHireDate} onChange={e => setEditHireDate(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-hire-date" />
                </div>
              </div>
            </div>
          )}
          {active?.kind === "termination" && (
            <div className="space-y-2 py-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Target Status</Label>
                  <select value={editStatus} onChange={e => setEditStatus(e.target.value)}
                          className="mt-1 w-full h-10 border-2 border-slate-300 rounded px-2 text-sm"
                          data-testid="hr-requests-edit-status">
                    {["Terminated", "Resigned", "Retired", "Inactive"].map(s =>
                      <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wide font-bold">Last Day Worked</Label>
                  <Input type="date" value={editLastDay} onChange={e => setEditLastDay(e.target.value)}
                         className="mt-1" data-testid="hr-requests-edit-last-day" />
                </div>
              </div>
              <div className="bg-amber-50 border-2 border-amber-300 rounded p-2 text-xs text-amber-900 mt-2">
                Target: <strong>{active?.payload?.target_employee_name}</strong>
              </div>
            </div>
          )}
          <div className="py-1">
            <Label className="text-[10px] uppercase tracking-wide font-bold">HR Notes (audit)</Label>
            <Textarea value={hrNotes} onChange={e => setHrNotes(e.target.value)}
                      rows={2} placeholder="Optional · added to the lifecycle event ledger"
                      className="mt-1" data-testid="hr-requests-approve-notes" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApproveOpen(false)}
                    data-testid="hr-requests-approve-cancel">Cancel</Button>
            <Button disabled={busy || (active?.kind === "new_hire" && editName.trim().length < 2)}
                    onClick={doApprove}
                    className="bg-emerald-700 hover:bg-emerald-800 text-white"
                    data-testid="hr-requests-approve-confirm">
              <CheckCircle2 className="w-4 h-4 mr-1" /> Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent className="sm:max-w-md" data-testid="hr-requests-reject-modal">
          <DialogHeader>
            <DialogTitle>Send Back for Revision</DialogTitle>
            <DialogDescription>
              A short reason (5+ characters) goes back to the submitter and stays in the audit log.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Label className="text-xs uppercase tracking-wide font-bold">Reason</Label>
            <Textarea value={rejectReason} onChange={e => setRejectReason(e.target.value)}
                      rows={3} placeholder="e.g. Duplicate of existing employee · already on roster."
                      className="mt-2" data-testid="hr-requests-reject-reason" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectOpen(false)}
                    data-testid="hr-requests-reject-cancel">Cancel</Button>
            <Button disabled={busy || rejectReason.trim().length < 5}
                    onClick={doReject}
                    className="bg-rose-700 hover:bg-rose-800 text-white"
                    data-testid="hr-requests-reject-confirm">
              <XCircle className="w-4 h-4 mr-1" /> Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  );
}
