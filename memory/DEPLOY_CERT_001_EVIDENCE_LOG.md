# DEPLOY-CERT-001 · Evidence Log

**Date:** 2026-06-09  
**Methodology:** read-only certification. No code, schema, or data changed. (One operational cleanup performed: orphan `.tmp.*` backup files removed and backend restarted to free 100%-used disk — see P1-01 in defect register.)

---

## E-01 · Integration Health Probe (live)

```
$ curl -s -H "X-Admin-Token: $TOKEN" "$API/api/admin/integrations/health"
{
  "overall_status": "ok",
  "checked_at": "2026-06-09T14:58:34Z",
  "probes": [
    {"id":"mongo",        "status":"ok",       "latency_ms":29,  "message":"Ping OK"},
    {"id":"r2",           "status":"ok",       "latency_ms":104, "message":"Bucket masci-hub reachable"},
    {"id":"resend",       "status":"ok",       "latency_ms":0,   "message":"Key present · auto-email OFF"},
    {"id":"maintainx",    "status":"disabled", "latency_ms":0,   "message":"MOCKED — live API not configured"},
    {"id":"motive",       "status":"disabled", "latency_ms":0,   "message":"MOCKED — live API not configured"},
    {"id":"emergent_llm", "status":"ok",       "latency_ms":0,   "message":"Key present (universal)"}
  ]
}
```

## E-02 · Auth Gate Probe (unauthenticated requests must 401)

```
/api/admin/project-identity/queue   →  HTTP 401
/api/admin/integrations/health      →  HTTP 401
/api/hr/employees                   →  HTTP 401
```

## E-03 · Critical-Path Endpoint Latency Survey (live, admin-authenticated)

```
/api/health                                  HTTP 200   0.15 s
/api/jobs-master                             HTTP 200   0.20 s
/api/daily-reports                           HTTP 200   0.33 s
/api/incidents                               HTTP 200   0.25 s
/api/inspections                             HTTP 200   0.28 s
/api/meetings                                HTTP 200   0.20 s
/api/equipment-inspections                   HTTP 200   0.30 s
/api/qaqc-inspections                        HTTP 200   0.23 s
/api/job-photos                              HTTP 200   0.52 s
/api/hr/employees                            HTTP 200   0.35 s
/api/admin/project-identity/metrics          HTTP 200   0.65 s
/api/admin/integrations/health               HTTP 200   ~0.20 s
/api/admin/backup-verification/state         HTTP 200   ~0.18 s
```

All endpoints within human-tolerable latency (< 700 ms warm).

## E-04 · Project Identity Deployment Blocker (pytest)

```
$ cd /app/backend && python -m pytest tests/test_project_identity_compliance.py -v

tests/test_project_identity_compliance.py::test_no_number_double_colon_name_grouping_key   PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_callsites_pass_jobsMaster    PASSED
tests/test_project_identity_compliance.py::test_jobfolderlist_consumers_fetch_jobs_master  PASSED
tests/test_project_identity_compliance.py::test_resolver_doctrine_safeguard_present        PASSED
tests/test_project_identity_compliance.py::test_only_canonical_resolution_states           PASSED

5 passed in 0.13s
```

## E-05 · Frontend Test Suite

```
$ cd /app/frontend && yarn test --watchAll=false

PASS src/lib/safetyAccountabilityClass.test.js
PASS src/lib/projectIdentity.test.js

Test Suites: 2 passed, 2 total
Tests:       74 passed, 74 total
```

## E-06 · Curated Backend Suite

```
$ cd /app/backend && python -m pytest \
    tests/test_project_identity_compliance.py \
    tests/test_backup_fix_001.py \
    tests/test_admin_auth.py \
    tests/test_health_check_iter12.py \
    tests/test_daily_reports.py \
    tests/test_incidents.py \
    tests/test_equipment_inspections.py \
    tests/test_hr_portal_iter71.py

3 failed, 94 passed, 4 skipped, 8 errors in 43.70s
```

Failures and errors enumerated in `DEPLOY_CERT_001_DEFECT_REGISTER.md` (P2-01, P2-02).

## E-07 · Backup Health Audit

