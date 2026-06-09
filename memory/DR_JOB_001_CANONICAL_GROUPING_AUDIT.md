# DR-JOB-001 · Canonical Daily Report Job Grouping · Audit

**Sprint:** DR-JOB-001 (AUDIT ONLY — no code changes)
**Status:** ✅ COMPLETE — findings returned
**Date:** 2026-02-09
**Verdict for current behavior:** 🔴 **FAIL** — DR hub groups by free-text name, producing duplicate buckets for the same job number.

---

## 1. Root cause (single line)

`/app/frontend/src/components/JobFolderList.jsx` line 48 builds the grouping key as `project_number + "::" + project_name`. When the same project_number is submitted with different free-text `project_name` strings (typos, abbreviations, case variants, legacy names), each name produces a separate folder. **`jobs_master` exists as a canonical registry but is never consulted by the DR hub.**

---

## 2. Exact code path — what is being grouped today

| Layer | File · Function · Line | Fields used |
|---|---|---|
| Hub component | `pages/DailyReportsDashboard.jsx::DailyReportsDashboard` line 36 | Fetches `GET /api/daily-reports`, passes to `JobFolderList items={…}` |
| Grouping logic | `components/JobFolderList.jsx::folders` lines 43-85 | `key = (project_number || "—") + "::" + (project_name || "(No Job)")` |
| Sort | line 68-75 | Folders sorted by `mostRecent` activity DESC; ties alphabetised by `name` |
| Filter | line 88-95 | Search matches against `f.name` + `f.number` substring |
| Backend list | `server.py @ /api/daily-reports` | Returns raw `daily_reports` rows with their submitted `project_number` + `project_name` fields — no canonical join |
| Distinct-projects helper (exists but unused by hub) | `server.py::list_projects_in_dailies` lines 4055-4087 | `$group: { _id: "$project_number", project_name: { $last: … } }` — already buckets by number, but only feeds the admin P&L picker |

**No fallback to `jobs_master`. No alias map. No canonical projection.** The hub treats the submitter's free-text label as authoritative.

---

## 3. Canonical job source — what's available but unused

`/app/backend/jobs_master.py` defines `db.jobs_master` with:
- `project_number` (UNIQUE indexed) — canonical key
- `project_name` — canonical name as MASCI uses it ("CC5744 - OXFORD RD Improvements (OXFORD)", "NSB Corbin Park Stormwater Improvements", etc.)
- `status` field exists in schema but is empty on most production rows
- Seeded from `data/jobs_master.json` on first run

**Production state (live `masci_safety` DB):**
- `jobs_master`: **28 canonical rows**
- `daily_reports`: 112 rows
- DR project_numbers NOT in `jobs_master`: structural mismatch — see §5

---

## 4. Duplicate group matrix (LIVE PRODUCTION DB · `masci_safety`)

| Displayed Group Name | Project # | Reports (sampled) | Latest Activity | Likely Canonical Job (from jobs_master) | Confidence | Issue Type |
|---|---|---|---|---|---|---|
| `Corbin park` | `26-01 - CP` | (subset) | recent | `26-01 - CP · "NSB Corbin Park Stormwater Improvements"` ✅ in jobs_master? **NOT FOUND** — pn `26-01 - CP` not present in 28-row registry | 95% (same pn, same project) | **Case/abbrev mismatch** |
| `NSB Corbin Park Stormwater Improvements` | `26-01 - CP` | (subset) | recent | same as above | 95% | **Canonical-form duplicate** |
| `Oxford coping` | `24-12` | (subset) | recent | `24-12 · "CC5744 - OXFORD RD Improvements (OXFORD)"` ✅ **IN jobs_master** | 99% | **Abbreviation / partial name** |
| `CC5744 - OXFORD RD Improvements (OXFORD)` | `24-12` | (subset) | recent | same as above | 99% | **Already canonical** |
| `Loop trail` | `25-21` | (subset) | recent | `25-21 · "SJR2C - Loop Trail - Spruce Creek"` — pn `25-21` **NOT in jobs_master** | 95% | **Short-form name + missing registry row** |
| `SJR2C - Loop Trail - Spruce Creek` | `25-21` | (subset) | recent | same as above | 95% | **Long-form name + missing registry row** |
| `University high school` | `26-07` | (subset) | recent | `26-07 · "University High Parent Loop Ext"` — pn `26-07` **NOT in jobs_master** | 95% | **Free-text alias + missing registry row** |
| `University High Parent Loop Ext` | `26-07` | (subset) | recent | same as above | 95% | **Long-form name + missing registry row** |
| `PROD-POST-DEPLOY-CERT-SMOKE` | `_PROD_CERT_DO_NOT_USE` | 1 | — | (none — production-cert smoke) | n/a | **Test/cert pollution in prod** |
| `PROD-ORPHAN-CORNER-VERIFY` | (empty) | 1 | — | (none — orphan-verify probe) | n/a | **Test/cert pollution + missing pn** |

