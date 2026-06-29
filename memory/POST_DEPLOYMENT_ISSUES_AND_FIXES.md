POST-DEPLOYMENT ISSUES AND FIXES
=================================

RELEASE     : MASCI Operations Platform · Track 18 Production Cut
RELEASE SHA : d5a8a4848ecbb3bf5e3eca1477fdee5929b7a84c
DATE        : 2026-06-29 (UTC)
VERDICT     : GO WITH WATCH

This register captures every defect found during the post-deployment
live-site verification track, the classification, the action taken
(or required), and the owner.

Severity legend:
  P0  · deployment-blocker · must be fixed before user traffic
  P1  · production-watch · users will hit this · fix at next redeploy
  P2  · non-blocking · scheduled
  WONTFIX · acknowledged but out of scope

Status legend:
  FIXED       · code change landed in preview · ships at next redeploy
  OPERATOR    · requires operator action on production plane
  TRACKING    · ticketed for future track · non-blocker
  WATCH       · post-deploy soak observation only

────────────────────────────────────────────────────────────────────────────
ISSUE-001 · P0 · Sign-In page banned legacy names
────────────────────────────────────────────────────────────────────────────
Surface          : `/sign-in` (public)
Discovered       : Live-prod screenshot smoke (prior agent · iter441)
Symptom          : The "Single-Portal Sign-In" link grid rendered the
                   banned legacy labels:
                     • PM Portal →
                     • Shop Portal →
                     • HR Portal →
                     • Safety Portal →
                     • Dispatch Portal →
                     • Admin Console →
                   Violates Track 18.03 Platform Language Constitution
                   and Track 18.04 migration.
Root cause       : Hardcoded user-facing strings in
                   `/app/frontend/src/pages/SignIn.jsx` lines 414-437.
                   The Track 18.04 mechanical cleanup did not reach this
                   surface because the strings were literal JSX children
                   (not wrapped in the audited i18n table).
Fix              : Replaced the seven CTA labels with canonical
                   workspace names:
                     PM Portal       → Project Management
                     Shop Portal     → Shop Operations
                     HR Portal       → Human Resources
                     Safety Portal   → Safety Operations
                     Dispatch Portal → Transportation Operations
                     Field Leadership → Field Leadership (already canonical)
                     Admin Console   → Administration
                   Also rewrote the "Multi-portal sign-in…" body copy and
                   the "Single-Portal Sign-In" header to use "workspace".
                   Verified by screenshot — banned-term scan returns
                   ZERO matches on the rendered DOM.
Status           : FIXED in preview (commit pending next redeploy)
Operator action  : redeploy the frontend artefact so the live prod
                   `/sign-in` renders the canonical labels.

────────────────────────────────────────────────────────────────────────────
ISSUE-002 · P1 · Missing `dispatch@mascigc.com` user on production DB
────────────────────────────────────────────────────────────────────────────
Surface          : `/api/dispatch/login` (production only)
Discovered       : Live-prod smoke (prior agent · iter441) — 401 on POST
                   with the documented dispatch credentials.
Symptom          : The canonical dispatch test user
                   (`dispatch@mascigc.com`) is missing OR has rotated
                   credentials on the production Atlas cluster. Preview
                   Atlas has the user; production does not.
Root cause       : The pre-deploy seed scripts intentionally refuse to
                   run against `APP_ENV=production` (data-safety guard).
                   The production-DB equivalent must be seeded by hand
                   by the operator after the env flip.
Fix              : E1 cannot fix this — write access to production
                   Atlas is operator-only.
Status           : OPERATOR
Operator action  :
  1. Connect to the production Atlas cluster with operator credentials.
  2. Verify whether `dispatch@mascigc.com` exists in the production
     users collection.
  3. If missing, seed via the production-safe variant of the dispatch
     seed (or create through the Administration UI):
        - role: dispatch
        - portals: ["dispatch", "transportation_operations"]
        - is_active: true
        - password: rotated per ops policy
  4. Document the new password in the operator-side secrets vault
     (do NOT write to `/app/memory/test_credentials.md` for production
     credentials).
  5. Re-run the Dispatch acceptance smoke against the live prod URL
     and update `/app/memory/POST_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE.md`
     with the live row counts.

