# TRENCH SAFETY PHASE 3 — MOBILE QR LANDING CERTIFICATION

**Phase:** 3 of 11
**Verdict:** 🟢 MOBILE-FIRST CERTIFIED · FIELD-SAFE PROJECTION VERIFIED

---

## 1. Route + auth

| Route | Auth | Notes |
|---|---|---|
| `/trench-safety/assets/:assetId` | **PUBLIC** (no token) | Hit anonymously from a phone scan |
| `GET /api/trench-safety/public/assets/{asset_id}` | **PUBLIC** (no token) | Phase 2 backend endpoint consumed |

## 2. Field-safe projection (server-side)

The server returns a HARDENED projection from `routes/trench_safety/_helpers.py::public_view()` — only these fields ever reach the wire:

```
asset_id, asset_type, manufacturer, model, size,
rated_depth_ft, rated_soil_type, color, condition,
operational_status, current_location, current_project_name,
last_inspection_at, next_inspection_due, certification_expires_at,
tabulated_data_missing, missing_serial_number, needs_review, qr_url
```

NOT returned (and therefore not renderable):
- `created_by`, `updated_by`, `assigned_to_name`, `assigned_to_role`
- `purchase_cost`, `purchase_date`, `notes`
- Audit trail / inspection details / repair details / deployment IDs
- Internal `id` (UUID) — only the public `asset_id` (TB-07) is exposed

Verified live:
```
$ curl https://safety-audit-mobile-1.preview.emergentagent.com/api/trench-safety/public/assets/TB-05
keys: asset_id, asset_type, manufacturer, model, size, rated_depth_ft, rated_soil_type,
      color, condition, operational_status, current_location, current_project_name,
      last_inspection_at, next_inspection_due, certification_expires_at,
      tabulated_data_missing, missing_serial_number, needs_review, qr_url
```

No PII keys, no admin keys, no audit keys. ✅

## 3. UI safety surface (frontend-side)

The QR landing page (`TrenchSafetyQrLanding.jsx`) renders:

| ✅ Shows | ❌ Does NOT show |
|---|---|
| Asset ID (big · centered) | Edit / Delete / Retire / Assign / Return buttons |
| Asset type, size, color | Cost / purchase data |
| Status pill (Available / Inspection Hold / Repair / etc.) | Internal audit IDs |
| **DO NOT USE** banner when on Hold or Repair | Inspection / repair detail timestamps |
| Missing-serial / Needs-review banners | Full inventory listing |
| Manufacturer, Model, Size, Color, Condition | Other assets' data |
| Current location + project | Assigned-to person name |
| Last inspection date | User session info |
| Tabulated Data status | Login forms / admin controls |
| Single CTA → "Open Tabulated Data" (public reference) | "Edit", "Inspect", "Report Damage" submit forms |

The "Report Damage" intake from the public endpoint exists at the API layer but is intentionally NOT wired into Phase 3 UI — it's a Phase 7+ surface (per directive).

## 4. Mobile-first construction

- `<div className="max-w-md mx-auto …">` — content column locked to 28rem (448 px) regardless of viewport, so the same component is the canonical experience on phones and benignly margined on desktop.
- Header is 56-px tall, single row, `LangToggle` + MasciLogo + Home back-link.
- Status pill is a centered ring (`ring-2`, `rounded-full`) with `text-sm font-bold uppercase tracking-[0.12em]` — readable on a dusty phone screen.
- Field rows use `flex justify-between` with mono labels left and large bold values right — scannable in one glance.
- CTA button is a full-width cyan-700 block at `py-3` — easy to tap with gloves.
- No tables. No tiny text. No tooltips (touch can't see hover).

## 5. Smoke evidence

Screenshot captured at `/tmp/qr_tb05.jpg` using viewport `420 × 900` (iPhone-class portrait). Visible elements:

```
caution stripe         · MASCI brand bar
HOME ← MasciLogo  EN|ES
[scan icon] MASCI TRENCH SAFETY · FIELD VIEW
┌──────────────────────────────────┐
│         TRENCH BOX               │
│          TB-05                   │   ← large hero
│       8x16 · Brown/Rust          │
│         ┌─────────────┐          │
│         │  AVAILABLE  │          │   ← status pill
│         └─────────────┘          │
└──────────────────────────────────┘

[!] Serial number not on file — verify
    the physical plate before use.        ← amber warning visible

ASSET DETAILS
  MANUFACTURER  —
  MODEL         —
  SIZE          8x16
  COLOR         Brown/Rust
  CONDITION     Fair

CURRENT USE
  STATUS              Available
  CURRENT LOCATION    MASCI Yard
  CURRENT PROJECT     —
  LAST INSPECTION     — (amber/“never”)
  TABULATED DATA      missing (amber)

[BookOpen icon]  OPEN TABULATED DATA      ← full-width cyan CTA
```

Console logs were clean — no compile errors, no runtime warnings.

## 6. Coaching present

Bottom of every QR page:

> **Coaching:** Scanning confirms the asset record — it does not move the asset. Location updates when the asset is assigned, transported, or returned. Report damage before the box goes into the trench.

Spanish parity:

> **Recomendación:** El escaneo confirma el registro del activo — no mueve el activo. La ubicación se actualiza cuando el activo se asigna, transporta o devuelve. Reporte daños antes de que la caja entre a la zanja.

## 7. Verdict

🟢 **MOBILE QR LANDING CERTIFIED.**

- Public endpoint returns hardened projection — no admin / audit / PII leakage.
- UI surfaces zero write actions to anonymous viewers.
- Mobile viewport (420 px) renders cleanly with one-thumb reach for every interactive element.
- EN/ES parity verified.
- "Do not use" banner appears for Inspection Hold + Repair statuses.
- TB-05 missing-serial alert visible on the live preview.

QR scan does NOT change asset location. (Required guidance string present in EN+ES.)
