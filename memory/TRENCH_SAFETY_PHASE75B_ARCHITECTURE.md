# Phase 7.5B + Phase 7 — Architecture
**Date:** 2026-02-07
**Verdict:** 🟢 GO

## Mission
Complete the actual field and safety workflows by wiring the operations surfaces that were left in Phase 7.5A's backlog: Safety Repair Review, Field Reports inbox, QR Management, Photo Management, and Daily Posture.

## Surface ownership (per directive)
- **Public Safety Tile** — Field reference only. No write surfaces.
- **Safety Portal** — Primary Command Center. Owns every write surface in this phase.
- **Admin Portal** — 100% feature parity via shared components. Routes mirror Safety Portal routes; backend gate (`safety_or_admin`) accepts either token.
- **Shop Portal** — Repair execution only. Never clears Safety Holds. Safety owns verification.

## Shared module
**NEW** `frontend/src/pages/trench_safety/TrenchSafetyOpsCenter.jsx` exports:
- `DailyPosturePanel` — top-of-portal posture strip.
- `SafetyRepairReview` — Repair Review queue with filters + Verify dialog.
- `SafetyFieldReports` — Field Reports inbox + actions.
- `QRManagementPanel` — Generate / Download / Print / Log Reprint / History.
- `PhotoManagementPanel` — Upload / Categorise / Visibility / Delete grid.

## Page wrappers (so both portals consume the same components)
- `TrenchSafetyRepairReviewPage` — `/safety/trench-safety/repair-review` and `/admin/trench-safety/repair-review`.
- `TrenchSafetyFieldReportsPage` — `/safety/trench-safety/field-reports` and `/admin/trench-safety/field-reports`.

## Backend reuse (zero new endpoints)
- `GET /api/trench-safety/dashboard` → Daily Posture metrics + Hub KPIs.
- `GET /api/trench-safety/shop/repairs` → Repair Review queue (filterable; field reports filtered client-side by `source` containing "Public").
- `POST /api/trench-safety/repairs/{id}/verify` → Safety verification (`safety_or_admin` gate from Phase 6).
- `PATCH /api/trench-safety/repairs/{id}` → Close / re-route field reports.
- `GET /api/trench-safety/assets/{id}/qr-label.png` → QR PNG (Phase 7 backend).
- `POST /api/trench-safety/assets/{id}/qr-label/audit` → Log reprint (Phase 7 backend).
- `GET /api/trench-safety/assets/{id}/photos` → Photo list.
- `POST /api/trench-safety/assets/{id}/photos` → Upload with `image_data_url`, `category`, `visibility`, `caption`, `source` (Phase 7 backend, re-gated `safety_or_admin` in Phase 7.5C).
- `DELETE /api/trench-safety/photos/{id}` → Delete.
- `GET /api/trench-safety/public/assets/{id}/photos` → Public projection (only Field Safe + Public visibility).

## Constraints honoured
- No new collections, no new endpoints, no demos, no mocks, no dead buttons.
- Repair Complete ≠ Safe To Use — UI never auto-releases Inspection Hold; the Verify dialog explicitly explains it.
- Internal photos never leak to the public surface (the public projection endpoint already filters).

## Routes
| Surface | Route | Notes |
|---|---|---|
| Safety Portal Hub | `/safety/trench-safety` | Daily Posture strip on top |
| Safety Repair Review | `/safety/trench-safety/repair-review` | Filters: all / awaiting / critical / vendor / completed / closed |
| Safety Field Reports | `/safety/trench-safety/field-reports` | Filter by report kind |
| Asset Detail | `/safety/trench-safety/assets/:id` | + QR panel + Photo panel |
| Admin mirrors | `/admin/trench-safety/repair-review`, `/admin/trench-safety/field-reports` | Same components |
