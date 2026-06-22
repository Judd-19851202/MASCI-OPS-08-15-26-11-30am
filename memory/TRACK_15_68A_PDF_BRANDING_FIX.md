# TRACK 15.68A · PDF Branding Fix

_Status: ✅ SHIPPED_

## What changed (`backend/pdf_branding.py`)
`get_white_label()` now reads the active tenant's `tenant_branding` doc FIRST, then falls back to `PDF_BRAND_*` env vars, then to the historical MASCI defaults.

```python
def get_white_label() -> WhiteLabelConfig:
    tenant_brand = _read_tenant_brand_sync()   # ← NEW
    return WhiteLabelConfig(
        brand_name=tenant_brand.get("brand_name") or env or DEFAULT,
        brand_long_name=tenant_brand.get("brand_long_name") or env or DEFAULT,
        brand_logo_url=tenant_brand.get("brand_logo_url") or env or "",
        brand_color=tenant_brand.get("brand_color") or env or DEFAULT,
        footer_tagline=tenant_brand.get("footer_tagline") or env or DEFAULT,
        company_legal_name=tenant_brand.get("company_legal_name") or env or DEFAULT,
        platform_owner="ForgedOps™",
    )
```

`_read_tenant_brand_sync()` synchronously hits `db.tenant_branding` via `pymongo` (so it works inside the WeasyPrint render context). Returns `{}` for the MASCI tenant (preserving bit-for-bit identical MASCI PDFs).

## What changed in PDF generators
- `pdf_render.py` — wired `get_white_label()` into the main PDF wrapper. `<title>`, `<header><img alt>` and the @bottom-left footer-tagline now use the resolved brand strings.
- `pm_welcome_pdf.py` — wired `get_white_label()`. Header lockup `alt`, footer brand text, mark `alt` attribute all use `wl.brand_name`.

## Proof
```bash
cd /app/backend && python3 -c "
from dotenv import load_dotenv; load_dotenv()
from tenant_context import set_current_tenant
import pdf_branding
set_current_tenant('track_15_68_tenant_test_delete')
wl = pdf_branding.get_white_label()
print(wl.brand_name)       # → Customer #2 Construction LLC
print(wl.brand_long_name)  # → Customer #2 Operations Platform
print(wl.brand_color)      # → 0F766E
print(wl.footer_tagline)   # → 'Generated through Customer #2 Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™'
"
```
**Result: ZERO MASCI strings.**

## PDF audit
| PDF generator | Tenant-aware? |
|---|:--:|
| `pdf_render.py` main wrapper (daily reports / inspections / meetings / incidents / JHAs / equipment / training) | ✅ |
| `pm_welcome_pdf.py` | ✅ |
| `pdf_branding.wrap_pdf_html()` chrome helpers | ✅ (env-driven, now tenant-resolved) |

## Filename templates (Phase 7 partial)
Frontend filename templates like `MASCI_DR_${id}.pdf` (in `ViewDailyReport.jsx`, `ViewInspection.jsx`, `AdminSafetyFormsPanel.jsx`) still hardcode "MASCI". **Not migrated this fork.** Listed in `TRACK_15_68A_FILENAME_EXPORT_SWEEP.md`.

## Verdict
**SHIPPED.** Backend PDFs are tenant-aware via `pdf_branding.get_white_label()`. MASCI PDFs unchanged. Customer #2 PDFs would render Customer #2 brand strings end-to-end.
