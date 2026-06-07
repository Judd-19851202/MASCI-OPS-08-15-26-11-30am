# DEPLOYMENT ROLLBACK REFERENCE

**Deployed at**: 2026-02-12
**Environment**: PREVIEW
**Preview URL**: https://safety-audit-mobile-1.preview.emergentagent.com

---

## ROLLBACK POINT — GIT COMMIT

**Current HEAD (this deployment)**:
```
d00a56fb9b15f51b57990a67fd91d3b03de54047
```
Date: 2026-06-07
Message: `auto-commit for 102db7b4-3fec-4671-bf8f-b90d84bc42c6`

---

## PREVIOUS COMMITS (rollback candidates · chronological)

| SHA | Date | Message |
|---|---|---|
| `d00a56fb9b15f51b57990a67fd91d3b03de54047` | 2026-06-07 | **CURRENT** · post FV-7 + FT hardening + i18n fix |
| `3fb5c3a5b9c18a7d11ea5afa4957f9bf10c6bdef` | 2026-06-07 | Pre i18n fix · post FV-7.1A backfill |
| `14e5ab42d2d68cb5705177b64114e26595f2dc56` | 2026-06-07 | Pre FV-7.1A · post FV-7 closure |
| `981c3ade372ee1d-021f-408b-a99e-702aa6f166e6` | 2026-06-07 | Earlier FV-7 sprint state |
| `d6d9ff8c2515782-a79f-4d56-b9c7-1d0344056eb4` | 2026-06-07 | Pre FV-7 (post Phase 10C / Daily Report rollback) |

---

## CHANGES SINCE PREVIOUS STABLE COMMIT (`3fb5c3a`)

1. `/app/frontend/src/lib/i18n.js` — added 2 Spanish translation entries for the Emergency Excavation block (FT-D1-002 fix).
2. `/app/backend/.env` — `CORS_ORIGINS` changed to `"*"` (deployment blocker fix).
3. `/app/.gitignore` — `.env`, `.env.*`, `*.env` pattern lines removed (deployment blocker fix).
4. `/app/memory/` — 8 new field-trial documents + this deployment report added.
5. No backend source files changed.
6. No frontend source files changed beyond i18n bundle.

---

## ROLLBACK STRATEGY

### Soft rollback (UI/translation only)
If only the i18n fix needs to be reverted:
```
git revert d00a56f -- frontend/src/lib/i18n.js
```
Hot-reload picks up the revert in ~2 s.

### Full rollback (this deployment)
Use Emergent platform's **Rollback** feature (free of charge per platform support guidance):
1. Go to checkpoint list in Emergent platform UI.
2. Select the previous stable checkpoint corresponding to commit `3fb5c3a` (pre-FT-D1-002 fix · pre-CORS-fix · pre-gitignore-fix).
3. Confirm rollback.

**Do NOT** use `git reset --hard` — Emergent's rollback feature is the supported path and preserves audit/observability.

### Database rollback
* No schema migrations were performed in this deployment.
* Asset metadata backfill (FV-7.1A) is idempotent — re-running is a no-op; data is preserved across rollback.
* Daily Reports and Excavations collections are untouched in this deployment cycle.
* **No DB rollback action required** for any code rollback in this checkpoint.

---

## ENVIRONMENT VARIABLE CHANGES

| Variable | Before | After | Reversion |
|---|---|---|---|
| `CORS_ORIGINS` (backend/.env) | `"https://mascidocs.com,https://www.mascidocs.com"` | `"*"` | Restore previous value if production deployment requires explicit origin allowlist |

---

## SAFE-TO-ROLLBACK INDICATORS

| Check | Status |
|---|---|
| No schema migrations performed | ✅ safe |
| No collection drops or renames | ✅ safe |
| No index removals | ✅ safe |
| Asset backfill is idempotent | ✅ safe |
| No third-party integration secrets rotated | ✅ safe |
| No user data transformed | ✅ safe |

A rollback to commit `3fb5c3a` would:
* Restore prior CORS_ORIGINS value (may need re-adjustment for any prior emergent-domain testing).
* Restore prior `.gitignore` (would re-block `.env` files — only matters for re-deploy, not for live preview).
* Revert the ES translation strings (Emergency Excavation block reverts to English-only).
* Leave all DB state intact.

---

## WHO TO CALL ON ROLLBACK

* **Emergent platform support** — for the platform Rollback feature (free).
* **MASCI internal Safety lead** — if the rollback is in response to a live field-trial issue.
* **Trial lead** — to pause the human field trial if it has already started.

---

## ARTIFACTS BUNDLED WITH THIS ROLLBACK POINT

* `DEPLOYMENT_REPORT.md` (this deployment)
* `PRE_FIELD_TRIAL_HARDENING_CERTIFICATION.md`
* `ASSET_METADATA_BACKFILL_REPORT.md`
* `REAL_ASSET_VALIDATION_REPORT.md`
* All 5 field-trial templates
* All FV-7 certification documents
* `tests/test_fv7_safety_gaps.py` (20 cases)
* `scripts/fv7_1a_asset_metadata_backfill.py` (idempotent)

These artifacts are committed alongside the code state. Rollback to `3fb5c3a` removes the i18n fix and the deployment-blocker fixes only — all field-trial documentation, asset backfill, FV-7 implementation, and tests remain.
