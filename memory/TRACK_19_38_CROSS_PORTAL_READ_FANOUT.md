# TRACK 19.38 · CROSS-PORTAL READ FANOUT

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillar: 58/60 · Production Strong · Zero-Drift**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md` · `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md` · `TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md`

## Charter
Surface incident intelligence to the right portals in the right shape. Read-only. Additive only. No new decisions. No leakage of Safety-owned fields to PM / Field / Public. Reuse the Track 19.37 deterministic scorer — never duplicate scoring logic.

## What shipped

### New backend module
`backend/incident_engine/portfolio_intelligence.py` — pure read-only aggregator with role-scoped projections. Never writes. Reuses `compute_presence_score` from Track 19.37.

### Three additive endpoints
| Method | Route | Auth gate | View |
|---|---|---|---|
| GET | `/api/incident-intelligence/portfolio-attention` | Safety **or** Admin | Portfolio — attention feed with top 3 signals per case |
| GET | `/api/incident-intelligence/safety-priority` | Safety **only** | Same shape + Safety preview fields (root_cause present · executive reviewer present · investigator name) |
| GET | `/api/incident-intelligence/pm-project-cases?project_id=…` | Safety / Admin / PM | **Strict allow-list** — 15 keys only · no signals · no rationales · no safety_block · no regulatory_review |

All three sort cases by `attention_score` DESC (then `days_open` DESC as tiebreak).

### Frontend
- Additive **Portfolio Attention Feed** section on the existing `/safety/executive-intelligence` page.
- Bilingual via `useT()`.
- Deep-links each row into the Track 19.36 Executive Case Report.
- Neutral wording — no OSHA / liability / root-cause / discipline terms.

## Architecture
Single row builder (`_rows_for_cases`) produces one uniform per-case dict. Three role-scoped projections (`_view_portfolio` · `_view_safety` · `_view_pm`) whittle that dict down to what the role is allowed to see. The PM projection is a **strict allow-list** — anything not on the 15-key list is dropped, and a runtime `_assert_pm_safe` scan asserts no forbidden token leaks (belt-and-braces).

## Zero-drift protection
- Existing `/api/incident-intelligence/*` endpoints (Track 19.16 Phase D) preserved byte-for-byte.
- Existing `/api/incident-cases/*` endpoints preserved byte-for-byte.
- No schemas mutated.
- No permissions widened; each gate uses the existing `make_require_*` factory.
- Direct read-only Mongo query in the aggregator bypasses `case_service.list_cases` (which has a write-side actor gate) so the read-only aggregator does not need to widen permissions.

## Rollback
1. Delete `backend/incident_engine/portfolio_intelligence.py`.
2. Remove the `_register_ie_portfolio_routes(…)` block in `server.py`.
3. Remove the Portfolio Attention Feed `<section>` block in `ExecutiveIntelligence.jsx` and revert the `loadAll()` `portfolio` fetch.

**Rollback confidence:** HIGH. Additive-only.
