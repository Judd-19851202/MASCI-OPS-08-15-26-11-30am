# AI-CONFIG-001 · Tenant Optionality (TENANT_AI_ENABLED Amendment)

**Track:** AI-CONFIG-001 · TENANT_AI_ENABLED amendment
**Date closed:** 2026-02
**Status:** ✅ Delivered — 17/17 lock tests passing.

---

## 1. Doctrine

Every tenant is an **island**. One tenant enabling AI must never affect
another tenant. A tenant on the platform can be:

- Fully off (no AI at all — the "quiet tier"),
- Partially on (e.g. Photo Intelligence only),
- Fully on (all modules enabled).

The tenant is the atomic unit of consent. The deployment operator gates
the outer envelope (which modules and which providers are even *available*
to be enabled). The tenant admin — or platform operator on the tenant's
behalf — flips per-module switches within the envelope the deployment
allows.

## 2. The five-link chain

```
    Global gateway               →  AI_GATEWAY_ENABLED
        │
        ▼
    Tenant enrollment            →  Mongo tenant_ai_capabilities[t].tenant_ai_enabled
                                     ↳ falls back to TENANT_AI_ENABLED env default
        │
        ▼
    Module (deployment scope)    →  AI_<MODULE>_ENABLED
        │
        ▼
    Module (tenant scope)        →  Mongo tenant_ai_capabilities[t].<module>_enabled
                                     ↳ falls back to TENANT_AI_<MODULE>_ENABLED env
        │
        ▼
    Provider + key               →  AI_PROVIDER_<X>_ENABLED AND <X>_API_KEY set
```

Every link must pass. Any single `false` returns
`Capability.enabled=False` with a `reason_disabled` code.

## 3. Mongo schema — `tenant_ai_capabilities`

Optional collection. **Absence of a doc for a tenant is normal** — the
env-level defaults apply. Create a doc only when a tenant needs to
diverge from the deployment defaults.

```json
{
  "tenant_id": "masci",
  "tenant_ai_enabled": true,
  "daily_report_summary_enabled": true,
  "photo_intelligence_enabled": true,
  "pm_intelligence_enabled": false,
  "admin_intelligence_enabled": false,
  "safety_intelligence_enabled": false,
  "translation_enabled": true,
  "notes": "MASCI opted into DR summary + photo + translation on 2026-02-14.",
  "updated_at": "2026-02-14T18:00:00Z",
  "updated_by": "jaymn.judd@mascigc.com"
}
```

Field name convention: env var `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED`
maps to Mongo key `photo_intelligence_enabled`. Enforced by the
`_snake_field()` helper in `services/ai_gateway/capabilities.py` and
locked by test `test_snake_field_helper_maps_env_names_to_doc_keys`.

## 4. Tenant states

### 4.1 Silent (default)

- No doc in `tenant_ai_capabilities`.
- `TENANT_AI_ENABLED` env default = `false`.
- Every module returns `reason_disabled="tenant_ai_disabled"`.
- Field UI is byte-identical to standard production.
- Daily Reports submit, ODS ingests, dashboards render.

### 4.2 Enrolled — envelope on, all modules off

```json
{ "tenant_id": "acme", "tenant_ai_enabled": true }
```

- Passes link 2. All module-scope flags fall back to their env defaults
  (typically `false`), so every module still returns
  `reason_disabled="module_disabled_tenant:<module>"`.
- Behavior identical to Silent from a user perspective.
- Used to "pre-enroll" a tenant while modules are still being staged.

### 4.3 Enrolled — selective modules

```json
{
  "tenant_id": "widgets",
  "tenant_ai_enabled": true,
  "photo_intelligence_enabled": true
}
```

- Passes links 2 and 4 for `photo_intelligence`. Every other module
  returns `reason_disabled="module_disabled_tenant:<module>"`.
- Lock test `test_tenant_module_flag_independent_of_other_modules`
  proves this granularity works.

### 4.4 Enrolled — full stack

```json
{
  "tenant_id": "flagship",
  "tenant_ai_enabled": true,
  "daily_report_summary_enabled": true,
  "photo_intelligence_enabled": true,
  "pm_intelligence_enabled": true,
  "admin_intelligence_enabled": true,
  "safety_intelligence_enabled": true,
  "translation_enabled": true
}
```

- Assumes deployment has all module + provider flags on and keys
  populated. If deployment has, say, `AI_ADMIN_INTELLIGENCE_ENABLED=false`,
  admin intelligence stays off for this tenant too
  (`reason_disabled="module_disabled_global:admin_intelligence"`).
- Lock test `test_summary_only_does_not_enable_photo_intelligence`
  proves deployment gates dominate tenant flags.

## 5. Tenant isolation guarantees

- Every AI callsite calls `resolve_ai_capabilities(db, tenant_id, module)`
  and passes the caller's `tenant_id`. There is no ambient/global
  "current tenant".
- Lock test `test_two_tenants_can_have_different_ai_state` proves that
  with identical deployment config, tenant A can have AI on and tenant B
  can have AI off, and the resolver returns divergent verdicts.
- ODS ingestion and Daily Report submission are tenant-agnostic — they
  never call the resolver. The resolver is only consulted when a
  potential AI callsite is about to fire.

## 6. Operator playbook

**Enrol a new tenant into AI:**

1. Confirm deployment has `AI_GATEWAY_ENABLED=true` and the desired
   module flags on.
2. Confirm providers on: at least one of
   `AI_PROVIDER_ANTHROPIC_ENABLED` / `_OPENAI_` / `_GOOGLE_` with a real
   `*_API_KEY` populated via the Emergent Secrets UI.
3. Insert a doc into `tenant_ai_capabilities`:

   ```js
   db.tenant_ai_capabilities.replaceOne(
     { tenant_id: "acme" },
     {
       tenant_id: "acme",
       tenant_ai_enabled: true,
       daily_report_summary_enabled: true,
       photo_intelligence_enabled: true,
       updated_at: new Date(),
       updated_by: "operator@mascigc.com"
     },
     { upsert: true }
   );
   ```

4. Call `GET /api/ai/gateway/status` as admin to sanity-check the
   deployment envelope. The endpoint does not expose per-tenant state
   (by design — one call surfaces deployment posture, tenant state is
   Mongo-native).

**Turn AI off for a tenant instantly:**

```js
db.tenant_ai_capabilities.updateOne(
  { tenant_id: "acme" },
  { $set: { tenant_ai_enabled: false, updated_at: new Date() } }
);
```

Effective on the next call (no restart needed — the resolver reads
Mongo per invocation).

## 7. Invisible Intelligence contract

The field UI **never** exposes AI state to the field user. Whether AI
is on or off, whether tenants are enrolled or not, whether providers
are up or down, the daily job report screen (`/daily/submit`) is
byte-identical.

- No "AI is disabled" banner.
- No greyed-out "AI Summary" button.
- No error toast on `no_provider_available`.

`reason_disabled` codes are for logs, telemetry, and admin dashboards
only.

## 8. References

- Resolver: `/app/backend/services/ai_gateway/capabilities.py`
- Mongo collection: `tenant_ai_capabilities`
- Lock envelope: `/app/backend/tests/test_ai_config_001_capabilities.py`
- Companion docs:
  - `AI_CONFIG_001_SECRET_CONTRACT.md`
  - `AI_CONFIG_001_DISABLED_MODE_PROOF.md`
