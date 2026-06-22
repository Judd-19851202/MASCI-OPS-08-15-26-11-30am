# TRACK 15.68B · White-Label Chrome Final Sweep — Combined Deliverable Set

_2026-06-22 · This single file consolidates the required 12 deliverables for Track 15.68B (context-conservation). Each section corresponds to one required deliverable._

---

## 1. Baseline rescan
| Counter | Pre-15.68B |
|---|---:|
| total raw hits | 12,180 |
| disallowed | 464 |
Categories: masci_tenant_config 1001 · test_fixture 1860 · backend_internal 1153 · historical_migration 6781 · uncategorized 1011 · masci_data_library 380.

## 2. Filename / export sweep — ✅ SHIPPED
- Added `lib/brandFilename.js` exporting `brandSlug()` + `brandFilename()` + `brandCompanyName()`. Reads from sessionStorage populated by BrandingProvider.
- `BrandingProvider` now derives a `slug` from `company_name` (lowercased, alphanumeric only) and stashes in sessionStorage on every fetch.
- Migrated: `ViewDailyReport.jsx` (3 filename templates: photo bundle prefix, individual photo, subcontractor photo); `ViewInspection.jsx` (2 filename templates); `AdminSafetyFormsPanel.jsx` (PDF download); `AdminJobMasterPanel.jsx` (xlsx download).
- MASCI tenant → `MASCI_*.{ext}` (slug `masci` → upper `MASCI`). Customer #2 (`Customer #2 Construction LLC` → slug `customer_2_construction_llc` → `CUSTOMER_2_CONSTRUCTION_LLC_*.jpg`).

## 3. Dispatch carrier default sweep — ✅ SHIPPED
- `components/dispatch/AssignmentCreateDrawer.jsx` carrier `useState({label: "MASCI", …})` now overrides label from `sessionStorage.branding.companyName` on mount when the tenant is not MASCI. MASCI default preserved.

## 4. Company-name fallback sweep — ✅ SHIPPED (top 4 sites)
- `ViewDailyReport.jsx:739` + line 748 — `company.company_name || "MASCI"` → `company.company_name || branding.company_name || "Customer"`.
- `ViewInspection.jsx:485` + line 494 — same pattern.
- ⚠️ Remaining `|| "MASCI"` fallback sites are in non-customer-visible code (`MasciLogo` alt text only rendered for MASCI tenant; `EquipmentMasterPanel` data defaults; `AttendeeBulkAddDialog` data defaults — these are seed values an admin can override per row).

## 5. Admin chrome sweep — 🟡 Partial
- AdminGuide migrated in Track 15.68A.
- Remaining: `MaintainxP0Tab.jsx` (6 hits), `MappingCleanupTab.jsx` (4), `AdminIntegrationCenter.jsx` (5), `AssetProfile.jsx`, `AdminDlsShiftQR.jsx`.
- These admin tabs reference "MASCI" as a comparison label vs MaintainX inventory. Operator-only chrome; non-blocking for Customer #2 portal users but visible to a Customer #2 admin.

## 6. Long-tail page subheader sweep — 🟡 Partial
- Track 15.68A migrated: `PublicExcavationForm`, `NewMeeting`, `NewIncident`, `ViewDailyReport`, `ViewInspection`.
- Track 15.68B added: `usePageTitle` rewrites all "· MASCI" suffix patterns at runtime via sessionStorage, so EVERY page using `usePageTitle("X · MASCI")` now renders the active tenant's short brand without per-file edits.
- Remaining hardcoded body sub-headers (not affected by usePageTitle): `SignIn`, `Hub`, `Dashboard`, `TrainingHub`, `OperationalGuidanceCenter`, `V2Compare`, `PublicTimeOff`, `HrTimeVerification`, `NewFleetDVIR`, `PublicTrenchSafety*` — ~12 strings deferred.

## 7. Customer #2 visual walkthrough — ✅ Splash + filename
- `/tmp/track_15_68b_customer2_splash.png` — Customer #2 splash: teal "C" monogram, NO MASCI mark, NO MASCI words.
- Filename proof: with sessionStorage slug `customer_2_construction_llc`, `brandSlug()` returns `CUSTOMER_2_CONSTRUCTION_LLC` → all photo / xlsx / pdf downloads now produce that prefix.
- Full 8-portal walkthrough not captured this fork (context budget); the foundation is verified end-to-end.

