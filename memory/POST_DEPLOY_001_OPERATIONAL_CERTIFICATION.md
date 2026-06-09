# POST-DEPLOY-001 · Operational Certification

**Date:** 2026-06-09  
**Target:** `https://mascidocs.com`  
**Verdict:** 🟡 **PRODUCTION HEALTHY WITH MINOR ISSUES** (certification gap, not platform defect)

## PASS / FAIL Matrix

| § | Module                              | Verdict          | Note |
|---|--------------------------------------|------------------|------|
| 1 | Platform Health (TLS, CDN, ping)     | ✅ PASS           | External probes |
| 2 | Authentication                       | ✅ PASS           | Auth gate `401` confirmed; login flow not executed by agent |
| 3 | Daily Reports                        | ⚠️ OPERATOR       | Requires prod admin token to create/cleanup |
| 4 | DR Project Grouping (canonical)      | ✅ INHERITED      | ID-002/003/004 doctrine shipped + verified preview-side |
| 5 | Job Photos                           | ✅ INHERITED      | ID-003 conversion verified preview-side |
| 6 | HR (legal + preferred name)          | ⚠️ OPERATOR       | UI verified preview-side; live re-test by operator |
| 7 | Time Verification + Print            | ⚠️ OPERATOR       | Last cert: HR-TIME-001E (preview) |
| 8 | Project Identity Governance Center   | ✅ PASS           | Endpoint reachable + auth-gated; metrics need operator session |
| 9 | Motive                               | ✅ PASS           | Endpoint auth-gated; data layer verified preview-side; intentionally MOCKED until API keys configured |
| 10 | Backups                              | ✅ PASS           | DEPLOY-FIX-001 hardening shipped + live startup sweep firing |
| 11 | Restore Readiness                    | ✅ INHERITED      | Archive integrity certified preview-side |
| 12 | Mobile                               | ⚠️ INHERITED      | Last cert: HR-TIME-001E + MOTIVE-DATA-003 |
| 13 | Performance                          | ✅ PASS           | Sub-500 ms across the board |
| 14 | Security                             | ✅ PASS           | 401 on all admin routes; HSTS preload; TLS valid |

## Production Issues Discovered

**None.** All externally-probable signals report healthy. The 🟡 verdict is solely due to the fork agent's inability to execute the authenticated half of the certification without operator-supplied credentials.

## Screenshots

- `/app/memory/post_deploy_001_prod_login.jpg` — production Admin Sign-In page, full branding intact.

## Performance Metrics

```
/                            avg 0.378 s
/api/health                  avg 0.134 s
/api/jobs-master             avg 0.170 s
/admin/login                 avg 0.442 s
```

## Security Findings

- ✅ HTTPS-only via HSTS preload.
- ✅ Cloudflare edge in front of origin (DDoS + Bot Management).
- ✅ TLS cert valid through 2026-07-25.
- ✅ Every admin / HR / identity endpoint returns `401` unauthenticated.
- ✅ POST with empty body returns `422` (Pydantic schema validation working).

## Operational Findings

- Production frontend renders cleanly at `/admin/login` with full MASCI brand + ForgedOps footer.
- Public Hub route `/hub` returns `200` (field-crew entry path open per design).
- Multi-portal master sign-in promoted in the UI (matches preview behavior).
- ForgedOps™ attribution preserved in production footer.

## What This Certification Does NOT Cover

- Authenticated end-to-end flows (DR create, HR edits, Print preview, Governance Center counts, Motive dashboards, mobile login).
- Operator-only data (production governance queue counts, prod backup recency display).
- Mobile device certification on prod (last drill: HR-TIME-001E preview).
- End-to-end restore drill against a clean prod copy.

These require either operator-supplied prod admin credentials (single-use, then rotated) or operator-driven verification via the 10-step runbook in `POST_DEPLOY_001_EXECUTIVE_SUMMARY.md`.

## Sign-Off

> 🟡 **PRODUCTION HEALTHY WITH MINOR ISSUES** — promote to 🟢 once the operator runbook is signed off.
