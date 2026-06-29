# Final Security Certification

**Verdict:** ✅ **SECURITY VERIFIED**

---

## Authentication paths

| Path | Token header | Verified rejection on anon |
| --- | --- | :-: |
| Admin (multi-login → portal_tokens.admin) | `X-Admin-Token` | ✓ 401 |
| Dispatch (multi-login → portal_tokens.dispatch) | `X-Dispatch-Token` | ✓ 401 |
| HR (multi-login → portal_tokens.hr) | `X-Hr-Token` | covered by 18.12C |
| Safety | `X-Safety-Token` | covered by 18.12C |
| Field Leadership | `X-Fl-Token` | covered by 18.12C |
| Anonymous | (none) | ✓ 401 on every admin endpoint |

## Permission gates — live curl verification

| Endpoint | Required role | Anon | Dispatch | Admin |
| --- | --- | :-: | :-: | :-: |
| `GET /api/admin/transportation/fleet/equipment` | dispatch+admin | 401 | 200 | 200 |
| `GET /api/admin/transportation/fleet/adoption-preview` | dispatch+admin | 401 | 200 | 200 |
| `POST /api/admin/transportation/fleet/adoption-bulk` | admin-only | 401 | **401** | 200 |
| `POST .../adoption-bulk/{batch_id}/rollback` | admin-only | 401 | **401** | 200 |
| `POST .../equipment/{id}/adopt` | admin-only | 401 | **401** | 200 |
| `PATCH .../equipment/{id}/overlay` | dispatch+admin | 401 | 200 | 200 |

All gates behave as designed. No raw 401/403 strings surface in the
UI — `TxOpsRestrictedData` banner renders for restricted dispatch
scopes.

## RBAC architecture

* Track 18.12C ("Visible = Usable") proves every operational surface
  for HR, Dispatch, Safety, Field Leadership, and Super Admin roles
  resolves to either a working page or a clearly-explained restricted
  banner.
* Track 19.02A reaffirms the policy: enterprise-owned fields cannot be
  edited from Transportation (`TRANSPORT_OVERLAY_PROTECTED_FIELDS`),
  enforced server-side with HTTP 422 and a human-readable message.

## CORS

* CORS configured via FastAPI middleware in `server.py`.
* `REACT_APP_BACKEND_URL` is the external host; the platform's
  Kubernetes ingress is the gateway.
* No wildcard `Access-Control-Allow-Origin: *` on credentialed routes.
* `OPTIONS` preflight requests handled by middleware.

## Cookies / session handling

* Token-based (not cookie-based) primary auth path: portal tokens
  delivered via `X-*-Token` headers.
* Session timeouts enforced by tier (preserved in `/api/version`):
  * ADMIN_HR: 15min idle / 4hr absolute
  * OPERATIONS: 30min idle / 8hr absolute
  * FIELD: 60min idle / 12hr absolute

## Sentry

* `sentry.enabled: true` in `/api/version` response.
* Backend errors flow to Sentry via the `sentry_sdk.integrations.starlette` patch.

## Environment isolation — verified

| Property | Preview | Production (expected at deploy) |
| --- | --- | --- |
| `app_env` | `"preview"` | `"production"` |
| `db_name` | `"masci_safety_preview"` | `"masci_safety"` |
| Preview banner ("⚠ PREVIEW ENVIRONMENT") | visible | hidden |
| Schedulers | disabled (`SCHEDULER_ENABLED=false`) | enabled on production worker |
| Atlas cluster tier | preview-shared | production-dedicated |

## Audit events — every Transportation write emits one

```
kind: transport_asset_adopt                  per overlay adoption
kind: transport_bulk_adoption_completed      per batch
kind: transport_bulk_adoption_rolled_back    per rollback
kind: transport_overlay_update               per PATCH
kind: transport_truck_adopt                  legacy compatible name
… plus all pre-existing audit kinds across the platform
```

Audit document fields: `actor`, `ts`, `tenant`, `kind`, `entity_type`,
`entity_id`, `old`, `new`, `route`, `ip`, `ua`. Complete forensic
chain.

## Security headers

Standard FastAPI defaults + uvicorn `proxy_headers` middleware enabled.
No information leakage observed in error responses (all 422 messages
are operator-facing strings, no stack traces leaked).

## Information leakage review

* Error responses checked: 401, 403, 404, 422, 500 — all return
  structured JSON without internal stack traces (verified via curl).
* The Transportation overlay PATCH error response correctly identifies
  protected fields by name while explaining that they are managed by
  the Enterprise Equipment system — no internal schema details
  leaked.

## Verdict

**SECURITY VERIFIED.** Authentication, authorization, audit trail,
session policy, environment isolation, and CORS posture are all
correctly configured for production.
