# POST_DEPLOY_VALIDATION_MATRIX

**Phase:** OMEGA Phase P · Production Deployment Readiness · Phase 4
**Date:** 2026-05-30 (UTC)
**Method:** Build a per-improvement validation matrix. Each OMEGA improvement maps to verifications in 7 dimensions: Health · Runtime · Database · Notifications · Tasks · Ownership · Dashboard Visibility. Each verification has explicit PASS/FAIL criteria.
**Mandate:** READ-ONLY plan. No verifications executed — these are operator-supervised post-deploy probes.

---

## 🎯 USAGE

Run this matrix in order at T+5 → T+35 min of the production deployment window. Each cell carries a curl/python probe + PASS criterion + FAIL criterion + next step on FAIL.

---

## 1 · Core platform health (must pass BEFORE any improvement validation)

### 1.1 · Backend `/api/health`

| Probe | PASS | FAIL |
|---|---|---|
| `curl -s https://mascidocs.com/api/health \| jq` | `{"ok":true,"service":"masci-hub","ts":<recent-iso>}` | non-200 OR `ok=false` OR no response within 10 sec |
| On FAIL | → Halt deploy. Rollback Path C (application rollback). | |

### 1.2 · Backend `/api/version`

| Probe | PASS | FAIL |
|---|---|---|
| `curl -s https://mascidocs.com/api/version` | `source_hash == "550118913c503ae6d206223be384372f"` AND `app_env == "production"` AND `db_name == "masci_safety"` AND `uptime_s > 30` | Any field mismatch |
| On FAIL | → Halt. Investigate which build was deployed. Path C if wrong build. | |

### 1.3 · Backup scheduler continuity

| Probe | PASS | FAIL |
|---|---|---|
| `curl "https://mascidocs.com/api/admin/backup-verification/recent-health?limit=4" -H "X-Admin-Token: $TOKEN"` | `scheduler.alive == true` AND `last_tick_ts > deploy_start_ts` AND `failed_attempts == {}` AND `recent_health[0].ok == true` | scheduler.alive=false OR last_tick_ts stuck for > 5 min |
| On FAIL | → Investigate. Backend restart (case b in §5 of ROLLBACK_CERTIFICATION). | |

---

## 2 · Improvement-by-improvement validation matrix

### 2.1 · OMEGA-1 / Photo Migration

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `curl https://mascidocs.com/api/health` | 200 ok=true (no regression from migration) | non-200 | Halt migration. Path A rollback on migrated DRs. |
| **Runtime** | Re-run dry-run: `python3 scripts/migrate_dr_photos.py --target-db masci_safety --i-know-this-is-prod` | `Photos to migrate: 0` AND `DRs already clean: 86` AND `DRs failed: 0` | Any non-zero photos remaining OR any DRs failed | Path A rollback on the failed DRs; re-attempt |
| **Database** | `db.daily_reports.find_one({}, {"_id":0, "photos":1})` for 5 random DRs | All `photos[]` entries start with `photo://` (no `data:image/` anywhere) | Any inline base64 remaining | Same |
| **Notifications** | n/a — migration doesn't emit notifications | n/a | n/a | n/a |
| **Tasks** | n/a — migration doesn't emit tasks | n/a | n/a | n/a |
| **Ownership** | n/a | n/a | n/a | n/a |
| **Dashboard** | Render `/api/daily-reports/<id>` PDF for 5 random DRs | All photos render correctly (R2 fetch + JPEG decode) | Any photo renders blank/broken | Investigate `photo_storage.read_photo_bytes`; Path A on the affected DR |
| **Backup-side** | Wait for next `recent_health[0].size_bytes` after migration | drops from ~464 MB → ~115 MB | size_bytes unchanged | Investigate scheduler; manual archive cut |

