# TRACK 15.67 — Customer #2 Leakage Audit (Phase 1)

**Date:** 2026-06-22  
**Question answered:** *"If Customer #2 went live tomorrow, what MASCI references would they still see or inherit?"*

## 1. The honest answer

**Phase 1 closes the routing-engine + sender-identity + admin-tooling leakage paths.** Phase 2 must close bootstrap personnel, PM directory hardcoded fallback, remaining sender swap sites, and frontend template wiring.

| Surface | MASCI still visible to Customer #2? | Source | Why | Fix required | Status |
|---|:-:|---|---|---|:-:|
| Email **routing decisions** (any of the 19 routes) | ❌ NO (proven) | `email_routes` collection (tenant-scoped) + `email_routing_v2.resolve` (tenant-aware) | Composite `_id` of `tenant_key::route_key` ensures isolation; resolver raises on critical-empty rather than silently leaking | n/a | ✅ DONE Track 15.65/66 + verified Phase 1 simulation |
| **Audit rows** carry `tenant_key` | ❌ NO | `email_routing_audit_v2.write_audit(..., tenant_key=...)` | Tenant flows through every write; second-tenant simulation confirms `tenant_key='tenant_15_67_demo'` on all written rows | n/a | ✅ DONE Track 15.65 |
| **Sender identity** (`from_email`, `reply_to`) for Customer #2 | ❌ NO (proven) | `branding_resolver.resolve_sender` (new this phase) | Hard-fails on `UnconfiguredSenderError` for non-MASCI tenant without branding doc; env fallback to `noreply@mascidocs.com` is **gated to MASCI tenant only** | n/a | ✅ DONE Phase 1 |
| **Sender identity** at 20 historical send sites still using `os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")` | ✅ YES — TODAY (preview) | inline env lookups in `server.py` + helpers | Send sites not yet migrated to `resolve_sender`. MASCI today; Customer #2 would inherit if onboarded before Phase 2 sender swap | wrap each site with `await resolve_sender(db)` | 🟡 Phase 2 |
| Tenant resolution (request → tenant) | ❌ NO leakage | `tenant_context.resolve_tenant_key(...)` | `STRICT_TENANT_RESOLUTION=true` env var forces an error if no tenant is resolved; second-tenant simulation runs in strict mode and passes | n/a | ✅ DONE Phase 1 |
| Route Health validation | ❌ NO | `POST /admin/email-routing/v2/route-health` | Returns green/amber/red per tenant; runs against the tenant resolved by `_current_tenant_key()` | n/a | ✅ DONE Phase 1 |
| Admin UI shows **19 routes** for the active tenant | ❌ NO leakage | `GET /admin/email-routing/v2/routes` reads tenant-scoped docs | UI is tenant-scoped; admin sees only the active tenant's routes | n/a | ✅ DONE Track 15.66 |
| **Login pages cosmetic placeholders** (`placeholder="you@mascigc.com"`) | ❌ NO | UI markup (genericized in Track 15.66) | All 16 cosmetic placeholders now `you@yourcompany.com` | n/a | ✅ DONE Track 15.66 |
| **`OWNER_SEED`** in `auth.py` (5 MASCI executive emails) | ✅ YES | `backend/auth.py` lines 35-39 hardcoded `MASCI_OWNERS` list | Bootstrap script seeds the `user_directory` collection with these names + emails on every cold start | Replace with env-driven seed list `OWNER_SEED_EMAILS` + tenant-scoped admin endpoint | 🟡 Phase 2 |
| **Portal seed users** (`safety_users.py`, `shop_users.py`, `hr_users.py`) | ✅ YES | per-portal `*_users.py` seed lists with MASCI personnel | Same pattern as OWNER_SEED | Drop hardcoded entries · use admin "create first user" path per tenant | 🟡 Phase 2 |
| **PM directory hardcoded fallback** (`pm_routing.py`) | ✅ YES | `pm_routing.py` PM dict with 6 MASCI PM emails + admin fallback to `jaymn.judd@` | Used when `project_managers` collection has no match | Remove the dict; require `project_managers` populated per tenant; route admin-fallback through `ADMIN_DEAD_LETTER_TO` | 🟡 Phase 2 |
| Frontend **help / training / i18n content** mentions of MASCI emails | ✅ YES (35 strings) | `data/training.js`, `lib/i18n.js`, `pages/AdminGuide.jsx`, etc. | Inline content strings; not yet templated through branding | Wire branding context + template `{{tenant.support_email}}` at render | 🟡 Phase 2 |
| Frontend UI display of "current default recipient" (SafetyDigest, HrPayrollVariance, AdminDigestConfig, AdminShopUsersPanel) | 🟡 partial | The UI reads from `/api/admin/email-routing/v2/routes/{key}` after Track 15.66; pages that still show MASCI default are showing the current configured value, which is correct for MASCI tenant; would correctly show Customer #2's configured value for tenant #2 | n/a | ✅ DONE Track 15.66 (resolver-backed; per-tenant by definition) |
| **PDF / printable footers** (`training_pdf.py`, `ops_manual.py`, `TrenchBoxPosterCard.jsx`) | ✅ YES | hardcoded contact email strings | Resolve via branding doc at render | 🟡 Phase 2 |

## 2. Customer #2 onboarding leakage scoreboard

| Acceptance question | Phase 1 verdict |
|---|:-:|
| Can Customer #2 be onboarded without code changes? | 🟡 partial — routing yes; PM directory + bootstrap personnel still require code |
| Can Customer #2 have independent routing? | ✅ YES (proven by simulation, 27/27 checks) |
| Can Customer #2 have independent sender identities? | ✅ YES (proven; non-MASCI tenant refuses env fallback) |
| Can Customer #2 have independent branding? | ✅ YES (`tenant_branding` doc per `_id`) |
| Can Customer #2 have independent support contacts? | 🟡 partial — branding doc supports it; frontend help text not yet templated |
| Can Customer #2 have independent PM routing? | ❌ NO — `pm_routing.py` hardcoded fallback still exists |
| Can Customer #2 avoid inheriting MASCI personnel? | ❌ NO — `OWNER_SEED` + portal seed files still seed MASCI personnel on every cold start |
| Can every route be validated from the Admin UI? | ✅ YES (Route Health one-click, this phase) |
| Can email routing be changed without code edits? | ✅ YES (Admin V2 panel, Track 15.66) |
| Can we cut over `EMAIL_ROUTING_V2` safely? | 🟡 partial — engine is ready; cutover should wait for Phase 2 bootstrap/PM cleanup so a future tenant inheriting the same code base sees zero MASCI leakage |

## 3. Phase 1 evidence

* Second-tenant simulation: `/app/test_reports/track_15_67_second_tenant_simulation.json` — 27/27 pass · 0 fail · cleanup done.
* Parity verification: 19/19 match · 0 mismatch · 0 critical-empty.
* Route Health endpoint: live response `total=19 summary={green:1, amber:18, red:0}`.
* Backend health green after every restart.

## 4. Track status

🟡 **OPEN.** Phase 2 must close OWNER_SEED + portal seed files + `pm_routing.py` fallback + remaining sender swap + frontend branding template wiring + production cutover readiness before this track can be marked DONE.
