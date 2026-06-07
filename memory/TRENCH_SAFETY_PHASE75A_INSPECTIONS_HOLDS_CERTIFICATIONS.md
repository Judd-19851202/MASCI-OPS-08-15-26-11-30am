# Phase 7.5A · Inspections · Holds · Certifications

## Inspections
- `CreateInspectionDialog` (`POST /api/trench-safety/assets/{id}/inspections`).
- Inspection types: `Daily Visual`, `Monthly Competent Person`, `Annual Review`, `Special Inspection`, `Damage Inspection`, `Return Inspection`.
- Results: `Pass` / `Fail`.
- Severities: `Minor` / `Major` / `Critical`.
- Coaching panel reminds the operator that **Fail + Major/Critical auto-opens an Inspection Hold and stubs a repair recommendation** (Phase 4B engine).
- `InspectionsPanel` lists last 25 with date, inspector, type, result, severity, notes.

## Holds
- `OpenHoldDialog` (`POST /api/trench-safety/assets/{id}/holds`) — kinds: Safety / Inspection / Maintenance / Certification.
- `ClearHoldDialog` (`POST /api/trench-safety/assets/{id}/holds/{hold_id}/clear`) — release reason required.
- `HoldsPanel` lists only active holds; "Release" button per row → opens Clear dialog.
- Hold engine (Phase 4B `apply_resolved_status`) drives the operational status — the dialogs never write status directly.
- Validation curl confirmed: `POST /…/holds` returns `operational_status=Safety Hold` after open.

## Certifications
- `UploadCertificationDialog` (`POST /api/trench-safety/assets/{id}/certifications`) — kinds: Manufacturer / Annual Inspection / Engineering Letter / Repair Certification / Special.
- Required fields: `kind`, `issuer`, `issued_at`, `expires_at`.
- `CertificationsPanel` renders rows with a status badge:
  - **OK** (>90 days) — emerald
  - **Due Soon** (≤90 days) — amber
  - **Expired** — red
  - **Revoked** — slate
- Revoke uses `POST /…/certifications/{id}/revoke` and is gated by the same `safety_or_admin` factory.
- Engine integration: `recompute_certification_hold` opens/clears the Certification Hold automatically based on expiry — the dialogs never manage the Cert Hold directly.

## Visual + i18n
- All dialogs use shadcn `Dialog` + `Select` + `Input` + `Textarea` + `Button` (same shapes used elsewhere in MASCI).
- Every label, helper line, toast, and error has an EN→ES translation in `lib/i18n.js`.
- "details" disclosure on Audit Timeline preserves engineering visibility without polluting the calm default view.

## Coverage
| Section | Backend | UI | EN | ES | data-testid |
|---|---|---|---|---|---|
| Inspections | ✅ | ✅ Create + List | ✅ | ✅ | `create-inspection-dialog`, `insp-row-*` |
| Holds | ✅ | ✅ Open + Clear + List | ✅ | ✅ | `open-hold-dialog`, `clear-hold-dialog`, `hold-row-*` |
| Certifications | ✅ | ✅ Upload + Revoke + List w/ badge | ✅ | ✅ | `upload-cert-dialog`, `cert-row-*`, `cert-revoke-*` |
