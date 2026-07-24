// SafetyIncidents — read-only roll-up of every incident & near-miss
// report filed from the field. Safety reviewers can filter by
// severity / status / type / date, drill into detail, and link out
// to corrective actions. Writes happen in the Incident Intelligence
// engine flow at /incidents/report; this view is review-only.
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Search, Loader2, AlertTriangle, ChevronRight, Filter,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import SafetyShell from "@/components/SafetyShell";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";

// SEV_PILL — colour bound to severity DATA, not theme.
// Reserved as the primary urgent-scan signal (do not desaturate).
const SEV_PILL = {
  Critical: "bg-red-700 text-white",
  High:     "bg-red-100 text-red-900 border-red-300",
  Medium:   "bg-amber-100 text-amber-900 border-amber-300",
  Low:      "bg-emerald-100 text-emerald-900 border-emerald-300",
};

// STATUS_PILL — workflow state, not severity. Demoted to neutral
// slate so the eye elevates SEV_PILL as the danger signal. (iter437
// IV-BETA.5A · false urgency removal — see SAFETY_ESCALATION_HIERARCHY
// _MAP.md §IV.)
const STATUS_PILL = {
  Open:          "bg-slate-100 text-slate-800",
  Investigating: "bg-slate-100 text-slate-800",
  Closed:        "bg-slate-100 text-slate-500",
};

export default function SafetyIncidents() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [sev, setSev] = useState("all");
  const [status, setStatus] = useState("all");
  const [type, setType] = useState("all");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await api.get("/incidents");
        setItems(Array.isArray(r.data) ? r.data : []);
      } catch (e) {
        toast.error(operationalError(e,
          t("Incidents temporarily unavailable. Try again in a moment."),
          t("Your Safety session expired. Please sign in again.")));
      } finally { setLoading(false); }
    })();
  }, [t]);   

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (sev !== "all" && (i.severity || "").toLowerCase() !== sev.toLowerCase()) return false;
      if (status !== "all" && (i.status || "Open") !== status) return false;
      if (type !== "all" && (i.incident_type || "").toLowerCase() !== type.toLowerCase()) return false;
      if (from && (i.incident_date || "") < from) return false;
      if (to && (i.incident_date || "") > to) return false;
      if (q) {
        const blob = `${i.title || ""} ${i.description || ""} ${i.project_name || ""} ${i.injured_name || ""} ${i.supervisor || ""}`.toLowerCase();
        if (!blob.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [items, q, sev, status, type, from, to]);

  return (
    <SafetyShell title={t("Incidents & Near Misses")} kicker={t("Safety Review")}>
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4" data-testid="safety-incidents-page">
        <header className="bg-white border border-slate-200 border-l-4 border-l-red-700 rounded-md p-5 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-800 text-white shrink-0">
            <ClipboardCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
              Safety Portal · Incidents
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              {t("Incidents & Near Misses")}
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              {t("Read-only review of every incident and near-miss filed from the field. Filter by severity, project, or employee.")}
            </p>
          </div>
          {/* TRACK 14.0-ELITE-OPS-B (iter510 friction fix · 2026-02-15):
              5:30 AM iPad audit found users scanned the header for a
              "New Incident" button and felt lost when the only entry
              point was a hyperlink buried in body copy. Promote it to
              a real CTA on the right rail. */}
          <Link
            to="/incidents/report"
            data-testid="incidents-submit-field-cta"
            className="hidden sm:inline-flex items-center gap-2 self-start px-4 py-2 rounded-md border-2 border-slate-800 text-slate-800 hover:bg-slate-800 hover:text-white transition-colors text-sm font-bold whitespace-nowrap"
          >
            <ClipboardCheck className="w-4 h-4" />
            {t("Submit Field Incident →")}
          </Link>
        </header>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-md p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-2">
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <Input className="pl-7 h-9" placeholder={t("Search title, employee, supervisor, job…")} value={q} onChange={(e) => setQ(e.target.value)} data-testid="incidents-search" />
          </div>
          <Select value={sev} onValueChange={setSev}>
            <SelectTrigger className="h-9" data-testid="incidents-severity"><SelectValue placeholder={t("Severity")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("All severities")}</SelectItem>
              <SelectItem value="Critical">Critical</SelectItem>
              <SelectItem value="High">High</SelectItem>
              <SelectItem value="Medium">Medium</SelectItem>
              <SelectItem value="Low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9" data-testid="incidents-status"><SelectValue placeholder={t("Status")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("All statuses")}</SelectItem>
              <SelectItem value="Open">Open</SelectItem>
              <SelectItem value="Investigating">Investigating</SelectItem>
              <SelectItem value="Closed">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="h-9" value={from} onChange={(e) => setFrom(e.target.value)} data-testid="incidents-from" placeholder={t("From")} />
          <Input type="date" className="h-9" value={to} onChange={(e) => setTo(e.target.value)} data-testid="incidents-to" placeholder={t("To")} />
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          {loading ? (
            <div className="text-center py-12 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center text-slate-500" data-testid="incidents-empty">
              <ClipboardCheck className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="italic">{t("No incidents match these filters.")}</p>
            </div>
          ) : (
            <table className="w-full text-sm" data-testid="incidents-table">
              <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em] text-[10px]">
                <tr>
                  <th className="text-left px-3 py-2">{t("Date")}</th>
                  <th className="text-left px-3 py-2">{t("Title")}</th>
                  <th className="text-left px-3 py-2">{t("Severity")}</th>
                  <th className="text-left px-3 py-2">{t("Status")}</th>
                  <th className="text-left px-3 py-2">{t("Project / Job")}</th>
                  <th className="text-left px-3 py-2">{t("Reporter")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i, idx) => (
                  <tr key={i.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`incident-row-${idx}`}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">{i.incident_date || "—"}</td>
                    <td className="px-3 py-2 font-bold max-w-xs truncate">{i.title || "Incident"}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${SEV_PILL[i.severity] || "bg-slate-100"}`}>
                        {i.severity || "—"}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_PILL[i.status] || "bg-slate-100"}`}>
                        {i.status || "Open"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">{i.project_name || i.project_number || "—"}</td>
                    <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">{i.reporter_name || i.supervisor || "—"}</td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        to={`/safety-portal/incidents/${i.id}`}
                        state={{
                          from: {
                            key: "safety-incidents",
                            label: "Incident Center",
                            path: "/safety-portal/incidents",
                          },
                        }}
                        className="text-slate-800 hover:underline font-bold inline-flex items-center"
                        data-testid={`incident-open-${idx}`}
                      >
                        {t("Open")} <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <p className="text-xs text-slate-500 font-mono">
          {filtered.length} {t("of")} {items.length} {t("incidents shown")}
        </p>
      </div>
    </SafetyShell>
  );
}
