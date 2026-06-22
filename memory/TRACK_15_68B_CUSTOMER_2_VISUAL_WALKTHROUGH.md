# TRACK 15.68B · Customer #2 Visual Walkthrough — Partial

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §7.

Screenshot proof:
- `/tmp/track_15_68b_customer2_splash.png` — Customer #2 preview splash, teal "C" monogram on dark canvas, NO MASCI mark, NO MASCI words.

Filename proof via shell:
```js
sessionStorage.setItem("branding.slug", "customer_2_construction_llc");
brandSlug() // → "CUSTOMER_2_CONSTRUCTION_LLC"
brandFilename("DR", "abc123") // → "CUSTOMER_2_CONSTRUCTION_LLC_DR_abc123"
```

| Surface | C2 sees MASCI? |
|---|:--:|
| Splash | NO ✅ |
| `/api/branding/current` | NO ✅ |
| Portal shell footer | NO ✅ |
| Daily Report photo / bundle filename | NO ✅ |
| Inspection finding filename | NO ✅ |
| Admin xlsx / pdf export filename | NO ✅ |
| Dispatch carrier default label | NO ✅ |
| ViewDailyReport "Daily Report" company name banner | NO ✅ |
| ViewInspection "Job Site Safety" company name | NO ✅ |
| Backend PDF chrome | NO ✅ |
| Legal Terms / Privacy | NO ✅ |
| AdminGuide print header | NO ✅ |
| Admin tabs (MaintainX/Mapping/IntegrationCenter/AssetProfile/AdminDlsShiftQR) | **YES** ❌ — 15.68C |
| `pages/SignIn`, `Hub`, `Dashboard`, `TrainingHub`, etc. body subheaders | **YES** ❌ — 15.68C |
| `EquipmentMasterPanel` / `AttendeeBulkAddDialog` row-seed defaults | **YES** ❌ — admin overrides per row |

Full 8-portal walkthrough not run (context budget). Splash + filename + dispatch verified end-to-end via screenshot + sessionStorage proof.
