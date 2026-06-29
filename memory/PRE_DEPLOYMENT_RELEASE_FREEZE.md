PRE-DEPLOYMENT RELEASE FREEZE
==============================

RELEASE NAME : MASCI Operations Platform · Track 18 Production Cut
TIMESTAMP    : 2026-02-15 (UTC)
DECISION     : ✅ GO (pending live release-candidate smoke pass)
GIT REF      : current HEAD on track-18 working branch (use `git log -1`
               at deploy time for the exact commit SHA stamp)

SCOPE FROZEN AT THIS POINT. NO NEW FEATURES UNTIL POST-DEPLOY.

────────────────────────────────────────────────────────────────────────────
INCLUDED TRACKS
────────────────────────────────────────────────────────────────────────────
- Track 18.00 Phase A (Universal Shell)
- Track 18.00 Phase B (Mission Control)
- Track 18.00 Phase C (Universal Search)
- Track 18.00 Phase D (Universal Relationships)
- Track 18.00 Phase E (Portal Transformation)
- Track 18.00E-FIX (Transportation Portal Rehome)
- Track 18.00 Phase F (Portal-Aware Data Layer)
- Track 18.00 Phase G (Final Polish)
- Track 18.01 (Platform language migration)
- Track 18.02 (Operational Design System foundation)
- Track 18.03 (Design-system linter rules R1–R6)
- Track 18.04 (Design-system linter rules R7 + critical amendment)
- Track 18.05 (PDF/email terminology updates)
- Track 18.06 (Hub/homepage language cleanup)
- Track 18.07 (Case-style lock)
- Track 18.08 (Device/browser polish · regression stability)
- Track 18.09  (Operational friction elimination)
- Track 18.09A (TRUE friction completion pass)
- Track 18.09C (Transportation ownership audit + UI re-routing)
- Track 18.10  (Governance boundary linter)
- Track 18.11  (R8 duplicate CTA linter calibration)
- Track 18.12  (Mission Control access + layout repair)
- Track 18.12B (Transportation dispatcher functionality restore)
- Track 18.12C (Transportation role permissions REAL functionality fix
                + VISIBLE = USABLE doctrine)

────────────────────────────────────────────────────────────────────────────
EXPLICITLY EXCLUDED (FUTURE / BACKLOG — DO NOT SHIP)
────────────────────────────────────────────────────────────────────────────
- Request Access CTA on restricted states
- Global Graph visualization of relationships
- Manual link/unlink relationship editing UI
- AI relationship suggestions
- Fuzzy search / fuzzy ranking
- Saved searches
- Cross-platform global relationship analytics outside Transportation
- Power-user keyboard shortcuts pack
- Operations-display dark mode
- Intelligence cold-start cache/index work (deferred — admin-only slow
  surface, not a blocker)

────────────────────────────────────────────────────────────────────────────
KNOWN NON-BLOCKING ISSUES
────────────────────────────────────────────────────────────────────────────
1. Admin `/api/admin/transportation/intelligence/{dashboard,
   recommendations,predictions,dispatch-learning}` cold-Mongo
   aggregation >30s on first load. Functional, slow only.
   IMPACT: admin only. Workaround: subsequent loads cached in-process.
2. Pre-existing Track 15.93 zero-touch-bootstrap test flakes only on
   heavy full-suite runs; passes solo in <2s. Not a product defect.
3. Pre-existing `react/no-unstable-nested-components` lint warning in
   `_orientation.jsx::Tile` — cosmetic React reconciliation hint, no
   functional impact.

────────────────────────────────────────────────────────────────────────────
DEPLOYMENT BLOCKERS
────────────────────────────────────────────────────────────────────────────
None identified as of this freeze. See:
  - PRE_DEPLOYMENT_TEST_RESULTS.md (linter + regression status)
  - PRE_DEPLOYMENT_ROLE_SMOKE_MATRIX.md (per-role functional smoke)
  - PRE_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE_GATE.md (high-risk area)
  - PRE_DEPLOYMENT_ENVIRONMENT_CHECK.md (config / env)
  - PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md (data preservation)

────────────────────────────────────────────────────────────────────────────
FINAL RELEASE DECISION
────────────────────────────────────────────────────────────────────────────
GO — provided:
  • the production environment swaps `APP_ENV=production` and points
    `MONGO_URL` / `DB_NAME` at the production cluster + database
    (this freeze captures preview values only).
  • a database snapshot is taken immediately before deploy (see
    PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md).
  • the live release-candidate smoke (testing_agent_v3_fork) reports
    no NEW critical issues.

Rollback point: capture `git log -1 --format=%H` and the database
snapshot URI before flipping the release.
