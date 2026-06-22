# TRACK 15.61 — Job Story Quality Audit (Phase 4)

**Method:** an 8-question YES/NO scoring rubric applied to every production report. Each YES = 1 point. Score range 0–8. Higher = the report tells more of the story.

## Rubric

| # | Question | YES when… |
|---|---|---|
| Q1 | What work occurred? | `activities` rows present OR `masci_crews` non-empty OR `subcontractors` non-empty |
| Q2 | What was completed? | any activity row has `status=complete` or "complete" in description OR `production[]` non-empty |
| Q3 | What delayed work? | `schedule_delays` true OR `schedule_delays_notes` non-empty OR `weather_impact` true OR `weather_impact_notes` non-empty |
| Q4 | What changed? | `general_notes` non-empty OR `constraints[]` non-empty |
| Q5 | What inspections occurred? | `excavation_activity_today` true OR `linked_excavation_ids[]` non-empty |
| Q6 | What issues need follow-up? | `constraints[]` non-empty OR `safety_incidents_today` truthy |
| Q7 | Could a PM understand the day? | Activity text ≥ 20 words OR `general_notes` ≥ 20 words |
| Q8 | Could an executive understand the day? | `production[]` non-empty OR activity text ≥ 50 words |

## Score distribution (n = 154)

| Score (out of 8) | Reports | % |
|---|---|---|
| 8 | **1** | 0.6 % |
| 7 | 0 | 0.0 % |
| 6 | 13 | 8.4 % |
| 5 | 35 | 22.7 % |
| 4 | 53 | 34.4 % |
| 3 | 49 | 31.8 % |
| 2 | 3 | 1.9 % |
| 1 | 0 | 0.0 % |
| 0 | 0 | 0.0 % |

Median score: **4 / 8**. Mode: **4** (34.4 % of reports). Only **1 of 154** production reports scored a perfect 8.

## Top 20 best reports

| Rank | doc_id | Score | Project | Preparer |
|---|---|---|---|---|
| 1 | DR-2026-00311 | **8/8** | 26-07 | Jaymn Judd |
| 2 | DR-2026-00347 | 6/8 | 24-12 | ALLEN SMATHERS |
| 3 | DR-2026-00343 | 6/8 | 26-01 - CP | MICHAEL TRAIL |
| 4 | DR-2026-00329 | 6/8 | 24-12 | ALLEN SMATHERS |
| 5 | DR-2026-00325 | 6/8 | 24-12 | CHRISTOPHER GAINES |
| 6–20 | — | 5–6/8 | — | — |

The one 8/8 report belongs to a known platform owner (Jaymn Judd), a strong reporter who narrates `activities`, populates `production[]`, and signs the report. Several 6/8 reports cluster around Allen Smathers / Michael Trail / Christopher Gaines on the active 24-12 / 26-01 projects.

## Top 20 worst reports

| Rank | doc_id | Score | Project | Preparer |
|---|---|---|---|---|
| —20 | DR-2026-00342 | 2/8 | 20-07 | TRACK 15.35 Cert | (synthetic) |
| —19 | DR-2026-00284 | 2/8 | PROD-ORPHAN-CORNER-VERIFY | (synthetic) |
| —18 | DR-2026-00283 | 2/8 | _PROD_CERT_DO_NOT_USE | (synthetic) |
| —17–—1 | DR-2026-0000{1..5} etc. | 3/8 | 25-21 / 24-12 | Joe spiker / Ivan Lopez / Leandro |

The bottom 20 are either synthetic harness records (acceptable — they were never meant to be full reports) or real reports that have a header + photos + crew BUT no narrative, no production, no inspections, no delays, no notes. From a PM/Exec read-back perspective these reports are a "the crew showed up" signal and little more.

## Can a stranger understand what happened on the job?

**No, in most cases.** With a median score of 4/8, half the production reports answer 4 or fewer of the 8 narrative questions a PM/exec would naturally ask. The unanswered questions cluster around Q2 (completed), Q3 (delays), Q4 (changes), Q5 (inspections), Q7 (PM-readable), and Q8 (exec-readable). The platform IS getting "who was there" and "what photos were taken", but is NOT getting "what happened" in the prose sense.

## Subtle observation

The single 8/8 report (DR-2026-00311) shows that the schema and form CAN support a complete story when the operator chooses to fill it in. The form is not blocking quality; the operators are simply not using it to its full capacity. This is consistent with the Activity Log forensics in Phase 2 — the surface exists, the durability exists, but the field UX does not coach the operator into telling the story.

See `TRACK_15_61_FIELD_BEHAVIOR_ANALYSIS.md` for behavioural diagnosis and `TRACK_15_61_HUMAN_USABILITY_AUDIT.md` for the UX-side findings.
