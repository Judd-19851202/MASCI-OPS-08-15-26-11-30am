# DR-ROI-001D · Operational Summary Integration

## Rule

The Daily Operational Summary (`AISummarySection`) may cite photo evidence but **must not** override supervisor-entered facts. If a photo observation conflicts with structured entry, the conflict surfaces as a question — never as a rewrite.

## What the summary references

- Photo-linked activity cards (post-accept) — production_fact payload now carries `photo_evidence_links[]`, so the day_narrative agent sees a linked evidence chain.
- Photo-linked delays — delay_fact carries `evidence_links[]`.
- Photo-linked safety observations — safety_fact carries `evidence_links[]`.

The three agent prompts (day_narrative, risk_and_constraints, tomorrow_readiness) already require that every claim cite fields present in the evidence bundle. Photo evidence flows in as additional structured evidence — no prompt changes required.

## Language

Summary may say:
- "Photos support the trench work on the South storm line."
- "Photos indicate standing water on the east area; delay is noted."

Summary may NOT say:
- "AI detected trench work" — no "AI" label.
- "OpenAI vision confirms..." — no provider.
- "0.87 confidence" — the field-facing UI expresses confidence as a % badge on the aggregate, never per-source.

## Storage

Photo-referenced intelligence facts still land in `operational_facts` (fact_type=`intelligence_fact`) with `sources_facts: [<production_fact_id>, <photo_evidence_fact_id>, ...]` — full traceability preserved.
