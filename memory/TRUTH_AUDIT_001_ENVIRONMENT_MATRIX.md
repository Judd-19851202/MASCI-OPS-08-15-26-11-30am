# TRUTH-AUDIT-001 · Environment Matrix

**Date:** 2026-06-09 · **Mode:** read-only forensic
**All claims:** primary-source verifiable in this audit session

---

## Section 1 · Environment Inventory

| # | Name | URL (entrypoint) | Database | Deployment Target | Purpose | Active? | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | **Production** | `https://mascidocs.com` | `masci_safety` (Atlas cluster `masci-prod.1nduwmg.mongodb.net`) | Operator-managed Emergent deploy | Live MASCI customer environment for superintendents, HR, admins, dispatch, field crews | ✅ ACTIVE | `curl https://mascidocs.com/api/version` → `app_env=production`, `db_name=masci_safety`, uptime 4519s, source_hash `7f68853f791fb19709cee3be9f7e70b8` |
| 2 | **Preview / Fork Container (this pod)** | `https://backup-forensics.preview.emergentagent.com` | `masci_safety_preview` (SAME Atlas cluster) | Emergent preview pod (this fork agent's working container) | E1 fork development + agent testing without touching prod data at the *database default* level — but credentials carry cluster-wide reach (see §3) | ✅ ACTIVE | `/app/backend/.env` `APP_ENV="preview"`, `DB_NAME="masci_safety_preview"`. `/api/version` confirms same. `/app/frontend/.env` `REACT_APP_BACKEND_URL=https://backup-forensics.preview.emergentagent.com` |
| 3 | **Restore Drill 2026-05-30** | (no UI — DB-only restore target) | `masci_restore_drill_2026_05_30` | One-shot restore validation DB | Backup-restore drill from 2026-05-30 — left in place as evidence (referenced in PHASE26_2_BACKUP_CONTINUITY_CERTIFICATION) | 🟡 INACTIVE (dormant) | `motor.list_database_names()` returns it; `MOTIVE_VERIFY_001 §1` previously queried it |
| 4 | **Restore Drill Auto 2026-06-01** | (no UI — DB-only) | `masci_restore_drill_auto_20260601_015003` | Automated restore drill | Auto-generated restore validation from 2026-06-01T01:50:03Z | 🟡 INACTIVE (dormant) | same |
| 5 | **Ephemeral test DBs** (21 of them) | (none — created/dropped inside pytest) | `masci_test_autoresolve_*_preview` (5) · `masci_test_webhook_harden_001_*_preview` (15) · `masci_test_webhook_harden_*_preview` (3) · `scheduler_test_iter445` | n/a — created by pytest fixtures that did not clean up after themselves | Test isolation DBs from prior fork test runs | 🟡 INACTIVE (orphaned) | listed by `list_database_names()` — 21 entries; 0 have UI surfaces |
| 6 | **Atlas system DBs** | n/a | `admin`, `config`, `local`, `sample_mflix` | Atlas-internal | Cluster metadata + Atlas sample dataset | n/a | listed by `list_database_names()` |

## Section 2 · What this matrix does NOT show

There is **no separate "development" or "staging" environment** in the Emergent platform model used here. The fork container *is* the development environment. There is no buffer between code change and the deploy gate. Deployment is operator-triggered (see `TRUTH_AUDIT_001_DEPLOYMENT_CHAIN.md`).

## Section 3 · Cross-Environment Atlas Cluster Sharing

Both `masci_safety` (production) and `masci_safety_preview` (preview) — and all 28 other DBs above — reside on the **same Atlas cluster** (`masci-prod.1nduwmg.mongodb.net`). The single Atlas credential held in the preview pod's `/app/backend/.env` has cluster-level read/write permission across all 32 DBs.

This is the critical fact that AUDIT-ACCESS-VERIFY-001 failed to surface and that this audit is forced to correct. See `TRUTH_AUDIT_001_ACCESS_MATRIX.md`.

## Section 4 · Evidence captured (this session)

```
$ python -c "
  from motor.motor_asyncio import AsyncIOMotorClient; import asyncio, os
  from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
  async def f():
    mc=AsyncIOMotorClient(os.environ['MONGO_URL'])
    print(await mc.list_database_names())
  asyncio.run(f())"

OUTPUT (sorted, 32 entries):
  admin, config, local, sample_mflix,                                  ← Atlas system
  masci_safety,                                                        ← PRODUCTION
  masci_safety_preview,                                                ← PREVIEW (this pod's default)
  masci_restore_drill_2026_05_30,
  masci_restore_drill_auto_20260601_015003,
  masci_test_autoresolve_{93de9b1c,a3455738,a6428b18,be1e58de,ebbcfe3e}_preview,
  masci_test_webhook_harden_001_{1106c20a,13b3d7e5,22282518,2df5f4a7,2e13f0e6,
                                  628025f8,687a40fc,76f19d68,7cdb8c79,94a2e498,
                                  bc0e23ef,c7274637,cd4bc01a,e4710583,f61d84a4}_preview,
  masci_test_webhook_harden_{48ec79b5,53b41102,a76214a4}_preview,
  scheduler_test_iter445
```

```
$ curl -sk https://mascidocs.com/api/version
{"service":"masci-hub","commit":"unknown","built_at":"unknown",
 "source_hash":"7f68853f791fb19709cee3be9f7e70b8",
 "app_env":"production","db_name":"masci_safety", ...}

$ curl -sk https://backup-forensics.preview.emergentagent.com/api/version
{"service":"masci-hub",
 "source_hash":"b1cfa3598c80665f606007f1e155a43c",
 "app_env":"preview","db_name":"masci_safety_preview", ...}
```
