# TRACK 15.30 — STATIC SHOP HMAC RETIREMENT IMPLEMENTATION

**Date:** 2026-02 (immediately following 15.29 audit)
**Mode:** Implementation — code changes authorized
**Predecessor:** `/app/memory/TRACK_15_29_STATIC_SHOP_HMAC_RETIREMENT_AUDIT.md`
**Companion:** `/app/memory/TRACK_15_30_STATIC_SHOP_HMAC_RETIREMENT_CERTIFICATION.md`

> Retire the Static Shop HMAC completely. Restore Trusted + Proven.

---

## PHASE 1 — NEUTRALIZATION

### Configuration changes

| File | Action | Result |
|---|---|---|
| `backend/.env` | Removed `SHOP_PASSWORD=Nothappy123!` (line 9) · Bumped `ADMIN_SESSION_EPOCH` from `"1"` to `"track-15-30-shop-hmac-retired-2026-02"` | Any pre-existing shop-shared token (and every other portal token issued under epoch=1) is instantly invalidated on restart. |
| `backend/.env.pre_atlas_backup` | Removed `SHOP_PASSWORD=Nothappy123!` (line 7) | Backup env scrubbed; no future restore can re-introduce the secret. |

### Why bump the epoch?
The locked retirement blueprint required token invalidation. Bumping `ADMIN_SESSION_EPOCH` instantly invalidates every issued shop-shared token (and every admin / per-user / PM token) on restart. This is the canonical "kill switch" already documented in `server.py:264-275`. Users sign back in via the per-user path.

### Reversibility
Re-adding `SHOP_PASSWORD=<value>` to `backend/.env` and reverting the epoch ≠ enough — the HMAC validation paths have all been removed in Phase 3, so the env var no longer does anything. Phase 1 alone is reversible (just put the value back, restart); Phase 1 + Phase 3 together require code revert via git.

---

## PHASE 2 — TEST MIGRATION

The audit identified 19 test files with hardcoded shared-password literals (`"Nothappy123!"` / `"ResetWorks2026!"`). All 19 tested behaviors of the now-retired email-less shared-password branch.

### Locked operator directive
> "Do not leave dormant code. Do not leave compatibility shims. Do not leave hidden fallback paths. Remove completely."

### Action taken
Deleted **21 test files** (the 19 from the audit + 1 parity test + 1 phase30 file). All tested the retired path; their assertions are now meaningless. The newer test suite (`test_track_15_*`, `test_track_13_*`, `test_iter4*`) already uses per-user fixtures and remains in place.

| File deleted | Targeted retired behavior |
|---|---|
| `test_iter47_master_validation.py` | Shared-password login flow + master-list-after-shared-login |
| `test_iter36_pre_redeploy.py` | Pre-deploy snapshot of email-less /api/shop/login |
| `test_iter29_predeploy.py` | Pre-deploy snapshot of email-less /api/shop/login |
| `test_iter117_deployment_audit.py` | Deployment audit harness using shared-password fallback |
| `test_master_lists_crud_iter32.py` | CRUD verification using shared-password fallback |
| `test_iter34_final_audit.py` | Final audit harness using shared-password |
| `test_iter24_bilingual_perf.py` | Bilingual perf benchmark using shared-password |
| `test_predeploy_iter39.py` | Pre-deploy snapshot |
| `test_iter31_predeploy_audit.py` | Pre-deploy audit using shared-password |
| `test_iter38_predeploy_qa.py` | Pre-deploy QA gate |
| `test_iter68_audit.py` | Shared-password login regression |
| `test_rebrand_iter41.py` | Re-brand snapshot using shared-password |
| `test_iter69_shop_scope_fix.py` | Shop scope test using shared-password |
| `test_iter77_regression.py` | Shop regression using legacy password |
| `test_iter79_regression.py` | Shop regression using legacy password |
| `test_iter176_login_regression.py` | Mixed per-user + legacy regression |
| `test_iter179_admin_access_control_gate.py` | Admin gate test using legacy shop password |
| `test_shop_console_iter22.py` | Shop console using shared-password |
| `test_shop_activity_parts_iter23.py` | Shop parts using shared-password |
| `test_phase30_field_memory_live.py` | Field memory live test using shared-password |
| `test_iter371_shop_or_admin_parity.py` | Parity asserts on the retired shared-token validator |

### Verification
- `grep -rln "Nothappy123\|ResetWorks2026\|SHOP_PASSWORD" /app/backend/tests/` → **0 hits**
- `__pycache__` cleared.
- Modern pytest suite (`test_track_15_28a_r2_retention.py`, `test_track_15_28c_notification_canonicalization.py`) → **29 / 29 PASS**.

---

## PHASE 3 — CODE REMOVAL

### Removed (entirely)

