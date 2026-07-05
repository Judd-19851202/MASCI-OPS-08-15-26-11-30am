# AI-ADMIN-001 · API Contract

**Prefix:** `/api/admin/ai`
**Auth:** `require_admin_strict` — an **Admin token** in `X-Admin-Token`.
PM tokens are rejected. Unauthenticated calls return **401**.
**Never returns raw API key values.** Provider keys are surfaced as
booleans only.

---

## 1. `GET /api/admin/ai/config/status`

Sanitised deployment-scope switchboard snapshot. Identical envelope to
`GET /api/ai/gateway/status`.

### Response 200

```json
{
  "gateway_enabled": true,
  "tenant_ai_default_enabled": false,
  "default_provider": "anthropic",
  "default_text_model": "claude-sonnet-4-5-20250929",
  "default_vision_provider": "openai",
  "default_vision_model": "gpt-5.2-vision",
  "resolved_selected_provider": null,
  "resolved_fallback_provider": null,
  "resolved_provider_available": false,
  "providers": {
    "anthropic": {
      "flag": "AI_PROVIDER_ANTHROPIC_ENABLED",
      "enabled": false,
      "key_env": "ANTHROPIC_API_KEY",
      "key_present": false
    },
    "openai":    { "flag": "AI_PROVIDER_OPENAI_ENABLED",    "enabled": false, "key_env": "OPENAI_API_KEY",    "key_present": false },
    "google":    { "flag": "AI_PROVIDER_GOOGLE_ENABLED",    "enabled": false, "key_env": "GOOGLE_AI_API_KEY", "key_present": false }
  },
  "modules": {
    "daily_report_summary":  { "deployment_flag": "AI_DAILY_REPORT_SUMMARY_ENABLED", "deployment_enabled": false, "tenant_default_flag": "TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED", "tenant_default_enabled": false },
    "photo_intelligence":    { ... },
    "pm_intelligence":       { ... },
    "admin_intelligence":    { ... },
    "safety_intelligence":   { ... },
    "translation":           { ... }
  },
  "transport": {
    "timeout_ms": 30000,
    "max_retries": 2,
    "failover_enabled": true
  }
}
```

### Errors

- **401** — no admin token, invalid admin token, or PM token supplied.

---

## 2. `GET /api/admin/ai/tenants`

List of tenants known to the AI switchboard.

### Response 200

```json
{
  "tenants": [
    {
      "tenant_id": "masci",
      "tenant_name": "MASCI (default)",
      "tenant_ai_enabled": false,
      "has_override_doc": false,
      "updated_at": null,
      "updated_by": null
    }
  ]
}
```

- `has_override_doc=false` means the tenant is running on env defaults —
  no doc in `tenant_ai_capabilities`.

---

## 3. `GET /api/admin/ai/tenants/{tenant_id}/capabilities`

Resolved capabilities + tenant override document for a single tenant.

### Response 200

```json
{
  "tenant_id": "masci",
  "tenant_name": "MASCI (default)",
  "has_override_doc": false,
  "overrides": {},
  "modules": {
    "daily_report_summary": {
      "module": "daily_report_summary",
      "tenant_id": "masci",
      "enabled": false,
      "reason_disabled": "ai_gateway_disabled_global",
      "selected_provider": null,
      "fallback_provider": null,
      "provider_available": false,
      "tenant_ai_enabled": false
    },
    "photo_intelligence":  { ... },
    "pm_intelligence":     { ... },
    "admin_intelligence":  { ... },
    "safety_intelligence": { ... },
    "translation":         { ... }
  }
}
```

### Errors

- **400** — empty `tenant_id`.
- **401** — no/invalid admin token.

---

## 4. `PUT /api/admin/ai/tenants/{tenant_id}/capabilities`

Upsert a tenant AI override doc.

### Headers

- `X-Admin-Token` — required.
- `X-Admin-Actor` — optional. Human email or identifier recorded in
  `updated_by` and the audit entry (fallback: `"admin"`).

