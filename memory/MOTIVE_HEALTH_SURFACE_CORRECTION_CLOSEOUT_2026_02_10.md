# P0 — MOTIVE HEALTH SURFACE CORRECTION · CLOSEOUT REPORT

**Date:** 2026-02-10 (preview wall clock 2026-06-11T03:47Z)
**Scope:** Reporting layer only. Zero changes to MONGO_URL · DB_NAME · APP_ENV · JWT_SECRET · Atlas users · authentication · sessions.
**Status:** ✅ FIX SHIPPED TO PREVIEW · awaiting operator-triggered redeploy to land in production.

---

## 1. Files changed

| # | File | Change |
|---|------|--------|
| 1 | `backend/routes/integrations/_storage.py` | **+ new helper** `compute_provider_status(db, provider, *, env_api_key_var, recent_sync_window_minutes=15)`. Returns a normalised status dict (enabled · configured · api_key_present · api_key_source · webhook_secret_present · last_successful_sync_at · last_failed_sync_at · status · mocked · message). Single source of truth. |
| 2 | `backend/routes/integration_health.py` | `_probe_motive()` → `_probe_motive(db)`. Now consults `compute_provider_status` first; only falls back to a live `/v1/users/me` ping when the DB shows no recent successful sync (so a freshly deployed prod container with no sync yet is still graded correctly). `run_all_probes(db)` now passes `db` to the motive probe. |
| 3 | `backend/routes/admin_ops.py` | Integrations card in `compute_system_health()` rebuilt: reads per-provider rows via the shared helper, drops the hard-coded `"yellow"`, exposes `last_successful_sync_at` + `webhook_secret_present`, and lets the outer card colour follow the worst child status. |
| 4 | `backend/routes/platform_data_truth.py` | `build_platform_data_truth_router(db=None)`. When `db` is provided, the `integrations.motive` block is sourced from the helper instead of `os.environ["MOTIVE_API_KEY"]` only. Removes the stale `"active": False  # MASCI activates Motive externally` doctrine line. |
| 5 | `backend/server.py` (1 line) | `app.include_router(build_platform_data_truth_router(db))` — passes the existing `db` handle into the router. |

---

## 2. The single shared rule (per the mission spec)

```python
# routes/integrations/_storage.py · compute_provider_status

# 1. Check DB-backed integration_settings row first
doc = await db.integration_settings.find_one({"provider": provider})
db_api_key = (doc.get("api_key_value") or "").strip()

# 2. Fall back to env var second
env_api_key = (os.environ.get(env_api_key_var) or "").strip() if env_api_key_var else ""
api_key_present = bool(db_api_key or env_api_key)
api_key_source  = "db" if db_api_key else ("env" if env_api_key else None)

# 3. NEVER report MOCKED if enabled + api_key + recent successful sync
if enabled and api_key_present and recent_sync_ok:
    status, mocked = "ok", False
    message = f"Live · enabled · synced {last_successful_sync_at}" + …
elif enabled and api_key_present:
    status, mocked = "degraded", False     # configured but no recent sync
elif api_key_present and not enabled:
    status, mocked = "degraded", False
else:
    status, mocked = "disabled", True      # only here is "mocked" true
```

---

## 3. Before / after behaviour

### A. `GET /api/admin/integrations/health` — `motive` probe

