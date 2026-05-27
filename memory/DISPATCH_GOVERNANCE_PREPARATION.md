# Dispatch Governance Preparation — Phase IV-BETA.5A-P4C

*iter437 · 2026-02-27*
*Status: 🟢 INVENTORY COMPLETE · governance phase NOT YET AUTHORISED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Synthesise the four Dispatch inventory documents into a single
preparation read so the operator can authorise (or veto) a future
Dispatch governance phase with complete context.

## II. Inventory artefacts (🟢 all produced this phase)

| # | Document |
|---|---|
| 1 | `DISPATCH_CURRENT_STATE_AUDIT.md` |
| 2 | `DISPATCH_OPERATIONAL_VOLATILITY_MAP.md` |
| 3 | `DISPATCH_MOBILE_WORKFLOW_REVIEW.md` |
| 4 | `DISPATCH_ESCALATION_DENSITY_ANALYSIS.md` |
| 5 | (this) `DISPATCH_GOVERNANCE_PREPARATION.md` |

## III. Dispatch portal state at audit time (🟢)

| Attribute | Value |
|---|---|
| Sidebar V2 | Does **not** exist yet |
| Hub kicker | Already doctrine-aligned (`Dispatch Portal` mono) |
| Severity discipline | Already data-bound · 4-tier pill · honoured |
| Escalation signals | Exactly **4** ("Nothing else fires" policy) |
| Polling cadence | 5 s silent refresh on the board |
| Mobile-criticality | **HIGH** — dispatcher is in the yard with a phone |
| Cross-portal entry | `PmHaulActivityTile` surfaces in PM Hub |
| Auth context | Standard portal token pattern (`masci.dispatch.token`) |
| Visible loudness | LOW relative to volatility (team already practised some discipline) |

## IV. Governance phase scope sketch (🟡 ADVISORY · not authorised)

When the operator authorises Dispatch governance, the recommended
scope is **3 sub-passes**, each individually small:

### Sub-pass 1 · `DISPATCH_INFORMATION_PRIORITY_MAP.json` + Sidebar V2

- 4-domain priority map (e.g. Board · Driver Coordination · Lifecycle Tools · Reports)
- `routes/dispatch/sidebar/SideNavV2.jsx` behind `?dispatchSidebarV2=1`
- DispatchShell conditional mount
- Coaching gate extended to govern the new domain map
- ~250 LOC + 1 test file

### Sub-pass 2 · Hub calmness pass

- Confirm Hub tiles already use the single-stripe doctrine
- Demote any decorative non-board palette
- Coaching sublines ≤ 14 words
- Mobile sticky-CTA enhancements
- ~150 LOC

### Sub-pass 3 · Cross-portal parity

- Email subject prefix `🚛 DISPATCH · …`
- Operational footer parity
- Severity-pill verification across all 4 codes
- Mobile workflow tests
- ~100 LOC + 1 test file

**Estimated total cost (3 sub-passes):** ~500 LOC and 3 small test
suites. Spread across 2-3 iterations.

## V. CRITICAL constraints (🟢 doctrine-locked · derived from inventory)

| Constraint | Source |
|---|---|
| Polling cadence MUST remain ≤ 5 s | `DispatchBoard.jsx::POLL_MS` |
| Rose `critical` pill MUST stay | `severityTone()` |
| "Nothing else fires" policy MUST hold (exactly 4 signals) | Source comment line 521 |
| Tap targets MUST stay ≥ 44 px | mobile-heavy ergonomics |
| Native `<input>` MUST be preserved | mobile-heavy ergonomics |
| Drawer transitions MUST stay ≤ 150 ms | volatility map |
| NO new 5th escalation signal | volatility map |
| NO decorative animations on severity changes | volatility map |

## VI. Recommended pre-implementation checklist (🟡 advisory)

Before authorising Dispatch governance, the operator may want to:

1. Declare a checkpoint:
   ```bash
   python3 scripts/diff_doctrine_baseline.py --append \
     --checkpoint "Pre-Dispatch governance · stable baseline"
   ```
2. Confirm Safety V2 has held its monitor band across 1 more iteration
   (P3 review classified Safety 🟢 STABLE).
3. Confirm no PM / HR / Admin doctrine regression in the meantime.
4. Authorise sub-pass 1 only, not all three at once.

## VII. What is NOT in scope (🟢 honoured)

Per the **NO Dispatch implementation** directive:

- ❌ NO Dispatch sidebar V2 built
- ❌ NO Dispatch Hub tile changes
- ❌ NO Dispatch email subject changes
- ❌ NO Dispatch mobile changes
- ❌ NO new tests against Dispatch beyond audit observations
- ❌ NO database changes
- ❌ NO auth changes

## VIII. Doctrine reaffirmed

- ✅ Inventory complete · zero code changes
- ✅ Critical constraints documented BEFORE any governance phase begins
- ✅ 3-sub-pass scope sketched · operator owns the authorisation
- ✅ Preview only · NO production deploy

# 🟢 STOP — awaiting operator authorisation before Dispatch governance begins.
