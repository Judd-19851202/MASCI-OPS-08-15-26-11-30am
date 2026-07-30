// Admin — Employee Terminations Dashboard.
// Dedicated HR-grade view of every Employee Termination record:
// rehire-eligibility filter chips, outstanding-equipment status column,
// law-enforcement-involved badge, separation-type column, supervisor +
// project columns, and per-row "View" / "PDF" actions. Mirrors the
// look-and-feel of the other admin record-list pages.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertOctagon, CheckCircle2, ShieldAlert, FileText,
  Wrench, Loader2, Search, Download,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { PortalShell } from "@/design-system";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const inputCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";

const REHIRE_CHIP = {
  Yes: "bg-emerald-100 text-emerald-900 border-emerald-300",
  No: "bg-red-100 text-red-900 border-red-300",
  Conditional: "bg-amber-100 text-amber-900 border-amber-300",
};

const SEP_TYPE_SHORT = {
  "Safety Violation": "Safety",
  "Company Policy Violation": "Policy",
  "Attendance Issues": "Attendance",
  "Performance Issues": "Performance",
  "Insubordination": "Insubordination",
  "Drug/Alcohol Violation": "Drug/Alcohol",
  "Equipment Abuse/Damage": "Equipment Damage",
  "Workplace Violence/Threats": "Violence/Threats",
  "Reduction in Workforce": "Reduction",
  "End of Project": "End of Project",
  "Self Termination (Quit)": "Quit",
  "Job Abandonment": "Abandonment",
  "Failure to Meet Training Requirements": "Training",
  "Other": "Other",
};

const fmtDate = (iso) => {
  if (!iso) return "—";
  try {
    return formatPlatformDate(iso);
  } catch { return iso; }
};

