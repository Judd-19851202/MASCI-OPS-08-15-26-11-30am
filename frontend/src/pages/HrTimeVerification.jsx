// HR — Time Verification view.
// Pulls supervisor-reported MASCI crew hours from Daily Reports
// (read-only) and renders both a per-day grid AND a per-employee weekly
// roll-up. HR uses this to cross-check against Exact payroll exports.
//
// Backend: GET /api/hr/time-verification?week_ending=YYYY-MM-DD&employee=&project_number=&supervisor=
// CSV:     GET /api/hr/time-verification.csv (same filters)
//
// Per the spec, ONLY payroll-relevant fields are exposed: employee name,
// date, job, supervisor, regular / overtime / lunch / total hours,
// submitted_at. Notes, photos, materials, etc. are intentionally
// stripped out server-side.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, FileDown, Filter, Clock, AlertCircle } from "lucide-react";
import { api, API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import HrPageShell from "@/components/HrPageShell";
import { Link } from "react-router-dom";
import { WhyItMattersPanel } from "@/components/guidance";
import { HelpTipBlock } from "@/components/HelpTip";
import { getHrToken } from "@/lib/hrAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { WeeklyHoursFlag, DailyHoursFlag } from "@/components/HoursSanityFlag";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

// Compute the Saturday-ending date of the current payroll week.
// MASCI runs Sun→Sat weeks; the backend window math is
// `end - 6 days = start`, so we MUST pass the Saturday-ending date
// for the current pay period (otherwise a mid-week query returns
// 0 records and HR sees a blank Time Verification board).
function defaultWeekEnding() {
  const d = new Date();
  // Day index: Sun=0, Mon=1 ... Sat=6 → add (6 - getDay()) days to reach Saturday.
  const offset = (6 - d.getDay() + 7) % 7;
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

const fmtHours = (n) => (Number.isFinite(n) ? n.toFixed(2) : "0.00");

export default function HrTimeVerification() {
  const { t } = useT();
  const [weekEnding, setWeekEnding] = useState(defaultWeekEnding());
  const [employee, setEmployee] = useState("");
  const [projectNumber, setProjectNumber] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("weekly"); // weekly | daily
  const [pendingFilters, setPendingFilters] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { week_ending: weekEnding };
      if (employee) params.employee = employee;
      if (projectNumber) params.project_number = projectNumber;
      if (supervisor) params.supervisor = supervisor;
      const r = await api.get("/hr/time-verification", { params });
      setData(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load time verification"));
    } finally {
      setLoading(false);
    }
  }, [weekEnding, employee, projectNumber, supervisor, t]);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingFilters]);

  const downloadCsv = async () => {
    const params = new URLSearchParams();
    params.set("week_ending", weekEnding);
    if (employee) params.set("employee", employee);
    if (projectNumber) params.set("project_number", projectNumber);
    if (supervisor) params.set("supervisor", supervisor);
    try {
      const tok = getHrToken();
      const url = `${API}/hr/time-verification.csv?${params.toString()}`;
      const r = await fetch(url, { headers: { "X-HR-Token": tok } });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `MASCI_time_verification_${weekEnding}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast.success(t("CSV downloaded"));
    } catch (err) {
      toast.error(t("CSV download failed"));
    }
  };

  const summary = data?.summary || {};
  const weekly = data?.weekly || [];
  const rows = data?.rows || [];

  const stats = useMemo(() => ([
    { label: t("Total Employees"), value: summary.total_employees || 0 },
    { label: t("Total Hours"), value: fmtHours(summary.total_hours) },
    { label: t("Regular Hours"), value: fmtHours(summary.total_regular) },
    { label: t("Overtime Hours"), value: fmtHours(summary.total_overtime), highlight: (summary.total_overtime || 0) > 0 },
    { label: t("Lunch Hours"), value: fmtHours(summary.total_lunch) },
  ]), [summary, t]);

  return (
    <HrPageShell
      title="Time Verification"
      kicker="HR · Payroll Cross-Check"
    >
      <div className="mb-4">
        <HelpTipBlock formKey="time-verification" showCounter />
      </div>
      {/* Filter bar */}
      <Card className="p-4 mb-5 border-2 border-purple-200 bg-purple-50/30">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6 gap-y-3 items-end">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Week Ending")}</Label>
            <Input type="date" value={weekEnding} onChange={(e) => setWeekEnding(e.target.value)} className={inputCls} data-testid="hr-tv-week" />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Employee")}</Label>
            <Input value={employee} onChange={(e) => setEmployee(e.target.value)} placeholder={t("Name contains...")} className={inputCls} data-testid="hr-tv-employee" />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Project #")}</Label>
            <Input value={projectNumber} onChange={(e) => setProjectNumber(e.target.value)} placeholder="e.g. 25-103" className={inputCls} data-testid="hr-tv-project" />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Supervisor")}</Label>
            <Input value={supervisor} onChange={(e) => setSupervisor(e.target.value)} placeholder={t("Name contains...")} className={inputCls} data-testid="hr-tv-supervisor" />
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setPendingFilters((n) => n + 1)} disabled={loading} className="flex-1 bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-tv-apply">
              {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Filter className="w-4 h-4 mr-1" />}
              {t("Apply")}
            </Button>
            <Button variant="outline" onClick={downloadCsv} disabled={!data || loading} data-testid="hr-tv-csv" title={t("Export CSV")}>
              <FileDown className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <div className="mt-3 text-xs text-slate-600 font-mono">
          {data?.week_start} → {data?.week_end}
        </div>
      </Card>

      {/* Stats strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6 gap-y-3 mb-5" data-testid="hr-tv-stats-strip">
        {stats.map((s) => (
          <Card key={s.label} className={`p-4 ${s.highlight ? "border-2 border-amber-500 bg-amber-50" : "border-2 border-slate-200"}`} data-testid={`hr-tv-stat-${s.label.toLowerCase().replace(/\s+/g, "-")}`}>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{s.label}</div>
            <div className="font-display text-2xl font-black mt-1">{s.value}</div>
          </Card>
        ))}
      </div>

      {/* View toggle */}
      <div className="flex items-center gap-2 mb-4">
        <Button
          size="sm"
          variant={view === "weekly" ? "default" : "outline"}
          onClick={() => setView("weekly")}
          className={view === "weekly" ? "bg-purple-700 hover:bg-purple-800 text-white" : ""}
          data-testid="hr-tv-view-weekly"
        >
          {t("Weekly Rollup")} · {weekly.length}
        </Button>
        <Button
          size="sm"
          variant={view === "daily" ? "default" : "outline"}
          onClick={() => setView("daily")}
          className={view === "daily" ? "bg-purple-700 hover:bg-purple-800 text-white" : ""}
          data-testid="hr-tv-view-daily"
        >
          {t("Per-Day Detail")} · {rows.length}
        </Button>
      </div>

      {/* iter213 · operational coaching surface for the discrepancy
          conversation — sits above the table because that's where HR
          actually catches the numbers that don't match. */}
      <div className="mb-4">
        <HelpTipBlock formKey="time-verification.discrepancy" />
      </div>

      {/* Body */}
      {loading ? (
        <Card className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 mx-auto animate-spin" /></Card>
      ) : view === "weekly" ? (
        <WeeklyTable rows={weekly} />
      ) : (
        <DailyTable rows={rows} />
      )}
    </HrPageShell>
  );
}

function WeeklyTable({ rows }) {
  const { t } = useT();
  if (!rows.length) {
    return (
      <Card className="p-10 text-center text-slate-500" data-testid="hr-tv-weekly-empty">
        <Clock className="w-8 h-8 mx-auto text-slate-400 mb-2" />
        {t("No supervisor-reported hours yet for this window.")}
      </Card>
    );
  }
  return (
    <Card className="overflow-x-auto" data-testid="hr-tv-weekly-table">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
          <tr>
            <th className="text-left px-3 py-2">{t("Employee")}</th>
            <th className="text-left px-3 py-2">{t("Jobs")}</th>
            <th className="text-left px-3 py-2">{t("Supervisor(s)")}</th>
            <th className="text-right px-3 py-2">{t("Reg")}</th>
            <th className="text-right px-3 py-2">{t("OT")}</th>
            <th className="text-right px-3 py-2">{t("Lunch")}</th>
            <th className="text-right px-3 py-2">{t("Total")}</th>
            <th className="text-center px-3 py-2">{t("Flags")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.employee_name} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2 font-semibold">{r.employee_name}</td>
              <td className="px-3 py-2 text-slate-700">{(r.jobs || []).join(", ") || "—"}</td>
              <td className="px-3 py-2 text-slate-700">{(r.supervisors || []).join(", ") || "—"}</td>
              <td className="px-3 py-2 text-right font-mono">{fmtHours(r.regular_hours)}</td>
              <td className={`px-3 py-2 text-right font-mono ${r.overtime_hours > 0 ? "text-amber-700 font-bold" : ""}`}>{fmtHours(r.overtime_hours)}</td>
              <td className="px-3 py-2 text-right font-mono text-slate-500">{fmtHours(r.lunch_hours)}</td>
              <td className="px-3 py-2 text-right font-mono font-bold">{fmtHours(r.total_hours)}</td>
              <td className="px-3 py-2 text-center">
                <div className="inline-flex items-center gap-1.5 flex-wrap justify-center">
                  {r.missing_lunch && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-bold" title={t("6+ hour day with no lunch")}>
                      <AlertCircle className="w-3 h-3" /> {t("No Lunch")}
                    </span>
                  )}
                  {/* iter100 — weekly typo catcher: flag totals > 80 hrs */}
                  <WeeklyHoursFlag
                    totalHours={r.total_hours}
                    testId={`weekly-flag-${r.employee_name.replace(/\s/g, "-").toLowerCase()}`}
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function DailyTable({ rows }) {
  const { t } = useT();
  if (!rows.length) {
    return (
      <Card className="p-10 text-center text-slate-500" data-testid="hr-tv-daily-empty">
        <Clock className="w-8 h-8 mx-auto text-slate-400 mb-2" />
        {t("No daily report rows in this window.")}
      </Card>
    );
  }
  return (
    <Card className="overflow-x-auto" data-testid="hr-tv-daily-table">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
          <tr>
            <th className="text-left px-3 py-2">{t("Date")}</th>
            <th className="text-left px-3 py-2">{t("Employee")}</th>
            <th className="text-left px-3 py-2">{t("Trade")}</th>
            <th className="text-left px-3 py-2">{t("Project")}</th>
            <th className="text-left px-3 py-2">{t("Supervisor")}</th>
            <th className="text-right px-3 py-2">{t("Start")}</th>
            <th className="text-right px-3 py-2">{t("Stop")}</th>
            <th className="text-right px-3 py-2">{t("Reg")}</th>
            <th className="text-right px-3 py-2">{t("OT")}</th>
            <th className="text-right px-3 py-2">{t("Lunch")}</th>
            <th className="text-right px-3 py-2">{t("Total")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${r.daily_report_id}-${r.employee_name}-${i}`} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2 font-mono text-xs">{r.date}</td>
              <td className="px-3 py-2 font-semibold">{r.employee_name}</td>
              <td className="px-3 py-2 text-slate-600">{r.trade || "—"}</td>
              <td className="px-3 py-2 text-slate-700">
                <div className="font-mono text-xs text-slate-500">{r.project_number}</div>
                <div>{r.project_name}</div>
              </td>
              <td className="px-3 py-2 text-slate-700">{r.supervisor || "—"}</td>
              <td className="px-3 py-2 text-right font-mono text-xs">{r.start_time || "—"}</td>
              <td className="px-3 py-2 text-right font-mono text-xs">{r.stop_time || "—"}</td>
              <td className="px-3 py-2 text-right font-mono">{fmtHours(r.regular_hours)}</td>
              <td className={`px-3 py-2 text-right font-mono ${r.overtime_hours > 0 ? "text-amber-700 font-bold" : ""}`}>{fmtHours(r.overtime_hours)}</td>
              <td className="px-3 py-2 text-right font-mono text-slate-500">{fmtHours(r.lunch_hours)}</td>
              <td className="px-3 py-2 text-right font-mono font-bold">
                <div className="inline-flex items-center gap-1.5 justify-end flex-wrap">
                  {fmtHours(r.total_hours)}
                  <DailyHoursFlag hours={r.total_hours} testId={`tv-daily-flag-${i}`} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
