// NotificationsDigest.jsx — Phase 2 P1 · Operational Intelligence Notifications.
//
// Single role-aware in-platform digest surface. Auto-detects which portal
// the user is currently authenticated as and renders that role's digest.
// Today: Admin + Safety. Tomorrow: HR / PM / Dispatch / FL (same render
// pipeline — server returns the same payload shape).
//
// Permanent operational-coaching standard: this page leads with a
// LifecycleGuide that explains what notifications are, why they exist,
// where the data comes from, and how to act on them.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell, BellRing, RefreshCw, ArrowRight, ShieldAlert, AlertOctagon,
  AlertTriangle, Activity, CheckCircle2, Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import { formatLocalDateTime, formatLocalShort } from "@/lib/dateUtils";
import { usePageTitle } from "@/lib/usePageTitle";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { getAdminToken } from "@/lib/adminAuth";
import { getSafetyToken } from "@/lib/safetyAuth";

const TOKEN_KEYS = [
  // Order = preference. Operational tokens come first (their digests are
  // tighter / more actionable); admin is the fallback so super-admins
  // still get a digest on any portal context.
  { role: "safety",   key: "masci.safety.token",   endpoint: "/safety/notifications/digest" },
  { role: "hr",       key: "masci.hr.token",       endpoint: "/hr/notifications/digest" },
  { role: "pm",       key: "masci.pm.token",       endpoint: "/pm/notifications/digest" },
  { role: "dispatch", key: "masci.dispatch.token", endpoint: "/dispatch/notifications/digest" },
  { role: "fl",       key: "masci.fl.token",       endpoint: "/fl/notifications/digest" },
];

function pickRoleAndEndpoint() {
  for (const { role, key, endpoint } of TOKEN_KEYS) {
    try {
      if (localStorage.getItem(key)) return { role, endpoint };
    } catch { /* ignore */ }
  }
  // Safety: also accept the cached helper (some portals store under
  // a different key than the constants above).
  if (getSafetyToken()) return { role: "safety", endpoint: "/safety/notifications/digest" };
  if (getAdminToken())  return { role: "admin",  endpoint: "/admin/notifications/digest" };
  return null;
}

const SEVERITY_TINTS = {
  critical: "border-rose-500 bg-rose-50 text-rose-900",
  high:     "border-amber-500 bg-amber-50 text-amber-900",
  medium:   "border-yellow-400 bg-yellow-50 text-yellow-900",
  low:      "border-sky-400 bg-sky-50 text-sky-900",
  info:     "border-slate-300 bg-slate-50 text-slate-700",
};

const SEVERITY_ICON = {
  critical: AlertOctagon,
  high:     AlertTriangle,
  medium:   Activity,
  low:      ShieldAlert,
  info:     CheckCircle2,
};

