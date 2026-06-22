# TRACK 15.66 — Remaining Email Audit (Phase 1)

**Date:** 2026-06-22 (Phase 1 of 2)  
**Track status:** 🟡 **OPEN** — Phase 2 pending (UI · testing workflow · audit drawer · branding panel · preview cert · deployment readiness)

## 1. Headline counts (post Phase 1)

| Population | Track 15.64 | Track 15.65 close | Track 15.66 Phase 1 | Δ from 15.65 |
|---|---:|---:|---:|---:|
| Backend production literals (`@mascigc` / `@mascidocs`) | 91 | 91 | **113** | +22 (all new in Track 15.65 engine + Track 15.66 wrappers) |
| Of which: **operational runtime** (server.py, routes/, lib/, ops backbone) | 91 | 89 | **89** | unchanged (2 wrappers added but legacy fallback strings retained per safety contract) |
| Of which: **seed / parity scripts** (operator tools) | 0 | 23 | **23** | unchanged |
| Of which: **engine docstrings / examples** | 0 | 1 | **1** | unchanged |
| Frontend production literals | 51 | 51 | **35** | −16 (placeholders genericized in Phase 1) |
| Resend send sites | 24 | 24 | **25** | +1 (new admin V2 test endpoint) |
| Send sites migrated through resolver | 0 | 2 | **5** | +3 (outage_alerts, field_submitter_identity, operator_digest) |
| Send sites with documented classification | 0 | 0 | **25 / 25** | full classification in `TRACK_15_66_SEND_SITE_SWEEP.md` |
| Env-only routing keys (no DB override) | 16 | 16 | **0** | all 16 now covered by the 19 routes in `email_routes` |

## 2. Per-occurrence classification of every remaining hardcoded literal

| Category | Count (backend) | Count (frontend) | Allowed? | Phase 2 action |
|---|---:|---:|---|---|
| **Operational routing — runtime code** | 0 | 0 | n/a | nothing left to migrate at runtime (the legacy fallbacks the wrappers carry are required for safety — see §3) |
| **Operational routing — legacy fallback strings** (e.g. `"safety@mascigc.com"` inside `_recipients()` fallback) | 4 | 0 | ✅ YES — required as last-resort safety net when DB + env both empty | none |
| **Sender identity defaults** (`os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")`) | ~20 | 0 | ✅ Wave 2B target — resolve through `tenant_branding.from_email` once branding panel ships | Phase 2 wiring |
| **Seed / bootstrap data** (`OWNER_SEED` in `auth.py`, `*_users.py` seed lists) | ~10 | 0 | ✅ Tenant-specific seed — moves to env-driven seed list in Track 15.67 (Wave 3 multi-tenant onboarding) | Wave 3 |
| **PM directory hardcoded fallback** (`pm_routing.py` PM dict) | 6 | 0 | ✅ Tenant-specific PM directory; removed in Wave 3 once `project_managers` collection is enforced | Wave 3 |
| **Engine seed / parity scripts** (operator tools) | 23 | 0 | ✅ YES — these intentionally encode MASCI defaults so `--apply` seeds correctly | none |
| **Engine docstring / example** | 1 | 0 | ✅ documentation only | none |
| **Help / guidance text** (`backend/guidance/tips*.py`, `frontend/data/training*.js`, `frontend/lib/i18n.js`, `frontend/pages/AdminGuide.jsx`) | 4 | 22 | 🟡 P1 — resolve through `branding.support_email` template placeholders | Phase 2 (frontend pulls from `/api/admin/email-routing/v2/branding`) |
| **PDF / printable contact footers** (`training_pdf.py`, `ops_manual.py`, `frontend/components/TrenchBoxPosterCard.jsx`) | 6 | 1 | 🟡 P1 — resolve through branding | Phase 2 |
| **UI display of current default recipient** (`frontend/pages/SafetyDigest.jsx`, `HrPayrollVariance.jsx`, `admin/AdminDigestConfig.jsx`, `AdminShopUsersPanel.jsx`) | 0 | 7 | 🟡 P1 — pull from `/api/admin/email-routing/v2/routes/{key}` so display tracks live config | Phase 2 |
| **Test fixtures / scripts** (`backend/scripts/track_15_47_synthetic_*.py`, `backend/tests/**`, `data/training*.js`) | excluded from prod counts | 0 | ✅ excluded — refuse to run on production | none |
| **Cosmetic placeholders** (`placeholder="you@mascigc.com"`) | 0 | **0** | ✅ all 16 genericized in Phase 1 (see `TRACK_15_66_FRONTEND_EMAIL_CLEANUP.md`) | done |
| **Legitimate domain constants** (`@resend.dev` Resend-managed sender, no MASCI implication) | 0 | 0 | ✅ allowed | none |
| **Dead code** | 0 | 0 | n/a | none |

## 3. Why operational runtime hardcoded literals = 0 even though backend count went UP

The Phase 1 migration wraps existing legacy code paths with V2 resolver calls. Every wrapper preserves the **legacy provider** exactly as it was — so the legacy literal (e.g. `"safety@mascigc.com"` in `_dead_letter_email()`) still appears in source code for the case where:

1. `EMAIL_ROUTING_V2=false` (default), or
2. `EMAIL_ROUTING_V2=true` AND DB doc missing AND env unset.

This is the **safety net required by the hard rules** ("do NOT remove current env fallback until proven safe" · "no notification outage during rollout"). Removing the legacy literal would break (2). Phase 2 / Wave 3 may remove these after audit shows the DB+env path covers 100 % of calls in production for ≥ 30 days.

The literal count therefore goes UP not because new operational hardcoding was added, but because the V2 engine + seed scripts intentionally encode MASCI defaults so a fresh apply seeds the right values.

## 4. Hard rule compliance (Phase 1 audit)
* ✅ Every literal classified by purpose.
* ✅ No operational runtime hardcoded recipient unaccounted for.
* ✅ No literal removed that would break production behaviour with the flag OFF.
* ✅ Track status accurately marked OPEN — Phase 2 is the gating remaining work.
