# Operational Guidance Center · Audit (Track 18.04)

> Coverage report of the `/guidance` Operational Guidance Center after
> the Platform Language Migration. Every primary workspace has a
> Constitutional-language overview article; per-feature deep dives keep
> their established feature names (which are not workspace names).

---

## Workspace overview coverage

| Workspace | Identity article | Title (post-migration) | Status |
|---|---|---|:---:|
| Transportation Operations | `portal-dispatch-identity` | Transportation Operations — Overview | ✅ |
| Project Management | `portal-pm-identity` | Project Management — Overview | ✅ |
| Human Resources | `portal-hr-identity` | Human Resources — Overview | ✅ |
| Safety Operations | `portal-safety-identity` | Safety Operations — Overview | ✅ |
| Shop Operations | `portal-shop-identity` | Shop Operations — Overview | ✅ |
| Administration | `portal-admin-identity` | Administration — Overview | ✅ |
| Field Leadership | `portal-leadership-identity` | Field Leadership — Overview (existing) | ✅ |

## Workspace training-track coverage

| Workspace | Guidance card | Title (post-migration) |
|---|---|---|
| Transportation Operations | `portal-dispatch` | Transportation Operations Guidance |
| Project Management | `portal-pm` | Project Management Guidance |
| Human Resources | `portal-hr` | Human Resources Guidance |
| Safety Operations | `portal-safety` | Safety Operations Guidance |
| Shop Operations | `portal-shop` | Shop Operations Guidance |
| Administration | `portal-admin` | Administration Guidance |

## Deep-dive feature coverage (sample · all retained as-is)

| Feature | Article id | Why preserved |
|---|---|---|
| Dispatch Board | `dispatch-board-deep` | "Dispatch Board" is a feature name, not a workspace name |
| Live Map | `dispatch-live-map` | Feature name |
| Haul Ledger | `dispatch-haul-ledger` | Feature name |
| Pre-Op Inspections | `shop-preop-deep` | Feature name |
| JHP | `safety-jhp` | Industry term |
| Trench Safety | `safety-trench` | Industry term |
| Daily Reports | `dr-deep` | Feature name |
| Driver Qualification | `dispatch-driver-qualification` | Feature name |
| Truck Readiness | `dispatch-truck-readiness` | Feature name |
| Carrier Packet Review | `dispatch-carrier-packet` | Feature name |
| Orientation | `dispatch-orientation` | Feature name |
| Right Rail / Related Records | `relationships-right-rail` | Canonical feature name (Track 18.00 Phase D) |
| Mission Control | `transportation-mission-control` | Canonical feature name (Track 18 Phase E) |
| Search | `platform-search` | Canonical feature name |

## "First-day employee" coverage

| Audience | Article(s) | Status |
|---|---|:---:|
| HR new hire | `onboard-hr-first-week` | ✅ |
| Safety new hire | `onboard-safety-first-week` | ✅ |
| Shop new hire | `onboard-shop-first-week` | ✅ |
| PM new hire | `onboard-pm-first-week` | ✅ |
| Dispatch new hire | `onboard-dispatch-first-week` | ✅ |
| Field Leadership new hire | `onboard-leadership-first-week` | ✅ |
| Administration new hire | `onboard-admin-first-week` | ✅ |

## Troubleshooting coverage

Each workspace has a `tshoot-{workspace}-login` companion (e.g., `tshoot-hr-login`, `tshoot-safety-login`) — preserved without change. The login-troubleshooting article wording references legacy names for muscle-memory continuity; titles align with the canonical workspace name.

---

## Gap-fill recommendations (future tracks)

1. Soft-edit BODY prose of identity articles to align with canonical names (article TITLES are already aligned).
2. Author a one-page **Platform Vocabulary Reference** card linked from `/guidance` for new hires.
3. Build a small **What changed?** changelog tile on `/guidance` summarizing the 18.04 cutover for returning users.

---

## How to verify

```bash
python -m pytest backend/tests/test_track_18_04_platform_language_migration.py::test_36_guidance_center_top_articles_renamed
python -m pytest backend/tests/test_track_18_04_platform_language_migration.py::test_37_guidance_page_workspace_chips_use_canonical_names
```
