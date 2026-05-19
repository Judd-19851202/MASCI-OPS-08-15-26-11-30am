// PoRequests.jsx — Iter153 (Phase D). Universal PO Requests page at
// `/po-requests`. Role-aware scoping happens server-side.
//
//   * Field Leadership / PM / Shop / Safety can SUBMIT.
//   * PM / HR / Admin can APPROVE / REJECT / CLARIFY.
//   * Submitter (or anyone with permission) can UPLOAD RECEIPT.
//   * Admins can close / cancel.
//
// Mobile-first form for the field. Receipt camera-capture supported
// via `<input type=file accept=image/*,application/pdf capture=environment>`.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Receipt, Plus, Search, ArrowLeft, Home, ChevronRight,
  Camera, CheckCircle2, XCircle, MessageSquare, RefreshCw,
  ClipboardCheck, AlertTriangle, FileText, Download, User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import NotificationBell from "@/components/NotificationBell";
import { JobPicker } from "@/components/JobPicker";
import { SupplierCombo } from "@/components/SupplierCombo";
import { useT } from "@/lib/i18n";
import {
  listPos, poSummary, getPo, submitPo, approvePo, uploadReceipt,
  closePo, cancelPo, respondClarification, downloadPoExportCsv,
  PO_CATEGORIES, PO_URGENCY,
} from "@/lib/poApi";
import { isSignedInAnywhere } from "@/lib/permissions";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { isAdmin } from "@/lib/adminAuth";
import { isHr } from "@/lib/hrAuth";
import { isPm } from "@/lib/pmAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import AccessDenied from "@/pages/AccessDenied";
import { toast } from "sonner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { PO_STATUS_TINTS } from "@/lib/statusBadges";
import GlobalSearch from "@/components/GlobalSearch";

const STATUS_COLORS = PO_STATUS_TINTS;

