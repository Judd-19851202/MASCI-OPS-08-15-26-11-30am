import React from "react";
import { SectionCard } from "../_ui";

/**
 * DR-ROI-001 · Phase C · Supervisor Approval Panel.
 *
 * Never auto-approves. Every supervisor action (accept / edit / reject /
 * regenerate) is written to the append-only audit log at
 * /api/dr-v2/ai/audit/:report_id.
 */
export default function SupervisorApprovalPanel({ ai, approvals }) {
  const last = approvals?.audit?.last_action || "unreviewed";
  const log = approvals?.audit?.log || [];

  const [reason, setReason] = React.useState("");
  const acceptAll = () => approvals?.submit("accept", { reason: "supervisor accepted full synthesis" });
  const rejectAll = () => approvals?.submit("reject", { reason: reason || "supervisor rejected synthesis" });
  const regen = () => {
    ai?.regenerate?.();
    approvals?.submit("regenerate", { reason: reason || "manual regenerate" });
  };

  return (
    <SectionCard id="panel-approval" title="Supervisor Approval" badge={last}>
      <div className="space-y-3 text-sm" data-testid="dr-v2-panel-approval">
        <p className="text-xs opacity-70">
          You are the source of truth. AI is a drafting assistant. Every action
          here is logged with a timestamp and cannot be deleted.
        </p>

        <div className="flex flex-wrap gap-2">
          <button
            className="text-xs rounded-md bg-emerald-800 hover:bg-emerald-700 px-3 py-1"
            onClick={acceptAll}
            data-testid="dr-v2-approval-accept-all"
            disabled={approvals?.busy}
          >
            Accept full synthesis
          </button>
          <button
            className="text-xs rounded-md border border-neutral-700 hover:border-amber-500 px-3 py-1"
            onClick={regen}
            data-testid="dr-v2-approval-regenerate"
            disabled={approvals?.busy}
          >
            Regenerate
          </button>
          <button
            className="text-xs rounded-md border border-neutral-700 hover:border-red-500 px-3 py-1"
            onClick={rejectAll}
            data-testid="dr-v2-approval-reject-all"
            disabled={approvals?.busy}
          >
            Reject
          </button>
        </div>

        <input
          className="w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs"
          placeholder="Reason (recorded in audit log)…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          data-testid="dr-v2-approval-reason"
        />

        <div className="rounded-md border border-neutral-800 bg-neutral-900/40 p-2 text-xs space-y-1 max-h-48 overflow-auto" data-testid="dr-v2-approval-log">
          <div className="font-semibold opacity-80">Audit log ({log.length})</div>
          {log.length === 0 ? (
            <div className="opacity-60">No actions yet.</div>
          ) : (
            [...log].reverse().map((e) => (
              <div key={e.entry_id} className="flex justify-between gap-2" data-testid={`dr-v2-approval-log-entry-${e.entry_id}`}>
                <span className="opacity-70 truncate">{e.ts?.slice(0, 19)} · <span className="uppercase text-[10px] tracking-wider">{e.action}</span>{e.agent ? ` · ${e.agent}` : ""}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </SectionCard>
  );
}
