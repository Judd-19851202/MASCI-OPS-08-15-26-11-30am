# Safe Route Extraction Certification — Phase IV-BETA.5A-P4B

*iter437 · 2026-02-27*
*Status: 🟢 ONE EXTRACTION SHIPPED · 9/9 regression assertions green · zero behavioural change*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Begin **lowest-risk** route extraction from `server.py`. Goal: reduce
long-term `server.py` operational risk gradually WITHOUT
destabilisation. Individually reversible · regression-locked · no
behavioural changes · no API contract changes · no startup-order
changes.

## II. What was extracted (🟢)

| Endpoint | Was | Now | Status |
|---|---|---|---|
| `GET /api/guidance/sections` | `server.py` line 528 | `routes/guidance_routes.py::guidance_sections` | 🟢 200 contract preserved |
| `GET /api/guidance/articles` | `server.py` line 537 | `routes/guidance_routes.py::guidance_articles` | 🟢 200 + filter preserved |
| `GET /api/guidance/articles/{id}` | `server.py` line 555 | `routes/guidance_routes.py::guidance_article` | 🟢 200 / 404 preserved |
| `GET /api/guidance/tips` | `server.py` line 576 | `routes/guidance_routes.py::guidance_tips` | 🟢 200 + empty-key handling preserved |
| `GET /api/guidance/search` | `server.py` line 593 | `routes/guidance_routes.py::guidance_search` | 🟢 200 + zero-results logging preserved |

**Total extracted:** 5 public read-only endpoints (~115 LOC). Behavioural
parity confirmed via `tests/pw_suite/test_guidance_routes_extraction.py`
(9 assertions · all green).

## III. How extraction was kept SAFE (🟢)

1. **Dependency-injection pattern** — mirrors the existing
   `build_training_center_router(db, require_admin, _guidance_caller_scopes)`
   pattern. The helper `_guidance_caller_scopes` STAYS in `server.py`
   (rich dependencies on internal token validators); it is passed into
   the new router as a parameter.
2. **No DB writes added** — the only DB write
   (`guidance_search_misses.insert_one`) is preserved verbatim from the
   original.
3. **No API contract change** — JSON shape is byte-for-byte equivalent.
   The new regression test asserts every field on every endpoint.
4. **Startup order preserved** — the new `include_router` call is
   placed **immediately after** `build_training_center_router` (which
   already takes the same helper), so import order is identical.
5. **No middleware added** — the new router has no `Depends` chain
   beyond the helper.

## IV. Reversibility (🟢)

To revert the extraction:

1. Delete `routes/guidance_routes.py`.
2. Remove the two new lines in `server.py` (`from routes.guidance_routes
   import build_guidance_router` + `app.include_router(build_guidance_router(db, _guidance_caller_scopes))`).
3. Re-add the original endpoint blocks (preserved in git history).

Estimated revert time: < 5 minutes.

## V. Regression contract (🟢)

`test_guidance_routes_extraction.py` (9 assertions):

| Test | Asserts |
|---|---|
| `test_guidance_sections_shape` | 200 + `sections` + `scopes` keys + sorted scopes |
| `test_guidance_articles_shape` | 200 + `articles` + `count` + canonical 5 fields per article |
| `test_guidance_articles_filter_by_section` | `?section=` filter preserves the contract |
| `test_guidance_article_unknown_returns_404` | 404 on missing article id |
| `test_guidance_tips_empty_form_key` | Exact response `{"form_key": "", "tips": []}` |
| `test_guidance_tips_with_form_key` | 200 + `form_key` + `tips` + `count` for a real form key |
| `test_guidance_search_shape` | 200 + `query` echoed + `results` ≤ limit |
| `test_guidance_search_zero_results_logs_without_exception` | Fire-and-forget miss-log path exercised |
| `test_guidance_search_limit_bounds` | `limit` clamped to `[1, 100]` |

## VI. server.py impact (🟢)

| Metric | Pre-P4B | Post-P4B | Δ |
|---|---|---|---|
| Line count | 11,399 | 11,315 | **−84** |
| `@api_router.get` declarations (in-file) | ~340 | ~335 | **−5** |
| External `include_router` calls | 25+ | 26+ | **+1** |

Net: `server.py` is **84 LOC lighter** and one cleaner domain has
moved into its own file.

## VII. What was NOT touched (🟢 honoured)

Per directive — NOT extracted this phase:

- ❌ Auth (login / refresh / multi-login)
- ❌ Escalation logic
- ❌ Notifications
- ❌ Safety business logic
- ❌ Dispatch business logic
- ❌ Session handling
- ❌ Startup logic / scheduler arming
- ❌ Middleware
- ❌ Websocket logic
- ❌ Upload pipelines
- ❌ Admin guidance-coverage endpoints (different domain · admin-strict · stays in server.py for now)
- ❌ Helper functions (`_guidance_caller_scopes`, `_is_valid_*_token`)

## VIII. Doctrine reaffirmed

- ✅ One lowest-risk domain extracted · no surprise behaviour
- ✅ 9/9 regression assertions green
- ✅ Fully reversible · < 5 minutes
- ✅ Startup order unchanged
- ✅ DB I/O contract preserved
- ✅ RBAC contract preserved
- ✅ Preview only · NO production deploy
