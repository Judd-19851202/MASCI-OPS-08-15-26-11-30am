# WP16 Navigation Trace Register

Date: 2026-07-29

## Phase 1 status
- Navigation trace work has **not** yet begun at item-level depth.
- This register is created in Phase 1 so later phases can append evidence without changing the runtime.
- Current known direct-entry traces come from manual preview openings, not sidebar/menu activation.

## Exact current totals
| Metric | Exact total | Note |
| --- | ---: | --- |
| Navigation elements traced from real in-UI launch points | 0 | Direct URL openings do not count as complete navigation-element traces. |
| Direct URL evidence openings recorded | 16 | These are route openings, not item-level nav traces. |
| Dead-end screens documented | UNKNOWN — evidence insufficient | Requires navigation phase. |
| Screens without clear return path documented | UNKNOWN — evidence insufficient | Requires navigation phase. |

## Seed rows from current accepted evidence
| Trace ID | Visible label | Icon | Source screen | Destination | Role context | Opened successfully? | Destination matched label? | Duplicate destination? | Intuitive? | Return path confirmed? | Back / Close / Cancel / Home available? | Operator trap risk | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAV-SEED-001 | Admin login submit | — | `/admin/login` | `/admin` | Admin authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-ADMIN-LOGIN.jpeg`, `WP16-EVID-ADMIN-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
| NAV-SEED-002 | PM login submit | — | `/pm/login` | `/pm` | Project Management authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-PM-LOGIN.jpeg`, `WP16-EVID-PM-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
| NAV-SEED-003 | HR login submit | — | `/hr/login` | `/hr` | HR authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-HR-LOGIN.jpeg`, `WP16-EVID-HR-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
| NAV-SEED-004 | Safety login submit | — | `/safety-portal/login` | `/safety-portal` | Safety authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-SAFETY-LOGIN.jpeg`, `WP16-EVID-SAFETY-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
| NAV-SEED-005 | Dispatch login submit | — | `/dispatch-portal/login` | `/dispatch-portal` | Dispatch authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-DISPATCH-LOGIN.jpeg`, `WP16-EVID-DISPATCH-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
| NAV-SEED-006 | Shop login submit | — | `/shop/login` | `/shop` | Shop authenticated | Yes | Yes | Unknown | Unknown | Unknown | Unknown | Unknown | `WP16-EVID-SHOP-LOGIN.jpeg`, `WP16-EVID-SHOP-HOME.jpeg` | Seeded from current login flow evidence; item-level nav phase pending. |
