// AdminSessions.jsx — iter189. Read-only operational visibility into
// the live `session_activity` table. No mutation surface, no kill
// switch — just the forensic info an operator needs when investigating
// "is timeout enforcement actually working?" or "why did user X get
// signed out?".
//
// Scope discipline (per operator directive 2026-02-XX):
//   - admin-strict read-only (backend gate is canonical)
//   - audit-logged on every panel view
//   - no filters beyond limit
//   - no kill-session actions
//   - mobile-friendly cards on narrow viewports
import React, { useEffect, useState } from "react";
import {
  Activity, RefreshCcw, Loader2, ShieldCheck, ShieldAlert, Clock,
  WifiOff, Globe,
} from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import { TroubleshootingLink } from "@/components/guidance";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const STATUS_STYLE = {
  active: {
    pill: "bg-emerald-700 text-white",
    label: "Active",
    Icon: ShieldCheck,
  },
  expired_idle: {
    pill: "bg-amber-600 text-white",
    label: "Idle expired",
    Icon: Clock,
  },
  expired_absolute: {
    pill: "bg-red-700 text-white",
    label: "Absolute expired",
    Icon: ShieldAlert,
  },
  enforcement_off: {
    pill: "bg-slate-500 text-white",
    label: "Enforcement off",
    Icon: WifiOff,
  },
};

const TIER_LABEL = {
  ADMIN_HR: "Admin / HR",
  OPERATIONS: "Operations",
  FIELD: "Field",
};

