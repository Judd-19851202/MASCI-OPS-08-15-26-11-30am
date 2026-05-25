# PHASE 30 · Role Cognition Convergence
## iter432 · 2026-05-25 · PLANNING DOC

## Scope decision (operator-approved)
Path (a) + Option (iii): **NOT a full rebuild of all 7 hubs**. Phase 30
locks in the doctrine; engineering of the per-role "operational
attention" component lands as a follow-on phase.

## Hub-by-hub doctrine
Every hub MUST surface, in this priority order:
1. **What needs my attention right now** — the smallest possible
   list of operational truth requiring my role.
2. **What's stuck downstream of me** — continuity into the next
   role's surface.
3. **What's stable** — implicit · the absence of red is the absence
   of red. Calm doctrine.

### Dispatch
- Stuck assignments (state ≥ X minutes without transition)
- Active recoveries needing dispatch acknowledgement
- Reassignment continuity events from last 24h

### Shop
- Recoveries in `waiting_on_parts`
- Recoveries past `operational_test` not yet `returned_to_service`
- Open breakdown evidence with no acknowledgement

### PM
- Hauls disrupted by active recoveries
- Project-level continuity events from last 24h
- Equipment unavailability windows overlapping production

### Field Leadership
- Today's planned vs active crews (continuity, not productivity)
- Open Field Memory notes scoped to today's projects
- Recent recovery events in active projects

### Safety
- Active inspection follow-ups
- Recent equipment-checkout failures (DVIR pattern)
- Open Field Memory notes tagged with safety conditions

### HR
- Open onboarding tasks
- Documents needing acknowledgement
- (No operational-attention duplication of Dispatch/Shop — HR is
  scoped to people)

### Admin
- Atlas / R2 health roll-up from `/api/admin-strict/diag/persistence-health`
- Last weekly digest send result
- Pending stability-sweep candidates count

## Engineering doctrine (when this lands)
- Each "operational attention" component is **additive** — never a
  replacement for the existing hub surface.
- Components are **server-rendered counts**, not live-polling
  widgets. One GET per hub on mount. No websocket.
- Each component is **role-locked** — admin cannot see PM's view by
  accident.
- All components are **dismissible per session** (calm doctrine ·
  no nags).
- All counts read from existing endpoints/collections — **no new
  collection** for role-cognition.

## What this phase did NOT do
- ❌ Did NOT touch any of the 7 hub pages
- ❌ Did NOT introduce role-cognition collections
- ❌ Did NOT redesign sidebars / nav / chrome

## Acceptance gates (when engineering lands)
- ☐ Parity-lock for every existing hub: home renders, no console
  errors, no regression in 6-hub touch matrix.
- ☐ No new global state · no new Redux/Zustand/Context wiring.
- ☐ Each hub `<RoleCognitionStrip />` component is ≤ 120 LOC.
- ☐ EN ↔ ES toggling works on every new label.
