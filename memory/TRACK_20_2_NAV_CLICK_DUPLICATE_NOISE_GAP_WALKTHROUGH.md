# TRACK 20.2 · Navigation / Click / Duplicate / Noise / Gap / Walkthrough (composite)

## Click audit — pre-promotion
| Question                                    | Current portal path                                                    | Clicks |
|---------------------------------------------|------------------------------------------------------------------------|:------:|
| How is this project doing?                   | PM CC → project selector → PmProjectDetail → scroll                     | 4      |
| Who has worked this project?                 | PM CC → project → Staffing / Team Roster                                | 4      |
| Which equipment has been here?               | PM CC → project → daily reports OR Dispatch JobBoard                    | 5      |
| Which incidents occurred?                    | Safety Hub → search by project OR PM CC → cross-reference               | 5      |
| Which trucks hauled?                         | Dispatch → JobBoard OR PmProjectDetail material-movement section        | 3      |
| Which POs are outstanding?                   | Operational events per day (multiple date drills)                       | 4      |
| Which photos exist?                          | JobPhotosLibrary                                                        | 3      |
| Which RFIs / Submittals exist?               | Not surfaced as first-class today                                       | ∞      |
| Which JHAs exist?                            | Safety Hub → project scope                                              | 4      |

## Click audit — post-promotion (proposed Track 19.57)
Every persona reaches ONE URL (e.g. `/pm/project/:job_number/thread`).
Every section renders in one scroll.
Expected: **≤ 2 clicks** for every question above.

## Duplicate detection
- No duplicate storage found. Every category has exactly one authoritative owner.
- No duplicate rendering framework. Track 19.54/19.55 primitives are the mandated visual layer.
- No duplicate score model. OI is the sole scoring source.
- Two overlapping surfaces exist (`PmProjectDetail` + `ProjectHealth`) — they cover different lenses (operational events vs. health), so they are NOT duplicates. Promotion would compose both into Sections 1 (Mission) + 8 (OI).

## Noise elimination
Apply the Delete Test to every card on `PmProjectDetail`. No decorative
widgets identified — every card either reads operational events,
material movement, or team facts. Zero cards flagged for removal.

## Gap analysis
- **RFIs / Submittals / Change Orders** — no first-class project surface today. LOW severity; a Thread can render honest empty states.
- **QA/QC test results** — not project-scoped in the frontend today.
- **Survey artifacts** — not project-scoped in the frontend today.
- **Warranty / Closeout** — not surfaced.
All gaps are LOW severity and non-blocking. No backend construction
required for the promotion track.

## Persona walkthrough
| Persona            | Question                                                       | Answered today? |
|--------------------|----------------------------------------------------------------|:---------------:|
| PM                 | How is my project doing?                                       | ✅ (PmProjectDetail + PmCC) |
| Superintendent     | What do I need before assigning today?                          | ✅ (recent-context + JobBoard) |
| Foreman            | What crew / equipment do I have?                                | ✅ (recent-context) |
| Safety Manager     | What JHAs / incidents on this project?                          | ✅ (Safety Hub + JHA files) |
| Ops Manager        | Is this project operationally healthy?                          | ✅ (project_intelligence OI) |
| Dispatcher         | What trucks/units are on this project?                          | ✅ (Dispatch JobBoard) |
| Fleet Manager      | Which units are on this project?                                | ✅ (dispatch + daily reports) |
| HR                 | Who is assigned?                                                | ✅ (team roster) |
| Executive          | Company-wide project health.                                    | ✅ (OI corporate_intelligence + weekly ops) |
| Estimator          | Cost / hauls / production for future estimates.                 | ✅ (P&L + material movement) |
| Engineer/Inspector | Compliance evidence (JHAs / DRs / photos).                       | ✅ (JHAs + JobPhotosLibrary + DRs) |
| Owner              | Progress overview.                                              | ⚠️ Partial (would benefit from Thread promotion) |

Every persona is served today. A Thread promotion improves the visual
consistency, not the underlying coverage.