### 2.2 · OMEGA-2 / Batch H Write-Path Defense

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `/api/health` after canary DR POST | 200 ok=true | non-200 | Path C rollback |
| **Runtime** | Operator POSTs canary DR with 1 inline base64 photo via `/api/daily-reports` | HTTP 200 + response carries `photo://` ref in `photos[0]` (NOT `data:image/`) | `photos[0]` is still inline base64 | Investigate `_sanitize_inline_photos` invocation; Path C if needed |
| **Database** | `db.daily_reports.find_one({"id":<canary>})` | `photos[0]` starts with `photo://` | inline base64 stored | Same |
| **Notifications** | n/a — Batch H doesn't emit notifications | n/a | n/a | n/a |
| **Tasks** | n/a | n/a | n/a | n/a |
| **Ownership** | n/a | n/a | n/a | n/a |
| **Dashboard** | Render canary DR PDF | All photos visible | broken | Investigate; Path C |

### 2.3 · OMEGA-3 / Fleet DVIR Routing (Batch L)

3-case matrix per `FLEET_DVIR_CERTIFICATION.md §3`:

#### Case A · Normal DVIR

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `/api/health` post-submit | 200 ok=true | non-200 | Path C |
| **Runtime** | `POST /api/fleet/inspections` with all-pass checklist | HTTP 200 ok=true · `defect_count=0` · `truck_status_after=available` | Any deviation | Path C |
| **Database** | Mongo `tasks` and `notifications` count delta pre/post | tasks +0 · notifications +0 | Non-zero deltas | Path C — code is emitting on Normal class (incorrect) |
| **Notifications** | `/api/notifications?source_module=fleet.dvir` | No new rows for the canary inspection id | New rows exist | Path C |
| **Tasks** | `/api/tasks?source_module=fleet.dvir` | No new rows for canary | New rows exist | Path C |
| **Ownership** | n/a | n/a | n/a | n/a |
| **Dashboard** | Shop Hub bell shows no new items | No new items | New items appear | Path C |

#### Case B · Defect DVIR (severity=monitor, no OOS)

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `/api/health` post-submit | 200 ok=true | non-200 | Path C |
| **Runtime** | `POST /api/fleet/inspections` with 1 fail (non-brake) | HTTP 200 ok=true · `defect_count=1` · `out_of_service=false` · `truck_status_after=defect_open` | deviation | Path C |
| **Database** | tasks/notifications delta | tasks +1 · notifications +2 (1 dvir.defect + 1 task.assigned auto-emit) | Wrong count | Path C |
| **Notifications** | Mongo query | type=`dvir.defect` · severity=`Warning` · recipient_role=`shop` · title contains canary unit number | mismatch | Path C |
| **Tasks** | Mongo query | source_module=`fleet.dvir` · assignee_role=`shop` · priority=`Medium` | mismatch | Path C |
| **Ownership** | Task's `assignee_role` field | exactly `shop` | anything else | Path C |
| **Dashboard** | Shop Hub bell · `/tasks` view | New row visible with correct title | Not visible | Investigate notifications query path |

#### Case C · OOS DVIR (any oos or out_of_service=Yes)

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `/api/health` | 200 ok=true | non-200 | Path C |
| **Runtime** | `POST /api/fleet/inspections` with brake fail | HTTP 200 · `defect_count=1` · `out_of_service=true` · `truck_status_after=oos` | deviation | Path C |
| **Database** | tasks/notifications delta | tasks +1 · notifications +3 (1 dvir.defect.oos to shop + 1 dvir.defect.oos to dispatch + 1 task.assigned to shop) | Wrong count | Path C |
| **Notifications** | Mongo query | TWO rows of type=`dvir.defect.oos`: one with recipient_role=`shop`, one with recipient_role=`dispatch` | Single row OR wrong roles | Path C |
| **Tasks** | Mongo query | source_module=`fleet.dvir` · assignee_role=`shop` · priority=`Critical` | mismatch | Path C |
| **Ownership** | Shop task + Dispatch notification (visibility only, no Dispatch task) | Shop task exists · Dispatch task does NOT exist (per decision package §3) | Dispatch task created (wrong) | Path C |
| **Dashboard** | Shop Hub bell shows Critical task · Dispatch Hub bell shows visibility notification | Both visible | Either missing | Investigate; Path C if structural |

### 2.4 · OMEGA-5 / Field Leadership Forms

