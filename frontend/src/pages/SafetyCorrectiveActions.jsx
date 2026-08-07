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
import React, { useCallback, useEffect, useMemo, useState } from "react";
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
import SignatureCapture from "@/components/SignatureCapture";
import MasterLookupCombobox from "@/components/MasterLookupCombobox";
import EmployeeRosterField from "@/components/EmployeeRosterField";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { HelpTip } from "@/components/ui/HelpTip";
import { HelpTipBlock } from "@/components/HelpTip";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { Link, useLocation } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { translateUserInput, persistBilingualSidecar } from "@/lib/translateOnSubmit";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { WhyItMattersPanel } from "@/components/guidance";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { ClipboardCheck } from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: buildScopedPortalAuthHeaders(["safety"]) });

const STATUS_OPTIONS = ["Open", "In Progress", "Pending Review", "Verified", "Closed"];
const STATUS_COLORS = {
  Open:             { dot: "bg-red-600",     pill: "bg-red-100 text-red-800 border-red-300" },
  "In Progress":    { dot: "bg-amber-500",   pill: "bg-amber-100 text-amber-900 border-amber-300" },
  "Pending Review": { dot: "bg-blue-600",    pill: "bg-blue-100 text-blue-800 border-blue-300" },
  Verified:         { dot: "bg-violet-600",  pill: "bg-violet-100 text-violet-900 border-violet-300" },
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
  // iter138 master-record bindings (kept optional — freetext OK)
  equipment_master_id: "",
  equipment_master_label: "",
  employee_master_id: "",
  employee_master_label: "",
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
  const { t, lang } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  // iter148 — remember the status tab + search per user across visits
  const [tab, setTab] = useRememberedFilter("safety.ca.status-tab", "All");
  const [search, setSearch] = useRememberedFilter("safety.ca.search", "");
  // iter139 — filter by linked master record
  const [filterEqId, setFilterEqId] = useState("");
  const [filterEqLabel, setFilterEqLabel] = useState("");
  const [filterEmpId, setFilterEmpId] = useState("");
  const [filterEmpLabel, setFilterEmpLabel] = useState("");
  const [dlg, setDlg] = useState({ open: false, mode: "create", form: blankForm(), id: null });
  const [saving, setSaving] = useState(false);

  // Phase 5D · P1 — accept query-param pre-fill from ViewIncident
  // ("Open Follow-Up CAPA" CTA). Auto-opens the create dialog with
  // source_kind/source_id/title prefilled, then strips the params so
  // a manual refresh doesn't re-open the dialog endlessly.
  const _location = useLocation();
  useEffect(() => {
    const sp = new URLSearchParams(_location.search);
    const srcKind = sp.get("source_kind");
    const srcId = sp.get("source_id");
    if (!srcKind && !srcId) return;
    const presetTitle = sp.get("title") || "";
    setDlg({
      open: true,
      mode: "create",
      id: null,
      form: {
        ...blankForm(),
        source_kind: srcKind || "manual",
        source_id: srcId || "",
        title: presetTitle,
      },
    });
    // Synchronous URL cleanup — replaces history entry without re-rendering.
    if (typeof window !== "undefined" && window.history?.replaceState) {
      window.history.replaceState(window.history.state, "", _location.pathname);
    }

  }, [_location.pathname, _location.search]);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterEqId) params.equipment_master_id = filterEqId;
      if (filterEmpId) params.employee_master_id = filterEmpId;
      const r = await axios.get(`${API}/safety/corrective-actions`, { ...auth(), params });
      setItems(Array.isArray(r.data) ? r.data : []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load corrective actions");
    } finally {
      setLoading(false);
    }
  }, [filterEmpId, filterEqId]);

  useEffect(() => { refresh(); }, [refresh]);

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
        // iter138 — preserve existing bindings; clear labels since we
        // only persist IDs server-side. The combobox shows "Linked"
        // badge from the id alone; user can re-search to see the label.
        equipment_master_id: ca.equipment_master_id || "",
        equipment_master_label: "",
        employee_master_id: ca.employee_master_id || "",
        employee_master_label: "",
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
      const rawPayload = {
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
        completion_notes: f.completion_notes || "",
        // iter138 — preserve master bindings on every save (empty = freetext OK)
        equipment_master_id: f.equipment_master_id || "",
        employee_master_id: f.employee_master_id || "",
      };
      // TRACK 14.0-S1-B4 — translate Spanish free text (title/description/
      // notes) to English BEFORE writing the canonical record so the office
      // sees English in PDFs / notifications / search / exports.
      const translated = await translateUserInput(rawPayload, lang);
      const payload = { ...translated };
      delete payload._originals;
      delete payload._original_language;
      delete payload._translated_at;
      delete payload._translation_source;
      if (dlg.mode === "create") {
        const res = await axios.post(`${API}/safety/corrective-actions`, payload, auth());
        const newId = res?.data?.id || res?.data?.doc_id;
        // Preserve original Spanish in the sidecar (best-effort).
        if (newId) {
          await persistBilingualSidecar("corrective_action", newId, translated);
        }
        toast.success("Corrective action created");
        // iter147 — usage telemetry
        import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
          trackFormSubmit("/safety/corrective-actions", true, "ca-create")).catch(() => {});
      } else {
        await axios.patch(
          `${API}/safety/corrective-actions/${dlg.id}`,
          { ...payload, status: f.status, completion_notes: translated.completion_notes || f.completion_notes || "" },
          auth(),
        );
        // Preserve original Spanish in the sidecar (best-effort).
        await persistBilingualSidecar("corrective_action", dlg.id, translated);
        toast.success("Corrective action updated");
        import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
          trackFormSubmit("/safety/corrective-actions", true, "ca-edit")).catch(() => {});
      }
      closeDlg();
      refresh();
    } catch (err) {
      toast.error(friendlyError(err, "Save failed"));
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/safety/corrective-actions", false, dlg.mode === "create" ? "ca-create" : "ca-edit")).catch(() => {});
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
    { id: "Verified",       label: "Verified",       count: counts.Verified || 0 },
    { id: "Closed",         label: "Closed",         count: counts.Closed || 0 },
    { id: "Overdue",        label: "Overdue",        count: counts.Overdue || 0, danger: true },
  ];

  return (
    <SafetyShell title="Corrective Actions" kicker="SAFETY · CORRECTIVE ACTION REGISTER">
      <div className="mb-5 space-y-3">
        <WhyItMattersPanel title="Why Corrective Actions matter">
          <p>
            A Corrective Action is the proof that an incident, audit finding,
            or near-miss was actually addressed — not just discussed. Always
            assign to a person (not a department), set a clear deadline,
            and verify before closing.{" "}
            <Link to="/guidance/safety-corrective-actions-workflow" className="font-medium underline">
              Deep workflow →
            </Link>
          </p>
        </WhyItMattersPanel>
        {/* iter356 · permanent operational coaching standard */}
        <LifecycleGuide
          id="capa-lifecycle"
          icon={ClipboardCheck}
          accent="indigo"
          title={t("CAPA Lifecycle")}
          summary={t("Open → In Progress → Pending Review → Verified → Closed (illegal jumps are blocked)")}
          sections={[
            {
              label: t("Roles"),
              body: t("Safety leads CAPA handling — create, edit, advance, verify, and close. HR adds labor and accountability notes only. PM and Field Leadership can read records affecting their crews. Admin keeps supervisory access."),
            },
            {
              label: t("Lifecycle gate"),
              body: t("A CAPA cannot move directly from Pending Review to Closed. It must pass through Verified — a separate review step that confirms the corrective work actually happened. The verifier is stamped onto the record."),
            },
            {
              label: t("Downstream visibility"),
              body: t("Open and Verified CAPAs surface on the PM Crew Compliance lens, HR Accountability Timeline, the standards dashboard, and Compliance Findings. Closed CAPAs remain in the audit trail forever."),
            },
            {
              label: t("Why this matters"),
              body: t("Open CAPAs that never close are silent operational debt. Severe incidents without a CAPA are surfaced on the standards dashboard. Every status change is appended to the CAPA history for OSHA / DOT / insurance review."),
            },
          ]}
        />
      </div>
      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm sm:text-base max-w-2xl leading-relaxed">
          {t("Track every safety deficiency to resolution. Auto-link CAs to incidents, audits, inspections, training records, and meetings. The pipeline is")}{" "}
          <span className="font-mono text-xs uppercase tracking-[0.18em] font-bold">{t("Open → In Progress → Pending Review → Verified → Closed")}</span>.
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
      {/* iter274 · page-root coaching · canonical 4 kinds */}
      <HelpTipBlock formKey="corrective" className="mb-3" showCounter />
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

      {/* iter139 — filter by linked master records */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 mb-4">
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Filter by linked equipment")}</Label>
          <div className="mt-1">
            <MasterLookupCombobox
              kind="equipment"
              value={filterEqId}
              displayValue={filterEqLabel}
              onPick={(item) => { setFilterEqId(item.id); setFilterEqLabel(item.label); }}
              onClear={() => { setFilterEqId(""); setFilterEqLabel(""); }}
              placeholder={t("Any equipment")}
              testIdPrefix="safety-ca-filter-equipment"
            />
          </div>
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Filter by linked employee")}</Label>
          <div className="mt-1">
            <MasterLookupCombobox
              kind="employees"
              value={filterEmpId}
              displayValue={filterEmpLabel}
              onPick={(item) => { setFilterEmpId(item.id); setFilterEmpLabel(item.label); }}
              onClear={() => { setFilterEmpId(""); setFilterEmpLabel(""); }}
              placeholder={t("Any employee")}
              testIdPrefix="safety-ca-filter-employee"
            />
          </div>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-ca-loading" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={AlertOctagon}
          title={t("No corrective actions")}
          body={tab === "All"
            ? t("Corrective actions track findings from inspections, incidents, and audits through to closure. Tap the New button above to create your first one.")
            : t("Nothing matches this filter yet. Try the 'All' tab to see every record.")}
          testId="safety-ca-empty"
        />
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
            {/* iter274 · dialog-top create coaching · Create mode only */}
            {dlg.mode === "create" && (
              <HelpTipBlock formKey="corrective.create" className="mb-1" />
            )}
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
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
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold flex items-center gap-1.5">
                  {t("Priority")}
                  <HelpTip
                    label={t("Priority vs. Severity")}
                    body={t("Priority drives WHEN we act — it controls the Open-queue ordering. Severity (set on the source incident or audit) describes the risk of the underlying finding itself.")}
                    testId="safety-ca-help-priority"
                  />
                </Label>
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
                {/* iter364 · CAPA assignee captured atomically (name + canonical
                    employee_id) via the same roster-first selector used on
                    Incidents / PPE / Training / Pre-Op / QA-QC. Free-text
                    fallback preserved for subcontractor / external owners. */}
                <EmployeeRosterField
                  label=""
                  value={{
                    id: dlg.form.employee_master_id || "",
                    name: dlg.form.assigned_to_name || "",
                    linked: !!dlg.form.employee_master_id,
                  }}
                  onChange={({ id, name, linked }) => {
                    setDlg((d) => ({
                      ...d,
                      form: {
                        ...d.form,
                        assigned_to_name: name,
                        employee_master_id: linked ? id : "",
                        employee_master_label: linked ? name : "",
                      },
                    }));
                  }}
                  placeholder={t("Type name to search roster")}
                  testId="safety-ca-form-assignee-roster"
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
            {/* iter138 — master record bindings (optional, freetext OK) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Linked equipment")}</Label>
                <div className="mt-1">
                  <MasterLookupCombobox
                    kind="equipment"
                    value={dlg.form.equipment_master_id}
                    displayValue={dlg.form.equipment_master_label}
                    onPick={(item) => setDlg((d) => ({
                      ...d,
                      form: { ...d.form, equipment_master_id: item.id, equipment_master_label: item.label },
                    }))}
                    onClear={() => setDlg((d) => ({
                      ...d,
                      form: { ...d.form, equipment_master_id: "", equipment_master_label: "" },
                    }))}
                    placeholder={t("Search by unit / make / VIN…")}
                    testIdPrefix="safety-ca-form-equipment"
                  />
                </div>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Linked employee")}</Label>
                <div className="mt-1">
                  <MasterLookupCombobox
                    kind="employees"
                    value={dlg.form.employee_master_id}
                    displayValue={dlg.form.employee_master_label}
                    onPick={(item) => setDlg((d) => ({
                      ...d,
                      form: { ...d.form, employee_master_id: item.id, employee_master_label: item.label },
                    }))}
                    onClear={() => setDlg((d) => ({
                      ...d,
                      form: { ...d.form, employee_master_id: "", employee_master_label: "" },
                    }))}
                    placeholder={t("Search by name / email / employee ID…")}
                    testIdPrefix="safety-ca-form-employee"
                  />
                </div>
              </div>
            </div>
            {dlg.mode === "edit" && (
              <div>
                {/* iter274 · close-out coaching (edit mode only) */}
                <HelpTipBlock formKey="corrective.close" className="mb-2" />
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
            {dlg.mode === "edit" && dlg.id && (
              <div className="pt-2 border-t border-slate-200">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">
                  {t("Employee acknowledgment")}
                </div>
                <SignatureCapture
                  sourceModule="safety.corrective_actions"
                  sourceRecordId={dlg.id}
                  signatureType="employee"
                  testIdPrefix="safety-ca-sig"
                />
              </div>
            )}
          </div>
          <DialogFooter className="pt-3 gap-2">
            <Button variant="outline" onClick={closeDlg} disabled={saving} data-testid="safety-ca-form-cancel">
              <X className="w-4 h-4 mr-1" /> {t("Cancel")}
            </Button>
            <Button
              onClick={save}
              disabled={saving}
              aria-busy={saving}
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
