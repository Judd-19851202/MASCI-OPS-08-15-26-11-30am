// Phase 10A · Safety/Admin Excavation Oversight Surface
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, AlertTriangle, CheckCircle2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";

const STATUSES = ["Submitted", "Needs Review", "Action Required", "Pending Verification", "Reviewed", "Closed", "Reopened"];

export default function ExcavationOversight() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [reviewing, setReviewing] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      const r = await api.get("/trench-safety/excavations", { params });
      setItems(r.data?.items || []);
    } catch { /* swallow */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [JSON.stringify(filters)]); // eslint-disable-line

  return (
    <TrenchSafetyShell active="excavations" title={t("Excavation Oversight")} kicker={t("Public field submissions · review and close")}>
      <p className="text-slate-700 mb-3 text-sm">{t("Field crews submit excavation records from the Public Safety Tile. Coaching language. No punitive vocabulary.")}</p>

      <div className="bg-white border border-slate-200 rounded p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2" data-testid="exc-filters">
        <Input placeholder={t("Project name")} value={filters.project_name || ""} onChange={(e) => setFilters({ ...filters, project_name: e.target.value })} data-testid="exc-filter-project" />
        <Input placeholder={t("Supervisor")} value={filters.supervisor_name || ""} onChange={(e) => setFilters({ ...filters, supervisor_name: e.target.value })} data-testid="exc-filter-supervisor" />
        <Select value={filters.status || "__all"} onValueChange={(v) => setFilters({ ...filters, status: v === "__all" ? "" : v })}>
          <SelectTrigger data-testid="exc-filter-status"><SelectValue placeholder={t("Status")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all">{t("All Statuses")}</SelectItem>
            {STATUSES.map((s) => <SelectItem key={s} value={s}>{t(s)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Input type="number" placeholder={t("Min depth ft")} value={filters.depth_min || ""} onChange={(e) => setFilters({ ...filters, depth_min: e.target.value })} data-testid="exc-filter-depth" />
        <Button variant="outline" size="sm" onClick={() => setFilters({})} data-testid="exc-filter-reset">{t("Reset")}</Button>
      </div>

      <div className="mt-3" data-testid="exc-list">
        {loading ? <Loader2 className="w-5 h-5 animate-spin text-cyan-700" /> :
          items.length === 0 ? <div className="text-sm italic text-slate-500" data-testid="exc-list-empty">— {t("no excavation records")} —</div> :
          <ul className="space-y-2">
            {items.map((d) => (
              <li key={d.id} className="bg-white border border-slate-200 rounded p-3" data-testid={`exc-row-${d.id}`}>
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <div className="font-mono font-black text-lg text-slate-900">{d.id}</div>
                    <div className="text-sm text-slate-700">{d.project_name} · {d.supervisor_name} · {d.date_of_work}</div>
                    <div className="text-xs text-slate-500">{t("Depth")}: {d.depth_ft ?? "—"} ft · {t("Protective")}: {d.protective_system} · {t("Soil")}: {d.soil_classification}</div>
                  </div>
                  <div className="text-right">
                    <div className={"text-[10px] uppercase tracking-[0.12em] px-2 py-0.5 rounded border font-bold " +
                      (d.status === "Action Required" ? "border-red-300 bg-red-50 text-red-800" :
                       d.status === "Needs Review" ? "border-amber-300 bg-amber-50 text-amber-800" :
                       d.status === "Closed" ? "border-emerald-300 bg-emerald-50 text-emerald-800" :
                       "border-slate-300 bg-slate-50 text-slate-700")}>{t(d.status)}</div>
                    <Button size="sm" variant="outline" onClick={() => setReviewing(d)} data-testid={`exc-review-${d.id}`} className="mt-2"><MessageSquare className="w-3.5 h-3.5 mr-1" /> {t("Review")}</Button>
                  </div>
                </div>
                {d.flags?.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {d.flags.map((fl, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs">
                        <AlertTriangle className="w-3 h-3 mt-0.5 text-amber-700 shrink-0" />
                        <span><b className="text-amber-900">{t(fl.level)}</b> · {t(fl.message)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        }
      </div>
      <ReviewDialog rec={reviewing} onClose={(refresh) => { setReviewing(null); if (refresh) load(); }} />
    </TrenchSafetyShell>
  );
}

function ReviewDialog({ rec, onClose }) {
  const { t } = useT();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  if (!rec) return null;
  async function act(action) {
    setBusy(true);
    try {
      await api.post(`/trench-safety/excavations/${rec.id}/review`, { action, coaching_note: note });
      toast.success(t("Saved"));
      onClose(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed");
    } finally { setBusy(false); }
  }
  return (
    <Dialog open={true} onOpenChange={() => onClose(false)}>
      <DialogContent className="max-w-lg" data-testid="exc-review-dialog">
        <DialogHeader><DialogTitle>{rec.id} · {t("Review")}</DialogTitle></DialogHeader>
        <div className="space-y-2 text-sm">
          <div>{rec.project_name} · {rec.supervisor_name}</div>
          <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("Coaching note (optional)")} rows={3} data-testid="exc-review-note" />
        </div>
        <DialogFooter className="flex-wrap gap-2">
          <Button variant="outline" onClick={() => act("request_clarification")} disabled={busy} data-testid="exc-action-clarify">{t("Request Clarification")}</Button>
          <Button variant="outline" onClick={() => act("review")} disabled={busy} data-testid="exc-action-review">{t("Mark Reviewed")}</Button>
          <Button onClick={() => act("close")} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800" data-testid="exc-action-close"><CheckCircle2 className="w-4 h-4 mr-1" /> {t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
