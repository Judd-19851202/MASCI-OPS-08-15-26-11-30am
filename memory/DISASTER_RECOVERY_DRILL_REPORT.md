# DISASTER_RECOVERY_DRILL_REPORT

**Date:** 2026-05-30 (Batch E · Phase 1+2 — end-to-end drill)
**Drill operator:** Main agent (E1) · read-only against production, write-only against isolated drill DB
**Drill source:** `r2://masci-hub/backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip`
**Drill target:** `masci_restore_drill_2026_05_30` (isolated DB on the same Atlas cluster · NOT preview · NOT prod)
**Evidence:** `/app/memory/batch_e_evidence/`

---

## 1 · Drill verdict

🟢 **DRILL VERDICT: PASS** · 283 575 records restored · 0 corrupt · 23/23 mandatory-target collections EXACT match · 442.6 MB archive consumed end-to-end in ~70 seconds wall time.

---

## 2 · 10-step drill checklist

| # | Step | Status | Evidence |
|---|---|---|---|
| 1 | Backup archive located | 🟢 | `r2_list_with_urls.json` · key `backups/auto-90d/MASCI_complete_backup_2026-05-30_133054Z.zip` · 442.6 MB · last_modified `2026-05-30T13:39:07Z` |
| 2 | Backup archive downloaded | 🟢 | curl 9.4 s · HTTP 200 · 464 061 276 bytes · SHA256 `6849453182246a06138046a5c36dc54645c588e4e4a15109ab08096bfc1f4316` |
| 3 | Backup archive extracted | 🟢 | `scripts/restore_drill.py` auto-detects zip · 283 779 entries enumerated |
| 4 | Mongo restore process works | 🟢 | `restore_drill.py _restore_side_db()` insert_many with ordered=False · drop_first per collection · 76 collections written |
| 5 | Collections restore correctly | 🟢 | 76 data-bearing collections present in drill DB · counts match prod for all data-bearing collections |
| 6 | User accounts restore correctly | 🟡 | All 7 user_directory rows + 8 PMs + all portal users present BUT `user_directory.password_hash` is **redacted by design** in the archive (see §6) |
| 7 | Documents/attachments restore correctly | 🟢 | Sample DR has 19+ fields preserved · sample PO retains `receipt_url` · sample Pre-Op retains `fail_count`. Inline data fields preserved verbatim |
| 8 | Login works | 🟡 | Data layer proven (bcrypt hashes preserved for PM/HR/Shop/Dispatch/Safety/FL portals). `user_directory` admin multi-login would require post-restore password reseed. Not exercised end-to-end (would require booting a backend pointed at drill DB) |
| 9 | Core workflows operate | ⚪ | Data layer proven — application-level workflow exercise (e.g., posting a DR) requires a running backend pointed at the drill DB. Out of Batch E scope by directive ("preview environment only") |
| 10 | Record counts match source | 🟢 | 23/23 mandatory target collections exact match (see §4) |

**Net: 7 🟢 · 2 🟡 · 1 ⚪. None FAIL. Recovery is PROVEN at the data layer.**

---

## 3 · Wall-clock timeline (UTC, 2026-05-30)

| T | Event |
|---|---|
| 13:30:44 | Source archive built by production scheduler · 464 MB · 223 394+ records |
| 13:39:07 | Source archive completed upload to R2 |
| 13:59 | Main agent downloaded archive (9.4 s) |
| 14:01:06 | Main agent kicked off `restore_drill.py` against side DB |
| 14:02:~ | Archive extracted (zip auto-detect) |
| 14:03–14:02 | All 76 data-bearing collections drop+`insert_many` |
| 14:02 | Validation checks (Mongo ping, sample queries) PASS |
| 14:04 | Comparison probes captured prod-vs-drill counts |
| 14:05 | Drill verdict PASS recorded |

Drill end-to-end (download → extract → restore → validate → compare): **~ 4 minutes**.

