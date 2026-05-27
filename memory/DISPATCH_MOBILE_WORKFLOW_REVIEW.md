# Dispatch Mobile Workflow Review — Phase IV-BETA.5A-P4C

*iter437 · 2026-02-27*
*Status: 🟢 READ-ONLY · mobile workflow inventory*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Inventory Dispatch's mobile workflows so governance discipline, when
applied later, **preserves operator speed at 390 × 844 viewports**.

## II. Mobile-critical surfaces (🟢)

| Surface | Mobile critical? | Why |
|---|---|---|
| `DispatchBoard.jsx` | 🔴 yes | Dispatcher is in the yard with a phone |
| `DispatchHub.jsx` | 🟡 medium | Used both at desktop and on the phone |
| `AssignmentDrawer.jsx` | 🔴 yes | Most-frequent interaction on the phone |
| `AssignmentCreateDrawer.jsx` | 🟡 medium | Used both at desktop and on the phone |
| `OperationalMomentsRail.jsx` | 🔴 yes | Where the dispatcher learns "something is wrong" |
| `DispatchDriverQualification.jsx` | 🟡 medium | Driver-side · used on phone |

## III. Operator workflows on mobile (🟢)

| Workflow | Steps | Sensitive to |
|---|---|---|
| Triage a stuck assignment | Read severity pill → tap assignment → read history → re-assign or revoke | Pill colour fidelity · drawer-open speed |
| Acknowledge a breakdown | Read rose pill → tap card → confirm acknowledgement | Tap target size · pill colour |
| Create a new assignment | Tap "+" → fill 4 fields → submit | Form input ergonomics |
| Cancel an assignment | Tap assignment → cancel → confirm | Confirmation prompt clarity |
| Revoke a magic-link session | Tap assignment → revoke | One-tap recovery |
| Issue a magic-link to driver | Tap assignment → issue link | One-tap re-issuance |

## IV. Mobile pitfalls to avoid in any future governance phase (🟢)

- 🔴 Do **NOT** add page-level modals that block the board view
- 🔴 Do **NOT** add a confirmation toast that auto-dismisses after < 4 s
- 🔴 Do **NOT** introduce keyboard-only shortcuts (mobile users have no keyboard)
- 🔴 Do **NOT** demote rose `critical` pill to slate
- 🔴 Do **NOT** push tap targets below 44 px
- 🔴 Do **NOT** add hover-state-only affordances (no hover on mobile)
- 🔴 Do **NOT** introduce parallax / scroll-driven animations

## V. Mobile-ergonomics opportunities (🟢)

These are pure improvements, NOT yet authorised:

| Item | Benefit |
|---|---|
| Sticky severity column on the board | Operator scans urgency first |
| Bottom-anchored "Issue work" CTA on the Hub at mobile width | One-tap from any scroll position |
| Drawer animations capped at 150 ms | Maintains responsiveness perception |
| Mobile-specific "5 s refresh" indicator chip | Lets operator know the data is fresh |
| Severity-grouped board view on mobile | Critical at top, low at bottom |

Each item is a **future** improvement requiring operator authorisation
in a later Dispatch governance phase.

## VI. Doctrine reaffirmed

- ✅ READ-ONLY · zero code changes
- ✅ Mobile-critical surfaces inventoried
- ✅ Hot-spots cataloged BEFORE implementation begins
- ✅ Preview only · NO production deploy
