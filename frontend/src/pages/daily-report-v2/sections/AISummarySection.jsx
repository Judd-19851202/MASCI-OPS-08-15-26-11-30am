import React from "react";
import { Section } from "@/components/Section";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { StatusChip } from "../_ui";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

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
  const { t, lang } = useDrV2Lang();
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
      title={t("s09.title")}
      testId="dr-v2-section-ai-summary"
      aside={
        accepted ? (
          <StatusChip tone="green">{t("s09.accepted")}</StatusChip>
        ) : (
          <StatusChip tone="slate">{t("s09.draft")}</StatusChip>
        )
      }
    >
      <p className="text-sm text-slate-600 -mt-2 mb-3">
        {t("s09.desc")}
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
          {t("s09.empty")}
        </div>
      ) : editing ? (
        <Textarea
          className="min-h-[180px] text-base border-2 border-slate-300"
          value={text}
          onChange={(e) => setText(e.target.value)}
          data-testid="dr-v2-ai-editor"
          lang={lang}
        />
      ) : (
        <div
          className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-800 whitespace-pre-wrap"
          data-testid="dr-v2-ai-summary-body"
          lang={lang}
        >
          {loading ? (
            <span className="text-slate-500 italic">
              {t("s09.loading")}
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
          {editing ? t("s09.save") : t("s09.accept")}
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
            {t("s09.edit")}
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
            {t("s09.cancel")}
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
          {loading ? t("s09.regenerating") : t("s09.regenerate")}
        </Button>
      </div>
    </Section>
  );
}
