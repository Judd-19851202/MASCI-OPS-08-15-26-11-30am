# TRACK 19.51 · Portal Home Inventory

Every home / hub / landing / command center surface discovered.

| # | Portal | Route | Component | Auth gate | Classification | OI-linked? |
|---|---|---|---|---|---|:-:|
| 1 | Admin (v1) | `/admin` | `AdminHub.jsx` | `A(...)` admin gate | ACTIVE BUT NOISY | partial |
| 2 | Admin (v2) | `/admin/v2/*` | `AdminHubV2.jsx` | `A(...)` admin gate | ACTIVE | partial |
| 3 | Admin · Operational Intelligence | `/admin/operational-intelligence` | `AdminOperationalIntelligence.jsx` | `A(...)` | **ACTIVE — REFERENCE STANDARD** | ✅ full |
| 4 | Admin · OI Recipients | `/admin/operational-intelligence/recipients` | `AdminOperationalIntelligenceRecipients.jsx` | `A(...)` | ACTIVE | ✅ full |
| 5 | Safety | `/safety` | `SafetySection.jsx` / `SafetyHub.jsx` | safety token | ACTIVE BUT CONFUSING | partial (safety_morning links) |
| 6 | HR | `/hr` | `HrHub.jsx` | hr token | ACTIVE BUT NOISY | ❌ |
| 7 | PM | `/pm` | `PmHub.jsx` · `PmCommandCenter.jsx` | pm token | ACTIVE BUT CONFUSING | partial |
| 8 | Shop | `/shop` | `ShopHub.jsx` | shop token | ACTIVE BUT HIDDEN | ❌ |
| 9 | Dispatch | `/dispatch` | `DispatchHub.jsx` · `DispatchHubV2.jsx` · `DispatchCommandCenter.jsx` | dispatch token | ACTIVE (best non-OI cockpit) | ❌ |
| 10 | Fleet | `/fleet` | `FleetVisibility.jsx` | safety_or_admin | ACTIVE BUT CONFUSING | partial |
| 11 | Field | `/field` | `FieldSection.jsx` · `FieldLeadershipHub.jsx` | field/leadership | ACTIVE | ❌ |
| 12 | Guidance / Help | (various) | `AdminGuide.jsx` · training hub | admin/general | ACTIVE BUT HIDDEN | ❌ |
| 13 | Public entry | `/` `/sign-in` | Multi-portal login | none | ACTIVE | ❌ |

## Classification tallies
- ACTIVE — REFERENCE STANDARD: 1
- ACTIVE (clean): 3
- ACTIVE BUT NOISY: 2
- ACTIVE BUT CONFUSING: 4
- ACTIVE BUT HIDDEN: 2
- LEGACY / RETIRED / BROKEN: 0 (none blocking)
- UNKNOWN: 1 (Field · needs targeted user interviews)

## Multiple-hub notes
Three portals ship both a v1 and a v2 hub file (Admin, Dispatch, PM). None of them break — v2 is the intended path. Consolidation to single-hub-per-portal is a P2 hygiene item on the roadmap.
