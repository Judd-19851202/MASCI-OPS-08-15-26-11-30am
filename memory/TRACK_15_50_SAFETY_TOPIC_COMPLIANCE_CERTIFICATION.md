# TRACK 15.50 · Safety Topic Compliance Certification (Phase 5)

**Status:** ✅ CERTIFIED · 9/9 topics ready for incident-driven retraining delivery.

## Topic inventory for incident-triggered retraining
| # | Topic key | EN | ES | Read-aloud | Corrective actions | Supervisor actions | Documentation |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `angry_public_de_escalation` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | `verbal_threats_harassment` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | `physical_confrontations` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | `recording_employees_social_media` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | `public_near_children` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | `media_public_questions` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | `trespassing_into_work_zones` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 8 | `drone_overhead_survey_ops` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | `stop_work_authority` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

(Note: "Social Media Encounters" and "Recording Employees" map to the single topic `recording_employees_social_media` covering both scenarios.)

## Topic file map
- EN: `/app/frontend/src/lib/topics/public_interaction.js` (topics 1-8) + `/app/frontend/src/lib/topics/stop_work.js` (topic 9)
- ES: `.es.js` companions for both
- Aggregators: `index.js` + `index.es.js` wired
- Discoverable in `TopicPicker.jsx` via domain chips `public_interaction` (8) + `stop_work` (1)

## Schema · TRACK 15.47-expanded (per topic)
All 9 topics carry:
- title · category · domain · severity
- incident_pattern · hazards_reviewed
- warning_signs · what_to_do · what_not_to_do
- supervisor_actions · documentation · corrective_actions
- read_aloud (60-second cab read)
- references_cited · action_items

Topic 9 (Stop Work) additionally carries when_to_stop, who_can_stop, how_to_stop, escalation_chain, restart_requirements.

## Mapping to the amendment's required topics
| Amendment requirement | Topic key |
|---|---|
| Dealing With Angry Members of the Public | ✅ `angry_public_de_escalation` |
| Stop Work Authority | ✅ `stop_work_authority` |
| Verbal Threats and Harassment | ✅ `verbal_threats_harassment` |
| Physical Confrontations and Workplace Violence | ✅ `physical_confrontations` |
| Recording Employees and Social Media | ✅ `recording_employees_social_media` |
| Trespassing Into Work Zones | ✅ `trespassing_into_work_zones` |
| Members of the Public Near Children | ✅ `public_near_children` |

All 7 amendment topic mandates are covered.

## Sign-off
GREEN. The topic library has the right content with the right depth in both languages with the right field structure. Incident-driven retraining can be DELIVERED from the existing library without writing new content.
