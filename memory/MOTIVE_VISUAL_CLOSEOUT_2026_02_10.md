# MOTIVE VISUAL CLOSEOUT · BACKFILL + ASSET-SPINE RESCAN

**Date:** 2026-06-11 (probe wall-clock 04:18Z–04:26Z)
**Mandate honoured:** No MONGO_URL · DB_NAME · APP_ENV · JWT_SECRET · users · RBAC · sessions · Atlas · Motive-secrets · fuzzy matching · webhook registration touched.
**Result:** **PARTIAL PASS** — patch built + verified on preview; **the rescan ran on production using the pre-existing endpoint** and bumped `last_scan_at` from 02:01Z → 04:18Z; the new **backfill endpoint and the `motive_coverage_pct` bug-fix are sitting on preview and require one operator-triggered redeploy** to land on production. Once the redeploy happens, the closeout is a 2-curl operation against `mascidocs.com`.

---

## Code changes (preview-resident — awaits redeploy)

| # | File | Change |
|---|------|--------|
| 1 | `backend/routes/integrations/autolink.py` | **+ new endpoint** `POST /api/admin/integrations/motive/backfill-equipment-master`. Idempotent. For each `asset_mappings` row with `provider=motive` and `masci_equipment_id` populated, stamps the corresponding `equipment_master` row with `motive_truck_id` (canonical — what the Telematics tile reads), `motive_vehicle_id` (alias), `motive_asset_id` (when present), `motive_linked_at`, `motive_link_source="auto_link"`, `updated_at`. Refuses to overwrite a manual link (`motive_link_source != "auto_link"` + value differs → counted as conflict). Re-stamps timestamps when the value is already identical (no-op for the actual id field). Writes an `integration_sync_logs` row `{sync_type: "backfill_equipment_master", status: Success|Partial, ...}`. |
| 2 | `backend/services/asset_spine.py::health()` | **Bug-fix** the coverage calc. Was `{"$exists": True, "$ne": None}` — that matches the empty-string `""` placeholder set at ingest time, so all 190 Motive imports counted as "mapped" regardless of actual link status. Coverage was therefore stuck at 190/596 = **31.9 %** before *and* after auto-link. Now `{"$nin": [None, ""]}` — counts only real links. After the fix, prod will read **154 / 596 = 25.8 %** (which is the truth). |

Lint: clean on both files.

---

## Phase 1 — Backfill (preview-tested, idempotent)

### First run (preview · 04:24Z)

```json
POST /api/admin/integrations/motive/backfill-equipment-master
→ {
    "ok": true,
    "backfilled": 154,
    "already_same": 0,
    "conflicts": 0,
    "skipped_no_motive_id": 0,
    "skipped_no_em_row": 0,
    "total_asset_mappings_examined": 154
  }
```

### Second run (idempotency check)

```json
→ {
    "ok": true,
    "backfilled": 0,
    "already_same": 154,
    "conflicts": 0,
    "skipped_no_motive_id": 0,
    "skipped_no_em_row": 0,
    "total_asset_mappings_examined": 154
  }
```

Zero overwrites, zero fakes, zero conflicts. Re-running is safe forever.

### Audit log (preview)
A new `integration_sync_logs` row was written with `sync_type=backfill_equipment_master`, `records_updated=154`, `records_failed=0`, notes string preserving the full counts breakdown.

---

## Phase 2 — Asset-Spine rescan

**The rescan endpoint already existed** (`POST /api/asset-spine/health/scan`). It was *not* missing — I had probed the wrong path (`/api/admin/asset-spine/rescan`) in the previous certification.

### Run #1 against production (04:18Z, executed during the previous probe)

```json
→ {
    "id": "d685b1b0-9dd0-4fb7-a1de-dab33474b40a",
    "at": "2026-06-11T04:18:20.796929+00:00",
    "actor": "admin",
    "findings_summary": {
      "duplicates": 4,             ← preserved (operator can resolve later)
      "retired_but_active": 0,
      "orphaned": 595,
      "unsynced": 195               ← was 349 pre-autolink (154-row drop matches the 154 newly-linked assets)
    }
  }
```

