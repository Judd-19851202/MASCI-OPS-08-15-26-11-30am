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
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { WeeklyHoursFlag, DailyHoursFlag } from "@/components/HoursSanityFlag";
import { formatEmployeeIdentity } from "@/lib/identity";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime, formatPlatformStamp, getPlatformTimezone } from "@/lib/platformTime";

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
  // TRACK 27.03 · Phase 3 · Emit the Saturday-ending DATE in the
  // operator's LOCAL calendar week (never UTC). `toISOString()` would
  // shift the boundary on the west coast when local Saturday night is
  // already Sunday UTC. `en-CA` yields YYYY-MM-DD.
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: getPlatformTimezone(),
    year: "numeric", month: "2-digit", day: "2-digit",
  }).format(d);
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
  }, [fetchData, pendingFilters]);

  const downloadCsv = async () => {
    const params = new URLSearchParams();
    params.set("week_ending", weekEnding);
    if (employee) params.set("employee", employee);
    if (projectNumber) params.set("project_number", projectNumber);
    if (supervisor) params.set("supervisor", supervisor);
    try {
      const tok = getHrToken();
      const url = `${API}/hr/time-verification.csv?${params.toString()}`;
      const r = await fetch(url, { headers: buildScopedPortalAuthHeaders(["hr"]) });
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

  const summary = useMemo(() => (data?.summary || {}), [data?.summary]);
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
      {/* HR-TIME-001E · FINAL executive-quality print lock.
          Restructured for stronger title hierarchy, prominent totals, balanced
          page utilization (~70-80% of letter page), readable footer. */}
      <style>{`
        @media print {
          @page { size: letter portrait; margin: 0.45in; }
          html, body {
            background: #fff !important; color: #0f172a !important;
            margin: 0 !important; padding: 0 !important;
            font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial !important;
          }
          * { -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important; }

          /* Hide chrome */
          .caution-stripe, header, nav, aside,
          [role="navigation"], [role="banner"],
          [data-testid="env-banner"],
          [data-testid="forgedops-attr-global"],
          main > a[href="/hr"],
          main > div.font-mono.text-purple-700,
          main > h1.font-display,
          [data-print-hide] { display: none !important; }
          .blueprint-bg { background: #fff !important; background-image: none !important; }

          /* Neutralise shell layout */
          .min-h-screen { min-height: 0 !important; }
          .pb-16 { padding-bottom: 0 !important; }
          main, .max-w-7xl, .max-w-6xl, .max-w-5xl {
            max-width: none !important; padding: 0 !important; margin: 0 !important;
          }
          main { display: block !important; }
          [data-print-only] { display: block !important; }

          /* ── A · Report header — TITLE is dominant ─────────────── */
          .pr-head { margin-bottom: 26px; padding-bottom: 14px;
                     border-bottom: 3px solid #6d28d9; }
          .pr-head .top-row {
            display: flex; align-items: flex-start; justify-content: space-between;
            gap: 16px;
          }
          .pr-head .title {
            font-size: 30px; font-weight: 900; color: #0f172a;
            letter-spacing: -0.02em; line-height: 1.05;
            text-transform: uppercase;
          }
          .pr-head .subtitle {
            font-size: 12px; font-weight: 600; color: #334155;
            margin-top: 8px; letter-spacing: 0.01em;
          }
          .pr-head .subtitle .sep { color: #94a3b8; margin: 0 6px; }
          .pr-head .gen-block {
            text-align: right; flex-shrink: 0;
          }
          .pr-head .gen-lbl {
            font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
            font-size: 8px; letter-spacing: 0.2em;
            text-transform: uppercase; color: #64748b;
          }
          .pr-head .gen-val {
            font-family: ui-monospace, monospace; font-size: 11px;
            font-weight: 700; color: #0f172a; margin-top: 2px;
          }
          .pr-head .env-label {
            display: inline-block; margin-top: 6px;
            font-family: ui-monospace, monospace; font-size: 8.5px;
            font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase;
            color: #b45309; padding: 2px 6px;
            border: 1px solid #f59e0b; border-radius: 3px;
            background: #fffbeb !important;
          }

          /* ── B · Compact metadata pills ────────────────────────── */
          .pr-meta { margin-bottom: 22px;
                     display: flex; flex-wrap: wrap; gap: 8px 10px;
                     padding: 0; }
          .pr-meta .pill {
            display: inline-flex; align-items: baseline; gap: 6px;
            padding: 5px 11px; border: 1px solid #cbd5e1; border-radius: 999px;
            background: #f8fafc !important;
          }
          .pr-meta .pill .lbl {
            font-family: ui-monospace, monospace; font-size: 8px;
            letter-spacing: 0.16em; text-transform: uppercase; color: #64748b;
          }
          .pr-meta .pill .val {
            font-size: 11px; font-weight: 700; color: #0f172a;
          }

          /* ── C · Prominent totals cards ────────────────────────── */
          [data-print-region] .pr-stats {
            display: grid !important;
            grid-template-columns: repeat(5, 1fr) !important;
            gap: 10px !important;
            margin-bottom: 26px !important;
          }
          [data-print-region] .pr-stats .cell {
            border: 1px solid #cbd5e1; border-radius: 6px;
            padding: 14px 12px; background: #fff !important;
            text-align: center;
          }
          [data-print-region] .pr-stats .lbl {
            font-family: ui-monospace, monospace; font-size: 8.5px;
            letter-spacing: 0.2em; text-transform: uppercase; color: #64748b;
          }
          [data-print-region] .pr-stats .val {
            font-size: 28px; font-weight: 900; color: #0f172a;
            margin-top: 6px; line-height: 1; letter-spacing: -0.02em;
          }
          [data-print-region] .pr-stats .cell.ot .val { color: #b45309; }
          [data-print-region] .pr-stats .cell.ot {
            border-color: #f59e0b; background: #fffbeb !important;
          }

          /* ── D · Employee table ─────────────────────────────────── */
          [data-print-region] table {
            font-size: 11.5px !important; width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
          }
          [data-print-region] th, [data-print-region] td {
            padding: 10px 9px !important;
            border-bottom: 1px solid #e2e8f0 !important;
            vertical-align: middle;
          }
          [data-print-region] thead th {
            background: #0f172a !important; color: #fff !important;
            border-bottom: none !important;
            font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em;
            font-weight: 700; padding: 9px 9px !important;
          }
          [data-print-region] tbody tr { page-break-inside: avoid; }
          [data-print-region] tbody tr:nth-child(even) td {
            background: #f8fafc !important;
          }
          [data-print-region] tbody tr td { line-height: 1.4; }
          [data-print-region] tbody tr td:first-child {
            font-weight: 700; color: #0f172a;
          }
          [data-print-region] thead { display: table-header-group; }
          /* Right-align numeric columns (Reg/OT/Lunch/Total) */
          [data-print-region] th:nth-child(4),
          [data-print-region] th:nth-child(5),
          [data-print-region] th:nth-child(6),
          [data-print-region] th:nth-child(7),
          [data-print-region] td:nth-child(4),
          [data-print-region] td:nth-child(5),
          [data-print-region] td:nth-child(6),
          [data-print-region] td:nth-child(7) {
            text-align: right;
            font-variant-numeric: tabular-nums;
          }
          [data-print-region] td:nth-child(7) { font-weight: 700; }
          /* Flag pills */
          [data-print-region] .inline-flex { font-size: 9.5px !important;
                                              padding: 3px 8px !important;
                                              border-radius: 999px; }

          /* Hide the live React stats strip + filter card */
          [data-print-region] [data-testid="hr-tv-stats-strip"] { display: none !important; }
          [data-print-region] [data-testid="hr-tv-filter-card"] { display: none !important; }

          /* ── E · Readable executive footer ──────────────────────── */
          .pr-footer {
            margin-top: 34px; padding-top: 14px;
            border-top: 2px solid #0f172a;
            text-align: center; line-height: 1.5;
            page-break-inside: avoid;
          }
          .pr-footer .brand {
            font-size: 13px; font-weight: 800; color: #0f172a;
            letter-spacing: 0.04em;
          }
          .pr-footer .powered {
            font-family: ui-monospace, monospace; font-size: 10.5px;
            font-weight: 700; color: #6d28d9;
            letter-spacing: 0.22em; text-transform: uppercase;
            margin-top: 4px;
          }
          .pr-footer .sub {
            font-size: 9.5px; color: #475569; margin-top: 10px;
            letter-spacing: 0.02em;
          }
        }
        @media not print {
          [data-print-only] { display: none; }
        }
      `}</style>

      <div data-print-region>
        {/* A · Print-only · executive report header */}
        <div data-print-only className="pr-head">
          <div className="top-row">
            <div>
              <div className="title">Time Verification Report</div>
              <div className="subtitle">
                MASCI Operations Platform <span className="sep">·</span> HR Payroll Cross-Check
              </div>
            </div>
            <div className="gen-block">
              <div className="gen-lbl">Generated</div>
              <div className="gen-val">{formatPlatformStamp(new Date())}</div>
              {typeof window !== "undefined" && window.location?.host?.includes("preview") ? (
                <div className="env-label">Staged Site · Not Operational Data</div>
              ) : null}
            </div>
          </div>
        </div>

        {/* B · Print-only · compact metadata pills */}
        <div data-print-only className="pr-meta">
          <div className="pill"><span className="lbl">Window</span><span className="val">{(data?.week_start || "—") + " → " + (data?.week_end || "—")}</span></div>
          <div className="pill"><span className="lbl">Week Ending</span><span className="val">{weekEnding || "—"}</span></div>
          <div className="pill"><span className="lbl">View</span><span className="val">{view === "weekly" ? "Weekly Rollup" : "Per-Day Detail"}</span></div>
          <div className="pill"><span className="lbl">Employee</span><span className="val">{employee || "All"}</span></div>
          <div className="pill"><span className="lbl">Project #</span><span className="val">{projectNumber || "All"}</span></div>
          <div className="pill"><span className="lbl">Supervisor</span><span className="val">{supervisor || "All"}</span></div>
        </div>

        {/* C · Print-only · prominent totals cards */}
        <div data-print-only className="pr-stats">
          <div className="cell"><div className="lbl">Total Employees</div><div className="val">{summary.total_employees || 0}</div></div>
          <div className="cell"><div className="lbl">Total Hours</div><div className="val">{fmtHours(summary.total_hours)}</div></div>
          <div className="cell"><div className="lbl">Regular Hours</div><div className="val">{fmtHours(summary.total_regular)}</div></div>
          <div className={`cell ${(summary.total_overtime || 0) > 0 ? "ot" : ""}`}><div className="lbl">Overtime Hours</div><div className="val">{fmtHours(summary.total_overtime)}</div></div>
          <div className="cell"><div className="lbl">Lunch Hours</div><div className="val">{fmtHours(summary.total_lunch)}</div></div>
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

        {/* E · Print-only · executive footer */}
        <div data-print-only className="pr-footer">
          <div className="brand">MASCI Operations Platform</div>
          <div className="powered">MASCI Operations Platform</div>
          <div className="sub">
            Generated {formatPlatformStamp(new Date())} · Confidential payroll cross-check
            {typeof window !== "undefined" && window.location?.host?.includes("preview") ? (
              <> · Staged Environment · Not Operational Data</>
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
            <tr key={formatEmployeeIdentity(r) || r.employee_name} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2 font-semibold">{formatEmployeeIdentity(r) || r.employee_name}</td>
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
            <tr key={`${r.daily_report_id}-${formatEmployeeIdentity(r) || r.employee_name}-${i}`} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2 font-mono text-xs">{r.date}</td>
              <td className="px-3 py-2 font-semibold">{formatEmployeeIdentity(r) || r.employee_name}</td>
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
