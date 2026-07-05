# Phase 1 · Zero-Drift Matrix

**Date:** 2026-02-05
**Attestation:** Phase 1 is behaviour-identical to the pre-refactor baseline. Every zero-drift claim below is machine-verifiable.

## Backend

| Layer | Baseline (pre-Phase-1) | Post-Phase-1 | Δ | Verified by |
|---|---:|---:|---:|---|
| Route count | 1,441 | 1,441 | 0 | `test_route_and_openapi_parity` (across 22.3, 22.4A locks) |
| Method count | 1,445 | 1,445 | 0 | same |
| OpenAPI paths | 1,264 | 1,264 | 0 | same |
| Middleware count | 7 | 7 | 0 | Runtime probe |
| `on_startup` legacy handlers | 0 | 0 | 0 | `test_lifecycle_complete_unchanged` |
| `on_shutdown` legacy handlers | 0 | 0 | 0 | same |
| `startup_migration_pct` | 100.0 | 100.0 | 0 | `platform_status.lifecycle.migration_progress` |
| `shutdown_migration_pct` | 100.0 | 100.0 | 0 | same |
| `lifecycle_complete` | true | true | 0 | same |
| Bytecode fingerprints checked | 9 | 9 | 0 | `verify_locked_bytecode` |
| Bytecode drift count | 0 | 0 | 0 | same |
| `EMAIL_SAFETY_MODE` | strict | strict | 0 | `platform_status.email_safety` |
| `resend_sdk_patched` | true | true | 0 | same |
| `live_emails_possible` | false | false | 0 | same |
| Pydantic v1 `class Config` in BaseModels | 1 | **0** | −1 | Track 22.4A AST guardrail |
| Pydantic v1 `regex=` in FastAPI params | 0 | 0 | 0 | Track 22.3 AST guardrail |
| Runtime `PydanticDeprecatedSince20` from passkeys | 1/import | **0/import** | −1 | Track 22.4A runtime warning capture |

## Frontend

| Layer | Baseline (pre-Phase-1) | Post-Phase-1 | Δ | Verified by |
|---|---:|---:|---:|---|
| `App.js` md5 | `d84cea05c1f64bd2ae82823d7f6aadcc` | `d84cea05c1f64bd2ae82823d7f6aadcc` | 0 | `md5sum` |
| `App.js` line count | 1,283 | 1,283 | 0 | `wc -l` |
| Route count in App.js | 385 | 385 | 0 | `extract_app_js_inventory.py` |
| Guard count | 11 | 11 | 0 | same |
| Provider count | 1 | 1 | 0 | same |
| Chrome component count | 15 | 15 | 0 | same |
| Duplicate route paths | 0 | 0 | 0 | same |
| Confirmed-dead imports | 0 | 0 | 0 | same |

## Cross-cutting

| Layer | Baseline | Post-Phase-1 | Δ |
|---|---|---|---:|
| `.env` files | 2 (backend, frontend) | 2 | 0 |
| CORS allow_origin_regex | Starlette regex (preserved) | Starlette regex (preserved) | 0 |
| Auth surface | JWT + portal tokens | JWT + portal tokens | 0 |
| Permission surface | 11 guards / 385 routes | 11 guards / 385 routes | 0 |
| Database schema | unchanged | unchanged | 0 |
| Track 22.* lock envelope | 254/254 pass | **254/254 pass** | 0 |

## Session-scope code changes (complete list)
| File | Diff | Reason |
|---|---|---|
| `backend/routes/passkeys.py` | +2 −3 (`class Config` → `model_config = ConfigDict(extra="allow")`) | Track 22.4A · Pydantic v2 completion |

## Attestation
🟢 **Zero drift confirmed.** Every measurable metric is unchanged from baseline, EXCEPT the two intentional reductions (Pydantic v1 `class Config`: −1; runtime PydanticDeprecatedSince20 warning from passkeys: −1). Both reductions are semantically-equivalent modernizations, not behavior changes.
