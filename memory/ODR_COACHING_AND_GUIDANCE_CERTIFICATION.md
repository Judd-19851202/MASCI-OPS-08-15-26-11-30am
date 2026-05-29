# ODR · COACHING & GUIDANCE CERTIFICATION

_Phase V.1 · Operational Daily Record · Pre-Lock Final Certification · 2026-05-29_

This certification verifies that the **Coaching / Training /
Operational Guidance** doctrine (O36–O50) is incorporated into the
ODR architecture before specification lock.

**No implementation. No code. No routes. No collections. No UI.**
**Architecture-only.**

---

## 1 · Required certifications (operator's 8-point checklist)

| # | Required certification | Verdict | Anchor |
|---|---|---|---|
| 1 | **Operational Guidance Center integration defined** | ✅ | `ODR_COACHING_GUIDANCE_ADDENDUM.md § 9` — single canonical store · cross-portal · `guidance_catalog` planned · diagram shows OGC as source of truth for all guidance surfaces |
| 2 | **English guidance path defined** | ✅ | § 4 (crew-specific EN bullets · 14 crew types) + § 9 (EN i18n string tables) + § 2 (four touchpoints render EN when toggle = EN) |
| 3 | **Spanish guidance path defined** | ✅ | § 4 (ES parity required for every EN bullet) + § 9 (ES i18n string tables) + O43 + § 11 hard-gate probe |
| 4 | **Crew-specific coaching defined** | ✅ | § 4 catalog map · 14 crew types each with 4+ tips · driven by `(crew_type, primary_operation, lang)` triple |
| 5 | **Readiness coaching defined** | ✅ | § 5 vocabulary contract · "coach not punish" hard rule · existing `ReadinessSnapshot.coaching_prompts` extended with `prompt_key` link to OGC |
| 6 | **First-time onboarding defined** | ✅ | § 6 properties · 4 cards · ≤ 2 min · dismissible · bilingual · stored per `(fingerprint, project_id)` · never mandatory after dismissal |
| 7 | **Field Leadership training architecture defined** | ✅ | § 7 FL Training Center · `/field-leadership/portal/training` · Best Practices · Examples · Quality Guidance · Coaching Metrics (aggregated · never per-foreman) |
| 8 | **PM visibility architecture defined** | ✅ | § 8 PM coaching consumption surface · Completion trends · Coaching opportunity trends · Common missing information · all aggregated · zero per-foreman rows |

**8 / 8 ✅**

---

## 2 · Full doctrine inventory now totals 50

The architecture now anchors **50 locked operator doctrines**:

| Range | Doctrine theme | Locked in |
|---|---|---|
| O1–O10 | Foundational (complexity ≠ burden · simplicity · bilingual · reliability · PDF executive) | revision pass 2 |
| O11–O20 | Public-Link Device Continuity (7 signals · trust boundary · audit log) | revision pass 3 |
| O21–O35 | Field Leadership Governance (Inbox · roles · amendments · official record · signature · attachments) | revision pass 4 |
| O36–O50 | Coaching / Training / Guidance (OGC integration · crew-specific · onboarding · FL Training · PM coaching consumption) | this pass |

**50 / 50 anchored.**

---

## 3 · Critical non-punitive guarantees (re-affirmed)

The coaching system is bound by three converging doctrines:

- **O9** — Safety hard-stops; production / detail deficiencies coach
- **O27** — Completion visibility is coaching · never punishment
- **O45** — Readiness coaches · never punishes (vocabulary contract)
- **O50** — Coaching telemetry never used as performance-review evidence

These four together form a **hard cultural contract**: the ODR
coaching system cannot, by architecture, be turned into a foreman
scoreboard. The Field Leadership Training Center and the PM
coaching consumption surface are both **aggregate-only by spec**;
per-foreman exposure is grep-checked by the planned coaching probe
extensions.

---

## 4 · Single source of truth · re-affirmed

Per O41 + O43 + § 9 of the addendum:

- **One canonical guidance catalog** (Operational Guidance Center +
  i18n string tables).
- Read by:
  - ODR inline drawers (Learn More · Example Entries · Crew Tips ·
    Best Practices)
  - First-time onboarding 4-card flow
  - Help menu "Quick start"
  - FL Training Center
  - PM coaching consumption surface
- Bilingual mirroring enforced by the planned bilingual probe
  (D8) and the extended `verify_coaching_sublines.py` (this pass).

There is **no parallel guidance system** in any portal. There is
**no risk** of EN/ES divergence without the probe failing.

---

## 5 · Architecture footprint of this addendum

The coaching layer is **architecturally lightweight**:

| What was added | What was NOT added |
|---|---|
| Coaching doctrine (O36–O50) | No new ODR Mongo collection |
| `prompt_key` field on `ReadinessSnapshot.coaching_prompts` | No new audit substrate (existing `odr_section_events` carries the events) |
| Reference to `guidance_catalog` (planned · per-project) | No new role tokens |
| Reference to coaching-metrics rollup (planned · materialized) | No new portal — just sub-surfaces under FL + PM |
| Extension of `verify_coaching_sublines.py` (planned) | No new auth gate |

The complete ODR collection inventory is unchanged at 7 + 1
derived (per `ODR_SPEC_LOCK_CERTIFICATION.md § 4`).

---

## 6 · Updated readiness scorecard (after this pass)

| # | Confirmation | Verdict |
|---|---|---|
| 1–21 | (Inherited from `ODR_SPEC_LOCK_READINESS_REVIEW.md`) | ✅ × 21 |
| 22 | Operational Guidance Center integration defined | ✅ |
| 23 | English guidance path defined | ✅ |
| 24 | Spanish guidance path defined | ✅ |
| 25 | Crew-specific coaching defined | ✅ |
| 26 | Readiness coaching defined | ✅ |
| 27 | First-time onboarding defined | ✅ |
| 28 | Field Leadership training architecture defined | ✅ |
| 29 | PM visibility architecture defined | ✅ |

**29 / 29 ✅**

---

## 7 · Stop condition honoured

- ✅ No code · no routes · no collections · no UI · no probe code
- ✅ Wave M0 NOT begun
- ✅ Spec lock command NOT yet issued
- ✅ V-Prelude Observation Freeze on broader platform still intact
- ✅ Only `/app/memory/` touched in this revision pass

---

## 8 · Final verdict

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ✅  ODR ARCHITECTURE COMPLETE · 50 / 50 DOCTRINES        ║
║      ✅  29 / 29 READINESS CONFIRMATIONS                      ║
║      ✅  8 / 8  COACHING & GUIDANCE CERTIFICATIONS            ║
║                                                              ║
║   STOP — awaiting operator spec-lock authorization.          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

When ready, the operator may issue:

```
LOCK ODR SPECIFICATION · PROCEED TO M0
```

(optionally with answers to the 25 open architecture questions, or
`accept all defaults`). Until then, the agent will not begin
implementation.

_End of Coaching & Guidance Certification._
