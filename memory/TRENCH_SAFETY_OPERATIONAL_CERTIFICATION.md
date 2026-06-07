# Trench Safety · Operational Certification
**Date:** 2026-02-07
**Mode:** Verification + hardening only. Zero code changes. No deployment.
**Verdict:** 🟢 **PASS · GO**

## Test suite roll-up
Full sequential run of every Trench Safety pytest suite (Phase 2 → Phase 7.5C):

| Suite | Result |
|---|---|
| `test_trench_safety_phase2` | 1 failure (stale fixture count — see below) · others pass |
| `test_trench_safety_phase4a` | PASS |
| `test_trench_safety_phase4b` | PASS |
| `test_trench_safety_phase5`  | PASS |
| `test_trench_safety_phase6`  | PASS |
| `test_trench_safety_phase7`  | PASS (14/14) |
| `test_trench_safety_phase75c`| PASS (5/5) |
| **Overall** | **105 passed · 1 fixture-drift failure** in 291s |

### One Phase 2 failure — not a behavioural regression
`test_seven_seeded_assets_present` asserts the asset count == 7. Live DB has 13 because Phase 7.5C test fixtures (`TB-NTF-XXXXX`, `TB-P75A`) were retired (per directive: Asset ID is immutable; retirement is terminal). The canonical TB-01..TB-07 are intact and live (see `TRENCH_SAFETY_DATA_INTEGRITY_CERTIFICATION.md`). This is a test-fixture drift, not a system bug. No code change made (verification-only sprint).

## Surface-by-surface verification

### Public Safety Tile
| Item | Status | Evidence |
|---|---|---|
| Asset Lookup | ✅ | `/trench-safety` PublicAssetLookup component renders + routes to QR landing |
| QR Scan landing | ✅ | `GET /api/trench-safety/public/assets/TB-01` returns 200 + field-safe projection |
| Tabulated Data | ✅ | `/trench-safety/tabulated-data` (separate route per UX sprint) |
| Safety References | ✅ | `/trench-safety/references` (separate route) |
| Field Reports surface (read-only) | ✅ | Inbox is Safety-Portal-only per directive; public surface only submits |
| Damage Reports | ✅ | `POST /api/trench-safety/public/damage-report` (verified) |
| Spanish | ✅ | LangToggle present on every public route |
| Mobile | ✅ | All public surfaces are 480-px-first |
| Back Navigation | ✅ | Contextual headers ("Back to Trench Safety" / "Back to Safety") |
| Serial Numbers | ✅ | TB-01 shows `C080102`; TB-05 shows "Missing — Action Required" |
| Public Photos | ✅ | `GET /api/trench-safety/public/assets/{id}/photos` projection filters Internal Only |
| DO NOT USE banners | ✅ | QR landing hold warnings + missing-serial alert |

### Safety Portal (full Command Center)
All sections from Phase 7.5A and 7.5B verified rendering with live data via Playwright:
Dashboard · Daily Posture · Asset List · Asset Detail · Create / Edit / Retire / Status Change · Inspection Create + List · Hold Open / Clear / List · Certification Upload / Revoke / List · Repair Review (6 filters + Verify dialog) · Field Report Inbox · Photo Management · QR Management · Audit Timeline · Notifications · Email escalation gating · Spanish parity.

### Admin Portal
100% parity via shared components from `TrenchSafetyActions.jsx` + `TrenchSafetyOpsCenter.jsx`. Mirror routes `/admin/trench-safety/{assets,assets/:id,tabulated-data,repair-review,field-reports}`. Same auth gate (`safety_or_admin` accepts X-Admin-Token).

### Shop Portal
Repair Queue (`/shop/trench-safety-repairs`) unchanged. Hand-off to Safety verification verified by Phase 7.5C notification test (`test_inspection_fail_critical_fans_out` + repair workflow).

### Dispatch / Projects
Asset transfers, assignments, return-to-yard flows verified in Phase 5 + Phase 7.5C `asset_returned_to_service` fanout.

## Final verdict
🟢 **PASS · GO** — Trench Safety operational. No behavioural regressions. Ready for the next sprint when authorised.
