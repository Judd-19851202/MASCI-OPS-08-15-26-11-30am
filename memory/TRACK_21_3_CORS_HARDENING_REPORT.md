# TRACK 21.3 · Phase B · CORS Hardening Report

**Date:** 2026-07-04
**File touched:** `backend/server.py` — CORS middleware block only (lines ~15877-15911).
**Guardrail:** `EMAIL_SAFETY_MODE=strict` was active throughout — no live email was possible.

## Before

```python
allow_methods=["*"],
allow_headers=["*"],
```

Wildcard methods and headers accepted anything the browser sent. Broadened
the CSRF/side-effect surface unnecessarily.

## After

```python
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
allow_headers=[
    "Accept", "Accept-Language", "Authorization", "Content-Type",
    "Origin", "Range", "X-Admin-Token", "X-Client-Trace",
    "X-CSRF-Token", "X-Portal-Token", "X-Requested-With",
    "X-Session-Id",
],
expose_headers=["Content-Disposition", "Content-Length", "ETag", "X-Request-Id"],
```

Every entry is present because we verified the frontend actually emits or
reads it. Multipart uploads keep working because `Content-Length` and
`Content-Disposition` are CORS-safelisted auto-headers.

## Verification (live curl · safe-only smoke)

Executed with the backend restarted under `EMAIL_SAFETY_MODE=strict`.
No workflow POSTs. No email-triggering endpoints. Only OPTIONS preflights
and health probes.

| Probe | Result |
|---|---|
| `GET /api/health` | **200** — service healthy after restart |
| `OPTIONS /api/health` (preflight for `GET` with `Content-Type,X-Admin-Token`) | **200** — echoes allow-methods + allow-headers |
| `OPTIONS /api/auth/multi-login` (preflight for `POST` with `Authorization,Content-Type`) | **200** |
| `OPTIONS /api/daily-reports/attachments/upload` (preflight for `POST` with `Content-Type,Authorization`) | **200** |
| Response headers include | `access-control-allow-methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD`, `access-control-allow-headers: Accept, Accept-Language, Authorization, Content-Language, Content-Type, Origin, Range, X-Admin-Token, X-CSRF-Token, X-Client-Trace, X-Portal-Token, X-Requested-With, X-Session-Id`, `access-control-allow-credentials: true` |
| Boot log | `[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.` |

No workflow endpoints were called. No email was dispatched.

## Blockers

None. If a future integration requires a new method (unlikely — REST doesn't
grow more verbs) or a new header, add it explicitly. That's the point of
tightening.

## Zero-drift statement

- Origin allow-list unchanged (still `CORS_ORIGIN_REGEX` from `.env`).
- Credentials mode unchanged (`allow_credentials=True`).
- No route-level middleware touched.
- No auth gate widened or narrowed.
- Production behavior identical when the frontend uses documented methods/headers (it does — verified across `frontend/src/**`).

## Class-C status

**CORS tightening** debt (formerly documented at the platform level) → **CLOSED.**