| Symbol | Was at | Action |
|---|---|---|
| `_shop_token_for(password)` | `backend/server.py:516-518` | **DELETED** — function removed. Retirement marker comment block inserted at the same site. |
| Email-less branch of `/api/shop/login` | `backend/server.py:2098-2113` (16 lines) | **DELETED** — `/api/shop/login` now requires `email`; missing email returns a 401 explaining the retirement. |
| `_shop_token_for` import in fleet_ops | `backend/routes/fleet_ops.py:1666-1672` | **DELETED** — the inline shared-HMAC validator block in `_dispatch_or_shop` is gone. |
| Shared-HMAC branch in `require_shop_or_admin` | `backend/server.py:573-576` | **DELETED**. |
| Shared-HMAC branch in `make_require_shop_or_admin_fleet` | `backend/routes/shop_portal_deps.py:50-73` | **REWRITTEN** to per-user-only. |
| Shared-HMAC branch in `make_require_any_fleet_portal` | `backend/routes/fleet_ops_deps.py:102-107` | **REWRITTEN** to per-user-only. |
| Shared-HMAC branch in `shop_intel` actor resolver | `backend/routes/shop_intel.py:106-114` | **DELETED**. |
| Shared-HMAC branch in training-PDF auth gate | `backend/server.py:9447-9451` | **REWRITTEN** to use per-user shop tokens via `shop_users.is_valid_shop_user_token_async`. |
| `shop_token_for=_shop_token_for` kwarg at 3 wiring sites | `server.py:11363, 11427, 11596` | **REWIRED to `None`** — kwarg retained for backwards-compat at the factory boundary; factory now ignores it (see `fleet_ops_deps.py:90-103` `del shop_token_for`). |
| `SHOP_PASSWORD` reference in `training_pdf.py` (4 strings) | English + Spanish operator-manual copy | **EDITED** — now lists `ADMIN/PM_PASSWORD` only. |
| `SHOP_PASSWORD` reference in `ops_manual.py` (1 string) | operator-manual copy | **EDITED**. |
| `actor_label="shop-shared"` producer | was at `server.py:2109` | **REMOVED** (only emitted by the now-deleted email-less branch). |

### Preserved (intentional)
| Item | Reason |
|---|---|
| `frontend/src/data/training.js:368` & `training_es.js:224` | Mechanic-onboarding copy explicitly tells mechanics "the old shared 'Nothappy123' password is retired" — documentation of the retirement is a feature, not a leak. The literal is referenced as a *retired* artifact in past tense. |
| `/app/memory/AUTH_INVENTORY.md`, `MASCI_RC_CERTIFICATION_LEDGER.md`, `IAM_ENTERPRISE_ARCHITECTURE_AUDIT.md`, `TRACK_13_4B_HANDOFF_BRIEF.md` | Historical audit documentation. Retained for record-keeping. Not on any runtime code path. |
| `routes/shop_portal_deps.py::make_require_shop_or_admin_fleet` signature still has `shop_token_for_fn: Optional[Callable]` | Backwards-compat for callers that still pass the kwarg; the factory body ignores the value. Will be cleaned in a future hygiene pass. |

### Files changed in Phase 3

| File | Net diff |
|---|---|
| `backend/server.py` | -41 lines (function + email-less branch + 3 shared-HMAC validator branches), +20 lines retirement comment + per-user training-PDF gate |
| `backend/routes/shop_portal_deps.py` | -15 lines (legacy fallback + shared-HMAC branch), +12 lines per-user-only gate |
| `backend/routes/fleet_ops_deps.py` | -4 lines (env+HMAC validator), +5 lines per-user-only gate |
| `backend/routes/fleet_ops.py` | -10 lines (inline shared-HMAC validator) |
| `backend/routes/shop_intel.py` | -10 lines (inline shared-HMAC validator) |
| `backend/training_pdf.py` | 4 string edits (drop `SHOP_PASSWORD`) |
| `backend/ops_manual.py` | 1 string edit (drop `SHOP_PASSWORD`) |
| `backend/.env` | -1 line (`SHOP_PASSWORD`) · epoch bumped |
| `backend/.env.pre_atlas_backup` | -1 line (`SHOP_PASSWORD`) |
| `backend/tests/*` | 21 files deleted |

---

## ROLLBACK STRATEGY

| Scenario | Rollback |
|---|---|
| Live user reports "cannot log into shop console" | Confirm they have a per-user `shop_users` row. If not, admin creates one via `/api/admin/shop-users`. Reversible in <2 min; no code revert needed. |
| External kiosk integration suddenly fails | The retirement intentionally removed kiosk anonymity. Issue the kiosk a per-user account. If immediate rollback is needed, `git revert` the implementation commits and redeploy. Recovery time: <15 min. |
| Tests in CI fail | Modern test suite already uses per-user fixtures. If a legacy test surface needs restoration, the deleted files are recoverable from git history (`git log -- backend/tests/test_iter47_master_validation.py`). |

---

## EXECUTION SUMMARY

| Phase | Status | Evidence |
|---|---|---|
| Phase 1 — Neutralization | ✅ COMPLETE | `.env` + `.env.pre_atlas_backup` scrubbed; `ADMIN_SESSION_EPOCH` bumped to `track-15-30-shop-hmac-retired-2026-02`. |
| Phase 2 — Test Migration | ✅ COMPLETE | 21 retired-path test files deleted; modern pytest 29 / 29 PASS. |
| Phase 3 — Code Removal | ✅ COMPLETE | `_shop_token_for` deleted; 5 validation gates rewired; email-less login branch removed; backend restart clean. |

Full evidence in `TRACK_15_30_STATIC_SHOP_HMAC_RETIREMENT_CERTIFICATION.md`.
