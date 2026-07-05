import React from "react";
import { SectionCard } from "../_ui";

/**
 * DR-ROI-001 · Phase C · AI Summary Section.
 *
 * Renders the multi-agent narrative with per-agent confidence, evidence
 * citations, and inline supervisor edit. Supervisor is source of truth —
 * every action is written to the append-only audit log via useDrV2Approvals.
 */
export default function AISummarySection({ ai, approvals }) {
  const outputs = ai?.result?.outputs || {};
  const aiAvailable = ai?.meta?.ai_available && (ai?.result?.ai_available ?? true);
  const loading = ai?.loading;
  const error = ai?.error;

  const [editing, setEditing] = React.useState({}); // agent -> string

  const onEditChange = (agent, value) => setEditing((s) => ({ ...s, [agent]: value }));
  const commitEdit = async (agent) => {
    const edited = editing[agent];
    if (!edited || !edited.trim()) return;
    await approvals?.submit("edit", { agent, edited_narrative: edited });
    setEditing((s) => ({ ...s, [agent]: "" }));
  };
  const accept = (agent) => approvals?.submit("accept", { agent });
  const reject = (agent) => approvals?.submit("reject", { agent, reason: "supervisor rejected agent output" });
  const regen = () => ai?.regenerate();

  return (
    <SectionCard id="ai-summary" title="9 · Live AI Operational Summary" badge={loading ? "syncing" : aiAvailable ? "ready" : "off"}>
      {!aiAvailable ? (
        <div className="rounded-md border border-amber-800/60 bg-amber-950/30 px-4 py-3 text-sm" data-testid="dr-v2-ai-summary-disabled">
          AI synthesis is not enabled or the LLM key is missing. You can still
          submit the report manually; the supervisor remains the source of truth.
        </div>
      ) : null}

      {error ? (
        <div className="rounded-md border border-red-800/60 bg-red-950/30 px-4 py-3 text-xs" data-testid="dr-v2-ai-summary-error">
          {String(error)}
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <p className="text-sm opacity-70">
          Every claim below cites structured fields you entered. AI never invents
          facts. Accept, edit, or regenerate before you submit.
        </p>
        <button
          className="text-xs rounded-md border border-neutral-700 hover:border-red-500 px-2 py-1"
          onClick={regen}
          disabled={loading || !ai?.result}
          data-testid="dr-v2-ai-regenerate"
        >
          {loading ? "Regenerating…" : "Regenerate all"}
        </button>
      </div>

      <div className="space-y-3" data-testid="dr-v2-ai-outputs">
        {Object.keys(outputs).length === 0 ? (
          <div className="rounded-md border border-dashed border-neutral-700 bg-neutral-950/40 px-4 py-6 text-sm opacity-75" data-testid="dr-v2-ai-empty">
            {loading ? "Synthesizing…" : "Enter Day Setup + at least one Activity Card, then AI will synthesize."}
          </div>
        ) : (
          Object.entries(outputs).map(([agent, out]) => (
            <AgentCard
              key={agent}
              agent={agent}
              out={out}
              editingValue={editing[agent] ?? ""}
              onEditChange={(v) => onEditChange(agent, v)}
              onAccept={() => accept(agent)}
              onCommit={() => commitEdit(agent)}
              onReject={() => reject(agent)}
            />
          ))
        )}
      </div>
    </SectionCard>
  );
}

function AgentCard({ agent, out, editingValue, onEditChange, onAccept, onCommit, onReject }) {
  const confidence = Math.round((out?.confidence ?? 0) * 100);
  const [showRefs, setShowRefs] = React.useState(false);
  const title = agent.replaceAll("_", " ");

  return (
    <div
      className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-4 space-y-3"
      data-testid={`dr-v2-ai-agent-${agent}`}
    >
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold capitalize">{title}</div>
        <div className="flex items-center gap-2 text-xs">
          <span className={`rounded-full px-2 py-0.5 border ${confidence >= 75 ? "border-emerald-700 text-emerald-300" : confidence >= 50 ? "border-amber-700 text-amber-300" : "border-red-700 text-red-300"}`}
                data-testid={`dr-v2-ai-conf-${agent}`}>
            {confidence}% confidence
          </span>
          {out?.ai_available === false ? <span className="opacity-70">· offline</span> : null}
        </div>
      </div>

      <div className="text-sm whitespace-pre-wrap opacity-90" data-testid={`dr-v2-ai-narrative-${agent}`}>
        {out?.narrative || "(no narrative)"}
      </div>

      {out?.uncertainties?.length ? (
        <div className="text-xs rounded-md border border-amber-800/60 bg-amber-950/20 px-3 py-2" data-testid={`dr-v2-ai-uncertainty-${agent}`}>
          <div className="font-semibold mb-1">Uncertainties</div>
          <ul className="list-disc pl-4 space-y-0.5 opacity-90">
            {out.uncertainties.map((u, i) => <li key={i}>{u}</li>)}
          </ul>
        </div>
      ) : null}

      <button
        className="text-xs underline opacity-70 hover:opacity-100"
        onClick={() => setShowRefs((v) => !v)}
        data-testid={`dr-v2-ai-toggle-refs-${agent}`}
      >
        {showRefs ? "Hide" : "Show"} evidence ({out?.evidence_refs?.length || 0})
      </button>
      {showRefs ? (
        <div className="text-xs opacity-80 rounded-md border border-neutral-800 bg-neutral-900/40 p-2" data-testid={`dr-v2-ai-refs-${agent}`}>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-1">
            {(out?.evidence_refs || []).map((r, i) => (
              <li key={i} className="font-mono truncate" title={r}>· {r}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="pt-1 border-t border-neutral-800/60 flex flex-wrap items-center gap-2">
        <button
          className="text-xs rounded-md bg-emerald-800 hover:bg-emerald-700 px-2 py-1"
          onClick={onAccept}
          data-testid={`dr-v2-ai-accept-${agent}`}
        >
          Accept
        </button>
        <button
          className="text-xs rounded-md bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 px-2 py-1"
          onClick={onReject}
          data-testid={`dr-v2-ai-reject-${agent}`}
        >
          Reject
        </button>
        <div className="flex-1 min-w-[220px]">
          <input
            className="w-full rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs"
            placeholder="Optional supervisor edit…"
            value={editingValue}
            onChange={(e) => onEditChange(e.target.value)}
            data-testid={`dr-v2-ai-edit-input-${agent}`}
          />
        </div>
        <button
          className="text-xs rounded-md bg-red-700 hover:bg-red-600 px-2 py-1 disabled:opacity-50"
          onClick={onCommit}
          disabled={!editingValue?.trim()}
          data-testid={`dr-v2-ai-edit-commit-${agent}`}
        >
          Save edit
        </button>
      </div>
    </div>
  );
}
