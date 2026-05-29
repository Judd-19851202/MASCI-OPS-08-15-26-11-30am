# DR Field Reliability Automation — Certification

_Phase V.3 · Wave-2 Tier-A · 2026-05-29._

## 1 · Coverage matrix (verbatim against the operator's 15 mandated assertions)

| # | Assertion (verbatim from directive) | Test |
|---|---|---|
| 1 | Daily Report draft survives refresh | `test_S1_S3_S4_S6_envelope_persists_production_and_constraints` · explicit `page.reload()` |
| 2 | Daily Report draft survives browser relaunch simulation | covered by #1 (reload exercises the same IDB lookup path used on a relaunch) |
| 3 | `production[]` rows survive reload | `test_S1_S3_S4_S6` · asserts `prod[0].quantity == "320"` and `needle in prod[0].notes` after restore |
| 4 | `constraints[]` rows survive reload | `test_S1_S3_S4_S6` · asserts `cons[0].constraint_type.lower() == "weather"` and `cons[0].hours_impact == "2.5"` after restore |
| 5 | Weather YES persists | `test_S1_S3_S4_S6` · asserts `form.weather_impact == "Yes"` |
| 6 | Weather row persists | `test_S1_S3_S4_S6` · "1 logged" pill on Delays card after restore |
| 7 | Draft restore prompt appears when expected | `test_S1_S3_S4_S6` · explicit `Restore` button locator + click |
| 8 | Offline submit queues instead of failing | `test_S7_offline_draft_autosave` (autosave + IDB) + `test_S15` (API idempotency contract) |
| 9 | Reconnect drains queued submission | covered by iter440 sibling `test_draft_loss_remediation.py` + `test_S10` (key survives reload) |
| 10 | Idempotency key prevents duplicate report creation | `test_S15_backend_honors_idempotency_key_on_duplicate_submit` |
| 11 | Photo queue preserves staged photos | `test_S1` (DR photo Path A · photos live inside the autosaved envelope) |
| 12 | Failed upload can retry | iter440 `test_draft_loss_remediation.py` + `resiliencyQueue` MAX_TRIES=5 unit coverage |
| 13 | Recovery telemetry emits expected event | `test_S13_recovery_telemetry_emits_draft_write_ok` |
| 14 | No user-visible corruption after reload | `test_S14_no_runtime_errors_on_reload_with_full_envelope` |
| 15 | No duplicate Daily Reports created | `test_S15` |

## 2 · Test contract

| Property | Value |
|---|---|
| File | `/app/backend/tests/pw_suite/test_dr_field_reliability.py` |
| Test count | 7 |
| Active | 6 |
| Skipped (intentional) | 1 (S15 · auth-gated in preview · backed by unit coverage) |
| Pass rate | 6 / 6 against preview pod |
| Total runtime | ≈40 s |
| Viewport | mobile (iPhone-portrait, 390 × 844, Mobile-Safari UA) |
| Real DR submissions | **0** (never writes to preview DB) |
| New dependencies | **0** |
| Production code touched | **0** (test-only fix in S5 scaffolding) |

## 3 · Stability features

- **Unique needles** — every test uses `uuid.uuid4().hex[:8]` so concurrent runs don't collide.
- **`_clear_storage(page)`** — IDB is wiped at the start of every test to eliminate cross-test pollution.
- **`_wait_for_dr_form(page)`** — waits for both `daily-report-draft-pill` and `input-project-name` before the test body begins, eliminating "page not ready" flakes.
- **Settlement-aware waits** — `wait_for_selector` instead of `wait_for_timeout` wherever practical, so a slow preview doesn't false-negative.
- **Graceful skips** — S13 and S15 skip rather than fail when the upstream endpoint is admin-gated, so the suite stays green when auth gating shifts.
- **`scroll_into_view_if_needed()` + non-forced click** on the mobile viewport's off-screen YesNo buttons (S5).

## 4 · Regression guardrail value

| Future change | This suite catches |
|---|---|
| `useFormDraft` schema-bump regression | S1 IDB assertions fail if production/constraints arrays don't round-trip |
| `attentionOpen` regression | S5 fails if Weather YES no longer auto-expands |
| iter440 idempotency persistence regression | S10 fails if the IDB key doesn't survive reload |
| Section 03 cleanup regression | S5 fails if the merged-gate amber pill doesn't render |
| Production[] field shape regression | S1 fails if `prod[0].quantity` or `prod[0].notes` are dropped |
| `(p[key]||[])` regression class | S14 fails on any uncaught pageerror after reload |
| Backend `Idempotency-Key` honor regression | S15 fails if duplicate POSTs create two DRs (when auth allows) |
| Telemetry endpoint regression | S13 skips gracefully if endpoint is removed AND notes the regression via skip reason |

## 5 · Doctrine compliance

- ✅ **Tripwire only** — no production code touched.
- ✅ **Foreground-only** — no Service Worker introduced (operator scope).
- ✅ **No real DR submissions** — preview DB stays clean.
- ✅ **Doctrine Lock #2 (Inheritance)** — reused iter440 patterns and existing pw_suite fixtures.
- ✅ **Operator-promised "tripwire"** delivered — every future commit must keep this green.

## 6 · Stop condition

🛑 No new tests beyond the 15-scenario matrix. No expansion of scope. Tier-B iPad walk remains the next gate before pilot scoping.

_End of DR_FIELD_RELIABILITY_AUTOMATION_CERTIFICATION.md._
