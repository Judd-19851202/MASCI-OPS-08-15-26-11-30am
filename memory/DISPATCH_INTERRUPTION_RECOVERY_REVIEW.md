# Dispatch Interruption-Recovery Review — Phase IV-BETA.5A-P5B

*iter437 · 2026-02-27*
*Status: 🟢 INTERRUPTION RECOVERY PRESERVED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Dispatch is interruption-heavy. Operators may be mid-action when the
state changes underneath them (new assignment, severity flip,
breakdown reported). Confirm sub-pass 1 changes do NOT degrade
interruption recovery.

## II. Interruption events catalogued (🟢)

| Event | Source | Recovery surface |
|---|---|---|
| New assignment arrives | 5 s poll · live mutation | Hub operational rail · card animation absent (intentional) |
| Severity flip (green → rose) | 5 s poll · severity recompute | Card border + pill colour change · NO animation |
| Breakdown reported | Driver-side action · 5 s poll | Operational moment fires on rail · severity = critical |
| Magic-link revoked | Operator action | Drawer closes · card refreshes |

## III. Interruption-recovery affordances preserved (🟢)

| Affordance | Why critical | Status |
|---|---|---|
| 5 s silent refresh | Dispatcher's awareness of yard state | 🟢 preserved (`POLL_MS = 5000`) |
| `silent` refresh flag | No UI flicker during the operator's interaction | 🟢 preserved |
| No assignment-card animation | Eye does NOT need to re-find a card after refresh | 🟢 preserved (no animation added) |
| Drawer state persistence | Operator's open drawer stays open across refresh | 🟢 preserved (no drawer reset added) |
| Severity sort order stability | Critical stays at the top | 🟢 preserved |
| `OperationalMomentsRail` ordering | Most-recent-first | 🟢 preserved |

## IV. Sub-pass 1 affordances examined (🟢)

The sidebar V2 mounts behind a flag. When mounted:

- It does **not** intercept refreshes.
- It does **not** intercept severity flips.
- It does **not** intercept drawer events.
- It does **not** mount any timer or interval of its own.
- It is **purely declarative navigation chrome** — same shape as HR/Safety/PM V2.

Therefore: interruption recovery is **unchanged** by construction.

## V. What was deliberately NOT added (🟢 honoured)

Per directive — sub-pass 1 must NOT introduce these even though
they were tempting:

- ❌ Toast notification on new assignment ("Dispatcher already saw the rail")
- ❌ Card flash / pulse animation on severity flip ("Animation steals eye-track")
- ❌ Audio cue on critical breakdown ("Yard noise drowns it · also: scope creep")
- ❌ Sidebar badge count of unresolved escalations ("Sidebar is navigation, not signal")
- ❌ Auto-open drawer when assignment becomes critical ("Operator must stay in control")

## VI. Recommended future sub-pass items (🟡 advisory · NOT authorised)

| Item | Sub-pass target |
|---|---|
| Mobile sticky severity header | Sub-pass 2 (mobile ergonomics) |
| Drawer state restoration test | Sub-pass 2 (test only) |
| Refresh-during-interaction Playwright assertion | Sub-pass 2 (test only) |

## VII. Doctrine reaffirmed

- ✅ 5 s poll preserved
- ✅ Silent refresh preserved
- ✅ No animation added · eye-track unchanged
- ✅ No timer/interval added in V2 sidebar
- ✅ Operator stays in control of every interaction
- ✅ Preview only · NO production deploy
