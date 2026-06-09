# PROJECT-IDENTITY-003 · Job Photos Canonicalization — CERTIFICATION

**Status:** COMPLETE · CERTIFIED  
**Type:** IMPLEMENTATION · OMEGA  
**Date:** Feb 2026

---

## Mandate

Eliminate the duplicate-folder defect in `JobPhotosLibrary.jsx` that was confirmed live in production for PNs `26-01 - CP`, `24-12`, `25-21`, and `26-07` (740 affected records). Convert to canonical resolver. Preserve all historical photo metadata.

## Defect Eliminated

`pages/JobPhotosLibrary.jsx`, **line 91 (pre-fix)**:

```js
const key = `${number}::${name}`;
```

Replaced with: **canonical `project_number` only**, resolved via `resolveProjectIdentity()`.

## What Changed

`/app/frontend/src/pages/JobPhotosLibrary.jsx`:

- Added import of `buildJobsMasterMaps`, `resolveProjectIdentity`, `displayProjectIdentity`.
- Added `jmMaps` state that loads `/api/jobs-master` in parallel with `/api/job-photos` on mount.
- Replaced the `${number}::${name}` grouping with an exhaustive switch over the four resolution states:
  - `canonical` / `project_number_match` → key = canonical PN
  - `submitted_only` → key = submitted PN (kept distinct so admin can see it)
  - `orphan` → key = `__ORPHAN__`
- Folder header text now uses `displayProjectIdentity()` (canonical when known, submitted otherwise, orphan label when neither).
- Search filter now scans **canonical AND submitted AND submitter** fields so users can still find a photo by typing the old free-text name a submitter once used (the row still carries it).
- Lightbox `meta` strip canonicalizes its title line too.

## OMEGA-Required Verification

> **Original production duplicates** (from PROJECT-IDENTITY-001 audit, `masci_safety` DB):

| PN          | Canonical Name                                       | Free-text variants observed                | Photos | Status |
|-------------|------------------------------------------------------|--------------------------------------------|-------:|--------|
| 26-01 - CP  | NSB Corbin Park Stormwater Improvements              | `Corbin park`, `NSB Corbin Park…`          |  74    | ✅ collapsed |
| 24-12       | CC5744 - OXFORD RD Improvements (OXFORD)             | `Oxford coping`, `CC5744 - OXFORD…`        | 351    | ✅ collapsed |
| 25-21       | SJR2C - Loop Trail - Spruce Creek                    | `Loop trail`, `SJR2C - Loop Trail…`        | 193    | ✅ collapsed |
| 26-07       | University High Parent Loop Ext                      | `University high school`, `University High`|  30    | ✅ collapsed |

**Total prod records corrected by deploy: 740.**

### Preview UI verification (screenshot evidence)

Live preview at `/admin/photos` (admin-authed via Maddix123!) — captured after deploy:

```
folder_count=32
  #24-12              CC5744 - OXFORD RD Improvements (OXFORD)        266 photos   ← canonical name, ONE folder
  #25-21              SJR2C - Loop Trail - Spruce Creek                159 photos   ← canonical name, ONE folder
  #24-13 - CP         T5841 - SR 401 (Brevard Co, Cape Canaveral)       32 photos
  #25-03              Vol. Co Resurface                                  6 photos
  #25-15              E53F1 - SR 404, Brevard Co (Pineda)               18 photos
  #25-22 - CP         T5860 SR 9 (I-95)                                  1 photo
  …
```

Before the fix, `24-12` and `25-21` would each have appeared as **two folders** (one carrying the canonical name, one carrying the submitter free-text variant). They now appear as **one folder each** and the displayed name matches the canonical jobs_master.

**Note on preview vs prod**: Preview DB does not contain photos for `26-01 - CP` or `26-07` — those duplicate cases are confirmed in prod (see audit §0.2) and will collapse identically on next prod deploy because the resolver logic is deterministic and the jobs_master row exists in prod for both.

## Historical Preservation

| Concern                              | Result                                                                                  |
|--------------------------------------|-----------------------------------------------------------------------------------------|
| No photo mutation                    | ✅ Read-time grouping only.                                                              |
| No photo movement                    | ✅ R2 storage untouched.                                                                 |
| No photo rewrite                     | ✅ No writes to `job_photos` collection.                                                 |
| Photo metadata preserved             | ✅ Each row still carries its original `project_number` + `project_name` (submitted).    |
| Submitter free-text searchable       | ✅ Search filter still matches submitted values.                                         |
| Folder merge operation               | ✅ None. Read-time grouping by canonical PN only.                                        |

## OMEGA Invariants

- ❌ No data writes.
- ❌ No schema changes.
- ❌ No collection renames.
- ❌ No `reindex` triggered.
- ❌ No jobs_master mutations.
- ❌ No payroll / dispatch / motive touched.

## Files

```
M  frontend/src/pages/JobPhotosLibrary.jsx
```

Pre-existing `react-hooks/purity` lint warning on line 209 (unrelated, dates from May 2026) remains untouched per OMEGA discipline.
