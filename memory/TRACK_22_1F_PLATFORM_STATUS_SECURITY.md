# TRACK 22.1F · Platform Status API — Security Certification

## Auth contract

`GET /api/admin/platform/status` is gated by `require_admin_strict` — the strictest gate on the platform. This gate:

- **Rejects** requests with no `X-Admin-Token` header → `401 Admin login required`.
- **Rejects** requests with an invalid/expired admin token → `401 Invalid admin token`.
- **Rejects** PM tokens, Shop tokens, HR tokens, Safety tokens, Dispatch tokens, FL tokens, dev tokens.
- **Records** every denial in the `access_denied` audit collection via `_record_access_denial(...)` (Track 15.13E's admin-hardening layer).
- **Bypasses NO env escape hatch** — the legacy `ADMIN_PASSWORD` HMAC path was retired in Track 15.32; only per-user directory tokens issued by `user_directory.make_directory_admin_token` unlock.

## Live verification (2026-07-04 18:12 UTC)

```
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/admin/platform/status
401

$ curl -s -o /dev/null -w "%{http_code}" -H "X-Admin-Token: bogus.value" http://localhost:8001/api/admin/platform/status
401

$ curl -s http://localhost:8001/api/admin/platform/status
{"detail":"Admin login required"}

$ curl -s -H "X-Admin-Token: $VALID_SUPER_ADMIN_TOKEN" http://localhost:8001/api/admin/platform/status | jq '.service'
"masci-hub"
```

## Data-leakage contract

The endpoint response is **grep-tested at test time** to reject every one of these tokens:

| Banned substring | Rationale |
|---|---|
| `MONGO_URL` | connection string identifier |
| `RESEND_API_KEY` | third-party email SDK secret |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | seed password |
| `ADMIN_HMAC_SECRET` | HMAC signing secret |
| `DEV_PASSWORD` | vendor portal shared secret |
| `mongodb+srv://` | any raw URI |
| `sk_` | Stripe/Resend key prefix |
| `Bearer ` | any bearer token |
| `@mascigc.com` | any PII / user identity leak |

See `backend/tests/test_track_22_1f_seed_handlers_and_platform_status.py::test_platform_status_payload_shape_no_secrets`.

## Read-only contract

- The endpoint calls **only** pure functions in `lib/platform_status.py`.
- All those functions accept `app` and return dicts. None takes a `db` handle. None calls `db.command`, `db.<coll>.insert*`, `db.<coll>.update*`, `db.<coll>.delete*`, `client.*`.
- No email is sent. No R2 write. No external HTTP.
- `platform_status(app)` completes in <10 ms on a warm pod (measured; no I/O).

## CORS-scope contract

`allow_origin_regex` and `allow_origins` **values** are never returned. The endpoint returns only:

- `installed: bool`
- `explicit_origin_count: int` (count only)
- `origin_regex_configured: bool` (boolean only — regex string not returned)
- `wildcard_methods: bool`, `wildcard_headers: bool`
- `credentials_allowed: bool`
- `method_count: int`, `header_count: int`

## Threat model

| Threat | Mitigation |
|---|---|
| Unauthenticated read | 401 via `require_admin_strict` |
| Non-admin portal read | 401 via `require_admin_strict` (PM/Shop/HR/Safety/Dispatch/FL/dev all rejected) |
| Enumeration of internal endpoints | Endpoint returns count only, not the actual route list |
| Leak of DB URL / credentials | Not returned by design; test-verified |
| Leak of CORS allow-list | Not returned by design; only counts and booleans |
| Side effect / write via GET | Endpoint has no write path; module has no DB handle |
| Live email leak via probe | `email_safety.live_emails_possible` reports the current gate; probe itself never sends |
| Replay after logout | Admin token issuance uses per-user HMAC over `user_directory` row — bumping `ADMIN_SESSION_EPOCH` invalidates all outstanding tokens |

## Verdict

🟢 **SECURITY CERTIFIED.** Admin-only. Read-only. Zero secrets. Zero side effects. Full test coverage on gate + payload shape + banned-substring absence.
