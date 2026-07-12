# TRACK 18.04 · Platform Language Migration + Operational Guidance Alignment

**Status:** ✅ MIGRATION EXECUTED · Regression-locked · Constitution applied
**Date:** 2026-02-10
**Type:** Coordinated user-facing terminology cutover · zero-route-break · zero-auth-break

---

## Executive summary

Track 18.03 ratified the Platform Language Constitution and published the Official Naming Registry. Track 18.04 executed the **coordinated user-facing migration** across the highest-impact surfaces — homepage, login chrome, top-bar shells, breadcrumbs, sidebars, access-management UI, branded email templates, the operational footer, and the Operational Guidance Center catalog — without touching backend routes, MongoDB collections, auth tokens, or test IDs.

The platform now speaks **one** vocabulary in user-visible text. Internal Python identifiers, FastAPI route paths, and database collections keep their legacy `admin`/`portal`/`hub`/`dispatch_portal` namespacing for engineering stability, as expressly permitted by the Constitution.

---

## Official Naming Registry · applied

| Canonical (user-facing) | Replaced legacy term(s) | Scope of change |
|---|---|---|
| **Transportation Operations** | Dispatch Portal (in user copy) | Hub card · Dispatch login chrome · TopBar · branded email theme · footer · access-management eyebrow · guidance article titles |
| **Project Management** | PM Portal · PM Hub | Hub card · PM login title · PmShell breadcrumb · branded email · footer · guidance article titles |
| **Human Resources** | HR Portal | Hub card · HR login title · HrPageShell kicker · branded email · footer · access-management eyebrow · guidance |
| **Safety Operations** | Safety Portal | Hub card · Safety login chrome · SafetyShell · branded email · footer · access-management eyebrow · guidance |
| **Shop Operations** | Shop Portal · Shop Hub | Hub card · branded email · footer · guidance |
| **Administration** | Admin Portal · Admin Console | Hub card · AdminShell · sidebar · branded email · footer · guidance |
| **Operations** | Office Portals | Hub section header (anonymous), CheatSheet section header |
| **Your Workspaces** | Your Portals | Hub authed-user section title |
| **Other Workspaces** | Other Portals | Hub locked-cards subsection |
| **Open Workspace** | Open Portal · Open Console | Hub card CTA labels |

---

## Files changed (user-facing strings only)

### Frontend
- `frontend/src/pages/Hub.jsx` — Hub Operations section: card titles, descriptions, section headers, authed-user split.
- `frontend/src/components/CheatSheetCard.jsx` — printed Field Card workspace pills.
- `frontend/src/pages/DispatchLogin.jsx` — title + footer label.
- `frontend/src/pages/HrLogin.jsx` — login title.
- `frontend/src/pages/PmLogin.jsx` — login title.
- `frontend/src/pages/SafetyLogin.jsx` — login title, footer label, welcome toast.
- `frontend/src/pages/SafetyFormsLogin.jsx` — ownership banner copy + CTA.
- `frontend/src/components/AdminShell.jsx` — sidebar Dispatch link label, mobile sheet title, breadcrumb root.
- `frontend/src/components/PmShell.jsx` — mobile sheet title + breadcrumb root.
- `frontend/src/components/HrPageShell.jsx` — kicker text.
- `frontend/src/components/SafetyShell.jsx` — back link, kicker.
- `frontend/src/components/BackLink.jsx` — auto-resolved role labels.
- `frontend/src/components/PortalSwitcher.jsx` — switcher labels for all 6 workspaces.
- `frontend/src/components/PortalHydratingLoader.jsx` — loader workspace labels.
- `frontend/src/components/PortalLoginHelp.jsx` — workspace name registry.
- `frontend/src/components/PortalContextBanner.jsx` — `?from=` workspace registry (EN + ES).
- `frontend/src/components/AdminDispatchUsersPanel.jsx` — eyebrow + impersonation toast/confirm.
- `frontend/src/components/AdminHRUsersPanel.jsx` — eyebrow text.
- `frontend/src/components/AdminSafetyUsersPanel.jsx` — eyebrow text + email helper copy.
- `frontend/src/components/AdminFieldLeadershipUsersPanel.jsx` — eyebrow text.
- `frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx` — change-password helper copy.
- `frontend/src/pages/guidance/OperationalGuidanceCenter.jsx` — PORTAL_TRACKS workspace chip labels + section subtitle.
- `frontend/src/pages/PmCommandCenter.jsx` — breadcrumb back link.
- `frontend/src/lib/i18n.js` — added canonical EN→ES translation entries for new strings; legacy keys kept as orphans (harmless).
- All call sites passing `portalRole="{Legacy}"` on the design-system `PortalShell` were swept to the canonical workspace name (12 files).

