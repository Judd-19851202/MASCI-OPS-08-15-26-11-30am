// SafetyFireExtinguishers — Phase 3 fire-extinguisher register.
// Each unit is one row with last/next inspection + status. Logging a new
// inspection POSTs to /inspect which auto-stamps last_inspection_date,
// last_status, next_due_date, and pushes the entry into inspections[].
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Flame, Plus, Loader2, ClipboardCheck, AlertTriangle,
  Pencil, Trash2, Save, X, Upload, Paperclip,
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
import SafetyFireExtManageDialog from "@/components/SafetyFireExtManageDialog";
import MasterLookupCombobox from "@/components/MasterLookupCombobox";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { getSafetyToken } from "@/lib/safetyAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const STATUS_OPTIONS = ["Pass", "Fail", "Needs Service"];
const STATUS_COLOR = {
  Pass: "bg-emerald-100 text-emerald-900 border-emerald-300",
  Fail: "bg-red-100 text-red-900 border-red-300",
  "Needs Service": "bg-amber-100 text-amber-900 border-amber-300",
};
const TYPES = ["ABC", "BC", "CO2", "Class K", "Water", "Halotron"];
const LOCATION_KINDS = [
  { value: "truck", label: "Truck #" },
  { value: "job", label: "Job # / Project" },
  { value: "facility", label: "Facility" },
];

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

const blank = () => ({
  unit_id: "", location_kind: "truck", location_value: "",
  type: "ABC", size: "10 lb",
  last_inspection_date: "", next_due_date: "",
  last_status: "Pass", notes: "",
  // iter138 — link this extinguisher to a specific master equipment unit
  equipment_master_id: "", equipment_master_label: "",
});

const inspectBlank = () => ({
  inspection_date: new Date().toISOString().slice(0, 10),
  status: "Pass", inspector_name: "", next_due_date: "", notes: "",
});

function isOverdue(fe) {
  if (!fe.next_due_date) return false;
  return fe.next_due_date < new Date().toISOString().slice(0, 10);
}

