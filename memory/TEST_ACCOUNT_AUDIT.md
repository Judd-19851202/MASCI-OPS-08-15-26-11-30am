# Test Account Audit · Critical Fix Sprint 1 · P0-1

**Batch:** OMEGA Critical Fix Sprint 1 · P0-1
**Date:** 2026-05-31
**Scope:** Inventory ALL production user accounts across 8 collections. Flag test/demo/training accounts, accounts with default passwords, orphaned accounts, inactive accounts. Read-only. No remediation.

---

## 1 · Total production user inventory

| Collection | Total | Notes |
|---|---|---|
| `users` | 5 | legacy owners + safety admin |
| `user_directory` | 7 | per-portal master account routing |
| `hr_users` | 3 | super-admin + 2 HR managers |
| `field_leadership_users` | 27 | FL crew leadership |
| `dispatch_users` | 2 | dispatcher + super-admin |
| `shop_users` | 2 | shop manager + super-admin |
| `safety_users` | 2 | safety manager + super-admin |
| `employees` | 245 | payroll/HRIS roster (mostly no email · no login) |
| **Total accounts in identity collections** | **48** (excluding `employees` HRIS roster) |
| **Total cross-portal-distinct emails** | 31 |

---

## 2 · 🔴 Test/demo/training accounts in production

| # | Email | Collection | Role | last_login | Flag |
|---|---|---|---|---|---|
| T-1 | **`fieldleader@mascigc.com`** | `field_leadership_users` | Superintendent | 2026-05-25 20:29Z | 🔴 EMAIL-SUSPECT · documented password in `/app/memory/test_credentials.md` |

**Evidence (from `/app/memory/test_credentials.md`):**
```
Test FL user: fieldleader@mascigc.com / FieldLead2026!
(must_change_password=false, ready for automated tests)
```

**Confirmed live on production with `must_change_password=False` · `is_active=True` · last_login 2026-05-25.**

🔴 **No other test/demo email patterns detected** across `test|demo|preview|sample|placeholder|dev|staging|qa` term match in any of 8 identity collections.

---

## 3 · 🟡 Accounts with no last_login (potentially abandoned or pre-onboarded)

| # | Email | Collection | mcp | Comment |
|---|---|---|---|---|
| A-1 | `hrmanager@mascigc.com` | `user_directory` | False | never logged in · mcp=False |
| A-2 | `shopmanager@mascigc.com` | `user_directory` | False | never logged in · mcp=False |
| A-3 | `safety@mascigc.com` | `user_directory` | False | never logged in · mcp=False |
| A-4 | `masciaccounting@mascigc.com` | `user_directory` | False | never logged in via directory · BUT `hr_users` row shows last_login 2026-05-29 11:17Z |
| A-5 | `leticiamasci@mascigc.com` | `user_directory` | False | never logged in via directory |
| A-6 | `leticiamasci@mascigc.com` | `hr_users` | True | role=HR Manager · never logged in (mcp=True · cleanly pre-onboarded) |
| A-7 | 25 of 27 FL users | `field_leadership_users` | True | `mcp=True · last_login=None` — appears cleanly pre-onboarded; await first login |

**Verdict on A-1..A-5 (`user_directory` rows with `mcp=False` and no last login):** 🟡 IMPORTANT. These rows have `must_change_password=False` meaning if a default/known password was set, it remains active without forced rotation. Operator should confirm password state.

---

## 4 · 🟡 Cross-portal email occurrences (super-admin + role overlaps)

| Email | In collections | Operational meaning |
|---|---|---|
| `jaymn.judd@mascigc.com` | `users`, `user_directory`, `hr_users`, `dispatch_users`, `shop_users`, `safety_users` (6 of 8) | Super-admin · expected · multi-portal access |
| `safety@mascigc.com` | `users`, `user_directory`, `safety_users` (3 of 8) | Safety-portal owner · expected |
| `dispatch@mascigc.com` | `user_directory`, `dispatch_users` | Dispatcher · expected |
| `shopmanager@mascigc.com` | `user_directory`, `shop_users` | Shop manager · expected |
| `masciaccounting@mascigc.com` | `user_directory`, `hr_users` | HR manager · expected |
| `leticiamasci@mascigc.com` | `user_directory`, `hr_users` | HR manager (pre-onboarded) · expected |

🟢 No unexpected cross-portal duplicates.

---

## 5 · 🟡 `user_directory` schema drift

7 rows · ALL with `is_active=null` (not `True` or `False`):

```
jaymn.judd@mascigc.com    is_active=None  mcp=False  last_login=2026-05-31T23:22:56
hrmanager@mascigc.com     is_active=None  mcp=False  last_login=None
shopmanager@mascigc.com   is_active=None  mcp=False  last_login=None
safety@mascigc.com        is_active=None  mcp=False  last_login=None
dispatch@mascigc.com      is_active=None  mcp=False  last_login=2026-05-16T17:09:51
masciaccounting@mascigc.com  is_active=None  mcp=False  last_login=None
leticiamasci@mascigc.com  is_active=None  mcp=False  last_login=None
```

**Implication:** Any UI surface filtering `is_active=True` would treat ALL `user_directory` rows as not-active. Any surface filtering `$ne False` would include them. **Inconsistent visibility.**

---

## 6 · Roles & permission overlap

- `users` collection (5 rows): 4 `role=owner` (David Jewett · Chris Wright · Ramon Rodriguez · Jaymn Judd) + 1 `role=admin` (safety@mascigc.com). All `is_active=True · mcp=True`. **All four owners last logged in 2026-04-28 (3 days after platform first stood up)**, then haven't been back since. The "owner" role is a legacy artifact — operational super-admin work flows through `jaymn.judd@mascigc.com` via multi-login.
- 245 `employees` records have NO email and NO login — these are HRIS-roster only, NOT auth subjects. Clean.
- 27 FL users are all `is_active=True · mcp=True` — pre-onboarded, awaiting first login. Clean.

---

## 7 · 🔴 / 🟡 / 🟢 summary

| Severity | Count | Items |
|---|---|---|
| 🔴 CRITICAL | 1 | `fieldleader@mascigc.com` test account with documented password |
| 🟡 IMPORTANT | 8 | 5 `user_directory` rows with `mcp=False · never logged in`; `user_directory` schema `is_active=null` everywhere (7 rows); 4 legacy `users.role=owner` accounts that last logged in 2026-04-28 |
| 🟢 CLEAN | 39 | all 27 FL users (pre-onboarded); 2 HR managers; 1 dispatcher; 1 shop manager; 1 safety manager; super-admin |

---

## 8 · Closeout

🟡 Production user base has **one confirmed test account** (`fieldleader@mascigc.com`) requiring decision, plus **8 important hygiene items** (mostly `user_directory` schema drift and legacy `users` owner accounts).

🛑 STOP. Remediation plan is in `TEST_ACCOUNT_REMEDIATION_PLAN.md`.
