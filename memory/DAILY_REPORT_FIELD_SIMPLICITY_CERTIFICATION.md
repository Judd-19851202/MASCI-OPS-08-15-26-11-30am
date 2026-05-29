# Daily Report · Field Simplicity Certification

_Phase V.1 · 2026-05-29 · application of Doctrine Lock #1 to the Daily Report uplift._

> **Doctrine source:** `ODR_SIMPLICITY_TEST_DOCTRINE.md`
> **The test that governs every change:**
> _"Would a foreman complete this on a phone, standing in mud,
> wearing gloves, at 5:30 PM, after a 12-hour shift?"_

This document certifies that the proposed Daily Report elite upgrade
respects the foreman experience. Every "ADD" from
`DAILY_REPORT_EVOLUTION_PLAN.md §3` is run through the test below
before it ships.

---

## 1 · The 9-step contract (locked)

Daily Report has 9 steps. **No 10th step is permitted.** Every new
capability lands inside an existing step or moves to PM/Super.

```
1. Project       — auto-detected (one tap to confirm)
2. Crew          — last-used (one tap to confirm)
3. Equipment     — last-used (one tap to confirm)
4. Production    — pick unit, enter qty, optional station
5. Photos        — tap, voice-caption, done
6. Issues/Delays — tap a chip if anything happened
7. Safety        — "any incident today?" Y/N + notes
8. Sign          — standard signature pad
9. Submit        — one tap, idempotent
```

## 2 · Simplicity Test results · per proposed ADD

### 2.1 Production Quantities

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **YES** (one tap for unit, swipe-up numeric for qty, optional voice for station) | n/a |
| Time-to-complete impact | **+15 to 30 seconds** per production row | acceptable; rows are 1–3 typical |
| Forbidden patterns introduced | None | n/a |

**Mitigations baked in:**
- Last-used unit pre-selected (one tap to use, swipe to change)
- Numeric keypad opens automatically on qty focus
- Station range is optional (foreman skips if unknown — PM fills later)
- Voice input available on the notes field

### 2.2 Constraint / Delay Tracking

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **YES** (chip selector → typed taxonomy, no free-text required) | n/a |
| Time-to-complete impact | **+10 seconds per constraint** if any | acceptable |
| Forbidden patterns introduced | None | n/a |

**Mitigations baked in:**
- "No constraints today" is the default zero-tap state
- Constraint type is a single tap on a chip (no dropdown)
- Hours_lost is optional (PM can backfill from telemetry)
- Description is voice-or-text, never required

### 2.3 Activity / Work Area Tracking

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **CONDITIONAL — YES only if inferred from production rows** | If NO, infer from production (already done in step 4); do not ask foreman to enter activities separately |
| Time-to-complete impact | **0 seconds** if inferred, **+30 seconds** if foreman has to author | inference is required |
| Forbidden patterns introduced | Risk of separate activity step (forbidden — must reuse step 4) | enforce via UI: activity tracking is a sub-aspect of production rows, not a separate section |

**Decision:** activity tracking is **inferred** from production rows + dispatch crew/equipment. Foreman does not author activities separately. This protects the 9-step contract and the < 5 min target.

### 2.4 RFI-ready flag

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **YES** (one checkbox · advisory only · default off) | n/a |
| Time-to-complete impact | **0 seconds typical** (default off; only when something truly needs an RFI) | acceptable |
| Forbidden patterns introduced | None | the flag does NOT create an RFI — pure signal |

### 2.5 Schedule-impact flag

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **YES** (one checkbox · advisory only · default off) | n/a |
| Time-to-complete impact | **0 seconds typical** | acceptable |
| Forbidden patterns introduced | None | the flag does NOT modify any schedule — pure signal |

### 2.6 Better photo linkage

| Test | Answer | Remediation if NO |
|---|---|---|
| Could a foreman do this in mud / gloves / 5:30 PM? | **YES** if defaulted; **NO** if foreman must pick a link | Default to "general"; offer one tap to pin to the nearest production/constraint row |
| Time-to-complete impact | **0 seconds typical** (default = general; manual pin is one tap) | acceptable |
| Forbidden patterns introduced | None | foreman is never forced to link |

## 3 · Anti-patterns that the simplicity gate forbids in this upgrade

1. ❌ Modal stack inside the foreman flow
2. ❌ "Required" fields beyond what is required today
3. ❌ A separate "ODR" form anywhere on the foreman path
4. ❌ Required PDF generation by the foreman
5. ❌ Required approval from a PM during foreman submit
6. ❌ Punitive coaching tone ("you forgot…", "you must…")
7. ❌ Aesthetic loudness (urgency pills, red alerts, exclamation marks) on the foreman path
8. ❌ A 10th wizard step
9. ❌ Telemetry-driven foreman UI (UI shape MUST NOT vary by foreman performance)
10. ❌ Onboarding interruptions on returning users

## 4 · Approval block — every PR in this wave must carry this

```
## Daily Report Simplicity Test
- Foreman completion test: [PASS / FAIL]
- Time-to-complete impact: [Δ seconds]
- Mud / gloves / 5:30 PM scenario: [Justification]
- Remediation taken (if FAIL): [Remove / Hide / Auto-populate /
  Infer / Move to Super / Move to PM / Move to Ops]
- 9-step contract preserved: [YES / NO]
```

PRs missing this block are not eligible for merge in this wave.

## 5 · Success metric

End-to-end foreman completion on a real device under real field
conditions:

| Bound | Today | Target after wave |
|---|---|---|
| Mean | ~5 min (sample) | hold or reduce |
| Stretch | n/a | < 3 min |
| Hard ceiling | 7 min | not breached |

Measurement: stopwatch a real foreman on a real device with gloves
and intermittent connectivity. Synthetic desktop timings are not
valid evidence.

## 6 · Inheritance

This certification inherits from and reinforces:

- `ODR_SIMPLICITY_TEST_DOCTRINE.md` (Doctrine Lock #1)
- `ODR_PLATFORM_INHERITANCE_DOCTRINE.md` (Doctrine Lock #2)
- `DAILY_REPORT_FIELD_TRUST_REVIEW.md` (TRUST-1)
- `OPERATIONAL_CALMNESS_DOCTRINE.md`
- `CROSS_PORTAL_COACHING_STANDARD.md` (non-punitive coaching)

---

_End of DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md._