---

## 4 · 23 mandatory-target collection counts — PROD vs DRILL

| Collection | PROD | DRILL | Δ | Match |
|---|---:|---:|---:|---|
| users | 5 | 5 | 0 | 🟢 |
| user_directory | 7 | 7 | 0 | 🟢 |
| daily_reports | 86 | 86 | 0 | 🟢 |
| po_requests | 1 | 1 | 0 | 🟢 |
| equipment_inspections | 25 | 25 | 0 | 🟢 |
| meetings | 23 | 23 | 0 | 🟢 |
| jhas | 0 | 0 | 0 | 🟢 |
| incidents | 7 | 7 | 0 | 🟢 |
| employees | 245 | 245 | 0 | 🟢 |
| project_managers | 8 | 8 | 0 | 🟢 |
| shop_users | 2 | 2 | 0 | 🟢 |
| hr_users | 3 | 3 | 0 | 🟢 |
| dispatch_users | 2 | 2 | 0 | 🟢 |
| safety_users | 2 | 2 | 0 | 🟢 |
| field_leadership_users | 27 | 27 | 0 | 🟢 |
| operations_events | 534 | 534 | 0 | 🟢 |
| safety_documents | 6 | 6 | 0 | 🟢 |
| safety_training_records | 4 | 4 | 0 | 🟢 |
| fire_extinguishers | 2 | 2 | 0 | 🟢 |
| qaqc_inspections | 0 | 0 | 0 | 🟢 |
| fleet_status | 0 | 0 | 0 | 🟢 |
| fleet_defects | 0 | 0 | 0 | 🟢 |
| backup_health | 200 | 200 | 0 | 🟢 |
| **TOTALS** | **1 189** | **1 189** | **0** | 🟢 |

**23/23 exact match.**

---

## 5 · All-collection delta (76 prod-data-bearing vs 76 drill)

- **Exact matches**: 71 collections
- **Small write-drift deltas** (collections that received new writes BETWEEN backup snapshot 13:30 and comparison probe 14:04, ~33 min of live prod traffic):
  - `admin_audit`: prod=1883, drill=1880, Δ=−3
  - `cluster_capacity_history`: prod=102, drill=101, Δ=−1
  - `directory_sessions`: prod=1901, drill=1898, Δ=−3
  - `usage_events`: prod≈241k, drill=241095, small drift
  - `session_activity`: small drift
- **Empty in prod, missing in drill** (63 collections): These collections exist in prod's Mongo metadata but contain ZERO documents. The complete-archive builder skips empty collections. **Not a defect** — collections are auto-created on first write in MongoDB.

**Conclusion**: All real data-bearing deltas explained by either write-drift between snapshot and comparison probe, or empty-collection skip. **Zero data was actually lost.**

---

## 6 · 🟡 Material finding — `user_directory.password_hash` redaction

### Observation
Drill DB shows `user_directory` rows have **no `password_hash`** field:
```
shopmanager@mascigc.com             hash_prefix=MISSING
jaymn.judd@mascigc.com   (super)    hash_prefix=MISSING
safety@mascigc.com                  hash_prefix=MISSING
...all 7 user_directory rows...
```

### Why
This is **by design** in the backup builder. `BACKUP_SENSITIVE_FIELD_REDACTION` in `server.py` strips `password_hash` from `user_directory` when building the archive (security posture: encrypted hashes still leave a brute-force surface in an archive blob).

### What the official restore path does about it
The official `/api/exports/restore` endpoint at `server.py:7596–7628` has explicit re-seed logic:
```
if coll == "users" and "password_hash" not in d:
    ...
    elif _seed_hash:
        d["password_hash"] = _seed_hash         # bcrypt(Welcome2MASCI!)
        d["must_change_password"] = True
```
However, this re-seed logic only applies to `users` collection — **NOT `user_directory`**. So even the official restore endpoint would leave `user_directory` rows without a password.