**Quantified pattern:**
- 4 production buckets in `masci_safety` have multiple name variants per project_number (Corbin Park, Oxford, Loop Trail, University HS)
- Each of these renders as **2 folders** in the current hub instead of 1
- **24 of 28 production project numbers in DR are NOT in `jobs_master`** — the canonical registry is severely under-populated relative to actual project activity

---

## 5. Test / certification pollution (NEVER auto-delete)

### Production DB — confirmed pollution rows

| Project # | Name | Classification | Recommended visibility |
|---|---|---|---|
| `_PROD_CERT_DO_NOT_USE` | `PROD-POST-DEPLOY-CERT-SMOKE` | Post-deploy smoke | **Hide from default hub** · keep in admin/audit |
| (empty) | `PROD-ORPHAN-CORNER-VERIFY` | Orphan-corner verify probe | **Hide from default hub** · keep in admin/audit |

### Preview DB — large pollution set (additional context, not for prod cleanup)

Preview DB carries **486 daily-report rows** matching test/cert/smoke patterns across:
- `TEST-452` (`iter452 DR test`) — 72 rows
- `TEST-4525` (`iter452.5 FSI DR test` · `iter452.5 legacy DR test` · `iter452.5.1 P0 smoke`) — 85 rows
- `JOB-FIX1-PYTEST` (`DR-FIX-1 · Pytest Project`) — 11 rows
- `0000-TEST` (`TEST_DocID Project` + 3 sequence variants) — 16 rows
- `TEST-25-23`, `TEST-J-1`, `TEST-79`, `QA-DR-001`, `DR-FIX3-*` — many more
- 47 rows with **empty project_number** (e.g., `iter452.5.1 ORPHAN corner`, `TEST_E2E_Project`, `M1 freeze test`, `x`)

**These are preview-only and not at risk** — but the production handling pattern (PROD-POST-DEPLOY-CERT-SMOKE) confirms test reports CAN leak into prod via deploy smoke tooling. The pattern matchers below must therefore also be applied to prod.

### Recommended classification matchers (visibility tier)

| Tier | Rule | Action |
|---|---|---|
| **HIDE from default hub** | `project_number` ∈ `{"_PROD_CERT_DO_NOT_USE", "JOB-FIX*", "JOB-MM-ENTRY-*"}` OR `project_name` matches `/^(TEST|PROD-|SEED|SMOKE|VERIFY|CERT|DEMO|SAMPLE|PREVIEW|QA-|iter\d+)/i` OR `/^.{0,2}$/` (length ≤ 2, e.g. `x`) | Hidden by default · accessible via `?show=cert` admin filter |
| **ARCHIVE** | Future explicit operator action | Keep in DB; render only in audit views |
| **DELETE** | Future explicit operator action — must be individually authorized | Never auto-deleted |
| **AUDIT-ONLY** | Anything not matching above | Visible in standard hub |

---

## 6. Recommended correction strategy (doctrine)

**Doctrine:** *Daily Reports keep their original submitted text as historical snapshot. The hub groups + displays by canonical job reference when available. Historical bodies are NEVER rewritten.*

### Field model (additive · no rewrites)

| Field | Source | Mutability | Notes |
|---|---|---|---|
| `project_number` (existing) | submitter | preserved | historical accuracy intact |
| `project_name` (existing) | submitter | preserved | historical accuracy intact |
| `canonical_project_number` (NEW · OPTIONAL · derived at read time) | `jobs_master` lookup | runtime-only | non-persistent; resolved by the DR list endpoint |
| `canonical_project_name` (NEW · OPTIONAL · derived at read time) | `jobs_master.project_name` | runtime-only | non-persistent |
| `submitted_project_label` | == existing `project_name` | preserved | shown in detail/audit only |
| `submitted_project_number` | == existing `project_number` | preserved | shown in detail/audit only |
| `jobs_master_id` (OPTIONAL · runtime) | `jobs_master._id` | runtime-only | derived join key |

**Critical:** the new canonical fields are **derived** — they are NOT written back into `daily_reports`. The list endpoint joins on read; the historical body stays frozen.

### Visibility tier

A new `visibility_tier` field is computed at read time (NOT persisted):
- `"operational"` (default) → shows in hub
- `"cert_or_test"` → hidden by default · `?show=cert` query parameter reveals
- `"orphan"` → no project_number AND name does not match operational pattern · shown in a dedicated "Unmapped" bucket

---

## 7. Proposed DR-JOB-002 build scope

**Sprint title:** DR-JOB-002 · Canonical Grouping Fix

**Changes (estimate):**

1. **Backend** — augment `GET /api/daily-reports` (or add a sibling `/api/daily-reports/by-canonical-project`) to:
   - Read all `daily_reports` (existing query)
   - Read full `jobs_master` set into an in-memory map (29-row max — cheap)
   - For each report, derive `canonical_project_number` (= `project_number` if in master, else `project_number` raw) + `canonical_project_name` (= `jobs_master.project_name` if found, else original `project_name`)
   - Attach a `visibility_tier` via the classification matcher in §5
   - **Do not write back**. Doctrine: historical body frozen.

