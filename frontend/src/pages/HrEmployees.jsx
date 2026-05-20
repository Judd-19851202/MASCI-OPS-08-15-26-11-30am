// HrEmployees.jsx — Iter152 (Phase C). HR Portal employee lifecycle
// management. Route: /hr/employees.
//
// Capabilities:
//   * List employees with default = "actively employed" only.
//   * "Show inactive" toggle to surface Terminated / Retired / etc.
//   * Add Employee dialog.
//   * Click row → side drawer with Edit / Status / Offboarding Summary tabs.
//   * Auto-offboarding playbook fires server-side when status →
//     Terminated/Resigned/Retired.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Users, Plus, Search, ArrowLeft, Home, RefreshCw,
  UserCheck, UserMinus, Briefcase, AlertOctagon, CheckCircle2,
  ChevronRight, FileText, ClipboardList, Wrench,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import NotificationBell from "@/components/NotificationBell";
import {
  listHrEmployees, createHrEmployee, patchHrEmployee,
  changeHrEmployeeStatus, offboardingSummary, LIFECYCLE_STATUSES,
} from "@/lib/employeesApi";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import AccessDenied from "@/pages/AccessDenied";
import { toast } from "sonner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import GlobalSearch from "@/components/GlobalSearch";
import { LIFECYCLE_STATUS_TINTS } from "@/lib/statusBadges";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";

const SEPARATION_TYPES = ["voluntary", "involuntary", "layoff"];
const DRIVER_STATUSES = ["active", "suspended", "restricted", "inactive"];

const STATUS_COLORS = LIFECYCLE_STATUS_TINTS;

