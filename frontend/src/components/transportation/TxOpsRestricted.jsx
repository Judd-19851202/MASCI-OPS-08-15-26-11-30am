/**
 * TRACK 18.00 · Phase F · Transportation-scoped restricted state.
 *
 * Replaces the Admin-Console-branded "Access denied" messaging when a
 * dispatch / safety / pm / fl / shop / hr token hits a Transportation
 * surface backed by an admin-strict endpoint. The user-facing chrome
 * must read TRANSPORTATION OPERATIONS, never the legacy admin gate.
 *
 * Doctrine:
 *   - Render this inline (workspace body) when an endpoint returns
 *     403, instead of bubbling up an Admin-Console redirect.
 *   - Honest: tell the user the workspace is restricted for their
 *     role, but never reveal what data is hidden.
 *   - Calm: no flashy reds, no scary icons. Operational.
 */
import React from "react";
import { Lock } from "lucide-react";

export default function TxOpsRestricted({
  workspace,
  reason,
  testid,
}) {
  return (
    <div
      data-testid={testid || "txops-restricted"}
      className="rounded-md border border-amber-300/40 bg-amber-50/60 px-4 py-6 text-center"
    >
      <Lock className="mx-auto h-5 w-5 text-amber-700 mb-2" aria-hidden />
      <div className="text-[11px] uppercase tracking-wider font-semibold text-amber-800">
        Transportation Operations
      </div>
      <p className="mt-1 text-sm text-slate-700 max-w-md mx-auto">
        {reason || (workspace
          ? `This Transportation workspace (${workspace}) is restricted for your role.`
          : "This Transportation workspace is restricted for your role.")}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Contact your dispatcher lead or operations manager to request access.
      </p>
    </div>
  );
}

export function TxOpsRestrictedData({ testid }) {
  return (
    <div
      data-testid={testid || "txops-restricted-data"}
      className="rounded-md border border-amber-300/40 bg-amber-50/60 px-4 py-3 text-xs text-slate-700"
    >
      <span className="font-semibold text-amber-800">Transportation Operations · </span>
      This Transportation data is not available for your role.
    </div>
  );
}