export default function PoRequests() {
  const nav = useNavigate();
  const signedIn = isSignedInAnywhere() || isLeadershipAuthed();
  const canApprove = isPm() || isHr() || isAdmin();

  const [tab, setTab] = useRememberedFilter("po.tab", "open");
  const [statusFilter, setStatusFilter] = useRememberedFilter("po.status", "all");
  const [quickFilter, setQuickFilter] = useRememberedFilter("po.quick", "all");
  const [vendorFilter, setVendorFilter] = useRememberedFilter("po.vendor", "");
  const [supervisorFilter, setSupervisorFilter] = useRememberedFilter("po.supervisor", "");
  const [projectFilter, setProjectFilter] = useRememberedFilter("po.project", "");
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [openId, setOpenId] = useState(null);
  const [addOpen, setAddOpen] = useState(false);

  // Quick-filter chips translate to query params. Each chip is a
  // server-side filter — keeps payload small and aligns with the
  // role-aware backend scoping.
  const QUICK_FILTERS = [
    { key: "all",          label: "All",            color: "bg-slate-100 text-slate-700" },
    { key: "pending_approval", label: "Pending Approval", color: "bg-blue-100 text-blue-800" },
    { key: "pending_receipt",  label: "Pending Receipt",  color: "bg-indigo-100 text-indigo-800" },
    { key: "overdue",      label: "Overdue Receipt", color: "bg-rose-100 text-rose-800" },
    { key: "clarification",label: "Needs Clarification", color: "bg-amber-100 text-amber-800" },
    { key: "mine",         label: "Mine",           color: "bg-emerald-100 text-emerald-800" },
  ];

  const fetchAll = useCallback(async () => {
    if (!signedIn) { setLoading(false); return; }
    setLoading(true);
    try {
      const params = { limit: 200 };
      if (statusFilter !== "all") params.status = statusFilter;
      if (q) params.q = q;
      if (vendorFilter) params.vendor = vendorFilter;
      if (supervisorFilter) params.requested_by_name = supervisorFilter;
      if (projectFilter) params.project_number = projectFilter;
      if (quickFilter === "pending_approval") params.status = "Pending Approval";
      else if (quickFilter === "pending_receipt") params.missing_receipt_only = true;
      else if (quickFilter === "overdue") params.status = "Overdue Receipt";
      else if (quickFilter === "clarification") params.status = "Clarification Needed";
      else if (quickFilter === "mine") params.mine_only = true;
      const r = await listPos(params);
      const allItems = r.items || [];
      const filtered = allItems.filter((p) => {
        if (tab === "open") return !["Closed", "Cancelled", "Rejected"].includes(p.status);
        if (tab === "closed") return ["Closed", "Cancelled", "Rejected"].includes(p.status);
        return true;
      });
      setItems(filtered);
      const s = await poSummary().catch(() => ({}));
      setSummary(s);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load PO requests"));
    } finally { setLoading(false); }
  }, [signedIn, statusFilter, q, tab, quickFilter, vendorFilter, supervisorFilter, projectFilter]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (!signedIn) return <AccessDenied attemptedPortal="po-requests" />;

  return (
    <div className="min-h-screen bg-slate-50" data-testid="po-requests-page">
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link to="/" className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="po-nav-home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
          </Link>
          <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="po-nav-back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
          </button>
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-400 font-bold">PO Requests · Receipt Tracking</div>
            <div className="font-display text-lg sm:text-xl font-black text-white leading-tight">Operational POs</div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <GlobalSearch accent="dark" />
            <NotificationBell accent="white" />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        {/* iter242 — Authority-boundary clarification banner. Field
            Leadership submits the request; PM / Co-PMs / HR / Admin
            issue the official PO. Visible to PM-role users (covers
            primary PM AND any Co-PMs on the job), HR, and Admin. */}
        <div className="bg-amber-50 border-l-4 border-amber-400 text-amber-900 text-[12px] sm:text-[13px] rounded-md px-3 py-2 mb-5 leading-snug" data-testid="po-authority-banner">
          <span className="font-bold uppercase tracking-wide text-[10px] sm:text-[11px] block mb-0.5">Authority &amp; Visibility</span>
          Field Leadership submits purchase <strong>requests</strong>. The assigned PM, any Co-PMs on the job, HR, and Admin issue the official PO and assign the PO number. After purchase, the requester uploads receipts here.
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <SummaryTile label="Pending Approval" value={summary.pending_approval ?? 0} icon={ClipboardCheck} accent="blue" />
          <SummaryTile label="Pending Receipt"  value={summary.pending_receipt ?? 0}  icon={Receipt}        accent="indigo" />
          <SummaryTile label="Overdue Receipt"  value={summary.overdue_receipt ?? 0}  icon={AlertTriangle}  accent="red" />
          <SummaryTile label="Closed"           value={summary.by_status?.Closed ?? 0} icon={CheckCircle2}  accent="emerald" />
        </div>

        <div className="bg-white border-2 border-slate-200 rounded-md p-3 sm:p-4 mb-4 space-y-3">
          {/* Quick-filter chips */}
          <div className="flex flex-wrap items-center gap-1.5" data-testid="po-quick-filters">
            {QUICK_FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setQuickFilter(f.key)}
                className={`px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border ${
                  quickFilter === f.key
                    ? `${f.color} border-current shadow-sm`
                    : "bg-white text-slate-500 border-slate-300 hover:bg-slate-50"
                }`}
                data-testid={`po-quick-${f.key}`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Main row: tabs / status / search / actions */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center bg-slate-100 rounded-md p-0.5">
              <button onClick={() => setTab("open")} className={`px-3 py-1.5 rounded text-xs font-bold ${tab === "open" ? "bg-white shadow-sm" : "text-slate-600"}`} data-testid="po-tab-open">Open</button>
              <button onClick={() => setTab("closed")} className={`px-3 py-1.5 rounded text-xs font-bold ${tab === "closed" ? "bg-white shadow-sm" : "text-slate-600"}`} data-testid="po-tab-closed">Closed</button>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px] h-9 text-xs" data-testid="po-status-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {Object.keys(STATUS_COLORS).map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
              </SelectContent>
            </Select>
            <div className="relative flex-1 min-w-[160px]">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="PO # · vendor · description" className="pl-8 h-9 text-xs" data-testid="po-search-input" />
            </div>
            <Button variant="outline" size="sm" onClick={fetchAll} className="text-xs" data-testid="po-refresh" title="Refresh">
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
            {canApprove && (
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    await downloadPoExportCsv({
                      ...(statusFilter !== "all" ? { status: statusFilter } : {}),
                      ...(vendorFilter ? { vendor: vendorFilter } : {}),
                      ...(supervisorFilter ? { requested_by_name: supervisorFilter } : {}),
                      ...(projectFilter ? { project_number: projectFilter } : {}),
                      ...(quickFilter === "pending_receipt" ? { missing_receipt_only: true } : {}),
                    });
                    toast.success("Export downloaded");
                  } catch (e) { toast.error(friendlyError(e, "Export failed")); }
                }}
                className="text-xs"
                data-testid="po-export-csv"
                title="Export current view as CSV"
              >
                <Download className="w-3.5 h-3.5 sm:mr-1" />
                <span className="hidden sm:inline">CSV</span>
              </Button>
            )}
            <AddDialog open={addOpen} setOpen={setAddOpen} onSaved={() => { setAddOpen(false); fetchAll(); }} />
          </div>

          {/* Advanced filters — supervisor, vendor, project (collapsed on mobile) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="relative">
              <User className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <Input
                value={supervisorFilter}
                onChange={(e) => setSupervisorFilter(e.target.value)}
                placeholder="Filter by supervisor / requester"
                className="pl-8 h-9 text-xs"
                data-testid="po-supervisor-filter"
              />
            </div>
            <div className="relative">
              <Receipt className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <Input
                value={vendorFilter}
                onChange={(e) => setVendorFilter(e.target.value)}
                placeholder="Filter by vendor"
                className="pl-8 h-9 text-xs"
                data-testid="po-vendor-filter"
              />
            </div>
            <div className="relative">
              <FileText className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <Input
                value={projectFilter}
                onChange={(e) => setProjectFilter(e.target.value)}
                placeholder="Filter by project / job #"
                className="pl-8 h-9 text-xs"
                data-testid="po-project-filter"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="bg-white border-2 border-slate-200 rounded-md py-10 text-center text-slate-500 text-sm">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="No PO requests in this view"
            hint={tab === "open"
              ? "Try the Closed tab, clear filters, or submit a new PO."
              : "Closed / Cancelled / Rejected POs will appear here."}
            testId="po-empty"
          />
        ) : (
          <div className="bg-white border-2 border-slate-200 rounded-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">PO #</th>
                  <th className="px-4 py-2.5">Vendor</th>
                  <th className="px-4 py-2.5">Project</th>
                  <th className="px-4 py-2.5">Amount</th>
                  <th className="px-4 py-2.5">Urgency</th>
                  <th className="px-4 py-2.5">Requested</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((p) => (
                  <tr key={p.id} onClick={() => setOpenId(p.id)} className="hover:bg-slate-50 cursor-pointer" data-testid={`po-row-${p.id}`}>
                    <td className="px-4 py-2.5">
                      <StatusBadge kind="po" value={p.status} size="sm" />
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs font-bold text-slate-900">{p.po_number || "—"}</td>
                    <td className="px-4 py-2.5 text-slate-800 text-sm">{p.vendor}</td>
                    <td className="px-4 py-2.5 text-slate-600 text-xs font-mono">{p.project_number}</td>
                    <td className="px-4 py-2.5 text-slate-800 text-xs font-mono">${(p.approved_amount ?? p.estimated_amount).toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-slate-600 text-xs">{p.urgency}</td>
                    <td className="px-4 py-2.5 text-slate-500 text-[11px] font-mono">{new Date(p.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-2.5"><ChevronRight className="w-4 h-4 text-slate-300" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      <PoDrawer id={openId} canApprove={canApprove} isAdmin={isAdmin()} onClose={() => { setOpenId(null); fetchAll(); }} />
    </div>
  );
}

function SummaryTile({ label, value, icon: Icon, accent }) {
  const palette = {
    blue: "border-blue-300 text-blue-900",
    indigo: "border-indigo-300 text-indigo-900",
    red: "border-red-400 text-red-900",
    emerald: "border-emerald-300 text-emerald-900",
  }[accent] || "border-slate-300 text-slate-900";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-3`} data-testid={`po-summary-${label.toLowerCase().replace(/\s+/g,'-')}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-80 font-bold">{label}</span>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

function AddDialog({ open, setOpen, onSaved }) {
  const { t } = useT();
  const empty = {
    project_number: "", project_name: "", vendor: "", description: "",
    estimated_amount: "", category: "Materials", urgency: "Normal",
    needed_by_date: "", notes: "", supervisor_signature: "",
  };
  const [form, setForm] = useState(empty);
  const submit = async (e) => {
    e.preventDefault();
    if (!form.project_number.trim() || !form.vendor.trim() || !form.description.trim()) {
      toast.error(t("Please select a job, choose a vendor, and add a description.")); return;
    }
    // project_name is local-only (used for picker display) — strip before submit
    // so the backend PoRequestCreate schema receives only the fields it knows.
    const { project_name: _pname, ...rest } = form;
    const payload = { ...rest,
      estimated_amount: parseFloat(form.estimated_amount) || 0 };
    try {
      const r = await submitPo(payload);
      toast.success(`${t("PO requested")} — ${r.id.slice(0, 8)}`);
      onSaved();
      setForm(empty);
    } catch (e2) { toast.error(friendlyError(e2, t("Could not request PO"))); }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="text-xs" data-testid="po-add-trigger">
          <Plus className="w-3.5 h-3.5 mr-1" /> {t("Request PO")}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto" data-testid="po-add-dialog">
        <DialogHeader><DialogTitle>{t("Request PO")}</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Label>{t("Job")} *</Label>
            <JobPicker
              projectName={form.project_name}
              projectNumber={form.project_number}
              allowCustom={false}
              emptyHint={t("I don't see this job — contact PM to add it.")}
              onSelect={(job) => {
                if (job) {
                  setForm((f) => ({
                    ...f,
                    project_number: job.project_number || "",
                    project_name: job.project_name || "",
                  }));
                }
              }}
              className="mt-1"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              {t("Active jobs only · maintained by PM / Admin.")}
            </p>
          </div>
          <div>
            <Label>{t("Vendor / Subcontractor")} *</Label>
            <SupplierCombo
              value={form.vendor}
              onChange={(v) => setForm((f) => ({ ...f, vendor: v }))}
              onPick={(sup) => setForm((f) => ({ ...f, vendor: sup?.name || f.vendor }))}
              placeholder={t("Search vendors or add a new one…")}
              testId="po-add-vendor"
              className="mt-1"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              {t("Type to search the shared vendor list. New names are added to the master list for everyone.")}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="col-span-2">
              <Label>{t("Description")} *</Label>
              <Textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="po-add-description" />
            </div>
            <div>
              <Label>{t("Estimated amount")}</Label>
              <Input type="number" step="0.01" value={form.estimated_amount} onChange={(e) => setForm({ ...form, estimated_amount: e.target.value })} data-testid="po-add-amount" />
            </div>
            <div>
              <Label>{t("Urgency")}</Label>
              <Select value={form.urgency} onValueChange={(v) => setForm({ ...form, urgency: v })}>
                <SelectTrigger data-testid="po-add-urgency"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {PO_URGENCY.map((u) => (<SelectItem key={u} value={u}>{u}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("Category")}</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger data-testid="po-add-category"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {PO_CATEGORIES.map((c) => (<SelectItem key={c} value={c}>{c}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("Needed by")}</Label>
              <Input type="date" value={form.needed_by_date} onChange={(e) => setForm({ ...form, needed_by_date: e.target.value })} />
            </div>
            <div className="col-span-2">
              <Label>{t("Supervisor signature")}</Label>
              <Input value={form.supervisor_signature} onChange={(e) => setForm({ ...form, supervisor_signature: e.target.value })} placeholder={t("Your name")} />
            </div>
            <div className="col-span-2">
              <Label>{t("Notes")}</Label>
              <Textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
          </div>
          <DialogFooter><Button type="submit" data-testid="po-add-submit">{t("Request PO")}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function PoDrawer({ id, canApprove, isAdmin: isAd, onClose }) {
  const [po, setPo] = useState(null);
  const [saving, setSaving] = useState(false);
  const [actionNotes, setActionNotes] = useState("");
  const [manualPoNumber, setManualPoNumber] = useState("");
  const [approvedAmount, setApprovedAmount] = useState("");
  const [receiptAmount, setReceiptAmount] = useState("");
  const [receiptNotes, setReceiptNotes] = useState("");
  const [clarifyResp, setClarifyResp] = useState("");

  useEffect(() => {
    if (!id) { setPo(null); return; }
    getPo(id).then(setPo).catch(() => setPo(null));
  }, [id]);

  const refresh = async () => { if (po) setPo(await getPo(po.id)); };
  const can = useMemo(() => ({
    approve: canApprove && ["Submitted", "Pending Approval", "Clarification Needed"].includes(po?.status),
    upload: po && ["Approved", "Pending Receipt", "Overdue Receipt"].includes(po?.status),
    close: isAd && ["Receipt Uploaded", "Approved", "Pending Receipt", "Overdue Receipt"].includes(po?.status),
    cancel: isAd && !["Closed", "Cancelled", "Rejected"].includes(po?.status),
    respondClarification: po?.status === "Clarification Needed",
  }), [po, canApprove, isAd]);

  const doRespondClarification = async () => {
    if (!clarifyResp.trim()) { toast.error("Response is required"); return; }
    setSaving(true);
    try {
      const r = await respondClarification(po.id, clarifyResp.trim());
      setPo(r);
      toast.success("Response sent — PO returned to Pending Approval");
      setClarifyResp("");
    } catch (e) { toast.error(friendlyError(e, "Could not send response")); }
    finally { setSaving(false); }
  };

  const doAction = async (action) => {
    setSaving(true);
    try {
      const payload = { notes: actionNotes };
      if (action === "approve") {
        if (manualPoNumber.trim()) payload.po_number_manual = manualPoNumber.trim();
        if (approvedAmount.trim()) payload.approved_amount = parseFloat(approvedAmount);
      }
      const r = await approvePo(po.id, action, payload);
      setPo(r);
      toast.success(`PO ${action === "approve" ? "approved" : action === "reject" ? "rejected" : "clarification requested"}`);
      setActionNotes(""); setManualPoNumber(""); setApprovedAmount("");
    } catch (e) { toast.error(friendlyError(e, "Action failed")); }
    finally { setSaving(false); }
  };

  const doReceipt = async (e) => {
    e.preventDefault();
    const file = e.target.elements.receipt_file?.files?.[0];
    if (!file) { toast.error("Pick a receipt file first"); return; }
    setSaving(true);
    try {
      const r = await uploadReceipt(po.id, file, receiptAmount, receiptNotes);
      setPo(r);
      toast.success("Receipt uploaded");
      setReceiptAmount(""); setReceiptNotes("");
    } catch (e2) { toast.error(friendlyError(e2, "Upload failed")); }
    finally { setSaving(false); }
  };

  return (
    <Sheet open={!!id} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 flex flex-col" data-testid="po-drawer">
        {!po ? (
          <div className="p-6 text-slate-500 text-sm">Loading…</div>
        ) : (
          <>
            <SheetHeader className="px-5 pt-5 pb-3 border-b border-slate-200">
              <SheetTitle className="font-display text-base leading-snug">
                {po.po_number || `PO ${po.id.slice(0, 8)}`}
              </SheetTitle>
              <div className="flex items-center gap-2 mt-2 flex-wrap text-xs">
                <StatusBadge kind="po" value={po.status} size="md" />
                <span className="text-slate-600 font-mono">${(po.approved_amount ?? po.estimated_amount).toFixed(2)}</span>
                <span className="text-slate-500">· {po.urgency}</span>
                <span className="text-slate-500 font-mono">· {po.project_number}</span>
              </div>
            </SheetHeader>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 text-sm">
              <KV label="Vendor" value={po.vendor} />
              <KV label="Category" value={po.category} />
              <KV label="Description" value={po.description} multiline />
              <KV label="Requested by" value={`${po.requested_by_name} (${po.requested_by_role})`} />
              <KV label="Submitted" value={new Date(po.created_at).toLocaleString()} />
              {po.needed_by_date && <KV label="Needed by" value={po.needed_by_date} />}
              {po.approved_by && <KV label="Approved by" value={`${po.approved_by.name} on ${new Date(po.approved_at).toLocaleString()}`} />}
              {po.rejection_reason && <KV label="Reason" value={po.rejection_reason} multiline />}

              {/* Receipt block */}
              {po.receipt_url ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-md p-3" data-testid="po-receipt-block">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-700 font-bold mb-1">Receipt Uploaded</div>
                  <a href={po.receipt_url} target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-slate-900 hover:text-red-700 underline">
                    {po.receipt_filename || "View"}
                  </a>
                  <div className="text-[11px] text-slate-600 mt-1">
                    {po.receipt_amount != null && <>${po.receipt_amount.toFixed(2)} · </>}
                    {po.receipt_uploaded_at && new Date(po.receipt_uploaded_at).toLocaleString()}
                  </div>
                  {po.receipt_notes && <div className="text-[11px] text-slate-700 mt-1">{po.receipt_notes}</div>}
                </div>
              ) : can.upload && (
                <form onSubmit={doReceipt} className="bg-amber-50 border border-amber-200 rounded-md p-3 space-y-2" data-testid="po-receipt-form">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold flex items-center gap-1.5">
                    <Camera className="w-3.5 h-3.5" /> Upload receipt
                  </div>
                  <Input type="file" name="receipt_file" accept="image/*,application/pdf" capture="environment" required data-testid="po-receipt-file" />
                  <div className="grid grid-cols-2 gap-2">
                    <Input type="number" step="0.01" placeholder="Actual amount" value={receiptAmount} onChange={(e) => setReceiptAmount(e.target.value)} className="text-xs" data-testid="po-receipt-amount" />
                    <Input placeholder="Notes" value={receiptNotes} onChange={(e) => setReceiptNotes(e.target.value)} className="text-xs" />
                  </div>
                  <Button type="submit" size="sm" disabled={saving} data-testid="po-receipt-submit">{saving ? "Uploading…" : "Upload"}</Button>
                </form>
              )}

              {/* Clarification response block — visible when status is "Clarification Needed". 
                  Original requester or same-role teammates can respond. */}
              {can.respondClarification && (
                <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-3 space-y-2" data-testid="po-clarification-response-block">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800 font-bold flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" /> Clarification requested by approver
                  </div>
                  {po.rejection_reason && (
                    <div className="text-xs text-amber-900 bg-white border border-amber-200 rounded p-2">
                      {po.rejection_reason}
                    </div>
                  )}
                  <Textarea
                    rows={3}
                    value={clarifyResp}
                    onChange={(e) => setClarifyResp(e.target.value)}
                    placeholder="Your response — provides the missing info / corrected amount / etc."
                    className="text-xs"
                    data-testid="po-clarification-response-input"
                  />
                  <Button
                    size="sm"
                    onClick={doRespondClarification}
                    disabled={saving || !clarifyResp.trim()}
                    className="bg-amber-700 hover:bg-amber-800 text-white text-xs"
                    data-testid="po-clarification-response-submit"
                  >
                    Send response · back to Pending Approval
                  </Button>
                </div>
              )}

              {/* Approval block */}
              {can.approve && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 space-y-2" data-testid="po-approval-block">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-blue-700 font-bold">Approval action</div>
                  <Textarea rows={2} value={actionNotes} onChange={(e) => setActionNotes(e.target.value)} placeholder="Approval / rejection notes" className="text-xs" data-testid="po-approval-notes" />
                  <div className="grid grid-cols-2 gap-2">
                    <Input placeholder="Manual PO # (optional)" value={manualPoNumber} onChange={(e) => setManualPoNumber(e.target.value)} className="text-xs" data-testid="po-approval-manual" />
                    <Input type="number" step="0.01" placeholder="Approved amount" value={approvedAmount} onChange={(e) => setApprovedAmount(e.target.value)} className="text-xs" data-testid="po-approval-amount" />
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <Button size="sm" onClick={() => doAction("approve")} disabled={saving} data-testid="po-approve-btn">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => doAction("clarify")} disabled={saving} data-testid="po-clarify-btn">
                      <MessageSquare className="w-3.5 h-3.5 mr-1" /> Clarify
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => doAction("reject")} disabled={saving} data-testid="po-reject-btn">
                      <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                    </Button>
                  </div>
                </div>
              )}

              {/* Admin actions */}
              {(can.close || can.cancel) && (
                <div className="flex gap-2 flex-wrap pt-2">
                  {can.close && (
                    <Button size="sm" variant="outline" onClick={async () => { setPo(await closePo(po.id)); toast.success("Closed"); }} data-testid="po-close-btn">
                      Mark Closed
                    </Button>
                  )}
                  {can.cancel && (
                    <Button size="sm" variant="outline" onClick={async () => { setPo(await cancelPo(po.id)); toast.success("Cancelled"); }} data-testid="po-cancel-btn">
                      Cancel
                    </Button>
                  )}
                </div>
              )}

              {(po.audit || []).length > 0 && (
                <div className="pt-3 border-t border-slate-200">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">History</div>
                  <ul className="space-y-1 text-[11px] text-slate-600">
                    {po.audit.slice().reverse().map((a, idx) => (
                      <li key={idx}>
                        <span className="font-mono text-slate-400">{new Date(a.at).toLocaleString()}</span>
                        {" · "}
                        <span className="font-bold">{a.action}</span>
                        {a.by?.name && ` · ${a.by.name}`}
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

function KV({ label, value, multiline }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">{label}</div>
      <div className={`text-slate-800 ${multiline ? "" : "truncate"}`}>{value || "—"}</div>
    </div>
  );
}
