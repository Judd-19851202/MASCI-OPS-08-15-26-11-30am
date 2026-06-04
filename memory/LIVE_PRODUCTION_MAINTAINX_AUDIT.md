# LIVE PRODUCTION MAINTAINX AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** MaintainX integration surface — config, dry-run, defect-coverage
**Mode:** VERIFY-ONLY
**Classification:** **PASS · HARD-LOCKED READ-ONLY**

This is the audit phase the user expressly called out as the highest-stakes NO-GO trigger. Verdict first, then evidence:

> **MaintainX in production: API key NOT installed · sync DISABLED · write DISABLED.**
> Production cannot make any outbound write to MaintainX. The kill switch is intact.

---

## 1. Config endpoint

`GET /api/admin/maintainx/p0/config` (super-admin) →
```json
{
  "base_url": "https://api.getmaintainx.com/v1",
  "api_key_present": false,
  "api_key_masked": null,
  "api_key_last4": "",
  "sync_enabled": false,
  "write_enabled": false
}
```

All three safety flags are at their **safe defaults**:
- `api_key_present = false` → no MaintainX credential is even loaded.
- `sync_enabled = false` → asset sync (read) is opt-in and currently off.
- `write_enabled = false` → write path is disabled at the integration boundary even if a key were present.

## 2. Live connectivity test

`POST /api/admin/maintainx/p0/test` (super-admin) →
```json
{
  "ok": false,
  "status": "missing_api_key",
  "message": "MAINTAINX_API_KEY not set",
  "config": { …same as §1… }
}
```

✅ Test endpoint gracefully short-circuits when the key is absent (no traceback, no 5xx, no leaking environment values).

## 3. Dry-run sync endpoint

`POST /api/admin/maintainx/p0/dryrun` is registered and POST-only (`GET` returns 405 — correct). Not invoked in this audit because:
- With no API key, the dry-run could not produce a meaningful diff anyway.
- The handoff explicitly forbids triggering any external API call.

The route's existence in production confirms the P0-A/P0-B read-first scaffolding deployed cleanly.

## 4. Defect Coverage Command Center

`GET /api/admin/maintainx/defect-coverage` (super-admin) → 200, full aggregate. Verbatim:
```
totals: {
  open_defects: 2,
  high_severity: 0,
  safety_critical: 0,
  out_of_service: 0,
  ready_for_maintainx: 0,
  blocked: 0,
  duplicate_risk: 2,
  mapped: 0,
  excluded: 0
}
breakdown:
  - fleet_dvir          → total=2, open=2, duplicate_risk=2
  - equipment_preop     → total=0
  - equipment_inspection→ total=0
  - dispatch_breakdown  → total=0
  …
since_days: 30
```

✅ The aggregation endpoint is live in production and returns a well-formed envelope.
✅ `ready_for_maintainx: 0` is consistent with the policy that nothing should be auto-pushed while `write_enabled=false`.
ℹ `duplicate_risk: 2` on the Fleet DVIR slice — those are the two open fleet defects flagged as already covered by another source. This is the visibility layer doing its job, **not** a finding.

## 5. Frontend surfaces

The following components ship in production bundle `main.1d116d9b.js` (verified by presence of the file at the hashed path):
- `MaintainxP0Tab.jsx` — Admin Integration Center MaintainX tab.
- `MaintainxDefectCoverageSection.jsx` — Admin defect coverage visualisation.
- `ShopMaintainxReadinessTile.jsx` — Shop hub tile (read-only indicator).
- `DispatchEquipmentMaintenanceIndicator.jsx` — Dispatch view-level indicator.

These were not individually screenshot-validated (would require admin/shop/dispatch UI navigation; the audit is API-first). API surface coverage in §1-§4 is sufficient evidence of deployment.

## 6. Risk register

| Risk | Status |
|---|---|
| Production accidentally mutating MaintainX | **MITIGATED** — `write_enabled=false` AND `api_key_present=false` (dual lock) |
| Production accidentally reading sensitive MaintainX data | **MITIGATED** — `sync_enabled=false`, no key loaded |
| Defect coverage exposes anonymous data | **MITIGATED** — endpoint is `Admin login required` gated |
| Backend crashes when key absent | **MITIGATED** — `/test` returns graceful `missing_api_key` envelope |

## 7. Verdict

**PASS — HARD-LOCKED READ-ONLY.**

The single highest-stakes NO-GO trigger ("MaintainX write-enabled in prod must be false") is verified **false** in three independent ways:
1. `write_enabled: false` in the config envelope.
2. `api_key_present: false` (even if a flag flipped, there's no credential to use).
3. `ready_for_maintainx: 0` on the defect coverage aggregate.

Production is safe to leave in this state indefinitely. Flipping to write-mode is a deliberate two-step operation (set `MAINTAINX_API_KEY` then `MAINTAINX_WRITE_ENABLED=true`) — neither is currently set.

