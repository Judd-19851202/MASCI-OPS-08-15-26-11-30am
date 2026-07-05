import React from "react";
import { Section } from "@/components/Section";
import { fetchDrV2PhotoIntel, resolveDrV2PhotoQuestion } from "@/lib/drV2Api";
import { useDrV2Lang } from "@/lib/dailyReportV2Lang";

/**
 * DR-ROI-001F-FINAL-REPAIR · Photo Evidence — quiet & supportive.
 *
 * Shown only when photos exist and the platform has surfaced an
 * unresolved item to verify against the report. No AI branding, no
 * detection dashboards, no confidence dials. Just: "here's a question
 * about your photos, confirm or mark not applicable."
 */
export default function PhotoIntelligencePanel({ draft }) {
  const { t } = useDrV2Lang();
  const photos = draft?.photos || [];
  const [openQuestions, setOpenQuestions] = React.useState([]);

  React.useEffect(() => {
    let alive = true;
    async function load() {
      const items = [];
      for (let i = 0; i < Math.min(photos.length, 20); i++) {
        const p = photos[i];
        const id = typeof p === "string" ? p : p.id || p.ref;
        if (!id) continue;
        try {
          const data = await fetchDrV2PhotoIntel(id, draft?.report_id);
          const qs = (data?.intel?.questions || []).filter(
            (q) => q.status === "open",
          );
          qs.forEach((q) => items.push({ photo_id: id, ...q }));
        } catch (_) {
          /* silent — no field-facing errors */
        }
      }
      if (alive) setOpenQuestions(items.slice(0, 3));
    }
    if (photos.length) load();
    return () => {
      alive = false;
    };
  }, [photos, draft?.report_id]);

  if (!photos.length || openQuestions.length === 0) return null;

  async function resolve(q, resolution) {
    try {
      await resolveDrV2PhotoQuestion({
        photo_id: q.photo_id,
        question_id: q.question_id,
        resolution,
      });
      setOpenQuestions((qs) => qs.filter((x) => x.question_id !== q.question_id));
    } catch (_) {
      /* silent */
    }
  }

  return (
    <Section
      number="08b"
      title={t("s08b.title")}
      testId="dr-v2-section-photo-evidence"
      dense
    >
      <p className="text-sm text-slate-600 -mt-2 mb-3">
        {t("s08b.desc")}
      </p>
      <ul className="space-y-2" data-testid="dr-v2-photo-questions">
        {openQuestions.map((q) => (
          <li
            key={q.question_id}
            className="rounded-md border border-amber-300 bg-amber-50 p-3"
            data-testid={`dr-v2-photo-question-${q.question_id}`}
          >
            <div className="text-sm text-slate-800">{q.prompt}</div>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={() => resolve(q, "confirmed")}
                className="rounded-md border-2 border-slate-300 bg-white hover:border-emerald-500 hover:text-emerald-700 px-3 h-9 text-xs font-semibold"
              >
                {t("s08b.confirm")}
              </button>
              <button
                type="button"
                onClick={() => resolve(q, "not applicable")}
                className="rounded-md border-2 border-slate-300 bg-white hover:border-red-500 hover:text-red-700 px-3 h-9 text-xs font-semibold"
              >
                {t("s08b.na")}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </Section>
  );
}
