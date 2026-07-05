import React from "react";
import { Section } from "@/components/Section";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { StatusChip } from "../_ui";

/**
 * DR-ROI-001F-FINAL-REPAIR · Daily Operational Summary.
 *
 * The ONLY major new supervisor-facing concept on the Daily Job Report.
 * The platform drafts a summary from what the supervisor entered plus
 * photos. Supervisor can Accept, Edit, or Regenerate. That's it.
 *
 * No per-source dashboards, no readiness scores, no audit log, no AI
 * branding — those exist under the hood but never surface here.
 */
function pickPrimaryNarrative(outputs) {
  // Prefer the aggregate synthesis if present, else the longest narrative,
  // else empty string.
  if (!outputs || typeof outputs !== "object") return "";
  const values = Object.values(outputs).filter(Boolean);
  if (values.length === 0) return "";
  const aggregate = outputs.aggregate || outputs.summary || outputs.report;
  if (aggregate?.narrative) return aggregate.narrative;
  return values
    .map((v) => v?.narrative || "")
    .filter(Boolean)
    .join("\n\n");
}

export default function AISummarySection({ ai, approvals }) {
  const outputs = ai?.result?.outputs || {};
  const suggested = React.useMemo(() => pickPrimaryNarrative(outputs), [outputs]);
  const loading = ai?.loading;
  const error = ai?.error;

  const [editing, setEditing] = React.useState(false);
  const [text, setText] = React.useState("");

  // Reset the editor text whenever a fresh suggestion arrives (and the
  // supervisor is not already editing).
  React.useEffect(() => {
    if (!editing && suggested) setText(suggested);
  }, [suggested, editing]);

  const accepted =
    approvals?.audit?.last_action === "accept" ||
    approvals?.audit?.last_action === "edit";

  async function onAccept() {
    await approvals?.submit("accept", { final_narrative: text || suggested });
  }
  async function onSaveEdit() {
    await approvals?.submit("edit", { edited_narrative: text });
    setEditing(false);
  }
  function onRegenerate() {
    setEditing(false);
    ai?.regenerate?.();
  }

  return (
    <Section
      number="09"
      title="Daily Operational Summary"
      testId="dr-v2-section-ai-summary"
      aside={
        accepted ? (
          <StatusChip tone="green">accepted</StatusChip>
        ) : (
          <StatusChip tone="slate">draft</StatusChip>
        )
      }
    >
      <p className="text-sm text-slate-600 -mt-2 mb-3">
        Review the summary below before submitting. Edit anything that
        needs corrected · you remain the source of truth.
      </p>

      {error ? (
        <div
          className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-800 mb-2"
          data-testid="dr-v2-ai-summary-error"
        >
          {String(error)}
        </div>
      ) : null}

      {!suggested && !loading ? (
        <div
          className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600"
          data-testid="dr-v2-ai-empty"
        >
          Add Day Setup, at least one Activity Card, and Photos. A summary
          will be drafted for you here.
        </div>
      ) : editing ? (
        <Textarea
          className="min-h-[180px] text-base border-2 border-slate-300"
          value={text}
          onChange={(e) => setText(e.target.value)}
          data-testid="dr-v2-ai-editor"
        />
      ) : (
        <div
          className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-800 whitespace-pre-wrap"
          data-testid="dr-v2-ai-summary-body"
        >
          {loading ? (
            <span className="text-slate-500 italic">
              Drafting your daily summary from what you entered…
            </span>
          ) : (
            text || suggested
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mt-3">
        <Button
          type="button"
          className="h-11 px-4 bg-red-700 hover:bg-red-600 text-white font-bold uppercase tracking-wide"
          onClick={editing ? onSaveEdit : onAccept}
          disabled={loading || (!suggested && !text)}
          data-testid="dr-v2-ai-accept"
        >
          {editing ? "Save Summary" : "Accept Summary"}
        </Button>
        {!editing ? (
          <Button
            type="button"
            variant="outline"
            className="h-11 border-2 border-slate-300 uppercase tracking-wide font-semibold"
            onClick={() => setEditing(true)}
            disabled={loading || !suggested}
            data-testid="dr-v2-ai-edit"
          >
            Edit Summary
          </Button>
        ) : (
          <Button
            type="button"
            variant="outline"
            className="h-11 border-2 border-slate-300 uppercase tracking-wide font-semibold"
            onClick={() => {
              setText(suggested);
              setEditing(false);
            }}
            data-testid="dr-v2-ai-cancel-edit"
          >
            Cancel Edit
          </Button>
        )}
        <Button
          type="button"
          variant="outline"
          className="h-11 border-2 border-slate-300 uppercase tracking-wide font-semibold"
          onClick={onRegenerate}
          disabled={loading}
          data-testid="dr-v2-ai-regenerate"
        >
          {loading ? "Regenerating…" : "Regenerate Summary"}
        </Button>
      </div>
    </Section>
  );
}