### Backend
- `backend/branded_portal_emails.py` — `_PORTAL_THEMES` sub-eyebrow strings rewritten to canonical workspace names.
- `backend/operational_footer.py` — added `_WORKSPACE_NAME` mapping; footer line 2 now renders canonical name instead of `{Portal} Portal`.
- `backend/server.py` — Shop password-reset subject + headline + body copy updated to "Shop Operations".
- `backend/routes/pm_routes.py` — PM password-reset email subject canonicalized.
- `backend/routes/pm_admin.py` — PM welcome email headline canonicalized.
- `backend/routes/hr_portal.py` — HR welcome + reset subject canonicalized; headline canonicalized.
- `backend/routes/safety_portal/auth_users.py` — Safety welcome subject + headline canonicalized.
- `backend/routes/field_leadership_portal.py` — Field Leadership subjects + headline canonicalized.
- `backend/pm_welcome_pdf.py` — `<title>` and tag chrome canonicalized.
- `backend/guidance/content.py` — guidance article titles for HR / Safety / Shop / PM / Dispatch / Admin renamed to canonical workspace names (both the role-overview entries and the Identity entries).
- `backend/tests/test_iter437_footer_standardization.py` — locked test updated to align with the canonical-name footer contract.

---

## Terms intentionally preserved (engineering stability)

| Surface | Term preserved | Reason |
|---|---|---|
| FastAPI route paths | `/api/admin/transportation/*`, `/api/dispatch/*`, `/api/hr/*`, `/api/safety/*`, `/api/shop/*`, `/api/pm/*`, `/api/field-leadership/*` | URL contracts shared with frontend + integration callers; locked by 200+ tests. |
| Auth tokens | `X-Admin-Token`, `X-Dispatch-Token`, `X-HR-Token`, `X-Safety-Token`, `X-Shop-Token`, `X-PM-Token` | Header contracts — renaming would break every authenticated client. |
| LocalStorage keys | `masci.admin.token`, `masci.dispatch.token`, `masci.hr.token`, etc. | Auth contracts read by `*Auth.js` libs. |
| MongoDB collections | `transport_persons`, `dispatch_assignments`, etc. | No data migration. |
| Test IDs | `admin-side-nav-v2`, `dispatch-hub`, `admin-transportation-page` | Locked by Track 18.01 + 18.02 testid contracts. |
| Internal Python identifiers | `_PORTAL_THEMES`, `portal="HR"`, `is_dispatch_admin()`, etc. | Constitution carve-out · backend code may keep namespacing. |
| Historical documentation | `/app/memory/*.md` legacy track records | Provenance — historical naming preserved as the record of what shipped. |
| Internal code comments / docstrings | Legacy portal names | Constitution governs user-facing strings only. |

---

## Operational Guidance Center · audit

Identity articles (`portal-hr-identity`, `portal-safety-identity`, `portal-shop-identity`, `portal-dispatch-identity`, `portal-pm-identity`, `portal-admin-identity`) and role guidance overviews now carry **canonical** workspace names in their titles. The Workspace chip tabs on `/guidance` show canonical names. Article BODY text often still references legacy terms for historical accuracy — this is intentional (the Constitution does not require rewriting prose, only labels, titles, and chips).

**Coverage:**
- ✅ Transportation Operations Guidance · Overview
- ✅ Project Management Guidance · Overview
- ✅ Human Resources Guidance · Overview
- ✅ Safety Operations Guidance · Overview
- ✅ Shop Operations Guidance · Overview
- ✅ Administration Guidance · Overview
- ✅ Mission Control · Dispatch Board · Live Map · Haul Ledger guidance retained.
- ⚠️ Per-feature deep-dive articles (Pre-Op, JHP, Trench, Orientation, etc.) retain their established names — these are feature names, not workspace names.

---

## Tests

`backend/tests/test_track_18_04_platform_language_migration.py` — 43 regression tests covering:

