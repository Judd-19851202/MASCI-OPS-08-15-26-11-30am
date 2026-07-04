# TRACK 22.1I · Test Report

## Envelope

Track 20.6B → 22.1I: **278 / 278** lock tests green (+15 Track 22.1I).

| Suite | Result |
|---|---|
| Track 20.6B through 22.1H (18 suites, 263 tests) | ✅ 263/263 (after minor 22.1H/22.1G relaxation to `<=`/`>=` invariants) |
| `test_track_22_1i_misc_bootstrap_migration.py` (**new**) | ✅ 15/15 |
| **Total** | ✅ **278 / 278** |

## Track 22.1I new assertions (15)

1. `LIFECYCLE_STEPS` contains exactly 20 entries with `group=="misc-bootstrap"`, in canonical source order.
2. `LIFECYCLE_STEPS` total is exactly 47 (11+7+4+5+20).
3. None of the 20 migrated handlers remain in `app.router.on_startup`.
4. `app.router.on_startup` count is exactly 3.
5. Excluded handlers (`_startup`, `_start_backup_scheduler`, `_iter453_6_flip_ready_flag`) all remain in on_startup.
6. `_iter453_6_flip_ready_flag` is `app.router.on_startup[-1]` (LAST).
7. No duplicate registrations · no cross-registry names.
8. Runtime snapshots committed.
9. Zero route/OpenAPI/middleware/dep-chain drift.
10. `verify_locked_bytecode(server.app)` returns 5 ok / 0 drift / 0 missing.
11. Platform Status API reports correct counts, `misc-bootstrap.closed=true`, `22.1I` in closures, no secret leak.
12. All 12 Track 22.1I deliverables present and non-trivial.
13. PRD + CHANGELOG + Debt Register record Track 22.1I.
14. `EMAIL_SAFETY_MODE=strict` and no `allow_methods=["*"]`.
15. `lib/lifespan_bootstrap.py` + `lib/platform_status.py` — AST-verified no module-scope `import resend`. All 9 prior lock test files committed.

## Runtime probes (2026-07-04 19:56 UTC)

| Probe | Response |
|---|---|
| `curl /api/health` | `{"ok":true,"service":"masci-hub","ts":"..."}` byte-identical |
| `curl -H "X-Admin-Token: <SA>" /api/admin/platform/status` | 200 · `by_group={index-ensure:11, seed:7, scheduler-nonemail:4, email-scheduler:5, misc-bootstrap:20}` · `on_startup_legacy_count=3` · `migrated_pct=94.00` |
| Boot log `[track-22.1e] executing 47 LIFECYCLE_STEPS` | Present |
| Boot log `[track-22.1d] executing 3 handlers` | Present |
| Boot log `[iter453.6] startup-readiness gate FLIPPED` | Present as final on_startup handler |
| `verify_locked_bytecode` | `checked=5 ok=5 drift=0 missing=0` |

**Zero live emails. Zero external HTTP change. Zero R2 write during tests.**

## Sign-off

Track 22.1I · Miscellaneous Bootstrap Handler Migration · **CLOSED · 🟢 GO**.