export default function AdminTerminations() {
  const { t } = useT();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [rehireFilter, setRehireFilter] = useState("all");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/field-leadership", {
        params: { kind: "employee_termination", limit: 500 },
      });
      setRows(r.data?.items || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load terminations"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { refresh(); }, [refresh]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter((r) => {
      const d = r.details || {};
      const rehire = d.rehire_eligibility || "—";
      if (rehireFilter !== "all" && rehire !== rehireFilter) return false;
      if (!needle) return true;
      const hay = [
        r.employee_name, r.employee_id, r.supervisor_name,
        r.project_number, r.project_name, d.separation_type,
      ].filter(Boolean).join(" ").toLowerCase();
      return hay.includes(needle);
    });
  }, [rows, q, rehireFilter]);

  const stats = useMemo(() => {
    const total = rows.length;
    const byRehire = { Yes: 0, No: 0, Conditional: 0 };
    let withOutstanding = 0;
    let withLawEnforcement = 0;
    for (const r of rows) {
      const d = r.details || {};
      if (byRehire[d.rehire_eligibility] !== undefined) byRehire[d.rehire_eligibility] += 1;
      const outs = Array.isArray(d.outstanding_equipment_acknowledged)
        ? d.outstanding_equipment_acknowledged : [];
      if (outs.some((o) => o.status === "still_outstanding")) withOutstanding += 1;
      if (d.law_enforcement_involved === "Yes") withLawEnforcement += 1;
    }
    return { total, byRehire, withOutstanding, withLawEnforcement };
  }, [rows]);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Admin · Terminations"
      pageTitle={t("Employee Terminations")}
      subtitle={t("Termination documentation · resignation tracking · policy enforcement · outstanding-equipment accountability")}
      sideNav={renderAdminRouteSideNav()}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6" data-testid="admin-terminations-page">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">
          {t("Restricted · HR Documentation")}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1">
          {t("Employee Terminations")}
        </h1>
        <p className="text-slate-600 mt-2 max-w-2xl">
          {t("Termination documentation · resignation tracking · policy enforcement · outstanding-equipment accountability")}
        </p>

        {/* STATS STRIP */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="terminations-stats">
          <Card className="p-3 border-2 border-slate-300">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">{t("Total")}</div>
            <div className="font-display text-2xl font-black mt-1">{stats.total}</div>
          </Card>
          <Card className="p-3 border-2 border-emerald-300">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-emerald-700">{t("Rehire · Yes")}</div>
            <div className="font-display text-2xl font-black mt-1 text-emerald-700">{stats.byRehire.Yes}</div>
          </Card>
          <Card className="p-3 border-2 border-red-300">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-red-700">{t("Rehire · No")}</div>
            <div className="font-display text-2xl font-black mt-1 text-red-700">{stats.byRehire.No}</div>
          </Card>
          <Card className="p-3 border-2 border-amber-300">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-amber-700">{t("Outstanding Equip")}</div>
            <div className="font-display text-2xl font-black mt-1 text-amber-700">{stats.withOutstanding}</div>
          </Card>
          <Card className="p-3 border-2 border-red-600">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-red-800">{t("Law Enforcement")}</div>
            <div className="font-display text-2xl font-black mt-1 text-red-800">{stats.withLawEnforcement}</div>
          </Card>
        </div>

        {/* FILTERS */}
        <Card className="p-4 mt-6 flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[200px]">
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("Search by employee, supervisor, project, or separation type…")}
              className={inputCls}
              data-testid="terminations-search"
            />
          </div>
          <div className="flex items-center gap-1.5">
            {["all", "Yes", "No", "Conditional"].map((opt) => (
              <button
                key={opt}
                onClick={() => setRehireFilter(opt)}
                className={`px-2.5 py-1.5 rounded border-2 text-xs font-bold uppercase tracking-wide ${
                  rehireFilter === opt
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
                }`}
                data-testid={`terminations-filter-${opt.toLowerCase()}`}
              >
                {opt === "all" ? t("All") : opt}
              </button>
            ))}
          </div>
          <Button
            onClick={refresh}
            variant="outline"
            size="sm"
            disabled={loading}
            data-testid="terminations-refresh"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Refresh")}
          </Button>
        </Card>

        {/* TABLE */}
        <div className="mt-6">
          {loading ? (
            <Card className="p-8 text-center text-slate-600">
              <Loader2 className="w-5 h-5 animate-spin inline mr-2" /> {t("Loading…")}
            </Card>
          ) : filtered.length === 0 ? (
            <Card className="p-10 text-center text-slate-500 border-2 border-dashed">
              {rows.length === 0
                ? t("No termination records yet.")
                : t("No records match the current filter.")}
            </Card>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse bg-white border border-slate-200 rounded-md">
                <thead className="bg-slate-50">
                  <tr className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-700">
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Date")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Employee")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Supervisor")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Job")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Type")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Rehire")}</th>
                    <th className="text-left p-3 border-b-2 border-slate-200">{t("Flags")}</th>
                    <th className="text-right p-3 border-b-2 border-slate-200"></th>
                  </tr>
                </thead>
                <tbody data-testid="terminations-table">
                  {filtered.map((r) => {
                    const d = r.details || {};
                    const outs = Array.isArray(d.outstanding_equipment_acknowledged)
                      ? d.outstanding_equipment_acknowledged : [];
                    const stillOutstanding = outs.filter((o) => o.status === "still_outstanding").length;
                    const returnedAtTerm = outs.filter((o) => o.status === "returned_at_termination").length;
                    const rehire = d.rehire_eligibility || "—";
                    const sepType = d.separation_type || "—";
                    return (
                      <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50"
                          data-testid={`termination-row-${r.id}`}>
                        <td className="p-3 align-top text-sm whitespace-nowrap font-mono">{fmtDate(r.occurred_at || r.created_at)}</td>
                        <td className="p-3 align-top">
                          <div className="font-bold text-sm">{r.employee_name || "—"}</div>
                          {r.employee_position && (
                            <div className="text-[11px] text-slate-500">{r.employee_position}</div>
                          )}
                        </td>
                        <td className="p-3 align-top text-sm">{r.supervisor_name || "—"}</td>
                        <td className="p-3 align-top text-sm">
                          <div className="font-mono text-xs">{r.project_number || "—"}</div>
                          <div className="text-[11px] text-slate-500 line-clamp-1 max-w-[200px]">{r.project_name || ""}</div>
                        </td>
                        <td className="p-3 align-top">
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 border border-slate-300 text-slate-900">
                            {SEP_TYPE_SHORT[sepType] || sepType}
                          </span>
                        </td>
                        <td className="p-3 align-top">
                          <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold border ${
                            REHIRE_CHIP[rehire] || "bg-slate-100 text-slate-700 border-slate-300"
                          }`}>
                            {rehire}
                          </span>
                        </td>
                        <td className="p-3 align-top">
                          <div className="flex flex-wrap gap-1">
                            {stillOutstanding > 0 && (
                              <span
                                title={t("Outstanding equipment still on file")}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-900 border border-red-300"
                                data-testid={`flag-outstanding-${r.id}`}
                              >
                                <Wrench className="w-3 h-3" />{stillOutstanding}
                              </span>
                            )}
                            {returnedAtTerm > 0 && stillOutstanding === 0 && (
                              <span
                                title={t("All equipment returned at termination")}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300"
                              >
                                <CheckCircle2 className="w-3 h-3" />{returnedAtTerm}
                              </span>
                            )}
                            {d.law_enforcement_involved === "Yes" && (
                              <span
                                title={t("Law enforcement involved")}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-200 text-red-900 border border-red-400"
                                data-testid={`flag-law-${r.id}`}
                              >
                                <ShieldAlert className="w-3 h-3" />{t("LE")}
                              </span>
                            )}
                            {r.employee_refused && (
                              <span
                                title={t("Refused to sign")}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300"
                              >
                                <AlertOctagon className="w-3 h-3" />{t("RTS")}
                              </span>
                            )}
                            {r.employee_not_present && (
                              <span
                                title={t("Employee not present")}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300"
                              >
                                {t("ABS")}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 align-top text-right whitespace-nowrap">
                          <Button asChild size="sm" variant="outline" className="h-8 text-xs">
                            <Link to={`/admin/leadership/records/${r.id}`} data-testid={`termination-view-${r.id}`}>
                              <FileText className="w-3.5 h-3.5 mr-1" />
                              {t("View")}
                            </Link>
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </PortalShell>
  );
}