function fmtAgo(seconds) {
  if (seconds == null || isNaN(seconds)) return "—";
  const s = Math.max(0, Math.round(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  if (s < 86400) {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  }
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  return `${d}d ${h}h`;
}

function fmtTs(iso) {
  if (!iso) return "—";
  try {
    return formatPlatformTime(iso);
  } catch {
    return iso;
  }
}

function shortUA(ua) {
  if (!ua) return "—";
  const m = ua.match(/(Chrome|Firefox|Safari|Edge|curl|python-requests|Postman)[\/ ]([0-9.]+)/i);
  if (m) return `${m[1]} ${m[2]}`;
  return ua.slice(0, 40);
}

export default function AdminSessions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setData((await api.get("/admin/sessions/recent?limit=50")).data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load sessions"));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);

  const sessions = data?.sessions || [];
  const enforcementOn = data?.timeouts_enabled;
  const tiers = data?.tiers || {};

  return (
    <LegacyAdminModernShell
      title="Sessions"
      subtitle="Read-only forensic view — last 50 portal sessions."
      breadcrumb={[
        { label: "Identity & Security", to: "/admin/identity-security" },
        { label: "Sessions" },
      ]}
      testidPrefix="admin-sessions"
    >
      <div className="max-w-7xl mx-auto" data-testid="admin-sessions-page">
        {/* Header */}
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex flex-col sm:flex-row sm:items-start gap-3">
          <div
            className={`inline-flex items-center justify-center w-12 h-12 rounded-md text-white shrink-0 ${
              enforcementOn ? "bg-emerald-700" : "bg-slate-500"
            }`}
            data-testid="admin-sessions-enforcement-indicator"
          >
            <Activity className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Operational visibility
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              Last 50 Sessions
            </h1>
            <p className="text-sm text-slate-600 mt-1 leading-relaxed">
              Read-only view of the live <code className="text-[11px]">session_activity</code> table.
              {enforcementOn
                ? " Timeout enforcement is ON in this environment."
                : " Timeout enforcement is OFF — status is shown for visibility only."}
              {" "}This panel logs an audit row every time it loads.
            </p>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
              {Object.entries(tiers).map(([tier, t]) => (
                <span
                  key={tier}
                  className="inline-flex items-center gap-1 border border-slate-300 rounded px-2 py-0.5"
                  data-testid={`admin-sessions-tier-chip-${tier}`}
                >
                  <strong className="font-mono">{TIER_LABEL[tier] || tier}</strong>
                  <span>· idle {t.idle_min}m · abs {t.abs_hour}h</span>
                </span>
              ))}
            </div>
          </div>
          <Button
            onClick={load}
            variant="outline"
            size="sm"
            disabled={loading}
            data-testid="admin-sessions-refresh-btn"
          >
            {loading
              ? <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              : <RefreshCcw className="w-4 h-4 mr-1" />}
            Refresh
          </Button>
        </div>

        {/* Table (desktop) */}
        <div className="hidden md:block bg-white border border-slate-200 rounded-md overflow-hidden">
          <table className="w-full text-sm" data-testid="admin-sessions-table">
            <thead className="bg-slate-100 text-[11px] uppercase tracking-wider text-slate-600">
              <tr>
                <th className="text-left px-3 py-2 font-bold">Identity</th>
                <th className="text-left px-3 py-2 font-bold">Portal / Tier</th>
                <th className="text-left px-3 py-2 font-bold">Login</th>
                <th className="text-left px-3 py-2 font-bold">Last activity</th>
                <th className="text-left px-3 py-2 font-bold">Idle</th>
                <th className="text-left px-3 py-2 font-bold">Status</th>
                <th className="text-left px-3 py-2 font-bold">IP · Agent</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 && !loading && (
                <tr data-testid="admin-sessions-empty">
                  <td colSpan={7} className="text-center py-10 text-slate-500">
                    No active sessions on record yet.
                  </td>
                </tr>
              )}
              {sessions.map((s, idx) => {
                const style = STATUS_STYLE[s.status] || STATUS_STYLE.enforcement_off;
                const Icon = style.Icon;
                return (
                  <tr
                    key={idx}
                    className="border-t border-slate-200 hover:bg-slate-50 transition-colors"
                    data-testid={`admin-sessions-row-${idx}`}
                  >
                    <td className="px-3 py-2 align-top">
                      <div className="font-medium text-slate-900">
                        {s.email || s.actor_label || "—"}
                      </div>
                      {s.email && s.actor_label && (
                        <div className="text-[11px] text-slate-500 font-mono">
                          {s.actor_label}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2 align-top text-slate-700">
                      <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                        {TIER_LABEL[s.tier] || s.tier}
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top text-slate-600 text-[12px]">
                      <div>{fmtTs(s.login_at)}</div>
                      <div className="text-[10px] text-slate-400">
                        duration {fmtAgo(s.session_duration_s)}
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top text-slate-600 text-[12px]">
                      <div>{fmtTs(s.last_activity_at)}</div>
                      <div className="text-[10px] text-slate-400">
                        {fmtAgo(s.idle_seconds)} ago
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top text-slate-700 text-[12px]">
                      <div>
                        {fmtAgo(s.idle_seconds)}
                        {s.idle_limit_seconds && (
                          <span className="text-slate-400">
                            {" / "}{fmtAgo(s.idle_limit_seconds)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold ${style.pill}`}
                        data-testid={`admin-sessions-status-pill-${idx}`}
                      >
                        <Icon className="w-3 h-3" />
                        {style.label}
                      </span>
                    </td>
                    <td className="px-3 py-2 align-top text-[11px] text-slate-600">
                      <div className="font-mono flex items-center gap-1">
                        <Globe className="w-3 h-3 text-slate-400" />
                        {s.ip || "—"}
                      </div>
                      <div
                        className="text-slate-500 truncate max-w-[200px]"
                        title={s.user_agent || ""}
                      >
                        {shortUA(s.user_agent)}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Cards (mobile) */}
        <div className="md:hidden space-y-2" data-testid="admin-sessions-mobile-list">
          {sessions.length === 0 && !loading && (
            <div className="bg-white border border-slate-200 rounded-md p-6 text-center text-slate-500 text-sm">
              No active sessions on record yet.
            </div>
          )}
          {sessions.map((s, idx) => {
            const style = STATUS_STYLE[s.status] || STATUS_STYLE.enforcement_off;
            const Icon = style.Icon;
            return (
              <div
                key={idx}
                className="bg-white border border-slate-200 rounded-md p-3"
                data-testid={`admin-sessions-card-${idx}`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900 truncate">
                      {s.email || s.actor_label || "—"}
                    </div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 font-mono">
                      {TIER_LABEL[s.tier] || s.tier}
                      {s.email && s.actor_label && ` · ${s.actor_label}`}
                    </div>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${style.pill}`}
                  >
                    <Icon className="w-3 h-3" />
                    {style.label}
                  </span>
                </div>
                <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
                  <dt className="text-slate-500">Login</dt>
                  <dd className="text-slate-700 text-right">{fmtTs(s.login_at)}</dd>
                  <dt className="text-slate-500">Last activity</dt>
                  <dd className="text-slate-700 text-right">{fmtTs(s.last_activity_at)}</dd>
                  <dt className="text-slate-500">Idle</dt>
                  <dd className="text-slate-700 text-right">
                    {fmtAgo(s.idle_seconds)}
                    {s.idle_limit_seconds && (
                      <span className="text-slate-400">
                        {" / "}{fmtAgo(s.idle_limit_seconds)}
                      </span>
                    )}
                  </dd>
                  <dt className="text-slate-500">Duration</dt>
                  <dd className="text-slate-700 text-right">
                    {fmtAgo(s.session_duration_s)}
                  </dd>
                  <dt className="text-slate-500">IP</dt>
                  <dd className="text-slate-700 text-right font-mono">{s.ip || "—"}</dd>
                  <dt className="text-slate-500">Agent</dt>
                  <dd
                    className="text-slate-700 text-right truncate"
                    title={s.user_agent || ""}
                  >
                    {shortUA(s.user_agent)}
                  </dd>
                </dl>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <p className="mt-3 text-[11px] text-slate-500">
          Showing {sessions.length} most-recent rows. Rows auto-expire after 30 days of inactivity (Mongo TTL).
          Server time:{" "}
          <span className="font-mono">{fmtTs(data?.server_now)}</span>
        </p>
        <div className="mt-2">
          <TroubleshootingLink articleId="why-session-timeouts" label="Why do sessions expire?" />
        </div>
      </div>
    </LegacyAdminModernShell>
  );
}
