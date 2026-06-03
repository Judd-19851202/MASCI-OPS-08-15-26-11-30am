/**
 * IAM Badge Components — OMEGA Standardization Sprint
 *
 * Tiny, reusable badge components that render the canonical access /
 * password badges and the row-level "View audit history" link.
 *
 * Importing panels keep their existing markup; they just swap their
 * local status badges + add the audit link.
 *
 * No backend calls. No state. Pure rendering.
 */
import React from "react";
import { Link } from "react-router-dom";
import { History } from "lucide-react";
import {
  normalizeAccessStatus, normalizePasswordStatus, normalizeActivity,
  ACCESS_BADGE_CLASS, ACCESS_BADGE_LABEL,
  PASSWORD_BADGE_CLASS, PASSWORD_BADGE_LABEL,
  formatRelative,
} from "@/lib/iam/userBadges";

export function IamAccessStatusBadge({ user, portal }) {
  const state = normalizeAccessStatus(user);
  const cls = ACCESS_BADGE_CLASS[state] || ACCESS_BADGE_CLASS.PENDING_ACTIVATION;
  const label = ACCESS_BADGE_LABEL[state];
  return (
    <span
      data-testid={`iam-row-status-${portal}-${user?.email || "x"}`}
      data-iam-status={state}
      className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${cls}`}
      title={`Access status: ${label}`}
    >
      {label}
    </span>
  );
}

export function IamPasswordStatusBadge({ user, portal }) {
  const state = normalizePasswordStatus(user);
  const cls = PASSWORD_BADGE_CLASS[state] || PASSWORD_BADGE_CLASS.NEVER_ISSUED;
  const label = PASSWORD_BADGE_LABEL[state];
  return (
    <span
      data-testid={`iam-row-pwstatus-${portal}-${user?.email || "x"}`}
      data-iam-password={state}
      className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${cls}`}
      title={`Password status: ${label}`}
    >
      {label}
    </span>
  );
}

/**
 * Compact activity strip — Last login · Last password issued · Issued by.
 * Renders "—" for unavailable fields rather than hiding them.
 */
export function IamActivityLine({ user, portal }) {
  const a = normalizeActivity(user);
  return (
    <div
      data-testid={`iam-row-activity-${portal}-${user?.email || "x"}`}
      className="text-[11px] text-slate-500 leading-tight flex flex-wrap gap-x-3 gap-y-0.5"
    >
      <span>
        <span className="font-mono uppercase tracking-wider text-[9px] text-slate-400">Last login</span>{" "}
        {formatRelative(a.last_login)}
      </span>
      <span>
        <span className="font-mono uppercase tracking-wider text-[9px] text-slate-400">Last pw issued</span>{" "}
        {formatRelative(a.last_password_issued)}
      </span>
      <span>
        <span className="font-mono uppercase tracking-wider text-[9px] text-slate-400">Issued by</span>{" "}
        {a.issued_by || "—"}
      </span>
    </div>
  );
}

/**
 * Canonical "View audit history" deep link.
 * Routes to the existing /admin/audit page filtered by the user's email.
 */
export function IamViewAuditLink({ user, portal, className = "" }) {
  if (!user?.email) return null;
  const href = `/admin/audit?actor=${encodeURIComponent(user.email)}`;
  return (
    <Link
      to={href}
      data-testid={`iam-row-view-audit-${portal}-${user.email}`}
      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide text-slate-700 hover:bg-slate-100 ${className}`}
      title="View audit history for this user"
    >
      <History className="w-3 h-3" />
      <span className="hidden sm:inline">Audit</span>
    </Link>
  );
}
