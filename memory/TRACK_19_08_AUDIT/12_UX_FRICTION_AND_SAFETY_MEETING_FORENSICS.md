# TRACK 19.08 · UX Friction Report + Safety Meeting Forensics

Two reports merged: general UX friction across the operational forms ecosystem + the safety-meeting deep-dive requested by Phase 11.

---

## PART A · General UX friction

### 1 · Cognitive load hotspots (evidence-backed)

| Form | LOC | Sections | Primary decisions per submit | Friction verdict |
| --- | ---: | ---: | ---: | --- |
| Daily Report (post-19.07) | 2,987 | 6 cognitive checkpoints | ~20 | 🟢 Simplified — 5 decisions removed vs. pre-19.07 |
| Equipment Pre-Op | 1,175 | N template sections + M items each | 40-80 depending on machine | 🔴 High — no progressive disclosure |
| DVIR | 887 | 7-10 sections × 6-8 items | 40-60 | 🔴 High — same pattern |
| Meeting | 1,161 | 7 sections | ~15 + attendee list | 🟡 Medium — attendance-driven |
| Incident | 1,672 | 11 sections | 30-50 (severity-dependent) | 🔴 High — longest form |
| Inspection (generic) | 835 | Template-driven | Variable | 🟡 Medium |
| QAQC | 671 | Template-driven | Variable | 🟡 Medium |
| Safety Equipment Issuance | 662 | 4 sections | ~10 | 🟢 Low |
| Safety Equipment Training | 509 | 4 sections | ~10 | 🟢 Low |

### 2 · Why forms feel long

Root causes, all evidenced in `15_ROOT_CAUSE_ANALYSIS.md`:
1. **No progressive disclosure** on Equipment/DVIR/Incident (unlike DR post-19.06).
2. **Coaching-panel stacking** — three helper systems visible simultaneously.
3. **Attendee row expansion** on Meetings — Nx signature pads plus HR-picker each.
4. **Field density in Incident** — 11 sections all always visible.

### 3 · Where operators hesitate (inferred from support tickets & telemetry patterns)

Observed via `draft_telemetry` events + support-ticket categorization (indirect evidence — no user studies performed in 19.08):
* **Job picker on Equipment Pre-Op** — operators select the wrong job, discover no auto-fill for location, hesitate.
* **Yes/No presence gate on "Was MASCI equipment on site?" (DR)** — some operators tap Yes then realise the section is optional; some hesitate.
* **Signature pad on mobile** — smaller devices trigger the wrong scroll region.
* **"Overall status" pill on DVIR** — auto-computed but not clearly labeled as auto → operators try to tap it.
* **Reset hours vs. Remove button (DR)** — with the new Track 19.06 amendment button, adjacent buttons could be confused (button text differs; not observed as an issue yet).

### 4 · Pencil-whip risk (industry-standard concern)

| Form | Pencil-whip surface | Detected? |
| --- | --- | --- |
| Equipment Pre-Op | 100% "Pass" submissions from same operator on same unit day-over-day | No detection heuristic currently |
| DVIR | Same | No |
| Meeting | Attendance list identical week-over-week | No |
| Daily Report | Crew list unchanged plus Smart Prefill auto-apply | Track 19.04 fixed this — Smart Prefill is now an explicit offer, not silent-apply |

**Industry standard**: Samsara / MaintainX detect these patterns. Not implemented on MASCI. P2 opportunity.

### 5 · Where hierarchy is broken

Evidenced by inspection of the shell primitives:
* **Coaching-tip bar** (`5 COACHING TIPS AVAILABLE · TAP TO EXPAND`) always renders at position 3 in the visual hierarchy on the DR — competing with the actual first section for operator attention.
* **Draft restore banner** overlaps with the coaching-tip bar visually — restore banner has amber accent while tips have red-ish accent → both fighting for attention.
* **Section 01 header** ("Report Information") is smaller than the cognitive-checkpoint band label above it — the *smaller* item is the actual form section title. This is intentional (bands are cognitive anchors, sections are procedural containers) but adds visual complexity.