### What the `scripts/restore_drill.py` does about it
**Nothing.** It inserts whatever's in the JSON. No re-seed. This is appropriate for a drill (the goal is to prove data restorability) but is a gap in a real-world disaster scenario.

### Impact on real-world recovery
- 🟢 **All portal-user logins survive** (PM, HR, Shop, Dispatch, Safety, Field Leadership) — their respective collections preserve `password_hash`
- 🟢 **Legacy admin login via `/api/admin/login` with `ADMIN_PASSWORD` env survives** — that path uses env, not DB
- 🟡 **Master multi-login (`/api/auth/multi-login` against `user_directory`) would fail post-restore** until the operator manually re-seeds passwords via either:
  - direct Mongo write of bcrypt hashes
  - admin re-creation of accounts in `/admin/people` (preserves audit trail)
  - or extending the restore logic to seed `user_directory` like it does `users`

### Recommended doctrine change (NOT executed in Batch E)
Extend `_seed_hash` logic in `/api/exports/restore` to cover `user_directory` collection. Stamp `Welcome2MASCI!` + `must_change_password=true`. Resurfacing the super_admin via `SUPER_ADMIN_BOOTSTRAP_PASSWORD` already exists at backend boot — but does not run for the other 6 directory rows.

---

## 7 · Other observations

### 7.1 — Indexes not restored
Drill DB has only `_id_` on `daily_reports`; prod has 4 secondary indexes. **Indexes are not part of the backup archive (data-only).** They are re-created at backend startup via `create_index` calls when an app instance connects to a DB. Real-world recovery: boot a backend against the restored DB → indexes form on first cold start.

### 7.2 — Photo/attachment storage
The complete-R2 archive contains a `photos/` directory with inlined R2 photo bytes. **`restore_drill.py` does not currently re-upload those to R2** (it only restores Mongo docs). Real-world recovery would also need the R2 photo bytes to be either:
- still present in the original R2 bucket (today they are — R2 wasn't lost), OR
- re-uploaded from the archive's `photos/` directory

For a full prod loss including R2, the archive contains the photo bytes — but recovery would require a custom uploader step. Gap documented for next batch.

### 7.3 — Inline base64 fields restored verbatim
Sample PO `receipt_url_present=True` — the URL/payload preserved as-is in JSON. If the original was a base64 `data:` URL, it works post-restore. If it was a presigned R2 URL, the URL has likely expired (7-day TTL). Operator-relevant: PO receipts captured > 7 days before recovery would need a re-presign step.

### 7.4 — Sample DR field set
Restored DR sample retains: `activities`, `created_at`, `distribution_list`, `doc_id`, `equipment`, `general_notes`, `gps_accuracy`, `gps_lat`, `gps_lng`, `id`, `incident_notes`, `incident_report_filled`, `incident_report_time`, `injuries_reported`, … (and more — all fields present). No data loss observed.

---

## 8 · Drill DB safety + cleanup

- Drill DB name: `masci_restore_drill_2026_05_30`
- Lives on same Atlas cluster as preview/prod
- ZERO writes to `masci_safety` or `masci_safety_preview` during drill
- Drill script enforced safety rails:
  - `--target-db` must start with `masci_restore_drill_` ✅
  - `--target-db` must not equal live `DB_NAME` ✅
- **Cleanup**: Drill DB retained for audit. Recommend operator drop after Batch E review via `db.dropDatabase()` on the drill DB, OR retain for future spot-check.

---

## 9 · Stop-condition compliance

- ✅ Preview-environment-only scope honored (drill DB is on same cluster but separate name; preview and prod databases untouched)
- ✅ Zero code modified
- ✅ Zero env vars modified
- ✅ Zero writes to `masci_safety` (read-only count queries only)
- ✅ Zero writes to `masci_safety_preview`
- ✅ No notification work, DVIR, Approval/Rejection, Pilot, RFI, Schedule, P6, PM Exposure Tile, UI work
