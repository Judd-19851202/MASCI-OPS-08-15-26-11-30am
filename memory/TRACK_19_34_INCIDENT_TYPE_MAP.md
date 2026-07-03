# TRACK 19.34 · INCIDENT TYPE MAP

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_33_INCIDENT_ENGINE_READINESS_BRIDGE.md`

Locks the mapping between the 10 required Track 19.34 incident types and the 17 actual types shipped in the platform via Track 19.16. **No legacy value is deleted.** Safety-lane re-classification remains available for edge cases.

---

## Type map (Track 19.34 spec ↔ code)

| # | Track 19.34 required type | Platform `incident_type` value(s) | Location | Notes |
|---|---|---|---|---|
| 1 | Utility Strike | `utility_strike` | `INCIDENT_FLOWS.utility_strike` | Includes locate ticket · marks · potholing · service interruption fields. |
| 2 | Employee Injury | `employee_injury` | `INCIDENT_FLOWS.employee_injury` | Body part · treatment · ambulance · clinic/hospital · sent home. |
| 3 | Vehicle Accident | `vehicle_accident` | `INCIDENT_FLOWS.vehicle_accident` | Vehicles · drivers · passengers · police · crash number · injuries · tow. |
| 4 | Equipment Accident | `equipment_accident` | `INCIDENT_FLOWS.equipment_accident` | Equipment · operator · spotter · ground · damage · fluid release · rollover · OOS. |
| 5 | Property Damage | `property_damage` | `INCIDENT_FLOWS.property_damage` | Property · owner · damage · severity · immediate protection. |
| 6 | Near Miss | `near_miss` | `INCIDENT_FLOWS.near_miss` | Almost-happened · potential severity · contributing conditions · prevention. |
| 7 | Environmental Spill | `environmental` | `INCIDENT_FLOWS.environmental` | Substance · quantity · containment · waterway · cleanup · agency notified. |
| 8 | Workplace Violence / Threat | `workplace_violence` + `threat` | `INCIDENT_FLOWS.workplace_violence`, `INCIDENT_FLOWS.threat` | Split into two nodes for clarity; both are field-facing options. `workplace_violence` = incident occurred; `threat` = verbal/written/implied. |
| 9 | Theft / Vandalism / Security | `theft` + `vandalism` + `security` | `INCIDENT_FLOWS.theft`, `INCIDENT_FLOWS.vandalism`, `INCIDENT_FLOWS.security` | Split into three nodes for clarity — each has a distinct fact-capture emphasis. All three tag as "security-category" for downstream routing. |
| 10 | Other | `other` | `INCIDENT_FLOWS.other` | Free-form facts · Safety triages type on review. |

## Additional shipped types (not in Track 19.34 required-10, preserved from 19.16)
| # | Extra type | Value | Field-facing? | Notes |
|---|---|---|---|---|
| Ext-1 | Public Injury | `public_injury` | Yes | Pedestrian fall · struck by material · trip on caution tape. |
| Ext-2 | Public Complaint | `public_complaint` | Yes | Noise · dust · traffic · property · conduct. |
| Ext-3 | Fire | `fire` | Yes | Any unplanned fire (equipment · brush · structure · vehicle). |
| Ext-4 | Hazard Identified | `hazard` | Yes | Hazardous condition observed before it caused harm. |

None of these will be removed. They are legitimate additional field workflows.

## Legacy value preservation

Zero legacy `incident_type` values are deleted. Backend `POST /api/incident-cases` continues to accept the full 17-type enumeration. Any historical record with any of these values continues to render correctly in the Case Workspace, Employee 360 timeline, and executive read fanout.

## Type discriminator contract (unchanged)

- `incident_type: string` — enum matches `INCIDENT_TYPE_ORDER` in `lib/incidentReportSchema.js:641-659`.
- `contract_version: string` — bumped by future incident-engine tracks (Track 19.34 does not bump it).
- Payload shape is per-type via `STEP_*` compositions in `incidentReportSchema.js` — additive only.

## Field-facing type ordering (picker layout · left-to-right, top-to-bottom on mobile)

Per `INCIDENT_TYPE_ORDER`:
`vehicle_accident · equipment_accident · utility_strike · employee_injury · public_injury · near_miss · property_damage · environmental · workplace_violence · public_complaint · fire · threat · theft · vandalism · security · hazard · other`

This order is the "operational familiarity" order — most-common workflows first, followed by less-common but still frequent categories.

## Rationale for keeping the 3-way split on Theft/Vandalism/Security

The Track 19.34 spec proposes a merged "Theft / Vandalism / Security" node. The platform keeps three nodes for these reasons:
1. **Different fact-capture emphasis.** Theft cares about the stolen item; vandalism cares about the damage; security cares about the access breach.
2. **Different downstream routing.** Theft often triggers police-report follow-up; vandalism triggers repair estimate; security triggers site-controls audit.
3. **Safety-lane reclassification remains available.** A field user who picks Theft on a vandalism event doesn't create a data integrity problem — Safety can reclassify in the Case Workspace.
4. **Zero-drift doctrine.** Removing existing enumeration values would break historical records. Track 19.34's ethos is additive-only.

## Rationale for keeping the 2-way split on Workplace Violence / Threat

Same reasoning: `workplace_violence` implies an occurred event; `threat` implies an implied event. Different fact-capture emphases, both legitimately field-owned.
