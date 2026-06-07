# PRODUCTION CLEANLINESS GATE

**Date**: 2026-02-12
**Subject**: Excavation Operations · production deployment readiness gate
**Posture**: STRICT — zero contamination tolerated.

---

## GATE STRUCTURE

Production is GO if and only if **EVERY** one of the 10 criteria below is independently verified.

If any criterion is unverified or fails, the final verdict is **NO GO** and production deployment is forbidden under OMEGA discipline.

---

## CRITERIA

| # | Criterion | Detail file | Status at this point in time |
|---|---|---|---|
| 1 | Production Mongo DB_NAME is separate from preview (`masci_safety_preview`) AND production Mongo URI does not point to preview DB | `PRODUCTION_DATA_SEPARATION_REPORT.md` | ⏳ **operator-confirmed required** · cluster shared, DB_NAME separation enforced by env var. |
| 2 | No deployment/migration/seed script writes preview/test/demo/smoke records to production | `PRODUCTION_TEST_DATA_SCAN_REPORT.md` | ✅ no automated path exists. ⚠️ TB-NTF-* placeholders + FV-7.1A backfill require operator-attention. |
| 3 | Production seed scripts disabled OR operator-gated | `PRODUCTION_TEST_DATA_SCAN_REPORT.md` | ⚠️ `dls_seed_demo.py` is operator-only (hard-blocks `_PRODUCTION_TENANT`). FV-7.1A backfill is operator-invoked only. Boot-time seed chain runs in ALL envs and includes TB-NTF-* — operator must gate or accept. |
| 4 | All seeded users / projects / assets / employees are real MASCI data | `PRODUCTION_EMPTY_STATE_CERTIFICATION.md` | ✅ users (5 real owners), employees (JSON roster), jobs (JSON), trench-safety real boxes — all real. ⚠️ TB-NTF-* placeholder + FV-7.1A "pending tabulated-data verification" labels are transparent but non-verified. |
| 5 | Production env (`APP_ENV=production` · prod CORS · prod DB_NAME · no preview domain as canonical) is correctly configured | `PRODUCTION_ENV_SECURITY_REVIEW.md` | ⏳ operator-confirmed required. |
| 6 | Production CORS is locked down — no `CORS_ORIGINS="*"` | `PRODUCTION_ENV_SECURITY_REVIEW.md` | ⏳ operator-confirmed required. Current preview is `"*"` (intentional). |
| 7 | No secret exposed in client bundle (Mongo URI · Resend key · R2 secret · admin password) | `PRODUCTION_ENV_SECURITY_REVIEW.md` | ✅ verified by `REACT_APP_*` prefix rule. Operator must grep-confirm post-build. |
| 8 | No migration copies preview→production data | `PRODUCTION_TEST_DATA_SCAN_REPORT.md` | ✅ no such path exists. |
| 9 | Production empty-state certification can be completed by operator after cutover | `PRODUCTION_EMPTY_STATE_CERTIFICATION.md` | ⏳ template provided · operator must execute after cutover. |
| 10 | Rollback reference exists · DB backup mechanism active · rollback procedure documented | this file + `DEPLOYMENT_ROLLBACK_REFERENCE.md` | ✅ rollback reference present · `BACKUP_R2_HOURLY=true` · `BACKUP_HOURS_UTC=2,18` in env · operator procedure documented. |

---

## ROLL-UP

| Criterion bucket | Count |
|---|---|
| ✅ Verified | 4 (criteria 2 · 7 · 8 · 10) |
| ⏳ Requires operator action / confirmation | 6 (criteria 1 · 3 · 4 [TB-NTF caveat] · 5 · 6 · 9) |
| ❌ Failed | 0 |

---

## CURRENT GATE STATUS

# **NOT YET GO** ⏳

Reason: **6 of 10 criteria require explicit operator action or post-cutover verification** before they can be ticked GREEN.

No criterion has FAILED. The gate is paused at "awaiting operator confirmation," not "rejected."

---

## OPERATOR ACTION QUEUE (sequenced)

1. **Confirm production env values** (`APP_ENV=production` · `DB_NAME` ≠ preview · `CORS_ORIGINS` explicit allowlist · `RATE_LIMITING=on` · `SCHEDULER_ENABLED=true`).
2. **Decide on TB-NTF-\* placeholders**: gate by APP_ENV, remove from seed, or accept as real.
3. **Decide on FV-7.1A backfill**: skip on production OR run with real manufacturer data substitution OR accept transparent placeholders.
4. **Decide on R2 bucket separation** (recommended: separate prod bucket or prefix discipline).
5. **Decide on Resend API key separation** (recommended: sandbox sender for preview).
6. **Rotate** `JWT_SECRET` · `ADMIN_HMAC_SECRET` · `MFA_ENCRYPTION_KEY` · `SUPER_ADMIN_BOOTSTRAP_PASSWORD` per MASCI policy before cutover.
7. **Execute production empty-state inventory script** (in `PRODUCTION_EMPTY_STATE_CERTIFICATION.md`) immediately after first boot. Re-publish the certification with real numbers.
8. **Confirm DB backup is current** and accessible (BACKUP_R2_HOURLY + scheduled cron).
9. **Confirm rollback procedure** with Emergent platform support if escalation needed.

---

## NEXT STEP

→ `PRODUCTION_GO_NO_GO_DECISION.md` — final verdict.
