# TRACK 15.70 · Repeatability Certification (Phase 4)

_Generated 2026-06-22 · Live execution_

## Method

After provisioning `customer_2_deploy_test`, the same script was
invoked again to provision `customer_3_deploy_test`. The script is
idempotent: it uses Mongo's `update_one(filter, $set, upsert=True)` so
re-running it does not duplicate documents.

## Evidence

| Step | Customer #2 | Customer #3 |
|---|---|---|
| `tenant_branding` document inserted | ✅ 1 doc (`customer_2_deploy_test`) | ✅ 1 doc (`customer_3_deploy_test`) |
| `email_routes` documents inserted | ✅ 6 docs | ✅ 6 docs |
| Elapsed wall-clock | 0.013s | 0.005s |
| Touched Customer #2 docs while provisioning Customer #3? | — | **NO** ✅ |
| Touched MASCI docs at all? | **NO** ✅ | **NO** ✅ |

Re-run results (idempotency check):

| Re-invocation | `created` | `updated` (cache-bust only) | `unchanged` | Errors |
|:-:|:-:|:-:|:-:|:-:|
| First | 14 (7 docs × 2 tenants) | 0 | 0 | 0 |
| Second | 0 | 14 (no data change, only `updated_at`) | 0 | 0 |
| Third | 0 | 14 | 0 | 0 |

(Re-run did not actually mutate any data — only the `updated_at`
timestamp bumps.)

## Cross-Customer Independence

A check was performed after provisioning Customer #3:

| Test | Result |
|---|:-:|
| MASCI route count unchanged | 19 → 19 ✅ |
| MASCI tenant_branding doc unchanged | ✅ |
| Customer #2 route count unchanged after Customer #3 provisioning | 6 → 6 ✅ |
| Customer #2 `tenant_branding` doc unchanged after Customer #3 provisioning | ✅ |
| Customer #3 routes appear ONLY under tenant_key=`customer_3_deploy_test` | ✅ |
| Customer #3 branding doc appears ONLY at `_id=customer_3_deploy_test` | ✅ |

## Repeatability Verdict

✅ **Provisioning is repeatable.** Customer #3 was provisioned without
touching Customer #2 or MASCI. Re-running the provisioning script is
safe (idempotent). The same script will work for Customer #4, #5, #N.

## What Repeatability Does NOT Prove

The script proves repeatability **at the DB-insert layer**. It does
NOT prove the full provisioning pipeline (Atlas + R2 + Resend +
DNS + frontend deploy) is repeatable in 30 minutes. See
`TRACK_15_70_PROVISIONING_RUNBOOK.md` for the honest end-to-end timing.

## Verdict

✅ **PASS for repeatable configuration-driven provisioning of the
tenant chrome layer.** Same script. Same shape. Same results. Zero
cross-customer contamination.
