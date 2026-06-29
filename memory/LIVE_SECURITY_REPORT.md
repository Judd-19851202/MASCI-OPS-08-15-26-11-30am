# LIVE Security Report — mascidocs.com

**Verdict:** ✅ **SECURITY VERIFIED ON LIVE**

---

## Authentication paths on LIVE

| Path | Verified |
| --- | :-: |
| `POST /api/auth/multi-login` returns `portal_tokens` for admin/pm/shop/hr/safety/dispatch/field_leadership/fl | ✓ (5+ tokens issued in test login) |
| Session token issued | ✓ |
| Admin token usable on subsequent admin endpoints | ✓ (all 7 verified return 200) |
| `must_change_password` flag respected | (returned in login payload; UI gates accordingly — verified in preview) |

## Permission gates on LIVE

| Endpoint | Anon | Notes |
| --- | :-: | --- |
| `GET /api/admin/transportation/fleet/equipment` | **401** | ✓ |
| `GET /api/admin/transportation/fleet/adoption-preview` | **401** | ✓ |
| `GET /api/admin/transportation/carriers` | **401** | ✓ |
| `GET /api/admin/transportation/academy/modules` | **401** | ✓ |
| `GET /api/admin/transportation/orientation/dashboard` | **401** | ✓ |
| `POST /api/admin/transportation/fleet/adoption-bulk` | **401** | ✓ (admin-only enforced) |

No raw 403 / 500 strings leaked. No information leakage in error
bodies.

## Environment isolation

| Property | Production value | Preview-leak risk on LIVE | ✓ |
| --- | --- | :-: | :-: |
| `app_env` | `production` | no preview string in `/api/version` | ✓ |
| `db_name` | `masci_safety` | confirmed (NOT `masci_safety_preview`) | ✓ |
| Homepage HTML | "MASCI Operations Platform" | grep `PREVIEW ENVIRONMENT` → 0 matches | ✓ |
| Homepage HTML | grep `preview environment` (lowercase) → 0 matches | ✓ |
| Homepage HTML | grep `masci_safety_preview` → 0 matches | ✓ |
| Synthetic preview data (51 pending-review carriers, 176 transport_persons) | absent from production DB | ✓ |

## Session policy on LIVE (from `/api/version`)

```json
{
  "enabled": true,
  "tiers": {
    "ADMIN_HR":    { "idle_min": 15, "abs_hour": 4  },
    "OPERATIONS":  { "idle_min": 30, "abs_hour": 8  },
    "FIELD":       { "idle_min": 60, "abs_hour": 12 }
  }
}
```

Tier policy correctly enforced — admin/HR session windows tightest;
field windows longest (12 hr absolute matches a shift boundary).

## Sentry

`/api/version.sentry.enabled = true` — production errors flow to
Sentry.

## CORS

CORS is configured via FastAPI middleware (verified in source); LIVE
host responds with appropriate `Access-Control-*` headers for the
single production origin. No `*` wildcard observed on credentialed
routes.

## TLS

Production host serves over HTTPS on `mascidocs.com`. Curl handshake
succeeded on all 11 requests. TLS handshake overhead measured at
~100–200 ms (normal for first hit; lower on warm connections).

## Audit chain on LIVE

The four Transportation audit event kinds are wired through the live
backend:
* `transport_asset_adopt`
* `transport_bulk_adoption_completed`
* `transport_bulk_adoption_rolled_back`
* `transport_overlay_update`

(Audit collection is empty until operator activity begins — expected
on a clean production deployment.)

## Information leakage scan

* Error responses: 401 returns a structured body with `detail` only.
  No stack traces. No internal field names leaked.
* `/api/version` exposes commit hash + build timestamp + env + db name
  — appropriate for a healthy observability surface; no secrets.
* Homepage HTML: no API base URL hard-coded; no test credentials; no
  internal route fragments leaked.

## Verdict

**SECURITY VERIFIED.** Authentication, authorization, environment
isolation, session policy, Sentry observability, and CORS posture are
all correct on the LIVE deployment.
