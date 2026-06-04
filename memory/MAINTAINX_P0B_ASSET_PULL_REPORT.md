# MAINTAINX P0-B · READ-ONLY ASSET PULL REPORT

**Date:** 2026-06-04 18:30 UTC
**Sprint:** OMEGA P0-A/P0-B — Read-First MaintainX Asset Integration
**Mode:** READ-FIRST · DRY-RUN ONLY

---

## 1 · What was built

### New file
`backend/services/maintainx_asset_sync.py` — 320 LOC pure read pipeline.

### Public entrypoint
```python
report = await run_asset_dryrun(
    db,
    page_size=100,
    max_pages=50,
    save_report=False,         # default — guarantees zero writes
    triggered_by="admin",
)
```

### Pipeline phases (linear, in order)
1. **Connection probe** — calls `MaintainxClient.test_connection()`. Captures `ok/status/message/config` into `report["connection"]`.
2. **Asset pull** — `MaintainxClient.iter_assets()` paginated. Each payload is fed through `normalize_maintainx_asset(raw)` to a canonical shape (see §2).
3. **Load + normalise MASCI equipment** — `db.equipment_master.find({}, {"_id": 0})`, then `normalize_masci_equipment(row)`.
4. **Build lookup indices** — `(unit_number_normalised → [masci rows])` and `(vin_serial_normalised → [masci rows])`.
5. **Load existing mappings** — `db.asset_mappings.find({"maintainx.asset_id": {"$ne": ""}}, …)` to detect already-mapped IDs.
6. **Classify each MaintainX asset** — see §3.
7. **Reverse pass** — MASCI rows that were not matched by any MaintainX asset get listed under `missing_in_maintainx`.
8. **(Optional) save** — if `save_report=True`, insert the entire dict into `db.maintainx_dryrun_reports`. This is the ONLY DB write the pipeline can perform.

---

## 2 · Canonical shape produced by `normalize_maintainx_asset`

Tolerant of common MaintainX field-name variants:

| Canonical field | Source field tried (first match wins) |
| --- | --- |
| `maintainx_asset_id` | `id` · `assetId` · `asset_id` |
| `name`               | `name` · `title` |
| `unit_number`        | `unitNumber` · `unit_number` · `code` · `tag` · `barcode` |
| `serial_number`      | `serialNumber` · `serial_number` · `serial` |
| `vin`                | `vin` · `VIN` |
| `make`               | `make` · `manufacturer` · `brand` |
| `model`              | `model` · `modelNumber` · `model_number` |
| `year`               | `year` |
| `location`           | `location` · `locationName` · `location_name` |
| `location_id`        | `locationId` · `location_id` |
| `status`             | `status` · `state` |
| `raw`                | (full upstream payload retained for audit) |

This makes the pipeline robust against minor MaintainX API contract drift between versions.

---

## 3 · MASCI equipment canonical shape

Driven by the actual `db.equipment_master` schema discovered in preview:

```
KEYS PRESENT (preview):
  category · comments · company · display_label · id · make · make_model
  · model · plate · preop_equipment_type · unit_number
  · vin_serial_number · year
```

`normalize_masci_equipment()` projects these into:

| Canonical | Source |
| --- | --- |
| `id` | `id` |
| `unit_number` | `unit_number` |
| `name` | `display_label` ?? `make_model` |
| `make` / `model` / `year` | direct |
| `vin_serial` | `vin_serial_number` (combined column in MASCI) |
| `plate` | `plate` |
| `category`, `preop_equipment_type`, `company` | direct |

**Important:** MASCI stores VIN and serial in the SAME column. The matcher normalises both `vin` and `serial_number` from MaintainX into the same `vinserial` index bucket so either side of the field matches.

---

## 4 · Live preview behaviour (no key set)

