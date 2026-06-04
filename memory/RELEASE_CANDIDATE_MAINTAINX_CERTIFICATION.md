# RELEASE CANDIDATE · MAINTAINX SAFETY CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · State of MaintainX integration

| Layer | Status |
| --- | --- |
| `MAINTAINX_API_KEY` | UNSET (empty default in `backend/.env`) |
| `MAINTAINX_BASE_URL` | `https://api.getmaintainx.com/v1` (safe default) |
| `MAINTAINX_SYNC_ENABLED` | `false` |
| `MAINTAINX_WRITE_ENABLED` | `false` |
| `MaintainxClient.create_asset/update_asset/delete_asset` | raise `MaintainxWriteDisabled` regardless of env flag (unit-tested) |
| Webhook handler | hardened scaffold; refuses to process without `webhook_secret_value` set |
| Live MaintainX traffic | 0 calls in this preview (no API key) |
| MaintainX data | not touched — zero outbound mutation possible |
| MASCI equipment data | not touched — read-only `find()` only |

## 2 · Admin Integration Center loads cleanly

- Route `/admin/integrations` renders.
- "MaintainX · Read-First" tab (`ic-tab-maintainx-p0`) opens; both sub-sections render:
  - `mx-p0-root` (Configuration / Test / Dry-Run / Saved Reports)
  - `mx-coverage-root` (Defect Source Coverage section)
- Screenshot capture at `/tmp/rc_smoke.png` shows the orange preview banner + all four card sections.

## 3 · API-key safety

| Check | Verdict |
| --- | --- |
| API key never appears in DOM | YES (HTML scrub returned `LEAKS_FOUND = []`) |
| API key never logged in full | YES (`mask_key()` everywhere; unit-tested) |
| `public_view()` exposes only `api_key_present` + `api_key_masked` + `api_key_last4` | YES |
| Missing key state handled cleanly | YES (UI renders "No — set MAINTAINX_API_KEY in env" with amber XCircle) |
| Test connection handles no-key state | YES (returns `{ok:false, status:"missing_api_key"}` rather than throwing) |
| Frontend has no input field for the secret | YES (no `<Input>` for API key on any surface) |

## 4 · Dry-run safety

Live `POST /api/admin/maintainx/p0/dryrun`:

```
totals.maintainx_assets_pulled = 0        (no key → no pull, graceful)
totals.masci_equipment_count    = 589      (read from real preview db)
writes_performed.maintainx       = 0
writes_performed.equipment_master = 0
writes_performed.asset_mappings   = 0
writes_performed.fleet_defects    = 0
saved = false
```

Backend unit tests verify the dry-run produces zero writes under both `save_report=False` (no audit row) and `save_report=True` (one audit row in `maintainx_dryrun_reports` only — never operational collections).

## 5 · Defect Source Coverage safety

Live `GET /api/admin/maintainx/defect-coverage`:

```
totals.open_defects        = 138
totals.out_of_service      = 110
writes_performed.{maintainx, equipment_master, fleet_defects,
                  equipment_inspections, asset_holds, asset_mappings}
                                    = 0 / 0 / 0 / 0 / 0 / 0
```

Coverage UI renders a green footer panel asserting `writes_performed: mx=0 · eq_master=0 · fleet_defects=0 · inspections=0 · holds=0 · mappings=0` on every refresh. Verified live.

## 6 · Shop and Dispatch surfaces

- **Shop Hub** — `ShopMaintainxReadinessTile` renders a 4-cell read-only display (Ready / Blocked / Duplicate Risk / Awaiting RTS). No action buttons. No MaintainX create / update / delete affordances.
- **Dispatch Hub** — `DispatchEquipmentMaintenanceIndicator` renders only when `out_of_service > 0`. Single line of text + a `/dispatch/board` link. No MaintainX-specific UI. No buttons that initiate MaintainX traffic.

Both consume the same portal-gated `GET /api/integrations/maintainx/defect-coverage` endpoint.

## 7 · Write-disable layered defence

| Layer | Status |
| --- | --- |
| Env: `MAINTAINX_WRITE_ENABLED` | `false` |
| Code: `MaintainxClient.{create,update,delete}_asset` | raises `MaintainxWriteDisabled` regardless of env (unit-tested as `test_client_write_methods_raise`) |
| No write-callsite in the codebase | `grep -rn "client.create_asset\|client.update_asset\|client.delete_asset" /app/backend` returns zero matches |
| Webhook handler | will not process inbound webhooks without `webhook_secret_value` set |

If any operator or developer attempts to enable writes, the code itself refuses until that explicit Stage 6 work is undertaken with operator authorisation.

## 8 · Compliance with directive's NO-GO clause

The directive's "RETURN NO GO" trigger is *"if any MaintainX write can occur"*. We can affirmatively state:

- **Zero** MaintainX write code exists in this release.
- **Zero** new write callsite was introduced.
- **Zero** write surfaces are exposed in any UI.
- **Zero** write paths can be reached even by flipping env vars to `true` — the client still raises.

The clause does NOT trigger. **GO.**

## 9 · Verdict — MaintainX Safety

```
MAINTAINX SAFETY CERTIFICATION  :  PASS

  Admin Integration Center loads          : YES
  API key not exposed                     : VERIFIED (HTML scrubbed)
  Missing key state                       : GRACEFUL
  Test connection no-key                  : GRACEFUL
  Dry-run writes_performed                : 0 / 0 / 0 / 0 / 0
  Coverage writes_performed                : 0 / 0 / 0 / 0 / 0 / 0
  Shop Readiness tile                      : loads · read-only
  Dispatch indicator                       : loads · read-only
  MAINTAINX_WRITE_ENABLED                  : false
  MAINTAINX_SYNC_ENABLED                   : false
  Write-disable layered defence            : 3 layers (env + code + no callsite)
  NO-GO trigger satisfied                  : NO (no MX writes possible)
```
