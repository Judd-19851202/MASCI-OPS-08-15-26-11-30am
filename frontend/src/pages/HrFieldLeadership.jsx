// HR — Field Leadership records (read-only).
// List with filter chips per kind and search box. Clicking an item
// opens an HR-scoped detail panel with the PDF download link.
import React, { useCallback, useEffect, useState } from "react";
import { Loader2, FileText, Search, Eye, X } from "lucide-react";
import { api, API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import HrPageShell from "@/components/HrPageShell";
import { getHrToken } from "@/lib/hrAuth";
import { HelpTipBlock } from "@/components/HelpTip";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const KINDS = [
  { value: "", label: "All forms" },
  { value: "write_up", label: "Write-Up" },
  { value: "verbal_coaching", label: "Verbal Coaching" },
  { value: "attendance", label: "Attendance" },
  { value: "recognition", label: "Recognition" },
  { value: "equipment_checkout", label: "Equipment Checkout" },
  { value: "new_employee_eval", label: "New Employee Eval" },
  { value: "crew_eval", label: "Crew Eval" },
  { value: "promotion_recommendation", label: "Promotion Recommendation" },
  { value: "training_deficiency", label: "Training Deficiency" },
  { value: "employee_termination", label: "Termination" },
];

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

export default function HrFieldLeadership() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(null);

  const fetchRows = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 200 };
      if (kind) params.kind = kind;
      if (q.trim()) params.q = q.trim();
      const r = await api.get("/hr/field-leadership", { params });
      setItems(r.data?.items || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load records"));
    } finally {
      setLoading(false);
    }
  }, [kind, q, t]);

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const downloadPdf = async (rec) => {
    try {
      const tok = getHrToken();
      const r = await fetch(`${API}/hr/field-leadership/${rec.id}/pdf`, { headers: { "X-HR-Token": tok } });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `MASCI_FL_${(rec.employee_name || rec.kind).replace(/\s+/g, "_")}_${(rec.id || "").slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      toast.error(t("PDF download failed"));
    }
  };

  return (
    <HrPageShell title="Field Leadership Records" kicker="HR · Read-Only">
      {/* iter221 · surface the iter218 reviewer-side coaching on the
          HR records page. Same family wired on FieldLeadershipRecords
          for supers; HR reviewers need the same anchor: reviewing
          isn't auditing — it's reading the crew's work. */}
      <div className="mb-5">
        <HelpTipBlock formKey="field-leadership.records" showCounter />
      </div>
      <Card className="p-4 mb-5 border-2 border-purple-200 bg-purple-50/30">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div className="md:col-span-2">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Search")}</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-3 text-slate-400" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && fetchRows()} className={`${inputCls} pl-8`} placeholder={t("Employee, supervisor, project...")} data-testid="hr-fl-search" />
            </div>
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Form Kind")}</label>
            <Select value={kind || "__all__"} onValueChange={(v) => setKind(v === "__all__" ? "" : v)}>
              <SelectTrigger className={inputCls} data-testid="hr-fl-kind"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">{t("All forms")}</SelectItem>
                {KINDS.filter((k) => k.value).map((k) => <SelectItem key={k.value} value={k.value}>{t(k.label)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={fetchRows} disabled={loading} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-fl-apply">
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {t("Apply")}
          </Button>
        </div>
      </Card>

      {loading ? (
        <Card className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 mx-auto animate-spin" /></Card>
      ) : items.length === 0 ? (
        <Card className="p-10 text-center text-slate-500" data-testid="hr-fl-empty">{t("No records match these filters.")}</Card>
      ) : (
        <Card className="overflow-x-auto" data-testid="hr-fl-table">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Date")}</th>
                <th className="text-left px-3 py-2">{t("Employee")}</th>
                <th className="text-left px-3 py-2">{t("Form")}</th>
                <th className="text-left px-3 py-2">{t("Supervisor")}</th>
                <th className="text-left px-3 py-2">{t("Project")}</th>
                <th className="text-right px-3 py-2">{t("Actions")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-xs">{(r.occurred_at || "").slice(0, 10)}</td>
                  <td className="px-3 py-2 font-semibold">{r.employee_name || "—"}</td>
                  <td className="px-3 py-2">
                    <span className="inline-block px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-xs font-mono">{r.kind}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-700">{r.supervisor_name || "—"}</td>
                  <td className="px-3 py-2 text-slate-700">
                    <div className="font-mono text-xs text-slate-500">{r.project_number}</div>
                    <div>{r.project_name}</div>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="inline-flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => setSelected(r)} className="h-8" title={t("View")} data-testid={`hr-fl-view-${r.id}`}>
                        <Eye className="w-3.5 h-3.5" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => downloadPdf(r)} className="h-8" title={t("PDF")} data-testid={`hr-fl-pdf-${r.id}`}>
                        <FileText className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {selected && <HrFlDetailDrawer rec={selected} onClose={() => setSelected(null)} onPdf={downloadPdf} />}
    </HrPageShell>
  );
}

function HrFlDetailDrawer({ rec, onClose, onPdf }) {
  const { t } = useT();
  const details = rec.details || {};
  const detailEntries = Object.entries(details).filter(([k, v]) => v !== "" && v != null && k !== "outstanding_equipment_acknowledged");

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4" onClick={onClose} data-testid="hr-fl-drawer">
      <Card className="max-w-2xl w-full max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b-2 border-slate-200 px-5 py-3 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-purple-700 font-bold">{rec.kind}</div>
            <h3 className="font-display text-xl font-black">{rec.employee_name || rec.kind}</h3>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => onPdf(rec)}><FileText className="w-3.5 h-3.5 mr-1" />{t("PDF")}</Button>
            <Button size="sm" variant="outline" onClick={onClose} data-testid="hr-fl-drawer-close"><X className="w-3.5 h-3.5" /></Button>
          </div>
        </div>
        <div className="p-5 space-y-3 text-sm">
          <Field label={t("Date")} value={rec.occurred_at} />
          <Field label={t("Supervisor")} value={rec.supervisor_name} />
          <Field label={t("Project")} value={`${rec.project_number || ""} ${rec.project_name || ""}`.trim()} />
          <Field label={t("Location")} value={rec.location} />
          {detailEntries.map(([k, v]) => (
            <Field key={k} label={prettifyKey(k)} value={renderValue(v)} />
          ))}
        </div>
      </Card>
    </div>
  );
}

function Field({ label, value }) {
  if (value === "" || value == null) return null;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">{label}</div>
      <div className="text-slate-900 whitespace-pre-wrap break-words">{value}</div>
    </div>
  );
}

function prettifyKey(k) {
  return k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderValue(v) {
  if (v == null) return "";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (Array.isArray(v)) return v.map((x) => (typeof x === "object" ? JSON.stringify(x) : String(x))).join(", ");
  if (typeof v === "object") return JSON.stringify(v, null, 2);
  return String(v);
}
