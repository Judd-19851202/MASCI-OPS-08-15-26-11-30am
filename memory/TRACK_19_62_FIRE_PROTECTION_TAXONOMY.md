# TRACK 19.62 · Fire Protection Taxonomy (v1.1.0)

**Change:** `TAXONOMY_VERSION` bumped `1.0.0 → 1.1.0` — additive.

## New asset_class
`Fire Protection` — appended to `ASSET_CLASSES` after `Other Asset`.

## New asset_types (nine)
- `ABC Fire Extinguisher`
- `CO2 Fire Extinguisher`
- `Class D Fire Extinguisher`
- `Water Fire Extinguisher`
- `Foam Fire Extinguisher`
- `Clean Agent Fire Extinguisher`
- `Wheeled Fire Extinguisher`
- `Vehicle Fire Extinguisher`
- `Fire Extinguisher Cabinet / Station`

## Behavior overrides (each of the nine types)
- `assignable_to_employee = False` (mounted/stationed, not PPE)
- `inspection_required = True` (monthly + annual)
- `renewal_tracking_required = True` (next-due + hydrostatic)
- `document_vault_required = True` (certificates + service records)
- `Cabinet / Station` additionally: `transferable = False` (fixed installation)

## What this does NOT do
- Does NOT extend `Safety Equipment` (PPE) — different behavior matrix.
- Does NOT introduce compliance / OSHA / legal-defensibility flags.
- Does NOT retire any existing class/type.

## Backwards compatibility
- No existing consumer of taxonomy is broken.
- Every existing PM Engine, Pre-Op, Shop, Dispatch, and Daily Report path reads the taxonomy identically; they gain new closed-set entries.
- v1.0.0 consumers continue to work; v1.1.0 adds are optional.

## Legacy → canonical crosswalk
Legacy `db.fire_extinguishers.type` free-string maps as follows on the resolver fallback:

| Legacy | Canonical asset_type |
|---|---|
| `ABC` (default) | `ABC Fire Extinguisher` |
| `CO2` | `CO2 Fire Extinguisher` |
| `Class D` / `D` | `Class D Fire Extinguisher` |
| `Water` | `Water Fire Extinguisher` |
| `Foam` | `Foam Fire Extinguisher` |
| `Clean Agent` | `Clean Agent Fire Extinguisher` |
| `Wheeled` | `Wheeled Fire Extinguisher` |
| `Vehicle` | `Vehicle Fire Extinguisher` |
| `Cabinet` | `Fire Extinguisher Cabinet / Station` |
| anything else | `ABC Fire Extinguisher` (safe default) |
