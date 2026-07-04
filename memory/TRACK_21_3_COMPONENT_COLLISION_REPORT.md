# TRACK 21.3 · Phase E · Component Collision Report (Documentation-Only Half)

**Date:** 2026-07-04
**Closes:** documentation portion of TD-21.2-C03. **Merges deferred** — behavior-parity proof required.

## The 5 pairs

| # | Component name | Path A | Path B | Behavior parity? | Decision |
|---|---|---|---|---|---|
| 1 | `EmptyState.jsx` | `frontend/src/design-system/EmptyState.jsx` (43 lines · Track 13.5A Phase B1 primitive) | `frontend/src/components/EmptyState.jsx` (48 lines · Iter B unification) | **NOT PROVEN** — both accept an `icon` + `message` prop but with slightly different visual tokens (spacing scale, icon size). Merging risks a subtle UX shift on the ~40 pages that consume one of them. | **KEEP BOTH** — rename design-system primitive to `EmptyStatePrimitive.jsx` in Track 21.y with a codemod that rewires imports. Not this track. |
| 2 | `StatusBadge.jsx` | `frontend/src/components/StatusBadge.jsx` (generic status pill) | `frontend/src/components/oa/StatusBadge.jsx` (Operational Attachments domain-specific status pill with different color mapping) | **NOT** — the OA version encodes attachment-specific states (`draft`, `submitted`, `superseded`) that the generic version doesn't know about. | **KEEP BOTH** — rename the OA one to `OaStatusBadge.jsx` for clarity. Deferred to Track 21.y. |
| 3 | `DraftStatusPill.jsx` | `frontend/src/components/DraftStatusPill.jsx` (36 lines · basic "Saved as draft" indicator) | `frontend/src/lib/resiliency/DraftStatusPill.jsx` (106 lines · Iter440 P0 field-incident remediation — includes retry timer + network-status detection) | **NOT** — the resiliency version is a superset. | **MERGE (superset wins)** — deferred to Track 21.y with an import codemod. Blocked by behavior test needed for the 36-line variant's 3 consumers. |
| 4 | `HelpTip.jsx` | `frontend/src/components/HelpTip.jsx` (238 lines · Iter209 Contextual Operational Guidance — includes portal-aware content lookup, Trust Spine event on open) | `frontend/src/components/ui/HelpTip.jsx` (54 lines · Iter148 basic info icon) | **NOT** — the Iter209 version is a superset with side effects (audit write). | **KEEP BOTH** — the UI-primitive version is intentional as a lightweight cousin for places that shouldn't emit audit events. Rename to `InfoTip.jsx` in Track 21.y for clarity. |
| 5 | `SideNavV2.jsx` | `frontend/src/components/admin/sidebar/SideNavV2.jsx` | `frontend/src/components/pm/sidebar/SideNavV2.jsx` | **NOT** — same architectural pattern applied to two different portals with different route lists, different permission gates, different collapse states. | **KEEP BOTH** — this is the correct pattern (portal-scoped nav). Not a collision to fix. |

## Verdict

**Zero merges in this track.** Every pair either (a) needs a behavior-test harness before merge (pairs 1, 3) or (b) is an intentional portal/domain variant that should be renamed for clarity (pairs 2, 4, 5).

## Class-C status

**TD-21.2-C03 → REMAINS OPEN** with detailed per-pair decisions above. Target track: **21.y** (frontend refactor). Owner: Frontend team.

**Zero code touched. Zero drift.**