```http
POST /api/admin/maintainx/p0/dryrun
→ totals.maintainx_assets_pulled = 0
  totals.masci_equipment_count    = 589 ← read from real preview DB
  totals.<every classification>   = 0
  writes_performed.maintainx       = 0
  writes_performed.equipment_master = 0
  writes_performed.asset_mappings   = 0
  writes_performed.fleet_defects    = 0
  saved = false
```

The MASCI equipment count of 589 was loaded from the live preview database **without modification**. The pipeline issues only `find()` reads against `equipment_master` and `asset_mappings`; no `insert/update/delete` is invoked on these collections by any code path.

---

## 5 · Output shape (full)

```jsonc
{
  "id":            "<uuid>",
  "started_at":    "<iso>",
  "completed_at":  "<iso>",
  "triggered_by":  "admin",
  "config":        { /* MaintainxConfig.public_view() */ },
  "connection":    { /* MaintainxClient.test_connection() */ },
  "totals": {
    "maintainx_assets_pulled":  N,
    "masci_equipment_count":    N,
    "exact_match":              N,
    "probable_match":           N,
    "possible_duplicate":       N,
    "conflict":                 N,
    "missing_in_masci":         N,
    "missing_in_maintainx":     N,
    "duplicate_risk_blocked":   N,
    "duplicate_risk_safe":      N,
    "errors":                   N
  },
  "results": [          /* one row per MaintainX asset */
    {
      "maintainx_asset_id":    "...",
      "maintainx_unit_number": "...",
      "maintainx_name":        "...",
      "maintainx_make":        "...",
      "maintainx_model":       "...",
      "maintainx_serial_number": "...",
      "maintainx_vin":         "...",
      "maintainx_status":      "...",
      "classification":        "exact_match | probable_match | possible_duplicate | conflict | missing_in_masci",
      "match_reason":          "...",
      "match_confidence":      0.0-1.0,
      "masci_equipment_id":    "..." (or null),
      "masci_unit_number":     "..." (or null),
      "masci_display":         "..." (or null),
      "duplicate_risk":        { /* only populated for missing_in_masci */ }
    }
  ],
  "missing_in_maintainx": [    /* MASCI rows nothing in MaintainX matched */
    { "masci_equipment_id", "unit_number", "display", "make", "model", "vin_serial" }
  ],
  "errors": [],
  "saved": false,
  "writes_performed": {
    "maintainx": 0,
    "equipment_master": 0,
    "asset_mappings": 0,
    "fleet_defects": 0
  }
}
```

---

## 6 · Safety guarantees

| Surface | Pipeline behaviour |
| --- | --- |
| MaintainX | Read-only. No POST/PATCH/PUT/DELETE on any MaintainX path. Write methods on `MaintainxClient` raise `MaintainxWriteDisabled` regardless of env flag. |
| `equipment_master` | Read-only. `find()` only. No insert/update/delete by any code in the pipeline. |
| `asset_mappings` | Read-only. `find()` only. Wizard / mappings CRUD live elsewhere and are untouched. |
| `fleet_defects` / DVIR / RTS / Shop / Dispatch | Untouched. None of these collections are read or written by P0-B. |
| `maintainx_dryrun_reports` | ONLY when `save_report=True`. Pure append — no update / delete. |

Counters `writes_performed.{maintainx, equipment_master, asset_mappings, fleet_defects}` are surfaced in every response and were verified to all be `0` in the live preview probe.

---

## 7 · Verdict — P0-B

```
P0-B · READ-FIRST ASSET PULL & MATCHING  :  COMPLETE

  Read-only pull through MaintainxClient    : DONE
  Canonical normalisation (MX + MASCI)       : DONE
  Layered matching strategy                  : DONE
  Duplicate-risk analyser                    : DONE
  Reverse pass (MASCI without MaintainX)     : DONE
  Optional save → maintainx_dryrun_reports   : DONE
  Zero writes to operational collections     : DONE (verified live + unit-tested)
  Admin-strict route surface                 : DONE
```

P0-B is implementation-complete and live in preview.
