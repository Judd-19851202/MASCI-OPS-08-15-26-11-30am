# PRODUCTION_RECOVERABILITY_ALIGNMENT_REPORT

**Batch:** J · Operational Reliability Closeout · P0-B
**Date:** 2026-05-30 (UTC)
**Probe time:** 2026-05-30T16:07:22Z
**Method:** Live read-only HTTP probes against `https://mascidocs.com` + side-by-side code inspection of `/app/backend` (preview source).
**Evidence files:** `prod_probes_p0b.txt`, `prod_probes_p0b2.txt`, `prod_probes_p0b3.txt`.

---

## 🟡 FINAL VERDICT — **PARTIAL ALIGNMENT**

| Aspect | Status |
|---|:--:|
| Backup scheduler | 🟢 ALIGNED (production healthy — see PRODUCTION_SCHEDULER_CERTIFICATION_REPORT) |
| Backup configuration | 🟢 ALIGNED (twice-daily lite + hourly complete-r2 · `auto_email_enabled: true`) |
| User Directory (GAP-2 / Batch G) | 🟦 INFERRED ALIGNED (endpoint live + 7 users · code path verified in preview · prod-side source hash not exposed) |
| Recovery tooling presence | 🟢 ALIGNED (`/api/exports/restore` accepting `file` POST · scripts present in repo) |
| **Photo architecture migration (Batch G)** | 🔴 **NOT RUN ON PROD** — direct evidence: prod DR-2026-00279 still has inline 347 KB base64 photo |
| **Photo write-path defense (Batch H)** | 🔴 **NOT DEPLOYED OR NOT EFFECTIVE** — same evidence |
| Version / source hash alignment | 🟡 NO VERSION ENDPOINT — cannot directly compare preview-source-hash with prod-deployed-hash |

---

## 1 · GAP-2 deployment status (Batch G multi-login reseed code)

**Required:** the Batch G `_seed_hash` extension to `("users", "user_directory")` should be present in production for restore-time auth recovery.

| Verification | Result | Evidence |
|---|:--:|---|
| Preview source has the code | 🟢 | `grep _seed_hash /app/backend/server.py` → hits at lines 7601, 7606, 7619, 7631 (J-P15) |
| Preview source enumerates BOTH collections | 🟢 | `_NEEDS_SEED_HASH = ("users", "user_directory")` at server.py:7602 |
| Production restore endpoint reachable | 🟢 | `POST /api/exports/restore` → HTTP 422 ("body.file required") confirms endpoint is wired (J-P10) |
| Production directory has users | 🟢 | `GET /api/admin/directory` → `{ok: true, users: [7 entries]}` with emails: `leticiamasci@`, `masciaccounting@`, `dispatch@`, `safety@`, `shopmanager@`, plus 2 more (J-P13) |
| Direct prod source-hash comparison | 🟡 | No version endpoint exists (`/api/admin/source-hash`, `/api/admin/version`, `/api/admin/code-version`, `/api/admin/deploy-version`, `/api/admin/build-info` all 404) |

**Verdict:** 🟦 GAP-2 logic is **inferred deployed** based on (a) preview source containing the code, (b) production directory functional with 7 users, (c) prod restore endpoint correctly shaped. Direct git-SHA confirmation cannot be performed from this environment. **Operator can verify by inspecting most recent prod deploy log** to confirm `server.py:7594–7635` was included.

---

## 2 · Photo architecture status — confirmed NOT migrated

### 2.1 Direct evidence

Pulled production DR via `GET /api/daily-reports/346d7dfb-568d-41ae-8e32-2f289c7b3818` (J-P9):

| Field | Value |
|---|---|
| `doc_id` | `DR-2026-00279` |
| `audit_envelope_sha256` | `e2243235a0bf12fea89b54cb069786bf95ecd2e2…` |
| `photos.len` | 7 |
| **`photos[0]`** | **`BASE64_INLINE (len=347559)`** ← 347 KB inline base64 string |
| `photos[0]` shape | starts with `data:image/...` — NOT `photo://` |

**Conclusion:** the Batch G migration (`scripts/migrate_dr_photos.py`) has NOT been executed against the production database. Inline base64 photos persist on at least DR-2026-00279.

### 2.2 Cross-references confirming this is expected

- `BATCH_G_EXECUTIVE_SUMMARY.md §5` and `BATCH_H_EXECUTIVE_SUMMARY.md §5`: both call out "OPERATOR ACTION REQUIRED: run `python3 scripts/migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod --apply` against production"
- `PLATFORM_RECOVERABILITY_PROOF_REPORT.md §6 item 1`: same operator action still pending

### 2.3 Operational impact (current state)

- Production R2 bucket is at **~80 GB** (per `r2-usage-alert` rows in P0-A · `gb=80.64 objects=2778`)
- Backup archives are **~464 MB** each (vs the post-migration target of ~115 MB)
- Worker OOM watermark is 600 MB → current archive 464 MB leaves ~22 % headroom but the trajectory documented in Batch G persists
- All backups continue to succeed (`ok=true`) — no immediate failure, but the documented OOM trajectory is real

---

## 3 · Photo write-path defense (Batch H `_sanitize_inline_photos`) deployment status

| Verification | Result | Evidence |
|---|:--:|---|
| Preview source has the code | 🟢 | `grep _sanitize_inline_photos /app/backend/routes/daily_reports.py` → function defined at line 186, invoked at line 257 (J-P16) |
| Code is wired in DR submit handler | 🟢 | Insertion confirmed between `doc = report.model_dump()` and `_compute_audit_envelope_sha256(doc)` |
| Production source contains the same code | 🔴 cannot directly verify (no version endpoint) |
| Production DR has been sanitized | 🔴 NO — DR-2026-00279 still inline (J-P9) — but this DR may pre-date any deploy |

