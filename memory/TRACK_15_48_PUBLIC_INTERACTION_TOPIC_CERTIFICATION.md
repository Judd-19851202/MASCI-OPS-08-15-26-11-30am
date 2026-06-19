# TRACK 15.48 · Public Interaction Topic Library Certification (Phase 3)

**Status:** ✅ CERTIFIED · 9/9 topics live · EN+ES parity · Topic Picker verified live.

## Required topics matrix
| # | Topic key | Title (EN) | EN file | ES file | Picker chip count | Search | Meeting | Signatures |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `angry_public_de_escalation` | Dealing With Angry Members of the Public | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 2 | `stop_work_authority` | Stop Work Authority — When and How to Stop Work | ✅ | ✅ | ✅ (in 1) | ✅ | ✅ | ✅ |
| 3 | `verbal_threats_harassment` | Verbal Threats & Harassment | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 4 | `physical_confrontations` | Physical Confrontations | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 5 | `recording_employees_social_media` | Recording Employees / Social Media Encounters | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 6 | `media_public_questions` | Media & Public Questions | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 7 | `public_near_children` | Members of the Public Near Children | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 8 | `trespassing_into_work_zones` | Trespassing Into Work Zones | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |
| 9 | `drone_overhead_survey_ops` | Drone & Overhead Survey Operations | ✅ | ✅ | ✅ (in 8) | ✅ | ✅ | ✅ |

## Live Topic Picker verification (screenshot evidence)
- Domain chip "Public Interaction **8**" renders.
- Domain chip "Stop Work **1**" renders.
- Category section heading "Public Interaction & Conflict De-Escalation · 8" renders.
- All 8 PI titles render in the category section.
- Stop Work renders under its own "Stop Work Authority" category.

## Schema fields (per topic · TRACK 15.47-expanded)
Every topic ships with:
- title · category · domain · severity
- incident_pattern · hazards_reviewed
- **warning_signs** (NEW in 15.47)
- **what_to_do** / **what_not_to_do** (NEW)
- **supervisor_actions** (NEW)
- **documentation** (NEW · binds to Track 15.47 classifications)
- **corrective_actions** (NEW)
- **read_aloud** (NEW · 60-second cab read)
- references_cited · action_items

Topic 2 (Stop Work) additionally carries: `when_to_stop` · `who_can_stop` · `how_to_stop` · `escalation_chain` · `restart_requirements`.

## EN ↔ ES parity
- EN files: `public_interaction.js` + `stop_work.js`
- ES files: `public_interaction.es.js` + `stop_work.es.js`
- Aggregators: `index.js` + `index.es.js` both wired
- DOMAIN_CHIPS in TopicPicker.jsx has both `public_interaction` and `stop_work` keys with EN + ES labels

## Sign-off
All 9 required topics exist, are searchable, are pickable in the Topic Picker, render in both English and Spanish, support meeting creation, support attendee management (including Track 15.46 bulk-add), support signature capture, and ride through the existing safety-meeting PDF pipeline. Phase 3 GREEN.
