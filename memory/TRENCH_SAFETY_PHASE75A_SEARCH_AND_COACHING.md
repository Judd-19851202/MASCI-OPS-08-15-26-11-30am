# Phase 7.5A · Search and Coaching

## Search
The existing platform global search (Hub-level) indexes `equipment_master` documents. Because every trench-safety asset already mirrors into `equipment_master` (via `upsert_equipment_master_mirror` in `_helpers.py`), every Trench Safety asset is **automatically searchable by Asset ID, Manufacturer, Model, Serial Number, and Size** through the existing search index. No parallel index introduced.

- Mirrored fields available to search: `asset_id`, `unit_number`, `year`, `make`, `model`, `make_model`, `vin_serial_number`, `manufacturer`, `serial_number`, `size`, `color`, `condition`, `status`, `location`, `current_project_name`, `current_project_number`.
- Phase 7.5A asset writes (`create_asset`, `update_asset`, retire) all call `upsert_equipment_master_mirror` → search index stays in lock-step.

Phase 7.5A introduces **no new global search bar** — that would duplicate the existing one. Future phases (per directive, Phase 9 includes Global Search expansion) can layer trench-specific facets on the existing index without rewriting it.

## Coaching pattern (every new screen)
Each new dialog and panel surfaces the three coaching dimensions:

| Section | Purpose | Why it matters | What happens next |
|---|---|---|---|
| Asset list `+ New Asset` | "Asset IDs are permanent" | Once printed on a QR poster, the tag can't change without re-printing every label in the field. | Asset Detail opens with audit timeline showing the create event. |
| Create dialog | "Asset ID is permanent. Choose deliberately." | Mistakes here cost decals + field confusion. | Asset enters with status `Available`; appears in field QR within seconds via the mirror. |
| Edit dialog | Asset ID disabled + "Immutable" badge | Prevents accidental rewrites. | Audit logs the field-level changes. |
| Retire dialog | Red banner + "terminal" warning | Retirement removes the asset from active service. | Status becomes `Retired`; field QR shows the retired pill. |
| Status change dialog | "holds cannot be cleared directly through status changes" | Reminds operators of the lifecycle engine. | Validator returns 400 if transition is forbidden. |
| Open Hold | Kind selector + reason | Hold Hierarchy applies (Safety > Cert > Maint > Inspection). | Asset becomes unavailable for assignment immediately. |
| Clear Hold | Original reason shown + release reason required | Audit trail of who released and why. | Hold engine recomputes operational status. |
| Create Inspection | "Fail + Major/Critical auto-opens Inspection Hold and stubs a repair recommendation" | Operators don't have to know which combinations trigger holds — the engine does. | Inspection Hold + Shop queue entry. |
| Upload Certification | Issue / Expires / Issuer required | Drives Certification Hold auto-engine. | OK / Due Soon / Expired / Revoked badge appears immediately. |
| Audit Timeline | "details" disclosure | Engineering visibility without polluting calm default view. | None — read-only. |

All coaching strings are bilingual (EN source + ES in `lib/i18n.js`).

## Help / Navigation integration
- Safety Portal Hub (`/safety/trench-safety`) already exposes a "Quick links" section that points to Trench Equipment and Tabulated Data — these tiles now open into the new Command Center UIs without modification.
- Admin Portal entries reuse the same Trench Safety Hub component when routed via `/admin/trench-safety` so the navigation experience is identical.
- Legacy `/trench-boxes` route preserved as a redirect — no broken bookmarks.

## What Phase 7.5A does NOT touch
- No global navigation rewrite. Adding a "Trench Safety" item to the platform-wide nav is a separate scope item (Phase 9, per directive).
- No platform-wide help index regen — the existing search index picks up trench safety records via `equipment_master` already, and coaching strings are co-located with their screens.
