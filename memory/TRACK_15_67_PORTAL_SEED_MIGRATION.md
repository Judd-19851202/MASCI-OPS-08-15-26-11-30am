# TRACK 15.67 · Phase 3 · Portal Seed Migration

_Status: ✅ SHIPPED · 2026-06-22_

## Goal
Remove hard-coded MASCI personnel from the portal seed paths
(`safety_users.py`, `shop_users.py`, `hr_users.py`) so that a
non-MASCI tenant cannot inherit MASCI users at first boot.

## Changes
| File | Before | After |
|---|---|---|
| `backend/safety_users.py` | `INITIAL_SAFETY_USERS = [{"safety@mascigc.com", "Safety Manager"}]` | `INITIAL_SAFETY_USERS = _resolve_initial_safety_users()` — reads `SAFETY_SEED_USERS` env (format `email|Name|Role,…`); MASCI list returned only when env unset AND `tenant_context.is_masci()` is true |
| `backend/shop_users.py` | `INITIAL_SHOP_USERS = [{"shopmanager@mascigc.com", "Shop Manager"}]` | `_resolve_initial_shop_users()` reading `SHOP_SEED_USERS` env, same MASCI-only fallback rule |
| `backend/hr_users.py` | `INITIAL_HR_USERS = [{"hrmanager@mascigc.com", "HR Manager"}]` | `_resolve_initial_hr_users()` reading `HR_SEED_USERS` env, same MASCI-only fallback rule |

The `seed_*_users(db)` boot hooks now log a clean `seed skipped — no
initial users resolved (tenant-safe)` line when the env is unset on a
non-MASCI tenant, rather than silently leaking MASCI personnel.

## Proof
Second-tenant simulation (`scripts/track_15_67_second_tenant_simulation.py`):

```
safety_seed_empty_for_non_masci      PASS  (len=0)
shop_seed_empty_for_non_masci        PASS  (len=0)
hr_seed_empty_for_non_masci          PASS  (len=0)
safety_seed_env_path_no_masci        PASS  (users seeded from env)
```

MASCI parity regression (`scripts/track_15_65_parity_verify.py`):
**19/19 routes match** — no MASCI behaviour change.

## Customer #2 onboarding
```bash
# .env for Customer #2
SAFETY_SEED_USERS="safety@customer2.com|Customer #2 Safety|Safety Manager"
SHOP_SEED_USERS="shop@customer2.com|Customer #2 Shop|Shop Manager"
HR_SEED_USERS="hr@customer2.com|Customer #2 HR|HR Manager"
EMAIL_ROUTING_TENANT="customer2"
```

No code change. No deploy. Just env + tenant key.