2. **Frontend** — change `JobFolderList` grouping key from `project_number + "::" + project_name` to **`canonical_project_number`** (the project_number is the only canonical key — name follows). The displayed name uses `canonical_project_name`. Submitted alias is shown in the DR detail page only.

3. **Test surface** — `tests/test_dr_job_002_canonical_grouping.py` with at least:
   - Pre-fix snapshot: count of folders for `26-01 - CP` is 2 (Corbin park + canonical) → assert post-fix count = 1
   - Pre-fix folders for `24-12`, `25-21`, `26-07` each = 2 → assert post-fix = 1
   - Historical row preservation: original submitted name is still in the row body
   - Visibility-tier matcher does not bleed cert-tier rows into default list

**Estimated effort:** ~80 lines (60 backend / 20 frontend) · 1 new test file (≈ 120 lines).

---

## 8. Proposed DR-JOB-003 build scope

**Sprint title:** DR-JOB-003 · Test/Cert Pollution Cleanup (Visibility-Tier Application)

**Changes:**

1. Apply the `visibility_tier = "cert_or_test"` matcher from §5 to the same endpoint produced by DR-JOB-002.
2. Default DR hub query filters to `operational` tier.
3. Add an admin-only `?show=cert` query parameter that includes cert/test rows.
4. **Never auto-archive · never auto-delete.**

**Estimated effort:** ~20 backend lines · 0 frontend lines (default filter is server-side).

---

## 9. Proposed DR-JOB-004 build scope (CONDITIONAL · not required)

**Sprint title:** DR-JOB-004 · Admin Job-Alias Reconciliation Tool

**Required only if** the operator wants HR/Admin to:
- Manually map a free-text name to a canonical job for ambiguous cases the matcher can't resolve
- Pre-populate `jobs_master` from observed DR project_numbers that are NOT yet in the registry (currently 24/28 prod rows are missing)

**Changes:**

1. New admin endpoint `GET /api/admin/dr/unmapped-projects` → returns the union of DR `project_number`s not in `jobs_master`
2. New admin endpoint `POST /api/admin/jobs-master/upsert` → adds a row to `jobs_master`
3. New admin page `/admin/dr-job-aliases` → UI for the above
4. Approve-then-apply model: no auto-mapping

**Estimated effort:** ~150 lines total.

---

## 10. Risk assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Historical DR body mutation | **HIGH (if mishandled)** | Doctrine §6: canonical fields are derived at read time, never persisted. Existing fields stay frozen. |
| Auto-mapping of wrong aliases | MEDIUM | Matcher uses `project_number` as the canonical join key. Name string is only DISPLAY, never used to merge. |
| Hiding legitimate operational reports as test pollution | MEDIUM | Conservative matcher (§5): only fires on explicit `TEST_`, `PROD-`, `_PROD_CERT_`, etc. prefixes. Operator can audit via `?show=cert`. |
| Performance | LOW | `jobs_master` is 28-29 rows — in-memory dict lookup is O(1). |
| Breaking PMs' P&L view | LOW | `list_projects_in_dailies` (server.py:4055) already buckets by `project_number`; DR-JOB-002 doesn't touch it. |
| Restoreability after rollback | LOW | DR-JOB-002 is read-time-only — rolling back the deploy reverts the behaviour with no data residue. |

---

## 11. PASS / FAIL — current behavior

🔴 **FAIL.**

Current DR hub:
- Groups by `project_number + "::" + project_name` → produces duplicate folders for the same job (4 confirmed in production)
- Does not consult `jobs_master` even when a canonical name is available
- Surfaces cert/test rows (`PROD-POST-DEPLOY-CERT-SMOKE`, `PROD-ORPHAN-CORNER-VERIFY`) in the default operational list
- Has 24 production project_numbers that exist on DRs but have no `jobs_master` row — so even after the grouping fix, the hub will need to either tolerate "missing canonical" cases gracefully or fall back to the longest-observed name

**Recommendation:** authorize DR-JOB-002 (canonical grouping) + DR-JOB-003 (cert visibility tier) together as a single follow-on sprint. DR-JOB-004 (admin alias UI) is optional and can wait until operators report a concrete need.

---

## 12. Constitutional adherence (OMEGA)

| Forbidden | Enforcement |
|---|---|
| ❌ Delete Daily Reports | Audit only · zero writes |
| ❌ Rewrite historical Daily Reports | Doctrine §6 makes derived fields runtime-only |
| ❌ Merge records | Buckets are a UI concern, not a DB concern |
| ❌ Change payroll data | Out of scope |
| ❌ Change report contents | Doctrine §6 |
| ❌ Hide operational reports without audit path | `?show=cert` admin path always available |
| ❌ Auto-map uncertain aliases | Matcher uses project_number; never trusts name string for mapping |
| ❌ Mutate `jobs_master` | Audit only |
| ❌ Mutate dispatch | Out of scope |
| ❌ Start FleetWatcher / unrelated cleanup | None initiated |

🛑 **STOP CONDITION OBSERVED.** Audit complete · awaiting authorization for DR-JOB-002 (and optionally DR-JOB-003/004).
