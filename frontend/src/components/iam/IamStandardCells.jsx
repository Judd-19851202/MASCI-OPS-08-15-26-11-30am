/**
 * IamStandardCells — additive canonical IAM strip.
 *
 * iter505 · OMEGA Admin IAM Screen Completion Sprint:
 *   - Cleaner one-line row: [ACCESS] [PASSWORD] · activity-pill · [DETAILS] [AUDIT]
 *   - Maximum 2 status badges visible (access + password); never 4 stacked
 *   - Activity surfaces a single concise tag (e.g. "6/3/26", "Never", "—")
 *     instead of a multi-line strip. Hover tooltip explains "—".
 *
 * iter506 · OMEGA Unified User Detail Drawer Sprint:
 *   - Adds inline "Details" button which opens the canonical
 *     <IamUserDetailDrawerHost/> if mounted on the host page. Gracefully
 *     hides itself when the host is not present (no-op).
 *
 * Usage (inside an existing <td> or <div>):
 *   <IamStandardCells user={u} portal="hr" />
 */
import React from "react";
import { Eye } from "lucide-react";
import {
  IamAccessStatusBadge,
  IamPasswordStatusBadge,
  IamViewAuditLink,
} from "@/components/iam/IamBadges";
import { normalizeActivity, formatRelative } from "@/lib/iam/userBadges";
import { openIamUserDrawer } from "@/components/iam/IamUserDetailDrawer";

/**
 * Compact one-token activity summary.
 *   - "6/3/26"   when last_login is known
 *   - "Never"    when last_login explicitly null AND password ever issued
 *   - "—"        when nothing is known (tooltip: "Not tracked by this login source yet.")
 */
function ActivityPill({ user, portal }) {
  const a = normalizeActivity(user);
  let label;
  let tooltip;
  if (a.last_login) {
    label = formatRelative(a.last_login);
    tooltip = `Last login: ${label}` + (a.issued_by ? ` · issued by ${a.issued_by}` : "");
  } else if (a.last_password_issued) {
    label = "Never logged in";
    tooltip = `Password issued ${formatRelative(a.last_password_issued)}${a.issued_by ? ` by ${a.issued_by}` : ""} · user has not logged in yet`;
  } else {
    label = "—";
    tooltip = "Not tracked by this login source yet.";
  }
  return (
    <span
      data-testid={`iam-row-activity-${portal}-${user?.email || "x"}`}
      className="text-[11px] text-slate-500 whitespace-nowrap"
      title={tooltip}
    >
      {label}
    </span>
  );
}

export function IamStandardCells({ user, portal, compact = false }) {
  if (!user) return null;
  return (
    <div
      data-testid={`iam-row-${portal}-${user.email || user.id}`}
      className={`inline-flex flex-wrap items-center gap-1.5 ${compact ? "" : "mt-1"}`}
    >
      <IamAccessStatusBadge user={user} portal={portal} />
      <IamPasswordStatusBadge user={user} portal={portal} />
      <ActivityPill user={user} portal={portal} />
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          openIamUserDrawer(user, portal);
        }}
        data-testid={`iam-row-view-details-${portal}-${user.email || user.id}`}
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border border-slate-200 hover:bg-slate-100 text-[10px] text-slate-700 font-mono uppercase tracking-wide"
        title="View identity, portal access, password lifecycle, activity, and audit link"
      >
        <Eye className="w-3 h-3" />
        Details
      </button>
      <IamViewAuditLink user={user} portal={portal} className="text-[10px]" />
    </div>
  );
}
