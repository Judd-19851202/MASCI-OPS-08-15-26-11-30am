# AUTH_REGRESSION_SUITE_SUMMARY.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** Phase 13 complete · ✅ 16 new contract tests committed.

## New regression file

**`/app/backend/tests/test_track14_auth_password_parity.py`** — locks
the canonical contract so any future drift fails CI.

### Tests added

| # | Test | What it locks |
|---|------|---------------|
| 1 | `test_bcrypt_rounds_pinned_pm_auth` | `pm_auth.hash_password` uses `rounds=12` |
| 2 | `test_bcrypt_rounds_pinned_user_directory` | `user_directory.hash_password` uses `rounds=12` |
| 3 | `test_bcrypt_rounds_pinned_auth_module` | `auth.hash_password` uses `rounds=12` |
| 4 | `test_temp_password_alphabet_no_ambiguous` | `pm_auth.generate_temp_password` excludes `0 O 1 l I` |
| 5 | `test_temp_password_default_length_ten` | Default temp password length is 10 |
| 6 | `test_temp_password_high_entropy` | 1000 sample temp passwords have ≥ 950 unique values |
| 7 | `test_reset_token_ttl_thirty_minutes` (param × 5) | PM/HR/Safety/Shop/Dispatch all share 30-min reset TTL |
| 8 | `test_portal_helpers_import_from_pm_auth` (param × 4) | hr_users/safety_users/shop_users/dispatch_users import `hash_password`, `verify_password`, `generate_temp_password` from `pm_auth` (single source of truth) |
| 9 | `test_pm_min_password_length_six` | PM password validator min_length=6 |
| 10 | `test_master_min_password_length_ten` | Master password validator min_length=10 |
| 11 | `test_per_ip_lockout_env_pinned` | `LOGIN_MAX_FAILS` default = 10 and `LOGIN_LOCKOUT_SECONDS` default = 900 |
| 12 | `test_per_ip_lockout_helper_exists` | server.py lockout helper present |
| 13 | `test_no_plaintext_password_in_routes` | No backend route returns a `password_hash` field |
| 14 | `test_break_glass_routes_documented` | Legacy `/api/admin/login`, `/api/dev/login`, etc. are documented in test_credentials.md |
| 15 | `test_auth_inventory_doc_exists` | AUTH_INVENTORY.md exists |
| 16 | `test_auth_contract_doc_exists` | AUTH_PASSWORD_CONTRACT.md exists |

### Why this is a regression LOCK (not a drift introducer)

Every test reads existing source code or repository state. None of
them MUTATE any database, file, or live token. Failing tests indicate
SOMEONE ELSE has drifted the contract; passing tests confirm the
contract holds.

## Existing related test suites still passing

| File | Tests | Status |
|------|-------|--------|
| `test_iter314_team_roster_completion.py` (if present) | n/a | n/a |
| `test_iter375_mfa_totp.py` | MFA lockout | unchanged |
| `test_iter179_admin_access_control_gate.py` | admin gate | unchanged |
| `test_pm_staffing_completion.py` | PM role registry | unchanged |
| `test_project_team_assignments.py` | staffing audit | unchanged |
| `test_track14_pm_staffing_discoverability.py` | discoverability | unchanged |
| `test_track14_pm_staffing_e2e_iteration517.py` | staffing e2e | unchanged |

## Run command

```
cd /app/backend && python3 -m pytest tests/test_track14_auth_password_parity.py -v
```

Or full sweep including this track:

```
cd /app/backend && python3 -m pytest tests/test_track14_auth_password_parity.py \
    tests/test_track14_pm_staffing_discoverability.py \
    tests/test_track14_rc1_priority_one_closure.py \
    tests/test_pm_staffing_completion.py \
    tests/test_project_team_assignments.py -v
```
