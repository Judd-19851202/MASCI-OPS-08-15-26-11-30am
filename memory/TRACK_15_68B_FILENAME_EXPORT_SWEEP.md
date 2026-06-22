# TRACK 15.68B · Filename / Export Sweep — ✅ SHIPPED

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §2.

**Infrastructure**
- `frontend/src/lib/brandFilename.js` — new module exporting `brandSlug()`, `brandFilename()`, `brandCompanyName()`.
- `BrandingProvider` now derives `data.slug` from `company_name` (lowercase + alphanumeric_ only) and writes it to `sessionStorage.branding.slug`.

**Migrated**
- `pages/ViewDailyReport.jsx` — `MASCI_DR_sub_*.jpg`, `MASCI_DR_*_photos`, `MASCI_DR_*_photo*.jpg` → `${brandSlug()}_…`.
- `pages/ViewInspection.jsx` — `MASCI_Inspection_*_findings`, `MASCI_Inspection_*_finding*.jpg` → tenant slug.
- `components/AdminSafetyFormsPanel.jsx` — `MASCI_${label}_${id}.pdf` → tenant slug.
- `components/AdminJobMasterPanel.jsx` — `MASCI_jobs.xlsx` → tenant slug.

**Proof**
- MASCI tenant → `MASCI_DR_*.jpg` (slug `masci` → upper `MASCI`).
- Customer #2 (`Customer #2 Construction LLC`) → slug `customer_2_construction_llc` → `CUSTOMER_2_CONSTRUCTION_LLC_DR_*.jpg`.
- **ZERO MASCI** in Customer #2 downloads.

**Hard rules honoured**: no broken downloads, no broken exports.
