import React from "react";
import { Section } from "@/components/Section";
import { Button } from "@/components/ui/button";
import {
  StatusChip, inputCls,
} from "../_ui";

/**
 * DR-ROI-001 · Daily Operational Summary section.
 *
 * Renders the platform-generated narrative with per-source confidence and
 * evidence citations. Supervisor is the source of truth — every action is
 * appended to an audit log via useDrV2Approvals.
 *
 * Invisible Intelligence: never surfaces model or provider or agent
 * names, token counts, or internal telemetry. Field-facing language only.
 */
export default function AISummarySection({ ai, approvals }) {
  const outputs = ai?.result?.outputs || {};
  const summaryAvailable =
    ai?.meta?.ai_available && (ai?.result?.ai_available ?? true);
  const loading = ai?.loading;
  const error = ai?.error;

  const [editing, setEditing] = React.useState({});

  const onEditChange = (source, value) =>
    setEditing((s) => ({ ...s, [source]: value }));
  const commitEdit = async (source) => {
    const edited = editing[source];
    if (!edited || !edited.trim()) return;
    await approvals?.submit("edit", {
      agent: source,
      edited_narrative: edited,
    });
    setEditing((s) => ({ ...s, [source]: "" }));
  };
  const accept = (source) => approvals?.submit("accept", { agent: source });
  const reject = (source) =>
    approvals?.submit("reject", {
      agent: source,
      reason: "supervisor rejected suggestion",
    });
  const regen = () => ai?.regenerate();

  const badgeTone = loading ? "amber" : summaryAvailable ? "green" : "slate";
  const badgeText = loading ? "syncing" : summaryAvailable ? "ready" : "off";

  return (
    <Section
      number="09"
      title="Daily Operational Summary"
      testId="dr-v2-section-ai-summary"
      aside={
        <div className="flex items-center gap-2">
          <StatusChip tone={badgeTone}>{badgeText}</StatusChip>
          <Button
            type="button"
            variant="outline"
            className="h-9 border-2 border-slate-300"
            onClick={regen}
            disabled={loading || !ai?.result}
            data-testid="dr-v2-ai-regenerate"
          >
            {loading ? "Regenerating…" : "Regenerate"}
          </Button>
        </div>
      }
    >
      {!summaryAvailable ? (
        <div
          className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800"
          data-testid="dr-v2-ai-summary-disabled"
        >
          The summary engine is not enabled for your account yet. You can still
          submit the report — you remain the source of truth.
        </div>
      ) : null}

      {error ? (
        <div
          className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-xs text-red-800"
          data-testid="dr-v2-ai-summary-error"
        >
          {String(error)}
        </div>
      ) : null}

      <div className="space-y-3" data-testid="dr-v2-ai-outputs">
        {Object.keys(outputs).length === 0 ? (
          <div
            className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600"
            data-testid="dr-v2-ai-empty"
          >
            {loading
              ? "Preparing your daily operational summary…"
              : "Enter Day Setup and at least one Activity Card. A summary will appear here as evidence accumulates."}
          </div>
        ) : (
          Object.entries(outputs).map(([source, out]) => (
            <SummaryCard
              key={source}
              source={source}
              out={out}
              editingValue={editing[source] ?? ""}
              onEditChange={(v) => onEditChange(source, v)}
              onAccept={() => accept(source)}
              onCommit={() => commitEdit(source)}
              onReject={() => reject(source)}
            />
          ))
        )}
      </div>
    </Section>
  );
}

function SummaryCard({
  source, out, editingValue, onEditChange, onAccept, onCommit, onReject,
}) {
  const confidence = Math.round((out?.confidence ?? 0) * 100);
  const tone = confidence >= 75 ? "green" : confidence >= 50 ? "amber" : "red";
  const [showRefs, setShowRefs] = React.useState(false);
  const title = source.replaceAll("_", " ");

  return (
    <div
      className="rounded-xl border border-slate-200 bg-white p-4 space-y-3"
      data-testid={`dr-v2-ai-agent-${source}`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="text-sm font-semibold text-slate-900 capitalize">
          {title}
        </div>
        <StatusChip tone={tone} testid={`dr-v2-ai-conf-${source}`}>
          {confidence}% confidence
        </StatusChip>
      </div>

      <p
        className="text-sm whitespace-pre-wrap text-slate-800"
        data-testid={`dr-v2-ai-narrative-${source}`}
      >
        {out?.narrative || "(no narrative)"}
      </p>

      {out?.uncertainties?.length ? (
        <div
          className="text-xs rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-amber-900"
          data-testid={`dr-v2-ai-uncertainty-${source}`}
        >
          <div className="font-semibold mb-1">Items to verify</div>
          <ul className="list-disc pl-4 space-y-0.5">
            {out.uncertainties.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <button
        type="button"
        className="text-xs text-slate-600 hover:text-slate-900 underline"
        onClick={() => setShowRefs((v) => !v)}
        data-testid={`dr-v2-ai-toggle-refs-${source}`}
      >
        {showRefs ? "Hide" : "Show"} evidence ({out?.evidence_refs?.length || 0})
      </button>
      {showRefs ? (
        <div
          className="text-xs text-slate-700 rounded-md border border-slate-200 bg-slate-50 p-2"
          data-testid={`dr-v2-ai-refs-${source}`}
        >
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-1">
            {(out?.evidence_refs || []).map((r, i) => (
              <li key={i} className="font-mono truncate" title={r}>
                · {r}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="pt-2 border-t border-slate-200 flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="inline-flex items-center rounded-md bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold px-3 h-9"
          onClick={onAccept}
          data-testid={`dr-v2-ai-accept-${source}`}
        >
          Accept
        </button>
        <button
          type="button"
          className="inline-flex items-center rounded-md border-2 border-slate-300 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold px-3 h-9"
          onClick={onReject}
          data-testid={`dr-v2-ai-reject-${source}`}
        >
          Reject
        </button>
        <input
          className="h-11 flex-1 min-w-[220px] rounded-md border-2 border-slate-300 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600"
          placeholder="Optional supervisor edit…"
          value={editingValue}
          onChange={(e) => onEditChange(e.target.value)}
          data-testid={`dr-v2-ai-edit-input-${source}`}
        />
        <button
          type="button"
          className="inline-flex items-center rounded-md bg-red-700 hover:bg-red-600 text-white text-xs font-semibold px-3 h-9 disabled:bg-red-300"
          onClick={onCommit}
          disabled={!editingValue?.trim()}
          data-testid={`dr-v2-ai-edit-commit-${source}`}
        >
          Save edit
        </button>
      </div>
    </div>
  );
}