function SeverityBadge({ severity }) {
  const Icon = SEVERITY_ICON[severity] || CheckCircle2;
  const tint = SEVERITY_TINTS[severity] || SEVERITY_TINTS.info;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${tint}`}>
      <Icon className="w-3 h-3" />{severity}
    </span>
  );
}

function SectionCard({ section }) {
  const tint = SEVERITY_TINTS[section.severity] || SEVERITY_TINTS.info;
  return (
    <article
      className={`bg-white border-2 ${tint} rounded-md overflow-hidden`}
      data-testid={`notif-section-${section.key}`}
    >
      <header className="px-3 py-2 sm:px-4 sm:py-3 flex flex-wrap items-start gap-2 border-b border-slate-200 bg-white/60">
        <SeverityBadge severity={section.severity} />
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-base font-black tracking-tight text-slate-900 leading-tight">
            {section.title}
          </h3>
          {section.body ? (
            <p className="text-xs text-slate-700 mt-1 leading-snug">{section.body}</p>
          ) : null}
        </div>
        {section.action_url ? (
          <Link to={section.action_url} className="shrink-0" data-testid={`notif-section-action-${section.key}`}>
            <Button variant="outline" size="sm">
              View <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </Link>
        ) : null}
      </header>
      {(section.items && section.items.length > 0) ? (
        <ul className="divide-y divide-slate-100 bg-white">
          {section.items.map((it) => (
            <li
              key={it.id || it.rule_id + (it.entity_name || "")}
              className="px-3 py-2 sm:px-4 sm:py-2.5 flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-3"
              data-testid={`notif-item-${it.id || it.rule_id}`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-slate-900 text-sm truncate max-w-full">
                    {it.entity_name || "(unnamed)"}
                  </span>
                  <span className="font-mono text-[10px] text-slate-500">{it.rule_id}</span>
                </div>
                <div className="text-xs text-slate-600 mt-0.5 line-clamp-2 leading-snug">
                  {it.description}
                </div>
              </div>
              {it.last_detected_at ? (
                <div className="text-[10px] font-mono text-slate-400 shrink-0 inline-flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {formatLocalShort(it.last_detected_at)}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

export default function NotificationsDigest() {
  usePageTitle("Today's intelligence · MASCI");
  const { t } = useT();
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const target = useMemo(pickRoleAndEndpoint, []);

  const load = useCallback(async () => {
    if (!target) { setLoading(false); return; }
    setLoading(true); setErr("");
    try {
      const { data } = await api.get(target.endpoint);
      setDigest(data);
    } catch (e) {
      setErr(operationalError(e, "Could not load digest."));
    } finally {
      setLoading(false);
    }
  }, [target]);

  useEffect(() => { load(); }, [load]);

  if (!target) {
    return (
      <div className="min-h-screen bg-slate-50 px-4 sm:px-6 py-8 max-w-3xl mx-auto" data-testid="notifications-digest">
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center">
          <Bell className="w-12 h-12 mx-auto text-slate-300" />
          <h2 className="font-display text-xl font-black text-slate-900 mt-3">
            {t("Sign in to see today's intelligence")}
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            {t("Each portal has a role-scoped digest. Sign into Safety or Admin to view yours.")}
          </p>
        </div>
      </div>
    );
  }

  const summary = digest?.summary || {};
  const sections = digest?.sections || [];

  return (
    <div className="min-h-screen bg-slate-50" data-testid="notifications-digest">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-5">
        {/* Header */}
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold flex items-center gap-1">
              <BellRing className="w-3 h-3" /> {t("Today's intelligence")} · {target.role}
            </div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
              {t("Operational digest")}
            </h1>
            {digest?.generated_at ? (
              <div className="text-xs font-mono text-slate-500 mt-1">
                {t("Generated")} {formatLocalDateTime(digest.generated_at)}
              </div>
            ) : null}
          </div>
          <Button onClick={load} disabled={loading} size="sm" data-testid="notif-refresh">
            <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            {t("Refresh")}
          </Button>
        </header>

        {/* Operational coaching banner (permanent standard) */}
        <LifecycleGuide
          id="notifications-digest"
          icon={BellRing}
          accent="amber"
          title={t("How notifications work")}
          summary={t("Role-scoped · severity-aware · sourced from the live detection engine · in-platform first, email follows.")}
          sections={[
            {
              label: t("What this is"),
              body: t("Your daily operational priorities. Generated from the live compliance findings + lifecycle state — no hand-curated lists, no spam. Each item points at a workflow you can resolve right now."),
            },
            {
              label: t("How items are chosen"),
              body: t("Every section maps to a detector rule from Governance Health. If a rule has zero open findings for you, it doesn't appear here. Items disappear automatically once the underlying condition is fixed or acknowledged."),
            },
            {
              label: t("What to do"),
              body: t("Open the View link on any section to act inside the relevant portal. Acknowledge or resolve from Compliance Findings; advance CAPAs from Safety Corrective Actions. Every action is audit-trailed."),
            },
            {
              label: t("Why this matters"),
              body: t("Operational risk surfaces here before it becomes a meeting, a citation, or an injury. Treating this digest as the start of every day is the cheapest insurance the platform offers."),
            },
          ]}
        />

        {/* Summary tile strip */}
        {target.role === "admin" && summary.score != null ? (
          <div className={`border-2 rounded-md p-4 sm:p-5 ${SEVERITY_TINTS[summary.score_label === "critical" ? "critical" : summary.score_label === "degraded" ? "high" : summary.score_label === "fair" ? "medium" : "info"]}`} data-testid="notif-admin-summary">
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold">{t("Convergence score")}</span>
              <span className="font-display text-4xl font-black leading-none">{summary.score}<span className="text-base opacity-70">/100</span></span>
              <span className="font-display text-lg font-black uppercase">{summary.score_label}</span>
              <span className="font-mono text-xs ml-auto">
                {summary.critical || 0} crit · {summary.high || 0} high · {summary.medium || 0} med · {summary.low || 0} low
              </span>
            </div>
          </div>
        ) : null}

        {target.role === "safety" ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4" data-testid="notif-safety-summary">
            {[
              ["overdue_capas",             t("Overdue CAPAs"),       "high"],
              ["incidents_needing_capa",    t("Need a CAPA"),         "critical"],
              ["capas_awaiting_verification", t("Pending verification"), "medium"],
              ["capas_without_owner",       t("No owner"),            "medium"],
              ["incidents_closed_capa_open", t("Closed w/ open CAPA"), "high"],
              ["trainings_expired",         t("Expired training"),    "high"],
            ].map(([key, label, sev]) => (
              <div key={key} className={`border-2 rounded-md p-3 ${SEVERITY_TINTS[sev]}`}>
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold opacity-80">{label}</div>
                <div className="font-display text-2xl font-black leading-none mt-1">{summary[key] ?? 0}</div>
              </div>
            ))}
          </div>
        ) : null}

        {target.role === "hr" ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4" data-testid="notif-hr-summary">
            {[
              ["linkage_failures",                t("Linkage failures"),    "high"],
              ["driver_qualification_expired",    t("Driver creds expired"),"critical"],
              ["driver_qualification_expiring_30d", t("Expiring ≤30d"),     "high"],
              ["archived_active",                 t("Archived but active"), "medium"],
              ["trainings_expired",               t("Expired training"),    "high"],
            ].map(([key, label, sev]) => (
              <div key={key} className={`border-2 rounded-md p-3 ${SEVERITY_TINTS[sev]}`}>
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold opacity-80">{label}</div>
                <div className="font-display text-2xl font-black leading-none mt-1">{summary[key] ?? 0}</div>
              </div>
            ))}
          </div>
        ) : null}

        {target.role === "pm" ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3" data-testid="notif-pm-summary">
            {[
              ["capa_overdue",       t("CAPAs past due"),    "high"],
              ["trainings_expired",  t("Expired training"),  "high"],
              ["ppe_missing",        t("No PPE"),            "medium"],
              ["driver_unavailable", t("Drivers unavailable"),"high"],
            ].map(([key, label, sev]) => (
              <div key={key} className={`border-2 rounded-md p-3 ${SEVERITY_TINTS[sev]}`}>
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold opacity-80">{label}</div>
                <div className="font-display text-2xl font-black leading-none mt-1">{summary[key] ?? 0}</div>
              </div>
            ))}
          </div>
        ) : null}

        {target.role === "dispatch" ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4" data-testid="notif-dispatch-summary">
            {[
              ["med_card_expired", t("Med card expired"), "critical"],
              ["cdl_expired",      t("CDL expired"),       "critical"],
              ["expiring_30d",     t("Expiring ≤30d"),     "high"],
            ].map(([key, label, sev]) => (
              <div key={key} className={`border-2 rounded-md p-3 ${SEVERITY_TINTS[sev]}`}>
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold opacity-80">{label}</div>
                <div className="font-display text-2xl font-black leading-none mt-1">{summary[key] ?? 0}</div>
              </div>
            ))}
          </div>
        ) : null}

        {target.role === "fl" ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3" data-testid="notif-fl-summary">
            {[
              ["trainings_expired",      t("Expired training"),  "high"],
              ["ppe_missing",            t("No PPE"),            "medium"],
              ["driver_unavailable",     t("Drivers unavailable"),"high"],
              ["incidents_needing_capa", t("Incidents need CAPA"),"high"],
            ].map(([key, label, sev]) => (
              <div key={key} className={`border-2 rounded-md p-3 ${SEVERITY_TINTS[sev]}`}>
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold opacity-80">{label}</div>
                <div className="font-display text-2xl font-black leading-none mt-1">{summary[key] ?? 0}</div>
              </div>
            ))}
          </div>
        ) : null}

        {err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="notif-error">{err}</div>
        ) : null}

        {/* Sections */}
        {sections.length === 0 && !loading ? (
          <div className="bg-white border-2 border-dashed border-emerald-200 rounded-md p-10 text-center" data-testid="notif-empty">
            <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-600 mb-3" />
            <div className="font-display text-lg font-black text-slate-900">
              {t("No operational signal today.")}
            </div>
            <div className="text-sm text-slate-600 mt-1">
              {t("Every monitored rule is clean for your role. Detection runs continuously — this surface refreshes the moment something changes.")}
            </div>
          </div>
        ) : null}

        <div className="space-y-3">
          {sections.map((s) => <SectionCard key={s.key} section={s} />)}
        </div>
      </div>
    </div>
  );
}
