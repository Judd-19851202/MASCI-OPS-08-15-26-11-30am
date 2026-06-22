# TRACK 15.68D · Admin Tab Label Sweep

_Generated 2026-06-22_

## Objective

Replace customer-visible MASCI labels in five admin tab files with
neutral, operationally meaningful terms. Preserve all backend API
contracts (object property reads, localStorage keys, CSV column names
that are literal schema columns).

## Files Touched

### 1. `frontend/src/components/admin/MaintainxP0Tab.jsx`

| Line | Before | After |
|---|---|---|
| 159 | `MASCI equipment records` | `company equipment records` |
| 372 | `matches them to MASCI equipment` | `matches them to company equipment` |
| 374 | `MaintainX or MASCI. "Run + Save Report"…` | `MaintainX or the platform inventory. "Run + Save Report"…` |
| 422 | `" · MASCI "` (dryrun report tally label) | `" · Company "` |
| 441 | `label: "MASCI count"` | `label: "Company count"` |
| 446 | `label: "Missing in MASCI"` | `label: "Missing in platform"` |

Object property reads (`r.totals?.masci_equipment_count`,
`missing_in_masci`) preserved — these are backend API field names.

### 2. `frontend/src/components/admin/MappingCleanupTab.jsx`

| Line | Before | After |
|---|---|---|
| 145 | Comment: `MASCI employee / equipment` | `company employee / equipment` |
| 186 | `Pick {MASCI equipment / MASCI employee}` | `Pick {company equipment / company employee}` |
| 313 | `<th>Existing MASCI Match</th>` (driver table) | `<th>Existing Match</th>` |
| 490 | `<th>Existing MASCI Match</th>` (asset table) | `<th>Existing Match</th>` |
| 623 | `Every MASCI record currently has at most one Motive owner.` | `Every internal record currently has at most one Motive owner.` |

Mapping payload reads (`c.mapping_a?.masci_unit_number`, etc.) preserved
— these are API response field names.

### 3. `frontend/src/pages/admin/AdminIntegrationCenter.jsx`

| Line | Before | After |
|---|---|---|
| 549 | `Link a MASCI equipment record to Motive + MaintainX IDs.` | `Link a company equipment record to Motive + MaintainX IDs.` |
| 550 | `Link a MASCI employee to Motive driver + MaintainX user.` | `Link a company employee to Motive driver + MaintainX user.` |
| 766–767 | `must include a <code>masci_equipment_id</code> (asset rows) or <code>masci_employee_id</code> (driver rows)` | `must include an internal asset key (column: <code>masci_equipment_id</code>, legacy name) for asset rows, or an internal employee key (column: <code>masci_employee_id</code>, legacy name) for driver/user rows` |
| 1014 | `match by MASCI unit number` | `match by company unit number` |
| 1242 | Comment: `Motive ↔ MASCI Auto-Link button.` | `Motive ↔ Company Auto-Link button.` |
| 1289 | `This will link Motive {target} to MASCI {equipment/employees}` | `… to company {equipment/employees}` |
| 1307 | `<th>MASCI</th>` (autolink preview header) | `<th>Company</th>` |

Field names (`masci_equipment_id`, `masci_employee_id`,
`masci_unit_number`, `masci_employee_name`, etc.) and the localStorage
key `masci.admin.token` preserved — functional contracts.

**Documented exception:** the literal CSV column header names
`masci_equipment_id` / `masci_employee_id` are kept inside `<code>` tags
because the backend asset-mapping ingest still expects those literal
columns. Surrounding prose now frames them as "internal asset/employee
key (column: …, legacy name)" so a tenant admin understands they are
internal identifiers, not a customer-brand reference. A future
schema-rename track (Track 16.x candidate) would migrate the underlying
column names to `internal_equipment_id` / `internal_employee_id`.

### 4. `frontend/src/pages/admin/AdminDlsShiftQR.jsx`

This page renders a printable Driver Shift Start QR card — the carrier
label is physically printed on truck-cab stickers, so it must reflect
the active tenant's brand, not a hardcoded "MASCI".

Changes:

- Imported `useBranding` from `@/lib/BrandingProvider`.
- Derived `brandShort = branding.platform_short_name || branding.company_name || "Operations"` and
  `brandCarrier = branding.company_name || brandShort || "Carrier"`.
- `usePageTitle("Shift Start QR · Dispatch · MASCI")` →
  `usePageTitle(\`Shift Start QR · Dispatch · ${brandShort}\`)`.
- `useState("MASCI")` for `carrierLabel` → `useState(brandCarrier)`.
- `placeholder="MASCI"` on the carrier input → `placeholder={brandCarrier}`.
- Print-card fallback `{carrierLabel || "MASCI"}` →
  `{carrierLabel || carrierFallback || "Carrier"}` (carrier fallback
  passed in from the parent and derived from `branding`).

MASCI tenant continues to render `"MASCI"` as the default carrier label
because `branding.company_name === "MASCI"` for the masci tenant.

### 5. `frontend/src/pages/admin/AssetProfile.jsx`

| Line | Before | After |
|---|---|---|
| 1 | File comment: `MASCI master` | `the company master` |
| 141 | `<Field label="MASCI ID" …>` | `<Field label="Asset ID" …>` |
| 240 | `This MASCI equipment record is not yet linked…` | `This company equipment record is not yet linked…` |
| 312 | `mapping?.masci_equipment_id ? "Linked to MASCI" : "Unlinked"` | `… ? "Linked" : "Unlinked"` |
| 471 | `<h3>MASCI operations events</h3>` | `<h3>Operations events</h3>` |

Field reads (`mapping?.masci_equipment_id`) preserved — API contract.

## Backend Contract Preservation

The following identifiers remain literal `masci`-named because they are
backend / API contracts, NOT customer-visible chrome:

- Object property reads from `/api/admin/integrations/...` responses:
  `masci_equipment_id`, `masci_employee_id`, `masci_unit_number`,
  `masci_equipment_name`, `masci_employee_name`,
  `masci_employee_trade`, `masci_employee_role`,
  `masci_equipment_count`, `missing_in_masci`.
- localStorage key `masci.admin.token` (single-tenant admin token store).
- CSV-import column header names `masci_equipment_id` /
  `masci_employee_id` (literal column names accepted by the ingest
  endpoint).
- Code comments that document historical field names.

Changing any of these would break the dry-run/ingest endpoints and the
admin-tier mapping wizard. These are flagged as Tier-2 schema-rename
work for a future track and explicitly documented in
`PRD.md`.

## Lint

All five files lint clean. (Pre-existing `react-hooks/exhaustive-deps`
warnings in `AdminIntegrationCenter.jsx` are untouched and predate this
track.)

## Verdict

✅ **PASS** — Visible labels are neutral / company-scoped. Backend
contracts intact. MASCI tenant unchanged.
