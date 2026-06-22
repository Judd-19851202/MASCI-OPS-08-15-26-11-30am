# TRACK 15.61 — Activity Log Forensics (Phase 2)

**Sample:** all 154 production Daily Reports in the 60-day window.
**Definition of "Activity Log"** for this audit: the union of every textual field across every row of the `activities[]` array on the canonical `db.daily_reports` document (`description` + `narrative` + `notes` + `details` + `location` + `crew`).

## Headline metrics

| Metric | Value |
|---|---|
| **% reports with a completely BLANK Activity Log** | **74.7 %** (115 / 154) |
| % under 25 words | 89.6 % (138 / 154) |
| % under 50 words | 95.5 % (147 / 154) |
| % over 100 words | **0.0 %** (0 / 154) |
| **Average words** | **7.0** |
| **Median words** | **0** |
| Average characters | 39.7 |
| Median characters | 0 |
| Average activity rows per report | **0.37** |
| Median activity rows per report | **0** |

> **Median of zero rows and zero words across 154 production reports** is not a typo. The typical Daily Report in production has NO entries in the Activity Log array.

## Distribution

| Bucket | Count | % |
|---|---|---|
| 0 words (blank) | 115 | 74.7 |
| 1–24 words | 23 | 14.9 |
| 25–49 words | 9 | 5.8 |
| 50–99 words | 7 | 4.5 |
| 100+ words | **0** | 0.0 |

## 25 best examples — full word-count ranking

The top 25 reports by Activity-Log word count (descending):

| Rank | Doc ID | Project | Preparer | Words | Rows | Preview |
|---|---|---|---|---|---|---|
| 1 | DR-2026-00029 | 25-21 | Joe spiker | **97** | 1 | "Backfill along outside of walls and finish grade for sod pallet I've all materia…" |
| 2 | DR-2026-00016 | 24-12 | Superintendent | **85** | 3 | "Grading · Worked on excavation in 2 different areas · Leandro worked on the nort…" |
| 3 | DR-2026-00026 | 25-21 | Joe spiker | **76** | 1 | "Backfill the remainder of the gravity wall grade between the gravity walls for …" |
| 4 | DR-2026-00266 | 25-21 | Joe spiker | **73** | 3 | "Silt fence removal · Trash and miscellaneous debris removal · Looks like a home…" |
| 5 | DR-2026-00061 | 24-12 | Superintendent | **67** | 3 | "Grading for sidewalk · As well, they graded the driveway at station 314 · Poure…" |
| 6–25 | — | — | — | 17–55 | 1–4 | (see `forensics.json` → `phase2.best_25_examples`) |

**Observation:** the best report in the entire 60-day corpus contains 97 words. By contrast, an Operationally complete Daily Report should narrate: who worked, what work occurred, on which stations, what was finished, what was delayed, what was the next step. A typical adequate narrative for a working civil crew is 200–400 words. **The MASCI corpus contains zero reports above 100 words.**

## 25 worst examples

The bottom 25 — all 0-word, 0-row Activity Logs. Identifiers include DR-2026-00045, DR-2026-00046, DR-2026-00047, DR-2026-00049, DR-2026-00051. These reports have a populated header (project, date, preparer) and often photos + crew rosters, but **the Activity Log is empty**. See `forensics.json` → `phase2.worst_25_examples` for the full list.

## Are crews actually using the Activity Log?

**No.** The behavioural picture is unambiguous:

- 74.7 % of reports have zero activity rows AND zero text. The Activity Log is **not** the foreman's chosen narrative surface.
- The 7-word average is essentially noise — when foremen do type into the Activities array, they type a single short phrase (e.g. "Grading", "Backfill", "Silt fence removal") and stop. They do not narrate the day.
- The `general_notes` text field is used MORE often than the Activities array (40.3 % non-empty vs. 26.0 % non-empty — see PHASE 10). Operators ARE writing narrative, they just write it in the wrong field for downstream aggregation.

## Triangulation

| Field | % non-empty |
|---|---|
| `activities[]` (Activity Log) | 26.0 % |
| `general_notes` (free-text "notes") | 40.3 % |
| `photos[]` | 97.4 % |
| `masci_crews[]` | 96.8 % |
| `production[]` | 3.2 % |
| `outbound_materials[]` | 2.6 % |

The data is being produced and the form IS being submitted — operators are taking photos and listing crews. They are NOT recording the day's narrative in the structured Activities field. They sometimes use `general_notes` as a substitute (40 %), and sometimes use photo captions or skip narrative entirely.

## Conclusion

The Activity Log is **functionally dead** in production. The field captures meaningful narrative on roughly 1 in 4 reports, and the typical entry is ≤ 7 words. No production report exceeds 100 words. This is the root finding of Phase 2. See `TRACK_15_61_FIELD_BEHAVIOR_ANALYSIS.md` for the behavioural rationale and `TRACK_15_61_RECOMMENDATIONS.md` for the prioritised fix list.
