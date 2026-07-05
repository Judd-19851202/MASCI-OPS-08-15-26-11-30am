import React from "react";
import {
  SectionCard, primaryBtn, secondaryBtn, ghostBtn, inputCls, StatusChip,
} from "../_ui";

/**
 * DR-ROI-001 · Supervisor Approval Panel · DR-ROI-001F platform styling.
 *
 * Never auto-approves. Every supervisor action (accept / edit / reject /
 * regenerate) is written to the append-only audit log at
 * /api/dr-v2/ai/audit/:report_id.
 */
export default function SupervisorApprovalPanel({ ai, approvals }) {
  const last = approvals?.audit?.last_action || "unreviewed";
  const log = approvals?.audit?.log || [];

  const [reason, setReason] = React.useState("");
  const acceptAll = () =>
    approvals?.submit("accept", { reason: "supervisor accepted full synthesis" });
  const rejectAll = () =>
    approvals?.submit("reject", {
      reason: reason || "supervisor rejected synthesis",
    });
  const regen = () => {
    ai?.regenerate?.();
    approvals?.submit("regenerate", { reason: reason || "manual regenerate" });
  };

  return (
    <SectionCard
      id="panel-approval"
      title="Supervisor Approval"
      badge={last}
      description="You are the source of truth. Every action here is logged with a timestamp and cannot be deleted."
    >
      <div className="space-y-3" data-testid="dr-v2-panel-approval">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex items-center rounded-md bg-emerald-700 hover:bg-emerald-600 text-white text-sm font-semibold px-4 h-11 disabled:opacity-50"
            onClick={acceptAll}
            data-testid="dr-v2-approval-accept-all"
            disabled={approvals?.busy}
          >
            Accept full summary
          </button>
          <button
            type="button"
            className={secondaryBtn}
            onClick={regen}
            data-testid="dr-v2-approval-regenerate"
            disabled={approvals?.busy}
          >
            Regenerate
          </button>
          <button
            type="button"
            className={secondaryBtn}
            onClick={rejectAll}
            data-testid="dr-v2-approval-reject-all"
            disabled={approvals?.busy}
          >
            Reject
          </button>
        </div>

        <input
          className={inputCls}
          placeholder="Reason (recorded in audit log)…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          data-testid="dr-v2-approval-reason"
        />

        <div
          className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs space-y-1 max-h-52 overflow-auto"
          data-testid="dr-v2-approval-log"
        >
          <div className="font-semibold text-slate-800 flex items-center justify-between">
            <span>Audit log</span>
            <StatusChip tone="slate">{log.length} entries</StatusChip>
          </div>
          {log.length === 0 ? (
            <div className="text-slate-500">No actions yet.</div>
          ) : (
            [...log].reverse().map((e) => (
              <div
                key={e.entry_id}
                className="flex justify-between gap-2 text-slate-700"
                data-testid={`dr-v2-approval-log-entry-${e.entry_id}`}
              >
                <span className="truncate">
                  {e.ts?.slice(0, 19)} ·{" "}
                  <span className="uppercase text-[10px] tracking-wider text-red-700 font-bold">
                    {e.action}
                  </span>
                  {e.agent ? ` · ${e.agent}` : ""}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </SectionCard>
  );
}
