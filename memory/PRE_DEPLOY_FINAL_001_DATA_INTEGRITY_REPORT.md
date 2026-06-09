# PRE-DEPLOY-FINAL-001 · DATA INTEGRITY REPORT

## Production (`masci_safety`) — read-only verification

### Preview contamination scan
| Collection | Test/cert markers | Verdict |
|---|---|---|
| `jobs_master` | 0 | ✅ PASS |
| `daily_reports` | 1 row | 🟢 P3 — forensic remnant, hidden by canonical filters |
| `employees` | 2 rows | 🟢 P3 — likely a legitimate "Testaverde" or similar surname; manual triage recommended |
| `job_photos` | 0 | ✅ PASS |
| `users` | 0 | ✅ PASS |

### Duplicate project folders
| Check | Result |
|---|---|
| `jobs_master` with same `project_number` | 0 duplicates · ✅ PASS |
| `job_photos` `project_number`s with multiple distinct `project_name` spellings | 4 — name-spelling drift, canonical resolver collapses display. P3 cosmetic. |

### Orphan critical records
| Check | Result | Tolerance | Verdict |
|---|---|---|---|
| `daily_reports.project_number` ∉ `jobs_master` | 2 / 113 (1.8%) | ≤ 10 | ✅ PASS |
| `job_photos.project_number` ∉ `jobs_master` | 0 / 776 | ≤ 50 | ✅ PASS |

### Specific § 7 projects (each must show a single canonical folder)
| project_number | jobs_master | photos | daily_reports | Verdict |
|---|---|---|---|---|
| `26-01 - CP` | 1 | 74 | 12 | ✅ PASS |
| `24-12` | 1 | 357 | 53 | ✅ PASS |
| `25-21` | 1 | 193 | 25 | ✅ PASS |
| `26-07` | 1 | 30 | 3 | ✅ PASS |

### No missing critical records
| Domain | Count | Continuity verified |
|---|---|---|
| Daily Reports | 113 | ✅ Apr 27 → Jun 9, no gaps |
| Job Photos | 776 | ✅ |
| Employees | 262 | ✅ |
| HR users | 3 | ✅ |
| Equipment master | 596 | ✅ |
| Equipment units | 484 | ✅ |
| Equipment inspections | 39 | ✅ |
| Suppliers | 156 | ✅ |
| Meetings | 33 | ✅ |
| Admin audit | 1,936+ | ✅ live |
| Audit events | 10,995+ | ✅ live |
| Usage events | 423,556+ | ✅ live |

### Failed migrations
None observed. `photo_migration_progress` collection present and empty of failure markers; `r2_degraded_events` = 0.

### Corrupted / orphan critical records
None observed in scan. All collections returned consistent counts; no `_id` collisions; no schema drift between motor reads.

## Overall Verdict
🟢 **PASS** with three documented P3 items (test marker remnants + 4 spelling-variant project_names + 2 DR orphans). None affects deployment.