| Dimension | Probe | PASS criterion | FAIL criterion | On FAIL |
|---|---|---|---|---|
| **Health** | `/api/health` post-submit | 200 ok=true | non-200 | Path C |
| **Runtime** | Operator POSTs canary Field Leadership form via the FL submission route | HTTP 200 + 1 row in `field_leadership_records` | Submission rejected | Path C |
| **Database** | tasks/notifications delta | tasks +1 · notifications +2 (1 fl.submitted + 1 task.assigned auto) | Wrong count | Path C |
| **Notifications** | Mongo query | type=`fl.submitted` · recipient_role=`safety` · severity=`Info` | mismatch | Path C |
| **Tasks** | Mongo query | source_module=`field_leadership.records` · assignee_role=`safety` | mismatch | Path C |
| **Ownership** | assignee_role | exactly `safety` | anything else | Path C |
| **Dashboard** | Safety Hub bell + `/tasks` (safety scope) | New row visible | Not visible | Investigate notification query |

### 2.5 · OMEGA-6 / Safety Equipment Issuance + Return + Training (3 events)

#### 2.5.1 · Issuance

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | POST canary issuance | HTTP 200 + row in `safety_equipment_issuances` | Rejected |
| DB delta | tasks +1 · notifications +2 (1 safety_form.issuance + 1 task.assigned) | Wrong | Path C |
| Notification fields | type=`safety_form.issuance` · recipient_role=`safety` | mismatch | Path C |
| Task fields | source_module=`safety.form.issuance` · assignee_role=`safety` | mismatch | Path C |
| Dashboard | Safety Hub bell | Visible | Not visible |

#### 2.5.2 · Return

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | POST canary return | HTTP 200 + return sub-record on existing issuance | Rejected |
| DB delta | tasks +0 (no task — notification only) · notifications +1 | Wrong | Path C |
| Notification fields | type=`safety_form.return` · recipient_role=`safety` · severity=`Warning` if chargeback else `Info` | mismatch | Path C |
| Dashboard | Safety Hub bell | Visible | Not visible |

#### 2.5.3 · Training

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | POST canary training | HTTP 200 + row in `safety_equipment_trainings` | Rejected |
| DB delta | tasks +1 · notifications +2 | Wrong | Path C |
| Notification fields | type=`safety_form.training` · recipient_role=`safety` | mismatch | Path C |
| Task fields | source_module=`safety.form.training` · assignee_role=`safety` | mismatch | Path C |
| Dashboard | Safety Hub bell | Visible | Not visible |

### 2.6 · OMEGA-7 / JHA Submit

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | POST canary JHA | HTTP 200 + row in `jhas` | Rejected |
| DB delta | tasks +1 · notifications +2 | Wrong | Path C |
| Notification fields | type=`jha.submitted` · recipient_role=`safety` | mismatch | Path C |
| Task fields | source_module=`safety.jha` · assignee_role=`safety` | mismatch | Path C |
| Dashboard | Safety Hub bell + `/admin/jha/<id>` | Visible | Not visible |

### 2.7 · OMEGA-8 / Safety Meeting

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | POST canary safety meeting | HTTP 200 + row in `meetings` | Rejected |
| DB delta | tasks +1 · notifications +2 | Wrong | Path C |
| Notification fields | type=`meeting.submitted` · recipient_role=`safety` | mismatch | Path C |
| Task fields | source_module=`safety.meeting` · assignee_role=`safety` | mismatch | Path C |
| Dashboard | Safety Hub bell + `/admin/meetings/<id>` | Visible | Not visible |

### 2.8 · OMEGA-13 / Payroll Variance Manual Run

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | Operator POSTs canary payroll variance manual run | HTTP 200 + row in `payroll_variance_batches` | Rejected |
| DB delta | tasks +0 (notification only) · notifications +1 | Wrong | Path C |
| Notification fields | type=`payroll_variance.manual_run` · recipient_role=`admin` · severity=`Info` | mismatch | Path C |
| Dashboard | Admin Hub bell + `/admin/audit-log` cross-reference | Visible | Not visible |

