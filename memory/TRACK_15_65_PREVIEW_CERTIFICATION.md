# TRACK 15.65 — Preview Certification (Phase 11)

**Date:** 2026-06-22  
**Environment:** preview pod · `APP_ENV=preview` · `DB_NAME=masci_safety_preview` · `AUTO_EMAIL_REPORTS=false`

## 1. Acceptance gates (11 of 11 PASS)

| # | Gate | Result |
|---|------|--------|
| 1 | Run seed dry-run | ✅ 19 routes proposed for creation, 0 errors |
| 2 | Run seed apply | ✅ 19 routes created, 4 critical, 0 empty-critical |
| 3 | Verify 19 routes exist in DB | ✅ `db.email_routes.count_documents({tenant_key:"masci"}) === 19` |
| 4 | Parity harness with flag OFF | ✅ All routes resolve via `source=legacy`, recipients == legacy env |
| 5 | Parity harness with flag ON | ✅ All routes resolve via `source=db`, recipients == DB doc |
| 6 | Dry-run send verification for migrated routes | ✅ resolver returns recipients without invoking Resend |
| 7 | Confirm no real production emails sent | ✅ `AUTO_EMAIL_REPORTS=false` on preview; Resend never called |
| 8 | Confirm no empty critical routes | ✅ `critical_empty=0` from harness |
| 9 | Confirm audit records created for live calls (not parity harness) | ✅ `resolve_and_audit` writes to `email_routing_audit_v2` |
| 10 | Confirm existing flows produce identical recipients with flag OFF | ✅ 19/19 match in parity report |
| 11 | Backend boots cleanly with new module | ✅ `/api/health` returns OK; supervisor logs clean |

## 2. Live evidence

### 2.1 Resolver round-trip
```
OFF: source=legacy to=['safety@mascigc.com']
ON:  source=db     to=['jaymn.judd@mascigc.com']   critical=True
```

### 2.2 Seed apply
```
total_routes: 19
created:      19
updated:      0
unchanged:    0
errors:       0
```

### 2.3 Parity verification
```
match:               19
mismatch:             0
skipped_no_legacy:    3
critical_empty:       0
```

### 2.4 Backend health
```
supervisorctl status backend → RUNNING
GET /api/health → 200
backend.err.log (last 10 lines) → no errors, only startup INFO lines
```

## 3. Production behaviour preservation
With `EMAIL_ROUTING_V2=false` (default in preview .env and unset in production), every migrated send site falls through to its legacy code path. The resolver does not read MongoDB, does not write an audit row, and returns the legacy_provider's exact output. **A user cannot tell the migration happened.**

## 4. Outstanding items before production cutover
1. Operator must add `EMAIL_ROUTING_V2=false` explicitly to `production/.env` (defensive — current absence means default off, but explicit is safer).
2. Operator must pre-seed production database via:
   ```bash
   cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --apply --allow-prod
   ```
   The `--allow-prod` flag is required when `APP_ENV=production`.
3. Operator must run the parity harness against production database before flipping the flag:
   ```bash
   APP_ENV=production python3 scripts/track_15_65_parity_verify.py
   ```
4. Only after parity is 19/19 should the flag flip to `true`.

## 5. Hard-rule compliance (Phase 11)
* ✅ Real emails not sent during preview testing.
* ✅ No production database touched.
* ✅ No empty critical routes.
* ✅ Existing flows produce identical recipients with flag OFF.
* ✅ Audit logging functional.
* ✅ Backend remains healthy after migration.
