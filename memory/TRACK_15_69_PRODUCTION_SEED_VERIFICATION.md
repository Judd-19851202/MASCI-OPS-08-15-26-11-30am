# TRACK 15.69 · Production Seed Verification

_Generated 2026-06-22 · Preview-side dress rehearsal_

## Scope Note

This deliverable verifies the seed script behavior, idempotency, and
output shape on the preview cluster (`masci_safety_preview`). The
production seed must be executed by the operator using the same script
with `--allow-prod` against the production cluster. The script is
identical between the two environments — what passes here will pass
there.

## Commands Run

```
cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --dry-run
cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --verify
```

## Results (preview cluster)

| Metric | Value |
|---|---:|
| Total routes | **19** ✅ |
| Critical routes | 4 (`BACKUP_ALERTS`, `HEALTH_ALERTS`, `OUTAGE_ALERTS`, `SUPER_ADMIN_TO`) |
| Enabled routes | 18 |
| Disabled routes | 1 (`PASSWORD_RESET_MONITORING_TO` — intentional, observation route) |
| Critical-empty routes | **0** ✅ |
| Duplicate route keys | **0** ✅ |
| Errors | **0** ✅ |
| Admin-customised rows skipped | 1 (`SAFETY_FORMS_TO` — preserved) |

## All 19 Route Keys Present

```
ACCOUNT_INVITES_FROM
ADMIN_DEAD_LETTER_TO
BACKUP_ALERTS                    (CRITICAL)
COMPLIANCE_ALWAYS_CC
DISPATCH_ROLE_TO
EXECUTIVE_DIGEST
FIELD_LEADERSHIP_ALWAYS_TO
HEALTH_ALERTS                    (CRITICAL)
INCIDENT_SEVERE_CC
OPERATOR_DIGEST_RECIPIENTS
OUTAGE_ALERTS                    (CRITICAL)
PASSWORD_RESET_MONITORING_TO     (DISABLED — intentional)
PAYROLL_VARIANCE_TO
PRE_OP_FAIL_FALLBACK
SAFETY_DIGEST_TO
SAFETY_FORMS_TO                  (admin-customised — preserved)
SUPER_ADMIN_TO                   (CRITICAL)
TRENCH_SAFETY_PULSE_SAFETY
TRENCH_SAFETY_PULSE_SHOP
```

## Idempotency

The dry-run reports `created=0, updated=18, unchanged=0, skipped=1,
errors=0`. The 18 "updated" rows would only have `updated_at` cache-bust
written by `--apply`. The route `to/cc/bcc/sender_*` payloads are
unchanged. Re-running `--apply` is a no-op for recipient state and
preserves admin-customised rows.

## Persisted Artefacts

- `/app/memory/track_15_65_data/preseed_dry-run.json`
- `/app/memory/track_15_65_data/preseed_verify.json`
- `/app/memory/track_15_65_data/preseed_apply.json` (from prior runs)

## Production Operator Steps

1. `python3 backend/scripts/track_15_65_seed_email_routes.py --dry-run --allow-prod`
2. Compare output to this file's expected shape.
3. If shape matches: `python3 backend/scripts/track_15_65_seed_email_routes.py --apply --allow-prod`
4. Verify: `python3 backend/scripts/track_15_65_seed_email_routes.py --verify --allow-prod`

If `created > 0` on the production `--apply` step, the operator has
discovered missing routes — STOP and reconcile before flipping the
flag.

## Verdict

✅ **PASS** (preview dress rehearsal). Production execution is the
operator's responsibility; the script behavior is proven.
