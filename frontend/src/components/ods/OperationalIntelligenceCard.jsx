import React from "react";

/**
 * TRACK 22.9C · Operational Intelligence Card
 *
 * Renders supervisor-accepted operational summaries + grounded photo
 * observation tags for a PM project. Reads canonical ODS facts only
 * (`day_summary_fact` + `photo_evidence_fact`) — never raw daily_reports.
 * Never surfaces AI provider / model / raw metadata.
 *
 * `summaries`: array of `{ fact_id, project_id, date, excerpt, meta_source, char_count, accepted_at }`.
 * `photoTags`: array of `{ tag, count }`.
 * `title`: optional heading (defaults to "Recent Operational Intelligence").
 * `testid`: root data-testid.
 */
export function OperationalIntelligenceCard({
  summaries = [],
  photoTags = [],
  title = "Recent Operational Intelligence",
  testid = "pm-operational-intelligence-card",
}) {
  const hasSummaries = Array.isArray(summaries) && summaries.length > 0;
  const hasTags = Array.isArray(photoTags) && photoTags.length > 0;

  if (!hasSummaries && !hasTags) {
    return null;
  }

  return (
    <section data-testid={testid}>
      <div className="rounded-lg border border-neutral-200 bg-white p-4">
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500">
              PM operational intelligence
            </div>
            <h3 className="text-base font-semibold text-neutral-900">
              {title}
            </h3>
          </div>
          <div className="text-[10px] text-neutral-400 font-mono">
            source: day_summary_fact · photo_evidence_fact
          </div>
        </div>

        {hasSummaries ? (
          <ul
            className="divide-y divide-neutral-100 mb-4"
            data-testid={`${testid}-summaries`}
          >
            {summaries.map((s) => (
              <li
                key={s.fact_id}
                className="py-3"
                data-testid={`${testid}-summary-${s.fact_id}`}
              >
                <div className="flex items-baseline justify-between gap-3 mb-1">
                  <div className="font-mono text-[11px] text-neutral-500">
                    {s.date} · {s.project_id}
                  </div>
                  <div className="text-[10px] uppercase tracking-widest text-neutral-400">
                    {s.meta_source === "supervisor_edited"
                      ? "Supervisor edited"
                      : "Supervisor accepted"}
                  </div>
                </div>
                <div className="text-sm text-neutral-900 leading-relaxed whitespace-pre-wrap">
                  {s.excerpt}
                </div>
                {s.char_count && s.char_count > 280 ? (
                  <div className="text-[11px] text-neutral-500 mt-1">
                    Full narrative in the Daily Report PDF.
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-neutral-500 mb-4">
            No supervisor-accepted summaries in this range.
          </div>
        )}

        {hasTags ? (
          <div data-testid={`${testid}-photo-tags`}>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">
              Photo observations (requires supervisor confirmation)
            </div>
            <div className="flex flex-wrap gap-1.5">
              {photoTags.map((t) => (
                <span
                  key={t.tag}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-neutral-200 bg-neutral-50 text-xs text-neutral-800"
                  data-testid={`${testid}-tag-${t.tag}`}
                >
                  <span>{t.tag}</span>
                  <span className="text-[10px] text-neutral-500 tabular-nums">
                    {t.count}
                  </span>
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