export default function SafetyFireExtinguishers() {
  const { t } = useT();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("All");
  const [search, setSearch] = useState("");
  const [editDlg, setEditDlg] = useState({ open: false, mode: "create", id: null, form: blank() });
  const [inspectDlg, setInspectDlg] = useState({ open: false, fe: null, form: inspectBlank() });
  const [manageDlg, setManageDlg] = useState({ open: false, fe: null });
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/safety/fire-extinguishers`, auth());
      setItems(Array.isArray(r.data) ? r.data : []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load fire extinguishers");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, []);

  const counts = useMemo(() => {
    const c = { All: items.length, Overdue: 0 };
    STATUS_OPTIONS.forEach((s) => { c[s] = 0; });
    items.forEach((it) => {
      c[it.last_status] = (c[it.last_status] || 0) + 1;
      if (isOverdue(it)) c.Overdue += 1;
    });
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    let list = items;
    if (tab === "Overdue") list = list.filter(isOverdue);
    else if (tab !== "All") list = list.filter((it) => it.last_status === tab);
    if (search.trim()) {
      const s = search.trim().toLowerCase();
      list = list.filter((it) =>
        (it.unit_id || "").toLowerCase().includes(s)
        || (it.location_value || "").toLowerCase().includes(s)
        || (it.type || "").toLowerCase().includes(s),
      );
    }
    return list;
  }, [items, tab, search]);

  const openCreate = () => setEditDlg({ open: true, mode: "create", id: null, form: blank() });
  const openEdit = (fe) => setEditDlg({ open: true, mode: "edit", id: fe.id, form: { ...blank(), ...fe } });
  const closeEdit = () => setEditDlg((d) => ({ ...d, open: false }));

  // iter139 — auto-suggest equipment_master_id from the truck location field.
  // Triggers only when (a) location_kind is 'truck', (b) the user typed a
  // value, (c) no master id is bound yet. Stops if exact unit_number match
  // not found (no guessing).
  useEffect(() => {
    if (!editDlg.open) return;
    const f = editDlg.form;
    if (f.equipment_master_id) return;
    if (f.location_kind !== "truck") return;
    const v = (f.location_value || "").trim();
    if (v.length < 2) return;
    const handle = setTimeout(async () => {
      try {
        const r = await axios.get(`${API}/master-lookup/equipment`, { params: { q: v, limit: 5 } });
        const items = r.data?.items || [];
        // Only auto-bind if we have an EXACT unit_number match (case-insensitive)
        const exact = items.find((it) => (it.unit_number || "").trim().toUpperCase() === v.toUpperCase());
        if (exact) {
          const label = `${exact.unit_number}${exact.make_model ? ` — ${exact.make_model}` : ""}`;
          setEditDlg((d) => ({
            ...d,
            form: { ...d.form, equipment_master_id: exact.id, equipment_master_label: label },
          }));
        }
      } catch { /* swallow — non-blocking */ }
    }, 350);
    return () => clearTimeout(handle);
  }, [editDlg.open, editDlg.form.location_kind, editDlg.form.location_value, editDlg.form.equipment_master_id]);

  const save = async () => {
    const f = editDlg.form;
    if (!f.unit_id.trim()) { toast.error("Unit ID required"); return; }
    setSaving(true);
    try {
      if (editDlg.mode === "create") {
        await axios.post(`${API}/safety/fire-extinguishers`, f, auth());
        toast.success("Extinguisher added");
      } else {
        await axios.patch(`${API}/safety/fire-extinguishers/${editDlg.id}`, f, auth());
        toast.success("Extinguisher updated");
      }
      closeEdit();
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const openInspect = (fe) => setInspectDlg({ open: true, fe, form: inspectBlank() });
  const closeInspect = () => setInspectDlg((d) => ({ ...d, open: false }));
  const submitInspect = async () => {
    const f = inspectDlg.form;
    if (!f.inspection_date) { toast.error("Inspection date required"); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/safety/fire-extinguishers/${inspectDlg.fe.id}/inspect`, f, auth());
      toast.success(`Inspection logged — next due ${f.next_due_date || "+30d"}`);
      // iter147 — track the inspection submit; the heaviest fire-ext flow
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/safety/fire-extinguishers/inspect", true, "fire-ext-inspect")).catch(() => {});
      closeInspect();
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Inspection failed");
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/safety/fire-extinguishers/inspect", false, "fire-ext-inspect")).catch(() => {});
    } finally {
      setSaving(false);
    }
  };

  const removeFe = async (fe) => {
    if (!window.confirm(`Delete ${fe.unit_id}? This removes its full inspection history.`)) return;
    try {
      await axios.delete(`${API}/safety/fire-extinguishers/${fe.id}`, auth());
      toast.success("Deleted");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const TABS = [
    { id: "All", label: "All", count: counts.All },
    { id: "Pass", label: "Pass", count: counts.Pass || 0 },
    { id: "Fail", label: "Fail", count: counts.Fail || 0 },
    { id: "Needs Service", label: "Needs Service", count: counts["Needs Service"] || 0 },
    { id: "Overdue", label: "Overdue", count: counts.Overdue || 0, danger: true },
  ];

  return (
    <SafetyShell title="Fire Extinguishers" kicker="SAFETY · FIRE EXTINGUISHER REGISTER">
      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm max-w-2xl leading-relaxed">
          {t("Track every fire extinguisher unit across trucks, jobsites, and facilities. Monthly inspections push status + next-due date + the inspection log automatically.")}
        </p>
        <div className="flex flex-wrap gap-2 shrink-0">
          <Button onClick={() => nav("/safety-portal/fire-extinguishers/import")} variant="outline" className="border-2 border-slate-300 font-bold uppercase tracking-wide h-11" data-testid="safety-fe-bulk-import">
            <Upload className="w-4 h-4 mr-1" /> {t("Bulk Import")}
          </Button>
          <Button onClick={openCreate} className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-11" data-testid="safety-fe-new">
            <Plus className="w-4 h-4 mr-1" /> {t("Add Extinguisher")}
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4 border-b-2 border-slate-200 pb-3">
        {TABS.map((tb) => (
          <button
            key={tb.id} onClick={() => setTab(tb.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold border-2 ${
              tab === tb.id
                ? (tb.danger ? "bg-red-600 text-white border-red-700" : "bg-cyan-700 text-white border-cyan-800")
                : (tb.danger ? "bg-white text-red-700 border-red-200" : "bg-white text-slate-700 border-slate-200")
            }`}
            data-testid={`safety-fe-tab-${tb.id.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {tb.label} <span className="opacity-70">({tb.count})</span>
          </button>
        ))}
      </div>

      <Input placeholder={t("Filter by unit, location, type…")} value={search} onChange={(e) => setSearch(e.target.value)} className={`${inputCls} max-w-md mb-4`} data-testid="safety-fe-search" />

      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-fe-loading" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Flame}
          title={t("No extinguishers")}
          body={tab === "All" ? t("Add the first one above.") : t("Try a different filter.")}
          testId="safety-fe-empty"
        />
      ) : (
        <div className="overflow-x-auto" data-testid="safety-fe-list">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">Unit</th>
                <th className="text-left px-3 py-2">Location</th>
                <th className="text-left px-3 py-2">Type / Size</th>
                <th className="text-left px-3 py-2">Last Inspect</th>
                <th className="text-left px-3 py-2">Next Due</th>
                <th className="text-center px-3 py-2">Status</th>
                <th className="text-right px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((fe) => (
                <tr key={fe.id} className={`border-t border-slate-100 ${isOverdue(fe) ? "bg-red-50" : ""}`} data-testid={`safety-fe-row-${fe.id}`}>
                  <td className="px-3 py-2 font-semibold">{fe.unit_id}</td>
                  <td className="px-3 py-2">
                    <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono uppercase mr-1">{fe.location_kind}</span>
                    {fe.location_value || "—"}
                  </td>
                  <td className="px-3 py-2">{fe.type} {fe.size ? <span className="text-slate-500">· {fe.size}</span> : null}</td>
                  <td className="px-3 py-2">{fe.last_inspection_date || "—"}</td>
                  <td className="px-3 py-2">
                    {fe.next_due_date || "—"}
                    {isOverdue(fe) && <AlertTriangle className="w-3.5 h-3.5 text-red-600 inline ml-1" />}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_COLOR[fe.last_status] || ""}`}>
                      {fe.last_status || "—"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="inline-flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => openInspect(fe)} className="h-8 border-cyan-300 text-cyan-800" data-testid={`safety-fe-inspect-${fe.id}`} title="Log inspection">
                        <ClipboardCheck className="w-3.5 h-3.5" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setManageDlg({ open: true, fe })} className="h-8 border-slate-300" data-testid={`safety-fe-manage-${fe.id}`} title="Attachments & PDF history">
                        <Paperclip className="w-3.5 h-3.5" />
                        {(fe.attachments || []).length > 0 && (
                          <span className="ml-1 text-[10px] font-bold text-cyan-700">{(fe.attachments || []).length}</span>
                        )}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => openEdit(fe)} className="h-8" data-testid={`safety-fe-edit-${fe.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
                      <Button size="sm" variant="outline" onClick={() => removeFe(fe)} className="h-8 border-red-300 text-red-700" data-testid={`safety-fe-delete-${fe.id}`}><Trash2 className="w-3.5 h-3.5" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / edit */}
      <Dialog open={editDlg.open} onOpenChange={(o) => !o && closeEdit()}>
        <DialogContent className="sm:max-w-xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editDlg.mode === "create" ? t("Add fire extinguisher") : t("Edit extinguisher")}</DialogTitle>
            <DialogDescription>{t("One record per physical unit. Logging inspections later updates this row + adds to history.")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Unit ID")} *</Label>
                <Input value={editDlg.form.unit_id} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, unit_id: e.target.value } }))} className={`${inputCls} mt-1`} placeholder="FE-001" data-testid="safety-fe-form-unit" />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Type")}</Label>
                <Select value={editDlg.form.type} onValueChange={(v) => setEditDlg((d) => ({ ...d, form: { ...d.form, type: v } }))}>
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-fe-form-type"><SelectValue /></SelectTrigger>
                  <SelectContent>{TYPES.map((tt) => <SelectItem key={tt} value={tt}>{tt}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Location kind")}</Label>
                <Select value={editDlg.form.location_kind} onValueChange={(v) => setEditDlg((d) => ({ ...d, form: { ...d.form, location_kind: v } }))}>
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-fe-form-loc-kind"><SelectValue /></SelectTrigger>
                  <SelectContent>{LOCATION_KINDS.map((lk) => <SelectItem key={lk.value} value={lk.value}>{lk.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Location value")}</Label>
                <Input value={editDlg.form.location_value} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, location_value: e.target.value } }))} className={`${inputCls} mt-1`} placeholder="e.g. Truck 12 / Job 220 / Shop" data-testid="safety-fe-form-loc-val" />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Size")}</Label>
                <Input value={editDlg.form.size} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, size: e.target.value } }))} className={`${inputCls} mt-1`} placeholder="10 lb" />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Last status")}</Label>
                <Select value={editDlg.form.last_status} onValueChange={(v) => setEditDlg((d) => ({ ...d, form: { ...d.form, last_status: v } }))}>
                  <SelectTrigger className={`${inputCls} mt-1`}><SelectValue /></SelectTrigger>
                  <SelectContent>{STATUS_OPTIONS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Last inspection date")}</Label>
                <Input type="date" value={editDlg.form.last_inspection_date || ""} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, last_inspection_date: e.target.value } }))} className={`${inputCls} mt-1`} />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Next due date")}</Label>
                <Input type="date" value={editDlg.form.next_due_date || ""} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, next_due_date: e.target.value } }))} className={`${inputCls} mt-1`} />
              </div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Notes")}</Label>
              <Textarea value={editDlg.form.notes} onChange={(e) => setEditDlg((d) => ({ ...d, form: { ...d.form, notes: e.target.value } }))} className="text-sm border-2 border-slate-300 mt-1" rows={2} />
            </div>
            {/* iter138 — link to a specific master equipment unit (truck mount) */}
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Linked equipment (optional)")}</Label>
              <div className="mt-1">
                <MasterLookupCombobox
                  kind="equipment"
                  value={editDlg.form.equipment_master_id}
                  displayValue={editDlg.form.equipment_master_label}
                  onPick={(item) => setEditDlg((d) => ({
                    ...d,
                    form: { ...d.form, equipment_master_id: item.id, equipment_master_label: item.label },
                  }))}
                  onClear={() => setEditDlg((d) => ({
                    ...d,
                    form: { ...d.form, equipment_master_id: "", equipment_master_label: "" },
                  }))}
                  placeholder={t("Truck or yard unit this extinguisher is assigned to")}
                  testIdPrefix="safety-fe-form-equipment"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="pt-3 gap-2">
            <Button variant="outline" onClick={closeEdit} disabled={saving}><X className="w-4 h-4 mr-1" /> {t("Cancel")}</Button>
            <Button onClick={save} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="safety-fe-form-save">
              {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />} {t("Save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Inspect dialog */}
      <Dialog open={inspectDlg.open} onOpenChange={(o) => !o && closeInspect()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("Log inspection")} {inspectDlg.fe ? `· ${inspectDlg.fe.unit_id}` : ""}</DialogTitle>
            <DialogDescription>{t("Saves the result + auto-stamps next due date (defaults to +30 days).")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Inspection date")} *</Label>
              <Input type="date" value={inspectDlg.form.inspection_date} onChange={(e) => setInspectDlg((d) => ({ ...d, form: { ...d.form, inspection_date: e.target.value } }))} className={`${inputCls} mt-1`} data-testid="safety-fe-inspect-date" />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Status")} *</Label>
              <Select value={inspectDlg.form.status} onValueChange={(v) => setInspectDlg((d) => ({ ...d, form: { ...d.form, status: v } }))}>
                <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-fe-inspect-status"><SelectValue /></SelectTrigger>
                <SelectContent>{STATUS_OPTIONS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Inspector name")}</Label>
              <Input value={inspectDlg.form.inspector_name} onChange={(e) => setInspectDlg((d) => ({ ...d, form: { ...d.form, inspector_name: e.target.value } }))} className={`${inputCls} mt-1`} placeholder={t("Defaults to signed-in safety user")} />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Next due date (optional)")}</Label>
              <Input type="date" value={inspectDlg.form.next_due_date} onChange={(e) => setInspectDlg((d) => ({ ...d, form: { ...d.form, next_due_date: e.target.value } }))} className={`${inputCls} mt-1`} />
              <div className="text-[11px] text-slate-500 mt-1">{t("Leave blank to auto-set +30 days.")}</div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Notes")}</Label>
              <Textarea value={inspectDlg.form.notes} onChange={(e) => setInspectDlg((d) => ({ ...d, form: { ...d.form, notes: e.target.value } }))} className="text-sm border-2 border-slate-300 mt-1" rows={2} />
            </div>
          </div>
          <DialogFooter className="pt-3 gap-2">
            <Button variant="outline" onClick={closeInspect} disabled={saving}>{t("Cancel")}</Button>
            <Button onClick={submitInspect} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="safety-fe-inspect-save">
              {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <ClipboardCheck className="w-4 h-4 mr-1" />} {t("Log inspection")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manage (attachments + history PDF) */}
      <SafetyFireExtManageDialog
        open={manageDlg.open}
        fe={manageDlg.fe}
        onClose={() => setManageDlg({ open: false, fe: null })}
        onChanged={(updated) => {
          setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
        }}
      />
    </SafetyShell>
  );
}
