# COLLECTION_CLASSIFICATION_REPORT

**Date:** 2026-05-30 (Batch F · Phase 3 — addendum)
**Method:** Static analysis + Mongo `collStats` cross-reference. Every collection in the prod DB classified A–H.

---

## 1 · Classification taxonomy (per directive)

| Code | Category | Inclusion in DR backup? |
|---|---|---|
| A | Operational Business Data | 🟢 MUST be included |
| B | Compliance Data | 🟢 MUST be included |
| C | Audit Data | 🟢 SHOULD be included (legal evidence) |
| D | Telemetry | 🟡 OPTIONAL · usage analytics, not recovery-critical |
| E | Logs | 🔴 SHOULD NOT be included · re-creatable |
| F | Cache | 🔴 MUST NOT be included · derived from source |
| G | Derived Data | 🔴 MUST NOT be included · re-computable |
| H | Temporary Data | 🔴 MUST NOT be included · TTL-bound |

---

## 2 · Classification of all 76 data-bearing collections

| Collection | Class | docs | size_MB | Rationale | In archive? |
|---|---|---:|---:|---|---|
| daily_reports | **A** | 86 | 260.69 | Core operational submission | 🟢 keep |
| incidents | **A** | 7 | 15.42 | Core operational | 🟢 keep |
| equipment_inspections | **A** | 25 | 1.06 | Pre-op DVIRs | 🟢 keep |
| meetings | **A** | 23 | 11.54 | Safety meetings | 🟢 keep |
| jhas | **A** | 0 | — | Job hazard analyses | 🟢 keep |
| inspections | **A** | 0 | — | Site inspections | 🟢 keep |
| qaqc_inspections | **A** | 0 | — | QAQC | 🟢 keep |
| po_requests | **A** | 1 | 0.34 | Procurement | 🟢 keep |
| fleet_status / fleet_defects | **A** | 0 | — | Fleet | 🟢 keep |
| operations_events | **A** | 534 | 0.41 | Ops state machine | 🟢 keep |
| time_off_public_links | **A** | 0 | — | HR ops | 🟢 keep |
| safety_documents | **B** | 6 | <0.01 | Compliance evidence | 🟢 keep |
| safety_training_records | **B** | 4 | <0.01 | Compliance | 🟢 keep |
| compliance_findings | **B** | 233 | 0.14 | Compliance | 🟢 keep |
| document_expirations | **B** | 1 | <0.01 | Compliance dates | 🟢 keep |
| driver_qualification_imports | **B** | 81 | <0.01 | DOT compliance | 🟢 keep |
| training_hits | **B** | 1 177 | 0.11 | Training delivery | 🟢 keep |
| job_hazard_files | **B** | 6 | 15.18 | Safety reference | 🟢 keep |
| users | **A** | 5 | <0.01 | Auth (general) | 🟢 keep |
| user_directory | **A** | 7 | <0.01 | Auth (master) | 🟢 keep |
| project_managers | **A** | 8 | <0.01 | Auth (PM portal) | 🟢 keep |
| shop_users | **A** | 2 | <0.01 | Auth (Shop) | 🟢 keep |
| hr_users | **A** | 3 | <0.01 | Auth (HR) | 🟢 keep |
| dispatch_users | **A** | 2 | <0.01 | Auth (Dispatch) | 🟢 keep |
| safety_users | **A** | 2 | <0.01 | Auth (Safety) | 🟢 keep |
| field_leadership_users | **A** | 27 | <0.01 | Auth (FL) | 🟢 keep |
| employees | **A** | 245 | 0.09 | Workforce | 🟢 keep |
| equipment_master | **A** | 589 | 0.21 | Asset registry | 🟢 keep |
| equipment_units | **A** | 484 | 0.12 | Asset registry | 🟢 keep |
| audit_events | **C** | 10 032 | 2.24 | Generic audit ledger | 🟢 keep |
| admin_audit | **C** | 1 883 | 0.73 | Admin actions | 🟢 keep |
| admin_audit_log | **C** | 142 | 0.06 | Admin actions (legacy) | 🟢 keep |
| fleet_audit | **C** | 582 | 0.26 | Fleet audit | 🟢 keep |
| hub_banner_audit | **C** | 1 161 | 0.24 | Banner reads | 🟡 keep (low value) |
| compliance_events | **C** | 0 | — | | 🟢 keep |
| usage_events | **D** | 241 446 | 38.10 | Click telemetry | 🟡 split off |
| health_monitor_runs | **D** | 16 908 | 1.89 | Self-monitoring | 🟡 split off |
| draft_telemetry | **D** | 1 638 | 0.53 | UX draft autosave probes | 🟡 split off |
| backup_health | **D** | 200 | <0.01 | Self-monitoring | 🟡 split off (recovery-irrelevant) |
| cluster_capacity_history | **D** | 102 | <0.01 | Self-monitoring | 🟡 split off |
| session_activity | **D** | 1 052 | 0.34 | Session telemetry | 🟡 split off |
| directory_sessions | **D**+ | 1 901 | 0.44 | Auth session tokens | 🟡 short TTL; split off |
| job_photos | **A** | 598 | 0.22 | Photo metadata (NOT bytes) | 🟢 keep |
| job_photo_thumb_cache | **F** | 1 791 | 24.17 | Thumb-cache derived | 🔴 EXCLUDE |
| signatures | **F** | 0 | — | Cached rendered signatures | 🔴 EXCLUDE |
| events | **E** | 0 | — | App-wide event stream | 🔴 EXCLUDE |
| system_health_events | **E** | 0 | — | Health probe outputs | 🔴 EXCLUDE |
| r2_degraded_events | **E** | 0 | — | R2-availability logs | 🔴 EXCLUDE |
| integration_error_logs | **E** | 0 | — | Integration errors | 🔴 EXCLUDE |
| login_attempts | **E** | 0 | — | Login attempt log | 🔴 EXCLUDE (security keeps in audit_events instead) |
| brute_force_blocks | **E** | 0 | — | Lockout state | 🔴 EXCLUDE (re-form on demand) |
| mfa_audit_events | **C** | 0 | — | MFA audit | 🟢 keep |
| temp_upload_chunks | **H** | 0 | — | In-flight chunked uploads | 🔴 EXCLUDE |
| webauthn_challenges | **H** | 0 | — | 5-min challenge nonces | 🔴 EXCLUDE (TTL-bound) |
| admin_step_ups | **H** | 0 | — | Step-up auth state | 🔴 EXCLUDE |
| idempotency_keys | **H** | 23 | 0.53 | Idempotency cache | 🔴 EXCLUDE (TTL) |
| scheduler_locks | **H** | 5 | <0.01 | Distributed lock state | 🔴 EXCLUDE |
| dispatch_continuity_events | **C** | 0 | — | Dispatch resume | 🟢 keep |
| dispatch_magic_links | **H** | 0 | — | Single-use links | 🔴 EXCLUDE |
| dispatch_driver_sessions | **D**+ | 0 | — | Session tokens | 🟡 split off |
| legacy_imports | **A** | varies | — | Legacy data | 🟢 keep |
| odr (+ subcolls) | **A**/**B** | 0 | — | ODR module | 🟢 keep |
| projects, project_members, jobs_master | **A** | varies | — | Project / job registry | 🟢 keep |
| activity_log, login_attempts | **E** | 0 | — | Logs | 🔴 EXCLUDE |
| messages | **A** | 0 | — | App messages | 🟢 keep |
| todo_lists, todos | **A** | 0 | — | Task tracking | 🟢 keep |
| trench_boxes | **A** | 0 | — | Equipment subcategory | 🟢 keep |
| (remaining ~30 zero-document collections) | various | 0 | — | (auto-create on first write) | n/a |

---

## 3 · Top 20 largest collections (data-bearing)

| Rank | Collection | size_MB | Class | Keep in DR backup? |
|---:|---|---:|---|---|
| 1 | daily_reports | 260.69 | A | 🟢 KEEP |
| 2 | usage_events | 38.10 | D | 🟡 SPLIT to telemetry archive |
| 3 | job_photo_thumb_cache | 24.17 | F | 🔴 EXCLUDE (derived cache) |
| 4 | incidents | 15.42 | A | 🟢 KEEP |
| 5 | job_hazard_files | 15.18 | B | 🟢 KEEP |
| 6 | meetings | 11.54 | A | 🟢 KEEP |
| 7 | audit_events | 2.24 | C | 🟢 KEEP |
| 8 | health_monitor_runs | 1.89 | D | 🟡 SPLIT |
| 9 | equipment_inspections | 1.06 | A | 🟢 KEEP |
| 10 | admin_audit | 0.73 | C | 🟢 KEEP |
| 11 | draft_telemetry | 0.53 | D | 🟡 SPLIT |
| 12 | idempotency_keys | 0.53 | H | 🔴 EXCLUDE (TTL) |
| 13 | directory_sessions | 0.44 | D | 🟡 SPLIT (short TTL anyway) |
| 14 | operations_events | 0.41 | A | 🟢 KEEP |
| 15 | po_requests | 0.34 | A | 🟢 KEEP |
| 16 | session_activity | 0.34 | D | 🟡 SPLIT |
| 17 | fleet_audit | 0.26 | C | 🟢 KEEP |
| 18 | hub_banner_audit | 0.24 | C | 🟡 KEEP (low value, but tiny) |
| 19 | job_photos | 0.22 | A | 🟢 KEEP |
| 20 | equipment_master | 0.21 | A | 🟢 KEEP |

---

## 4 · Top 20 fastest-growing collections (estimated rate/day)

| Rank | Collection | Est rate/day | Class | Action |
|---:|---|---:|---|---|
| 1 | usage_events | ~1 500 | D | 🟡 TTL 180-day |
| 2 | health_monitor_runs | ~250 | D | 🟡 TTL 30-day |
| 3 | audit_events | ~150 | C | 🟡 TTL 365-day (legal retention) |
| 4 | directory_sessions | ~100 | D | 🔴 Already short TTL — keep |
| 5 | session_activity | ~50 | D | 🟡 TTL 30-day |
| 6 | admin_audit | ~30 | C | 🟢 KEEP (legal) |
| 7 | hub_banner_audit | ~20 | C | 🟡 TTL 90-day |
| 8 | draft_telemetry | ~30 | D | 🟡 TTL 7-day |
| 9 | training_hits | ~25 | B | 🟢 KEEP |
| 10 | fleet_audit | ~15 | C | 🟢 KEEP |
| 11 | daily_reports | ~3 | A | 🟢 KEEP (but address size — see Phase 4) |
| 12 | operations_events | ~10 | A | 🟢 KEEP |
| 13 | health_monitor_runs (already counted) | — | — | — |
| 14 | equipment_inspections | ~1 | A | 🟢 KEEP |
| 15 | meetings | ~1 | A | 🟢 KEEP |
| 16 | incidents | <0.5 | A | 🟢 KEEP |
| 17 | po_requests | <0.1 | A | 🟢 KEEP |
| 18 | compliance_findings | varies | B | 🟢 KEEP |
| 19 | job_photos | varies | A | 🟢 KEEP |
| 20 | driver_qualification_imports | low | B | 🟢 KEEP |

(Rate confidence limited — see growth forensics §5. Numbers are estimates not direct probes.)

---

## 5 · "Should not be in DR backups" — explicit list

| Collection | Class | Why not |
|---|---|---|
| job_photo_thumb_cache | F | Derived from source images on R2; re-form on demand |
| signatures | F | Cached rendered signature images; re-form from source |
| temp_upload_chunks | H | In-flight uploads · TTL minutes |
| webauthn_challenges | H | 5-minute nonces |
| admin_step_ups | H | Short-lived authentication tokens |
| idempotency_keys | H | Short-lived dedup state |
| scheduler_locks | H | Distributed lock state · should reset on restore |
| dispatch_magic_links | H | Single-use ≤ 24h links |
| events / system_health_events / r2_degraded_events / integration_error_logs / activity_log / login_attempts / brute_force_blocks | E | Logs — re-create on demand · keep last 30 days in production but exclude from DR archive |

Total excludable size: ~25 MB (the thumb cache is the dominant excludable item).

---

## 6 · "Should be split off into a telemetry archive" — explicit list

| Collection | Class | Size/MB | Reason |
|---|---|---:|---|
| usage_events | D | 38.10 | Click telemetry |
| health_monitor_runs | D | 1.89 | Self-monitoring |
| draft_telemetry | D | 0.53 | Autosave probes |
| backup_health | D | <0.01 | Backup self-records |
| cluster_capacity_history | D | <0.01 | Capacity sampler |
| session_activity | D | 0.34 | Session telemetry |

Total split-off potential: ~41 MB → would drop the recovery archive from 442 MB to ~400 MB (modest gain).

---

## 7 · Net classification result

| Bucket | Collections | Total MB | Action |
|---|---:|---:|---|
| A (Operational) | ~30 | 290 MB | KEEP — primary recovery target |
| B (Compliance) | 8 | 15.5 MB | KEEP — legal retention |
| C (Audit) | 6 | 3.5 MB | KEEP — legal evidence |
| D (Telemetry) | 6 | 41 MB | SPLIT — separate telemetry archive |
| E (Logs) | 7+ | 0 today | EXCLUDE |
| F (Cache) | 2 | 24 MB | EXCLUDE |
| G (Derived) | 0 today | — | n/a |
| H (Temporary) | 7+ | 0.5 MB | EXCLUDE |

**If telemetry + cache + temp/log collections were excluded today**, archive size would drop from 442 MB to **~370 MB (-16%)**.

If `daily_reports` photo bloat (the dominant 260 MB) were ALSO moved to R2 references, archive would drop to **~110 MB (-75%)**. **This is where the structural fix lies.**
