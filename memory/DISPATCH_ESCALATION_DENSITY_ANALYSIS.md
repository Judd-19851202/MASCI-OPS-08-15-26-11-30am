# Dispatch Escalation-Density Analysis — Phase IV-BETA.5A-P4C

*iter437 · 2026-02-27*
*Status: 🟢 READ-ONLY · escalation discipline measurement*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Measure Dispatch's escalation density to confirm the portal already
honours the "Nothing else fires" policy and to identify any false-
urgency drift before a governance phase begins.

## II. Active escalation signals (🟢)

Per the source-of-truth comment in `DispatchBoard.jsx` line 521,
Dispatch fires exactly **FOUR** real signals:

| Code | Severity | Trigger |
|---|---|---|
| `BREAKDOWN_ACTIVE` | critical | Truck reports active breakdown |
| `ASSIGNMENT_STUCK` | escalation | ≥ 30 min in non-terminal state |
| `WAIT_THRESHOLD_EXCEEDED` | escalation | ≥ 20 min in `WAITING` |
| `NON_STANDARD_TRANSITION_PATTERN` | escalation | ≥ 3 non-standard transitions in 2 h per truck |

"Nothing else fires" — the operator policy is literal. Governance MUST
preserve this discipline. Adding a 5th signal would dilute the
operator's pattern recognition.

## III. Visual escalation surfaces (🟢)

| Surface | Element | Tone |
|---|---|---|
| `DispatchBoard.jsx` filter chip | `severityTone()` | rose (critical) → amber → emerald (low) |
| `DispatchLifecycleTile.jsx` | Lifecycle-status badge | colour follows transition state |
| `OperationalMomentsRail.jsx` | Moment cards | severity-graded |
| Hub Operational Attention | Header section | already calm · doctrine-aligned |

**Decorative escalations found:** none in the surfaces inspected. Every
red / rose appearance is data-bound. Operationally honest.

## IV. Severity-pill discipline (🟢 honoured)

`DispatchBoard.jsx::severityTone()` follows the same pattern as
`SafetyIncidents.jsx::SEV_PILL` — colour determined by `sev`, not by
`status`. Workflow state (`WAITING`, `IN_PROGRESS`, etc.) is rendered
in **neutral chrome**. This already matches the iter437 IV-BETA.5A
discipline applied to Safety.

## V. Cross-portal escalation parity (🟢)

| Portal | Severity pill component | Discipline |
|---|---|---|
| Safety | `SEV_PILL` | data-bound · 4 tiers · status pills slate |
| Dispatch | `severityTone()` | data-bound · 4 tiers · status pills slate |
| PM | n/a (PM is calmest portal) | — |
| HR | data-bound for compliance pills | — |

Dispatch is **already aligned** with the cross-portal escalation
discipline. Future governance need only verify and tighten — not
overhaul.

## VI. Anti-patterns to guard against (🟢)

- 🔴 Adding a 5th signal class would weaken the "Nothing else fires" doctrine.
- 🔴 Demoting rose `critical` to slate would mute true urgency.
- 🔴 Adding decorative badges (e.g. "New", "Updated") would dilute pattern recognition.
- 🔴 Coloring the polling indicator would attract eye from the actual escalations.
- 🔴 Animating severity transitions would attract eye AT THE WORST POSSIBLE TIME.

## VII. Recommended governance follow-up (🟡 advisory · NOT authorised)

| Item | Goal |
|---|---|
| Document the 4-signal contract in a doctrine doc | Lock the policy formally |
| Verify no 5th signal has leaked in since iter392 | Confirm policy still honoured |
| Confirm all 4 signals fire EMAIL with the canonical operational footer | Communication parity |
| Mobile: surface the 4 signals at the top of the board on mobile | Reinforce policy through UX |

## VIII. Doctrine reaffirmed

- ✅ READ-ONLY · zero code changes
- ✅ Dispatch already honours "Nothing else fires" policy
- ✅ No decorative escalations identified
- ✅ Cross-portal severity discipline aligned
- ✅ Preview only · NO production deploy
