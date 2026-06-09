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
import { Loader2, FileDown, Filter, Clock, AlertCircle, Printer } from "lucide-react";
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

  // iter445 · F-001 fix — accept deep-link from Payroll Variance page.
  // ?employee=Name&week_ending=YYYY-MM-DD&open_detail=daily
  const _qs = (typeof window !== "undefined") ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const _qsEmployee = _qs.get("employee") || "";
  const _qsWeekEnding = _qs.get("week_ending") || "";
  const _qsOpenDetail = _qs.get("open_detail") || "";

  const [weekEnding, setWeekEnding] = useState(_qsWeekEnding || defaultWeekEnding());
  const [employee, setEmployee] = useState(_qsEmployee);
  const [projectNumber, setProjectNumber] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState(_qsOpenDetail === "daily" ? "daily" : "weekly"); // weekly | daily
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
      {/* HR-TIME-001 / 001B · Print stylesheet — portrait, upright, no blank
          trailing page. Targeted-hide approach (NOT body>*:not(...)) so it
          works inside the deeply-nested HrPageShell DOM. */}
      <style>{`
        @media print {
          @page { size: letter portrait; margin: 0.4in 0.45in; }
          html, body {
            background: #fff !important;
            margin: 0 !important; padding: 0 !important;
          }
          /* Force backgrounds + colors to render */
          * { -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important; }

          /* Hide known chrome — must enumerate; "hide-all-then-restore"
             collapses table/grid semantics in webkit. HR-TIME-001C adds:
               · EnvBanner preview warning
               · HrPageShell HR-Hub back link + kicker + live h1 title */
          .caution-stripe, header, nav, aside,
          [role="navigation"], [role="banner"],
          [data-testid="env-banner"],
          [data-testid="forgedops-attr-global"],
          main > a[href="/hr"],
          main > div.font-mono.text-purple-700,
          main > h1.font-display,
          [data-print-hide] { display: none !important; }

          /* Strip the blueprint-grid background — print mode prints flat white. */
          .blueprint-bg { background: #fff !important; background-image: none !important; }

          /* Neutralise layout constraints inherited from the page shell so the
             printed region is the natural height of its content (no phantom page). */
          .min-h-screen { min-height: 0 !important; }
          .pb-16 { padding-bottom: 0 !important; }
          main, .max-w-7xl, .max-w-6xl, .max-w-5xl {
            max-width: none !important;
            padding: 0 !important; margin: 0 !important;
          }
          main { display: block !important; }

          /* Reveal print-only header & footer */
          [data-print-only] { display: block !important; }

          /* Compact tables for portrait letter */
          [data-print-region] { width: 100%; }
          [data-print-region] table {
            font-size: 10px; width: 100%;
            border-collapse: collapse;
          }
          [data-print-region] th, [data-print-region] td {
            padding: 3px 5px !important;
            border-bottom: 1px solid #e2e8f0 !important;
            vertical-align: top;
          }
          [data-print-region] thead th {
            background: #f1f5f9 !important; color: #0f172a !important;
            border-bottom: 1px solid #94a3b8 !important;
            font-size: 9px; text-transform: uppercase; letter-spacing: 0.04em;
          }
          [data-print-region] tr { page-break-inside: avoid; }
          [data-print-region] thead { display: table-header-group; }
          [data-print-region] .text-3xl { font-size: 13px !important; }
          [data-print-region] .border-2 { border-width: 1px !important; }
          [data-print-region] .grid { gap: 6px !important; }
          [data-print-region] .p-5 { padding: 6px 0 !important; }
          [data-print-region] .mb-5, [data-print-region] .mb-4 { margin-bottom: 8px !important; }

          /* Print footer · flows in document (NOT fixed) so it never spawns
             a phantom trailing page. */
          .print-footer {
            margin-top: 14px; padding-top: 6px;
            border-top: 1px solid #cbd5e1;
            font-size: 9px; color: #475569;
            text-align: center; line-height: 1.45;
            page-break-inside: avoid;
          }
          .print-footer .brand { font-weight: 700; color: #0f172a; }
          .print-footer .sub   { color: #64748b; font-size: 8.5px; }
        }
        @media not print {
          [data-print-only] { display: none; }
        }
      `}</style>

      <div data-print-region>
        {/* Print-only report header (hidden on screen) */}
        <div data-print-only style={{ marginBottom: 10, borderBottom: "1.5px solid #6d28d9", paddingBottom: 6 }}>
          <div style={{ fontFamily: "monospace", fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", color: "#64748b" }}>
            MASCI Operations Platform · HR · Payroll Cross-Check
          </div>
          <div style={{ fontSize: 16, fontWeight: 900, color: "#0f172a", marginTop: 2 }}>
            Time Verification Report
          </div>
          <div style={{ fontSize: 10, color: "#334155", marginTop: 4, lineHeight: 1.5 }}>
            <strong>Window:</strong> {data?.week_start || "—"} → {data?.week_end || "—"}
            {" · "}
            <strong>Week Ending:</strong> {weekEnding || "—"}
            {employee ? <> · <strong>Employee:</strong> {employee}</> : null}
            {projectNumber ? <> · <strong>Project #:</strong> {projectNumber}</> : null}
            {supervisor ? <> · <strong>Supervisor:</strong> {supervisor}</> : null}
            {" · "}
            <strong>View:</strong> {view === "weekly" ? "Weekly Rollup" : "Per-Day Detail"}
            {" · "}
            <strong>Generated:</strong> {new Date().toISOString().replace("T", " ").slice(0, 16)} UTC
          </div>
        </div>

      <div className="mb-4" data-print-hide>
        <HelpTipBlock formKey="time-verification" showCounter />
      </div>
      {/* Filter bar — Pass-6 UX quality: clear input grid + dedicated action footer with window context */}
      <Card className="p-5 mb-5 border-2 border-purple-200 bg-purple-50/30" data-testid="hr-tv-filter-card" data-print-hide>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Week Ending")}</Label>
            <Input type="date" value={weekEnding} onChange={(e) => setWeekEnding(e.target.value)} className={`${inputCls} w-full`} data-testid="hr-tv-week" />
          </div>
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Employee")}</Label>
            <Input value={employee} onChange={(e) => setEmployee(e.target.value)} placeholder={t("Name contains...")} className={`${inputCls} w-full`} data-testid="hr-tv-employee" />
          </div>
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Project #")}</Label>
            <Input value={projectNumber} onChange={(e) => setProjectNumber(e.target.value)} placeholder="e.g. 25-103" className={`${inputCls} w-full`} data-testid="hr-tv-project" />
          </div>
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Supervisor")}</Label>
            <Input value={supervisor} onChange={(e) => setSupervisor(e.target.value)} placeholder={t("Name contains...")} className={`${inputCls} w-full`} data-testid="hr-tv-supervisor" />
          </div>
        </div>
        <div className="mt-5 pt-4 border-t border-purple-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-500" data-testid="hr-tv-window-chip">
            {data?.week_start ? <>{t("Window")} · <span className="text-slate-700 font-bold">{data.week_start} → {data.week_end}</span></> : t("Set a week to begin")}
          </div>
          <div className="flex gap-2 sm:ml-auto print:hidden">
            <Button variant="outline" onClick={downloadCsv} disabled={!data || loading} data-testid="hr-tv-csv" title={t("Export CSV")} className="h-10">
              <FileDown className="w-4 h-4 mr-1" />{t("Export CSV")}
            </Button>
            {/* HR-TIME-001 · Print Report button */}
            <Button variant="outline" onClick={() => window.print()} disabled={!data || loading} data-testid="hr-tv-print" title={t("Print Report")} className="h-10">
              <Printer className="w-4 h-4 mr-1" />{t("Print Report")}
            </Button>
            <Button onClick={() => setPendingFilters((n) => n + 1)} disabled={loading} className="h-10 px-6 bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-tv-apply">
              {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Filter className="w-4 h-4 mr-1" />}
              {t("Apply Filters")}
            </Button>
          </div>
        </div>
      </Card>

      {/* Stats strip — Pass-6 UX: single card with 5 inline metrics + divider columns */}
      <Card className="p-5 mb-5 border-2 border-slate-200" data-testid="hr-tv-stats-strip">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-6 gap-y-5 sm:divide-x sm:divide-slate-200">
          {stats.map((s, i) => (
            <div
              key={s.label}
              className={`flex flex-col ${i > 0 ? 'sm:pl-6' : ''} ${s.highlight ? 'sm:relative' : ''}`}
              data-testid={`hr-tv-stat-${s.label.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{s.label}</div>
              <div className={`font-display text-3xl font-black mt-1.5 leading-none ${s.highlight ? 'text-amber-700' : 'text-slate-900'}`}>{s.value}</div>
              {s.highlight ? <div className="mt-1 text-[10px] font-mono uppercase tracking-wider text-amber-700">{t("Variance flagged")}</div> : null}
            </div>
          ))}
        </div>
      </Card>

      {/* View toggle */}
      <div className="flex items-center gap-2 mb-4" data-print-hide>
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
      <div className="mb-4" data-print-hide>
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

        {/* Print footer (hidden on screen) · ForgedOps platform credit. Flows in
            document, never fixed-position, so it does not generate a phantom page. */}
        <div data-print-only className="print-footer">
          <div className="brand">MASCI Operations Platform</div>
          <div>Powered by ForgedOps</div>
          <div className="sub">
            Generated {new Date().toISOString().replace("T", " ").slice(0, 19)} UTC · Confidential payroll cross-check
            {typeof window !== "undefined" && window.location?.host?.includes("preview") ? (
              <> · Preview Environment · Not Operational Data</>
            ) : null}
          </div>
        </div>
      </div>
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