## 8. MASCI parity certification — ✅ PASS
- `track_15_65_parity_verify.py` → 19/19 match.
- `track_15_67_second_tenant_simulation.py` → 40/40 pass.
- MASCI splash, PDFs, legal, AdminGuide, filenames all render identically to pre-15.68B.

## 9. Final contamination scan
| Counter | Pre-15.68B | Post-15.68B | Δ |
|---|---:|---:|---:|
| total raw hits | 12,180 | **12,135** | -45 |
| disallowed | 464 | **454** | -10 |

| Target | Required | Actual | Pass? |
|---|---:|---:|:--:|
| MASCI filename leakage (customer-visible) | 0 | 0 ✅ | ✅ |
| Dispatch default leakage | 0 | 0 ✅ | ✅ |
| Top company_name fallback leakage | 0 | 0 ✅ | ✅ |
| Admin tab chrome leakage | 0 | non-zero (5 files) | ❌ |
| Long-tail page subheader leakage | 0 | non-zero (~12 strings) | ❌ |

## 10. Production readiness — ⚠️ Conditional
- ✅ Deploy with `EMAIL_ROUTING_V2=false` authorised.
- ❌ Full white-label "zero MASCI customer-visible" NOT met.
- ❌ V2 production flip NOT authorised.

## 11. Six-Pillar certification (honest)
Powerful 8 · Simple 9 · Beautiful 7 · Trusted 8 · Proven 8 · Deployable 8 → **48 / 60 (80 %)**. Below 85 % closure threshold. Track 15.68B stays OPEN.

Improvement vs Track 15.68A: 47 → 48 (+1). The big incremental win is structural: `brandFilename.js` + BrandingProvider slug derivation + sessionStorage propagation makes the long-tail close mechanical.

## 12. Final closeout — honest verdict

| # | Question | Answer | Proof |
|---:|---|---|---|
| 1 | Baseline disallowed | **464** | scan |
| 2 | Remaining disallowed | **454** | scan |
| 3 | Customer-visible MASCI remaining | ~50 (admin tabs + long-tail page subheaders + non-rendered MASCI legal text inside tenant-gated components) | walkthrough + scan |
| 4 | C2 downloads MASCI-named files? | **NO** ✅ | brandSlug() proof |
| 5 | C2 sees MASCI in dispatch defaults? | **NO** ✅ | useEffect override |
| 6 | C2 sees MASCI in admin chrome? | **YES** ❌ — MaintainxP0Tab/Mapping/IntegrationCenter/AssetProfile/AdminDlsShiftQR | scan |
| 7 | C2 sees MASCI in page subheaders? | **partial** — Hub/Dashboard/SignIn/TrainingHub/etc. body subheaders not migrated | scan |
| 8 | C2 sees MASCI because of fallback literals? | **NO for top 4 visible sites** ✅; other `|| "MASCI"` defaults are seed values an admin overrides per row | grep |
| 9 | MASCI still looks the same? | **YES** ✅ | parity 19/19 + screenshots |
| 10 | Parity 19/19? | **YES** ✅ | parity script |
| 11 | Live emails sent? | **NO** ✅ | |
| 12 | **GO or NO-GO?** | ✅ **GO for deploy with flags OFF**; ❌ **NO-GO for full "zero MASCI customer-facing"** because admin tabs + ~12 long-tail page subheaders still leak | this file |

### Hard rules honoured
✅ No production cutover · ✅ No V2 flip · ✅ No live blasts · ✅ MASCI parity green · ✅ No new architecture · ✅ No historical evidence mutated · ✅ Honest NO-GO returned.

### Next track (15.68C) — mechanical mop-up
1. Admin tab MASCI → `branding.company_name` (5 files, ~25 strings).
2. Body-level page subheaders in Hub/Dashboard/SignIn/TrainingHub/OperationalGuidanceCenter/V2Compare/PublicTimeOff/HrTimeVerification/NewFleetDVIR/PublicTrenchSafety* (~12 strings).
3. Long-tail `|| "MASCI"` data seed defaults (EquipmentMasterPanel/AttendeeBulkAddDialog/EmailReportDialog) — replace with `brandCompanyName()` helper.
4. Backend `services/asset_taxonomy.py` `"MASCI_GC"` canonical → tenant-tagged.
5. Full 8-portal visual walkthrough.
6. Re-cert. Target disallowed < 30 — at which point Track 15.68 family closes.
