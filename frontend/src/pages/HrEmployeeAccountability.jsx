// HR — Employee Accountability.
// Search by employee name → consolidated view of all Field Leadership
// records, outstanding equipment, trainings, safety form issuances.
// Used by HR before approving offboarding / clearance.
import React, { useState } from "react";
import { Loader2, Search, AlertOctagon, Award, ClipboardCheck, Wrench, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import HrPageShell from "@/components/HrPageShell";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { HelpTipBlock } from "@/components/HelpTip";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

const KIND_LABEL = {
  write_up: "Write-Up",
  verbal_coaching: "Verbal Coaching",
  attendance: "Attendance",
  recognition: "Recognition",
  equipment_checkout: "Equipment Checkout",
  new_employee_eval: "New Employee Eval",
  crew_eval: "Crew Eval",
  promotion_recommendation: "Promotion",
  training_deficiency: "Training Deficiency",
  employee_termination: "Termination",
  supervisor_notes: "Supervisor Notes",
};

export default function HrEmployeeAccountability() {
  const { t } = useT();
  const [name, setName] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const search = async (e) => {
    e?.preventDefault();
    if (name.trim().length < 2) return toast.error(t("Type at least 2 characters"));
    setLoading(true);
    try {
      const r = await api.get("/hr/employee-accountability", { params: { employee: name.trim() } });
      setData(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Search failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <HrPageShell title="Employee Accountability" kicker="HR · Offboarding & Clearance">
      {/* iter223 · operational leadership coaching for the trust-impact
          moment. Anchor: "The answer lives in the record — read first,
          respond second." */}
      <div className="mb-5">
        <HelpTipBlock formKey="employee-accountability" showCounter />
      </div>
      <Card className="p-4 mb-5 border-2 border-purple-200 bg-purple-50/30">
        <form onSubmit={search} className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Employee Name")}</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("Type at least 2 characters of the employee's name...")} className={inputCls} data-testid="hr-acc-name" />
          </div>
          <Button type="submit" disabled={loading} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-acc-search">
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {t("Search")}
          </Button>
        </form>
      </Card>

      {!data ? (
        <Card className="p-10 text-center text-slate-500" data-testid="hr-acc-empty">
          <Search className="w-8 h-8 mx-auto text-slate-400 mb-2" />
          {t("Search by employee name to see their complete accountability profile.")}
        </Card>
      ) : (
        <AccountabilityResults data={data} />
      )}
    </HrPageShell>
  );
}

function AccountabilityResults({ data }) {
  const { t } = useT();
  const counts = data.counts || {};
  const byKind = data.by_kind || {};

  return (
    <div className="space-y-6">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{t("Search results for")}</div>
        <h2 className="font-display text-2xl font-black">{data.employee}</h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        <StatCard icon={ClipboardCheck} label={t("FL Records")} value={counts.fl_records} accent="purple" testId="hr-acc-stat-fl" />
        <StatCard icon={AlertOctagon} label={t("Active Write-ups")} value={counts.active_writeups} accent={counts.active_writeups > 0 ? "amber" : "slate"} testId="hr-acc-stat-writeups" />
        <StatCard icon={Wrench} label={t("Outstanding Equipment")} value={counts.outstanding_equipment} accent={counts.outstanding_equipment > 0 ? "red" : "emerald"} testId="hr-acc-stat-equip" />
        <StatCard icon={Award} label={t("Trainings")} value={counts.trainings} accent="blue" testId="hr-acc-stat-train" />
      </div>

      {counts.terminations > 0 && (
        <Card className="border-2 border-red-400 bg-red-50 p-4" data-testid="hr-acc-terminated">
          <div className="flex items-center gap-2 text-red-800 font-bold">
            <AlertOctagon className="w-5 h-5" /> {t("TERMINATED")} · {counts.terminations} {t("record(s) on file")}
          </div>
        </Card>
      )}

      {Object.keys(byKind).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(byKind).map(([k, n]) => (
            <span key={k} className="inline-flex items-center px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-mono font-bold">
              {KIND_LABEL[k] || k}: {n}
            </span>
          ))}
        </div>
      )}

      {/* Outstanding equipment table */}
      {data.outstanding_equipment?.length > 0 && (
        <Card className="overflow-x-auto" data-testid="hr-acc-outstanding-table">
          <div className="bg-red-100 border-b-2 border-red-300 px-4 py-2 font-bold text-red-900 text-sm">
            <Wrench className="w-4 h-4 inline mr-2" /> {t("OUTSTANDING EQUIPMENT — must be recovered before offboarding")}
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Item")}</th>
                <th className="text-left px-3 py-2">{t("Serial")}</th>
                <th className="text-right px-3 py-2">{t("Qty")}</th>
                <th className="text-left px-3 py-2">{t("Checked Out")}</th>
                <th className="text-left px-3 py-2">{t("Project")}</th>
              </tr>
            </thead>
            <tbody>
              {data.outstanding_equipment.map((e, i) => (
                <tr key={`${e.checkout_id}-${e.line_index}-${i}`} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-semibold">{e.name || "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{e.serial || "—"}</td>
                  <td className="px-3 py-2 text-right">{e.qty || 1}</td>
                  <td className="px-3 py-2 font-mono text-xs">{(e.checkout_date || "").slice(0, 10)}</td>
                  <td className="px-3 py-2">{e.project_number || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* FL records table */}
      {data.fl_records?.length > 0 && (
        <Card className="overflow-x-auto" data-testid="hr-acc-fl-table">
          <div className="bg-slate-100 border-b-2 border-slate-300 px-4 py-2 font-bold text-slate-900 text-sm">
            <FileText className="w-4 h-4 inline mr-2" /> {t("Field Leadership Records")}
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Date")}</th>
                <th className="text-left px-3 py-2">{t("Kind")}</th>
                <th className="text-left px-3 py-2">{t("Supervisor")}</th>
                <th className="text-left px-3 py-2">{t("Project")}</th>
              </tr>
            </thead>
            <tbody>
              {data.fl_records.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-mono text-xs">{(r.occurred_at || "").slice(0, 10)}</td>
                  <td className="px-3 py-2">
                    <span className="inline-block px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-xs font-mono">{KIND_LABEL[r.kind] || r.kind}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-700">{r.supervisor_name || "—"}</td>
                  <td className="px-3 py-2 text-slate-700">
                    <span className="font-mono text-xs text-slate-500">{r.project_number}</span> {r.project_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Trainings */}
      {data.trainings?.length > 0 && (
        <Card className="overflow-x-auto" data-testid="hr-acc-train-table">
          <div className="bg-blue-100 border-b-2 border-blue-300 px-4 py-2 font-bold text-blue-900 text-sm">
            <Award className="w-4 h-4 inline mr-2" /> {t("Training Records")}
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Track")}</th>
                <th className="text-left px-3 py-2">{t("Completed")}</th>
              </tr>
            </thead>
            <tbody>
              {data.trainings.map((tr, i) => (
                <tr key={tr.id || i} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-semibold">{tr.track_name || tr.track_slug || "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{(tr.completed_at || "").slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent, testId }) {
  const cls = {
    purple: "border-purple-200 bg-purple-50",
    amber: "border-amber-400 bg-amber-50",
    red: "border-red-400 bg-red-50",
    emerald: "border-emerald-300 bg-emerald-50",
    blue: "border-blue-200 bg-blue-50",
    slate: "border-slate-200 bg-slate-50",
  }[accent || "slate"];
  return (
    <Card className={`border-2 ${cls} p-4`} data-testid={testId}>
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className="font-display text-2xl font-black mt-1">{value ?? 0}</div>
    </Card>
  );
}
