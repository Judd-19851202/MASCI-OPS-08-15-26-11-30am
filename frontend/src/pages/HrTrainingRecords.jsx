// HR — Training Records (read-only).
// iter350 · UNION of Safety source-of-truth (safety_training_records)
// + legacy HR curriculums (training_track_records). Adds a source
// filter pill, an Expires column, and a linkage badge for any record
// whose employee_id couldn't resolve to the roster (so HR can see
// data-hygiene gaps without records disappearing).
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Search, GraduationCap, AlertTriangle, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import HrPageShell from "@/components/HrPageShell";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

const SOURCE_PILL = {
  safety: "bg-cyan-100 text-cyan-900 border-cyan-300",
  track:  "bg-purple-100 text-purple-900 border-purple-300",
};

function expStatus(r) {
  if (!r.expiration_date) return "none";
  const today = new Date().toISOString().slice(0, 10);
  const thirty = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  if (r.expiration_date < today) return "expired";
  if (r.expiration_date <= thirty) return "soon";
  return "ok";
}
const EXP_PILL = {
  expired: "bg-red-100 text-red-900 border-red-300",
  soon:    "bg-amber-100 text-amber-900 border-amber-300",
  ok:      "bg-emerald-100 text-emerald-900 border-emerald-300",
  none:    "bg-slate-100 text-slate-700 border-slate-300",
};

export default function HrTrainingRecords() {
  const { t } = useT();
  const [employee, setEmployee] = useState("");
  const [source, setSource] = useState("");  // "" | "safety" | "track"
  const [items, setItems] = useState([]);
  const [counts, setCounts] = useState({ safety: 0, track: 0, total: 0, unlinked: 0 });
  const [loading, setLoading] = useState(true);

  const fetchRows = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (employee.trim()) params.employee = employee.trim();
      if (source) params.source = source;
      const r = await api.get("/hr/training-records", { params });
      setItems(r.data?.items || []);
      setCounts(r.data?.counts || { safety: 0, track: 0, total: 0, unlinked: 0 });
    } catch (err) {
      toast.error(operationalError(err, t("Training records temporarily unavailable. Try again in a moment."), t("Your HR session expired. Please sign in again.")));
    } finally {
      setLoading(false);
    }
  }, [employee, source, t]);

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  const summary = useMemo(() => counts, [counts]);

  return (
    <HrPageShell title="Training Records" kicker="HR · COMPLIANCE ROSTER · READ-ONLY">
      <Card className="p-4 mb-5 border-2 border-purple-200 bg-purple-50/30">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[180px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Employee Filter")}</label>
            <Input value={employee} onChange={(e) => setEmployee(e.target.value)} onKeyDown={(e) => e.key === "Enter" && fetchRows()} placeholder={t("Name contains...")} className={inputCls} data-testid="hr-train-filter" />
          </div>
          <div className="min-w-[160px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold block mb-1">{t("Source")}</label>
            <div className="flex gap-1" data-testid="hr-train-source-pills">
              {[["", "All"], ["safety", "Safety"], ["track", "Tracks"]].map(([k, label]) => (
                <button key={k} type="button" onClick={() => setSource(k)} data-testid={`hr-train-source-${k || "all"}`} className={`px-3 h-10 rounded border-2 text-xs font-mono uppercase tracking-[0.12em] font-bold ${source === k ? "bg-purple-700 text-white border-purple-700" : "bg-white text-slate-700 border-slate-300 hover:border-purple-400"}`}>
                  {t(label)}
                </button>
              ))}
            </div>
          </div>
          <Button onClick={fetchRows} disabled={loading} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-train-apply">
            {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
            {t("Apply")}
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-mono uppercase tracking-[0.15em]" data-testid="hr-train-counts">
          <span className="px-2 py-1 rounded bg-slate-100 border border-slate-300 text-slate-700"><strong>{summary.total}</strong> {t("Total")}</span>
          <span className="px-2 py-1 rounded bg-cyan-100 border border-cyan-300 text-cyan-900"><strong>{summary.safety}</strong> {t("Safety")}</span>
          <span className="px-2 py-1 rounded bg-purple-100 border border-purple-300 text-purple-900"><strong>{summary.track}</strong> {t("Tracks")}</span>
          {summary.unlinked > 0 && (
            <span className="px-2 py-1 rounded bg-amber-100 border border-amber-300 text-amber-900 inline-flex items-center gap-1" data-testid="hr-train-unlinked-badge">
              <ShieldAlert className="w-3 h-3" /> <strong>{summary.unlinked}</strong> {t("Unlinked")}
            </span>
          )}
        </div>
      </Card>

      {loading ? (
        <Card className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 mx-auto animate-spin" /></Card>
      ) : items.length === 0 ? (
        <Card className="p-10 text-center text-slate-500" data-testid="hr-train-empty">
          <GraduationCap className="w-10 h-10 mx-auto text-slate-400 mb-3" />
          <div className="font-bold text-base text-slate-900">{t("No training records yet")}</div>
          <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
            {t("Training records appear here automatically when Safety logs a certification or an employee finishes a Training Center track. Read-only — uploads and edits live in the Safety Portal.")}
          </p>
        </Card>
      ) : (
        <Card className="overflow-x-auto" data-testid="hr-train-table">
          <table className="w-full text-sm min-w-[900px]">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Employee")}</th>
                <th className="text-left px-3 py-2">{t("Training")}</th>
                <th className="text-left px-3 py-2">{t("Type")}</th>
                <th className="text-left px-3 py-2">{t("Completed")}</th>
                <th className="text-left px-3 py-2">{t("Expires")}</th>
                <th className="text-center px-3 py-2">{t("Source")}</th>
                <th className="text-center px-3 py-2">{t("Status")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r, i) => {
                const st = expStatus(r);
                const label = st === "expired" ? t("Expired") : st === "soon" ? t("Expiring 30d") : st === "ok" ? t("Current") : t("No expiry");
                const unlinked = r.linkage_method === "unlinked";
                return (
                  <tr key={r.id || i} className={`border-t border-slate-100 hover:bg-slate-50 ${st === "expired" ? "bg-red-50/50" : ""}`}>
                    <td className="px-3 py-2 font-semibold">
                      {r.employee_name || r.linked_employee_name || "—"}
                      {unlinked && (
                        <span className="ml-1 inline-flex items-center gap-1 text-amber-700" title={t("Employee linkage missing — no matching roster profile.")}>
                          <ShieldAlert className="w-3 h-3" />
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">{r.training_name || r.track_name || r.track_slug || "—"}</td>
                    <td className="px-3 py-2 text-slate-600 text-xs font-mono">{r.certification_type || "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs">{(r.completed_date || r.completed_at || "").slice(0, 10) || "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {r.expiration_date || <span className="text-slate-400">—</span>}
                      {st === "expired" && <AlertTriangle className="w-3.5 h-3.5 text-red-600 inline ml-1" />}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${SOURCE_PILL[r.source] || "bg-slate-100 text-slate-700 border-slate-300"}`} data-testid={`hr-train-source-pill-${r.id || i}`}>
                        {r.source === "safety" ? t("Safety") : r.source === "track" ? t("Track") : "—"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${EXP_PILL[st]}`}>{label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </HrPageShell>
  );
}
