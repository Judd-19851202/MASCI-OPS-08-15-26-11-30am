# TRACK 15.67 — Final Zero-Tolerance Audit (Phase 1)

**Date:** 2026-06-22  
**Track status:** 🟡 **OPEN** — Phase 2 must close OWNER_SEED + portal seed files + `pm_routing.py` fallback + remaining sender swap + frontend branding template wiring.

## 1. Operational hard-coded recipients (the headline number)

| Layer | Count | Allowed? | Notes |
|---|---:|:-:|---|
| **Operational hard-coded recipients at any send site** | **0** | n/a | All routing decisions flow through `email_routing_v2.resolve` or the legacy alias shim |
| **Operational hard-coded sender defaults reachable by non-MASCI tenant** | **0** | ✅ | `branding_resolver.resolve_sender` hard-fails for non-MASCI tenants without branding |
| **Operational hard-coded sender defaults reachable by MASCI tenant (env fallback)** | ~20 (unchanged from Track 15.66) | ✅ as MASCI-only env fallback during rollout | Phase 2 swaps to `resolve_sender(db)` so the env fallback becomes redundant; current behaviour is identical for MASCI |
| **Critical routes resolving empty** | 0 | n/a | Verified by parity harness + Route Health endpoint |

## 2. Tenant-specific hard-coded data (Phase 2 closure targets)

| Category | Count | Status | Phase 2 fix |
|---|---:|:-:|---|
| `OWNER_SEED` in `auth.py` | 5 MASCI executives | 🟡 OPEN | env-driven seed list (`OWNER_SEED_EMAILS`) |
| Portal seed users (`safety_users.py`, `shop_users.py`, `hr_users.py`) | ~5 personnel | 🟡 OPEN | Drop hardcoded list, use admin "create first user" path per tenant |
| `pm_routing.py` PM directory fallback | 6 MASCI PM emails + 1 admin fallback | 🟡 OPEN | Remove the dict, require `project_managers` populated per tenant, admin-fallback through `ADMIN_DEAD_LETTER_TO` route |
| Frontend training/i18n/help content (35 strings) | 35 | 🟡 OPEN | Wire branding context + `{{tenant.support_email}}` template at render |
| PDF / poster contact footers (~6 places) | 6 | 🟡 OPEN | Resolve from branding doc at render |

## 3. Engine + tooling hard-coded literals (intentional · DOES NOT block Customer #2)

| Category | Count | Allowed? | Notes |
|---|---:|:-:|---|
| `email_routing_v2.py` engine — docstring examples | 1 | ✅ | docs only |
| `track_15_65_seed_email_routes.py` — MASCI env defaults | 8 | ✅ | seed tool, refuses production without `--allow-prod` |
| `track_15_65_parity_verify.py` — legacy provider implementations | 15 | ✅ | parity tool, mirrors current MASCI behaviour |
| `track_15_67_second_tenant_simulation.py` — synthetic non-MASCI fixtures | 0 MASCI references in the synthetic tenant; only references MASCI in the no-leak assertion strings | ✅ | proof tool |

## 4. Cosmetic placeholders

| Category | Count | Notes |
|---|---:|---|
| Login / form `placeholder="you@mascigc.com"` | **0** | All 16 cleaned in Track 15.66 |
| Frontend display strings (`AdminGuide`, `companyInfo`, training content) | 35 | All classified — Phase 2 wires branding context |

## 5. Customer #2 leakage proof

The second-tenant simulation (27/27 pass) is the live, machine-verifiable proof that the engine + sender + branding + audit layers do not leak MASCI to a non-MASCI tenant. Phase 2 must extend this proof to the bootstrap / PM / frontend surfaces.

## 6. Hard-rule compliance (Phase 1 audit)
* ✅ Operational hard-coded recipients = 0.
* ✅ Operational hard-coded senders reaching Customer #2 = 0.
* ✅ Customer #2 simulation = 0 MASCI inheritance in the proved surfaces.
* ✅ Every literal classified.
* 🟡 Track marked OPEN — Phase 2 mandatory before production cutover.
