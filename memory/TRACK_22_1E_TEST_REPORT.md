# TRACK 22.1E · Test Report

## Suites executed (Track 20.6B → 22.1E envelope)

| Suite | Result |
|---|---|
| `test_track_20_6b_test_hardening.py` | ✅ 6/6 |
| `test_track_20_7_universal_photo_capture.py` | ✅ 26/26 |
| `test_track_20_8_deployment_certification.py` | ✅ 12/12 |
| `test_track_20_9_cleanup.py` | ✅ 8/8 |
| `test_track_21_0_platform_census.py` | ✅ 28/28 |
| `test_track_21_1_remediation.py` | ✅ 8/8 |
| `test_track_21_2e_email_safety.py` | ✅ 11/11 |
| `test_track_21_2e_1_canonicalization.py` | ✅ 6/6 |
| `test_track_21_2e1_payload_canonicalization.py` | ✅ 15/15 |
| `test_track_21_3_remaining_debt_remediation.py` | ✅ 12/12 |
| `test_track_22_0_platform_excellence.py` | ✅ 13/13 |
| `test_track_22_1_server_modularization.py` | ✅ 16/16 |
| `test_track_22_1b_email_dispatch.py` | ✅ 17/17 |
| `test_track_22_1c_scheduler_bootstrap.py` | ✅ 16/16 |
| `test_track_22_1d_lifespan_migration.py` | ✅ 12/12 |
| `test_track_22_1e_index_handler_migration.py` (**new**) | ✅ 11/11 |
| **Total** | ✅ **218 / 218** |

## Track 22.1E new assertions (11)

1. `LIFECYCLE_STEPS` contains exactly 11 entries with `group == "index-ensure"`, in the canonical source order.
2. None of the 11 migrated handlers remain in `app.router.on_startup` (no duplicate execution).
3. `app.router.on_startup` handler count reduced from 51 → 40.
4. Runtime snapshots committed: `RUNTIME_ENUMERATION_before/after.json`, `STARTUP_ORDER_before/after.json`, `INDEX_HANDLER_INVENTORY_before.json` (all present, non-trivial size).
5. Route parity: `route_count`, `route_methods_total`, `openapi_path_count`, `middleware`, `shutdown_handlers`, `exception_handlers` all byte-equal before/after.
6. Per-route `endpoint_qualname` and `dependency_chain` byte-equal for all 1,440 routes.
7. `verify_locked_bytecode(server.app)` returns 5 ok / 0 drift / 0 missing.
8. All 9 Track 22.1E deliverables present and non-empty.
9. PRD + CHANGELOG + Debt Register record Track 22.1E.
10. Email safety layers preserved (SDK gate string, `EMAIL_SAFETY_MODE=strict`, CORS explicit allow-list).
11. `lib/lifespan_bootstrap.py` still AST-verified to NOT `import resend`; prior lock-test files (22.0, 22.1, 22.1B, 22.1C, 22.1D) still committed.

## Runtime probes

| Probe | Response |
|---|---|
| `curl /api/health` | `{"ok":true,"service":"masci-hub","ts":"..."}` — byte-identical |
| Boot log `[track-22.1e] lifespan.startup: executing 11 LIFECYCLE_STEPS` | Present, count = 11 |
| Boot log `[track-22.1e] lifespan.startup: LIFECYCLE_STEPS complete` | Present after the 11th step |
| Boot log `[track-22.1d] lifespan.startup: complete` | Present after the 40th on_startup handler (unchanged) |
| Boot log `[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched.` | Present (30+ activations) |
| `verify_locked_bytecode(server.app)` | `{"checked":5,"ok":[5 names],"drift":[],"missing":[]}` |

**No HTTP POST to any workflow endpoint. No email dispatched. No R2 write.**

## Duplicate / missing execution proof

- **No duplicate execution** — each of the 11 migrated handlers appears in `LIFECYCLE_STEPS` exactly once and is NOT present in `app.router.on_startup` (asserted by `test_on_startup_no_longer_contains_migrated_handlers`).
- **No missing execution** — `LIFECYCLE_STEPS complete` fires with 11 handlers, then `lifespan.startup: complete` fires with 40 handlers, then readiness gate flips. Total callables executed per boot = 51 (unchanged).

## Deprecation-warning delta

| State | `@app.on_event("startup")` count |
|---|---|
| Track 22.1D close | 51 |
| Track 22.1E close | **40** (−11) |

`pytest.ini` `filterwarnings` unchanged — deprecation warnings remain visible per the constitutional mandate that migration, not silencing, retires warnings.

## Sign-off

Track 22.1E · Index-Ensure Handler Migration · **CLOSED · 🟢 GO**.
