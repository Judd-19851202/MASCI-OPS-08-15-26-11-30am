# Phase 7.5A · Audit History

## Source
- `GET /api/trench-safety/assets/{id}/audit` (existing endpoint, `require_any_portal`).
- Reads from the platform-wide `db.audit_events` collection — **no parallel audit system created**.

## Events captured (engine already in place from Phases 2 → 6)
| Kind | Trigger |
|---|---|
| `trench_asset_created` | `POST /assets` |
| `trench_asset_updated` | `PUT /assets/{id}` |
| `trench_asset_status_changed` | `POST /assets/{id}/status` |
| `trench_asset_retired` | `POST /assets/{id}/retire` |
| `trench_asset_hold_opened` | `open_hold()` |
| `trench_asset_hold_cleared` | `clear_hold()` |
| `trench_asset_inspection_recorded` | `POST /inspections` |
| `trench_asset_certification_uploaded` | `POST /certifications` |
| `trench_asset_certification_revoked` | `POST /certifications/{id}/revoke` |
| `trench_asset_repair_*` | repair lifecycle |
| `trench_asset_qr_label_*` | Phase 7 QR audit |
| `trench_asset_damage_reported_public` | public damage report |

## UI — `AuditTimelinePanel`
- Renders a left-rail timeline with a cyan dot per event.
- Shows `kind` (humanised), `ts` (UTC, 16-char slice), `actor` (`safety:name` / `admin:Admin` / `system` / `public:…`).
- Click-to-expand `details` JSON for deep inspection without polluting the calm default view.
- data-testid: `audit-panel`, `audit-row-{id}`, `audit-empty`.

## Coverage matrix vs directive
| Required | Status |
|---|---|
| Created | ✅ |
| Edited | ✅ (`trench_asset_updated`) |
| Assigned / Moved | ✅ (deployment audit kinds from Phase 5) |
| Inspected | ✅ |
| Held / Released | ✅ |
| Certified / Recertified | ✅ |

The Phase 7.5A UI surfaces them all by rendering whatever `audit_events.find({asset_id})` returns — no whitelisting, so any future event types appear automatically.
