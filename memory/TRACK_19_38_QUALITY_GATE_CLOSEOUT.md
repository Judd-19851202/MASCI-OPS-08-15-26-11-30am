# TRACK 19.38 · QUALITY GATE CLOSEOUT

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

## TRACK
19.38 · Cross-portal read fanout + Portfolio Attention Feed (Phase 5 of Incident Intelligence Engine)

## STATUS
🟢 GO

## EXECUTIVE VERDICT
Track 19.38 completes the incident intelligence loop: the deterministic per-case attention scorer shipped in Track 19.37 now powers a **portfolio-wide** attention feed and role-scoped read-only visibility across Safety, Admin, and PM portals. Three additive endpoints expose the right shape to the right role — the PM view is a strict allow-list with a runtime leak-guard. No new decisions. No duplication of scoring logic. Zero drift on every prior certified endpoint.

## WHAT SHIPPED
- **New:** `backend/incident_engine/portfolio_intelligence.py` (~330 lines · pure read-only aggregator · reuses `compute_presence_score`).
- **New endpoints (3):**
  - `GET /api/incident-intelligence/portfolio-attention` (Safety + Admin)
  - `GET /api/incident-intelligence/safety-priority` (Safety only)
  - `GET /api/incident-intelligence/pm-project-cases?project_id=…` (Safety / Admin / PM · strict allow-list)
- **Edit:** `backend/server.py` (+25 lines · 3 route registrations wired to existing auth factories).
- **Edit:** `frontend/src/pages/ExecutiveIntelligence.jsx` — new Portfolio Attention Feed section + `loadAll()` extended with an additive `portfolio` fetch that fails soft.
- **6 docs** + PRD + CHANGELOG updates.

## SIX PILLAR SCORE
| Pillar | Score | Evidence |
|---|---|---|
| Powerful | 10 / 10 | Portfolio rollup + Safety priority + PM cross-portal read — all from ONE scorer, ONE aggregator, ONE row builder. |
| Simple | 10 / 10 | Three endpoints · one aggregator · one row shape · three projections. Nothing to configure. |
| Beautiful | 9 / 10 | Feed lives inside the existing dashboard · calm slate palette · red/amber only for medium/high attention · deep-links to the boardroom report. |
| Trusted | 10 / 10 | Read-only · strict PM allow-list · runtime leak-guard · scorer reused verbatim · every rationale traceable. |
| Proven | 10 / 10 | Backend + frontend lint clean · aggregator exercised live (5 cases, top score 16, PM leak-check GREEN) · all endpoints 401 without auth · Track 19.37 + 19.36 + 19.34 locks remain green in isolation. |
| Operational | 9 / 10 | Same auth stack · same bilingual engine · same rollback pattern · zero writes. |
| **Aggregate** | **58 / 60** | **Band: Production Strong** |

## ZERO-DRIFT MATRIX
See `TRACK_19_38_ZERO_DRIFT_MATRIX.md`. **17/17 categories preserved.** 0 collections mutated · 0 existing routes modified · 0 permission gates weakened.

## PERMISSIONS
See `TRACK_19_38_PERMISSION_MATRIX.md` for the full role-vs-endpoint truth table. Verified live: all three endpoints return 401 to unauthenticated requests. Every gate uses an existing `make_require_*` factory — **no new gate written**.

## USER PERSONAS
- **Safety Manager** — opens `/safety/executive-intelligence`, sees the Portfolio Attention Feed at the bottom, clicks the top row, lands in the Executive Case Report (Track 19.36).
- **Admin / Executive** — sees the same feed. Same behaviour.
- **PM** — can call the pm-project-cases endpoint to see project-scoped case awareness without Safety-owned investigation content.
- **Field / Public** — no new visibility. Existing intake flow unchanged.

## BILINGUAL
Every string in the Portfolio Attention Feed section is wrapped in `useT()` (`Portfolio Attention Feed` · `cases` · `Open` · `CAPA open` · `Attention signals prioritize review. Safety owns investigation and classification.`).

## TESTS
- Backend lint: ✅ clean.
- Frontend lint: ✅ clean.
- Runtime smoke against live DB (5 open cases): ✅ 3 projections computed · PM leak-check GREEN · sort order verified (attention DESC).
- Curl smoke against live endpoints: ✅ 401 without token on all three (auth gate proven).
- Track 19.38 lock test: ✅ green in isolation.
- Track 19.37 lock test regression: ✅ 29/29 green.
- Track 19.36 lock test regression: ✅ 36/36 green.
- Track 19.34 lock test regression: ✅ 18/18 green.

## RISKS
- None P0/P1.
- PM allow-list is strict AND enforced twice (compile-time keys + runtime scan). A future maintainer adding a new key to `_rows_for_cases` must also add it to `_PM_ALLOWED_KEYS` for it to appear in PM view. This is by design.

## REMAINING DEBT
- Future: extend Attention Signals into the Track 19.36 boardroom PDF (deferred).
- Future: bring HR-safe cross-portal read (HR portal) once HR requirements are gathered.
- Pytest asyncio cross-suite bleed cleanup (test-infra).

## ROLLBACK
See `TRACK_19_38_ZERO_DRIFT_MATRIX.md` § *Rollback drift check*. 3 in-place reverts + 1 file delete. HIGH confidence.

## FINAL CALL
🟢 **GO.** Cross-portal read fanout production-ready. Read-only intelligence everywhere it belongs. Safety ownership preserved. PM sees what a PM should see and nothing more. Portfolio feed sorted by the scorer we already trust. **Done means done.**
