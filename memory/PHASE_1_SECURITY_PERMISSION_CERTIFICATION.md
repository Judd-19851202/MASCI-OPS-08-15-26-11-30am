# Phase 1 · Security & Permission Certification

**Date:** 2026-02-05
**Status:** 🟢 GO

## Authentication surface
- Master sign-in: `/sign-in` (multi-workspace) — public form, no auth requirement to render.
- Portal sign-in variants (public): `/admin/login`, `/pm/login`, `/hr/login`, `/shop/login`, `/dispatch-portal/login`, `/safety-portal/login`, `/field-leadership/portal/login`, `/leadership/login`, `/dev/login`, `/safety/forms/login`.
- Admin API surface: gated by `RequireAdmin` on backend + `A` alias on frontend.

## Permission gating (frontend — machine-verified from `APP_JS_INVENTORY.json`)
| Guard alias | Component | Routes |
|---|---|---:|
| PUBLIC | *(none)* | 143 |
| A | RequireAdmin | 65 |
| AP | RequireAdminOrPm | 45 |
| SF | RequireSafety | 33 |
| H | RequireHr | 28 |
| S | RequireShop | 25 |
| P | RequirePm | 22 |
| DP | RequireDispatch | 10 |
| D | RequireDev | 6 |
| FL | RequireFl | 4 |
| APS | RequireAdminPmOrSafety | 3 |
| TX | RequireTransportationPortal | 1 |
| **Total** | | **385** |

## Backend gate verification (live smoke)
| Endpoint | Expected | Actual | Verdict |
|---|---|---|---|
| `GET /api/admin/platform/status` (no auth) | 401 | 401 `{"detail":"Admin login required"}` | 🟢 |

## No-secret-leakage audit
- Platform Status API returns only lifecycle + email-safety flags. No API keys, no DSNs, no MongoDB URIs.
- Frontend `.env` exposes ONLY `REACT_APP_BACKEND_URL`, `WDS_SOCKET_PORT`, `ENABLE_HEALTH_CHECK`, `REACT_APP_SENTRY_DSN` (public DSN, intentional).
- Backend `.env` NEVER exposed to frontend (verified — no `process.env.RESEND_API_KEY` or similar in bundle).

## CORS
- No wildcard `*` origins.
- `allow_origin_regex` is a documented Starlette middleware pattern (Track 22.3 zero-drift attestation).

## No-widened-surface delta (session-scope)
- Files touched this session on backend: 1 (`routes/passkeys.py` — 3-line ConfigDict swap · zero permission change)
- Files touched this session on frontend: 0
- Permission surface delta: **0**

## Class A/B security findings
_None._

## Certification
🟢 **Security & Permission surface unchanged from baseline. Phase 1 GO.**