### Request body — all fields optional; empty payload rejected

```json
{
  "tenant_ai_enabled": true,
  "daily_report_summary_enabled": true,
  "photo_intelligence_enabled": false,
  "pm_intelligence_enabled": false,
  "admin_intelligence_enabled": false,
  "safety_intelligence_enabled": false,
  "translation_enabled": true,
  "note": "Pilot enrolment on 2026-02-14."
}
```

Extra fields (e.g. `ANTHROPIC_API_KEY`, `tenant_id`) are **silently
dropped** by the pydantic model + allow-list.

### Response 200

```json
{
  "ok": true,
  "tenant_id": "masci",
  "overrides": {
    "tenant_id": "masci",
    "tenant_ai_enabled": true,
    "daily_report_summary_enabled": true,
    "translation_enabled": true,
    "version": 1,
    "updated_at": "2026-02-14T18:00:00+00:00",
    "updated_by": "jaymn.judd@mascigc.com",
    "created_at": "2026-02-14T18:00:00+00:00",
    "note": "Pilot enrolment on 2026-02-14."
  },
  "changed_fields": [
    "tenant_ai_enabled",
    "daily_report_summary_enabled",
    "translation_enabled"
  ],
  "modules": { /* recomputed resolver verdicts */ }
}
```

### Errors

- **400** — payload contains none of the seven allow-listed fields.
- **401** — no/invalid admin token.
- **500** — Mongo write failure (surfaced as `tenant update failed: …`).

### Side effects

- Writes/updates a doc in `tenant_ai_capabilities`.
- Appends an entry to `tenant_ai_capability_audit` with:
  - `tenant_id`, `actor`, `before`, `after`, `changed_fields`, `note`,
    `timestamp`, `request_id`, `ip`, `user_agent`.
  - No API key values.

---

## 5. `GET /api/admin/ai/tenants/{tenant_id}/audit`

Recent AI capability audit entries for a tenant, newest first.

### Query params

- `limit` (default 50, max 200).

### Response 200

```json
{
  "tenant_id": "masci",
  "entries": [
    {
      "tenant_id": "masci",
      "actor": "jaymn.judd@mascigc.com",
      "before": {},
      "after": { "tenant_ai_enabled": true },
      "changed_fields": ["tenant_ai_enabled"],
      "note": "Pilot enrolment on 2026-02-14.",
      "timestamp": "2026-02-14T18:00:00+00:00",
      "request_id": null,
      "ip": "10.0.0.4",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

---

## 6. `POST /api/admin/ai/providers/{provider}/test`

Safe, bounded provider readiness check. **Does not make a live
provider call.** Reports whether the provider is *configurable* given
current flags + key presence.

### Path params

- `provider` — one of `anthropic`, `openai`, `google`.

### Response 200

```json
{
  "provider": "anthropic",
  "flag_env": "AI_PROVIDER_ANTHROPIC_ENABLED",
  "flag_enabled": true,
  "key_env": "ANTHROPIC_API_KEY",
  "key_present": true,
  "status": "ready",
  "note": "This endpoint does NOT issue a live provider call. Configure flags/keys via the Emergent Secrets UI, then re-check status."
}
```

`status` is one of:
- `ready` — flag on + key present.
- `missing_key` — flag on, key blank.
- `flag_disabled` — flag off, key present.
- `unavailable` — flag off and key blank.

### Errors

- **404** — unknown provider name.
- **401** — no/invalid admin token.

---

## Universal contract

- No endpoint on this router ever returns a raw API key value.
- No endpoint on this router accepts a raw API key value in a request
  body — provider keys are managed only through the Emergent Secrets UI.
- Every mutation is audit-logged best-effort (a failed audit write does
  not fail the mutation).
- Every read/write is tenant-scoped via `{tenant_id}` in the path —
  there is no cross-tenant bulk mutation surface.
