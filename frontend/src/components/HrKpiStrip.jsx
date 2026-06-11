// HrKpiStrip.jsx — HR-native KPI strip (Track 13 · §4 HR KPI Correction).
//
// Replaces the operations-center paste (`<OperationsCenter compact />`)
// previously rendered on the HR hub. The old strip surfaced Incidents
// Open · Overdue PO Receipts · CAPAs Overdue · Docs Expired — all real
// numbers but conceptually misshelved (the first three belong on
// Safety/Admin, not HR).
//
// This component surfaces only HR-native signals, all sourced from
// existing endpoints — no new backend route:
//   • Active employees    /api/employees
//   • Pending employee req /api/employee-requests
//   • Time-off pending    /api/time-off-requests
//   • Training/cert exp   /api/operations/expirations/summary
//   • Docs expired soon   /api/operations/expirations/summary
//
// Inherits the platform Tile shape — no new visual language.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Users, ClipboardList, GraduationCap, FileWarning, CalendarOff } from "lucide-react";
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function _authHeaders() {
  const t =
    sessionStorage.getItem("masci.hr.token") ||
    sessionStorage.getItem("masci.admin.token") ||
    "";
  return t ? { "X-Admin-Token": t } : {};
}

function Tile({ to, icon: Icon, label, value, tone = "slate", testId, hint }) {
  const toneCls = {
    rose:    "border-rose-300 bg-rose-50 text-rose-800",
    amber:   "border-amber-300 bg-amber-50 text-amber-800",
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-800",
    slate:   "border-slate-200 bg-white text-slate-800",
  }[tone] || "border-slate-200 bg-white text-slate-800";
  const showAttn = tone === "rose" || tone === "amber";
  return (
    <Link
      to={to}
      data-testid={testId}
      className={`group border-2 rounded-md p-4 sm:p-5 transition-colors hover:border-slate-400 ${toneCls}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold opacity-80">
          {label}
        </div>
        <Icon className="w-4 h-4 opacity-70" />
      </div>
      <div className="text-3xl font-display font-black tabular-nums">{value}</div>
      {hint ? (
        <div className="mt-2 text-[11px] leading-snug opacity-80">{hint}</div>
      ) : showAttn ? (
        <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-white/70 border border-current text-[10px] font-mono uppercase tracking-wider px-2 py-0.5">
          Needs attention
        </div>
      ) : null}
    </Link>
  );
}

export default function HrKpiStrip({ className = "" }) {
  const { t } = useT();
  const [counts, setCounts] = useState({
    active_employees: null,
    pending_requests: null,
    time_off_pending: null,
    training_exp_soon: null,
    docs_expired: null,
  });

  useEffect(() => {
    let cancelled = false;
    const headers = _authHeaders();

    async function loadEmployees() {
      try {
        const r = await fetch(`${API}/employees?limit=5000`, { headers });
        if (!r.ok) return null;
        const data = await r.json();
        const items = Array.isArray(data) ? data : (data?.items || data?.employees || []);
        const active = items.filter((e) => {
          const s = (e.employment_status || e.status || "").toLowerCase();
          return !s || s === "active";
        });
        return active.length;
      } catch { return null; }
    }
    async function loadEmployeeRequests() {
      try {
        const r = await fetch(`${API}/employee-requests?status=pending`, { headers });
        if (!r.ok) return null;
        const data = await r.json();
        const items = Array.isArray(data) ? data : (data?.items || []);
        return items.length;
      } catch { return null; }
    }
    async function loadTimeOff() {
      try {
        const r = await fetch(`${API}/time-off-requests?status=pending`, { headers });
        if (!r.ok) return null;
        const data = await r.json();
        const items = Array.isArray(data) ? data : (data?.items || []);
        return items.length;
      } catch { return null; }
    }
    async function loadExpirations() {
      try {
        const r = await fetch(`${API}/operations/expirations/summary`, { headers });
        if (!r.ok) return null;
        const data = await r.json();
        return {
          training_exp_soon: (data?.expiring_in_30 ?? 0) + (data?.expiring_in_60 ?? 0),
          docs_expired: data?.expired ?? 0,
        };
      } catch { return null; }
    }

    Promise.all([loadEmployees(), loadEmployeeRequests(), loadTimeOff(), loadExpirations()])
      .then(([active_employees, pending_requests, time_off_pending, exp]) => {
        if (cancelled) return;
        setCounts({
          active_employees,
          pending_requests,
          time_off_pending,
          training_exp_soon: exp?.training_exp_soon ?? null,
          docs_expired: exp?.docs_expired ?? null,
        });
      });
    return () => { cancelled = true; };
  }, []);

  const fmt = (v) => (v === null ? "—" : v);

  return (
    <section
      className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 ${className}`}
      data-testid="hr-kpi-strip"
    >
      <Tile
        to="/hr/employees"
        icon={Users}
        label={t("Active Employees")}
        value={fmt(counts.active_employees)}
        tone="slate"
        testId="hr-kpi-active-employees"
        hint={t("On the active roster.")}
      />
      <Tile
        to="/hr/employee-requests"
        icon={ClipboardList}
        label={t("Pending Requests")}
        value={fmt(counts.pending_requests)}
        tone={(counts.pending_requests ?? 0) > 0 ? "amber" : "slate"}
        testId="hr-kpi-pending-requests"
        hint={t("New-hire and termination submissions to approve.")}
      />
      <Tile
        to="/hr/time-off"
        icon={CalendarOff}
        label={t("Time Off Pending")}
        value={fmt(counts.time_off_pending)}
        tone={(counts.time_off_pending ?? 0) > 0 ? "amber" : "slate"}
        testId="hr-kpi-time-off-pending"
        hint={t("Vacation / sick approvals awaiting HR.")}
      />
      <Tile
        to="/safety-portal/document-expirations"
        icon={GraduationCap}
        label={t("Training / Cert Due")}
        value={fmt(counts.training_exp_soon)}
        tone={(counts.training_exp_soon ?? 0) > 0 ? "amber" : "slate"}
        testId="hr-kpi-training-due"
        hint={t("Credentials expiring in the next 60 days.")}
      />
      <Tile
        to="/safety-portal/document-expirations?bucket=expired"
        icon={FileWarning}
        label={t("Documents Expired")}
        value={fmt(counts.docs_expired)}
        tone={(counts.docs_expired ?? 0) > 0 ? "rose" : "slate"}
        testId="hr-kpi-docs-expired"
        hint={t("Past their expiration date — review now.")}
      />
    </section>
  );
}
