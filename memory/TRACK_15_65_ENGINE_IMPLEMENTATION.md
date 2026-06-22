# TRACK 15.65 — Engine Implementation (Phases 3 + 5)

**Date:** 2026-06-22  
**Files shipped:**
* `backend/email_routing_v2.py` — new resolver, audit, legacy shim.
* `backend/scripts/track_15_65_seed_email_routes.py` — idempotent seed.
* `backend/scripts/track_15_65_parity_verify.py` — parity harness.
* `backend/safety_digest.py` — Wave-1 send-site migration.
* `backend/health_monitor.py` — Wave-1 send-site migration.

## 1. Storage / data model

**Collection:** `email_routes`

```json
{
  "_id":           "masci::SAFETY_FORMS_TO",
  "tenant_key":    "masci",
  "route_key":     "SAFETY_FORMS_TO",
  "display_name":  "Safety Forms Distribution",
  "description":   "Equipment Issuance / Training / Return.",
  "category":      "compliance",
  "severity":      "info",
  "to":            ["safety@mascigc.com", "jaymn.judd@mascigc.com"],
  "cc":            [],
  "bcc":           [],
  "from_email":    null,
  "reply_to":      null,
  "enabled":       true,
  "critical":      false,
  "owner_role":    "Safety Manager",
  "fallback_env_keys": ["SAFETY_FORMS_EMAIL_TO"],
  "legacy_key":    "safety_forms_to",
  "source":        "seed",
  "version":       1,
  "created_at":    "...",
  "updated_at":    "...",
  "updated_by":    "track_15_65_seed",
  "last_tested_at": null,
  "last_test_status": null
}
```

Composite `_id` (`tenant::route`) avoids index gymnastics across multiple tenants and is naturally unique.

**Audit collection:** `email_routing_audit_v2` (append-only) with row schema documented in `TRACK_15_65_EMAIL_AUDIT_LOGGING.md`.

**Indexes (added by seed script `--apply`):**
* `email_routes`: `(tenant_key, route_key)`.
* `email_routing_audit_v2`: `(tenant_key, ts desc)`.

No mutation of `email_routing_config` (the legacy collection) and no mutation of `email_audit`. The new engine is **strictly additive**.

## 2. Resolver behaviour (recap)

```
EMAIL_ROUTING_V2=false  →  resolve(...) returns legacy_provider() verbatim. source="legacy".
EMAIL_ROUTING_V2=true   →  DB doc → env fallback → legacy fallback → hard-fail on critical+empty.
```

Live proof (recorded in this session):

```
OFF: source=legacy to=['safety@mascigc.com']
ON:  source=db     to=['jaymn.judd@mascigc.com']   critical=True
```

## 3. Critical-route guard
For every route flagged `critical=true`:
1. The seed script REFUSES to write the doc with an empty `to` list.
2. The resolver RAISES `UnconfiguredCriticalRouteError` if V2 resolution lands on an empty list (no silent send to nobody, no silent send to "safety@mascigc.com" as a hidden default).
3. The parity harness reports `critical_empty` count separately — non-zero fails the harness exit code.

## 4. Cache
* 60-second in-process TTL on `email_routes` reads.
* `invalidate_cache()` exposed for tests and for any future admin PUT.

## 5. Legacy back-compat
`email_routing_v2.legacy_get_value(db, legacy_key)` is a drop-in replacement for `email_routing.get_value`:
* Flag OFF → delegates to the original.
* Flag ON  → consults the new catalog via `LEGACY_TO_NEW`; falls back to the original on empty.

No existing caller is required to change. The 6 callers of `email_routing.get_value` (in `pm_routing.py`, `routes/safety_forms.py`, `routes/field_leadership.py`, `server.py` × 3) continue to compile.

## 6. Lint
`mcp_lint_python` returns `No lint errors found` for all three touched files (`email_routing_v2.py`, `safety_digest.py`, `health_monitor.py`).

## 7. Hard-rule compliance (Phases 3 + 5)
* ✅ Extended existing infrastructure — did not duplicate.
* ✅ Additive collections — no destructive migration.
* ✅ No mutation of historical email audit rows.
* ✅ Backward-compatible (legacy provider passes through unchanged when flag is OFF).
* ✅ Critical routes hard-fail on empty resolution; no silent catch-all to MASCI inboxes.
