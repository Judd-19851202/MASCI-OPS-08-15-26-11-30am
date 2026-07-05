# Phase 1 · Post-Deploy Smoke Plan

**Date:** 2026-02-05
**Execution window:** ≤ 10 minutes after each deploy
**Verdict rule:** ANY step failing → immediate rollback per `PHASE_1_ROLLBACK_PLAN.md`.

## Backend smoke (execute in order)

### 1. Health check
```bash
API_URL=<production backend URL>
curl -sS "$API_URL/api/admin/platform/status" -o /tmp/ps.json -w "%{http_code}\n"
```
- Expected: `401`
- Body: `{"detail":"Admin login required"}`
- Verdict rule: any 5xx → rollback

### 2. Route surface (admin-authenticated — pre-issued admin JWT recommended)
```bash
curl -sS -H "Authorization: Bearer $ADMIN_JWT" "$API_URL/api/admin/platform/status" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['lifecycle']['migration_progress'])"
```
- Expected: `lifecycle_complete=true · startup_pct=100 · shutdown_pct=100`

### 3. Email safety
Same call as (2) — verify:
- `email_safety.mode` matches production intent (may be `strict` or normal per operator decision)
- `email_safety.resend_sdk_patched` matches operator intent
- If `mode=live` and dispatch enabled: monitor Resend dashboard for first 10 minutes

### 4. Auth smoke
```bash
curl -sS -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"<valid-admin>","password":"<valid-pw>"}' \
  -w "%{http_code}\n"
```
- Expected: `200` with JWT
- Rollback on: 5xx, timeout, 401 with valid credentials

## Frontend smoke (execute in order)

### 5. Public landing
- Visit `https://<production-frontend>/`
- Expected: MASCI hero + 3 portal cards render within 5 seconds
- Rollback on: blank screen, 5xx, console errors

### 6. Sign-in (master)
- Visit `https://<production-frontend>/sign-in`
- Expected: Form + 7 workspace links + zero console errors
- Rollback on: 5xx, broken form, missing links

### 7. Deep-link 404
- Visit `https://<production-frontend>/nonexistent-page-xyz`
- Expected: Custom 404 with Sign In + Public Home CTAs
- Rollback on: server 404 (nginx page) or blank React error

### 8. Role portal spot-check (per role — smoke only)
For each role with a live user:
- Login via portal login
- Confirm portal home loads
- Confirm one representative deep-link (e.g. `/admin/hub` for Admin, `/pm/hub` for PM)
- Rollback on: infinite redirect, forbidden page, console errors

Roles to spot-check: Admin, PM, HR, Safety, Dispatch, Shop, Field Leadership.

## Rollback authority
If any smoke step fails and cannot be diagnosed within 5 minutes: execute rollback IMMEDIATELY per `PHASE_1_ROLLBACK_PLAN.md`. No debugging in production.

## Success criteria
All 8 smoke steps green within 10 minutes of deploy completion.
