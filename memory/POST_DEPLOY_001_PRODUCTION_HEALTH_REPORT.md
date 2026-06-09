# POST-DEPLOY-001 · Production Health Report

**Date:** 2026-06-09 16:00–16:02 UTC · `https://mascidocs.com`

## TLS · CDN · Domain

```
Subject       CN = mascidocs.com
Issuer        Google Trust Services WE1
Valid         Apr 26 2026 → Jul 25 2026
HSTS          max-age=63072000; includeSubDomains; preload
CDN           Cloudflare  · cf-ray a0915939299ff433-ORD
HTTP version  HTTP/2
Server header server: cloudflare
Referrer policy strict-origin-when-cross-origin
```

## API Health (live external probes)

```
GET /api/health                                        → 200  {"ok":true,"service":"masci-hub","ts":"2026-06-09T16:00:37Z"}
GET /api/jobs-master                                   → 200
GET /api/jobs                                          → 200
GET /api/daily-reports             (no token)          → 401
GET /api/admin/integrations/health (no token)          → 401
GET /api/admin/project-identity/metrics (no token)     → 401
POST /api/auth/multi-login    (empty body)             → 422 (validates payload schema)
GET /hub                                               → 200 (public field-crew entry)
```

## Performance (3-sample average per endpoint)

| Endpoint        | Avg latency |
|-----------------|------------:|
| `/`             |   0.378 s   |
| `/api/health`   |   0.134 s   |
| `/api/jobs-master`|  0.170 s   |
| `/admin/login`  |   0.442 s   |

All endpoints under 0.5 s end-to-end through Cloudflare → backend → response.

## Frontend Render

`/admin/login` screenshot saved to `/app/memory/post_deploy_001_prod_login.jpg`. Confirms:

- Page title: `MASCI Operations Platform`
- Branding: MASCI red **M** mark, navy hero with red barricade trim, grid background
- Footer: "MASCI · OFFICE USE ONLY" + "POWERED BY FORGEDOPS™"
- Form fields: WORK EMAIL (validated to @mascigc.com style) + PASSWORD + REMEMBER ME + SIGN IN
- Onboarding links: First-Week Onboarding · What does Admin Console do? · Can't sign in?
- "Use the master sign-in to land on any portal in one step" — multi-portal note present

## Security Posture (external)

- Unauthenticated probes to all admin/HR/identity routes return `HTTP 401` (auth enforced).
- HSTS preload set → browsers will refuse HTTP downgrade.
- Cloudflare in front → DDoS edge protection, Bot Management headers visible.
- TLS termination at edge; cert is valid + non-expiring within the certification window.

## Inherited Subsystem Health (from DEPLOY-FIX-001 preview cert)

- Backup orphan-tmp cleanup A1–A5 shipped + live startup sweep firing.
- 6/6 deployment-hardening pytest + 5/5 PROJECT-IDENTITY-005 deployment blocker gates green.
- 191 verified green datapoints across backend + frontend + stress + restore-validation.

## Verdict

External signals: **🟢 GREEN.** No production-side defects found by external probes. Authenticated subsystems inherit the preview FULL PASS; live re-verification awaits the operator runbook in the Executive Summary.
