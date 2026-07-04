# TRACK 20.6 · Asset Taxonomy Review — Fire Protection

**Question:** Should Fire Protection become a new asset_class in
`services/asset_taxonomy.py`, or extend an existing class?

**Answer:** **New asset_class.** Do not overload Safety Equipment.

## Why not extend `Safety Equipment`?

Current `Safety Equipment` types (per taxonomy v1.0.0):
Harness · Gas Monitor · Confined Space Equipment · Respirator · Fall
Protection · Other Safety Equipment.

These are all **worn/carried personal protection** with an **employee
issuance** lifecycle (checked out to a person). Fire extinguishers are
**mounted/stationed equipment** with a **location + monthly-inspection**
lifecycle. Different behavior matrix:

| Behavior | PPE (Safety Equipment today) | Fire Protection (proposed) |
|---|---|---|
| `assignable_to_employee` | ✅ Yes | ❌ No — assigned to a **location** or **vehicle** |
| `requires_preop` | ❌ No | ❌ No |
| `requires_pm` | ❌ No | ⚠️ Monthly inspection (safety-owned, not PM) |
| `inspection_required` | ❌ No | ✅ Yes (safety-authored, existing register) |
| `appears_on_map` | ❌ No | ⚠️ Optional (via parent vehicle) |
| `renewal_tracking_required` | ⚠️ Certifications | ✅ Next-due + hydrostatic |
| `document_vault_required` | ✅ Yes | ✅ Yes |
| `dot_required` | ❌ No | ⚠️ Some fleet extinguishers per DOT/FMCSA |

Overloading Safety Equipment would corrupt the PPE behavior matrix.

## Proposed taxonomy extension (Phase A · Track 19.62)

Bump `TAXONOMY_VERSION` **1.0.0 → 1.1.0** (additive · backwards-compat).

Add to `ASSET_CLASSES`:

```
"Fire Protection",
```

Add to `ASSET_TYPES_BY_CLASS`:

```python
"Fire Protection": (
    "Fire Extinguisher · ABC",
    "Fire Extinguisher · BC",
    "Fire Extinguisher · CO2",
    "Fire Extinguisher · Class D",
    "Fire Extinguisher · Class K",
    "Fire Extinguisher · Water",
    "Fire Extinguisher · Wet Chemical",
    "Fire Extinguisher · Water Mist",
    "Fire Extinguisher · Other",
    # Reserved for later phases — NOT part of Track 19.62 scope.
    # "Fire Hose",
    # "Fire Hose Cabinet",
    # "Smoke Detector",
    # "CO Alarm",
    # "Emergency Light",
    # "Exit Sign",
    # "AED",
    # "Emergency Shower",
    # "Eyewash Station",
    # "First Aid Kit",
),
```

Proposed behavior overrides for each Fire Extinguisher type:

```python
{
    "requires_registration": False,
    "requires_insurance": False,
    "requires_pm": False,
    "requires_preop": False,
    "assignable_to_employee": False,
    "transferable": True,
    "appears_on_map": False,
    "employee_lifecycle_managed": False,
    "renewal_tracking_required": True,
    "document_vault_required": True,
    "dot_required": False,   # per-instance override for DOT vehicles
    "inspection_required": True,
    "exportable": True,
}
```

## Crosswalk from legacy `db.fire_extinguishers.type` → canonical type

| Legacy string | Canonical asset_type |
|---|---|
| `ABC` | `Fire Extinguisher · ABC` |
| `BC` | `Fire Extinguisher · BC` |
| `CO2` | `Fire Extinguisher · CO2` |
| `Class D` / `D` | `Fire Extinguisher · Class D` |
| `Class K` / `K` | `Fire Extinguisher · Class K` |
| `Water` | `Fire Extinguisher · Water` |
| `Wet Chemical` | `Fire Extinguisher · Wet Chemical` |
| `Water Mist` | `Fire Extinguisher · Water Mist` |
| anything else | `Fire Extinguisher · Other` (with `needs_review=true` per Track 13.31B doctrine) |

## Zero-Drift accounting for the taxonomy bump

- `TAXONOMY_VERSION` bumped 1.0.0 → 1.1.0 (semver minor — additive).
- No existing class renamed. No existing type removed.
- Every existing consumer (PM Engine · Pre-Op · Shop · Dispatch · Daily
  Reports · Fuel/Lube · Asset Administration) continues to read the
  taxonomy exactly as before — they simply gain a new closed-set entry.
- The Track 13.31B taxonomy lock test expects a stable set — it will
  need to be updated in Phase A to accept the union. This is the same
  additive-safe pattern used when the vendor lane was added.

## Recommendation

**Add exactly one asset_class ("Fire Protection") with nine
extinguisher types.** Do not scope-creep into hoses / AEDs / smoke
detectors — leave those as reserved comments for later phases. Do NOT
extend Safety Equipment for fire extinguishers.
