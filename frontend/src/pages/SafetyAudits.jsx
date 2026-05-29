// SafetyAudits — read-only roll-up of every site safety audit and
// jobsite inspection filed from the field. Same /api/inspections
// endpoint that powers the field submission form; this view lets
// Safety filter, drill in, and link to corrective actions.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  ShieldAlert, Search, Loader2, ChevronRight, CheckCircle2, AlertTriangle, Plus,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import SafetyShell from "@/components/SafetyShell";
import { getSafetyToken } from "@/lib/safetyAuth";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const STATUS_PILL = {
  Pass:   "bg-emerald-100 text-emerald-900 border-emerald-300",
  Fail:   "bg-red-100 text-red-900 border-red-300",
  Open:   "bg-amber-100 text-amber-900 border-amber-300",
  Closed: "bg-emerald-100 text-emerald-900 border-emerald-300",
};

export default function SafetyAudits() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await axios.get(`${API}/inspections`, auth());
        setItems(Array.isArray(r.data) ? r.data : []);
      } catch (e) {
        toast.error(operationalError(e,
          t("Audits & Inspections temporarily unavailable. Try again in a moment."),
          t("Your Safety session expired. Please sign in again.")));
      } finally { setLoading(false); }
    })();
  }, []);  // eslint-disable-line

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (statusFilter !== "all") {
        const s = i.overall_status || (i.deficiencies_count > 0 ? "Fail" : "Pass");
        if (s !== statusFilter) return false;
      }
      if (from && (i.inspection_date || "") < from) return false;
      if (to && (i.inspection_date || "") > to) return false;
      if (q) {
        const blob = `${i.location || ""} ${i.inspector_name || ""} ${i.project_name || ""} ${i.notes || ""}`.toLowerCase();
        if (!blob.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [items, q, statusFilter, from, to]);

  const totalDef = filtered.reduce((sum, i) => sum + (i.deficiencies_count || 0), 0);

  return (
    <SafetyShell title={t("Audits & Inspections")} kicker={t("Safety Review")}>
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4" data-testid="safety-audits-page">
        <header className="bg-white border border-slate-200 border-l-4 border-l-emerald-600 rounded-md p-5 flex flex-col sm:flex-row sm:items-start gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <ShieldAlert className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
            <div className="min-w-0 flex-1">
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-emerald-700 font-bold">
                {t("Safety Portal")}
              </span>
              <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight mt-0.5">
                {t("Audits & Inspections")}
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                {t("Every site safety audit and Job Site Safety Inspection — the records the field submits through")} <code className="text-xs">/safety/inspections</code> {t("— organized for Safety review and corrective-action close-out.")}
              </p>
            </div>
          </div>
          {/* iter322-C · Start new Site Inspection — surfacing the
              authenticated form path directly inside the Safety Portal
              review surface so signed-in Safety users never have to
              hunt for the entry point. */}
          <Link
            to="/safety/inspections/new"
            data-testid="audits-start-new-inspection"
            className="shrink-0 inline-flex items-center justify-center h-10 px-4 rounded-md bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            {t("New Site Inspection")}
          </Link>
        </header>

        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-3">
          <SummaryCard label={t("Total")} value={filtered.length} icon={ShieldAlert} accent="bg-slate-700" testId="audits-summary-total" />
          <SummaryCard label={t("With Deficiencies")} value={filtered.filter((i) => (i.deficiencies_count || 0) > 0).length} icon={AlertTriangle} accent="bg-amber-600" testId="audits-summary-defs" />
          <SummaryCard label={t("Open Deficiencies")} value={totalDef} icon={AlertTriangle} accent="bg-red-700" testId="audits-summary-open" />
          <SummaryCard label={t("Pass")} value={filtered.filter((i) => (i.deficiencies_count || 0) === 0).length} icon={CheckCircle2} accent="bg-emerald-700" testId="audits-summary-pass" />
        </div>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-md p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <Input className="pl-7 h-9" placeholder={t("Search location, inspector, project, notes…")} value={q} onChange={(e) => setQ(e.target.value)} data-testid="audits-search" />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-9" data-testid="audits-status"><SelectValue placeholder={t("Status")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("All results")}</SelectItem>
              <SelectItem value="Pass">Pass</SelectItem>
              <SelectItem value="Fail">Fail</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="h-9" value={from} onChange={(e) => setFrom(e.target.value)} data-testid="audits-from" />
          <Input type="date" className="h-9" value={to} onChange={(e) => setTo(e.target.value)} data-testid="audits-to" />
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          {loading ? (
            <div className="text-center py-12 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center text-slate-500" data-testid="audits-empty">
              <ShieldAlert className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="italic">{t("No audits or inspections match these filters.")}</p>
            </div>
          ) : (
            <table className="w-full text-sm" data-testid="audits-table">
              <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em] text-[10px]">
                <tr>
                  <th className="text-left px-3 py-2">{t("Date")}</th>
                  <th className="text-left px-3 py-2">{t("Location / Project")}</th>
                  <th className="text-left px-3 py-2">{t("Inspector")}</th>
                  <th className="text-left px-3 py-2">{t("Deficiencies")}</th>
                  <th className="text-left px-3 py-2">{t("Result")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i, idx) => {
                  const defs = i.deficiencies_count || 0;
                  const result = defs === 0 ? "Pass" : "Fail";
                  return (
                    <tr key={i.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`audit-row-${idx}`}>
                      <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">{i.inspection_date || "—"}</td>
                      <td className="px-3 py-2 font-bold truncate max-w-[14rem]">
                        {i.location || i.project_name || "Site inspection"}
                      </td>
                      <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">{i.inspector_name || "—"}</td>
                      <td className="px-3 py-2 font-mono font-bold">{defs}</td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_PILL[result] || "bg-slate-100"}`}>
                          {result}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Link to={`/inspections/${i.id}`} className="text-cyan-700 hover:underline font-bold inline-flex items-center" data-testid={`audit-open-${idx}`}>
                          {t("Open")} <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <p className="text-xs text-slate-500 font-mono">
          {filtered.length} {t("of")} {items.length} {t("audits/inspections shown")}
        </p>
      </div>
    </SafetyShell>
  );
}

function SummaryCard({ label, value, icon: Icon, accent, testId }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid={testId}>
      <div className="flex items-center gap-2">
        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-md ${accent} text-white`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">{label}</div>
      </div>
      <div className="font-display text-2xl font-black mt-1">{value}</div>
    </div>
  );
}
