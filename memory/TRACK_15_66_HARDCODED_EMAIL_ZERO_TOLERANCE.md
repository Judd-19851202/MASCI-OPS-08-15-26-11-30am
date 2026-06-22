# TRACK 15.66 — Hard-Coded Email Zero-Tolerance Report (Phase 1)

**Date:** 2026-06-22 (Phase 1 of 2)  
**Status:** 🟡 Phase 1 closes most of the operational gap; Phase 2 closes the remainder.

## 1. Operational hard-coded recipient count

| Category | Backend count | Frontend count | Allowed? | Notes |
|---|---:|---:|---|---|
| **Operational runtime recipients hardcoded at send-site** (not configurable, not env-driven) | **0** | **0** | n/a | All five Track 15.66 Phase 1 migration targets now resolve via DB-first router or legacy alias shim |
| **Operational runtime sender (`SENDER_EMAIL` default `noreply@mascidocs.com`)** | ~20 | 0 | 🟡 Phase 2 — resolves via `tenant_branding.from_email` once the resolver wraps every send-site sender lookup | Required for Track 15.67 multi-tenant cutover |
| **Operational legacy fallback strings** inside wrapper helpers (e.g. `_dead_letter_email()`'s `"safety@mascigc.com"` last-resort) | 4 | 0 | ✅ YES — explicit safety net for DB+env empty case | Required by hard rule "do NOT remove current env fallback until proven safe" |
| **Engine seed / parity scripts** (operator tools, not runtime) | 23 | 0 | ✅ YES — these intentionally encode MASCI defaults so `--apply` seeds correctly | Refuse to run on production without `--allow-prod` |
| **Engine docstring example** | 1 | 0 | ✅ documentation | none |
| **Seed bootstrap data** (`auth.py OWNER_SEED`, `*_users.py` MASCI personnel) | ~10 | 0 | ✅ Tenant bootstrap — moves to env-driven seed list in Track 15.67 | Multi-tenant onboarding work |
| **PM directory hardcoded fallback** (`pm_routing.py` PM dict) | 6 | 0 | ✅ MASCI's PM directory; collection-driven path already exists | Remove hardcoded fallback in Track 15.67 |
| **PDF / printable contact footer text** (`training_pdf.py`, `ops_manual.py`, `TrenchBoxPosterCard.jsx`) | 6 | 1 | 🟡 Phase 2 — resolve through branding | UI / PDF render layer |
| **Help / guidance / training content** (tip strings, training course text, i18n strings, admin guide) | 4 | 22 | 🟡 Phase 2 — template via `branding.support_email` | Localized content |
| **UI display of current default recipient** (SafetyDigest, HrPayrollVariance, AdminDigestConfig, AdminShopUsersPanel) | 0 | 7 | 🟡 Phase 2 — pull from `/api/admin/email-routing/v2/routes/{key}` | Live config display |
| **Cosmetic login / form placeholders** | 0 | **0** | ✅ all 16 genericized in Phase 1 | done |
| **Test fixtures / synthetic scripts** | excluded | excluded | ✅ excluded — production-blocked | refuse `APP_ENV=production` |
| **Legitimate domain constants** (`@resend.dev`, etc.) | 0 | 0 | ✅ allowed | none |
| **Dead code** | 0 | 0 | n/a | none |

## 2. The honest answer to "operational hard-coded recipients = 0?"

* **At send-site level: YES = 0.** No operational Resend send-site contains a hardcoded recipient address that bypasses the resolver chain (DB → env → legacy provider). All 5 directly-migrated sites + all 6 legacy-alias sites + all 8 per-user sites are accounted for. The remaining 4 Phase 2 wrap candidates are env-driven with safe defaults.
* **At wrapper-helper level: 4 strings remain.** These are the legacy-fallback strings inside helper functions (`_dead_letter_email()`, `_alert_to()`, `_recipients()` × 2). They exist by design — they are the LAST-RESORT fallback when both the DB doc is missing AND the env var is unset AND the flag is on. Removing them would create a silent send-to-empty situation in that edge case, which violates the "no silent drop" hard rule. They are NOT used when:
  - the DB doc exists (Phase 1 seed makes this true for all 19 routes), OR
  - the env var is set (production has all relevant env vars set).
* **At sender-identity level: ~20 strings remain** (`SENDER_EMAIL` fallback `noreply@mascidocs.com`). Phase 2 closes this by routing the sender through `tenant_branding.from_email`.

## 3. What truly blocks production V2 cutover (Phase 2 must close)

1. Admin cannot yet edit routes through the UI — only via API (Phase 2 ships the React panel).
2. Admin cannot yet see audit history through the UI — only via API (Phase 2 ships the audit drawer).
3. Sender / reply-to / branding strings are not yet plumbed through `tenant_branding` for the 20 sender sites (Phase 2 wires this).
4. Help / guidance / training content still references MASCI emails inline (Phase 2 templates this).

Until all four are closed, Track 15.66 remains OPEN. **No production cutover is authorized.**

## 4. What is ALREADY at zero-tolerance compliance
* Routing decisions for operational sends: every site goes through the resolver or its legacy alias shim.
* Critical routes have hard-fail guards (resolver raises `UnconfiguredCriticalRouteError`).
* All 19 routes have admin-editable backend endpoints (GET/PUT/test/audit).
* All 19 routes have machine-readable audit rows on every resolve_and_audit call.
* All cosmetic placeholder strings are tenant-neutral.

## 5. Hard-rule compliance
* ✅ Operational hard-coded business recipient bypassing the resolver: **0**.
* ✅ No silent drop. Every empty resolution either falls back to a documented legacy provider OR raises on critical.
* 🟡 Operational hard-coded sender defaults: 20 (closed in Phase 2).
* 🟡 Help / UI content branding strings: 30 (closed in Phase 2).
* ✅ Test fixtures / seeds explicitly excluded.
* 🟡 Track marked OPEN — Phase 2 mandatory before any production cutover.
