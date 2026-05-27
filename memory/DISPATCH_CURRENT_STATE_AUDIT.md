# Dispatch Portal · Current-State Audit — Phase IV-BETA.5A-P4C

*iter437 · 2026-02-27*
*Status: 🟢 READ-ONLY AUDIT · NOT YET IMPLEMENTATION-AUTHORISED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Inventory the Dispatch portal in its current production-shape. No
code changes. The audit produces governance-ready intelligence so the
operator can authorise a future Dispatch governance phase with full
context.

## II. Pages inventoried (🟢)

| Page | LOC | Role |
|---|---|---|
| `pages/DispatchHub.jsx` | 620 | Landing dashboard — operational moments + primary actions |
| `pages/DispatchBoard.jsx` | 600 | The "haul board" — live cards · 5-second polling |
| `pages/DispatchLogin.jsx` | (modest) | Magic-link / password login |
| `pages/DispatchForgotPassword.jsx` | (modest) | Password recovery |
| `pages/DispatchResetPassword.jsx` | (modest) | Token-issued reset |
| `pages/DispatchChangePassword.jsx` | (modest) | Standard PW rotation |
| `pages/DispatchDriverQualification.jsx` | (large) | Driver-side qualification surface |
| `pages/admin/AdminDispatch.jsx` | 775 | Admin-only dispatch ops |

## III. Components inventoried (🟢)

| Component | Role |
|---|---|
| `components/dispatch/AssignmentDrawer.jsx` | Slide-out for an individual assignment |
| `components/dispatch/AssignmentCreateDrawer.jsx` | Create flow |
| `components/dispatch/AttachmentStrip.jsx` | Attachment carousel for an assignment |
| `components/dispatch/DispatchLifecycleTile.jsx` | Per-truck lifecycle status card |
| `components/dispatch/OperationalMomentsRail.jsx` | Hub-level moments rail (escalations) |
| `components/dispatch/PmHaulActivityTile.jsx` | Cross-portal — PM-side view of Dispatch hauls |

## IV. Sidebar / chrome (🟢)

| Surface | Status |
|---|---|
| Dispatch sidebar V2 | **Does NOT exist yet** — no `routes/dispatch/sidebar/SideNavV2.jsx` |
| DispatchHub kicker | `t("Dispatch Portal")` mono · already doctrine-aligned |
| DispatchHub title | `t("Dispatch Command")` |
| Hub structure | Operational moments rail · primary-actions section · operator handoffs · activity tile |

## V. Polling / refresh cadence (🟢 verified)

`pages/DispatchBoard.jsx`:

```js
const POLL_MS = 5000;                                       // line 36
const id = setInterval(() => refresh({ silent: true }), POLL_MS);  // line 380
```

**5-second poll** with a `silent` flag (no UI flicker on refresh).
This is the platform's most aggressive polling cadence — operationally
necessary; governance must NOT slow it.

## VI. Severity / escalation language (🟢)

`DispatchBoard.jsx` already uses severity-graded escalation:

| Tier | Visual | Source line |
|---|---|---|
| critical | `bg-rose-100 text-rose-900 border-rose-300` | 111 |
| (other tiers exist · cataloged for governance phase) | (mixed) | nearby |

Four signal categories explicitly identified in the source (line 521):

1. `BREAKDOWN_ACTIVE` (critical)
2. `ASSIGNMENT_STUCK` (≥ 30 min non-terminal)
3. `WAIT_THRESHOLD_EXCEEDED` (≥ 20 min in WAITING)
4. `NON_STANDARD_TRANSITION_PATTERN` (≥ 3 in 2 h per truck)

**"Nothing else fires"** is operator policy — already doctrine-aligned
escalation discipline.

## VII. Authentication boundary (🟢)

- Dispatch login flow uses standard portal-token pattern (`masci.dispatch.token`).
- Cross-portal panel `PmHaulActivityTile` shares PM context.
- Admin override path via `AdminDispatch.jsx`.

No `/api/admin/*` leakage from Dispatch context has been documented yet
(audit-pending — flagged as a governance prep follow-up).

## VIII. Color-load preview (🟢 cataloged · not measured against doctrine)

`DispatchBoard.jsx` has ~15 colour-bearing class hits (red / amber /
emerald / cyan / rose). `DispatchHub.jsx` has ~1 colour class hit.

This is **lower visual loudness than expected** given the operational
volatility — the team has clearly already practised some calmness
discipline on Dispatch. Governance will tighten the rest.

## IX. Doctrine reaffirmed

- ✅ READ-ONLY audit · zero code changes
- ✅ Dispatch implementation NOT started
- ✅ Five Dispatch-inventory docs being produced (this is doc 1 of 5)
- ✅ Preview only · NO production deploy
