# MAINTAINX P0-A · API CLIENT IMPLEMENTATION REPORT

**Date:** 2026-06-04 18:30 UTC
**Sprint:** OMEGA P0-A/P0-B — Read-First MaintainX Asset Integration
**Mode:** READ-FIRST · NO WRITES · NO LIVE WRITE TRAFFIC

---

## 1 · What was built

### Files created
| Path | LOC | Purpose |
| --- | --- | --- |
| `backend/services/maintainx_client.py` | 285 | Hardened read-first HTTP client |
| `backend/routes/integrations/maintainx_p0.py` | 86 | Admin-strict P0 routes |

### File modified
| Path | Change |
| --- | --- |
| `backend/routes/integrations/__init__.py` | +2 imports / +1 registration line — wires the new P0 routes into the existing Integration Center router |
| `backend/.env` | +4 keys (all empty / safe defaults) — `MAINTAINX_API_KEY=`, `MAINTAINX_BASE_URL=https://api.getmaintainx.com/v1`, `MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false` |

No backend service was disabled, no existing routes were edited, no DB schema was altered.

---

## 2 · Client design — `MaintainxClient`

### Public surface
```python
client = MaintainxClient()                     # reads MaintainxConfig.from_env()
client.is_configured()                         # → bool
await client.test_connection()                 # → dict (never raises)
await client.list_assets(page_size=100, max_pages=50)
async for a in client.iter_assets(...):
    ...
# Write methods exist but are HARD-DISABLED:
await client.create_asset(...)                 # → MaintainxWriteDisabled
await client.update_asset(...)                 # → MaintainxWriteDisabled
await client.delete_asset(...)                 # → MaintainxWriteDisabled
```

### Env var contract
| Var | Default | Behaviour |
| --- | --- | --- |
| `MAINTAINX_API_KEY` | `""` (unset) | When empty → `is_configured()` is False; `test_connection()` returns `status="missing_api_key"`; `iter_assets()` raises `MaintainxConfigError` (test 1, 1b) |
| `MAINTAINX_BASE_URL` | `https://api.getmaintainx.com/v1` | Falls back to this default if unset |
| `MAINTAINX_SYNC_ENABLED` | `false` | Read-only kill-switch surfaced via `MaintainxConfig.sync_enabled`; consumers honour it before calling any sync method |
| `MAINTAINX_WRITE_ENABLED` | `false` | Layered safety: even if flipped to `true`, the client's write methods STILL raise `MaintainxWriteDisabled` in this sprint |

### Error classification (HTTP → structured code)
| HTTP | Code | Behaviour |
| --- | --- | --- |
| 200-299 | — | Return `resp.json()` |
| 401 | `unauthorized` | Raise `MaintainxClientError(status=401, code="unauthorized", …)` |
| 403 | `forbidden` | Raise `MaintainxClientError` |
| 408 / network timeout | `timeout` | Raise `MaintainxClientError` |
| 429 | `rate_limited` (carries `retry_after` from `Retry-After` header) | Raise |
| 5xx | `server_error` | Raise |
| Other 4xx | `http_error` | Raise |
| Transport-level | `transport_error` | Raise |

`test_connection()` wraps the above and **never raises**; it returns the structured error as a flat dict.

### Pagination
- Honours both common MaintainX shapes:
  - `{"results": [...], "hasMore": true|false, "next": "<url>"}`
  - bare list (assumes `len(items) >= page_size` means more pages may follow)
- Caps at `max_pages` (default 50, hard-capped at 500) and `page_size` (default 100, hard-capped at 500).
- Stops the moment the first empty page is returned.

### Timeout
- Default `httpx.Timeout(15s)` (configurable via `timeout_s=` constructor arg)
- Wrapped so `TimeoutException` and other `httpx.HTTPError` subclasses surface as structured `MaintainxClientError(code="timeout"|"transport_error")`.

### Structured error logging
- Logger name `backend.services.maintainx_client`.
- Errors include `status`, `code`, `message`, `retry_after`, and a redacted `raw` payload — never the API key.

