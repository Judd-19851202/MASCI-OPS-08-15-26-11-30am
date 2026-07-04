# TRACK 22.1F · Platform Status API — Design & Contract

## Purpose

A permanent, admin-only, read-only runtime attestation surface that lets ops and engineering verify — from inside the running pod — the platform's foundation health, lifespan-migration progress, bytecode-safety posture, email safety posture, and route/OpenAPI counts. Not a widget. Not a temporary migration endpoint. This is the foundation for all future platform-ops visibility.

## Route

```
GET /api/admin/platform/status
```

- **Auth:** `require_admin_strict` (PM tokens are rejected).
- **Side effects:** none.
- **DB writes:** zero.
- **External calls:** zero.
- **Email calls:** zero.
- **Cache-Control:** default (no explicit caching; response is small and cheap).
- **Response shape:** stable JSON — additive field growth allowed across future tracks, no removals without a versioned `attestation_version` bump.

## Backing module

`backend/lib/platform_status.py` (pure functions · no `import resend` at module scope · AST-verified).

Public entry:
```python
from lib.platform_status import platform_status
payload = platform_status(app)
```

## Response schema

```jsonc
{
  "service": "masci-hub",
  "attestation_version": "22.1F",
  "runtime": {
    "app_env": "preview",           // enum: preview | production | (any lower-cased APP_ENV)
    "worker_pid": 4389              // integer — helpful for multi-worker debugging
  },
  "routes": {
    "route_count": 1441,
    "route_methods_total": 1445,
    "openapi_path_count": 1264
  },
  "middleware": {
    "count": 7,
    "cors": {
      "installed": true,
      "explicit_origin_count": 0,       // count only; NEVER the origin strings themselves
      "origin_regex_configured": true,  // boolean — we do NOT return the regex value
      "wildcard_methods": false,
      "wildcard_headers": false,
      "credentials_allowed": true,
      "method_count": 7,
      "header_count": 12
    }
  },
  "lifecycle": {
    "on_startup_legacy_count": 33,
    "on_shutdown_count": 1,
    "registry": {
      "total": 18,
      "by_group": { "index-ensure": 11, "seed": 7 },
      "names_by_group": { "index-ensure": [...], "seed": [...] }   // handler names only
    },
    "migration_progress": {
      "on_startup_legacy_count": 33,
      "lifecycle_steps_count": 18,
      "total_lifecycle_callables": 51,
      "migrated_pct": 35.29,
      "target_groups": {
        "index-ensure":       { "track": "22.1E", "closed": true },
        "seed":               { "track": "22.1F", "closed": true },
        "scheduler-nonemail": { "track": "22.1G", "closed": false },
        "scheduler-email":    { "track": "22.1H", "closed": false },
        "bootstrap-misc":     { "track": "22.1I", "closed": false },
        "readiness":          { "track": "22.1J", "closed": false },
        "shutdown":           { "track": "22.1K", "closed": false }
      }
    }
  },
  "bytecode_fingerprints": {
    "checked": 5,
    "ok_count": 5,
    "drift_count": 0,
    "missing_count": 0,
    "clean": true
  },
  "email_safety": {
    "mode": "strict",                    // enum: off | strict | silent | test
    "resend_sdk_patched": true,
    "live_emails_possible": false
  },
  "readiness": {
    "ready_flag": true                   // app.state.ready — post iter453.6 flip
  },
  "recent_track_closures": ["22.1D", "22.1E", "22.1F"],
  "recommended_next_actions": [
    {
      "priority": "P1",
      "action": "Execute Track 22.1G — migrate non-email schedulers to LIFECYCLE_STEPS.",
      "gate": "..."
    },
    ...
  ]
}
```

## Operational value

The endpoint answers, in one authenticated curl:

1. **Is lifecycle migration progressing?** → `lifecycle.migration_progress.migrated_pct`.
2. **How many handlers remain legacy?** → `lifecycle.on_startup_legacy_count`.
3. **Are the 5 safety-critical bytecode fingerprints clean?** → `bytecode_fingerprints.clean`.
4. **Is email safety active on this pod?** → `email_safety.live_emails_possible`.
5. **Is CORS still explicit (no wildcards)?** → `middleware.cors.wildcard_methods` + `wildcard_headers`.
6. **Is the pod ready to accept writes?** → `readiness.ready_flag`.
7. **What should engineering do next?** → `recommended_next_actions`.
8. **What environment / worker am I probing?** → `runtime.app_env` + `runtime.worker_pid`.

## Extensibility guarantees

- **Additive-only:** future tracks may add fields; existing field semantics are stable within an `attestation_version`.
- **Versioned:** bumping `attestation_version` signals a breaking-shape change; consumers can pin.
- **No hidden shape:** every field visible in the JSON is documented here.
- **No secret ever surfaces:** enforced by unit test (`test_platform_status_payload_shape_no_secrets`).

## Non-goals

- No user-level metrics (nothing per-user, nothing per-record).
- No latency traces (that's Sentry's job).
- No full CORS origin dump (that's the .env's job).
- No connection-string exposure (obvious).
- No DB row counts by collection (would leak load/business signal).

## Verdict

🟢 **DESIGN CERTIFIED.** Powerful, simple, beautiful, trusted, proven, operational, durable, owned.
