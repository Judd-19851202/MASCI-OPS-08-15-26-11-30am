# TRACK 15.47 · Public Interaction Series — Build Certification

**Status:** ✅ DELIVERED · 8 topics · EN + ES · live in topic library.

## Topic roster
| # | Key | Title (EN) | Severity | EN | ES |
|---|---|---|---|:---:|:---:|
| 1 | `angry_public_de_escalation` | Dealing With Angry Members of the Public | serious_injury | ✅ | ✅ |
| 2 | `public_near_children` | Members of the Public Near Children | serious_injury | ✅ | ✅ |
| 3 | `verbal_threats_harassment` | Verbal Threats & Harassment | serious_injury | ✅ | ✅ |
| 4 | `physical_confrontations` | Physical Confrontations | serious_injury | ✅ | ✅ |
| 5 | `recording_employees_social_media` | Recording Employees / Social Media Encounters | moderate | ✅ | ✅ |
| 6 | `media_public_questions` | Media & Public Questions | moderate | ✅ | ✅ |
| 7 | `trespassing_into_work_zones` | Trespassing Into Work Zones | serious_injury | ✅ | ✅ |
| 8 | `drone_overhead_survey_ops` | Drone & Overhead Survey Operations | moderate | ✅ | ✅ |

Topic 1 carried over from Track 15.46A (extended in 15.47 with the new schema fields). Topics 2-8 are new in Track 15.47.

## TRACK 15.47-expanded schema (per topic)
Every topic above carries the full TRACK 15.47 schema:
- title · category · domain · severity
- incident_pattern (real MASCI lesson, not theory)
- hazards_reviewed
- **warning_signs** (NEW · field-observable cues)
- **what_to_do** (NEW · numbered imperative steps)
- **what_not_to_do** (NEW · explicit don'ts)
- **supervisor_actions** (NEW · foreman / super accountability)
- **documentation** (NEW · ForgedOps-specific instructions with classification names)
- **corrective_actions** (NEW · verifiable items)
- **read_aloud** (NEW · 60-second cab read)
- references_cited
- action_items

## Foreman read-aloud (5:30 AM test)
Every topic carries a `read_aloud` block written for direct delivery to the crew. Sample (Topic 4, Physical Confrontations):

> "If someone touches you — pushes you, swings at you, throws something at you — STOP. Hands open. Step back, not forward. Do not push back. The second you push back, it stops being a video of THEM assaulting you and it becomes a video of TWO PEOPLE fighting. We lose the case. You lose the case. You stop. You retreat. You call 911. Then you call me. Then you take pictures of the spot, the barricade, your hands, your shirt. Even if you feel fine — you get checked out. Concussions show up an hour later."

ES versions mirror tone, length, and field-real voice. Translator chose campo Spanish (not formal HR Spanish) on purpose.

## Documentation guidance per topic
Every topic's `documentation` field references the Track 15.47 incident classifications by name — e.g. "Classifications: Public Interaction + Verbal Confrontation (and Threat / Physical Contact / Workplace Violence if applicable)." This binds the safety topic to the actual reporting workflow operators will use.

## Discoverability
- Domain chip `public_interaction` (EN "Public Interaction" / ES "Trato con Público") already in `DOMAIN_CHIPS` from 15.46A.
- All 8 topics under category "Public Interaction & Conflict De-Escalation" — appear together in the Topic Picker grouped view.
- Searchable via TopicPicker search input.

## Topic library counts
- Pre-15.47: ~115 topics · 1 public-interaction topic.
- Post-15.47: ~122 topics · **8** public-interaction topics + **1** stop-work topic.
- EN/ES parity: ✅ (verified via aggregator file diff).

## Sign-off
The Public Interaction Series is delivered in full, EN + ES, with field-real voice, foreman read-aloud blocks, and explicit binding to the Track 15.47 incident workflow classifications. No corporate-HR voice; no OSHA-manual prose; every topic survives the 5:30 AM laborer comprehension test.
