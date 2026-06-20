# TRACK 15.59 — Live Production Post-Deployment Automated Verification — PLAN

**Status:** EXECUTED · PASS
**Target:** `https://mascidocs.com` (PRODUCTION · `APP_ENV=production` · `DB_NAME=masci_safety`)
**Executed:** 2026-06-20 12:55 UTC
**Runner:** `/app/tests/post_deploy/track_15_59_live_prod_verify.py`
**Report (JSON):** `/app/test_reports/track_15_59_live_prod_verify.json`
**Screenshots:** `/app/memory/track_15_59_screenshots/` (27 PNGs)
**Cleanup tag:** `POST_DEPLOY_TEST_TRACK_15_59_DELETE`

---

## Purpose

Independently re-verify, from outside the production network, that:

1. The deployed front-door (`mascidocs.com`) is reachable, the SPA loads, and the API answers.
2. Every advertised public route resolves to its login surface.
3. Every protected portal URL refuses an unauthenticated visitor (redirects to login).
4. The production-environment shape matches the deploy contract (`APP_ENV=production` / `DB_NAME=masci_safety` / health endpoint reports ok).
5. The super-admin can authenticate against the live production database (via `POST /api/auth/multi-login`).
6. All 8 portal tokens (admin · pm · shop · hr · safety · dispatch · field_leadership · fl) are minted by the directory layer.
7. The SPA accepts a UI login and lands the user on `/admin`.
8. Authenticated portal renders work (admin, pm, hr, safety-portal).
9. Cross-portal API reads succeed for the canonical safety read-set (`/api/meetings`, `/api/inspections`, `/api/incidents`, `/api/daily-reports`, `/api/equipment-inspections`, `/api/jhas`).
10. A real write workflow on production (create Safety Meeting) succeeds and persists a `doc_id` (`MTG-YYYY-NNNNN`).
11. The PDF render pipeline produces a non-trivial PDF (size_bytes > 1 MB) via `POST /api/email-report` for the created meeting.
12. The cleanup contract holds: the created record is deleted, the GET returns 404, and a sweep of `/api/meetings` shows ZERO records still bearing the cleanup tag.

## Test Boundary — what this run is and is not

- ✅ **End-to-end, real network, real DB.** Hits the production CDN edge, the production FastAPI, the production MongoDB Atlas database `masci_safety`.
- ✅ **Single tagged write.** Exactly one synthetic Safety Meeting is created, tagged `POST_DEPLOY_TEST_TRACK_15_59_DELETE` in `project_name`, `location`, `topic`, `references_cited`, and `action_items` so any leftover is trivially greppable.
- ✅ **Authorized email side-effect.** The PDF proof step emits exactly one email to `safety@mascigc.com` (pre-authorized) using `POST /api/email-report`.
- ❌ **Does not run destructive admin actions.** No backup mutation, no restore drill, no user-directory write, no equipment master mutation.
- ❌ **Does not delete pre-existing production data.** The DELETE only targets the record id minted by Phase 10.
- ❌ **Does not exercise the legacy admin-password break-glass (`/api/admin/login`).** Stick to the canonical multi-login path which is what real humans use.

## Authoring decisions

- Phase numbering and naming match the 15.59 prompt one-for-one.
- Both `X-Admin-Token` and `X-Safety-Token` are sent on the safety read gate because the directory-minted admin token is NOT accepted by the legacy `is_valid_admin_token()` predicate inside `routes/safety_portal/_deps.py::make_require_safety_admin_or_pm`; the safety token from the same `multi_login` call is. This is an observed, non-blocking quirk — documented for the operator. The DELETE/admin-only gate accepted the directory admin token without issue.
- Browser automation uses headless Chromium via Playwright 1.59 + the bundled chromium-headless-shell 1217. Viewport 1440×900 — wide enough to render the desktop layout shipped to production.
- Screenshots are full-viewport (NOT full page) to keep evidence size proportional and reviewable.
- The token-inject step in Phase 8 mirrors how `/sign-in` populates localStorage. This is a deliberate shortcut — Phase 7 already proves UI sign-in actually works; Phase 8 just needs an authenticated visit to each portal.

## Exit criterion

The run is `PASS` iff every phase reports `status: pass`, the `left_over_artefacts` array is empty, and the GET-after-DELETE returns 404. Anything else flips the script's exit code to 1 and is reported as a production-blocking finding in the EXECUTIVE_SUMMARY.

## Result

```
overall_status: PASS
duration_sec : 56.7
failed_phases: []
screenshots  : 27
left_over_artefacts: 0
```

See `TRACK_15_59_FINAL_CERTIFICATION.md` for the certification grid and
`TRACK_15_59_EXECUTIVE_SUMMARY.md` for the operator-facing summary.
