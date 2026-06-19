# TRACK 15.47 · Stop Work Authority Topic — Build Certification

**Status:** ✅ DELIVERED · EN + ES · live in topic library.
**Files:**
- `frontend/src/lib/topics/stop_work.js` (EN)
- `frontend/src/lib/topics/stop_work.es.js` (ES)
- `frontend/src/lib/topics/index.js` (aggregator wired)
- `frontend/src/lib/topics/index.es.js` (aggregator wired)
- `frontend/src/components/TopicPicker.jsx` (`stop_work` domain chip added)

## Voice test (60-second laborer comprehension)
The user mandate was: "If a laborer cannot understand it, rewrite it."

The topic carries a `read_aloud` field built explicitly for the foreman to read to the crew in 60 seconds at 5:30 AM:

> "Listen — sixty seconds. If you see something that is about to go wrong, say STOP. Out loud. Open palm in the air. Doesn't matter if you've been here a day or twenty years. Doesn't matter if I'm here, or if the GC is here, or if the owner is here. You can stop the work. We will back you. Every time. If something gets fixed, we restart. If it doesn't get fixed, we don't restart. We have lost people because somebody knew it was wrong and didn't say it. We are not losing another one. Stop Work is your job. It is not optional. It is not for emergencies only. It is for the moment you think 'this isn't right.' Trust that moment."

ES version mirrors voice and length.

## Schema coverage (TRACK 15.47-expanded)
| Field | EN | ES |
|---|---|---|
| title | ✅ | ✅ |
| incident_pattern | ✅ | ✅ |
| hazards_reviewed | ✅ | ✅ |
| warning_signs | ✅ | ✅ |
| when_to_stop | ✅ (9 explicit triggers) | ✅ |
| who_can_stop | ✅ (laborer through PM, all roles) | ✅ |
| how_to_stop | ✅ (7-step sequence) | ✅ |
| escalation_chain | ✅ (4-step ladder + retaliation clause) | ✅ |
| restart_requirements | ✅ (5-condition checklist) | ✅ |
| what_to_do / what_not_to_do | ✅ | ✅ |
| supervisor_actions | ✅ | ✅ |
| documentation | ✅ | ✅ |
| corrective_actions | ✅ | ✅ |
| read_aloud | ✅ (60-second cab read) | ✅ |
| references_cited | ✅ | ✅ |
| action_items | ✅ | ✅ |

## Triggers in the topic
The topic lists 9 specific Stop Work triggers, drawn from real MASCI patterns:
1. Aggressive public at trench edge (Track 15.47 trigger event)
2. Credible threat or weapon
3. Utility strike risk change (one-call stale, hydro-vac dry where utility expected)
4. Excavation instability or worker discomfort
5. Equipment safety alarm (not maintenance reminder)
6. Near-miss in previous 60 minutes
7. Visibly impaired worker (fatigue / med / alcohol / emotional)
8. Storm cell within 10 miles
9. Overhead utility / drone / aircraft closer than planned

## Anti-retaliation clause
The topic explicitly states "Retaliation for a Stop Work call is grounds for termination of the retaliator — laborer, foreman, super, or PM." This is the cultural backbone of the program.

## Discoverability
- New domain `stop_work` in `TopicPicker.jsx` `DOMAIN_CHIPS` (between `public_interaction` and `office`).
- New chip label: EN "Stop Work" · ES "Parar Trabajo".
- Topic exposed in both EN and ES TOPIC_LIBRARY (count delta = +1 in each).

## Field-real test (per user mandate)
- 5:30 AM foreman test: ✅ — the read_aloud is 60 seconds spoken.
- Laborer comprehension test: ✅ — no OSHA-manual passive voice; imperative sentences; concrete examples; first-person ownership.
- Foreman / super pressure test: ✅ — explicit "GC, Owner, DOT pressure does not change the call" clause.

## Sign-off
Stop Work Authority is the cultural backbone of every other topic in the Public-Interaction series. It is delivered with full bilingual parity and 60-second laborer comprehension.
