# TRACK 19.36 · EXECUTIVE DASHBOARD

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Scope note
Track 19.16 Phase D shipped the platform-wide Executive Intelligence Center at `/safety/executive-intelligence` consuming `/api/incident-intelligence/*`. Track 19.36 does **not** modify that dashboard — it is preserved untouched under the Zero-Drift doctrine.

Track 19.36 delivers a **per-case boardroom report** (Executive Case Report) that fills the previously-missing "one screen · one case · executive-grade" surface. The two surfaces are complementary:

| Surface | Scope | Powered by |
|---|---|---|
| `/safety/executive-intelligence` (Phase D) | Platform-wide roll-up (open cases · trends · fleet · projects · brief) | `/api/incident-intelligence/*` (existing) |
| `/safety/cases/:caseId/executive-report` (19.36) | Single case · boardroom quality | `/api/incident-cases/{id}/executive-intelligence` (new · single model) |
| `/api/incident-cases/{id}/executive-report.pdf` (19.36) | Same case · printable PDF | Same model as above |

## Metrics available today (Phase D)
- Open cases · Critical cases · Avg readiness · SLA lanes.
- CAPA totals (open · overdue · in-flight).
- Project / fleet / learning cuts.
- Weekly digest.

All of these continue to work exactly as certified in Track 19.16 Phase D + E.

## Metrics newly consolidated (19.36 per-case model)
Per case, the new Executive Intelligence Model exposes:

- Days open · time-to-intake · time-to-CAPA · time-to-closure.
- Severity band with explicit rationale.
- Readiness sub-scores (6) with numerator, denominator, and human rationale.
- CAPA totals (total · open · verified · canceled).
- Regulatory / Insurance / Legal / Executive review buckets.
- Decision records (state transitions with actor / reason).
- Why-It-Matters briefing.

## Migration path (future track)
When the platform-wide dashboard is next revised, its per-case drill-downs should read the Track 19.36 model rather than the Phase D aggregate routes — this closes the loop on the "one intelligence object" architecture. **Not in scope for Track 19.36.**

## Zero drift
- No change to `ExecutiveIntelligence.jsx`.
- No change to `/api/incident-intelligence/*`.
- No change to the Phase D route table.
