# GOVERNANCE PRIMITIVES STANDARD

_Phase GOVERNANCE-INFRA-1 · Workstream 4 · 2026-05-28._

These are the reusable primitives that encode platform governance.
**Future shared-surface code MUST consume these primitives instead of
re-rolling ad-hoc conditional logic.**

---

## The Five Primitives

### 1 · `lib/portalContext.js` (live · TRUST-PO-1)
* Declares **which portal the operator is currently in**.
* Source of truth: `sessionStorage.masci.portal-context`.
* Read with `getPortalContext()`; write with `setPortalContext(name)`.
* Capability decisions on shared surfaces MUST consult this FIRST,
  token presence SECOND.
* Each portal hub mount declares its context on entry; navigating
  away does NOT clear (entering a different hub overwrites).

### 2 · `lib/poCapabilities.js` (live · TRUST-PO-1)
* Pattern template for capability-scoped rendering.
* Returns explicit per-action flags, not a single "isApprover" boolean.
* Field-Leadership context FORCES every approver capability OFF
  regardless of token coexistence.
* Each new workflow with authority gradients SHOULD add a sibling
  `lib/<workflow>Capabilities.js` following this pattern.

### 3 · `lib/returnContext.js` (live · iter443)
* Computes a context-aware "Back" link label on any shared view page.
* Honors `location.state.from`, then query params, then pathname
  derivation. Never hardcoded.
* Future shared view pages (ViewCAPA, ViewInspection, ViewMeeting)
  MUST adopt this — Wave 3 doctrine extension.

### 4 · `lib/resiliency/useFormDraft.js` (live · TRUST-1)
* Form-level autosave with the full survivability contract baked in:
  IDB write · device-scoped actorId · idempotency key persistence ·
  visibility/pagehide lifecycle · quota probe · prior-usage beacon.
* Returns the complete state tuple: `pendingDraft`, `loaded`,
  `draftStatus`, `lastSavedAt`, `lastError`, `quotaPressure`,
  `restore`, `discard`, `commit`.
* Every new long-form workflow MUST use this hook — never
  re-implement autosave.

### 5 · `lib/resiliency/resiliencyQueue.js` (live · TRUST-1 TF-011)
* Shared offline queue with `onQueueItemSettled(idem, cb)` callback
  registry for deferred-commit truthful-state.
* `enqueueUpload(req)` returns either an immediate response OR
  schedules retry with exponential back-off (max 5 tries).
* Drains on focus / online.
* New POST endpoints that need offline-tolerance MUST queue through
  this primitive — never custom retry logic.

---

## Primitive Authoring Rules

When a new primitive is proposed:

1. **Single responsibility** — one doctrine concern per module.
   No "kitchen sink" governance modules.
2. **Pure where possible** — primitives MUST be unit-testable
   without React mount.
3. **Read-side first** — primitives ship as readers (`get*`) before
   adding writers; a new primitive should never have side-effects
   in its first PR.
4. **Test seam exported** — every primitive exports an
   `__TESTING__` object so regression tests don't need to monkey-
   patch internals.
5. **Backend mirror documented** — primitives that gate UI authority
   MUST document their backend enforcement counterpart in
   `TRUST_SURFACES.md`.

---

## Anti-Patterns the Probe Catches

* `isPm() || isHr() || isAdmin()` (token coexistence) — see
  `scripts/authority_mismatch_probe.py` for the regex.
* Inline ternary gates on action buttons.
* `const canX = isPm() || isAdmin()` derivations outside the
  capability layer.
* Authority controls inside shared portal pages that haven't been
  routed through `getPoCapabilities()` (or future sibling).

---

## Sibling Capability Layers (planned · NOT yet implemented)

Phase V will require these sibling primitives — they MUST follow the
poCapabilities template exactly:

* `lib/rfiCapabilities.js` — `rfi.create` · `rfi.send` · `rfi.respond`
  · `rfi.close` · `rfi.escalate`.
* `lib/scheduleCapabilities.js` — `schedule.upload` · `schedule.link`
  · `schedule.publish`.
* `lib/safetyCapabilities.js` — `safety.investigate` · `safety.close`
  · `safety.escalate` · `incident.create`.
* `lib/notificationCapabilities.js` — `notif.acknowledge` ·
  `notif.dismiss` (these are user-facing, so the layer is mostly
  about discoverability).

---

## How to add a new primitive (PR template)

1. Create `lib/<name>.js` with named exports + `__TESTING__` seam.
2. Add it to `GOVERNANCE_PRIMITIVES_STANDARD.md` (this file).
3. Add a stanza to `TRUST_SURFACES.md` if the primitive gates a
   trust surface.
4. Add at least one regression test asserting the primitive's
   contract.
5. Wire any consuming pages so the probe stops flagging
   token-coexistence patterns on those pages.