**Interpretation:** the existence of inline-base64 in DR-2026-00279 PROVES one of these:
- (a) Batch H code was never deployed to prod
- (b) Batch H was deployed but this DR was submitted BEFORE the deploy
- (c) Batch H is deployed but R2 was unreachable at submit time and the soft-fail path kept inline

Without a version endpoint to compare source hashes, we cannot distinguish (a) from (b) from (c).

**Operator can verify** by either:
1. Checking the most recent prod deploy log for `routes/daily_reports.py` changes
2. Submitting a new test DR with 1 base64 photo and inspecting whether it lands as `photo://` ref or inline base64

---

## 4 · Backup configuration alignment

| Setting | Preview env | Production runtime | Aligned? |
|---|---|---|:--:|
| `scheduled_hours_utc` | [2, 18] | [2, 18] | 🟢 |
| `lite_mode_only_env` | true | true | 🟢 |
| `oom_watermark_mb` | 600 | 600 | 🟢 |
| `watchdog_threshold_hours` | 25.0 | 25.0 | 🟢 |
| `circuit_breaker_max_attempts_per_day` | 3 | 3 | 🟢 |
| `retention_days` (local) | 14 | 14 | 🟢 |
| `storage_dir` (local) | `/app/backend/backups` | `/app/backend/backups` | 🟢 |
| `auto_email_enabled` | false | **true** | 🟢 expected divergence (preview suppresses email; prod sends) |

All knob alignment confirmed.

---

## 5 · Recovery tooling presence

| Artifact | Preview | Production | Status |
|---|:--:|:--:|:--:|
| `/app/scripts/restore_drill.py` | ✅ | (inherits deploy) | 🟢 |
| `/app/scripts/migrate_dr_photos.py` | ✅ | (inherits deploy) | 🟢 |
| `routes/daily_reports.py:_sanitize_inline_photos` | ✅ line 186 | (inherits deploy) | 🟦 inferred deployed but evidence weak (see §3) |
| `server.py:_seed_hash` GAP-2 extension | ✅ line 7601 | (inferred deployed) | 🟦 see §1 |
| `POST /api/exports/restore` admin endpoint | ✅ | ✅ accepts `file` POST (J-P10) | 🟢 |

---

## 6 · Source hash / version alignment

| Method | Result |
|---|---|
| `/api/admin/source-hash` | 🔴 404 |
| `/api/admin/version` | 🔴 404 |
| `/api/admin/code-version` | 🔴 404 |
| `/api/admin/deploy-version` | 🔴 404 |
| `/api/admin/build-info` | 🔴 404 |

**Verdict:** 🟡 **No prod-exposed version endpoint.** Operators cannot remotely verify which preview commit is currently deployed to prod. This is a gap of its own — not a defect, but a hygiene improvement for future batches.

**Workaround for the operator:**
1. Inspect the most recent `git log` against the deployed branch
2. Cross-reference with deploy-pipeline logs
3. Compare key file mtimes / line counts: `/app/backend/server.py` is currently 10,400 lines (preview); `/app/backend/routes/daily_reports.py` is 562 lines (preview)

---

## 7 · Summary table — production alignment matrix

| # | Component | Aligned? | Evidence | Action needed |
|---|---|:--:|---|---|
| 1 | Scheduler alive | 🟢 | J-P2 | none |
| 2 | Backup cadence | 🟢 | J-P2 | none |
| 3 | Email path | 🟢 | J-P2 `emailed_to` rows | none |
| 4 | User Directory | 🟦 | J-P13 (7 users, all rows healthy) | operator confirms deploy log includes `_seed_hash` change |
| 5 | Restore tooling reachable | 🟢 | J-P10 | none |
| 6 | **Photo migration on prod** | 🔴 | J-P9 (DR-2026-00279 still inline base64) | **Run `migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod --apply --backup-dir <path>` in prod** |
| 7 | **Photo write-path defense deployed** | 🔴 likely undeployed | J-P9 + no version endpoint | **Trigger fresh deploy of preview→prod or test by submitting a new DR with base64 photo and inspecting result** |
| 8 | Version visibility | 🟡 | J-P14 (all 404) | optional: expose `/api/admin/version` returning git SHA |

---

## 8 · Concrete operator actions (prioritized)

1. **Run the prod photo migration** (P0 — closes 🔴 #6 and shrinks R2 from 80 GB → ~20 GB and archive from 464 MB → ~115 MB):
   ```bash
   python3 /app/scripts/migrate_dr_photos.py \
     --target-db masci_safety \
     --i-know-this-is-prod \
     --apply \
     --backup-dir /app/memory/dr_migration_backups
   ```
2. **Confirm Batch G + H code is in the prod deploy** (P0 — closes 🔴 #7):
   - Inspect the most recent deploy log; or
   - Submit a new test DR with 1 base64 photo to `https://mascidocs.com/api/daily-reports` and inspect whether `photos[0]` is `photo://...` or `data:image/...` in the response
3. **Optional**: expose `/api/admin/version` returning the deployed git SHA — small future hygiene improvement (P3, NOT for this batch)

---

## 9 · Stop-condition compliance

- ✅ Read-only GET probes only (one POST to `/api/exports/restore` with empty body was for endpoint-shape verification — returned 422 validation error, did NOT trigger a restore)
- ✅ No production writes
- ✅ No code changes
- ✅ No env changes
- ✅ All evidence captured to `batch_j_evidence/prod_probes_p0b*.txt`

---

_End of PRODUCTION_RECOVERABILITY_ALIGNMENT_REPORT.md · 🟡 **PARTIAL ALIGNMENT** — photo migration outstanding._
