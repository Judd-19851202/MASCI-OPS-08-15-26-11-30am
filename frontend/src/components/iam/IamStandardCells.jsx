/**
 * IamStandardCells — additive canonical IAM badge strip + audit link.
 *
 * Drop this into ANY existing portal-user panel's row to overlay the
 * canonical IAM contract on top of the panel's existing markup. No
 * existing element is removed; existing test-ids stay intact. The
 * canonical badges + audit link sit alongside the legacy markup.
 *
 * Usage (inside an existing <td> or <div>):
 *   <IamStandardCells user={u} portal="hr" />
 */
import React from "react";
import {
  IamAccessStatusBadge,
  IamPasswordStatusBadge,
  IamActivityLine,
  IamViewAuditLink,
} from "@/components/iam/IamBadges";

export function IamStandardCells({ user, portal, compact = false }) {
  if (!user) return null;
  return (
    <div
      data-testid={`iam-row-${portal}-${user.email || user.id}`}
      className={`inline-flex flex-wrap items-center gap-1.5 ${compact ? "" : "mt-1"}`}
    >
      <IamAccessStatusBadge user={user} portal={portal} />
      <IamPasswordStatusBadge user={user} portal={portal} />
      <IamViewAuditLink user={user} portal={portal} className="text-[10px]" />
      {!compact && (
        <span className="basis-full">
          <IamActivityLine user={user} portal={portal} />
        </span>
      )}
    </div>
  );
}