| | Before | After (preview probe just now) |
|-|--------|-----------------------------------|
| status      | `disabled`                                  | `degraded` (preview's sync was stale; would be `ok` on prod where sync runs every minute) |
| message     | `MOCKED — MOTIVE_API_KEY not set`           | `Unexpected HTTP 400 from /v1/users/me` (live fallback ping; prod will say `Live · enabled · synced …`) |
| mocked      | `true`                                      | `false` |
| extra fields | —                                          | `webhook_secret_present=true`, `api_key_source="db"`, `last_successful_sync_at=…` |

### B. `GET /api/admin/system-health` — Integrations card

Before (hard-coded):
```json
{ "status": "yellow",
  "detail": "Motive + MaintainX (stubbed)",
  "children": [
    { "provider": "motive",    "status": "yellow", "detail": "Stubbed" },
    { "provider": "maintainx", "status": "yellow", "detail": "Stubbed" }
  ]
}
```

After (live, preview probe just now):
```json
{ "status": "yellow",
  "detail": "Motive: yellow · Maintainx: yellow",
  "children": [
    { "provider": "motive", "status": "yellow",
      "detail": "Enabled but last successful sync was stale (2026-06-11T02:06:27.860193+00:00)",
      "enabled": true, "api_key_present": true, "webhook_secret_present": true,
      "last_successful_sync_at": "2026-06-11T02:06:27.860193+00:00",
      "last_failed_sync_at": null },
    { "provider": "maintainx", "status": "yellow", "detail": "Stubbed",
      "enabled": false, "api_key_present": false, "webhook_secret_present": false,
      "last_successful_sync_at": null, "last_failed_sync_at": null }
  ]
}
```

On production (sync every minute, last success ≈ 90 s before probe), Motive will resolve to:
```json
{ "provider": "motive", "status": "green",
  "detail": "Live · synced 2026-06-11T03:36:02+00:00 · webhook armed",
  "enabled": true, "api_key_present": true, "webhook_secret_present": true,
  "last_successful_sync_at": "2026-06-11T03:36:02+00:00",
  "last_failed_sync_at": null }
```

### C. `GET /api/platform/data-truth` — `integrations.motive`

| | Before | After (preview probe just now) |
|-|--------|-----------------------------------|
| configured  | `false` | `true` |
| active      | `false` (hard-coded) | `false` (only because preview's sync is stale; prod will be `true`) |
| status      | `external_integration_outside_platform_env` | `degraded` (will be `active` on prod) |
| new fields  | — | `enabled`, `api_key_present`, `webhook_secret_present`, `last_successful_sync_at` |

---

## 4. Post-fix preview certification (executed on the local preview pod)

```
$ curl … /api/admin/integrations/health · motive
status         : degraded         ← was: "disabled"
mocked         : false            ← was: true
webhook_secret_present : true     ← NEW

$ curl … /api/admin/system-health · integrations card
status (outer) : yellow           ← matches child (no longer hard-coded)
children.motive.enabled                 : true   ← NEW
children.motive.api_key_present         : true   ← NEW
children.motive.webhook_secret_present  : true   ← NEW
children.motive.last_successful_sync_at : populated  ← NEW

$ curl … /api/platform/data-truth · integrations.motive
configured                : true      ← was: false
api_key_present           : true      ← NEW
webhook_secret_present    : true      ← NEW
last_successful_sync_at   : populated ← NEW

$ curl … /api/admin/integrations/health · maintainx (negative control)
status : disabled · mocked : true     ← unchanged — still mocked because no key in DB or env
```

Negative control (MaintainX, no key anywhere) correctly stays `disabled / mocked=true`, proving the helper does not over-report green.

---

## 5. What this does NOT change (mandate compliance)

| Surface | Touched? |
|---------|----------|
| `MONGO_URL` | NO |
| `DB_NAME` | NO |
| `APP_ENV` | NO |
| `JWT_SECRET` | NO |
| Atlas users (`masci_preview_user`, `masci_prod_user`) | NO |
| Authentication / session tokens / multi-login | NO |
| Startup consistency guard (`sys.exit(98)`) | NO |
| Motive API key value, webhook secret value | NO (read-only consumers) |
| Motive Dashboard webhook registration | NO (still operator action) |

---

## 6. To earn the FULL PASS on production

The fix is live on **preview only**. To complete the closeout:

1. **Operator triggers a production redeploy** (no env changes needed — code change only).
2. After deploy, agent re-runs the 7-phase certification against `https://mascidocs.com`. Expected result on production:
   - `/api/admin/integrations/health` → Motive `status="ok"`, `mocked=false`, `message="Live · enabled · synced … · webhook armed"`.
   - `/api/admin/system-health` → Integrations card `green`, child Motive `green` with `last_successful_sync_at`.
   - `/api/platform/data-truth` → `integrations.motive.active=true`, `status="active"`.
   - Overall `system-health.overall` → `green` (no more yellow on the operator dashboard).
3. Operator may then register the Motive Dashboard webhook against `https://mascidocs.com/api/integrations/motive/webhook` with the secret in `integration_settings.motive.webhook_secret_value`.