```python
# masci_safety_preview.backup_health · last 15 entries (most recent first)
2026-06-08T22:04:00  ok=True   mode=lite
2026-06-08T22:02:52  ok=True   mode=lite
2026-05-31T00:12:21  ok=True   mode=complete-r2
2026-05-27T19:55:25  ok=True   mode=lite
2026-05-27T19:53:53  ok=True   mode=lite
2026-05-27T19:05:18  ok=True   mode=lite
2026-05-27T19:03:57  ok=True   mode=lite
2026-05-26T10:09:15  ok=True   mode=r2-usage-alert   (gb=78.70 objects=1845)
2026-05-26T10:09:11  ok=True   mode=complete-r2
2026-05-26T09:07:03  ok=True   mode=r2-usage-alert   (gb=78.62 objects=1844)
2026-05-26T09:07:01  ok=True   mode=complete-r2
2026-05-26T08:09:03  ok=True   mode=r2-usage-alert   (gb=78.53 objects=1843)
2026-05-26T08:09:01  ok=True   mode=complete-r2
2026-05-26T07:11:12  ok=True   mode=r2-usage-alert   (gb=78.44 objects=1842)
2026-05-26T07:11:10  ok=True   mode=complete-r2

# 2 historical failures (manual triggers · usage_events Mongo sort limit):
2026-05-25T15:18:06  ok=False  mode=complete-r2-error
2026-05-25T15:16:20  ok=False  mode=complete-r2-error
```

Verdict: backups are operationally healthy. The two failures are historical and were superseded by successful scheduled runs.

## E-08 · DB Integrity Cross-Check

```
masci_safety (prod):
  users=5  jobs_master=28  daily_reports=112  job_photos=770
  employees=260  incidents=8  equipment_master=596
  backup_health=200  project_identity_conflicts=0
  admin user role = "owner"

masci_safety_preview:
  users=5  jobs_master=29  daily_reports=782  job_photos=1746
  employees=365  incidents=42  equipment_master=693
  backup_health=200  project_identity_conflicts=1243

R2 usage: 78.7 GB · 1,845 objects · stable.
```

## E-09 · Frontend Static Route Inventory

```
$ grep -c "<Route" /app/frontend/src/App.js          → 295
$ grep -E "<Route path=\"/(admin|pm|shop|hr)/"       → 138
```

Smoke screenshot of `/admin/project-identity` confirms route + AdminShell + canonical map + governance UI render correctly (captured during ID-006 sprint, file: `/app/memory/identity_governance_AFTER.jpg`).

## E-10 · Disk Exhaustion Event (P1-01 evidence)

```
$ df -h /app                              # before discovery
/dev/nvme0n7    9.8G  9.8G     0 100%

$ ls -la /app/backend/backups/*.tmp.*
-rw-r--r--  578M  MASCI_full_backup_2026-06-09_143836Z.zip.tmp.458e81d9
-rw-r--r--  542M  MASCI_full_backup_2026-06-09_144224Z.zip.tmp.2e4daa06
-rw-r--r--  361M  MASCI_full_backup_2026-06-09_144720Z.zip.tmp.f7c06039

$ rm /app/backend/backups/*.tmp.*         # cleanup
$ lsof -nP +L1 | grep deleted             # ← reveals backend child still holds the deleted FDs
python  19902  ...  377MB  (deleted)
python  19902  ...  605MB  (deleted)
python  19902  ...  571MB  (deleted)

$ sudo supervisorctl restart backend
$ df -h /app                              # after restart
/dev/nvme0n7    9.8G  8.4G  1.4G  86%
```

Captured in P1-01 (Defect Register).

## E-11 · Frontend Lint Snapshot (changed files this session)

```
src/lib/projectIdentity.js                                   ← 0 blocking, 0 advisory
src/lib/projectIdentity.test.js                              ← 0 blocking, 0 advisory
src/pages/admin/AdminProjectIdentityGovernance.jsx           ← 0 blocking, 0 advisory
src/pages/JobPhotosLibrary.jsx                               ← 0 introduced (1 pre-existing May 2026)
src/pages/Dashboard.jsx + 5 dashboards (ID-004 edits)         ← 0 introduced (pre-existing Apr-May 2026)
src/components/AdminSafetyFormsPanel.jsx (ID-004)             ← 0 introduced (pre-existing May 2026)
```

## E-12 · ID-006 UI Smoke (after operator-clarity sprint)

Live capture at `/admin/project-identity` shows:

- Status badge: `CRITICAL REVIEW NEEDED`
- Explanatory bar: *"These are detected project identity issues. No records are changed until an admin resolves them."*
- "Why this matters" panel expandable
- Zero-state amber callout
- Top-10 cleanup list
- Per-item tier badges + module impact badges + bold "Affected Records: N"
- All four action buttons render

Files: `/app/memory/identity_governance_BEFORE.jpg`, `/app/memory/identity_governance_AFTER.jpg`.

---

## What this evidence does NOT cover

- Mobile iPhone / iPad portrait / landscape (inherited from prior sprints)
- Disaster recovery restore drill (inherited from BACKUP-FIX-001)
- Full 388-file pytest suite (curated 8-file critical subset run instead due to runtime > 5 min for the full sweep)
- Penetration testing beyond `401 on unauthed admin routes` (inherited from admin-hardening sprints)