### 2.9 · Wave 1 Substrate

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Health | `/api/health` | 200 ok=true | non-200 |
| Runtime | `GET /api/operational/timeline/...` (read-only endpoint per Wave 1 doctrine) | 200 OK + empty array (no data yet on prod) | non-200 |
| Database | `db.operational_*.estimated_document_count()` | All 5 collections exist with 0 docs | Collections missing |
| Frontend | Open a PM Project Detail page | Sidecar renders as passive read-only rail on right side | Sidecar absent OR breaks page layout |

### 2.10 · Multi-Login Reseed (Item 5)

**Validation does NOT require a real restore on prod.** Validate via:

| Dimension | Probe | PASS criterion | FAIL criterion |
|---|---|---|---|
| Runtime | `git diff` of `server.py:7592-7635` matches preview | Diff matches MULTI_LOGIN_RESEED_REPORT.md §1.1 | Diff differs |
| Drill-side | Operator runs `restore_drill.py --backup <archive> --target-db drill_db --seed-user-passwords` against an archive on a side DB | Returns `seeded=N · skipped=0` | Error or 0 seeded |
| Login probes | Hit drill-backend login with `Welcome2MASCI!` for each of 7 master-directory users | All 7 return OK with portal_tokens | Any failure |

---

## 3 · Aggregate validation summary table (PASS/FAIL gates)

| # | Improvement | Gate count | Critical gate (deploy-stopper) |
|---|---|---:|---|
| 1 | Core platform health | 3 | `/api/version.source_hash` mismatch ⇒ Path C |
| 2 | OMEGA-1 / Photo migration | 5 | `Photos to migrate: 0` on dry-run-after-apply |
| 3 | OMEGA-2 / Batch H write-path | 4 | Canary DR's photos[0] starts with `photo://` |
| 4 | OMEGA-3 / Fleet DVIR (Case A) | 7 | Normal DVIR emits 0 fan-out rows |
| 5 | OMEGA-3 / Fleet DVIR (Case B) | 7 | Defect emits Shop Medium task + dvir.defect notification |
| 6 | OMEGA-3 / Fleet DVIR (Case C) | 7 | OOS emits Shop Critical task + DUAL notifications (shop + dispatch) |
| 7 | OMEGA-5 / FL forms | 7 | `assignee_role=safety` on emitted task |
| 8 | OMEGA-6 / Issuance | 5 | type=`safety_form.issuance` notification fires |
| 9 | OMEGA-6 / Return | 4 | Notification-only (no task) |
| 10 | OMEGA-6 / Training | 5 | type=`safety_form.training` notification fires |
| 11 | OMEGA-7 / JHA | 5 | `source_module=safety.jha` task fires |
| 12 | OMEGA-8 / Meeting | 5 | `source_module=safety.meeting` task fires |
| 13 | OMEGA-13 / Payroll variance | 4 | Admin notification only (no task) |
| 14 | Wave 1 substrate | 4 | Sidecar renders on PM Project Detail |
| 15 | Multi-login reseed | 3 | Drill-side 7/7 multi-login passes |

**Total gates: 75.** All gates must PASS for deploy to be declared SUCCESSFUL. Any single FAIL triggers the corresponding rollback path documented in `ROLLBACK_CERTIFICATION.md`.

---

## 4 · Time budget for validation

| Phase | Duration |
|---|---|
| Core platform health (3 gates) | 2 min |
| OMEGA improvements canary submissions (Items 1–13 above) | 20 min (one submission per workflow + DB enumeration per workflow) |
| Photo migration dry-run-after-apply | 3 min |
| Wave 1 sidecar render check | 1 min |
| Multi-login drill verification (optional, side DB only) | 5 min |
| Long-tail observation (next backup archive size drop) | ~3 hr (next scheduler tick) |
| **Total active validation window** | **~35 min** |

---

## 5 · Stop-condition compliance

- ✅ No probes executed during this audit
- ✅ Plan only · operator-supervised execution
- ✅ Every gate has explicit PASS/FAIL criterion
- ✅ Every FAIL has a corresponding rollback path
- ✅ Total gate count (75) maps 1:1 to operator-visible runtime evidence

---

_End of POST_DEPLOY_VALIDATION_MATRIX.md._
