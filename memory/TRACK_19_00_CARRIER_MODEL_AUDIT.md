TRACK 19.00 · CARRIER MODEL AUDIT
==================================

DATE   : 2026-06-29
SCOPE  : Audit `carriers` and the carrier endpoints. Records the
         Track 19.00 permission opening for dispatcher create/edit.

────────────────────────────────────────────────────────────────────────────
COLLECTION
────────────────────────────────────────────────────────────────────────────
`carriers` — single source of truth for Transportation carriers
(leased haulers, owner-operators, suppliers, MASCI-internal carriers).

────────────────────────────────────────────────────────────────────────────
DOCUMENT SHAPE
────────────────────────────────────────────────────────────────────────────
Identity:
  · `id`                  UUID
  · `tenant`              "masci"
  · `legal_name`          required
  · `dba_name`            optional display name
  · `carrier_type`        one of:
                            · leased_hauler
                            · owner_operator
                            · supplier
                            · masci_internal
                            · other

Regulatory references:
  · `dot_number`          US DOT number (string)
  · `mc_number`           MC number (string, optional)

Contact:
  · `contact_name`        primary contact / dispatch contact
  · `contact_phone`
  · `contact_email`

Operational status:
  · `status`              "pending_review" · "active" · "suspended" · "inactive"
  · `safety_hold`         bool — Transportation-side hold from dispatch
  · `notes`

Audit metadata:
  · `created_at`, `created_by`
  · `updated_at`, `updated_by`

────────────────────────────────────────────────────────────────────────────
ENDPOINTS
────────────────────────────────────────────────────────────────────────────
| Endpoint                                              | Read     | Write          |
|-------------------------------------------------------|----------|----------------|
| GET   /api/admin/transportation/carriers              | dispatch | —              |
| GET   /api/admin/transportation/carriers/{cid}        | dispatch | —              |
| POST  /api/admin/transportation/carriers              | —        | dispatch+admin |
| PATCH /api/admin/transportation/carriers/{cid}        | —        | dispatch+admin |

Audit events fire on create/update via the shared `_audit` helper.

────────────────────────────────────────────────────────────────────────────
FRONTEND
────────────────────────────────────────────────────────────────────────────
Surface: `/transportation-operations/carriers` and
`/admin/transportation/carriers/{id}`.

Component: `/app/frontend/src/pages/transportation/_lists.jsx :: CarriersList`.

Track 19.00 added:
  · `[Add Carrier]` page-level CTA → `AddCarrierModal`
  · Per-row `[Edit]` action → `EditCarrierModal`

────────────────────────────────────────────────────────────────────────────
DOCUMENTS / COMPLIANCE
────────────────────────────────────────────────────────────────────────────
Existing surface: each carrier workspace already supports document
upload via `DocumentDropzone` with the carrier doc-type set:
  · sunbiz_certificate
  · mcs_company_snapshot
  · w9
  · insurance_certificate
  · hauling_agreement
  · vehicle_registration
  · lien_release_authorization
  · payment_pickup_authorization
  · other

These ride on the existing transport document collection and are
unchanged by Track 19.00.

────────────────────────────────────────────────────────────────────────────
RIGHT RAIL / RELATIONSHIPS
────────────────────────────────────────────────────────────────────────────
Carrier ↔ drivers, carrier ↔ trucks, carrier ↔ documents, carrier ↔
orientation. Unchanged by Track 19.00 — the new write surface
participates in the existing right-rail wiring.

────────────────────────────────────────────────────────────────────────────
PRE-TRACK 19.00 GAPS
────────────────────────────────────────────────────────────────────────────
  · POST / PATCH `/carriers` were admin-only — dispatchers could see
    carriers but had to escalate to Admin to add or update one.
  · There was no "Add Carrier" CTA on the Carriers list page.

────────────────────────────────────────────────────────────────────────────
POST-TRACK 19.00 STATE
────────────────────────────────────────────────────────────────────────────
  · Dispatchers and admins can create AND edit carriers from inside
    Transportation Operations.
  · No raw 401/403 surfaces — restricted-state plumbing remains in
    place for any future endpoint that returns 401/403.
  · Modal-based UX keeps the dispatcher in context.

────────────────────────────────────────────────────────────────────────────
DEFERRED (NOT IN SCOPE FOR TRACK 19.00)
────────────────────────────────────────────────────────────────────────────
  · Insurance expiration field on the carrier root document (today
    expirations are tracked at the document level — insurance
    certificate has its own expiration field via the document model).
  · W9 status flag on the carrier root document.
  · Carrier safety rating (FMCSA-sourced) — would require an external
    integration; intentionally not fabricated.
  · Agreement / contract status flag on the carrier root document.

Compliance status modelling can be added in a follow-on track without
reworking the Track 19.00 write surface.
