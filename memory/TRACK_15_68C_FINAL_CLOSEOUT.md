# TRACK 15.68C · White-Label Chrome Final Mop-Up — Combined Deliverable Set

_2026-06-22 · Consolidates the required 11 deliverables for Track 15.68C. Honest closeout._

---

## 1. Baseline Rescan
Disallowed pre-15.68C: **454**.

## 2. Admin Tab Sweep — ❌ NOT shipped this fork
Files surveyed (5): `MaintainxP0Tab.jsx` (6 hits), `MappingCleanupTab.jsx` (10), `AdminIntegrationCenter.jsx` (6), `AssetProfile.jsx` (5), `AdminDlsShiftQR.jsx` (4) — total ~31 strings.

**Reason for deferral**: these admin tabs reference "MASCI" mostly as a *comparison label* against MaintainX/Motive inventory (e.g. "Existing MASCI Match", "Link to MASCI", "MASCI count"). Migrating them requires per-string review to decide between `branding.company_name` (when used as the tenant's own inventory) vs a neutral term like "Internal" or "Local fleet" (when used as a label against an external system). Mechanical search-replace would produce vague copy — violating Six-Pillar #3 (Beautiful: useful and field-ready).

The right approach is to introduce a single helper `t("Tenant equipment match")` style i18n key and rewire — that's the next dedicated 100-token effort, not a bulk replace.

**Honest classification**: Admin-only chrome, visible to Customer #2 admins. Per the brief: customer-visible → counts as NO-GO.

## 3. Page Subheader Sweep — ❌ NOT shipped this fork
Files surveyed (11): `SignIn.jsx` (2), `Hub.jsx` (3), `Dashboard.jsx` (2), `TrainingHub.jsx` (5), `OperationalGuidanceCenter.jsx` (9), `V2Compare.jsx` (3), `PublicTimeOff.jsx` (2), `HrTimeVerification.jsx` (5), `NewFleetDVIR.jsx` (3), `PublicTrenchSafetyDashboard.jsx` (5), `PublicTrenchSafetyReport.jsx` (2) — total ~41 strings.

**Reason for deferral**: many are inside `t("MASCI Operations Platform")` i18n call sites — the right fix is to migrate the `i18n.js` translation map to template via `BrandingProvider` rather than per-file edits (which would produce 41 inconsistent strings). Single-line `usePageTitle` rewriter (shipped in 15.68A) already cleans the `<title>` tag globally; body subheaders need the i18n-map upgrade.

## 4. Asset Taxonomy Sweep — ✅ Classified (no code change required)
`backend/services/asset_taxonomy.py` contains `CANONICAL_COMPANIES: Tuple[str, ...] = ("MASCI", "MASCI_GC", …)` — this is an **internal Mongo discriminator** used for asset-ownership classification (separating MASCI-owned equipment from rented/sub equipment). It is not surfaced to the Customer #2 UI: a tenant Customer #2 would seed their own canonical company keys via the admin equipment master. Verified by grep: no `CANONICAL_COMPANIES` reference reaches any rendered JSX page. **Classified as non-customer-visible internal taxonomy** — allowed per Phase 4's option (3).

## 5. Data-Seed / Default Sweep — ✅ SHIPPED
- `EquipmentMasterPanel.jsx` — `company: "MASCI"` default → `brandCompanyName("Customer")` (2 sites); `MASCI_equipment.xlsx` export filename → `${brandSlug()}_equipment.xlsx`.
- `AttendeeBulkAddDialog.jsx` — `company: "MASCI"` default → `brandCompanyName("Customer")`.
- `EmailReportDialog.jsx` — `proj = … || "MASCI"` fallback → `brandCompanyName("Project")`.

MASCI tenant: sessionStorage returns "MASCI" → default value unchanged. Customer #2: returns "Customer #2 Construction LLC" → seed values reflect the tenant.

## 6. Customer #2 Walkthrough — partial
Splash + filename + dispatch + top fallbacks + data-seed defaults verified clean for Customer #2. Admin tabs + page body subheaders still leak. Visual screenshot from 15.68B remains the latest proof (`/tmp/track_15_68b_customer2_splash.png`).

## 7. MASCI Parity — ✅ PASS
- `track_15_65_parity_verify.py` → **19/19 match**.
- `track_15_67_second_tenant_simulation.py` → **40/40 pass**.
- All Track 15.68C edits respect MASCI tenant: sessionStorage falls back to "MASCI" when tenant_key is `masci`, so `brandCompanyName("Customer")` returns "MASCI" for MASCI admins and `brandSlug()` returns "MASCI".

## 8. Final Contamination Scan
| Counter | Pre-15.68C | Post-15.68C | Δ |
|---|---:|---:|---:|
| total raw hits | 12,180 | 12,279 | +99 (new deliverables) |
| disallowed | 454 | **449** | **-5** |

| Target | Required | Actual | Pass? |
|---|---:|---:|:--:|
| Filename / export leakage | 0 | 0 ✅ | ✅ |
| Dispatch default leakage | 0 | 0 ✅ | ✅ |
| Fallback `|| "MASCI"` leakage (visible chrome + data seeds) | 0 | 0 ✅ | ✅ |
| Admin tab chrome leakage | 0 | ~31 | ❌ |
| Page body subheader leakage | 0 | ~41 | ❌ |
| Asset taxonomy leakage | 0 (or classified) | classified internal ✅ | ✅ |

## 9. Production Readiness — Conditional GO
- ✅ Deploy with `EMAIL_ROUTING_V2=false`.
- ❌ Full white-label "zero MASCI" NOT met.
- ❌ V2 production flip NOT authorised.
- MASCI parity GREEN.

## 10. Final Closeout — honest verdict

| # | Question | Answer | Proof |
|---:|---|---|---|
| 1 | Baseline disallowed | **454** | |
| 2 | Remaining disallowed | **449** | scan |
| 3 | Customer-visible MASCI remaining | ~72 (admin tabs + body subheaders) | classification |
| 4 | C2 sees MASCI in admin tabs? | **YES** ❌ | scan |
| 5 | C2 sees MASCI in page subheaders? | **partial** ❌ | scan |
| 6 | C2 sees MASCI from data-seed defaults? | **NO** ✅ | brandCompanyName migration |
| 7 | C2 sees MASCI from asset taxonomy? | **NO** ✅ (internal discriminator) | classification |
| 8 | MASCI still looks/behaves same? | **YES** ✅ | parity 19/19 |
| 9 | Route parity 19/19? | **YES** ✅ | |
| 10 | Live emails sent? | **NO** ✅ | |
| 11 | Track 15.68 family finally closed? | **NO** — admin tabs + body subheaders remain | |
| 12 | **GO or NO-GO?** | ✅ GO for deploy with flags OFF; ❌ **NO-GO** for full "zero customer-visible MASCI" until admin tabs + body subheaders migrate via i18n upgrade | |

### Hard rules honoured
✅ No production cutover · ✅ No V2 flip · ✅ No live blasts · ✅ MASCI parity green · ✅ No new branding system · ✅ No V3 · ✅ Historical evidence preserved · ✅ Honest NO-GO returned.

### What unlocks closure (Track 15.68D — i18n.js migration)
The remaining ~72 customer-visible hits are predominantly inside `t("MASCI …")` i18n call sites. Rather than per-file edits, the single right fix is to migrate `lib/i18n.js` translation values to template via the active tenant's `branding.platform_short_name` / `branding.company_name`. That single architectural change (~100 lines in i18n.js) closes ALL the remaining body subheaders in one shot. Admin tabs need a separate ~20 line `t("Internal equipment match")` rename batch.

After Track 15.68D, the disallowed count should drop below **30** (just historical refs + asset taxonomy + tenant-gated MASCI components) — at which point the Track 15.68 family CLOSES with a true full white-label GO.

## 11. Six-Pillar Certification (honest)
Powerful 8 · Simple 9 · Beautiful 7 · Trusted 8 · Proven 8 · Deployable 8 = **48 / 60 (80 %)**. Same score as 15.68B because the closure work this fork was incremental on infrastructure already in place. Track 15.68 family stays OPEN.
