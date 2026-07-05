# DR-UNIFY-001 — P0 · Admin Token Gate 401 · RCA

**Track:** DR-UNIFY-001 companion RCA
**Severity:** P0 (blocks Wave-2 live PDF smoke; likely also breaks `/api/admin/daily-roll-up` and `/api/admin/daily-report-health` for real admin users)
**Date:** 2026-02-15
**Status:** ROOT CAUSE IDENTIFIED · fix specified · **not applied in this audit pass** (audit is docs-only per user directive)

---

## SYMPTOM

Wave-2 live smoke test:
```
1. POST /api/auth/multi-login  →  200  →  portal_tokens.admin (101 chars)  ✓
2. POST /api/dr-v2/drafts       →  200  ✓
3. POST /api/dr-v2/ai/approve   →  200 (accept)  ✓
4. GET  /api/dr-v2/reports/{id}/pdf  → **401  "Invalid admin/PM/HR token"**
5. Legacy `POST /api/admin/login` with MASCI1982!  → returns empty token (204 or 200 w/ empty)
```

Both admin-token flows are rejected by the gate `require_admin_pm_or_hr_read`.

---

## ROOT CAUSE

`require_admin_pm_or_hr_read` (server.py:746) calls the **synchronous** helper `_is_valid_admin_token`:

```python
# server.py:759
if x_admin_token and _is_valid_admin_token(x_admin_token):
    return True  # legacy admin sentinel
```

But `_is_valid_admin_token` was **retired in TRACK 15.32** and now returns `False` unconditionally (server.py:353–363):

```python
def _is_valid_admin_token(tok: Optional[str]) -> bool:
    """TRACK 15.32 — shared ADMIN_PASSWORD HMAC retired.
    Synchronous fast-path now returns False unconditionally.
    """
    del tok
    return False
```

**Consequence:** `require_admin_pm_or_hr_read` NEVER accepts an admin token via the sync path. Admins fall through to the PM branch, then the HR branch, then the final 401. Only PM and HR tokens work.

Contrast with the canonical `require_admin` gate (server.py:409+), which was correctly updated to the async validator:

```python
if x_admin_token and await _is_valid_directory_admin_token_async(x_admin_token):
    return True
```

`require_admin_pm_or_hr_read` was **NOT** updated during TRACK 15.32 sweep. It's a stale gate.

---

## BLAST RADIUS

Routes gated by `require_admin_pm_or_hr_read` (from grep):
- `/api/admin/daily-roll-up` (`routes/dr_admin_intel.py:42`)
- `/api/admin/daily-report-health` (`routes/dr_admin_intel.py:66`)
- `/api/admin/…` (`routes/dr_admin_intel.py:122`)
- `/api/dr-v2/reports/{id}/pdf` (**new · this track**)
- `/api/dr-v2/reports/approved` (**new · this track**)

Any admin user hitting these routes via the frontend intelligence dashboards would get 401. Because the PM branch works, PMs and HRs experience no issue → the bug is invisible to non-admin users. Admins hitting the `/admin/operational-intelligence` dashboard would see delays data fail to load (`fetchAdminDelays`).

**Why nobody noticed sooner:** `fetchAdminDelays` errors are surfaced as a small "Load failed" text in a corner of the dashboard, not a crash. QA has been running the dashboards under PM tokens (which do work). The bug lay dormant until Wave-2 tried to use admin tokens for PDF download.

---

## FIX SPECIFICATION (to apply in DR-UNIFY-002)

Replace the sync path with the async directory validator, mirroring `require_admin`:

```diff
async def require_admin_pm_or_hr_read(
    request: Request,
    x_admin_token: Optional[str] = Header(default=None),
    x_pm_token: Optional[str] = Header(default=None),
    x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
):
-    if x_admin_token and _is_valid_admin_token(x_admin_token):
-        return True
+    if x_admin_token and await _is_valid_directory_admin_token_async(x_admin_token):
+        return True
```

One-line change. Everything else in the gate stays the same.

**Test:** add a pytest that seeds a directory admin token via `user_directory.make_directory_admin_token`, presents it to `/api/dr-v2/reports/approved`, and asserts 200.

**Related:** while we're there, sweep for any other gate still calling `_is_valid_admin_token` (the sync stub). Grep already found line 549 (`require_admin_or_pm_read`) — needs the same treatment. Others:

```bash
grep -n "_is_valid_admin_token\b" /app/backend/server.py
```
Result: 353 (definition), 549 (another gate that needs updating), 630 (comment).

Both `require_admin_or_pm_read` and `require_admin_pm_or_hr_read` need the fix. Also verify the `X-Directory-Token` header path (used by some admin routes).

---

## LEGACY BREAK-GLASS `POST /api/admin/login`

The legacy `POST /api/admin/login` with `ADMIN_PASSWORD=MASCI1982!` returned an empty token in preview. This suggests the legacy break-glass path was retired alongside TRACK 15.32 (see server.py:353 doc: "shared ADMIN_PASSWORD HMAC retired"). The `/app/memory/test_credentials.md` note "Legacy API-only break-glass" is out of date — the endpoint responds but issues a no-op token.

**Recommendation:** either (a) fix the legacy endpoint to issue a valid directory token bound to a synthetic emergency admin row, or (b) remove the endpoint entirely and update docs. Not urgent — normal admins use `/api/auth/multi-login`.

---

## WHY NOT FIX IN THIS AUDIT PASS

The user's directive DR-UNIFY-001 is explicit: **"Only docs/tests/inspection artifacts unless a tiny no-risk grep/test helper is required."**

A gate change is not a tiny no-risk edit — it changes auth semantics on 5 endpoints and needs its own test suite. Deferred to DR-UNIFY-002 where it can land alongside the copy scrub and be verified by the full lock-test plan.

---

## ACCEPTANCE CRITERIA (DR-UNIFY-002)

- [ ] `require_admin_pm_or_hr_read` accepts directory admin tokens
- [ ] `require_admin_or_pm_read` (server.py:549) audited and fixed if broken
- [ ] Wave-2 live smoke re-runs: admin token → 200 PDF
- [ ] Wave-2 live smoke re-runs: PM in-scope → 200 PDF · out-of-scope → 404
- [ ] Wave-2 live smoke re-runs: HR read token → 200 PDF
- [ ] Admin dashboard OI page loads delays chart without 401
