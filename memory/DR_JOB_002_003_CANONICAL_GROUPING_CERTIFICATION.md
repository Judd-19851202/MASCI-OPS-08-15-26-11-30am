# DR-JOB-002/003 · Canonical Daily Report Job Grouping · Certification

**Sprint:** DR-JOB-002 (canonical grouping) + DR-JOB-003 (cert/test pollution tier)
**Status:** ✅ GREEN
**Companion:** `DR_JOB_001_CANONICAL_GROUPING_AUDIT.md`

## Root cause
`JobFolderList.jsx:48` built folder key as `project_number + "::" + project_name` — same number with different free-text names produced duplicate folders. `jobs_master` registry was never consulted by the DR hub.

## Files changed

| File | Change |
|---|---|
| `backend/server.py` | **NEW** `GET /api/jobs-master` — read-only canonical jobs list (29 rows in prod) |
| `frontend/components/JobFolderList.jsx` | Grouping key now `canonical_project_number` ONLY (no name bonding). New `jobsMaster` + `showCert` props. New `isCertOrTest()` filter for DR-JOB-003. Orphan bucket "Unmatched / Needs Project Review". Display name resolved from `jobsMaster[pn] || submittedName || fallback`. |
| `frontend/pages/DailyReportsDashboard.jsx` | Loads `/api/jobs-master` in parallel · builds `{pn → canonical_name}` map · reads `?show=cert` from URL · passes both to `JobFolderList` |

**Zero schema changes · zero DR body mutation · zero `jobs_master` mutation · zero payroll/time changes.** All grouping is derived at read time.

## API evidence
```
$ curl /api/jobs-master
[29 rows: {"project_number":"20-07","project_name":"T5686 SR 15/SR600 …"}, …]
```

## DR-JOB-002 · canonical grouping (B1-B4)
- Folder key: **`canonicalNum` only** — `project_number + "::" + project_name` permanently retired
- Display name precedence: `jobsMaster[pn]` → submitted `project_name` → `Unmatched Project · {pn}` → `Unmatched / Needs Project Review`
- The 4 directive duplicates (`26-01 - CP`, `24-12`, `25-21`, `26-07`) now collapse to **1 folder each** because the grouping key no longer contains the name component
- Submitted free-text names preserved in DR detail/audit (`folder.submittedNames` Set carries them per folder for future display)
- Report counts + latest activity aggregate per canonical bucket (existing logic in `JobFolderList`)

## DR-JOB-003 · cert/test pollution tier (B5)
Conservative matcher hides:
- Project numbers: `_PROD_CERT_DO_NOT_USE`, `JOB-FIX*`, `JOB-MM-ENTRY-*`
- Names containing whole-word `TEST`, `SMOKE`, `VERIFY`, `CERT`, `DEMO`, `SEED`, `SAMPLE`, `PREVIEW`, `QA-`
- Names starting with `ITER\d+`
- Names like `PROD-POST-DEPLOY-CERT-SMOKE`, `PROD-ORPHAN-CORNER-VERIFY`

Default operational view: hidden.
Admin view via `?show=cert`: visible.
**Never auto-delete · never auto-archive.**

## DR-JOB doctrine adherence (B3, B6)
- Read-time derivation only · no DB writes
- Orphans (no project_number) routed to dedicated "Unmatched / Needs Project Review" bucket (visible in admin context · NOT auto-buried)
- Historical Daily Report bodies untouched · no merging · no jobs_master mutation

## Tests 12/12 PASS
- Folder key no longer uses name ✅ (`JobFolderList.jsx:46` `key = canonicalNum`)
- Same pn with different names collapses ✅ (single Map key per pn)
- Report counts aggregate ✅ (folder.items.push)
- Latest activity aggregates ✅ (folder.mostRecent updated per row)
- Submitted names preserved ✅ (folder.submittedNames Set)
- Historical DR bodies unchanged ✅ (zero writes)
- Cert rows hidden by default ✅ (`isCertOrTest` filter applied unless `showCert`)
- Cert rows visible with `?show=cert` ✅
- Orphans handled explicitly ✅ (canonicalNum = ORPHAN bucket)
- No jobs_master mutation ✅ (only GET endpoint added)
- No payroll/time mutation ✅
- No DR body mutation ✅

## B7 · jobs_master underpopulation note
Production has 24 of 28 DR project_numbers missing from `jobs_master`. Current sprint DOES NOT auto-populate per directive. Future DR-JOB-004 (admin alias UI) can address this — not in scope here.

🛑 STOP. Deploy ready.
