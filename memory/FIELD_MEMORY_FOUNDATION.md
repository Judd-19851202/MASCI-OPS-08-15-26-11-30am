# Field Memory Foundation

_Phase V-Prelude · Priority #7 · doctrine + scope · 2026-05-28._

## Mission

The platform should accumulate institutional knowledge over time
WITHOUT becoming an "AI copilot". Recurring patterns surface
quietly — "this utility conflict appeared 4 times on SR-7 last
month" — without unsolicited recommendations.

This is **field memory**, not analytics spam. Not summarization.
Not sentiment scoring. Not coaching. Just deterministic counting
and chronology.

## Doctrine

1. **No language models. No embedding. No "AI features."**
2. **Deterministic counters, not predictions.** "5 occurrences
   in 30 days" is fine. "Likely recurring" is not.
3. **Surface, don't suggest.** Show what has happened. Never
   recommend what should happen next.
4. **Operator-driven discovery.** Field memory is OPT-IN — the
   operator searches for a thing and the memory surfaces
   alongside.

## Initial patterns to count (deterministic)

| Pattern | Source | Threshold to surface |
|---|---|---|
| Same utility-conflict discipline on same project | constraints | 3+ in 30 days |
| Same density-test failure on same project | inspections | 2+ in 14 days |
| Same MOT restriction kind reappearing | constraints | 2+ in 30 days |
| Same FAA-closure cause | constraints | any 2 records |
| Same subcontractor + same delay reason | constraints | 3+ in 60 days |
| Same incident kind, same location | incidents | 3+ in 90 days |

**Counts only. No ranking. No score.**

## Surface (calm)

When an operator opens a constraint detail page, a small slate
text section appears IF a pattern is detected:

```
⚮ Field memory · this project, last 30 days
  · 3 similar utility conflicts logged (SR-7 corridor)
  · 1 was resolved in 4 days · 1 in 11 days · 1 still open
  · last similar resolution note: "ULM coord required"
```

That's it. No "would you like to..." prompts. No "recommended
actions". The operator decides what to do with the information.

## Architecture

### Backend (single endpoint)
```
GET /api/field-memory?context=<constraint|incident|inspection>&ref_id=<id>
→ {
    "patterns": [
      { "label": "...", "count": 3, "window_days": 30, "links": [ids] },
      ...
    ],
    "generated_at": "tz-aware ISO"
  }
```

Implementation: pure Mongo aggregation pipeline. ≤ 200 ms p95.
No precomputed cache (small dataset · always fresh).

### Frontend
A tiny calm panel component reused across constraint / incident /
inspection detail pages. No animation. Slate text. No icons
beyond the existing Lucide set.

## What this is NOT

- ⛔ Not an LLM-based summarizer.
- ⛔ Not predictive scoring.
- ⛔ Not a "smart suggestions" panel.
- ⛔ Not a dashboard widget.
- ⛔ Not a notification.
- ⛔ Not surfaced unless the operator is already looking at the
  relevant detail surface.

## Governance hooks

- TRUST-TIME-1 compliant on all timestamps.
- Authority Mismatch Probe: no new patterns.
- OPS-1 `trust_surfaces` registry adds one entry:
  `field-memory-panel` (read-only · authority hidden · count-only).
- The endpoint is admin-readable for diagnostics:
  `/api/admin/field-memory/health`.

## Privacy doctrine

- No employee names in pattern surface.
- No EXIF GPS in pattern surface.
- No PII whatsoever in `/api/field-memory` responses.

## Phase-V handoff

When V.1 RFI MVP lands, RFI patterns become countable:
"3 similar RFIs on this project resolved by GC clarification
within 7 days." Same primitive. New `context` value.

## Stop condition

Doctrine only. Implementation lands AFTER Priority #1
(constraints) — the constraints collection is the first
non-trivial source of patterns.