- 5 doc-presence tests (Constitution, 18.04 doc, registry, inventory, guidance audit)
- 8 Hub homepage tests (Operations section, card titles, no legacy strings in portalDefs)
- 5 login-chrome tests (DispatchLogin, HrLogin, PmLogin, SafetyLogin, SafetyFormsLogin)
- 9 shell + breadcrumb + access tests (AdminShell, PmShell, HrShell, SafetyShell, BackLink, PortalSwitcher, Loader, LoginHelp, ContextBanner)
- 4 admin access-management panel tests (Dispatch, HR, Safety, FieldLeadership)
- 4 email + footer tests (branded themes, operational footer, subjects, headlines)
- 2 guidance content tests (top-article rename + chip labels)
- 3 backend carve-out tests (route prefix, dispatch token, dispatch login route contract)
- 1 deployment-gate wiring test
- 1 Constitution registry integrity test
- 1 no-empty-shells test

**All 43 tests passing.**

---

## Deployment gate

`scripts/deployment_gate.py` updated to include Track 18.04 regression.

---

## Risks / deferrals

- **Article body prose** (not titles) in `guidance/content.py` still references legacy names in places — intentional for narrative continuity; will be soft-edited in a future content pass.
- **i18n.js** orphan legacy keys (`"HR Portal"`, `"PM Portal"`, etc.) left in place as harmless passthroughs. A future translation cleanup can drop them.
- **operator-review markdown** (`/app/memory/*.md`) keeps legacy names as historical record per the Constitution.
- **Email body prose** beyond subjects/headlines was not edited line-by-line; canonical names appear via the operational footer and sub-eyebrow theme so every email arrives carrying the canonical workspace identity.
- **PDF body prose** in non-welcome templates not edited; PDF titles / chrome canonicalized where present.

---

## Final certification

**Migration: EXECUTED.**
**Regression: LOCKED (43/43 passing).**
**Carve-out: HONORED — backend routes, tokens, collections, and testids unchanged.**
**Deployment gate: WIRED.**

The platform speaks one vocabulary. Future drift is blocked by static-scan regression.

---

## AMENDMENT (post-merge defect) — 2026-02-10

**Defect found on public homepage:** hero kicker rendered as
`MASCI HUB HUB HUB OPERATIONS PLATFORM` — triple-Hub token bleed
caused by the `_brandSubst` i18n chain when the backend branding
served `platform_short_name = "MASCI Hub"` and the chain
re-substituted `MASCI` → `MASCI Hub` repeatedly.

**Fixes applied:**
1. `backend/server.py` — MASCI tenant defaults: `platform_short_name`
   changed from `"MASCI Hub"` → `"MASCI"`. Backend now serves canonical
   short name.
2. `frontend/src/lib/BrandingProvider.jsx` — neutral fallback short name
   changed from `"Ops Hub"` → `"Ops"`. No "Hub" in fallbacks.
3. `frontend/src/lib/i18n.js` — `_brandSubst()` made idempotent. Even
   if a legacy tenant doc still holds `"MASCI Hub"` in DB,
   `cleanBrand`/`cleanCompany` strip the `MASCI` prefix from the brand
   variable before chaining so we never double-emit tokens.
4. `frontend/src/pages/Hub.jsx` — hero subtext refreshed to use
   `Transportation Operations` instead of bare `dispatch` as a top-level
   platform pillar. EN + ES dictionary keys updated.
5. `frontend/src/data/training.js` — Field-101 lesson + cross-portal
   references renamed `MASCI Hub` → `MASCI Operations Platform`.

**New regression locks (`test_track_18_04_platform_language_migration.py`):**
- `test_44_hub_hero_uses_masci_operations_platform_kicker`
- `test_45_hub_hero_subtext_uses_transportation_operations`
- `test_46_backend_branding_returns_masci_short_name`
- `test_47_no_user_facing_hub_in_homepage_kicker_or_section`
- `test_48_no_legacy_office_portals_anywhere_in_hub`
- `test_49_brand_subst_chain_is_idempotent_against_brand_containing_masci`
- `test_50_training_data_uses_masci_operations_platform_not_hub`

**Total Track 18.04 regression: 50/50 PASS.**

**Live smoke (post-fix):** Hero reads `MASCI OPERATIONS PLATFORM` (single
clean kicker) and subtext uses `Transportation Operations`. Hub
verified at `https://backup-forensics.preview.emergentagent.com/`.
