# Dispatch Operational Volatility Map — Phase IV-BETA.5A-P4C

*iter437 · 2026-02-27*
*Status: 🟢 READ-ONLY · governance prep · NOT implementation*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Map Dispatch's **operational volatility** so governance discipline,
when applied later, does NOT accidentally slow operators down.
Dispatch is **interruption-heavy · mobile-heavy · real-time
sensitive · operationally chaotic** — by far the most volatile
surface on the platform.

## II. Volatility taxonomy (🟢)

| Volatility class | Surface | Operational consequence |
|---|---|---|
| **Polling-induced** | `DispatchBoard.jsx` 5-second silent refresh | Every screen refresh introduces re-render risk; UI must not flicker |
| **Event-induced** | New assignment created · driver responds · breakdown reported | Operator may be mid-interaction when state changes underneath |
| **Cross-portal** | `PmHaulActivityTile` shows Dispatch activity in PM | Two simultaneous editors possible |
| **Time-driven** | `ASSIGNMENT_STUCK` (≥ 30 min), `WAIT_THRESHOLD_EXCEEDED` (≥ 20 min), `NON_STANDARD_TRANSITION_PATTERN` (≥ 3 / 2 h) | Operator decisions degrade if delayed by UI friction |
| **Severity-toggling** | `BREAKDOWN_ACTIVE` flips a card from green → rose live | Eye-track must NOT have to re-find the card after a colour change |

## III. Where governance discipline could slow operators (🟢 candidate hot-spots)

| Surface | Governance temptation | Why it could slow operators |
|---|---|---|
| `severityTone()` palette | Reduce rose to slate for "calmness" | 🔴 **BAD** — rose IS the urgency signal · do NOT demote |
| 5-second poll | Add a doctrine sweep on every refresh | 🔴 **BAD** — any wasted ms on each refresh compounds |
| Assignment drawer animation | Smooth in/out animation | 🟡 mild — keep transitions ≤ 150 ms |
| Hub kicker | Lengthen sub-line for context | 🔴 **BAD** — operators want kicker scannable in < 200 ms |
| Filter chips | Add filter for low-severity items | 🟡 unsure — adds clicks · gather operator feedback |
| Status pills | Demote to slate (matches Safety P3) | 🔴 **BAD** — Dispatch status IS lifecycle, not aesthetic |

## IV. Where governance discipline would HELP (🟢)

| Surface | Improvement | Why it helps |
|---|---|---|
| Hub tile palette | Single-stripe + slate CTA pattern | Lower decorative-loudness on the non-board surfaces |
| Operational moments rail (`OperationalMomentsRail`) | Confirm only the four real signals appear (no decorative escalations) | Honour the "Nothing else fires" policy literally |
| Mobile sheet for the board | Sticky severity column | Operator scans severity first at every viewport |
| Email subject prefix consistency | `🚛 DISPATCH · …` mirroring PM/Safety subject prefixes | Inbox triage parity |
| Sub-page kickers | Mono-uppercase parity with PM/HR/Safety | Cross-portal scan rhythm preserved |

## V. Polling cadence preserved (🟢)

`POLL_MS = 5000` ms is **doctrine-locked**: no governance phase should
slow this below 5 s without explicit operator authorisation. Faster
polling is acceptable if operationally justified; slower is not.

## VI. Severity-pill discipline (🟢 already followed)

`severityTone()` in `DispatchBoard.jsx`:

```js
sev === "critical" ? "bg-rose-100 text-rose-900 border-rose-300" : ...
```

This is the **same data-bound discipline** that Safety uses for
`SEV_PILL`. Rose is reserved for `critical` only · do NOT demote.

## VII. Mobile-heavy ergonomics (🟢)

Dispatch is the platform's most mobile-heavy portal. The 5-second
poll runs ON THE PHONE while the dispatcher is in a yard. Governance
phases must:

- Preserve native `<input>` controls
- Preserve current scroll behaviour
- Keep tap targets ≥ 44 px
- Avoid adding sheets / modals that intercept input
- Avoid adding mandatory confirmations

## VIII. Doctrine reaffirmed

- ✅ READ-ONLY · zero code changes
- ✅ Volatility classes catalogued
- ✅ "Do not demote" hot-spots identified BEFORE implementation begins
- ✅ Preview only · NO production deploy
