# Phase 7.5A · Asset Management

## Endpoints exposed
- `POST /api/trench-safety/assets` — create
- `PUT  /api/trench-safety/assets/{id}` — edit (Asset ID immutable; ignored if present in body)
- `POST /api/trench-safety/assets/{id}/status` — change status (validated against `validate_status_transition`)
- `POST /api/trench-safety/assets/{id}/retire` — retire (`require_admin` retained; admin terminal action)
- `GET  /api/trench-safety/assets/{id}/audit` — full audit timeline

All write endpoints accept Safety **or** Admin tokens via the shared `safety_or_admin` factory.

## UI components (in `TrenchSafetyActions.jsx`)
- `CreateAssetDialog` — `AssetForm` with: Asset ID *, Asset Type *, Manufacturer, Model, Serial, Size, Color, Weight, Rated Depth, Rated Soil, Condition, Yard/Location, Notes, Requires Certification.
- `EditAssetDialog` — same form, Asset ID disabled and labelled "Immutable".
- `RetireAssetDialog` — confirmation + reason; red-bordered "terminal" warning.
- `StatusChangeDialog` — target status + reason; respects `validate_status_transition`.

## Asset ID immutability
- Form input is `disabled` when `isEdit=true`.
- `EditAssetDialog.save()` explicitly deletes `asset_id` from payload before PUT.
- Backend `TrenchSafetyAssetUpdate` already ignores `asset_id`.

## Action surfaces
- `/safety/trench-safety/assets` (list) — `+ New Asset` CTA visible to Safety and Admin.
- `/safety/trench-safety/assets/:assetId` — Edit Asset · Change Status · Retire buttons inline with existing Assign/Return.
- `/admin/trench-safety/assets` and `/admin/trench-safety/assets/:assetId` mirror the same components.

## Validation curl (admin token)
```
POST /api/trench-safety/assets {"asset_id":"TB-P75A","asset_type":"Trench Box","size":"6x16","condition":"Good"}
→ 200 · asset_id=TB-P75A · operational_status=Available
GET /api/trench-safety/assets/TB-P75A/audit → 200 · 1 audit event (created)
POST /api/trench-safety/assets/TB-P75A/retire {"reason":"…"} → 200 · operational_status=Retired
```

## Coaching
"Asset IDs (TB-01, EP-001…) are permanent once created. Safety and Admin can both create, edit, and retire." (visible above the list)
"Asset ID is permanent. Choose deliberately — TB-01, EP-001, SP-001, etc." (Create dialog)
"Retirement is terminal. Reactivation requires an admin edit." (Retire dialog)
