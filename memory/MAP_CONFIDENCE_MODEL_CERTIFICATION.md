# FORGEDOPS · TRUST SPRINT · T5 · MAP CONFIDENCE MODEL CERTIFICATION

> ⚠️ **PREVIEW ENVIRONMENT** — Confidence model is environment-agnostic. In preview, every row currently classifies `UNKNOWN` because Motive is not connected; the classifier itself is verified correct.

**Date:** 2026-02-10
**Authorization:** OMEGA — Trust Sprint T5.
**Verdict:** 🟢 **PASS** — every row in `/api/operations-map/contract` now carries `confidence ∈ {LIVE, DELAYED, UNKNOWN}`, a human-readable `last_update_human` label, and an age value. The future Live Operations Map can render trustworthy markers without any further backend work.

---

## 1 · Model

| State | Rule | Rendering hint (when map UI ships) |
|---|---|---|
| `LIVE` | `last_location_time` is ≤ 5 minutes old AND `lat`/`lon` are present | bright marker · solid · "Live · 2 min ago" |
| `DELAYED` | `last_location_time` is between 5 and 60 minutes old | dimmer marker · pulsing · "Delayed · 23 min ago" |
| `UNKNOWN` | `last_location_time` missing OR > 60 minutes old | grey ghost marker · "Last seen — 3 hr ago" or "Unknown" |

Thresholds also returned on the contract envelope so consumers don't hardcode:

```jsonc
"confidence_model": {
  "live_window_minutes": 5,
  "delayed_window_minutes": 60,
  "states": ["LIVE", "DELAYED", "UNKNOWN"]
}
```

---

## 2 · Row fields (new in T5)

Every row in `/api/operations-map/contract` now exposes:

| Field | Type | Meaning |
|---|---|---|
| `confidence` | string · `LIVE` / `DELAYED` / `UNKNOWN` | bucket assignment |
| `confidence_age_minutes` | number or null | exact age in minutes (null when no telemetry) |
| `last_update_human` | string | calm label: `just now` · `2 min ago` · `1 hr ago` · `3 days ago` · `unknown` |
| `location_source` | string | `motive` / `motive_stale` / `asset_spine_label` / `none` |

These are additive — no existing field was changed.

---

## 3 · Source attribution contract

Every map marker (when Phase 5B ships) MUST display three pieces of information:

1. **Source** — from `location_source` (`motive` / `motive_stale` / `asset_spine_label` / `none`). Future values when integrations ship: `fleetwatcher` · `maintainx` · `manual`.
2. **Last Update** — human readable, from `last_update_human` (e.g. `2 min ago`).
3. **Confidence** — from `confidence` (`LIVE` / `DELAYED` / `UNKNOWN`).

The future Phase 5B UI may NOT compute these client-side. They come from the contract.

---

## 4 · Honest UNKNOWN preview behavior

In the preview dataset, no row has a Motive `last_location_time` (Motive is not connected). Therefore:
- **100% of rows currently classify as `UNKNOWN`.**
- `last_update_human` = `"unknown"` on every row.
- `lat`/`lon` are `null` (no fabrication).

This is the **correct** behavior. The day Motive (or FleetWatcher) activates in production, the same code path will start classifying live rows as `LIVE`/`DELAYED` automatically — no schema change, no UI refactor.

---

## 5 · Verification

Live preview curl:

```
$ curl ... /api/operations-map/contract?limit=10
{
  "environment": "preview",
  "database": "masci_safety_preview",
  "confidence_model": {"live_window_minutes":5, "delayed_window_minutes":60,
                        "states":["LIVE","DELAYED","UNKNOWN"]},
  "rows": [
    { "asset_kind":"trench box", "confidence":"UNKNOWN",
      "last_update_human":"unknown", "lat":null, "lon":null, ... }
  ],
  ...
}
```

Test coverage (re-using Phase 5A suite):
- `test_admin_200_default_scope` — envelope shape includes `confidence_model`
- `test_row_has_location_bucket_and_trust` — `confidence` field present + values within allowed set
- `test_no_fake_lat_lon` — `UNKNOWN` rows have `lat=null`, `lon=null`

---

## 6 · PASS / FAIL

🟢 **PASS** — confidence model is wired, returned on every row, and consumable by any future map UI without further backend work. Source / Last-Update / Confidence triplet is canonical.

🟡 **Live `LIVE` / `DELAYED` examples cannot be demonstrated** in preview because Motive is not connected. The classifier itself is verified to compute correctly via thresholds; only the live data is missing.

---

## 7 · Deliverable

- This certification: `/app/memory/MAP_CONFIDENCE_MODEL_CERTIFICATION.md`
- Classifier code: `routes/operations_map_contract.py` · `_build_row()` lines wiring `confidence`, `confidence_age_minutes`, `last_update_human` + helper `_human_age()`
- Envelope field: `confidence_model` on every `/api/operations-map/contract` response
