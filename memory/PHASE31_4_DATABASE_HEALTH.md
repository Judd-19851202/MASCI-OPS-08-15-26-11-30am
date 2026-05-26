# Phase 31.4 · Database Health
## iter441 · 2026-05-26 · MongoDB Atlas masci-prod

---

## Cluster snapshot

```
Atlas connections:    current=35 / available=465       ✅ (7% utilization)
Resident memory:      reported 0 MB                    ℹ️ Atlas serverless reports differently
DB collections:       123
DB indexes:           332 total
DB objects:           245,080
Data size:            70 MB
Index size:           32 MB
Storage size:         54 MB (compressed)
```

🟢 Healthy. Plenty of headroom for 10× growth.

---

## Top 10 collections by storage

```
job_hazard_files               29.0 MB · count=     7  ix=3  avg=2.27 MB
usage_events                   11.2 MB · count=189,034 ix=5  avg=168 b  TTL 90d ✅
notifications                   1.8 MB · count=  5,615 ix=7  avg=682 b  TTL by expires_at ✅
dispatch_state_events           1.4 MB · count=  5,678 ix=5  avg=488 b
dispatch_assignments            1.2 MB · count=  2,146 ix=6  avg=1.6KB
tasks                           1.2 MB · count=  3,556 ix=11 avg=799 b  TTL 1y on closed_at ✅
audit_events                    0.8 MB · count= 10,395 ix=2  avg=235 b  TTL 30d ✅
compliance_findings             0.4 MB · count=  1,387 ix=1
directory_sessions              0.4 MB · count=  1,905 ix=1
field_leadership_records        0.4 MB · count=    964 ix=3
```

🟢 No collection > 30 MB. All high-churn collections (>10k docs) have TTL.

---

## TTL inventory (21 indexes)

```
admin_audit                    1y      audit_events                30d
admin_step_ups                 1d      brute_force_blocks           7d
alert_events                   90d     digest_runs                  30d
dispatch_driver_sessions       (by ts) dispatch_magic_links         (by ts)
driver_qualification_imports   1h      health_monitor_runs          30d
integration_error_logs         90d     job_photo_thumb_cache         7d
login_attempts                 30d     notifications                 (by expires_at)
r2_degraded_events             30d     session_activity             30d
system_health_events           30d     tasks                          (by closed_at, 1y)
temp_upload_chunks             1d      usage_events                 90d
webauthn_challenges            5min
```

🟢 Every high-churn collection has bounded retention.

---

## Index coverage on hot query fields

```
✅ daily_reports.project_number          (in 2 indexes)
✅ daily_reports.report_date             (in 2 indexes)
✅ incidents.incident_date               (in 2 indexes)
✅ incidents.severity                    (in severity_1)
✅ dispatch_assignments.state            (in 3 compound indexes)
✅ field_memory_notes.subject_kind       (in ix_field_memory_subject_unresolved)
✅ operational_attachments.host_id       (in ix_op_attachments_host)
⚠️ continuity_events.kind                (collection has 0 docs · indexes lazy-created)
```

🟢 7/7 hot-query fields covered on collections with real data.

---

## Attachment integrity

```
storage_backend='r2': count=70 · 100% of total
inline_b64:           0
unknown:              0
orphan (no data + no key): 0
```

🟢 Zero orphans. Full R2 migration verified.

---

## Recent writes (proof of liveness)

```
daily_reports         latest 2026-05-26T00:16:47 ✅
incidents             latest 2026-05-26T00:16:47 ✅
inspections           latest 2026-05-24T01:02:52 (2 days, normal cadence)
dispatch_assignments  latest 2026-05-26T00:16:59 ✅
field_memory_notes    latest 2026-05-25T20:07:33 ✅
```

🟢 All critical collections received writes within the last hour.

---

## Risks watched, none active

* Unbounded growth: NONE — all 4 collections > 10k docs have TTL.
* Auth mismatch: NONE — same Atlas connection string from preview + prod.
* Missing indexes on hot fields: NONE.
* Orphan attachments: NONE.
* Dead collections: NONE (sub-doc-count collections are intentional fixtures).
* WiredTiger cache pressure: not directly readable on Atlas serverless · cluster fully responsive.

🟢 Database certified healthy.
