# TRACK 15.46A · Safety Topic Library · Audit

**Date:** 2026-06-19
**Companion:** `TRACK_15_46_SAFETY_TOPIC_LIBRARY_CERTIFICATION.md`
**Track parent:** 15.46 (Friction Reduction — this is the safety-topic-library side track)

---

## 1 · Purpose of the audit

The Safety Topic Library is the canonical source of every topic available to foremen when they file a Safety Meeting. Each topic carries:

- `title` · what gets printed on the meeting form and the PDF
- `incident_pattern` · the real story behind why this topic exists
- `hazards_reviewed` · the bullets the foreman must read aloud
- `discussion_notes` · the field-real talking points (not HR pablum)
- `references_cited` · OSHA / ANSI / MASCI policy references
- `action_items` · what gets verified on next pre-shift

Track 15.46A was authorized to (a) audit existing coverage, (b) identify gaps that field reports keep surfacing, and (c) add a new category for the most acutely missing area.

---

## 2 · Existing coverage (pre-15.46A)

22 domain modules cover the work the crews actually do:

| Domain | Topics | Bilingual |
|---|---|:---:|
| airport | airport-specific hazards | ✅ |
| concrete | placement, finishing, formwork | ✅ |
| confined_space | entry, atmospheric, rescue | ✅ |
| dewatering | pumps, discharge, control | ✅ |
| electrical | LOTO, energized work, qualified-person | ✅ |
| environmental | spill, dust, runoff | ✅ |
| excavation | trench, shoring, soil class | ✅ |
| fall_protection | tie-off, harness, retrieval | ✅ |
| general | PPE, housekeeping, hot work | ✅ |
| grading | equipment ops, line of fire | ✅ |
| lab | testing, materials, sampling | ✅ |
| milling | mill ops, traffic interface | ✅ |
| mot | maintenance of traffic, flagging | ✅ |
| office | office ergonomics, fire egress | ✅ |
| paving | hot-mix temp, screed, rollers | ✅ |
| pipe | trench-and-pipe combined hazards | ✅ |
| plant | hot-mix plant ops | ✅ |
| rigging | crane, signal-person, load | ✅ |
| shop | repair, fluids, hot work | ✅ |
| trucking | dump-body, tarping, brakes | ✅ |
| wellness | heat, cold, fatigue, hydration | ✅ |

EN/ES parity verified across `index.js` ↔ `index.es.js`. Total topics: ~115.

---

## 3 · Gap identified by field reports

Across the last 90 days of incident reports the platform indexed, the recurring near-miss / minor-injury pattern that had NO dedicated topic was:

> **Confrontation with members of the public.**

Examples lifted from incident free-text:
- Foreman approached by frustrated resident at 0700 about prior-day jackhammer noise → verbal escalation → resident filmed the exchange → posted to social media.
- Driver detoured by MOT cone tape ran the cones, stopped at the flagger, screamed for ~3 minutes, threw a coffee cup at the flagger.
- Business owner whose entrance was blocked by an excavation arrived with a baseball bat demanding access. SSC called the Sheriff.

Every existing topic touches a hazard the crew controls (a tool, a machine, a procedure). The "angry public" hazard is unique: the crew does NOT control the other person's behaviour, and the failure mode is almost entirely linguistic and postural. A workplace-violence reporter exists in the operational SOP but no pre-shift topic prepares the crew for the moment of impact.

**Audit conclusion:** add a new category and a flagship topic, write it in field-real language, ship it in both EN and ES.

---

## 4 · What 15.46A delivered

### 4.1 · New category

`Public Interaction & Conflict De-Escalation` — a sibling category to `wellness` (which already covers "the human in the worker"). The new category covers "the human outside the fence line."

### 4.2 · New topic

**Key:** `angry_public_de_escalation`
**Title:** `Dealing With Angry Members of the Public`

The topic body (field-real, not HR-speak) includes:

- A concrete `incident_pattern` based on real MASCI near-misses — the 7 a.m. resident, the detoured driver, the bat-wielding business owner — so the foreman knows this is a real risk and not a checkbox exercise.
- `hazards_reviewed` covering verbal confrontation through to workplace violence and personal injury.
- `discussion_notes` that are POSTURAL and LINGUISTIC, not procedural: lower your voice when theirs rises, acknowledge ("I hear you, I understand this is affecting your day") not agree, route the complaint up the chain, walk away to a vehicle, call 911 + then superintendent if a weapon shows, do not record, do not post.
- `references_cited` to OSHA Workplace Violence Prevention guidance, MASCI's existing workplace-violence policy, and the existing incident-reporting SOP.
- `action_items` the foreman can verify in the next pre-shift: superintendent phone posted in the cab, workplace-violence report form known, "walk away" rehearsed.

### 4.3 · Bilingual parity

| File | Status |
|---|:---:|
| `/app/frontend/src/lib/topics/public_interaction.js` | ✅ EN |
| `/app/frontend/src/lib/topics/public_interaction.es.js` | ✅ ES — translated to match wellness.es.js voice (field Spanish, not corporate Spanish) |
| `/app/frontend/src/lib/topics/index.js` | ✅ Aggregator wired |
| `/app/frontend/src/lib/topics/index.es.js` | ✅ Aggregator wired |
| `/app/frontend/src/components/TopicPicker.jsx` | ✅ Domain chip + category section added |

### 4.4 · Discoverability

The new domain shows up in the Topic Picker as a chip labelled "Public Interaction" with a count of 1 topic. The category section beneath the chip reads "Public Interaction & Conflict De-Escalation · 1" with the topic listed directly. Foreman taps once to filter, once to select — same UX flow as the other 22 domains.

---

## 5 · Audit findings beyond the new category

| Finding | Severity | Owner |
|---|---|---|
| No topic on "Stop work — when and how" as its own item (currently embedded in several domain topics). | Minor | Defer to next library track. |
| No topic on "Working alongside drones / overhead imagery surveys" — the survey program is new. | Minor | Defer. |
| No topic on "Member-of-the-public near children" (school zones, pedestrian) — partially covered in mot but a dedicated topic would be sharper. | Minor | Defer. |
| EN/ES voice consistency across older topics (e.g. `office`) is slightly less field-real than `wellness` and `public_interaction`. | Cosmetic | Defer; not blocking. |

None of these block 15.46A certification. They are noted for backlog grooming.

---

## 6 · Outcome

Library coverage moves from "22 domains, work-controlled hazards only" to "23 domains, work-controlled hazards + the most acute non-controlled-environment hazard." The new topic is bilingual, discoverable, follows the existing schema, and is written in language the crew will actually use at 6:45 a.m.

Sign-off: see `TRACK_15_46_SAFETY_TOPIC_LIBRARY_CERTIFICATION.md`.
