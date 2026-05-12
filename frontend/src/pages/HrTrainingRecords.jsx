// HR — Training Records (read-only).
// Pulls from training_track_records (populated when an employee finishes
// a Training Hub track). Empty state shows guidance for HR until the
// collection has rows.
import React, { useCallback, useEffect, useState } from "react";
import { Loader2, Search, GraduationCap } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import HrPageShell from "@/components/HrPageShell";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

export default function HrTrainingRecords() {
  const { t } = useT();
  const [employee, setEmployee] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRows = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (employee.trim()) params.employee = employee.trim();
      const r = await api.get("/hr/training-records", { params });
      setItems(r.data?.items || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load training records"));
    } finally {
      setLoading(false);
    }
  }, [employee, t]);

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <HrPageShell title="Training Records" kicker="HR · Compliance Roster">
      <Card className="p-4 mb-5 border-2 border-purple-200 bg-purple-50/30">
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Employee Filter")}</label>
            <Input value={employee} onChange={(e) => setEmployee(e.target.value)} onKeyDown={(e) => e.key === "Enter" && fetchRows()} placeholder={t("Name contains...")} className={inputCls} data-testid="hr-train-filter" />
          </div>
          <Button onClick={fetchRows} disabled={loading} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-train-apply">
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {t("Apply")}
          </Button>
        </div>
      </Card>

      {loading ? (
        <Card className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 mx-auto animate-spin" /></Card>
      ) : items.length === 0 ? (
        <Card className="p-10 text-center text-slate-500" data-testid="hr-train-empty">
          <GraduationCap className="w-10 h-10 mx-auto text-slate-400 mb-3" />
          <div className="font-bold text-base text-slate-900">{t("No training records yet")}</div>
          <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
            {t("Training completions appear here automatically once an employee finishes a track in the Training Hub. The HR-side report stays read-only.")}
          </p>
        </Card>
      ) : (
        <Card className="overflow-x-auto" data-testid="hr-train-table">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Employee")}</th>
                <th className="text-left px-3 py-2">{t("Track")}</th>
                <th className="text-left px-3 py-2">{t("Completed")}</th>
                <th className="text-left px-3 py-2">{t("Score")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r, i) => (
                <tr key={r.id || i} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-semibold">{r.employee_name || "—"}</td>
                  <td className="px-3 py-2">{r.track_name || r.track_slug || "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{(r.completed_at || "").slice(0, 10)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.score != null ? `${r.score}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </HrPageShell>
  );
}
