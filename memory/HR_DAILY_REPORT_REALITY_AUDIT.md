# HR DAILY REPORT REALITY AUDIT · TRACK 15.13B

**Date**: 2026-02-15
**Scope**: every field on the HR Daily Report (list + detail) — source collection · source property · expected value · actual value before 15.13B · actual value after 15.13B.

---

## List endpoint · `GET /api/hr/daily-reports`

| Field | Source collection | Source property | Pre-15.13B (production) | Post-15.13B (preview-verified) |
| ----- | ----------------- | --------------- | ----------------------- | ------------------------------ |
| `id` | `daily_reports` | `id` | ✅ | ✅ |
| `project_name` | `daily_reports` | `project_name` | ✅ when populated | ✅ + fallback to `jobs_master.project_name` |
| `project_number` | `daily_reports` | `project_number` | ✅ | ✅ |
| `report_number` | `daily_reports` | `report_number` | ✅ | ✅ |
| `report_date` | `daily_reports` | `report_date` | ✅ | ✅ |
| `prepared_by` | `daily_reports` | `prepared_by` | ✅ | ✅ |
| `superintendent` | `daily_reports` | `superintendent` | ✅ | ✅ |
| `location` | `daily_reports` | `location` | ✅ | ✅ |
| `weather_summary` | `daily_reports` | `weather_summary` | ✅ | ✅ |
| `created_at` | `daily_reports` | `created_at` | ✅ | ✅ |
| `photo_count` | `daily_reports` | `$size of photos` | ✅ | ✅ |
| `crew_count` | `daily_reports` | `$size of masci_crews` | ✅ | ✅ |
| `sub_count` | `daily_reports` | `$size of subcontractors` | ✅ | ✅ |
| `visitor_count` | `daily_reports` | `$size of visitors` | ✅ | ✅ |
| **`pm_name`** | **`projects` only** (15.9A) | `pm_name` | **🔴 EMPTY for ~most rows** — `projects` table is sparse vs `jobs_master` | **🟢 fallback to `jobs_master.pm_name`** |
| **`pm_email`** | **`projects` only** (15.9A) | `pm_email` | **🔴 EMPTY for ~most rows** | **🟢 fallback to `jobs_master.pm_email`** |

---

## Detail endpoint · `GET /api/hr/daily-reports/{id}`

| Field | Source | Pre-15.13B | Post-15.13B |
| ----- | ------ | ---------- | ----------- |
| narrative / weather / crews / subs / vendors / location / sign-off | `daily_reports` | ✅ | ✅ |
| `pm_name` | `projects` only | 🔴 often empty | 🟢 projects → jobs_master → derived-from-email |
| `pm_email` | `projects` only | 🔴 often empty | 🟢 same chain |
| `project_name` | `daily_reports` | 🟡 sometimes empty | 🟢 fallback from `jobs_master.project_name` |
| **`photos[i]`** | `daily_reports.photos[i]` | 🔴 RENDERED AS `photo-0..photo-3` alt text — `<img src="photo://...">` failed | 🟢 piped through `resolvePhotoSrc()` → `/api/photo-bytes?ref=...` |

---

## Filter endpoints

| Filter | Pre-15.13B resolution | Post-15.13B |
| ------ | --------------------- | ----------- |
| `?date_from` / `?date_to` | `daily_reports.report_date` | ✅ unchanged |
| `?project=…` | `daily_reports.project_number` | ✅ unchanged |
| `?report_number=…` | `daily_reports.report_number` | ✅ unchanged |
| `?employee=…` | `daily_reports.masci_crews[].members[].name` | ✅ unchanged |
| `?subcontractor=…` | `daily_reports.subcontractors[].name` | ✅ unchanged |
| `?vendor=…` | `daily_reports.visitors[].name` | ✅ unchanged |
| `?superintendent=…` | `daily_reports.superintendent` | ✅ unchanged |
| `?foreman=…` | `daily_reports.masci_crews[].foreman` | ✅ unchanged |
| **`?pm=…`** | **`projects` ONLY** — invisible for jobs_master-only projects | **🟢 union of `projects` + `jobs_master`** |

---

## Defect list (closed in 15.13B)

| # | Defect | Root cause | Fix |
| - | ------ | ---------- | --- |
| HR-1 | `pm_name` / `pm_email` empty on HR list | `db.projects` is sparse vs `db.jobs_master` | $lookup union via $ifNull cascade |
| HR-2 | `pm_name` / `pm_email` empty on HR detail | Same | 3-tier fallback: projects → jobs_master → derived |
| HR-3 | `?pm=…` filter returns 0 rows for legacy DRs | Same | Filter resolves via both collections |
| HR-4 | Photo grid shows literal `photo-0..photo-3` strings | `<img src="photo://...">` un-resolvable | Pipe through `resolvePhotoSrc()` |
| HR-5 | Photo grid alt text doubles as broken-image text | `alt={`photo-${idx}`}` | Changed to `Photo ${idx + 1}` |
| HR-6 | `project_name` blank on some legacy DRs | `daily_reports.project_name` was never stamped | Fallback from `jobs_master.project_name` on the detail endpoint |

END · HR DAILY REPORT REALITY AUDIT.
