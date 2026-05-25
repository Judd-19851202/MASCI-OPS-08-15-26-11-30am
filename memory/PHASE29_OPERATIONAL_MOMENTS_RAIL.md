# PHASE 29 · Operational Moments Rail
## iter431 · 2026-05-25

## What it is
A read-only, chronological vertical timeline inside
`AssignmentDrawer.jsx` that surfaces operational continuity truth for
a single assignment — merged from FOUR existing collections, NO new
collection introduced.

## Data sources merged
1. **`dispatch_assignments.state_history`** — every lifecycle state
   change (assigned → en_route → on_site → completed / breakdown).
2. **`dispatch_assignments.recovery_history`** — every Shop recovery
   sub-state change (waiting_on_parts → operational_test →
   returned_to_service).
3. **`dispatch_continuity_events`** — explicit operational events
   (breakdowns reported, dispatch acknowledgements, etc).
4. **`operational_attachments`** — every photo / load proof / breakdown
   evidence file uploaded.

## API
- New endpoint:
  `GET /api/dispatch/operational-moments/by-assignment/{assignment_id}`
- Admin / Dispatch / Shop / PM / Safety / Driver-session all
  authorised — read is operational truth, never identity gated.
- Returns:
  ```jsonc
  {
    "assignment_id": "asgn-1",
    "count": 12,
    "moments": [
      {"kind": "lifecycle", "ts": "...", "label": "State → assigned",
       "actor": "DispatchOp", "actor_role": "dispatch", ...},
      {"kind": "continuity", "ts": "...", "label": "Breakdown reported", ...},
      {"kind": "attachment", "ts": "...", "label": "Photo attached · breakdown_photo", ...},
      {"kind": "recovery", "ts": "...", "label": "Recovery → waiting_on_parts", ...}
    ]
  }
  ```
- One round-trip · backend does the merge + sort so the FE never
  juggles 4 GETs and 4 loading states.

## Frontend
- `components/dispatch/OperationalMomentsRail.jsx` (NEW · ~180 LOC)
- Mounted inside `AssignmentDrawer.jsx` just above the existing
  AttachmentStrip.
- One `<ol>` · per-row icon + accent + timestamp + actor + detail.
- Calm operational icons: `CircleDot` (lifecycle), `Wrench` (recovery),
  `Activity` (continuity), `Camera` (attachment).
- Bilingual via `useT()`. Common lifecycle / recovery labels mapped to
  short EN/ES strings.

## Doctrine
- Read-only · no actions, no buttons, no alerts.
- Mobile-first · vertical · no graphs.
- Calm operational language: "Driver started", "Returned to service",
  "Photo attached" — never "feed" or "activity".
- No new collection. Reuses what's already operational truth.

## What this is NOT
- ❌ An activity feed
- ❌ A notifications surface
- ❌ A chat
- ❌ An analytics view
- ❌ A KPI strip
