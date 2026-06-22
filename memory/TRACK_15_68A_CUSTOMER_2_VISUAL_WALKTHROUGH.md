# TRACK 15.68A · Customer #2 Visual Walkthrough

_Status: ✅ Splash & PDF cleared · ⚠️ Long-tail page chrome partial · ❌ Filename templates leak_

## Method
- Synthetic tenant `track_15_68_tenant_test_delete` (`Customer #2 Construction LLC`).
- Preview via `?tenantPreview=track_15_68_tenant_test_delete` URL param → backend `X-Tenant-Preview` header.

## Captured screenshots
- `/tmp/track_15_68a_customer2_splash.png` — Customer #2 splash: **teal "C" monogram on `#0F766E`, NO MASCI MARK**, NO MASCI words. ✅
- `/tmp/track_15_68a_masci_splash.png` — MASCI splash: original red M + caution stripe, parity preserved. ✅
- `/tmp/track_15_68a_customer2_postsplash.png` — post-splash; sessionStorage clears after first view.

## Surface-by-surface verdict

| Surface | C2 sees MASCI? | Notes |
|---|:--:|---|
| Splash / login | ❌ **NO** ✅ | Customer #2 monogram + tenant name + teal stripe |
| `/api/branding/current` | ❌ NO ✅ | Returns Customer #2 data 100% |
| Portal shell footer | ❌ NO ✅ | Phase 3 migration |
| Email Routing admin panel | ❌ NO ✅ | Phase 3 |
| Daily Report Section 04 | ❌ NO ✅ | Section title "Crews" now |
| Daily Report photo download filenames | ✅ **YES** ❌ | `MASCI_DR_*.jpg` filename templates not yet migrated |
| Inspection findings filenames | ✅ **YES** ❌ | `MASCI_Inspection_*.jpg` |
| Excavation form (Trench Safety) | ❌ NO ✅ | Migrated |
| New Meeting / New Incident sub-headers | ❌ NO ✅ | Migrated |
| ViewInspection KV labels | ❌ NO ✅ | Migrated |
| Legal Terms / Privacy | ❌ NO ✅ | Tenant-gated render — placeholder for Customer #2 |
| AdminGuide print header | ❌ NO ✅ | Uses platform_display_name + marketing_url |
| AdminGuide body content | ⚠️ partial | Several body strings still mention MASCI |
| Backend PDFs (header alt + footer) | ❌ NO ✅ | `pdf_branding.get_white_label()` tenant-aware |
| Dispatch carrier dropdown default | ✅ **YES** ❌ | Default `{label:"MASCI"}` not yet migrated |
| Admin tabs (MaintainX/Mapping) | ✅ **YES** ❌ | Not migrated |
| TrainingHub / OperationalGuidance / SignIn / Dashboard / Hub sub-headers | ✅ **YES** ❌ | Not migrated |

## Verdict
**Massive improvement; not yet zero.** Customer #2 no longer sees MASCI in the splash, PDF chrome, legal pages, public forms, daily report sections, meetings, incidents, or inspections — but still sees MASCI in download filenames (`MASCI_DR_*`), dispatch dropdown default, admin integration tabs, and several training/guidance sub-headers.

Per the brief's hard rule "if Customer #2 can still see MASCI anywhere customer-facing: RETURN NO-GO" — **NO-GO**.

The leakage is now finite and surgical: the filename sweep alone (Phase 7) plus migrating dispatch+training+guidance sub-headers would close the gap. Estimated next-session work: ~80-100 string-level edits.
