# TRACK 15.51 · Platform Inventory (Phase 1)

**Status:** ✅ Evidence-collected from live preview environment 2026-06-19.

## Counts (live · preview DB)
| Component | Count |
|---|---|
| Backend route modules (`routes/*.py`) | 131 |
| Safety portal route modules (`routes/safety_portal/*.py`) | 12 |
| Frontend pages (`pages/*.jsx`) | 169 |
| Safety topic modules (EN, excluding aggregator) | 23 |
| Safety topics (total) | 152 |
| Incidents | 70 |
| Daily Reports | 1,114 |
| JHAs | 3 |
| Tasks | 3,009 |
| Notifications | 8,887 |
| Corrective Actions (CAPAs) | 42 |
| Safety Training Records | 10 |
| Employees | 396 |
| Jobs Master | 30 |
| User Directory | 162 |
| Incident State Events | 3 |

## Core surfaces (verified live)
- ✅ `GET /api/health` returns ok+service+ts
- ✅ `POST /api/auth/multi-login` returns 7 portal tokens (admin, pm, shop, hr, safety, dispatch, field_leadership, fl)
- ✅ `GET /api/admin/executive/overview` returns foundation_version `15.50.1`
- ✅ `GET /api/incidents` returns list
- ✅ `GET /api/employees` returns 396-row roster
- ✅ `GET /api/safety/corrective-actions` returns CAPA list

## PDF surfaces
- ✅ Universal PDF Foundation `pdf_render.py` covers: daily_report · safety_meeting · jha · incident · po_request · po_receipt · qaqc · field_leadership · safety_form (issuance/return/training) · preop · dvir · fuel_lube · training_certificate
- ✅ Branding wrapper `pdf_branding.py` + `pdf_branding_rl.py` (ReportLab parity)
- ✅ Foundation footer rendering with v15.41.1 audit envelope

## Sign-off
Inventory captured. Platform surface is large but well-organized along the canonical Track 15.41-15.50 architecture.
