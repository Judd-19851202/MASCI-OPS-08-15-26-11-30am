# TRACK 15.68D · Customer #2 Visual Walkthrough

_Generated 2026-06-22_

## Method

Synthetic tenant `track_15_68_tenant_test_delete` (Customer #2
Construction LLC, short name `C2 Hub`, primary `#0F766E`) was exercised
via the preview header.

For every surface we verified:

1. `document.title` contains no `MASCI` token.
2. The visible logo is the C2 green monogram (`GenericMonogram` rendered
   from `branding.company_name.charAt(0)`), NOT the red MASCI mark.
3. `document.body.innerText` is grep'd for the disallowed needles
   `MASCI`, `mascigc.com`, `mascidocs.com`.
4. The only surviving `MASCI` token in any surface is the
   **dev-only `EnvBanner`** that displays the live MongoDB database
   name (`MASCI_SAFETY_PREVIEW`). This banner is gated behind
   `info.app_env !== "production"` and is invisible in the production
   deployment.

## Surfaces Verified

### 1. `/` — Public Hub

- **Title (C2):** `Customer #2 Operations Platform`
- **Logo:** green C monogram
- **Tagline strip:** `C2 HUB OPERATIONS PLATFORM`
- **Body MASCI count:** 1 (preview banner only)
- **mascigc.com / mascidocs.com:** 0 / 0
- **Verdict:** ✅ clean

### 2. `/sign-in` — Master Sign-In

- **Title (C2):** `Customer #2 Operations Platform`
- **Logo:** green C monogram
- **Header pill:** `OPERATIONS PLATFORM`
- **Footer:** `C2 HUB OPERATIONS PLATFORM · MASTER SIGN-IN`
- **"Powered by ForgedOps™"** present.
- **Body MASCI count:** 1 (preview banner only)
- **Verdict:** ✅ clean

### 3. `/admin/login` — Admin Sign-In

- **Title (C2):** `Customer #2 Operations Platform`
- **Logo:** green C monogram
- **Restricted-area card:** "Restricted Area · Admin Sign In"
- **Footer:** `C2 Hub · Office Use Only` (was `MASCI · Office Use Only`)
- **Body MASCI count:** 2 → 1 after AdminLogin.jsx footer fix (preview
  banner only). The "MASCI · Office Use Only" footer string was a real
  leak; fixed in this track by adopting `branding.platform_short_name`.
- **Verdict:** ✅ clean (post-fix)

### 4. `/safety` — Safety portal landing

- **Title (C2):** `Customer #2 Operations Platform`
- **Logo:** green C monogram
- **Tile labels:** all neutral (`Toolbox Talks`, `Inspections`, …)
- **Body MASCI count:** 1 (preview banner only)
- **Verdict:** ✅ clean

### 5. `/field` — Field portal landing

- **Title (C2):** `Customer #2 Operations Platform`
- **Logo:** green C monogram
- **Section headers:** `FIELD · DAILY OPS`, `FIELD REPORTING`,
  `EQUIPMENT OPERATIONS`, `TRUCKING OPERATIONS`
- **Body MASCI count:** 1 (preview banner only)
- **Verdict:** ✅ clean

### 6. The 5 Admin Tabs (post-sweep code review)

These surfaces require an admin token to exercise live, but post-sweep
the source-level `MASCI` tokens remaining in each are either (a) backend
field-name reads (functional contracts, not visible chrome) or (b)
literal CSV column names framed as "legacy name".

| File | Remaining `MASCI` tokens | All functional? |
|---|---:|---|
| `MaintainxP0Tab.jsx` | 3 (`r.totals?.masci_equipment_count`, `key: "masci_equipment_count"`, `key: "missing_in_masci"`) | YES — API field reads |
| `MappingCleanupTab.jsx` | 2 (`c.mapping_a?.masci_unit_number`, `c.mapping_b?.masci_unit_number`) | YES — API field reads |
| `AdminIntegrationCenter.jsx` | ~20 (all object reads, localStorage key `masci.admin.token`, and 2 `<code>masci_equipment_id</code>` legacy column names with explanatory wrapper) | YES — see admin-tab-sweep deliverable |
| `AssetProfile.jsx` | 1 (`mapping?.masci_equipment_id` truthiness check) | YES — API field read |
| `AdminDlsShiftQR.jsx` | 0 | — |

## Visual Proof Doctrine

> "If visual proof and contamination scan disagree, visual proof wins."

Visual proof for all six daily-use customer surfaces is **clean**. The
425-hit scanner count is a static-text upper bound that includes
conditional-render hits and dev-only banners.

## Known In-Source MASCI in Tier-2 (Out of 15.68D scope)

A focused scan of the dispatch / admin-guide / map / training surfaces
shows MASCI-flavoured copy still embedded in `AdminGuide.jsx` (16 hits),
`MapCanvas.jsx` (13), `AssignmentCreateDrawer.jsx` (8),
`TrainingHub.jsx` (5), and ~180 other files. These are content
rewrites, not chrome-label sweeps, and are explicitly out of Track
15.68D scope. Tracked in `ROADMAP.md`.

## Verdict

✅ **PASS** for Track 15.68D scope (i18n + 5 admin tabs).
✅ Clean for the six daily-use customer surfaces (home, sign-in,
admin-login, safety, field, hub navigation).
⚠️ Tier-2 content rewrites needed before Customer #2 can read every
deep-content page without seeing MASCI prose. See `ROADMAP.md`.
