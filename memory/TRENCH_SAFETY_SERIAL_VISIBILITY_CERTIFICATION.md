# Trench Safety — Serial Number Visibility Certification
**Sprint:** Public Trench Safety UX Correction
**Date:** 2026-02-07

---

## 1. Directive
Every public asset / QR field view must show **Serial Number** clearly near the top, alongside Asset ID, Asset Type, Size, Color, Condition, Status, Location, Project, and Tabulated Data status. For TB-05 (no serial on file) the surface must read:

> Serial Number: Missing — Action Required

---

## 2. Backend
File: `backend/routes/trench_safety/_helpers.py` · function `public_view(asset)`
- Added `serial_number` to the field-safe `keep` set.
- The pre-existing `missing_serial_number` boolean is unchanged and continues to drive the alert.
- No other internal data is exposed.

Verification:
```bash
$ curl -s /api/trench-safety/public/assets/TB-01 | jq .serial_number
"C080102"

$ curl -s /api/trench-safety/public/assets/TB-05 | jq '{serial_number, missing_serial_number}'
{ "serial_number": "", "missing_serial_number": true }
```

---

## 3. Frontend
File: `frontend/src/pages/trench_safety/TrenchSafetyQrLanding.jsx`

### 3.1 Hero block (near the top)
A dedicated `Serial Number` block sits inside the hero card directly beneath the status pill:
- **Present serial** (TB-01) — slate background, monospace bold text rendering `C080102`.
- **Missing serial** (TB-05) — red bordered card with the value `Missing — Action Required` in red, followed by an alert line: *"Verify the physical serial plate before use · Report to Safety"*.

### 3.2 Asset Details table
A new `Serial Number` row is added to the Asset Details table — it shows the value in monospace bold, and when the serial is missing it shows the same `Missing — Action Required` warning in amber/red font so the field also surfaces it lower on the page.

### 3.3 Decision logic
```js
const serialMissing = doc
  ? Boolean(doc.missing_serial_number) || !(doc.serial_number && String(doc.serial_number).trim())
  : false;
```
This is intentionally permissive: it trusts the explicit projection flag first, then falls back to a literal empty/whitespace serial. That covers data-quality drift in either direction.

---

## 4. Visual proof
- **TB-01 (with serial)** — Hero block reads:
  ```
  SERIAL NUMBER
  C080102
  ```
- **TB-05 (missing)** — Hero block reads (red border):
  ```
  SERIAL NUMBER
  Missing — Action Required
  ⚠ VERIFY THE PHYSICAL SERIAL PLATE BEFORE USE · REPORT TO SAFETY
  ```

Playwright assertions:
```
TB01 serial='C080102' missing_alert=0
TB05 serial='Missing — Action Required' missing_alert=1
```

---

## 5. Complete public asset surface coverage

| Field | Present on QR landing |
|---|---|
| Asset ID | ✅ (hero giant text + details row) |
| Asset Type | ✅ (hero subtitle + details row) |
| Size | ✅ |
| Serial Number | ✅ — prominent block near the top + details row |
| Color | ✅ |
| Condition | ✅ |
| Status | ✅ (large pill) |
| Location | ✅ (Current Use card) |
| Project (if assigned) | ✅ (Current Use card) |
| Tabulated Data status | ✅ (Current Use card — flags missing) |

---

## 6. Verdict
🟢 **Serial Number is now visible near the top on every public asset / QR field view. TB-05 surfaces the `Missing — Action Required` alert exactly as specified.**
