# CONTEXT GOVERNANCE STANDARD

_Phase GOVERNANCE-INFRA-1 · Workstream 6 · 2026-05-28._

This is the formal contract every shared-surface page and component
MUST satisfy. Where `SHARED_SURFACE_DOCTRINE.md` is the design rule
book, this file is the **compliance contract** — the checklist that
makes a page "context-governed".

Companion machine-readable matrix:
`SHARED_SURFACE_CONTEXT_MATRIX.json`.

---

## The Six Contract Fields

| Field | Description |
|---|---|
| **origin_context** | The portal context the surface was opened from. ALWAYS declared by `setPortalContext()` on hub mount; never inferred at navigation time. |
| **return_path** | How a "Back" affordance computes its destination + label. MUST use `useReturnContext()`. |
| **capability_inheritance** | Which capability bundle the surface consumes (`getPoCapabilities`, `getRfiCapabilities`, ...). |
| **portal_identity** | How the surface advertises which portal hosts it (shell + label + theme). |
| **authority_visibility** | Which controls render when caps are OFF. Doctrine: **hidden, not greyed**. |
| **shell_expectation** | Which shell wraps the surface OR how it announces portal identity inline. |

---

## Per-Surface Contract Matrix

### `/po-requests` (live · TRUST-PO-1)
* origin_context: `field-leadership`, `pm`, `hr`, `admin` (declared by hub mount)
* return_path: `useReturnContext()` planned — currently hub-relative
* capability_inheritance: `getPoCapabilities()`
* portal_identity: inline "Authority & Visibility" banner + portal-aware nav
* authority_visibility: hidden when capability OFF (no grey)
* shell_expectation: raw page (predates shell); inline identity banner

### `/incidents/:id` (live · iter443 + STABILIZATION-FINAL)
* origin_context: any (`safety`, `pm`, `admin`, `field-leadership`)
* return_path: `useReturnContext()` ✅ wired
* capability_inheritance: `getSafetyCapabilities()` — incidents are safety records (same primitive as meetings)
* portal_identity: shell-aware
* authority_visibility: hidden-not-greyed
* shell_expectation: portal-specific shell

### `/capa/:id` (live · STABILIZATION-FINAL)
* origin_context: any of safety / pm / hr / admin (CAPAs not surfaced to field-leadership by doctrine)
* return_path: `useReturnContext()` — wired on the safety corrective-actions list
* capability_inheritance: `getCapaCapabilities()` (lib/capaCapabilities.js)
* portal_identity: shell-aware
* authority_visibility: hidden-not-greyed
* shell_expectation: portal-specific shell

### `/meetings/:id` (live · STABILIZATION-FINAL)
* origin_context: any of safety / pm / admin / field-leadership
* return_path: `useReturnContext()` ✅ wired
* capability_inheritance: `getSafetyCapabilities()` (lib/safetyCapabilities.js)
* portal_identity: shell-aware
* authority_visibility: hidden-not-greyed
* shell_expectation: shell-aware

### `/inspections/:id` (live · STABILIZATION-FINAL)
* origin_context: any of safety / pm / admin / field-leadership
* return_path: `useReturnContext()` ✅ wired
* capability_inheritance: `getInspectionCapabilities()` (lib/inspectionCapabilities.js)
* portal_identity: shell-aware
* authority_visibility: hidden-not-greyed
* shell_expectation: portal-specific shell

### `/rfis` (planned · Phase V.1)
* All six fields MUST be defined at MVP merge.

### `/schedule` (planned · Phase V.3)
* All six fields MUST be defined at MVP merge.

---

## Compliance Gate

A shared surface is **context-governed** when:

1. All six contract fields are non-TBD in this matrix.
2. The corresponding `data-testid="*-back-link"` matches the `useReturnContext` label contract.
3. The capability bundle is used by every actionable button.
4. The Authority Mismatch Probe gate passes for the surface's file.
5. At least one regression test asserts the context-switch behavior.

A surface marked TBD here is acceptable IF it pre-dates this doctrine
AND has no observed governance defects. Wave 3 doctrine extension
will close all TBD entries before Phase V begins.

---

## Cross-Portal State Lifecycle

When the operator switches portals MID-SESSION, every shared surface
on screen MUST re-derive its context. Implementation gates:

* `setPortalContext()` writes to sessionStorage AND emits a
  `storage` event (browsers do this automatically for `setItem`).
* Shared surfaces SHOULD subscribe via `useEffect` + storage listener
  on `masci.portal-context` and recompute their capabilities on
  change.
* No primitive currently subscribes — capabilities are derived at
  mount. Wave 3 will add the `useCapabilities()` reactive hook.

---

## Anti-Patterns

* Capability flag read in render but never re-derived on prop change.
* Hardcoded "Back" label.
* Portal-specific button text rendered conditionally on token presence.
* `<Sidebar />` mounted from a different portal than the route URL.
* Shell prop drilling overriding portal context.

The Authority Mismatch Probe catches the first; manual review +
regression tests catch the rest.
