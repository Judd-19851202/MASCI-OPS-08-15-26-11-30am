# TRACK 15.68A · Filename / Export Sweep

_Status: ❌ NOT MIGRATED this fork_

## Inventory
The following filename templates still produce `MASCI_*` filenames for any tenant:

| File | Pattern | Surfaces |
|---|---|---|
| `pages/ViewDailyReport.jsx:540` | `MASCI_DR_sub_${s.company}_${i+1}.jpg` | Daily Report subcontractor photo download |
| `pages/ViewDailyReport.jsx:686` | `MASCI_DR_${id.slice(0,8)}_photos` | Daily Report photo bundle prefix |
| `pages/ViewDailyReport.jsx:696` | `MASCI_DR_${id.slice(0,8)}_photo${i+1}.jpg` | Daily Report individual photo download |
| `pages/ViewInspection.jsx:413` | `MASCI_Inspection_${id.slice(0,8)}_findings` | Inspection findings bundle prefix |
| `pages/ViewInspection.jsx:423` | `MASCI_Inspection_${id.slice(0,8)}_finding${i+1}.jpg` | Inspection finding photo |
| `components/AdminSafetyFormsPanel.jsx` | `MASCI_${label}_${id.slice(0,8)}.pdf` | Admin export filename |
| `components/AdminJobMasterPanel.jsx` | `MASCI_jobs.xlsx` | Admin job export |

## Required pattern (next phase)
1. Add `slug` field to BrandingProvider that lowercases `company_name` and strips non-alphanumerics (e.g. `"Customer #2 Construction LLC"` → `customer2`).
2. Replace `MASCI_` literal prefixes with `${branding.slug.toUpperCase()}_` template strings.
3. MASCI tenant still produces `MASCI_*.pdf` filenames (slug is `masci` → upper → `MASCI`).
4. Customer #2 produces `CUSTOMER2_*.pdf` filenames.

## Verdict
**NOT SHIPPED.** Customer #2 downloads would still be named `MASCI_DR_*.jpg` / `MASCI_Inspection_*.jpg`. This is a clear customer-visible leak.
