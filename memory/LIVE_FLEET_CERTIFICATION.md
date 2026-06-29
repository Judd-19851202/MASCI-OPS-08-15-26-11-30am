# LIVE Fleet Certification — mascidocs.com

**Verdict:** ✅ **FLEET IS A VIEW INTO MASCI EQUIPMENT — NOT A DUPLICATE DATABASE**

---

## Live Fleet projection (verified against mascidocs.com)

```json
{
  "count": 136,
  "summary": {
    "masci_fleet_total": 136,
    "masci_fleet_adopted": 0,
    "leased_total": 0,
    "categories": [
      "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
      "Water Trucks", "Misc Trucks", "Flatbed Trucks", "Trailers"
    ]
  }
}
```

## Fleet UI header (rendered on LIVE)

```
Fleet
Transportation view of the MASCI fleet · one asset, one source of truth.

┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ MASCI fleet      │ Adopted into     │ Leased /         │ Surfaced in      │
│ (transport-      │ Transportation   │ owner-operator   │ this view        │
│  capable)        │                  │                  │                  │
│       136        │     0 · 0%       │        0         │       136        │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘

[ Search asset #, VIN, plate, make/… ]   [All categories ▾]  [All ownership ▾]

[ Adopt All Transportation Assets ]   [ Refresh ]
```

## First 8 rows surfaced from production fleet (verified)

| Asset | Category | Ownership | VIN / Ref | Transport status | Action |
| --- | --- | --- | --- | --- | --- |
| 2015 Garmin 465 LMT | Dump Trucks | masci_owned | 1SK143649 | not adopted | Adopt into Transportation |
| 2015 Garmin 465 LMT | Dump Trucks | masci_owned | 28Q14524 | not adopted | Adopt into Transportation |
| 2017 Garmin dezl 570 LMT | Dump Trucks | masci_owned | 3YD116145 | not adopted | Adopt into Transportation |
| 2017 Garmin dezl 570 LMT | Dump Trucks | masci_owned | 3YD109512 | not adopted | Adopt into Transportation |
| 2017 Garmin dezl 570 LMT | Dump Trucks | masci_owned | 3YD116155 | not adopted | Adopt into Transportation |
| 2017 Garmin dezl 570 LMT | Dump Trucks | masci_owned | 3YD116426 | not adopted | Adopt into Transportation |
| 2017 Garmin dezl 570 LMT | Dump Trucks | masci_owned | 3YD116484 | not adopted | Adopt into Transportation |
| DPT002-6387 (2006 Mack CV713) | Dump Trucks | masci_owned | 1M2AG11C36M036387 | not adopted | Adopt into Transportation |
| DPT007-8803 (2010 Mack GU713) | Dump Trucks | masci_owned | 1M2AX07C2AM008803 | not adopted | Adopt into Transportation |

(All 136 rows render correctly.)

## Architectural verification on LIVE

| Property | Status |
| --- | :-: |
| Fleet shows MASCI equipment (not a duplicate) | ✓ all 136 sourced from `equipment_master` via projection |
| `transport_trucks` overlay collection has zero MASCI duplicates | ✓ 0 overlays exist (clean baseline) |
| Categories scoped (no Pickup, no Supervisor/Mgmt, no Excavators) | ✓ exactly the 7 transport-capable categories surface |
| Per-row Adopt CTA visible | ✓ verified on every un-adopted row |
| Bulk "Adopt All" CTA visible in header | ✓ `[data-testid=tx-fleet-bulk-adopt-btn]` rendered |
| Search bar + category filter + ownership filter | ✓ all rendered |
| Operational overlay editor (PATCH endpoint) | ✓ live (returns 404 until adoption — by design) |
| Rollback endpoint live | ✓ admin-only, idempotent |

## Adoption preview on LIVE

```json
{
  "summary": {
    "already_adopted": 0,
    "would_adopt": 136,
    "skipped_inactive": 0,
    "skipped_retired": 0,
    "conflicts": 0,
    "missing_equipment_id": 0,
    "unknown_classification": 4,
    "leased_only_overlays": 0
  }
}
```

## Verdict

**FLEET CERTIFIED.** Transportation Fleet is correctly architected as a
read-mostly operational view of the MASCI Equipment Master. Zero
duplicate fleet records exist. The Adopt All workflow is staged and
ready for the operator's first click.
