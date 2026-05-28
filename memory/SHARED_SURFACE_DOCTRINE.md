# SHARED SURFACE DOCTRINE

_Phase GOVERNANCE-INFRA-1 · Workstream 4 + 6 · 2026-05-28._

A **Shared Surface** is any page or component rendered under multiple
portals. The canonical example is `/po-requests` — invoked from
Admin, PM, HR, AND Field Leadership. Shared surfaces are where
trust drift most commonly originates because the same React tree
ships approver controls to every caller unless rigorously gated.

Companion machine-readable matrix:
`SHARED_SURFACE_CONTEXT_MATRIX.json`.

---

## Origin Context

Every navigation INTO a shared surface MUST declare its origin:

| Origin signal | When to use | Example |
|---|---|---|
| `setPortalContext("...")` on hub mount | **Always** for portal hubs | `AdminHub` → `"admin"` |
| `location.state.from` | Mid-session jump from a non-hub page | `IncidentsDashboard → ViewIncident` |
| `?from=...` query param | Cross-portal deep links | `/po-requests?from=safety` |
| Pathname derivation | Fallback only | `/safety-portal/incidents` → `"safety"` |

Doctrine: portal context is **declared on hub mount**, not derived on
demand. The hub knows; the shared surface trusts.

---

## Return-Path Contract

Every shared surface MUST emit a context-aware "Back" affordance:

* Use `useReturnContext()` (lib/returnContext.js).
* Never hardcode `<- INCIDENTS` etc. (the iter443 P1 governance issue).
* If origin is unresolvable, fall back to the most recent portal hub.

---

## Capability Inheritance

Shared surfaces NEVER override capability scope. They consume the
primitive bundle from `getPoCapabilities()` (or future sibling).
Doctrine table:

| Portal context | Inherits from | Owns local override? |
|---|---|---|
| field-leadership | submitter caps only | NO |
| pm | approver caps (no close/cancel) | YES |
| hr | approver caps (no close/cancel) | YES |
| admin | full caps | YES |
| safety | none on `/po-requests` (read-only) | NO |
| shop | none on `/po-requests` (read-only) | NO |
| unknown | conservative (submitter only if any token) | NO |

---

## Portal Identity in Chrome

Shared surfaces SHOULD display their host portal's chrome:

* Sidebar / nav matches the portal context.
* Header logo / breadcrumb references the host portal.
* Background palette stays neutral (slate) — never an alarm color.

If a shared surface CAN'T render the host portal's chrome (e.g.,
print view), it MUST display a calm "PORTAL: ADMIN" label inline so
the operator never mistakes which portal they're in.

---

## Authority Visibility

Doctrine: **An action you cannot perform should NOT appear on screen.**
This is the core lesson of TRUST-PO-1.

* No "permission denied" toasts.
* No greyed-out buttons.
* No "Admin only" labels on hidden buttons.
* A capability OFF means the affordance is **not rendered**, period.

Rationale: greyed-out buttons invite curiosity ("why can't I?") and
imply hidden privileged paths. Calm doctrine: if it's not yours,
you don't see it.

---

## Shell Expectations

Shared surfaces SHOULD wrap in the host portal's shell where one
exists (`AdminShell`, `PmShell`, `SafetyShell`, etc.). For pages
that have historically been raw (e.g., `/po-requests` predates
shells), the shared surface MUST at minimum:

* Honor the portal-context theme tokens.
* Surface the host portal's notification bell.
* Surface the host portal's home link.
* Never display chrome from a DIFFERENT portal.

---

## The Three Failure Modes

1. **Authority bleed** — controls rendered without the capability gate.
   Caught by Workstream 1 probe.
2. **Context confusion** — wrong "Back" label, wrong sidebar, wrong
   theme.  Caught by `useReturnContext()` adoption + capability tests.
3. **State drift** — shared surface caches a state that another
   portal has invalidated. Each surface MUST refresh on portal-context
   change (subscribe to a future `onPortalContextChange` event).

---

## Practical PR Checklist (shared surface)

* [ ] Consumes a capability bundle (`getPoCapabilities()` or sibling).
* [ ] Wraps in host portal's shell OR displays inline portal label.
* [ ] Uses `useReturnContext()` for any "Back" affordance.
* [ ] Registers in `TRUST_SURFACES.json` with its capability list.
* [ ] Passes `python3 scripts/authority_mismatch_probe.py --gate`.
* [ ] Has at least one capability-scope regression test in
      `backend/tests/pw_suite/`.
* [ ] No greyed-out / disabled approver controls — caps OFF means
      not rendered.
