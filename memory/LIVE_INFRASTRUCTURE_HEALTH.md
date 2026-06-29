# LIVE Infrastructure Health — mascidocs.com

**Verdict:** ✅ **HEALTHY**

---

## /api/health (LIVE)

```
GET https://mascidocs.com/api/health
HTTP 200 · 0.349 s

{
  "ok": true,
  "service": "masci-hub",
  "ts": "2026-06-29T16:11:04.314711+00:00"
}
```

## /api/version (LIVE)

```
GET https://mascidocs.com/api/version
HTTP 200 · 0.218 s

{
  "service": "masci-hub",
  "commit": "c95b0d90c88e",
  "built_at": "2026-06-29T15:41:17.893889+00:00",
  "source_hash": "c95b0d90c88e246ae7a45d7a77202fad",
  "release": "c95b0d90c88e246ae7a45d7a77202fad",
  "started_at": "2026-06-29T15:41:17.893889+00:00",
  "uptime_s": 1786,
  "session_timeouts": {
    "enabled": true,
    "tiers": {
      "ADMIN_HR":    { "idle_min": 15, "abs_hour": 4  },
      "OPERATIONS":  { "idle_min": 30, "abs_hour": 8  },
      "FIELD":       { "idle_min": 60, "abs_hour": 12 }
    }
  },
  "sentry":  { "enabled": true },
  "app_env": "production",
  "db_name": "masci_safety"
}
```

## /api/cluster/capacity (LIVE)

```
GET https://mascidocs.com/api/cluster/capacity
HTTP 200 · 0.270 s

{
  "ok": true,
  "tier_quota_mb": 10240,
  "storage_used_mb": 485.73,
  "storage_used_pct": 4.7,
  "severity": "ok",
  "dbs": { "masci_safety": 485.73 },
  "ts": "2026-06-29T16:11:04.873060+00:00"
}
```

## Environment isolation — VERIFIED on LIVE

| Property | Expected | Actual on LIVE | ✓ |
| --- | --- | --- | :-: |
| `app_env` | `production` | `production` | ✓ |
| `db_name` | `masci_safety` | `masci_safety` (NOT `masci_safety_preview`) | ✓ |
| Preview banner in HTML | absent | absent (verified by HTML grep) | ✓ |
| Sentry | enabled | enabled | ✓ |
| Session timeouts | configured (3 tiers) | configured (3 tiers) | ✓ |

## Uptime + release

| Metric | Value |
| --- | --- |
| Deployment uptime | **1786 s ≈ 30 min** at certification time |
| Release / commit | `c95b0d90c88e` |
| Built at | 2026-06-29T15:41:17 UTC |
| Started at | 2026-06-29T15:41:17 UTC (cold start aligned) |
| Now | 2026-06-29T16:11:04 UTC |

## Capacity headroom

| Resource | Used | Tier | Headroom |
| --- | ---: | ---: | ---: |
| Atlas DB storage | 485.73 MB | 10240 MB | **95.3%** free |
| Severity | "ok" | — | n/a |

## Health endpoints not exposed

* `/api/health/ready` → 404 (not implemented; canonical is `/api/health`)
* `/api/health/live` → 404 (not implemented; canonical is `/api/health`)

These are not blockers — `/api/health` is the documented contract and
returns 200.

## Verdict

**HEALTHY.** Live infrastructure is correctly configured for
production. Environment isolation verified. Atlas storage has 95%
headroom. Sentry on. Session policies in place.
