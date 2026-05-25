# PHASE 28.2 · Production Observability
## iter430 · 2026-05-25

## Stack
- **Sentry** — already integrated via `backend/sentry_init.py` and
  `frontend/src/lib/sentryInit.js`. DSN-gated · PII scrubbed by
  `_before_send` (passwords, tokens, secrets, api keys, cookies,
  every `X-*-Token` header). No-op when `SENTRY_DSN` is unset →
  preview/dev environments stay completely silent.
- **NEW this phase**: `backend/sentry_tags.py` —
  `SentryOperationalTagsMiddleware`. Auto-attaches operational tags
  to every event so a production exception card answers "which
  portal, which role, which device, which language" without
  log-diving.

## Tag set (every captured event carries these)
| Tag        | Source                                       | Values (examples) |
|------------|----------------------------------------------|------------------|
| `portal`   | `X-*-Token` header inspection · path fallback | admin · dispatch · pm · shop · safety · hr · field · driver · public |
| `role`     | mirror of `portal` (RBAC class, not identity) | admin · dispatch · … |
| `route`    | FastAPI route template (post-routing)         | `/api/dispatch/assignments/{assignment_id}` |
| `device`   | coarse UA classification                      | ios · android · mac · windows · linux · bot · unknown |
| `browser`  | coarse UA classification                      | safari · chrome · edge · firefox · unknown |
| `language` | `X-Lang` header · falls back to `Accept-Language` | en · es |
| `tenant`   | `X-Tenant-Id` header                          | masci (default) |
| `platform` | static                                        | masci-hub |
| `component`| static                                        | backend |
| `tagged_by`| audit signal                                  | sentry_tags.middleware |

No PII, no unique identifiers, no fingerprinting. Just bucket names
that Sentry's filter UI can group by.

## What gets captured
- ✅ backend FastAPI exceptions (`FastApiIntegration`)
- ✅ `logger.error(...)` (LoggingIntegration · ERROR+ becomes event)
- ✅ frontend React errors via `lib/sentryInit.js`
- ✅ request body / query string (PII-scrubbed)
- ✅ release identifier = `/api/version` `source_hash` (same string
   on both backend and frontend bundles)

## What is intentionally NOT captured
- ❌ uptime % / SLA dashboard inside MASCI
- ❌ "system health" UI · no charts, no graphs, no metrics screen
- ❌ session recording / replays
- ❌ user-bound identifiers (Sentry `user.id`)
- ❌ raw auth headers (scrubbed before send)

## Verification
- ✅ Unit tests against the coarse UA + portal classifiers:
  `tests/test_iter430_persistence_health_and_sentry_tags.py`
- ✅ Middleware mounted in `server.py` after CORS · noop when
  `SENTRY_DSN` is unset.
- ☐ Operator: confirm a forced 500 on prod produces a Sentry event
  carrying the new tags (curl an admin endpoint with a malformed
  payload and check the Sentry inbox).
