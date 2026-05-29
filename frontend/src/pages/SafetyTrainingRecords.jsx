// SafetyTrainingRecords — Phase 4 training & certifications list tied
// to db.employees. Expiration tracking with "expiring within X days"
// filter. Each row: employee, training, cert type, completed, expiration.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Award, Plus, Loader2, AlertTriangle, Pencil, Trash2, Save, X, Filter,
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
import MasterLookupCombobox from "@/components/MasterLookupCombobox";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { HelpTip } from "@/components/ui/HelpTip";
import { HelpTipBlock } from "@/components/HelpTip";
import { useRememberedFilter, useRememberedFormValue } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { getSafetyToken } from "@/lib/safetyAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const CERT_TYPES = [
  "OSHA 10", "OSHA 30", "First Aid / CPR", "Confined Space",
  "Fall Protection", "Trench / Excavation", "Forklift", "Aerial Lift",
  "Hazmat / DOT", "Rigging / Signal Person", "Other",
];

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

const blank = () => ({
  employee_id: "",
  employee_name: "",
  training_name: "",
  certification_type: "OSHA 10",
  completed_date: new Date().toISOString().slice(0, 10),
  expiration_date: "",
  issued_by: "",
  notes: "",
  // iter138 — bind to employees master collection
  employee_master_id: "",
  employee_master_label: "",
});

function expStatus(rec) {
  if (!rec.expiration_date) return "none";
  const today = new Date().toISOString().slice(0, 10);
  const thirty = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  if (rec.expiration_date < today) return "expired";
  if (rec.expiration_date <= thirty) return "soon";
  return "ok";
}

const EXP_PILL = {
  expired: "bg-red-100 text-red-900 border-red-300",
  soon:    "bg-amber-100 text-amber-900 border-amber-300",
  ok:      "bg-emerald-100 text-emerald-900 border-emerald-300",
  none:    "bg-slate-100 text-slate-700 border-slate-300",
};

