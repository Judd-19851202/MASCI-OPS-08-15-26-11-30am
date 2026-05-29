# Reliability Regression Guardrail — Report

_Phase V.3 · Wave-2 Tier-A · 2026-05-29._

> **Operator directive (verbatim):** _"Future commits must not silently break field reliability. Build the tripwire."_

## 1 · The tripwire is live

| Guardrail | Where | Trigger |
|---|---|---|
| Backend unit suite (89 / 89 ODR · daily-reports · idempotency contracts) | `backend/tests/odr/` + `backend/tests/test_daily_reports.py` | every commit (CI / pre-deploy) |
| iter440 draft-loss regression suite | `backend/tests/pw_suite/test_draft_loss_regression_iter440.py` + `test_draft_loss_remediation.py` + `test_draft_telemetry_endpoint.py` | every commit |
| **NEW · DR Field Reliability suite** | `backend/tests/pw_suite/test_dr_field_reliability.py` | every commit |
| Authority Mismatch Probe baseline (Trust-1) | `backend/tests/pw_suite/test_governance_authority_mismatch_probe.py` | every commit |
| Trust-1 calmness/posture probes | `backend/tests/pw_suite/test_trust1_*.py` | every commit |
| Visual doctrine baseline | `backend/tests/pw_suite/test_visual_doctrine_baseline.py` | every commit |

## 2 · What each tripwire protects

| Surface | Tripwire | If silently broken, this would catch |
|---|---|---|
| Autosave landing | DR `test_S1` IDB assertions | A future hook refactor that drops `production[]` or `constraints[]` from the persisted form |
| Draft restore | DR `test_S1` Restore-button + status-pill assertion | A future change that surfaces but doesn't apply the recovered envelope |
| iPad-friendly auto-expand | DR `test_S5` | A future CollapseCard refactor that breaks `attentionOpen` |
| Amber required pill | DR `test_S5` text scan | A future Section 03 wording change that drops "Add a row with cause = Weather (required)" |
| Idempotency persistence | DR `test_S10` | A future idempotency-key store refactor that breaks reload survival |
| Telemetry firing | DR `test_S13` | A future change that silently disables `emitDraftEvent` |
| Runtime errors | DR `test_S14` | A future schema bump that crashes RepeatBlock or any consumer of the form payload |
| Backend dedup | DR `test_S15` (when auth allows) + unit tests | A future backend refactor that drops `Idempotency-Key` header parsing |
| iter440 idempotency persistence | iter441 `test_idempotency_key_persisted_in_idb_after_autosave_landing` | The original P0 incident regression |
| Telemetry endpoint | `test_draft_telemetry_endpoint.py` | A future change that breaks `/api/draft-telemetry` ingestion |
| Sibling forms (Incident, Inspection, HR payroll, DLS) | iter441 sibling smoke | A future `useFormDraft` hook signature break |

## 3 · Doctrine: what the guardrail is NOT

- ❌ NOT a Tier-B field-walk replacement. The 15-scenario iPad checklist (`FIELD_RELIABILITY_TEST_MATRIX.md §4`) MUST still be walked by a real superintendent on a real iPad in a realistic project before pilot scoping is authorized.
- ❌ NOT a Service Worker replacement. Operator scope deferred SW uplift. If Tier-B surfaces real-world failure modes that need a SW, the guardrail will need to evolve.
- ❌ NOT a load test. Concurrent-foreman traffic is exercised at the backend layer by the existing unit suite, not by this Playwright file.

## 4 · Run cadence

| Cadence | Suites |
|---|---|
| Pre-PR / pre-merge | iter440 + Wave-2 DR Field Reliability + ODR backend |
| Pre-deploy | Everything above + Authority Mismatch + Trust-1 + Visual Doctrine |
| Operator-on-demand | Full `backend/tests/pw_suite/` + `backend/tests/odr/` |
| Tier-B (iPad walk) | Manual · operator-led · before pilot scoping |

## 5 · Maintenance contract

| Event | Required follow-up |
|---|---|
| New field added to DR (top-level OR per-row) | If field is operationally critical, add an explicit IDB assertion to `test_S1`. Otherwise nothing (engine is per-field-coupling-free). |
| New CollapseCard added | If the card has `attentionOpen` driven by Section-03-style YES gates, mirror a S5-style assertion. |
| New chip added to constraint UI | No test change required (chip selectors are generic). |
| `useFormDraft` hook signature change | iter441 sibling smoke covers backward-compat. Run the suite. |
| `enqueueUpload` / `resiliencyQueue` change | Run iter440 + Wave-2 DR suite. |
| `/api/draft-telemetry` endpoint change | S13 will skip gracefully OR fail loud — both are signal. |
| `Idempotency-Key` header semantics change | Update `test_daily_reports.py` unit + S15 if auth surface changes. |

## 6 · Doctrine compliance

- ✅ **Reliability protection only** — operator-mandated scope honored.
- ✅ **No production code changes** in this wave (besides the new test file).
- ✅ **No new dependencies.**
- ✅ **No Service Worker · no Background Sync.**
- ✅ **89 / 89 ODR backend tests + 6 / 6 active Wave-2 reliability tests + ESLint clean.**

## 7 · Stop condition

🛑 **HALTED at end of Tier-A authoring as directed.**

The tripwire is built. Future commits that silently break field reliability will fail this suite before they merge. Pilot scoping awaits operator review of the test results AND the Tier-B iPad walk.

---

_End of RELIABILITY_REGRESSION_GUARDRAIL_REPORT.md._
