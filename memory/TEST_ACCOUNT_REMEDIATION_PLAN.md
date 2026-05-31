# Test Account Remediation Plan · Critical Fix Sprint 1 · P0-1

**Batch:** OMEGA Critical Fix Sprint 1 · P0-1
**Date:** 2026-05-31
**Scope:** Recommended remediation actions for the 9 findings in `TEST_ACCOUNT_AUDIT.md`. **NO ACCOUNTS MODIFIED.** Operator authorization required.

---

## 1 · Priority sequence

| # | Action | Severity | Risk if left alone | Recommended order |
|---|---|---|---|---|
| R-1 | Rotate / deactivate / delete `fieldleader@mascigc.com` | 🔴 P0 | Anyone with repo read access can authenticate to production with Superintendent FL scope | **1st** |
| R-2 | Audit `user_directory` 5 accounts with `mcp=False · never logged in` for password state | 🟡 P1 | Default-or-known passwords may persist without forced rotation | 2nd |
| R-3 | Backfill `is_active` field on the 7 `user_directory` rows | 🟡 P2 | Inconsistent UI visibility | 3rd |
| R-4 | Decide fate of legacy 4 `users.role=owner` accounts | 🟡 P2 | Stale auth records; if compromised, would grant owner-level platform access | 4th |
| R-5 | Update `/app/memory/test_credentials.md` to remove `fieldleader@mascigc.com` reference once R-1 ships | 🟡 P1 | Documentation drift | tied to R-1 |

---

## 2 · R-1 · `fieldleader@mascigc.com` test account

### 2.1 · 3 options (operator decides)

| Option | Action | Effort | Reversibility |
|---|---|---|---|
| A · Rotate password | `db.field_leadership_users.update_one({"email":"fieldleader@mascigc.com"}, {"$set": {"password_hash": <new-bcrypt>, "must_change_password": True}})` + update `/app/memory/test_credentials.md` with new password | <30 min | reversible |
| B · Deactivate | `db.field_leadership_users.update_one({"email":"fieldleader@mascigc.com"}, {"$set": {"is_active": False}})` + remove from `/app/memory/test_credentials.md` | <10 min | reversible |
| C · Delete | `db.field_leadership_users.delete_one({"email":"fieldleader@mascigc.com"})` + remove from `/app/memory/test_credentials.md` | <10 min | non-reversible without re-seed |

**Recommendation:** **Option B (deactivate)** — preserves audit trail · easy to reactivate if a future cert batch needs it · `is_active=False` will cause login routes to reject.

### 2.2 · Pytest impact

After R-1 ships, automated tests that authenticate as `fieldleader@mascigc.com` will fail. **Verify no pytest depends on this account before remediation.**

Search command (operator can run before authorizing R-1):
```bash
grep -rn "fieldleader@mascigc.com" /app/backend/tests/ /app/scripts/
```

### 2.3 · Verification step (post-remediation)

```bash
curl -s -X POST https://mascidocs.com/api/auth/multi-login \
  -H "Content-Type: application/json" \
  -d '{"email":"fieldleader@mascigc.com","password":"FieldLead2026!"}'
# Expected: 401 or "user inactive"
```

### 2.4 · Risk if left alone

🔴 Anyone with `/app/memory/test_credentials.md` access can authenticate to production with Superintendent Field Leadership scope. The Field Leadership token unlocks:
- Daily Reports (own + assigned projects · read/write)
- Safety Meetings (write)
- JHAs (write)
- DVIRs (write)
- Fleet read-only · Dispatch read-only
- Incidents (read + report)
- Driver Qualification dashboard

Worst-case attacker action: submit forged daily reports, inject false safety-meeting attendance, fabricate JHAs / DVIRs, or report falsified incidents in the operator's name.

---

## 3 · R-2 · `user_directory` rows with `mcp=False · never logged in`

### 3.1 · Verification step (operator-side · no code change)

Run for each account:
```javascript
db.user_directory.findOne({email: "hrmanager@mascigc.com"})
// Inspect `password_hash` / `password_set_at` fields
```

Each row's bcrypt hash must NOT match common dictionary defaults (`Welcome1!` · `Password1!` · `Demo2026!` · `Test1234!` · `MASCI1982!` · etc).

### 3.2 · If a default password is found

Force `must_change_password=True`:
```javascript
db.user_directory.update_one(
  {email: "hrmanager@mascigc.com"},
  {$set: {must_change_password: true, password_force_rotate_at: ISODate()}}
)
```

### 3.3 · Risk if left alone

🟡 IMPORTANT. If any of these 5 accounts has a default password, an actor who guesses or brute-forces it would gain portal access without any forced rotation step.

---

## 4 · R-3 · `user_directory.is_active` backfill

### 4.1 · Diagnosis

7 of 7 `user_directory` rows have `is_active=null` (not `True` or `False`).

### 4.2 · Recommended action

Backfill all 7 with `is_active=True`:
```javascript
db.user_directory.updateMany(
  {is_active: null},
  {$set: {is_active: true}}
)
```

Then update the schema validator (if any) to require `is_active` field on insert.

### 4.3 · Risk if left alone

🟡 IMPORTANT. Any UI surface filtering `is_active=True` treats all `user_directory` rows as not-active → directory-based features may silently lose users.

---

## 5 · R-4 · Legacy `users.role=owner` accounts

### 5.1 · Diagnosis

4 of 5 rows in `users` collection have `role=owner` and last logged in 2026-04-28 (one-time login during platform initialization). These are:
- `david.jewett@mascigc.com`
- `chris.wright@mascigc.com`
- `ramon.rodriguez@mascigc.com`
- `jaymn.judd@mascigc.com` (super-admin · still active via multi-login)

The 5th row is `safety@mascigc.com · role=admin`.

### 5.2 · Recommended action

Three sub-decisions per account:
1. **Confirm operational intent** with each owner.
2. If still needed: rotate password + set `must_change_password=True` to force re-auth.
3. If not needed: deactivate (`is_active=False`).

### 5.3 · Risk if left alone

🟡 IMPORTANT. Stale "owner" accounts with valid (and possibly rotated-default) passwords are credential targets. The 4 owner accounts haven't been used in 33+ days as of audit date.

---

## 6 · R-5 · Update `test_credentials.md`

Once R-1 ships, update `/app/memory/test_credentials.md` to either:
- Remove the `fieldleader@mascigc.com` entry entirely (if deleted), OR
- Note that the account is deactivated and the documented password is invalid

This prevents future agents from assuming the test account is still usable.

---

## 7 · Closeout

🟡 5 remediation actions ranked. **NO modifications made.** Operator authorization required for each action.

🛑 STOP.
