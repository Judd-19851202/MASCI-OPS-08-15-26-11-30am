// SafetyCorrectiveActions — Phase 2 CRUD UI for /api/safety/corrective-actions
//
// Status pipeline: Open → In Progress → Pending Review → Closed.
// Cards are filtered by status tab. Each row supports inline status
// progression + a "View / Edit" dialog for full edit (assignment,
// priority, due date, completion notes). The "New CA" button on the
// shell opens the same dialog in create mode.
//
// Source links: every CA references a source kind (incident / audit /
// inspection / training / meeting / manual) + optional source_id so
// admins can click straight to the originating record once the
// cross-link routes are wired in Phase 5.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  AlertOctagon, Plus, Loader2, Pencil, Trash2, Save, X,
  CheckCircle2, Clock, AlertTriangle, Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import SafetyShell from "@/components/SafetyShell";
import SafetyCaLinksManager from "@/components/SafetyCaLinksManager";
import { useT } from "@/lib/i18n";
import { getSafetyToken } from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const STATUS_OPTIONS = ["Open", "In Progress", "Pending Review", "Closed"];
const STATUS_COLORS = {
  Open:             { dot: "bg-red-600",     pill: "bg-red-100 text-red-800 border-red-300" },
  "In Progress":    { dot: "bg-amber-500",   pill: "bg-amber-100 text-amber-900 border-amber-300" },
  "Pending Review": { dot: "bg-blue-600",    pill: "bg-blue-100 text-blue-800 border-blue-300" },
  Closed:           { dot: "bg-emerald-600", pill: "bg-emerald-100 text-emerald-900 border-emerald-300" },
};
const PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"];
const PRIORITY_COLORS = {
  Low:      "bg-slate-100 text-slate-700 border-slate-300",
  Medium:   "bg-blue-100 text-blue-800 border-blue-300",
  High:     "bg-amber-100 text-amber-900 border-amber-300",
  Critical: "bg-red-200 text-red-900 border-red-400",
};
const SOURCE_OPTIONS = [
  { value: "incident",   label: "Incident / Near Miss" },
  { value: "inspection", label: "Site Inspection" },
  { value: "audit",      label: "Safety Audit" },
  { value: "meeting",    label: "Safety Meeting" },
  { value: "training",   label: "Training Deficiency" },
  { value: "manual",     label: "Manual / Other" },
];

const blankForm = () => ({
  title: "",
  description: "",
  source_kind: "manual",
  source_id: "",
  project_number: "",
  assigned_to_name: "",
  assigned_to_email: "",
  priority: "Medium",
  due_date: "",
  notes: "",
  completion_notes: "",
});

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

function StatusPill({ status }) {
  const c = STATUS_COLORS[status] || STATUS_COLORS.Open;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${c.pill}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {status}
    </span>
  );
}

