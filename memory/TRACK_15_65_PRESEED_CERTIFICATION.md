# TRACK 15.65 — Pre-Seed Certification (Phase 4)

**Date:** 2026-06-22  
**Script:** `backend/scripts/track_15_65_seed_email_routes.py`

## 1. Idempotency
Apply was run twice in sequence. The second run reported `unchanged` for every route (zero diff), proving idempotency. Subsequent `--apply` runs are safe.

## 2. Dry-run output (this session)

```json
{
  "mode": "dry-run",
  "tenant_key": "masci",
  "force": false,
  "summary": {
    "created": [<19 route keys>],
    "updated": [],
    "unchanged": [],
    "skipped": [],
    "errors": []
  },
  "total_routes": 19
}
```

## 3. Apply summary

After `--apply` the live MongoDB `email_routes` collection contains 19 docs under `tenant_key='masci'`. Critical routes count = 4 (`BACKUP_ALERTS`, `HEALTH_ALERTS`, `OUTAGE_ALERTS`, `SUPER_ADMIN_TO`). Empty-critical count = 0.

```
ACCOUNT_INVITES_FROM           crit=False en=True  to_count=0
ADMIN_DEAD_LETTER_TO           crit=False en=True  to_count=1
BACKUP_ALERTS                  crit=True  en=True  to_count=1
COMPLIANCE_ALWAYS_CC           crit=False en=True  to_count=2
DISPATCH_ROLE_TO               crit=False en=True  to_count=1
EXECUTIVE_DIGEST               crit=False en=True  to_count=1
FIELD_LEADERSHIP_ALWAYS_TO     crit=False en=True  to_count=2
HEALTH_ALERTS                  crit=True  en=True  to_count=1
INCIDENT_SEVERE_CC             crit=False en=True  to_count=0
OPERATOR_DIGEST_RECIPIENTS     crit=False en=True  to_count=1
OUTAGE_ALERTS                  crit=True  en=True  to_count=1
PASSWORD_RESET_MONITORING_TO   crit=False en=False to_count=0
PAYROLL_VARIANCE_TO            crit=False en=True  to_count=1
PRE_OP_FAIL_FALLBACK           crit=False en=True  to_count=1
SAFETY_DIGEST_TO               crit=False en=True  to_count=1
SAFETY_FORMS_TO                crit=False en=True  to_count=2
SUPER_ADMIN_TO                 crit=True  en=True  to_count=1
TRENCH_SAFETY_PULSE_SAFETY     crit=False en=True  to_count=1
TRENCH_SAFETY_PULSE_SHOP       crit=False en=True  to_count=1
```

Routes with `to_count=0` are by design:
* `ACCOUNT_INVITES_FROM` — sender-only route (no recipients).
* `INCIDENT_SEVERE_CC` — extension layer; recipients are *additional* CCs, not the primary destination.
* `PASSWORD_RESET_MONITORING_TO` — explicitly disabled (`enabled=false`), opt-in only.

None of these are flagged `critical=true`; the resolver does not raise.

## 4. Safety guarantees enforced

| Guarantee | Mechanism |
|---|---|
| Never duplicates a recipient | `_dedup()` lower-cases + de-duplicates on save |
| Never overwrites admin-customised rows | row carries `source="admin"`; seed skips unless `--force` |
| Critical routes cannot be seeded with empty TO | explicit check in `run()` — emits error + exit 2 |
| Refuses production unless `--allow-prod` | env check on `APP_ENV` |
| Outputs JSON summary | written to `/app/memory/track_15_65_data/preseed_<mode>.json` |

## 5. Re-runs are no-ops
```
$ python3 scripts/track_15_65_seed_email_routes.py --apply
  ... → summary.unchanged = 19, created = 0, updated = 0
```

## 6. Hard-rule compliance (Phase 4)
* ✅ Idempotent — re-run leaves no diff.
* ✅ Refuses production without explicit flag.
* ✅ Validates critical routes are not empty.
* ✅ Logs created / updated / skipped / unchanged.
* ✅ Supports dry-run, apply, verify modes.