export default function HrEmployees() {
  const nav = useNavigate();
  const allowed = isHr() || isAdmin();
  const [showInactive, setShowInactive] = useRememberedFilter("hr.employees.show_inactive", false);
  const [statusFilter, setStatusFilter] = useRememberedFilter("hr.employees.status", "all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editId, setEditId] = useState(null);

  const fetchAll = useCallback(async () => {
    if (!allowed) { setLoading(false); return; }
    setLoading(true);
    try {
      const r = await listHrEmployees({
        show_inactive: showInactive,
        ...(statusFilter !== "all" ? { lifecycle_status: statusFilter } : {}),
        ...(q ? { q } : {}),
      });
      setItems(r.items || []);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load employees"));
    } finally { setLoading(false); }
  }, [allowed, showInactive, statusFilter, q]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const counts = useMemo(() => {
    const c = { active: 0, inactive: 0 };
    items.forEach((e) => {
      const s = e.lifecycle_status || (e.is_active === false ? "Inactive" : "Active");
      if (["Active", "Pending Hire", "Seasonal", "Leave of Absence"].includes(s)) c.active++;
      else c.inactive++;
    });
    return c;
  }, [items]);

  if (!allowed) return <AccessDenied attemptedPortal="hr" />;

  return (
    <div className="min-h-screen bg-slate-50" data-testid="hr-employees-page">
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link to="/" className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="hremp-nav-home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
          </Link>
          <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="hremp-nav-back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
          </button>
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-400 font-bold">HR · Employee Lifecycle</div>
            <div className="font-display text-lg sm:text-xl font-black text-white leading-tight">Employees</div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <GlobalSearch accent="dark" />
            <NotificationBell accent="white" />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        <HelpTipBlock formKey="employee-lifecycle" showCounter />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
          <SummaryTile label="Actively Employed" value={counts.active} icon={UserCheck} accent="emerald" />
          <SummaryTile label="Inactive / Off-roll" value={counts.inactive} icon={UserMinus} accent="slate" />
          <SummaryTile label="Total in View" value={items.length} icon={Users} accent="blue" />
        </div>

        <div className="bg-white border-2 border-slate-200 rounded-md p-3 sm:p-4 mb-4 flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2">
            <Switch
              id="show-inactive"
              checked={showInactive}
              onCheckedChange={setShowInactive}
              data-testid="hremp-show-inactive"
            />
            <Label htmlFor="show-inactive" className="text-xs cursor-pointer">
              Show inactive employees
            </Label>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px] h-9 text-xs" data-testid="hremp-status-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {LIFECYCLE_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <Input
              value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search name, employee id, trade…"
              className="pl-8 h-9 text-xs"
              data-testid="hremp-search-input"
            />
          </div>
          <Button variant="outline" size="sm" onClick={fetchAll} className="text-xs" data-testid="hremp-refresh">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <AddDialog open={addOpen} setOpen={setAddOpen} onSaved={(_e) => { setAddOpen(false); fetchAll(); }} />
        </div>

        {loading ? (
          <div className="bg-white border-2 border-slate-200 rounded-md py-10 text-center text-slate-500 text-sm">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No employees match the current filter"
            hint="Try clearing the search box, adjusting the status filter, or toggling Show Inactive."
            testId="hremp-empty"
          />
        ) : (
          <div className="bg-white border-2 border-slate-200 rounded-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Name</th>
                  <th className="px-4 py-2.5">Trade / Role</th>
                  <th className="px-4 py-2.5">Crew</th>
                  <th className="px-4 py-2.5">Supervisor</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((e) => {
                  const status = e.lifecycle_status || (e.is_active === false ? "Inactive" : "Active");
                  return (
                    <tr
                      key={e.id}
                      onClick={() => setEditId(e.id)}
                      className="hover:bg-slate-50 cursor-pointer"
                      data-testid={`hremp-row-${e.id}`}
                    >
                      <td className="px-4 py-2.5">
                        <StatusBadge kind="lifecycle" value={status} size="sm" />
                      </td>
                      <td className="px-4 py-2.5 font-bold text-slate-900">{e.name}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.trade || "—"} {e.role && <span className="text-slate-400">· {e.role}</span>}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.crew || "—"}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.supervisor || "—"}</td>
                      <td className="px-4 py-2.5"><ChevronRight className="w-4 h-4 text-slate-300" /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>

      <EmployeeDrawer id={editId} onClose={() => { setEditId(null); fetchAll(); }} />
    </div>
  );
}

function SummaryTile({ label, value, icon: Icon, accent }) {
  const palette = {
    emerald: "border-emerald-300 text-emerald-900",
    slate: "border-slate-300 text-slate-700",
    blue: "border-blue-300 text-blue-900",
  }[accent] || "border-slate-300 text-slate-900";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-3`} data-testid={`hremp-summary-${label.toLowerCase().replace(/\s+/g,'-')}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-80 font-bold">{label}</span>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

function AddDialog({ open, setOpen, onSaved }) {
  const [form, setForm] = useState({
    name: "", trade: "", role: "", crew: "", employee_id: "", email: "",
    phone: "", supervisor: "", department: "", default_project_number: "",
    lifecycle_status: "Active", hire_date: "",
  });
  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error("Name is required"); return; }
    try {
      const r = await createHrEmployee(form);
      toast.success(`Added ${r.name}`);
      onSaved(r);
      setForm({ ...form, name: "", employee_id: "", email: "", phone: "" });
    } catch (e2) { toast.error(friendlyError(e2, "Could not save employee")); }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="text-xs" data-testid="hremp-add-trigger">
          <Plus className="w-3.5 h-3.5 mr-1" /> Add Employee
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg" data-testid="hremp-add-dialog">
        <DialogHeader><DialogTitle>Add Employee</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="col-span-2">
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="hremp-add-name" />
            </div>
            <div>
              <Label>Employee ID</Label>
              <Input value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })} data-testid="hremp-add-empid" />
            </div>
            <div>
              <Label>Status</Label>
              <Select value={form.lifecycle_status} onValueChange={(v) => setForm({ ...form, lifecycle_status: v })}>
                <SelectTrigger data-testid="hremp-add-status"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {LIFECYCLE_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Trade</Label>
              <Input value={form.trade} onChange={(e) => setForm({ ...form, trade: e.target.value })} data-testid="hremp-add-trade" />
            </div>
            <div>
              <Label>Role / Title</Label>
              <Input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
            </div>
            <div>
              <Label>Crew</Label>
              <Input value={form.crew} onChange={(e) => setForm({ ...form, crew: e.target.value })} />
            </div>
            <div>
              <Label>Supervisor</Label>
              <Input value={form.supervisor} onChange={(e) => setForm({ ...form, supervisor: e.target.value })} />
            </div>
            <div>
              <Label>Department</Label>
              <Input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
            </div>
            <div>
              <Label>Hire Date</Label>
              <Input type="date" value={form.hire_date} onChange={(e) => setForm({ ...form, hire_date: e.target.value })} />
            </div>
            <div>
              <Label>Email</Label>
              <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <Label>Phone</Label>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
          </div>
          <DialogFooter><Button type="submit" data-testid="hremp-add-submit">Save</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EmployeeDrawer({ id, onClose }) {
  const { t } = useT();
  const [employee, setEmployee] = useState(null);
  const [summary, setSummary] = useState(null);
  const [tab, setTab] = useState("details");
  const [statusForm, setStatusForm] = useState({
    lifecycle_status: "Active",
    reason: "",
    separation_type: "",
    termination_date: "",
    last_day_worked: "",
    leave_start_date: "",
    expected_return_date: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) { setEmployee(null); setSummary(null); return; }
    offboardingSummary(id).then((s) => {
      setSummary(s);
      setEmployee(s.employee);
      setStatusForm({
        lifecycle_status: s.lifecycle_status || "Active",
        reason: "",
        separation_type: "",
        termination_date: "",
        last_day_worked: "",
        leave_start_date: "",
        expected_return_date: "",
      });
    }).catch(() => setEmployee(null));
  }, [id]);

  const submitStatusChange = async () => {
    if (!employee) return;
    const isOffboarding = ["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status);
    const wasOffboarded = ["Terminated", "Resigned", "Retired"].includes(summary?.lifecycle_status);
    const offboardingTransition = isOffboarding && !wasOffboarded;
    if (offboardingTransition && !statusForm.separation_type && !employee.separation_type) {
      toast.error(t("Pick a separation type — voluntary, involuntary, or layoff"));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        lifecycle_status: statusForm.lifecycle_status,
        reason: statusForm.reason,
      };
      if (statusForm.separation_type) payload.separation_type = statusForm.separation_type;
      if (statusForm.termination_date) payload.termination_date = statusForm.termination_date;
      if (statusForm.last_day_worked) payload.last_day_worked = statusForm.last_day_worked;
      if (statusForm.leave_start_date) payload.leave_start_date = statusForm.leave_start_date;
      if (statusForm.expected_return_date) payload.expected_return_date = statusForm.expected_return_date;
      const r = await changeHrEmployeeStatus(employee.id, statusForm.lifecycle_status, statusForm.reason, payload);
      if (r.playbook_fired) {
        toast.success(`${t("Status updated")} · ${r.tasks_created} ${t("offboarding tasks created")}`);
      } else {
        toast.success(t("Status updated"));
      }
      const s = await offboardingSummary(employee.id);
      setSummary(s);
      setEmployee(s.employee);
    } catch (e) {
      toast.error(friendlyError(e, t("Status change failed")));
    } finally { setSaving(false); }
  };

  const submitEdit = async (patch) => {
    if (!employee) return;
    setSaving(true);
    try {
      const r = await patchHrEmployee(employee.id, patch);
      setEmployee(r);
      toast.success(t("Employee updated"));
    } catch (e) { toast.error(friendlyError(e, t("Update failed"))); }
    finally { setSaving(false); }
  };

  return (
    <Sheet open={!!id} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 flex flex-col" data-testid="hremp-drawer">
        {!employee ? (
          <div className="p-6 text-slate-500 text-sm">Loading…</div>
        ) : (
          <>
            <SheetHeader className="px-5 pt-5 pb-3 border-b border-slate-200">
              <SheetTitle className="font-display text-base leading-snug">{employee.name}</SheetTitle>
              <div className="flex items-center gap-2 mt-2 flex-wrap text-xs">
                <StatusBadge kind="lifecycle" value={summary?.lifecycle_status} size="sm" />
                {employee.trade && <span className="text-slate-600">{employee.trade}</span>}
                {employee.employee_id && <span className="text-slate-500 font-mono text-[10px]">#{employee.employee_id}</span>}
              </div>
            </SheetHeader>
            <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col">
              <TabsList className="rounded-none border-b border-slate-200 px-5">
                <TabsTrigger value="details" data-testid="hremp-tab-details">Details</TabsTrigger>
                <TabsTrigger value="status" data-testid="hremp-tab-status">Status</TabsTrigger>
                <TabsTrigger value="offboarding" data-testid="hremp-tab-offboarding">Offboarding Summary</TabsTrigger>
              </TabsList>
              <div className="flex-1 overflow-y-auto px-5 py-4 text-sm">
                <TabsContent value="details" className="mt-0 space-y-3">
                  <EditField label="Trade" value={employee.trade} save={(v) => submitEdit({ trade: v })} testid="hremp-edit-trade" />
                  <EditField label="Role / Title" value={employee.role} save={(v) => submitEdit({ role: v })} />
                  <EditField label="Crew" value={employee.crew} save={(v) => submitEdit({ crew: v })} />
                  <EditField label="Supervisor" value={employee.supervisor} save={(v) => submitEdit({ supervisor: v })} />
                  <EditField label="Department" value={employee.department} save={(v) => submitEdit({ department: v })} />
                  <EditField label="Default Project #" value={employee.default_project_number} save={(v) => submitEdit({ default_project_number: v })} />
                  <EditField label="Email" value={employee.email} save={(v) => submitEdit({ email: v })} />
                  <EditField label="Phone" value={employee.phone} save={(v) => submitEdit({ phone: v })} />
                  <EditField label="Hire Date" value={employee.hire_date} save={(v) => submitEdit({ hire_date: v })} />

                  <div className="pt-3 border-t border-slate-200">
                    <HelpTipBlock formKey="employee-lifecycle.lifecycle-dates" />
                  </div>
                  <EditField
                    label={t("Original Hire Date") + (employee.original_hire_date ? " · " + t("write-once · already set") : "")}
                    value={employee.original_hire_date}
                    save={(v) => submitEdit({ original_hire_date: v })}
                    testid="hremp-edit-original-hire"
                  />
                  {employee.tenure_days != null && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-tenure">
                      <span className="text-slate-600">{t("Tenure")}</span>
                      <span className="font-mono text-slate-900 font-bold">
                        {employee.tenure_days} {t("days")}
                        {employee.tenure_days >= 365 && (
                          <span className="text-slate-500 ml-2">({Math.floor(employee.tenure_days / 365)} {t("yr")})</span>
                        )}
                      </span>
                    </div>
                  )}
                  <EditField label={t("Last Day Worked")} value={employee.last_day_worked} save={(v) => submitEdit({ last_day_worked: v })} testid="hremp-edit-last-day" />
                  <EditField label={t("Termination Date")} value={employee.termination_date} save={(v) => submitEdit({ termination_date: v })} testid="hremp-edit-term-date" />
                  <EditField label={t("Leave Start Date")} value={employee.leave_start_date} save={(v) => submitEdit({ leave_start_date: v })} testid="hremp-edit-leave-start" />
                  <EditField label={t("Expected Return Date")} value={employee.expected_return_date} save={(v) => submitEdit({ expected_return_date: v })} testid="hremp-edit-leave-return" />
                  {employee.separation_type && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-separation-type-display">
                      <span className="text-slate-600">{t("Separation Type")}</span>
                      <span className="font-mono text-slate-900 font-bold uppercase">{t(employee.separation_type)}</span>
                    </div>
                  )}

                  {/* iter286 · Driver Qualification card */}
                  <div className="pt-3 mt-3 border-t border-slate-200" data-testid="hremp-driver-qualification">
                    <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("Driver Qualification")}</h4>
                    <HelpTipBlock formKey="driver-qualification" />
                    <HelpTipBlock formKey="driver-qualification.cdl-vs-approved" />

                    <div className="flex items-center justify-between py-2 border-b border-slate-100">
                      <Label htmlFor="cdl-holder-switch" className="text-sm">{t("CDL Holder")}</Label>
                      <Switch
                        id="cdl-holder-switch"
                        checked={Boolean(employee.cdl_holder)}
                        onCheckedChange={(v) => submitEdit({ cdl_holder: v })}
                        data-testid="hremp-cdl-holder"
                      />
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-slate-100">
                      <Label htmlFor="approved-driver-switch" className="text-sm">{t("Approved Company Driver")}</Label>
                      <Switch
                        id="approved-driver-switch"
                        checked={Boolean(employee.approved_company_driver)}
                        onCheckedChange={(v) => submitEdit({ approved_company_driver: v })}
                        data-testid="hremp-approved-driver"
                      />
                    </div>
                    {employee.approved_company_driver && (
                      <div className="py-2">
                        <Label className="text-sm">{t("Driver Status")}</Label>
                        <Select value={employee.driver_status || ""} onValueChange={(v) => submitEdit({ driver_status: v })}>
                          <SelectTrigger data-testid="hremp-driver-status"><SelectValue placeholder={t("Pick a status")} /></SelectTrigger>
                          <SelectContent>
                            {DRIVER_STATUSES.map((s) => (<SelectItem key={s} value={s}>{t(s)}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                    <EditField label={t("CDL License Number")} value={employee.cdl_license_number} save={(v) => submitEdit({ cdl_license_number: v })} testid="hremp-cdl-number" />
                    <EditField label={t("CDL State")} value={employee.cdl_state} save={(v) => submitEdit({ cdl_state: v })} testid="hremp-cdl-state" />
                    <HelpTipBlock formKey="driver-qualification.expirations" />
                    <EditField label={t("CDL Expiration Date")} value={employee.cdl_expiration_date} save={(v) => submitEdit({ cdl_expiration_date: v })} testid="hremp-cdl-exp" />
                    <EditField label={t("Medical Card Expiration Date")} value={employee.medical_card_expiration_date} save={(v) => submitEdit({ medical_card_expiration_date: v })} testid="hremp-med-card-exp" />
                  </div>
                </TabsContent>
                <TabsContent value="status" className="mt-0 space-y-3">
                  <HelpTipBlock formKey="employee-lifecycle.separation" />
                  <div>
                    <Label>{t("New status")}</Label>
                    <Select value={statusForm.lifecycle_status} onValueChange={(v) => setStatusForm({ ...statusForm, lifecycle_status: v })}>
                      <SelectTrigger data-testid="hremp-status-new"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {LIFECYCLE_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                  {["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status) && (
                    <div data-testid="hremp-separation-section" className="space-y-2 bg-slate-50 border border-slate-200 rounded-md p-3">
                      <div>
                        <Label>{t("Separation Type")} *</Label>
                        <Select value={statusForm.separation_type} onValueChange={(v) => setStatusForm({ ...statusForm, separation_type: v })}>
                          <SelectTrigger data-testid="hremp-separation-type"><SelectValue placeholder={t("Pick a type")} /></SelectTrigger>
                          <SelectContent>
                            {SEPARATION_TYPES.map((s) => (<SelectItem key={s} value={s}>{t(s)}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <Label>{t("Last Day Worked")}</Label>
                          <Input type="date" value={statusForm.last_day_worked} onChange={(e) => setStatusForm({ ...statusForm, last_day_worked: e.target.value })} data-testid="hremp-tx-last-day" />
                        </div>
                        <div>
                          <Label>{t("Termination Date")}</Label>
                          <Input type="date" value={statusForm.termination_date} onChange={(e) => setStatusForm({ ...statusForm, termination_date: e.target.value })} data-testid="hremp-tx-term-date" />
                        </div>
                      </div>
                    </div>
                  )}
                  {statusForm.lifecycle_status === "Leave of Absence" && (
                    <div data-testid="hremp-leave-section" className="space-y-2 bg-slate-50 border border-slate-200 rounded-md p-3">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <Label>{t("Leave Start Date")}</Label>
                          <Input type="date" value={statusForm.leave_start_date} onChange={(e) => setStatusForm({ ...statusForm, leave_start_date: e.target.value })} data-testid="hremp-tx-leave-start" />
                        </div>
                        <div>
                          <Label>{t("Expected Return Date")}</Label>
                          <Input type="date" value={statusForm.expected_return_date} onChange={(e) => setStatusForm({ ...statusForm, expected_return_date: e.target.value })} data-testid="hremp-tx-leave-return" />
                        </div>
                      </div>
                    </div>
                  )}
                  <div>
                    <Label>{t("Reason / note")}</Label>
                    <Textarea
                      rows={3}
                      value={statusForm.reason}
                      onChange={(e) => setStatusForm({ ...statusForm, reason: e.target.value })}
                      placeholder={t("Optional context recorded in status history")}
                      data-testid="hremp-status-reason"
                    />
                  </div>
                  {["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status) &&
                    !["Terminated", "Resigned", "Retired"].includes(summary?.lifecycle_status) && (
                    <div className="bg-amber-50 border border-amber-300 rounded-md p-3 text-xs text-amber-900" data-testid="hremp-playbook-warning">
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        <AlertOctagon className="w-3.5 h-3.5" /> Offboarding playbook will fire
                      </div>
                      This status change will create 8 follow-up tasks across HR, Shop, Admin, Safety, and PM.
                    </div>
                  )}
                  <Button onClick={submitStatusChange} disabled={saving} data-testid="hremp-status-save">
                    {saving ? "Saving…" : "Update status"}
                  </Button>

                  {summary?.last_status_change && (
                    <div className="mt-4 pt-3 border-t border-slate-200">
                      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">Recent status history</div>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {(employee.status_history || []).slice().reverse().slice(0, 5).map((h, idx) => (
                          <li key={idx} className="font-mono">
                            <span className="text-slate-500">{new Date(h.at).toLocaleString()}</span>
                            {" · "}
                            {h.from && <>{h.from} → </>}
                            <span className="font-bold text-slate-900">{h.to}</span>
                            {h.reason && <span className="text-slate-500"> · {h.reason}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </TabsContent>
                <TabsContent value="offboarding" className="mt-0 space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <MiniStat label="Open tasks" value={summary?.open_tasks_count ?? 0} icon={ClipboardList} accent="amber" />
                    <MiniStat label="Documents" value={summary?.document_expirations_count ?? 0} icon={FileText} accent="rose" />
                    <MiniStat label="Equipment" value={summary?.equipment_issuances_count ?? 0} icon={Wrench} accent="blue" />
                  </div>
                  <Section title={`Open Tasks (${summary?.open_tasks_count ?? 0})`}>
                    {(summary?.open_tasks || []).length === 0 ? (
                      <Empty msg="No open tasks — clean." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.open_tasks.slice(0, 20).map((t) => (
                          <li key={t.id} className="bg-slate-50 rounded-md px-3 py-2">
                            <Link to={`/tasks?id=${t.id}`} className="text-xs font-bold text-slate-900 hover:text-red-700" data-testid={`hremp-open-task-${t.id}`}>
                              {t.title}
                            </Link>
                            <div className="font-mono text-[10px] text-slate-500 mt-0.5">{t.priority} · {t.status} · {t.source_module}</div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Document Expirations (${summary?.document_expirations_count ?? 0})`}>
                    {(summary?.document_expirations || []).length === 0 ? (
                      <Empty msg="No tracked expirations." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.document_expirations.slice(0, 20).map((d) => (
                          <li key={d.id} className="bg-slate-50 rounded-md px-3 py-2 flex items-center justify-between">
                            <div>
                              <div className="text-xs font-bold text-slate-900">{d.document_type}</div>
                              <div className="font-mono text-[10px] text-slate-500">{d.status} · expires {d.expiration_date}</div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Equipment Issuances (${summary?.equipment_issuances_count ?? 0})`}>
                    {(summary?.equipment_issuances || []).length === 0 ? (
                      <Empty msg="No equipment currently assigned." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.equipment_issuances.slice(0, 20).map((e) => (
                          <li key={e.id} className="bg-slate-50 rounded-md px-3 py-2 text-xs font-mono">
                            {e.unit_number || e.name || e.id}
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Open POs (${summary?.open_pos_count ?? 0})`}>
                    {(summary?.open_pos || []).length === 0 ? (
                      <Empty msg="No open PO requests." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.open_pos.slice(0, 20).map((p) => (
                          <li key={p.id} className="bg-slate-50 rounded-md px-3 py-2">
                            <Link to={`/po-requests?id=${p.id}`} className="text-xs font-bold text-slate-900 hover:text-red-700 font-mono" data-testid={`hremp-open-po-${p.id}`}>
                              {p.po_number || p.id.slice(0, 8)}
                            </Link>
                            <div className="font-mono text-[10px] text-slate-500">{p.vendor} · {p.status} · ${(p.approved_amount ?? p.estimated_amount ?? 0).toFixed(2)}</div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                </TabsContent>
              </div>
            </Tabs>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

function EditField({ label, value, save, testid }) {
  const [v, setV] = useState(value || "");
  useEffect(() => { setV(value || ""); }, [value]);
  const dirty = v !== (value || "");
  return (
    <div className="flex items-end gap-2">
      <div className="flex-1">
        <Label className="text-[11px]">{label}</Label>
        <Input value={v} onChange={(e) => setV(e.target.value)} className="h-9 text-xs" data-testid={testid} />
      </div>
      {dirty && (
        <Button size="sm" onClick={() => save(v)} className="h-9 text-xs">Save</Button>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5 flex items-center gap-1.5">
        <Briefcase className="w-3 h-3" /> {title}
      </div>
      {children}
    </div>
  );
}

function Empty({ msg, accent }) {
  const cls = accent === "emerald" ? "border-emerald-200 text-emerald-700" : "border-slate-200 text-slate-500";
  return (
    <div className={`text-center py-3 text-xs border rounded-md ${cls}`}>
      <CheckCircle2 className="w-4 h-4 inline-block mr-1 align-middle" /> {msg}
    </div>
  );
}

function MiniStat({ label, value, icon: Icon, accent }) {
  const palette = {
    amber: "border-amber-300 text-amber-900",
    rose: "border-rose-300 text-rose-900",
    blue: "border-blue-300 text-blue-900",
  }[accent] || "border-slate-300";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-2.5`}>
      <div className="flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 opacity-70" />
        <span className="font-mono text-[9px] uppercase tracking-[0.18em] font-bold opacity-80">{label}</span>
      </div>
      <div className="font-display text-xl font-black mt-0.5 leading-none">{value}</div>
    </div>
  );
}