export default function SafetyTrainingRecords() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useRememberedFilter("safety.training.tab", "All");
  const [search, setSearch] = useRememberedFilter("safety.training.search", "");
  // iter148 — pre-fill last cert type on a fresh training record
  const [lastCertType, rememberLastCertType] = useRememberedFormValue(
    "safety.training.last-cert-type", "",
  );
  const [dlg, setDlg] = useState({ open: false, mode: "create", id: null, form: blank() });
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [recs, emps] = await Promise.all([
        axios.get(`${API}/safety/training-records`, auth()),
        axios.get(`${API}/employees`),
      ]);
      setItems(Array.isArray(recs.data) ? recs.data : []);
      setEmployees((emps.data?.items || []).map((e) => ({ id: e.id, name: e.name })));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load training records");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, []);

  const counts = useMemo(() => {
    const c = { All: items.length, Expired: 0, "Expiring 30d": 0 };
    items.forEach((r) => {
      const s = expStatus(r);
      if (s === "expired") c.Expired++;
      else if (s === "soon") c["Expiring 30d"]++;
    });
    return c;
  }, [items]);

  const filtered = useMemo(() => {
    let list = items;
    if (tab === "Expired") list = list.filter((r) => expStatus(r) === "expired");
    else if (tab === "Expiring 30d") list = list.filter((r) => expStatus(r) === "soon");
    if (search.trim()) {
      const s = search.trim().toLowerCase();
      list = list.filter((r) =>
        (r.employee_name || "").toLowerCase().includes(s)
        || (r.training_name || "").toLowerCase().includes(s)
        || (r.certification_type || "").toLowerCase().includes(s),
      );
    }
    return list;
  }, [items, tab, search]);

  const openCreate = () => setDlg({
    open: true,
    mode: "create",
    id: null,
    // iter148 — pre-fill certification_type from last submission. The
    // most-common workflow is logging the same cert type for several
    // employees in a row (e.g. OSHA-10 onboarding day).
    form: { ...blank(), certification_type: lastCertType || blank().certification_type },
  });
  const openEdit = (r) => setDlg({
    open: true, mode: "edit", id: r.id,
    form: {
      ...blank(),
      ...r,
      completed_date: r.completed_date || "",
      expiration_date: r.expiration_date || "",
    },
  });
  const close = () => setDlg((d) => ({ ...d, open: false }));

  const save = async () => {
    const f = dlg.form;
    if (!f.employee_id) { toast.error("Pick an employee"); return; }
    if (!f.training_name.trim()) { toast.error("Training name required"); return; }
    if (!f.completed_date) { toast.error("Completed date required"); return; }
    setSaving(true);
    try {
      const payload = {
        ...f,
        employee_name: f.employee_name || (employees.find((e) => e.id === f.employee_id)?.name || ""),
        expiration_date: f.expiration_date || null,
      };
      if (dlg.mode === "create") {
        await axios.post(`${API}/safety/training-records`, payload, auth());
        toast.success("Training record added");
        // iter147 — training submit telemetry
        import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
          trackFormSubmit("/safety/training-records", true, "training-create")).catch(() => {});
        // iter148 — remember the cert type for the next entry
        if (payload.certification_type) rememberLastCertType(payload.certification_type);
      } else {
        await axios.patch(`${API}/safety/training-records/${dlg.id}`, payload, auth());
        toast.success("Training record updated");
        import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
          trackFormSubmit("/safety/training-records", true, "training-edit")).catch(() => {});
      }
      close();
      refresh();
    } catch (err) {
      toast.error(friendlyError(err, "Save failed"));
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/safety/training-records", false, dlg.mode === "create" ? "training-create" : "training-edit")).catch(() => {});
    } finally {
      setSaving(false);
    }
  };

  const remove = async (r) => {
    if (!window.confirm(`Delete training record for ${r.employee_name || "this employee"}?`)) return;
    try {
      await axios.delete(`${API}/safety/training-records/${r.id}`, auth());
      toast.success("Deleted");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const TABS = [
    { id: "All", label: "All", count: counts.All },
    { id: "Expiring 30d", label: "Expiring 30d", count: counts["Expiring 30d"], warn: true },
    { id: "Expired", label: "Expired", count: counts.Expired, danger: true },
  ];

  return (
    <SafetyShell title="Training & Certifications" kicker="SAFETY · TRAINING REGISTER">
      {/* iter289 · coaching family · top-of-page canonical 4 */}
      <HelpTipBlock formKey="safety-training" />
      {/* iter289 · expiration sub-key — sits next to the renewal queue */}
      <HelpTipBlock formKey="safety-training.expiration" />

      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm max-w-2xl leading-relaxed">
          {t("Per-employee training records tied to the MASCI employee roster. Expiration tracking flags certs about to lapse so they're renewed before the field crew is non-compliant.")}
        </p>
        <Button onClick={openCreate} className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-11 shrink-0" data-testid="safety-tr-new">
          <Plus className="w-4 h-4 mr-1" /> {t("Add Record")}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4 border-b-2 border-slate-200 pb-3">
        {TABS.map((tb) => (
          <button
            key={tb.id} onClick={() => setTab(tb.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold border-2 ${
              tab === tb.id
                ? (tb.danger ? "bg-red-600 text-white border-red-700" : tb.warn ? "bg-amber-600 text-white border-amber-700" : "bg-cyan-700 text-white border-cyan-800")
                : (tb.danger ? "bg-white text-red-700 border-red-200" : tb.warn ? "bg-white text-amber-800 border-amber-200" : "bg-white text-slate-700 border-slate-200")
            }`}
            data-testid={`safety-tr-tab-${tb.id.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {tb.label} ({tb.count})
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Input placeholder={t("Filter by employee, training, cert type…")} value={search} onChange={(e) => setSearch(e.target.value)} className={`${inputCls} max-w-md`} data-testid="safety-tr-search" />
      </div>

      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-tr-loading" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Award}
          title={t("No training records")}
          body={tab === "All" ? t("Add the first one above.") : t("Nothing matches this filter.")}
          testId="safety-tr-empty"
        />
      ) : (
        <div className="overflow-x-auto" data-testid="safety-tr-list">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">Employee</th>
                <th className="text-left px-3 py-2">Training</th>
                <th className="text-left px-3 py-2">Type</th>
                <th className="text-left px-3 py-2">Completed</th>
                <th className="text-left px-3 py-2">Expires</th>
                <th className="text-center px-3 py-2">Status</th>
                <th className="text-right px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const st = expStatus(r);
                const label = st === "expired" ? "Expired" : st === "soon" ? "Expiring 30d" : st === "ok" ? "Current" : "No expiry";
                return (
                  <tr key={r.id} className={`border-t border-slate-100 ${st === "expired" ? "bg-red-50" : ""}`} data-testid={`safety-tr-row-${r.id}`}>
                    <td className="px-3 py-2 font-semibold">{r.employee_name}</td>
                    <td className="px-3 py-2">{r.training_name}</td>
                    <td className="px-3 py-2 text-slate-600 text-xs font-mono">{r.certification_type || "—"}</td>
                    <td className="px-3 py-2">{r.completed_date || "—"}</td>
                    <td className="px-3 py-2">
                      {r.expiration_date || <span className="text-slate-400">—</span>}
                      {st === "expired" && <AlertTriangle className="w-3.5 h-3.5 text-red-600 inline ml-1" />}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${EXP_PILL[st]}`}>
                        {label}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <div className="inline-flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => openEdit(r)} className="h-8" data-testid={`safety-tr-edit-${r.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" onClick={() => remove(r)} className="h-8 border-red-300 text-red-700" data-testid={`safety-tr-delete-${r.id}`}><Trash2 className="w-3.5 h-3.5" /></Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <Dialog open={dlg.open} onOpenChange={(o) => !o && close()}>
        <DialogContent className="sm:max-w-xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{dlg.mode === "create" ? t("Add training record") : t("Edit training record")}</DialogTitle>
            <DialogDescription>{t("Tied to the MASCI employee roster. Leave expiration blank for trainings that don't expire.")}</DialogDescription>
          </DialogHeader>
          {/* iter289 · upload-discipline coaching inside the entry dialog */}
          <HelpTipBlock formKey="safety-training.upload" />
          <div className="space-y-3 pt-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Employee")} *</Label>
              <Select value={dlg.form.employee_id || ""} onValueChange={(v) => {
                const emp = employees.find((e) => e.id === v);
                // iter138 — picking from the in-memory list also binds master id
                setDlg((d) => ({ ...d, form: {
                  ...d.form, employee_id: v, employee_name: emp?.name || "",
                  employee_master_id: emp?.id || "", employee_master_label: emp?.name || "",
                } }));
              }}>
                <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-tr-form-employee"><SelectValue placeholder={t("Pick employee")} /></SelectTrigger>
                <SelectContent className="max-h-72">
                  {employees.map((e) => <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>)}
                </SelectContent>
              </Select>
              {/* iter138 — for fast-typing supervisors, also offer the typeahead */}
              <details className="mt-1.5 text-[11px]">
                <summary className="cursor-pointer text-slate-500 hover:text-slate-700">{t("Or search by name / email / employee ID…")}</summary>
                <div className="mt-2">
                  <MasterLookupCombobox
                    kind="employees"
                    value={dlg.form.employee_master_id}
                    displayValue={dlg.form.employee_master_label}
                    onPick={(item) => setDlg((d) => ({
                      ...d,
                      form: {
                        ...d.form,
                        employee_id: item.id || d.form.employee_id,
                        employee_name: item.label || d.form.employee_name,
                        employee_master_id: item.id,
                        employee_master_label: item.label,
                      },
                    }))}
                    onClear={() => setDlg((d) => ({
                      ...d,
                      form: { ...d.form, employee_master_id: "", employee_master_label: "" },
                    }))}
                    testIdPrefix="safety-tr-form-employee-typeahead"
                  />
                </div>
              </details>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Training name")} *</Label>
                <Input value={dlg.form.training_name} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, training_name: e.target.value } }))} className={`${inputCls} mt-1`} placeholder="e.g. OSHA 10-hour Construction" data-testid="safety-tr-form-name" />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Certification type")}</Label>
                <Select value={dlg.form.certification_type} onValueChange={(v) => setDlg((d) => ({ ...d, form: { ...d.form, certification_type: v } }))}>
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-tr-form-cert"><SelectValue /></SelectTrigger>
                  <SelectContent>{CERT_TYPES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Completed date")} *</Label>
                <Input type="date" value={dlg.form.completed_date} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, completed_date: e.target.value } }))} className={`${inputCls} mt-1`} data-testid="safety-tr-form-completed" />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold flex items-center gap-1.5">
                  {t("Expiration date")}
                  <HelpTip
                    label={t("When does a training expire?")}
                    body={t("Leave blank for certifications that don't expire (e.g. orientation). For OSHA-10/30, MSHA, CPR/First Aid, and other annual or biennial certs, set this to the date the credential lapses.")}
                    testId="training-help-expiration"
                  />
                </Label>
                <Input type="date" value={dlg.form.expiration_date || ""} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, expiration_date: e.target.value } }))} className={`${inputCls} mt-1`} data-testid="safety-tr-form-expiration" />
              </div>
              <div className="sm:col-span-2">
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Issued by")}</Label>
                <Input value={dlg.form.issued_by} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, issued_by: e.target.value } }))} className={`${inputCls} mt-1`} placeholder="e.g. OSHA Outreach Trainer · ATSSA · Provider name" />
              </div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Notes")}</Label>
              <Textarea value={dlg.form.notes} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, notes: e.target.value } }))} rows={2} className="text-sm border-2 border-slate-300 mt-1" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={close} disabled={saving}><X className="w-4 h-4 mr-1" /> {t("Cancel")}</Button>
            <Button onClick={save} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="safety-tr-form-save">
              {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />} {t("Save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </SafetyShell>
  );
}
