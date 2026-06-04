# MAINTAINX P0 · GO / NO-GO

**Date:** 2026-06-04 18:30 UTC
**Sprint:** OMEGA P0-A/P0-B — Read-First MaintainX Asset Integration
**Decision:** Operator authorisation gate before promoting the read-first scaffold

---

## 1 · Sprint deliverables

| # | Deliverable | Path | Status |
| --- | --- | --- | --- |
| 1 | API client implementation report | `/app/memory/MAINTAINX_P0A_API_CLIENT_REPORT.md` | DONE |
| 2 | Read-only asset pull report | `/app/memory/MAINTAINX_P0B_ASSET_PULL_REPORT.md` | DONE |
| 3 | Asset match report | `/app/memory/MAINTAINX_ASSET_MATCH_REPORT.md` | DONE |
| 4 | Duplicate risk report | `/app/memory/MAINTAINX_DUPLICATE_RISK_REPORT.md` | DONE |
| 5 | Test report | `/app/memory/MAINTAINX_P0_READ_FIRST_TEST_REPORT.md` | DONE (13/13 PASS) |
| 6 | GO / NO-GO (this doc) | `/app/memory/MAINTAINX_P0_GO_NO_GO.md` | DONE |

---

## 2 · Files added / changed in this sprint

```
NEW: backend/services/maintainx_client.py                    (285 LOC)
NEW: backend/services/maintainx_asset_sync.py                (320 LOC)
NEW: backend/routes/integrations/maintainx_p0.py             (86  LOC)
NEW: backend/tests/test_maintainx_p0_read_first.py           (260 LOC)

MOD: backend/routes/integrations/__init__.py                 (+2 import, +1 register)
MOD: backend/.env                                            (+4 keys, all empty/safe defaults)
```

**Operational collections (`equipment_master`, `equipment_units`, `asset_mappings`, `fleet_defects`, `dvir_*`, `shop_*`, `dispatch_*`, RTS) are NOT touched by any code in this sprint.**

The only new MongoDB collection introduced is `maintainx_dryrun_reports`, populated only when an admin explicitly calls `POST /api/admin/maintainx/p0/dryrun?save=true`.

---

## 3 · Live preview verification (no API key set)

| Endpoint | Result |
| --- | --- |
| `GET /api/admin/maintainx/p0/config` | 200 OK — `api_key_present=false`, kill-switches off |
| `POST /api/admin/maintainx/p0/test` | 200 OK — `{ok:false, status:"missing_api_key"}` |
| `POST /api/admin/maintainx/p0/dryrun` | 200 OK — pulled 0 MX assets · loaded 589 MASCI rows · all `writes_performed` counters = 0 · saved=false |

Backend supervisor log clean. No exceptions raised.

---

## 4 · ABSOLUTE-RULE compliance check

| Rule | Status |
| --- | --- |
| DO NOT Create MaintainX assets | RESPECTED (write methods hard-disabled, unit-tested) |
| DO NOT Update MaintainX assets | RESPECTED |
| DO NOT Delete MaintainX assets | RESPECTED |
| DO NOT Modify MASCI equipment records | RESPECTED (read-only `find()` only; unit test asserts `insert_calls==0`, `update_calls==0`) |
| DO NOT Modify `equipment_master` | RESPECTED (same as above) |
| DO NOT Modify `equipment_units` | RESPECTED (collection never referenced) |
| DO NOT Modify dispatch assets | RESPECTED (no dispatch collection referenced) |
| DO NOT Modify fleet DVIR records | RESPECTED (`fleet_defects` writes_performed counter = 0) |
| DO NOT Modify RTS records | RESPECTED |
| DO NOT Modify shop records | RESPECTED |
| DO NOT Change equipment status | RESPECTED |
| DO NOT Run migrations | RESPECTED (no migration code added) |
| DO NOT Deploy write-enabled sync | RESPECTED (`MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false`) |
| DO NOT Enable automatic sync | RESPECTED (no scheduler entry added; `SCHEDULER_ENABLED` env unchanged) |

The kill-switches `MAINTAINX_SYNC_ENABLED` and `MAINTAINX_WRITE_ENABLED` are layered on top of the code-level write-disable in `MaintainxClient`. Even if both env flags are flipped to `true`, the client's `create_asset/update_asset/delete_asset` methods still raise `MaintainxWriteDisabled`. This is verified by `test_client_write_methods_raise`.

---

## 5 · Operator surface

Today's admin can already:

1. **Probe configuration** — `GET /api/admin/maintainx/p0/config` returns env state with masked key.
2. **Probe connectivity** — `POST /api/admin/maintainx/p0/test` calls MaintainX (only if key is set).
3. **Run a dry-run** — `POST /api/admin/maintainx/p0/dryrun` pulls + matches + classifies, returns full report.
4. **Save & list reports** — `?save=true` then `GET /api/admin/maintainx/p0/dryrun-reports` for audit history.

Admin frontend UI placement is left for the next sprint per directive ("If this requires new architecture, skip and document"). The current Admin Integration Center page (`/admin/integration-center`) already shows the MaintainX tab; a sub-section calling the four endpoints above can be added safely without affecting any other surface.

---

## 6 · Outstanding limitations

| Limitation | Why it's acceptable for P0 |
| --- | --- |
| `MAINTAINX_API_KEY` not yet populated in preview/production | Operator must provide a real MaintainX key before any data appears in dry-run results; no code change required when the key lands |
| Match strategy #4 (make+model similarity) uses a 0.85 threshold derived from `difflib.SequenceMatcher` | Threshold may need tuning once a real dataset is available; this is read-only classification, no writes hinge on it |
| MaintainX webhook signature algorithm still placeholder | Out of scope for P0-A/P0-B (tracked in `MAINTAINX_GAP_REGISTER.md` as P0-F) |
| Admin UI sub-section not built | Out of scope per directive ("Preferred: Admin-only report · No write button · No sync button · No create button") — the data is available via the four new endpoints today |

---

## 7 · Final verdict

```
================================================================
  MAINTAINX P0-A / P0-B READ-FIRST ASSET INTEGRATION
================================================================
  API Client                : COMPLETE
  Read-only asset pull       : COMPLETE
  MASCI equipment matching   : COMPLETE
  Duplicate-risk analyser    : COMPLETE
  Admin-strict routes        : LIVE
  Tests                      : 13/13 PASS
  Writes performed in sprint : 0
  Kill-switches engaged       : SYNC=false · WRITE=false
================================================================
                        DECISION
        🟢 MAINTAINX READ-FIRST ASSET INTEGRATION READY
================================================================
```

### What this verdict means
- The codebase is **ready** for an operator-provided `MAINTAINX_API_KEY` to be wired into `backend/.env`.
- Once the key is set, an admin may run `POST /api/admin/maintainx/p0/dryrun` and receive a full populated report — without any write being performed to MaintainX, MASCI equipment, or any other operational system.
- No further code changes are required to begin **reading** from MaintainX.
- Writes (MASCI synthesis from MaintainX, DVIR → WO push, RTS gate, status sync) remain explicitly out of scope and require fresh operator authorisation per the gap roadmap.

### What this verdict does NOT authorise
- Enabling `MAINTAINX_WRITE_ENABLED=true` (still no write code exists)
- Auto-creating MASCI equipment from MaintainX-only assets
- Scheduling automatic sync
- Pushing any data outbound to MaintainX
- Deploying this sprint's preview changes to production (operator must explicitly redeploy)

— End of MaintainX P0-A/P0-B Read-First Certification —
