# Safety Incident Governance Alignment

*Phase IV-BETA.5A · iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · regression-locked*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Apply governance alignment to **incident surfaces only** (Phase IV-BETA.5A):

- `SafetyIncidents.jsx` — list / review surface
- `ViewIncident.jsx` — single-incident detail page (verbiage preserved)
- Incident hierarchy structure on the Safety Hub
- Incident notification tone alignment

**NOT in scope** (preserved verbatim): the backend escalation engine,
notification routing, severe-incident email subject contracts, or any
write-side incident workflow.

## II. Three-tier escalation contract (🟢 inherited unchanged)

Per `SAFETY_ESCALATION_HIERARCHY_MAP.md §I` — the existing 3-tier
contract stays as-is:

| Tier | Visual signal | Email prefix |
|---|---|---|
| Routine | Neutral chrome, doctrine stripe, no badge | `[MASCI · {TAG}] …` |
| Action Required | Amber pill on the row, no panel colour | TAG only |
| Severe / Immediate | `SEV_PILL` red + per-record banner | `🚨 SEVERE INCIDENT · …` |

## III. Incident-list surface changes (🟢 VERIFIED · `SafetyIncidents.jsx`)

| Element | Before | After |
|---|---|---|
| Page header icon block | `bg-amber-600` (false urgency) | `bg-slate-800` (neutral chrome) |
| Page header stripe | none | `border-l-4 border-l-red-700` (the ONE red signal at the page level — anchors the incidents-domain identity) |
| Header kicker label | `text-amber-700` "Safety Portal" | `text-red-700` "Safety Portal · Incidents" |
| Intro sentence | 27 words, multi-clause | **22 words**, single-clause, period termination |
| Open-incident link colour | `text-cyan-700` (loud, off-doctrine for an incidents surface) | `text-slate-800` (neutral · matches the CTA neutralisation pattern) |
| `STATUS_PILL` Open | `bg-red-100 text-red-900` (decorative red) | `bg-slate-100 text-slate-800` (neutral state) |
| `STATUS_PILL` Investigating | `bg-amber-100 text-amber-900` | `bg-slate-100 text-slate-800` |
| `STATUS_PILL` Closed | `bg-emerald-100 text-emerald-900` | `bg-slate-100 text-slate-500` (calm, faded) |
| `SEV_PILL` (severity column) | unchanged | unchanged — **true urgency preserved** |

## IV. Incident detail (`ViewIncident.jsx`) — preserved (🟢)

The single-incident detail page was intentionally NOT modified:

- Severe-tier banner (`AlertOctagon` rose tone) preserved verbatim
- `severityOf()` colour selection preserved
- OSHA Recordable pill (red-900) preserved
- Follow-up status banner (rose / amber / emerald) preserved
- Tier-2 follow-up CTA preserved

Rationale: `ViewIncident.jsx` is the **operational record of true
severity** — and the per-record signal is doctrine-correct. Demoting
the detail page would mute true urgency. Only the **roll-up surface**
(list view) was demoted, exactly because aggregate roll-ups should
not appear panic-coloured by default.

## V. Hub-level alignment (🟢)

Incident-domain tiles on `SafetyHub.jsx`:

| Tile | Accent | Stripe colour |
|---|---|---|
| Tasks & Actions | `incidents` | red-700 |
| Corrective Actions | `incidents` | red-700 |
| Incidents & Near Misses | `incidents` | red-700 |
| Audits & Inspections | `audits` | slate-500 (demoted out of incidents) |

The three operational incidents-domain tiles cluster visually via the
red-700 left stripe; Audits is decoupled into the Audits & Guidance
slate domain (a single inspection is routine, not an escalation).

## VI. Notification tone alignment (🟢 preserved · 🟡 not modified)

Per operator directive (PHASE IV-BETA.5A scope), the notification
engine and email subject lines are **NOT** modified in this phase.
The existing email subject contracts remain doctrine-compliant
(`🚨 SEVERE INCIDENT · …` / `⚠ EQUIPMENT FAIL · …`) and inherit the
operational footer added in `COMMUNICATION_FOOTER_STANDARDIZATION.md`.

## VII. Mobile contract (🟢 see `SAFETY_MOBILE_CALMNESS_REPORT.md`)

Mobile incident scanning ergonomics:

- Severity pill **size and weight preserved** at all viewports
- Status pill becomes calm slate (read-as-state, not read-as-alarm)
- Header stripe scales unchanged (4 px left border)
- File-upload paths preserved (no UI change to camera capture flow)

## VIII. Doctrine preserved (🟢)

- ✅ `SEV_PILL` not touched — true urgency stays loud
- ✅ Severe-tier banner per-record discipline preserved
- ✅ OSHA Recordable pill preserved at red-900
- ✅ Severe-incident email subject contract preserved
- ✅ NO write-side workflow changes
- ✅ NO backend escalation logic changes
- ✅ NO database schema changes
- ✅ Hub Incidents tile uses the red-700 doctrine stripe (not legacy red-600)
- ✅ Status pill demoted to slate (workflow state ≠ severity)
