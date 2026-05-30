# RECOVERABILITY_CERTIFICATION

**Date:** 2026-05-30 (Batch E · Phase 4 — final recoverability determination)
**Question:** "If production disappeared completely right now, could MASCI be restored from backup?"

---

## 🟢 FINAL VERDICT — **PARTIALLY RECOVERABLE**

### Specifically:

| Recovery axis | Verdict | Notes |
|---|---|---|
| Operational data (all collections) | 🟢 FULLY RECOVERABLE | Every Daily Report · PO · Equipment Pre-Op · Safety Meeting · Incident · Training Record · Dispatch Event · Employee · Project · audit event |
| Portal-user logins (PM/HR/Shop/Dispatch/Safety/FL) | 🟢 FULLY RECOVERABLE | bcrypt hashes preserved in archive |
| Legacy admin login (`/api/admin/login`) | 🟢 FULLY RECOVERABLE | Uses `ADMIN_PASSWORD` env var, not DB |
| Master multi-login (`/api/auth/multi-login`) | 🟡 RECOVERABLE WITH MANUAL STEP | `user_directory.password_hash` redacted from archive by design; requires post-restore password reseed |
| Photo / image binaries (R2-stored) | 🟢 IF R2 SURVIVED · 🟡 IF R2 ALSO LOST | Archive contains photo bytes BUT no automated re-upload to R2 |
| Database indexes | 🟢 AUTO-RESTORED ON BACKEND BOOT | `create_index` calls in app code recreate indexes on cold start |
| Operational continuity (post-restore) | ⚪ NOT YET PROVEN END-TO-END | Drill validated data layer; live-backend boot against restored DB not exercised in this batch |

---

## 1 · What we proved (in this batch)

1. **The 442 MB complete-R2 archive exists in R2 and is downloadable** (presigned URL, no R2 credentials needed for download).
2. **The archive parses cleanly** (`zipfile` + JSON load · 0 corrupt entries out of 283 779).
3. **The archive contains all 76 data-bearing prod collections** (the 63 "missing" collections are zero-document in prod, auto-create on first write).
4. **All 1 189 mandatory-target records restore with EXACT count match** to prod source.
5. **All portal-user bcrypt password hashes survive the restore** (PM, HR, Shop, Dispatch, Safety, Field Leadership).
6. **The drill ran end-to-end in under 5 minutes** (download → extract → restore → validate → compare).
7. **The drill script enforces safety rails** (`scripts/restore_drill.py` refuses to write to live DB names).
8. **Zero collateral damage**: preview and prod databases were not modified during the drill.

---

## 2 · What we identified as gaps

| Gap | Severity | Impact in real DR scenario |
|---|---|---|
| `user_directory.password_hash` redacted from archive | 🟡 Material | Multi-login UI broken until operator manually reseeds 7 admin passwords |
| R2 photo re-upload not automated by `restore_drill.py` | 🟡 Material | If R2 is also lost: photos require a custom batch-upload step (bytes ARE in the archive) |
| Indexes not in archive | 🟢 Operational | Auto-restored on backend cold start (no operator action) |
| End-to-end live-backend boot against restored DB | ⚪ Unknown | Drill stopped at data validation; "boot a backend and confirm login + record-submit" would close the loop |
| Restore script (`restore_drill.py`) only handles `{collection}/json/*.json` shape | 🟢 Sufficient for current archives | But would not handle `/api/exports/full-backup` format (different shape) — not a blocker since complete-R2 IS the path proven |

---

## 3 · Recovery time objective (RTO) — proven empirically

| Step | Wall time | Notes |
|---|---|---|
| Get archive download URL | ~ 0.5 s | Existing endpoint |
| Download 442 MB archive | 9.4 s | From this preview container; production-class workstation would be similar |
| Extract ZIP | ~ 5 s | 283 779 entries |
| Restore to clean Mongo | ~ 60 s | insert_many ordered=False, 76 collections |
| Validation (counts + sample queries) | ~ 5 s | |
| **TOTAL Data Layer RTO** | **≈ 80 seconds** | |
| Backend bring-up against restored DB (estimate, not exercised) | ~ 30–60 s | Indexes form on cold start |
| Post-restore password reseed (7 directory users) | 5–15 min manual | Or 1-time automated step if added |
| Photo bucket re-upload (if R2 also lost) | hours · TB-scale | Not automated; custom batch step |
| **TOTAL Data + Auth + App RTO (estimate, R2 surviving)** | **≈ 10–20 minutes** | |

---

## 4 · Recovery point objective (RPO) — current production posture

While `BACKUP_R2_HOURLY=true` (current state):
- 1 complete-R2 archive per UTC hour
- **Maximum data loss window: ≤ 60 minutes**

Plus the email lite path (currently scheduled 02:00 + 18:00 UTC):
- 2 lite backups per day · emailed to `jaymn.judd@mascigc.com`
- These are an independent recovery path with smaller payload (211 KB text-only)

See `BACKUP_POSTURE_RECOMMENDATION.md` for analysis of whether 60-min RPO is the right posture vs. alternatives.

---

## 5 · Final answer to the operator's question

**"If production disappeared completely right now, could MASCI be restored from backup?"**

**YES — within ~15 minutes for the data layer + simple auth, with 60-min maximum data-loss window. Master multi-login UI requires a manual 7-user password reseed. Photo binaries are recoverable if R2 survived (current state). If R2 is also lost, photos require a custom re-upload step (their bytes are inside the archive).**

This is materially better than "untested theoretical recoverability." The drill converted the principal UNKNOWN from Batch D into 🟢 PROVEN at the data layer, with documented yellow-flag remediation paths for the auth and photo gaps.

---

## 6 · Recommended next-batch deliverables to convert remaining ⚪ to 🟢

1. **Live-backend boot drill**: spin up a transient backend container with `DB_NAME=masci_restore_drill_2026_05_30`, attempt login + post a DR + view a PDF → confirms application layer reaches operational state from restored data.
2. **Master multi-login reseed automation**: extend `/api/exports/restore` to seed `user_directory.password_hash` (same pattern as `users` collection at server.py:7596).
3. **R2-loss-also drill**: simulate R2 deletion by pointing R2 client at a parallel bucket; verify archive's `photos/` directory contains full byte coverage; build a re-upload script.
4. **Index-creation gate**: verify backend's index-creation code paths are bulletproof on a freshly-restored DB.

**None of these are scoped into Batch E.** Listed for operator roadmap.
