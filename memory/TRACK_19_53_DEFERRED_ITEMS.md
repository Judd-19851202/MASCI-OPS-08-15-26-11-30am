# TRACK 19.53 · Deferred Items

## P2 #9 · Guidance Center role-based restructure — DEFERRED

### Scope from the roadmap
> "Guidance Center role-based restructure — pivot from feature-list to
> workflow-list. Scope: L. OI: N/A. Risk: LOW."

### Why deferred
- **LARGE scope.** The current Guidance Center (`OperationalGuidanceCenter.jsx`) is server-driven. Sections + articles are pulled from `/api/guidance/*` and rendered exactly as the backend groups them. The current backend groups articles by **portal + cross-cutting section**, not by **workflow**.
- A true "role → workflow" pivot requires a new backend grouping (e.g., a `workflow` field on each article, a `/api/guidance/workflows` collection, RBAC-aware surfacing per role). That is **new backend logic**, which Track 19.53 explicitly forbids (see the "ABSOLUTE NON-NEGOTIABLES" block: *"DO NOT CREATE new command center engine, new attention systems, new backend routes"*).
- Attempting to force a workflow-list purely on the frontend would produce a hard-coded static tree that:
  - drifts from the server-driven article catalog,
  - breaks RBAC (server currently decides which articles a role sees),
  - duplicates data (frontend list vs. server list).

Any of those is a zero-drift violation.

### Follow-up recommendation
- Schedule as **Track 19.54 · Guidance Workflow Restructure** (or roll into a broader Guidance overhaul).
- Backend delta needed:
  - Add `workflow: string | null` to the article schema (nullable, backward-compatible).
  - Add `GET /api/guidance/workflows` returning a role-scoped list of workflow → article groupings.
  - Add a lock test that no article is left unmapped for privileged roles.
- Frontend delta:
  - New "By workflow" tab on `OperationalGuidanceCenter` consuming the new endpoint.
  - Preserve the existing "By portal" / "Cross-cutting" tabs so classic navigation stays.
- Risk: still LOW, but not surgical enough for the current audit-execution track.

### Interim mitigation (already true today)
- The Guidance Center already exposes a portal-first grid (Safety + Dispatch first-class) and search, so a superintendent can already reach their portal's articles in ≤ 2 clicks.
- The Track 19.51 audit's `HUMAN_PERSONA_WALKTHROUGH` recorded this as "❌ major" only for the workflow-pivot ambition — not for functional usability.

## No other P2 items deferred
Items #6, #7, #8, #10, #11, #12 were all executed surgically in Track 19.53.
