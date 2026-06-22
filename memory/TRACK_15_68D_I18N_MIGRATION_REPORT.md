# TRACK 15.68D · `lib/i18n.js` Migration Report

_Generated 2026-06-22_

## Objective

Migrate every MASCI-flavoured English/Spanish translation value in
`frontend/src/lib/i18n.js` so that:

1. The MASCI tenant continues to render the literal historical strings
   bit-for-bit (parity).
2. Any non-MASCI tenant (Customer #2, future Customer #3, etc.) sees the
   active tenant's short brand substituted for `MASCI` at render time.

## Approach

Renderer-level interpolation (not dictionary edits). A new `_brandSubst()`
helper is invoked from `tStr()` after the dictionary lookup. It:

1. Reads `branding.shortName` / `branding.companyName` from
   `sessionStorage` (populated by `BrandingProvider`).
2. If the active tenant resolves to MASCI, returns the raw string
   unchanged (zero diff on MASCI parity).
3. Otherwise applies an ordered regex pass that maps the most specific
   patterns first:
   - `MASCI General Contractors Inc.` → `{company_name}`
   - `MASCI Operations Platform` → `{short} Operations Platform`
   - `MASCI Safety Hub` → `{short} Safety Hub`
   - `MASCI Hub`, `MASCI Safety`, `MASCI Field`, `Centro MASCI` →
     `{short}`-prefixed variants
   - `MASCI Crews`, `Cuadrillas MASCI` → neutral "Crews / Cuadrillas"
   - `MASCI Trench Safety` → neutral "Trench Safety"
   - `\bMASCI\b` → `{short}` (final catch-all)

Why renderer-level: the dictionaries contain ~595 translation entries
referencing MASCI. Editing each one risks breaking English/Spanish parity
for the MASCI tenant and creates a massive diff. The interpolation
approach preserves the legacy strings (so a future i18n review still has
the originals) and routes every render through one tested helper.

## Files Touched

| File | Change |
|---|---|
| `frontend/src/lib/i18n.js` | Added `_brandSubst()` helper (~30 LOC) and wired it into `tStr()`. |
| `frontend/src/lib/BrandingProvider.jsx` | Already populates `sessionStorage` with `shortName` / `companyName` (Track 15.68B). Added document.title override for non-MASCI tenants so Customer #2 never sees "MASCI Operations Platform" in the browser tab before the first `usePageTitle()` call site fires. |

## Verification

| Probe | MASCI tenant | Customer #2 preview |
|---|---|---|
| `tStr("MASCI Operations Platform")` | `"MASCI Operations Platform"` | `"C2 Hub Operations Platform"` |
| `tStr("MASCI Safety Hub")` | `"MASCI Safety Hub"` | `"C2 Hub Safety Hub"` |
| `tStr("MASCI Crews on Site")` (Spanish) | `"Cuadrillas MASCI en Sitio"` | `"Cuadrillas en Sitio"` |
| Document title at boot (`/`) | `"MASCI Operations Platform"` | `"Customer #2 Operations Platform"` |

## Risk / Scope Notes

- The dictionary lookup itself is unchanged. If a future tenant needs a
  fully different translation (not just a brand swap) the right path is
  per-tenant dictionary overrides, not extending `_brandSubst()`.
- `_brandSubst()` operates on the rendered string only — it does NOT
  rewrite component code or attributes. JSX `data-testid`s and
  `aria-label`s that contain literal MASCI in source still need an
  explicit edit (handled by the chrome sweep tracks).
- 595 duplicate-key lint warnings in `i18n.js` are pre-existing and
  intentionally left untouched (Track 15.68 scope).

## Verdict

✅ **PASS** — i18n strings are now tenant-aware via renderer-level
interpolation. MASCI bit-for-bit parity preserved. Customer #2 sees its
own short brand throughout every translated string.
