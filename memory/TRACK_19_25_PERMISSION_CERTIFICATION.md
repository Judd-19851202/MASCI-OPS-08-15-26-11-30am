# TRACK 19.25 · Permission Certification

## Matrix (unchanged from Track 19.21b · re-verified in this pass)

| Actor | Lanes read | Lanes upload | Lanes approve | Export packages |
|---|---|---|---|---|
| HR | all 4 | all 4 | all 4 | all 6 |
| Safety | safety | safety | safety | safety · historical_records |
| Asset Admin (Shop `is_asset_admin`) | asset | asset | asset | ppe_asset · historical_records |
| Admin | all 4 | all 4 | all 4 | all 6 |
| Field / Public / PM (no HR token) | — | — | — | 401 on any package |

## Track 19.25 impact
- Zero permission-model changes.
- New sidebar entries navigate to the same routes the backend already gates.
- Safety users clicking their new "Safety Records Intake" sidebar item hit the same `/hr/historical-records/intake` page, but the vocabulary endpoint scopes their view to `allowed_lanes_for_actor: ["safety"]` — the lane picker only shows Safety, and the record-type dropdown only offers Safety-lane types.
- Same for Asset Administrator clicking through Shop Hub tiles.

## Verified live
- HR token → sees new HR Bulk Historical Intake sidebar item + creates batch across any lane.
- Safety token → sees Safety Records Intake sidebar item + can only create Safety-lane batches (vocabulary confines the lane picker).
- Shop token WITHOUT `is_asset_admin` → sees the Shop Hub Asset Records tile (nav is intentional so admins can enable the flag later), but clicking through triggers 401/403 on the vocabulary endpoint → user sees "HR, Safety, Asset Administrator, or Admin auth required" and cannot proceed.
- Shop token WITH `is_asset_admin=true` → full Asset-lane workflow.

**Verdict:** GO. Zero permission leaks. Zero drift.
