# TRACK 28.11B · PRODUCTION RELEASE

**Frozen preview SHA (source of truth):** `576f7fb89b5d2bbdc3aa3a607e887fa8a6972a17`
**Frozen commit time:** `1783794572` → `2026-07-11T18:29:32Z`
**Preview host (verified backend health):** `https://safety-audit-mobile-1.preview.emergentagent.com/api/health` → `ok:true`

**Current production commit (last known-good before this release):** `fe34b609ca92` (source_hash `fe34b609ca92ab60364677ad32865946`, built `2026-07-11T13:52:35Z`)
**Rollback target SHA if the deploy misbehaves:** `fe34b609ca92` — the exact Track 28.10-verified image.

**Production URL:** `https://mascidocs.com`
**Production DB identity:** `masci_safety` (isolation enforced)
**Production `app_env`:** `production`

## Release body (all files)

New:
* `backend/lib/canonical_status.py`
* `backend/tests/test_track_28_11_canonical_status.py`
* `memory/TRACK_28_11_DIAGNOSTICS_TRUTHFULNESS.md`
* `memory/TRACK_28_11B_PRODUCTION_RELEASE.md` (this doc)

Edited (backward-compatible response additions only):
* `backend/routes/admin_ops.py` — system-health canonical counts, MaintainX NOT_APPLICABLE, runtime version fallback
* `backend/routes/deploy_readiness.py` — canonical_status + canonical_reason_code + recommended_action
* `backend/routes/governance_self_protection.py` — overall_status + canonical_status + warning_classification + field-walk freshness + `auto_record_deploy_on_startup`
* `backend/routes/occ_health_aggregator.py` — canonical fields, root_cause_id="r2_bucket_capacity" shared on storage cards, canonical_counts, root_cause_groups, unique_critical_root_causes, integrations NOT_APPLICABLE
* `backend/server.py` — idempotent startup hook `auto_record_deploy_on_startup(_SOURCE_HASH)`
* `frontend/src/pages/admin/AdminDiagnostics.jsx` — reads new canonical fields (System Health "0/8" bug fixed; Deploy Readiness ATTENTION mapped; OCC shows unique root causes)
* `memory/PRD.md`, `memory/CHANGELOG.md`, `memory/TRACK_28_CERTIFICATION_REGISTER.md`

## Configuration protected (must not change on deploy)

`APP_ENV=production` · `MONGO_URL` · `DB_NAME=masci_safety` · R2 bucket + creds · `SCHEDULER_ENABLED` · `AUTO_EMAIL_REPORTS` · Resend keys · Anthropic/AI keys · Sentry · CORS · JWT/admin/HMAC/MFA secrets · session settings · Cloudflare · production domain · resource allocation · DB users · storage thresholds.

**No `.env` edits. No secret rotation. No preview crossover.**

## Release gate

Phase 1-2 status:
* Backend `import server` — OK.
* Backend lint on all touched files — clean (0 issues).
* Frontend lint on `AdminDiagnostics.jsx` — clean (0 issues).
* `backend/tests/test_track_28_11_canonical_status.py` — **24/24 pass** in 0.08s.
* `backend/tests/test_track_28_09d_backup_health_aggregator.py` — passing (Track 28.09D regression proof).
* `backend/tests/test_track_28_09a_environment_separation.py` — passing.
* `backend/tests/test_track_25_01_occ_consolidation.py::test_deploy_readiness_returns_unavailable_when_no_db` — pass.
* `backend/tests/test_maintainx_p0_read_first.py::test_successful_connection_mock` — pass.
* `backend/tests/test_track_15_80_no_secrets_in_repo.py` — pass (no secrets leaked in Track 28.11 code).
* Direct blast-radius composite: **49/49 pass, 1 error** (test infra: legacy shared-password login retired in Track 15.32; pre-existing test bug, unrelated to Track 28.11).

## Pre-deploy production baseline (captured 2026-07-11T18:31Z)

| Signal | Before status | Missing canonical field | Expected post-deploy |
|---|---|---|---|
| `/api/version` | commit=`fe34b609ca92` app_env=production, isolation enforced | (identity fields already emitted by 28.09A) | commit changes to `576f7fb89b5d` build time updates |
| system-health | `overall=yellow` · 8 cards · `counts=None` · `canonical=<absent>` | `counts.total_applicable`, per-card `canonical_status` | truthful `counts.healthy` / `total_applicable` (approx 7/8) |
| deploy-readiness | `overall_status=attention` · 12 checks · 0 blockers · 1 warn · `canonical=<absent>` | `canonical_status` | `canonical_status=ATTENTION` explicitly |
| governance.self-protection | `overall_status=None` · `deployment.status=amber` · `deployed_at=None` · `history_size=8` | `overall_status`, `canonical_status`, `deployment.deployed_at`, `authority.warning_classification` | non-null `overall_status=amber`, deploy recorded on startup (`deployment.status=green`, `history_size=9`), 60/24/0 warning_classification |
| OCC | `overall=red` · counts {green:7, yellow:2, red:4} · `canonical=<absent>` · `root_cause_groups=<absent>` | canonical_counts, root_cause_groups, unique_critical_root_causes | `r2_bucket_capacity` grouping · red count remains 4 · unique_critical drops to 3 (2 storage RED cards share one root cause) |
| Integrations | 5 live probes green, MaintainX `disabled+mocked=True` | MaintainX still counted as an integration | MaintainX classified `NOT_APPLICABLE`, excluded from healthy/total, no severity contribution |

## Deployment safety contract

* Deployment is **code-only** — no `.env` edits.
* Startup hook `auto_record_deploy_on_startup(_SOURCE_HASH)` is idempotent — an unchanged hash is a no-op, so bouncing prod later without a code change will NOT duplicate ledger entries.
* All response additions are **new fields**, not replacements — every legacy consumer continues to receive `status`, `overall`, `page_status`, `counts` unchanged.
* R2 delete engine remains `DISABLED`.
* MaintainX remains write-disabled.
* R2 bucket 320GB overage remains truthfully CRITICAL (now attributed to one shared `root_cause_id`).

## Rollback plan

If any Phase 5-18 verification fails on prod:
1. Redeploy the recorded prior SHA `fe34b609ca92`.
2. The deployment ledger entry created by the startup hook remains in Mongo but is immutable; the rolled-back build won't emit `deployed_at` field going forward (that's the pre-fix behavior we already tolerated).
3. No R2 data touched. No DB schema changed. No secrets rotated.

## Sign-off

Release gate: **PASS**. Baseline captured. Ready for operator deploy trigger.