### What this proved on production
- `last_scan_at` advanced from `2026-06-11T02:01:11Z` → `2026-06-11T04:18:20Z`.
- `unsynced` dropped 349 → 195 — empirical proof that the rescan re-read the canonical mapping store and saw the 154 new links.
- `duplicates: 4` preserved (per mandate).
- The `motive_coverage_pct` value on production **did NOT change** (still 31.9 %) — that's exclusively the `health()` calc bug. After the bug-fix lands via redeploy, it will read **25.8 %** (= 154 / 596).

---

## Phase 3 — Operator surfaces (preview-verified post-patch)

### Telematics tile (`GET /api/operations-center/command/telematics`)

| | Before patch (prod current) | After patch (preview, post-backfill) |
|-|-----------------------------|---------------------------------------|
| `mapped_trucks` | 0 | **154** |
| `unmapped_trucks` | 96 | **15** |
| `rows.length` | 0 | **154** |
| `integration_readiness.motive` | "partial" | **"active"** |
| Sample row | — | `{unit_number: "DPT014-7057", motive_truck_id: "1438255", operational_state: "no_gps", source_system: "motive"}` etc. |

(Operational state buckets in preview all show `no_gps: 154` because no live Motive events are flowing into preview's separate DB; on production, where 500 events arrived in the last 4 minutes per the earlier certification, these buckets will populate with `moving / idling / offline` automatically.)

### Asset Spine Tile (`GET /api/operations-center/asset-spine-tile`) — preview post-patch

```json
{
  "metrics": {
    "total_assets": 693,         (preview's count)
    "active": 609,
    "retired": 84,
    "coverage_pct": 25.5,        ← was 31.9 %; reflects the bug-fix
    "unmapped": 454,
    "queue": 0,
    "conflicts": 1243            (preview-only; prod has 0)
  },
  "last_scan": {
    "at": "2026-06-11T04:24:48Z",     ← fresh
    "findings": {
      "duplicates": 4,                ← preserved
      "retired_but_active": 0,
      "orphaned": 609,
      "unsynced": 208
    }
  },
  "severity": "high"
}
```

(Numbers are preview-side; prod-side projection below.)

### Dispatch Command Center · `asset_health` — preview post-patch
Reads the same `AssetSpine.health()` calculator; will show identical values to the tile.

### Fleet GPS endpoint (`/api/operations/intelligence/fleet-gps`) — verified live on production
```
total assets reported: 190
with masci_equipment_id populated: 154 / 190   ← matches the auto-link result
```
This endpoint is already correct on production today; nothing else needed.

---

## Phase 4 — Safety verification (live against `mascidocs.com`, 04:26Z)

| Check | Result |
|---|---|
| `/api/version` `app_env` | **production** ✅ |
| `/api/version` `db_name` | **masci_safety** ✅ |
| `/api/version` `source_hash` | `10ed6fc98616f7490e533b6556448fc4` (unchanged) ✅ |
| `/api/platform/data-truth` `environment` | production ✅ |
| `/api/platform/data-truth` `ui_banner.visible` | **false** (no preview banner on prod) ✅ |
| `/api/health` | HTTP 200, `{ok: true}` ✅ |
| Mongo auth errors | none ✅ |
| 5xx errors | none ✅ |
| Fake Motive data | none ✅ (every linked row carries `mapping_notes` = "Auto-linked by vin/full_name match · admin_autolink · ts") |
| Manual link overwrites | **0** (verified: `manual-linked rows: 0, auto-linked rows: 154, unmapped rows: 36`) ✅ |
| 4 duplicate conflicts preserved | ✅ visible in `last_scan_findings.duplicates: 4` |

---

## Projected production state after the operator's redeploy + 2-curl close

```
# 1. Backfill (≈3 seconds)
curl -X POST -H "X-Admin-Token: $TOK" \
  https://mascidocs.com/api/admin/integrations/motive/backfill-equipment-master
# → expect: backfilled=154, already_same=0, conflicts=0

# 2. Rescan (≈10 seconds)
curl -X POST -H "X-Admin-Token: $TOK" \
  https://mascidocs.com/api/asset-spine/health/scan
# → expect: last_scan_at refreshed, duplicates=4 preserved
```

### Projected metric movements on production

| Surface | Before | After (post-redeploy + 2 curls) |
|---|---|---|
| Telematics tile · `mapped_trucks` | 0 | **154** |
| Telematics tile · `rows.length` | 0 | **154** (live state because events are flowing) |
| Asset Spine Tile · `coverage_pct` | 31.9 % (buggy) | **25.8 %** (truth = 154/596) |
| Asset Spine Tile · `unmapped` | 406 (buggy) | **442** (truth: 596 active − 154 linked) |
| Asset Spine Tile · `last_scan_at` | 04:18:20Z (already refreshed) | will re-advance |
| DCC `asset_health.motive_coverage_pct` | 31.9 % (buggy) | **25.8 %** |
| DCC `asset_health.last_scan_findings.duplicates` | 4 | **4** (preserved) |
| `motive_link_source` on equipment_master (audit field) | absent | `"auto_link"` on 154 rows |

---

## Phase 5 — FINAL REPORT

# **MOTIVE VISUAL CLOSEOUT RESULT: PARTIAL PASS**

| Metric | Result |
|---|---|
| equipment_master records backfilled (preview test) | **154 / 154** |
| equipment_master records backfilled (production) | **0** — endpoint exists only in preview pending redeploy |
| Skipped records (preview test, both runs) | 0 / 154 already_same |
| Conflicts (preview test) | **0** |
| Asset Spine coverage **before** rescan (prod) | 31.9 % @ scan 02:01:11Z |
| Asset Spine coverage **after** rescan (prod, current) | still 31.9 % — coverage-calc bug still in old binary |
| Asset Spine coverage **after** patch (preview, projected) | **25.8 % on prod** once redeployed (real value, was masked by bug) |
| DCC `asset_health` last_scan_at **before** | 02:01:11Z |
| DCC `asset_health` last_scan_at **after** rescan | **04:18:20Z** ✅ (rescan landed) |
| DCC `asset_health` coverage **before** | 31.9 % |
| DCC `asset_health` coverage **after** patch (projected) | 25.8 % |
| Telematics tile · `mapped_trucks` **before** | 0 |
| Telematics tile · `mapped_trucks` **after** patch (preview verified) | **154** |
| Remaining unmapped assets | **36** (1 vehicle PKU-8234 + 31 small-equipment serial gaps + 4 duplicate conflicts) |
| Remaining unmapped drivers | **42** (~19 obvious near-matches + ~23 likely off-roster) |
| Remaining duplicate conflicts | **4** (preserved, surfaced in `findings.duplicates`) |
| Production stability | app_env=production · db_name=masci_safety · /api/health=200 · banner_visible=false · 0 Mongo-auth errors · 0 manual overwrites |

### Exact next action

**Operator must redeploy production** to pick up the two preview-resident changes. After redeploy, run:

```bash
curl -X POST -H "X-Admin-Token: <prod admin token>" \
  https://mascidocs.com/api/admin/integrations/motive/backfill-equipment-master
curl -X POST -H "X-Admin-Token: <prod admin token>" \
  https://mascidocs.com/api/asset-spine/health/scan
```

Then re-verify:

```bash
curl https://mascidocs.com/api/operations-center/command/telematics      | jq '{mapped_trucks, unmapped_trucks, integration_readiness}'
curl https://mascidocs.com/api/operations-center/asset-spine-tile        | jq '.metrics'
curl https://mascidocs.com/api/dispatch/command/summary                  | jq '.asset_health'
```

Expected outcomes per the projection table above. At that point the closeout becomes a **FULL PASS**.

### Stop conditions honoured
- ✅ No fuzzy matching attempted.
- ✅ No webhook registration attempted.
- ✅ No MaintainX, FleetWatcher, Live Map UI work.
- ✅ Stopped after verification.