### Key masking
- `mask_key()` displays `"•"*(len-4) + last4` so admins can confirm the right credential without leaking it.
- `MaintainxConfig.public_view()` returns `api_key_present` (bool) + `api_key_masked` (string) + `api_key_last4` (string) — and **nothing else** about the secret.
- Asserted by test #13 `test_api_key_masked_everywhere`.

---

## 3 · Admin-strict routes added

All under `/api/admin/maintainx/p0/*` (admin-strict gate via the existing `require_admin` dependency):

| Method | Path | Behaviour |
| --- | --- | --- |
| GET | `/admin/maintainx/p0/config` | Returns `MaintainxConfig.public_view()` (api key MASKED) |
| POST | `/admin/maintainx/p0/test` | Calls `MaintainxClient.test_connection()` |
| POST | `/admin/maintainx/p0/dryrun?save={bool}&page_size={n}&max_pages={n}` | Runs the full dry-run pipeline; optionally saves the report dict to `db.maintainx_dryrun_reports` |
| GET | `/admin/maintainx/p0/dryrun-reports` | List saved reports (most recent first, results array stripped for size) |
| GET | `/admin/maintainx/p0/dryrun-reports/{run_id}` | Full saved report including results & missing_in_maintainx arrays |

**No write paths exist** to MaintainX, `equipment_master`, `asset_mappings`, or any other operational collection. The ONLY collection these routes can write to (and only when `?save=true`) is `maintainx_dryrun_reports`, which is a brand-new, isolated audit collection.

---

## 4 · Live preview verification (no API key set)

Run against `https://backup-forensics.preview.emergentagent.com` using admin token:

```http
GET /api/admin/maintainx/p0/config
→ {
    "base_url": "https://api.getmaintainx.com/v1",
    "api_key_present": false,
    "api_key_masked": null,
    "api_key_last4": "",
    "sync_enabled": false,
    "write_enabled": false
  }
```

```http
POST /api/admin/maintainx/p0/test
→ {
    "ok": false,
    "status": "missing_api_key",
    "message": "MAINTAINX_API_KEY not set",
    "config": { …public_view… }
  }
```

```http
POST /api/admin/maintainx/p0/dryrun
→ {
    "id": "<uuid>",
    "totals": {
      "maintainx_assets_pulled": 0,
      "masci_equipment_count": 589,
      "exact_match": 0, "probable_match": 0,
      "possible_duplicate": 0, "conflict": 0,
      "missing_in_masci": 0, "missing_in_maintainx": 0,
      "duplicate_risk_blocked": 0, "duplicate_risk_safe": 0,
      "errors": 0
    },
    "errors": [{"phase": "asset_pull", "skipped": true,
                "reason": "client not configured or connection probe failed"}],
    "saved": false,
    "writes_performed": {
      "maintainx": 0,
      "equipment_master": 0,
      "asset_mappings": 0,
      "fleet_defects": 0
    }
  }
```

**Confirmed: pipeline behaves correctly in the absence of credentials — graceful degradation, structured error, zero writes.**

---

## 5 · Verdict — P0-A

```
P0-A · MAINTAINX API CLIENT  :  COMPLETE

  HTTP client (httpx, async)               : DONE
  Config from env w/ kill-switches          : DONE
  401 / 403 / 429 / 5xx classification      : DONE (unit-tested)
  Pagination support (capped)               : DONE (unit-tested)
  Timeout (15s default)                     : DONE
  Structured error logging (no key leak)    : DONE
  API key masking                           : DONE (unit-tested)
  Write methods hard-disabled               : DONE (unit-tested)
  Admin-strict route surface                : DONE (live-tested)
  Live preview reachability                 : DONE (graceful when key missing)
```

P0-A is implementation-complete and live. The integration **cannot make any outbound MaintainX call** until `MAINTAINX_API_KEY` is populated in `backend/.env` (or via `PATCH /api/admin/integrations/maintainx`, which writes to `integration_settings.maintainx.api_key_value` — though this P0 client reads ONLY from env, not from DB, to keep the safety surface minimal).