### 6 · Architectural drift signals

| Signal | Evidence |
| --- | --- |
| **Helper-system accretion** | iter194 + iter305 + iter360 all added a distinct helper mechanism |
| **Section-count growth** | Equipment Pre-Op sections grew with each machine-type addition; no consolidation |
| **Hub V2 dual-run** | V1 and V2 both mounted — no retirement plan |
| **Two JHA surfaces** | `inspections.subtype=jha` and `jhas` collection both live |
| **Actor-scope late-arrival** | Draft-store isolation didn't ship until Track 19.04 — 190+ iterations after the platform first stored drafts |

None of these are broken. All are drift.

---

## PART B · Safety Meeting Forensics (Phase 11 focus)

### B.1 · Why safety meetings feel low-value

The `NewMeeting.jsx` form is well-built. Attendance is captured. Photos are optional. Signatures are collected. A PDF renders and emails go out. From a *compliance* standpoint the form is complete.

The perceived low value comes from a specific structural gap:

| Meeting captures | Meeting does NOT capture |
| --- | --- |
| Who attended | Whether attendees understood the topic |
| What was covered | What decisions each crew member will make differently today |
| Presenter | Any commitment / action item per attendee |
| Duration | Any linkage back to a triggering incident / near-miss / observation |
| Signatures | Any verification of learning after the meeting |

**Consequence**: A weekly meeting produces perfect legal documentation and zero operational intelligence. From a compliance auditor's view the form is 10/10. From an operations executive's view it's 3/10.

### B.2 · Duplicate work operators perceive

* Foreman must sign each attendee's signature pad individually (some rooms have 10+ crew). No batch sign.
* Same topic often runs across multiple crews on same day — no cross-meeting "topic instance" primitive; each is a fresh submit.
* Attendee names must be picked from HR roster one-by-one. No "select last week's attendees" shortcut.

### B.3 · Confusing flow

* **Meeting type** (safety-meeting / toolbox-talk / pre-task-briefing / tailgate) — legacy alias `tailgate` still accepted. Operators sometimes pick "tailgate" thinking it's different from "toolbox-talk"; they're the same.
* **Topic library** — powerful but discoverability is low. Most operators type free text.
* **Key Takeaways vs. Topics Covered** — labels are close in meaning; operators fill either or both inconsistently.

### B.4 · Downstream weakness

* Meetings mirror to `safety_training_records` for HR-accountability credit. But there's no linkage back showing "this employee's last training on topic X was N days ago." So repeated meetings on the same topic aren't detected.
* Weekly safety-digest lists meetings but not their operational outcomes — no delta between "meetings held" and "incidents avoided."

### B.5 · Industry benchmarks

* **Raken**: attaches meeting to a specific day's Day Sheet — operators immediately see the meeting alongside their crew's actual work.
* **Procore Safety**: adds a "quick knowledge check" (single question) at meeting end; captures per-attendee.
* **HCSS Safety Inspection**: links meetings to open corrective actions.
* **Samsara AI Coaching**: uses meeting attendance + observed driver events to *personalise* the next meeting's content per driver.

**None of these are implemented on MASCI.** All are P1/P2 opportunities.

### B.6 · Non-changes to make in redesign

MUST PRESERVE (per §14 protection matrix):
* Attendee signature capture — this is the OSHA / legal artifact
* Meeting PDF format — auditors expect this
* `meeting_type` enum values (all four, incl. legacy `tailgate`)
* `topics_covered` free-text field
* Photo attachment path
* Weekly digest cadence

CAN SIMPLIFY:
* Merge "Topics Covered" + "Key Takeaways" into a single "What did we discuss and decide?" field (single intent, less confusion).
* Add a per-attendee single-tap knowledge-check pill ("Repeat back the one thing you'll do differently").
* Add "Copy attendees from last meeting" one-click.

CAN HIDE:
* `tailgate` synonym — surface as `toolbox_talk` only in the picker (still accept it on read).

None of these are executed in Track 19.08.
