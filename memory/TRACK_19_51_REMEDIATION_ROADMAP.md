# TRACK 19.51 · Remediation Roadmap

19 items · P0–P3 · every item names the portal, the fix, the estimated scope, and whether OI powers it.

## P0 (blocks work / hides critical action)
**None.** No portal home has a P0 blocker. Audit finished 2026-07-04.

## P1 (serious usability / visibility issue — highest priority)

1. **Safety Hub Attention Strip** — surface the `safety_morning_digest` top-attention label + open-CAPA count at the top of `/safety`. Scope: S. OI-powered: ✅. Risk: LOW.
2. **HR Hub Attention Strip** — surface `hr_intelligence` + `training_intelligence` combined. Adds "expiring certs" & "onboarding stalled" signals. Scope: S. OI: ✅. Risk: LOW.
3. **PM landing = PM Command Center** — retire the PM Hub as the default `/pm` route in favour of `PmCommandCenter.jsx`. Add `project_intelligence` snapshot. Scope: S. OI: ✅. Risk: LOW.
4. **Shop Hub Attention Strip** — surface `shop_intelligence` (safety holds → aging critical defects → OOS). Scope: S. OI: ✅. Risk: LOW.
5. **Fleet Visibility Attention Strip + mobile fix** — surface `fleet_intelligence` and repair the >900px table blowout. Scope: M. OI: ✅. Risk: LOW.

## P2 (important polish)

6. **Admin v1 hub deprecation** — collapse 34 tiles into 8-section standard by phased retirement. Scope: M. OI: partial. Risk: LOW.
7. **Dispatch Attention Strip formalisation** — Dispatch Command Center is close to compliance; formalise the strip using `transportation_intelligence`. Scope: S. OI: ✅. Risk: LOW.
8. **Field / Leadership Today Action Queue** — assignments + safety cards + trench inspections due today. Scope: M. OI: N/A (task-launcher). Risk: LOW.
9. **Guidance Center role-based restructure** — pivot from feature-list to workflow-list. Scope: L. OI: N/A. Risk: LOW.
10. **Asset Administrator polish** — inline attention pill for holds. Scope: S. OI: partial. Risk: LOW.
11. **Superintendent Today Action Queue** — extension of #8. Scope: S. Risk: LOW.
12. **Cockpit sparkline mini-chart** — Track 19.47 potential enhancement. Scope: S. OI: ✅. Risk: LOW.

## P3 (nice-to-have)

13. Mobile-native shell (portfolio-wide). Scope: L. Risk: MED.
14. Group member removal API + UI (finishes group-CRUD symmetry). Scope: S. Risk: LOW.
15. 15-min cache on Corporate + Weekly Ops for sub-second Cockpit drill-down. Scope: S. Risk: LOW.
16. Executive one-line summary email (Monday 06:00 UTC). Scope: XS. Risk: LOW.
17. Sidebar V2 polish across remaining sections. Scope: M. Risk: LOW.
18. TrenchAssetPicker + HR polish. Scope: M. Risk: LOW.
19. Pilot-signoff PDF stitcher. Scope: M. Risk: LOW.

## Sequencing recommendation
Ship P1 items **1 → 2 → 3 → 4 → 5** first (each is a Small-scope Attention-Strip addition powered by an already-shipped OI summary). None require new backend endpoints. Combined effort < 1 track worth of implementation. Total risk: LOW.