function PriorityPill({ priority }) {
  const cls = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Medium;
  return (
    <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.18em] font-bold ${cls}`}>
      {priority || "Medium"}
    </span>
  );
}

function isOverdue(ca) {
  if (!ca.due_date) return false;
  if (ca.status === "Closed") return false;
  return ca.due_date < new Date().toISOString().slice(0, 10);
}

export default function SafetyCorrectiveActions() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("All");
  const [search, setSearch] = useState("");
  const [dlg, setDlg] = useState({ open: false, mode: "create", form: blankForm(), id: null });
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/safety/corrective-actions`, auth());
      setItems(Array.isArray(r.data) ? r.data : []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load corrective actions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const counts = useMemo(() => {
    const c = { All: items.length, Overdue: 0 };
    STATUS_OPTIONS.forEach((s) => { c[s] = 0; });
    items.forEach((it) => {
      c[it.status] = (c[it.status] || 0) + 1;
      if (isOverdue(it)) c.Overdue += 1;
    });
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    let list = items;
    if (tab === "Overdue") list = list.filter(isOverdue);
    else if (tab !== "All") list = list.filter((it) => it.status === tab);
    if (search.trim()) {
      const s = search.trim().toLowerCase();
      list = list.filter((it) =>
        (it.title || "").toLowerCase().includes(s)
        || (it.project_number || "").toLowerCase().includes(s)
        || (it.assigned_to_name || "").toLowerCase().includes(s)
        || (it.description || "").toLowerCase().includes(s),
      );
    }
    return list;
  }, [items, tab, search]);

  const openCreate = () => {
    setDlg({ open: true, mode: "create", form: blankForm(), id: null });
  };

  const openEdit = (ca) => {
    setDlg({
      open: true,
      mode: "edit",
      id: ca.id,
      form: {
        ...blankForm(),
        ...ca,
        due_date: ca.due_date || "",
      },
    });
  };

  const closeDlg = () => setDlg((d) => ({ ...d, open: false }));

  const save = async () => {
    const f = dlg.form;
    if (!f.title || f.title.trim().length < 3) {
      toast.error("Title is required (3+ characters)");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: f.title.trim(),
        description: f.description || "",
        source_kind: f.source_kind || "manual",
        source_id: f.source_id || null,
        project_number: f.project_number || "",
        assigned_to_name: f.assigned_to_name || "",
        assigned_to_email: f.assigned_to_email || "",
        priority: f.priority || "Medium",
        due_date: f.due_date || null,
        notes: f.notes || "",
      };
      if (dlg.mode === "create") {
        await axios.post(`${API}/safety/corrective-actions`, payload, auth());
        toast.success("Corrective action created");
      } else {
        await axios.patch(
          `${API}/safety/corrective-actions/${dlg.id}`,
          { ...payload, status: f.status, completion_notes: f.completion_notes || "" },
          auth(),
        );
        toast.success("Corrective action updated");
      }
      closeDlg();
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const advanceStatus = async (ca, nextStatus) => {
    try {
      await axios.patch(
        `${API}/safety/corrective-actions/${ca.id}`,
        { status: nextStatus },
        auth(),
      );
      toast.success(`Moved to ${nextStatus}`);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Status change failed");
    }
  };

  const removeCa = async (ca) => {
    if (!window.confirm(`Delete corrective action “${ca.title}”? This cannot be undone.`)) return;
    try {
      await axios.delete(`${API}/safety/corrective-actions/${ca.id}`, auth());
      toast.success("Deleted");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const TABS = [
    { id: "All",            label: "All",            count: counts.All },
    { id: "Open",           label: "Open",           count: counts.Open || 0 },
    { id: "In Progress",    label: "In Progress",    count: counts["In Progress"] || 0 },
    { id: "Pending Review", label: "Pending Review", count: counts["Pending Review"] || 0 },
    { id: "Closed",         label: "Closed",         count: counts.Closed || 0 },
    { id: "Overdue",        label: "Overdue",        count: counts.Overdue || 0, danger: true },
  ];

  return (
    <SafetyShell title="Corrective Actions" kicker="SAFETY · CORRECTIVE ACTION REGISTER">
      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm sm:text-base max-w-2xl leading-relaxed">
          {t("Track every safety deficiency to resolution. Auto-link CAs to incidents, audits, inspections, training records, and meetings. The pipeline is")}{" "}
          <span className="font-mono text-xs uppercase tracking-[0.18em] font-bold">{t("Open → In Progress → Pending Review → Closed")}</span>.
        </p>
        <Button
          onClick={openCreate}
          className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-11 shrink-0"
          data-testid="safety-ca-new"
        >
          <Plus className="w-4 h-4 mr-1" /> {t("New Corrective Action")}
        </Button>
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2 mb-4 border-b-2 border-slate-200 pb-3">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold border-2 transition-colors ${
              tab === t.id
                ? (t.danger ? "bg-red-600 text-white border-red-700" : "bg-cyan-700 text-white border-cyan-800")
                : (t.danger ? "bg-white text-red-700 border-red-200 hover:border-red-400" : "bg-white text-slate-700 border-slate-200 hover:border-slate-400")
            }`}
            data-testid={`safety-ca-tab-${t.id.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {t.label} <span className="opacity-70">({t.count})</span>
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Input
          placeholder={t("Filter by title, project, assignee, description…")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={`${inputCls} max-w-md`}
          data-testid="safety-ca-search"
        />
      </div>

      {/* List */}
      {loading ? (
        <div className="text-center text-slate-500 py-12">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" /> {t("Loading…")}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-slate-500 py-12 border-2 border-dashed border-slate-200 rounded-md">
          <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-slate-400" />
          <div className="font-display text-lg font-black text-slate-700">{t("No corrective actions")}</div>
          <p className="text-sm mt-1">{tab === "All" ? t("Create the first one with the button above.") : t("Try a different filter.")}</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="safety-ca-list">
          {filtered.map((ca) => (
            <div
              key={ca.id}
              className={`bg-white border-2 rounded-md p-4 sm:p-5 ${isOverdue(ca) ? "border-red-400" : "border-slate-200"}`}
              data-testid={`safety-ca-row-${ca.id}`}
            >
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <StatusPill status={ca.status || "Open"} />
                    <PriorityPill priority={ca.priority} />
                    {isOverdue(ca) && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.18em] font-bold bg-red-600 text-white border-red-700">
                        <AlertTriangle className="w-3 h-3" /> {t("Overdue")}
                      </span>
                    )}
                    {ca.source_kind && ca.source_kind !== "manual" && (
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-mono uppercase tracking-[0.18em] font-bold">
                        {SOURCE_OPTIONS.find((s) => s.value === ca.source_kind)?.label || ca.source_kind}
                      </span>
                    )}
                  </div>
                  <h3 className="font-display text-lg font-black text-slate-900">{ca.title}</h3>
                  {ca.description && (
                    <p className="text-sm text-slate-600 mt-1 leading-relaxed line-clamp-2">{ca.description}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-2">
                    {ca.project_number && <span><strong>{t("Project")}:</strong> {ca.project_number}</span>}
                    {ca.assigned_to_name && <span><strong>{t("Assigned")}:</strong> {ca.assigned_to_name}</span>}
                    {ca.due_date && <span><strong>{t("Due")}:</strong> {ca.due_date}</span>}
                    {ca.created_by_name && <span><strong>{t("By")}:</strong> {ca.created_by_name}</span>}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-1 shrink-0">
                  {ca.status === "Open" && (
                    <Button size="sm" variant="outline" onClick={() => advanceStatus(ca, "In Progress")} className="h-9 border-amber-300 text-amber-800" data-testid={`safety-ca-start-${ca.id}`}>
                      <Clock className="w-3.5 h-3.5 mr-1" /> {t("Start")}
                    </Button>
                  )}
                  {ca.status === "In Progress" && (
                    <Button size="sm" variant="outline" onClick={() => advanceStatus(ca, "Pending Review")} className="h-9 border-blue-300 text-blue-800" data-testid={`safety-ca-review-${ca.id}`}>
                      {t("Submit for Review")}
                    </Button>
                  )}
                  {ca.status === "Pending Review" && (
                    <Button size="sm" variant="outline" onClick={() => advanceStatus(ca, "Closed")} className="h-9 border-emerald-300 text-emerald-800" data-testid={`safety-ca-close-${ca.id}`}>
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> {t("Close")}
                    </Button>
                  )}
                  <Button size="sm" variant="outline" onClick={() => openEdit(ca)} className="h-9" data-testid={`safety-ca-edit-${ca.id}`}>
                    <Pencil className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => removeCa(ca)} className="h-9 border-red-300 text-red-700 hover:bg-red-50" data-testid={`safety-ca-delete-${ca.id}`}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit dialog */}
      <Dialog open={dlg.open} onOpenChange={(o) => !o && closeDlg()}>
        <DialogContent className="sm:max-w-2xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {dlg.mode === "create" ? t("New corrective action") : t("Edit corrective action")}
            </DialogTitle>
            <DialogDescription>
              {t("Link to a source record (incident, audit, inspection, training, meeting) and assign a responsible party.")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Title")} *</Label>
              <Input
                value={dlg.form.title}
                onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, title: e.target.value } }))}
                className={`${inputCls} mt-1`}
                placeholder={t("Short summary — e.g. Install missing fire extinguisher at job 220")}
                data-testid="safety-ca-form-title"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Description")}</Label>
              <Textarea
                value={dlg.form.description}
                onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, description: e.target.value } }))}
                className="text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700 mt-1"
                rows={3}
                placeholder={t("What needs to happen and why?")}
                data-testid="safety-ca-form-desc"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Source")}</Label>
                <Select
                  value={dlg.form.source_kind}
                  onValueChange={(v) => setDlg((d) => ({ ...d, form: { ...d.form, source_kind: v } }))}
                >
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-ca-form-source"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SOURCE_OPTIONS.map((s) => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Source record ID")}</Label>
                <Input
                  value={dlg.form.source_id || ""}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, source_id: e.target.value } }))}
                  className={`${inputCls} mt-1`}
                  placeholder={t("Optional — paste record ID")}
                  data-testid="safety-ca-form-source-id"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Project number")}</Label>
                <Input
                  value={dlg.form.project_number}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, project_number: e.target.value } }))}
                  className={`${inputCls} mt-1`}
                  data-testid="safety-ca-form-project"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Priority")}</Label>
                <Select
                  value={dlg.form.priority}
                  onValueChange={(v) => setDlg((d) => ({ ...d, form: { ...d.form, priority: v } }))}
                >
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-ca-form-priority"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {PRIORITY_OPTIONS.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Assigned to (name)")}</Label>
                <Input
                  value={dlg.form.assigned_to_name}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, assigned_to_name: e.target.value } }))}
                  className={`${inputCls} mt-1`}
                  data-testid="safety-ca-form-assignee-name"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Assigned to (email)")}</Label>
                <Input
                  type="email"
                  value={dlg.form.assigned_to_email}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, assigned_to_email: e.target.value } }))}
                  className={`${inputCls} mt-1`}
                  data-testid="safety-ca-form-assignee-email"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Due date")}</Label>
                <Input
                  type="date"
                  value={dlg.form.due_date || ""}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, due_date: e.target.value } }))}
                  className={`${inputCls} mt-1`}
                  data-testid="safety-ca-form-due"
                />
              </div>
              {dlg.mode === "edit" && (
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Status")}</Label>
                  <Select
                    value={dlg.form.status || "Open"}
                    onValueChange={(v) => setDlg((d) => ({ ...d, form: { ...d.form, status: v } }))}
                  >
                    <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-ca-form-status"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {STATUS_OPTIONS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Notes")}</Label>
              <Textarea
                value={dlg.form.notes}
                onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, notes: e.target.value } }))}
                className="text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700 mt-1"
                rows={2}
                data-testid="safety-ca-form-notes"
              />
            </div>
            {dlg.mode === "edit" && (
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Completion notes")}</Label>
                <Textarea
                  value={dlg.form.completion_notes || ""}
                  onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, completion_notes: e.target.value } }))}
                  className="text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700 mt-1"
                  rows={2}
                  placeholder={t("Required to mark as Closed — what was done and when?")}
                  data-testid="safety-ca-form-completion"
                />
              </div>
            )}
            {dlg.mode === "edit" && dlg.id && (
              <SafetyCaLinksManager caId={dlg.id} />
            )}
          </div>
          <DialogFooter className="pt-3 gap-2">
            <Button variant="outline" onClick={closeDlg} disabled={saving} data-testid="safety-ca-form-cancel">
              <X className="w-4 h-4 mr-1" /> {t("Cancel")}
            </Button>
            <Button
              onClick={save}
              disabled={saving}
              className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide"
              data-testid="safety-ca-form-save"
            >
              {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
              {t("Save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </SafetyShell>
  );
}