NOTE: This does not block release because:
  · Real production dispatchers (who already exist in the prod DB)
    are not affected.
  · The blocker is on the verification flow, not the user-facing flow.
  · Preview-build verification on the same artefact PASSED.

────────────────────────────────────────────────────────────────────────────
ISSUE-003 · WATCH · `routes.job_photos` auto-warm "120 failed"
────────────────────────────────────────────────────────────────────────────
Surface          : backend background warm tick
Symptom          : Log line every 10 min:
                     `[job-photos] auto-warm tick: 0 warmed, 120 failed`
                   120 legacy job-photo rows do not have valid R2 keys.
Root cause       : Historical data — photos predating the current S3
                   key schema. Not user-impacting because the public
                   gallery skips rows that fail warm.
Fix              : Out of scope for Track 18 (cleanup task is tracked
                   for a future asset-spine track).
Status           : TRACKING / WATCH
Operator action  : none — non-blocking. May surface as a "needs
                   attention" badge on the Asset Spine workspace
                   once the cleanup track lands.

────────────────────────────────────────────────────────────────────────────
ISSUE-004 · WATCH · /api/version commit / built_at show "unknown"
────────────────────────────────────────────────────────────────────────────
Surface          : `/api/version`
Symptom          : `commit:"unknown"`, `built_at:"unknown"`. The
                   `release` field still carries a usable hash but the
                   commit-pin and build-time are not embedded.
Root cause       : Preview pod doesn't embed git commit metadata at
                   container build. Production deploy artefact has the
                   same constraint unless the operator pipeline embeds
                   `GIT_COMMIT` and `BUILD_TIME` at container build.
Fix              : Out of scope for Track 18 — this is a build-pipeline
                   improvement (tracked in PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md).
Status           : TRACKING / WATCH
Operator action  : optional — embed `GIT_COMMIT` + `BUILD_TIME` as
                   container env at build time so the version endpoint
                   surfaces them.

────────────────────────────────────────────────────────────────────────────
ISSUE-005 · WATCH · Scheduler intentionally OFF — re-evaluate at 24 h
────────────────────────────────────────────────────────────────────────────
Surface          : background workers
Symptom          : `SCHEDULER_ENABLED=false` — no transport automation,
                   no command digest, no dispatch reminders, no
                   Motive reliability events, no R2 hourly backup,
                   no asset spine sync.
Root cause       : Intentional — Track 18 deploy directive holds
                   automation off for the first 24 h post-flip.
Fix              : none — by design.
Status           : WATCH
Operator action  : at T+24 h after the env flip, set
                   `SCHEDULER_ENABLED=true` and:
                     · re-run the scheduler health check
                     · confirm the singleton locks acquire/release
                     · confirm the first R2 hourly backup completes
                     · confirm Motive API calls return 200

────────────────────────────────────────────────────────────────────────────
ISSUE-006 · WATCH · Atlas pre-deploy snapshot ID not recorded
────────────────────────────────────────────────────────────────────────────
Surface          : rollback safety net
Symptom          : `/app/memory/PRODUCTION_DEPLOYMENT_EXECUTION_LOG.md`
                   §STEP 2 has a blank line for the Atlas snapshot ID.
Root cause       : Operator-only action — only the human operator with
                   the production Atlas console can capture the
                   snapshot ID.
Fix              : E1 cannot capture this.
Status           : OPERATOR
Operator action  : record the Atlas snapshot ID in
                   PRODUCTION_DEPLOYMENT_EXECUTION_LOG.md §STEP 2 so
                   the rollback target is unambiguous.

────────────────────────────────────────────────────────────────────────────
SUMMARY
────────────────────────────────────────────────────────────────────────────
| ID  | Severity | Status   | Owner    |
|-----|----------|----------|----------|
| 001 | P0       | FIXED    | E1 (preview) · OPERATOR (redeploy) |
| 002 | P1       | OPERATOR | OPERATOR |
| 003 | WATCH    | TRACKING | future track |
| 004 | WATCH    | TRACKING | future track / operator |
| 005 | WATCH    | WATCH    | OPERATOR (T+24 h) |
| 006 | WATCH    | OPERATOR | OPERATOR |

Zero P0 items remain after ISSUE-001 was patched in preview. The single
P1 (ISSUE-002) is operator-scoped and does not block release. All
other items are tracking / watch.
