# WP-16 Phase B — Wave 2 7-Gate Inspection

Date: 2026-07-30
Protocol: Executive-authorized inspection only
Scope lock: Wave 2 only. No repairs performed.

## Seven gates used in this pass

1. **Access / navigation continuity**
2. **Functional render / interaction**
3. **Visual integrity**
4. **Responsive behavior**
5. **Operational clarity**
6. **Human readability / copy clarity**
7. **Data truth / state truth**

## Inspection sources

- Runtime route verification in preview: `https://masci-audit-hub.preview.emergentagent.com`
- Focused browser evidence via screenshot automation on 2026-07-30
- Wave 2 denominator source: `/app/memory/WP16_WAVE2_INVENTORY_AND_RECONCILIATION.md`
- Certification ledger: `/app/memory/WP16_CERTIFICATION_REGISTER.csv`
- Live issue ledger: `/app/memory/WP16_LIVE_PUNCH_LIST.md`
- Key source references:
  - `frontend/src/components/operational_intelligence/OiAttentionStrip.jsx`
  - `frontend/src/pages/PmHomeRedirect.jsx`
  - `frontend/src/pages/admin/AdminOS.jsx`
  - `frontend/src/pages/admin/AdminPlatformOverview.jsx`
  - legacy home routes under `frontend/src/pages/*Hub.jsx`

## Final inspected denominator

- **Wave 2 inspected denominator:** `99 / 99`
  - Route / homepage / dashboard / redirect surfaces: `30 / 30`
  - Embedded widget / section / dialog clusters: `47 / 47`
  - Shared navigation / state / access foundations: `22 / 22`
- **Items with no defect linked:** `81`
- **Items with confirmed defect linkage:** `18`

## Confirmed Wave 2 defects

| Issue ID | Severity | Affected W2 IDs | Defect | Evidence | Root cause | Recommended smallest-safe repair |
|---|---|---|---|---|---|---|
| WP16-W2-001 | High | W2-011, W2-013, W2-014, W2-016, W2-020, W2-022, W2-040, W2-056, W2-064 | Shared portal-home OI strip blocks intended HR/Safety/Shop users with an admin-only message on their own home surfaces. | Runtime 2026-07-30: `/hr`, `/safety-portal`, `/shop` all show `Admin token required to view OI signals · request access from your administrator.` Code: `frontend/src/components/operational_intelligence/OiAttentionStrip.jsx:67-73,145,197`. | Shared widget hard-codes admin-only auth headers and admin-only cockpit ownership inside a multi-portal home component. | Keep the shared widget, but switch it to portal-appropriate scoped auth and portal-safe drill-down ownership so intended home users do not hit an admin-only block on first screen. |
| WP16-W2-002 | High | W2-007 | `/pm` is counted as a Wave 2 homepage route but runtime lands on `/pm/command-center`, which is outside the approved Wave 2 denominator. | Runtime 2026-07-30: PM login and direct `/pm` both resolve to `/pm/command-center`. Code: `frontend/src/pages/PmHomeRedirect.jsx:4-12`, `AppRoutes.jsx:876,925`. | PM root was intentionally redirected to the Command Center, collapsing homepage ownership into a later-wave workflow surface. | Either reclassify `/pm` as an out-of-wave redirect alias in the certification ledger or restore `/pm` to an in-wave homepage surface. |
| WP16-W2-003 | Medium | W2-001, W2-032 | Admin OS posture strip shows live counts while the posture narrative still says `Loading domain probes…`, creating contradictory first-screen state. | Runtime 2026-07-30 after 10s on `/admin`: counts rendered `4 / 2 / 3 / 0 / 10` while posture copy still said `Loading domain probes…`. Code: `frontend/src/pages/admin/AdminOS.jsx:669-676,747-753`. | Posture copy is gated by `loaded`, while summary counts can render from partially-populated probe results earlier. | Tie the posture narrative to the same resolved state as the counts, or hold both until the same loaded boundary is reached. |
| WP16-W2-004 | Medium | W2-009, W2-012, W2-015, W2-021, W2-030 | Legacy/public Wave 2 home surfaces bypass the canonical PortalShell and visually diverge from the approved homepage/dashboard shell contract. | Runtime 2026-07-30 screenshots for `/pm/hub_legacy`, `/hr/hub_legacy`, `/safety-portal/hub_legacy`, `/shop/hub_legacy`, and `/safety` show no `ds-portal-shell` chrome. | Route-local legacy home pages still render through bespoke or older shell patterns instead of the canonical Wave 2 shell. | Wrap the existing page bodies in `PortalShell` only, preserving current route logic, data calls, and page structure. |
| WP16-W2-005 | Low | W2-006 | `/admin/platform-overview` is denominated as a standalone route screen, but runtime is only an alias redirect to `/admin`. | Runtime 2026-07-30: `/admin/platform-overview` resolves to `/admin`. Code: `frontend/src/pages/admin/AdminPlatformOverview.jsx:3-17`. | Certification denominator treats an alias redirect as a separate screen experience. | Reclassify this row as a redirect alias linked to W2-001, or explicitly note it as the same underlying experience in the register. |

## A. Route / homepage / dashboard / redirect inspection matrix

| W2 ID | Surface | 7-gate outcome | Issue / note |
|---|---|---|---|
| W2-001 | `/admin` | DEFECT LINKED | WP16-W2-003 — contradictory posture loading state on the primary Admin OS landing. |
| W2-002 | `/admin/hub_v1` | PASS | Redirect verified to `/admin`; no separate user-facing defect observed. |
| W2-003 | `/admin/hub_v2` | PASS | Redirect verified to `/admin`; no separate user-facing defect observed. |
| W2-004 | `/admin/executive-overview` | PASS | Loaded successfully with canonical shell and executive summary content. |
| W2-005 | `/admin/operations-dashboard` | PASS | Loaded successfully with canonical shell and operational dashboard content. |
| W2-006 | `/admin/platform-overview` | DEFECT LINKED | WP16-W2-005 — route is a duplicate alias experience rather than a standalone Wave 2 screen. |
| W2-007 | `/pm` | DEFECT LINKED | WP16-W2-002 — runtime lands on `/pm/command-center`, outside the approved Wave 2 experience denominator. |
| W2-008 | `/pm/hub` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-009 | `/pm/hub_legacy` | DEFECT LINKED | WP16-W2-004 — legacy home bypasses canonical PortalShell. |
| W2-010 | `/pm/hub_v2` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-011 | `/hr` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended HR home users with admin-only message. |
| W2-012 | `/hr/hub_legacy` | DEFECT LINKED | WP16-W2-004 — legacy home bypasses canonical PortalShell. |
| W2-013 | `/hr/hub_v2` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended HR home users with admin-only message. |
| W2-014 | `/safety-portal` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended Safety home users with admin-only message. |
| W2-015 | `/safety-portal/hub_legacy` | DEFECT LINKED | WP16-W2-004 — legacy home bypasses canonical PortalShell. |
| W2-016 | `/safety-portal/hub_v2` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended Safety home users with admin-only message. |
| W2-017 | `/dispatch-portal` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-018 | `/dispatch-portal/hub_legacy` | PASS | Loaded successfully; no Wave 2 defect observed in this pass. |
| W2-019 | `/dispatch-portal/hub_v2` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-020 | `/shop` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended Shop home users with admin-only message. |
| W2-021 | `/shop/hub_legacy` | DEFECT LINKED | WP16-W2-004 — legacy home bypasses canonical PortalShell. |
| W2-022 | `/shop/hub_v2` | DEFECT LINKED | WP16-W2-001 — shared OI strip blocks intended Shop home users with admin-only message. |
| W2-023 | `/leadership` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-024 | `/leadership/hub_v2` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-025 | `/field-leadership/portal/dashboard` | PASS | Loaded successfully with portal shell and no first-screen defect observed. |
| W2-026 | `/training-hub` | PASS | Redirect verified to `/training`; no separate defect observed. |
| W2-027 | `/driver` | PASS | Driver entry behavior observed; route hands off to `/shift` as designed for unauthenticated entry. |
| W2-028 | `/shift` | PASS | Loaded successfully as the shift-start entry experience. |
| W2-029 | `/executive-dashboard` | PASS | Redirect verified to `/admin/executive-overview`; no separate defect observed. |
| W2-030 | `/safety` | DEFECT LINKED | WP16-W2-004 — public/shared Wave 2 safety landing bypasses canonical PortalShell. |

## B. Embedded widget / section / dialog cluster inspection matrix

| W2 ID | Surface | 7-gate outcome | Issue / note |
|---|---|---|---|
| W2-031 | Admin OS primary action strip | PASS | No defect observed. |
| W2-032 | Admin OS platform posture strip | DEFECT LINKED | WP16-W2-003 — contradictory loading copy versus rendered counts. |
| W2-033 | Admin OS backup integrity panel | PASS | No defect observed. |
| W2-034 | Admin OS 10-domain grid | PASS | No defect observed. |
| W2-035 | Leadership V2 preview banner | PASS | No defect observed. |
| W2-036 | Leadership V2 executive overview tile | PASS | No defect observed. |
| W2-037 | Leadership V2 safety attention section | PASS | No defect observed. |
| W2-038 | Leadership V2 fleet + shop execution-threat section | PASS | No defect observed. |
| W2-039 | Leadership V2 compliance-expiration section | PASS | No defect observed. |
| W2-040 | HR OI attention strip | DEFECT LINKED | WP16-W2-001 — admin-only block on intended portal-home widget. |
| W2-041 | HR compliance-at-risk widget | PASS | No defect observed. |
| W2-042 | Employee record completeness tile | PASS | No defect observed. |
| W2-043 | Employee directory search block | PASS | No defect observed. |
| W2-044 | Open HR work queue grid | PASS | No defect observed. |
| W2-045 | Field signals HR watches grid | PASS | No defect observed. |
| W2-046 | Always-on HR destinations grid | PASS | No defect observed. |
| W2-047 | HR calm-state empty block | PASS | No defect observed. |
| W2-048 | PM open work queue grid | PASS | No defect observed. |
| W2-049 | PM recent field activity grid | PASS | No defect observed. |
| W2-050 | PM always-on destinations grid | PASS | No defect observed. |
| W2-051 | PM calm-state empty block | PASS | No defect observed. |
| W2-052 | Dispatch driver + haul queue grid | PASS | No defect observed. |
| W2-053 | Dispatch equipment + shop signals grid | PASS | No defect observed. |
| W2-054 | Dispatch safety cross-portal read grid | PASS | No defect observed. |
| W2-055 | Dispatch all-clear empty block | PASS | No defect observed. |
| W2-056 | Safety OI attention strip | DEFECT LINKED | WP16-W2-001 — admin-only block on intended portal-home widget. |
| W2-057 | Safety operational KPIs card | PASS | No defect observed. |
| W2-058 | Safety trench intelligence card | PASS | No defect observed. |
| W2-059 | Safety CAPA grid | PASS | No defect observed. |
| W2-060 | Safety compliance grid | PASS | No defect observed. |
| W2-061 | Safety incidents / trench / documents grid | PASS | No defect observed. |
| W2-062 | Safety field records & plans grid | PASS | No defect observed. |
| W2-063 | Safety all-clear empty block | PASS | No defect observed. |
| W2-064 | Shop OI attention strip | DEFECT LINKED | WP16-W2-001 — admin-only block on intended portal-home widget. |
| W2-065 | Shop global unit search section | PASS | No defect observed. |
| W2-066 | Shop Your Queue strip | PASS | No defect observed. |
| W2-067 | Shop attention-required grid | PASS | No defect observed. |
| W2-068 | Shop active work grid | PASS | No defect observed. |
| W2-069 | Shop mechanic workload card | PASS | No defect observed. |
| W2-070 | Shop preventive-maintenance section | PASS | No defect observed. |
| W2-071 | Shop parts and waiting section | PASS | No defect observed. |
| W2-072 | Shop fuel and service grid | PASS | No defect observed. |
| W2-073 | Shop unit-intelligence grid | PASS | No confirmed user-facing defect observed in this inspection pass. |
| W2-074 | Shop records grid | PASS | No defect observed. |
| W2-075 | Shop recovery map | PASS | No defect observed. |
| W2-076 | Shop asset-administrator historical-records grid | PASS | No defect observed. |
| W2-077 | Shop all-clear empty block | PASS | No defect observed. |

## C. Shared navigation / state / access foundation matrix

| W2 ID | Surface | 7-gate outcome | Issue / note |
|---|---|---|---|
| W2-078 | PortalShell desktop header/chrome | PASS | Verified in runtime across Admin, HR, Safety, Shop, Dispatch, and Leadership routes. |
| W2-079 | PortalShell mobile more-menu action tray | PASS | No Wave 2-specific defect confirmed; foundation evidence reused from prior responsive checkpoint. |
| W2-080 | EmptyState | PASS | Code review and runtime usage showed no defect. |
| W2-081 | LoadingState | PASS | Code review and runtime usage showed no defect. |
| W2-082 | ErrorState | PASS | Code review and runtime usage showed no defect. |
| W2-083 | Admin navigation rail (`SideNavV3`) | PASS | Loaded successfully on Admin routes; no defect observed. |
| W2-084 | HR sidebar V2 | PASS | Loaded successfully on HR routes; no defect observed. |
| W2-085 | PM sidebar V2 | PASS | Loaded successfully on PM routes; no defect observed. |
| W2-086 | Dispatch sidebar V2 | PASS | Loaded successfully on Dispatch routes; no defect observed. |
| W2-087 | Safety sidebar V2 | PASS | Loaded successfully on Safety routes; no defect observed. |
| W2-088 | Shop sidebar V2 | PASS | Loaded successfully on Shop routes; no defect observed. |
| W2-089 | Transportation sidebar V2 | PASS | Code-reviewed and no Wave 2-specific defect was confirmed in this pass. |
| W2-090 | RequireAdmin | PASS | Guard behavior matched Admin home routing in runtime checks. |
| W2-091 | RequireAdminOrPm | PASS | No confirmed Wave 2 defect observed in this pass. |
| W2-092 | RequireAdminPmOrSafety | PASS | No confirmed Wave 2 defect observed in this pass. |
| W2-093 | RequireDispatch | PASS | Guard behavior matched Dispatch home routing in runtime checks. |
| W2-094 | RequireFl | PASS | Guard behavior matched Field Leadership home routing in runtime checks. |
| W2-095 | RequireHr | PASS | Guard behavior matched HR home routing in runtime checks. |
| W2-096 | RequirePm | PASS | Guard behavior matched PM home routing in runtime checks. |
| W2-097 | RequireSafety | PASS | Guard behavior matched Safety home routing in runtime checks. |
| W2-098 | RequireShop | PASS | Guard behavior matched Shop home routing in runtime checks. |
| W2-099 | RequireTransportationPortal | PASS | No confirmed Wave 2 defect observed in this pass. |

## Defect counts by severity

- **High:** `2`
- **Medium:** `2`
- **Low:** `1`
- **Total issue IDs opened / linked:** `5`

## Seven-gate summary

| Gate | Summary |
|---|---|
| Access / navigation continuity | Mostly stable. Redirect aliases verified. One major scope defect remains: W2-007 (`/pm`) lands outside Wave 2. |
| Functional render / interaction | Core Wave 2 routes rendered and interacted successfully in preview. No blank-screen or crash defect was confirmed in this pass. |
| Visual integrity | Main PortalShell surfaces are stable, but five legacy/public home routes still diverge from the canonical shell. |
| Responsive behavior | No new Wave 2-specific overflow defect was confirmed during this pass. PortalShell foundation prior evidence remains the main responsive proof. Legacy non-PortalShell routes remain desktop-observed only. |
| Operational clarity | HR/Safety/Shop homes expose an admin-only OI block on first-screen attention widgets, weakening operator-first clarity. |
| Human readability / copy clarity | Admin OS posture copy contradicts rendered counts; OI strip copy tells intended home users to ask for admin access on their own portal homes. |
| Data truth / state truth | Admin OS posture strip mixes live numbers with a loading state. Shared OI strip presents an auth truth that is accurate for its implementation but wrong for intended home-surface ownership. |

## Common root causes

1. **Shared widget ownership drift**
   - Multi-portal home widget still assumes admin ownership and admin auth, even when embedded in non-admin home surfaces.

2. **Legacy shell carry-forward**
   - Older home routes remain in denominator but still bypass the canonical Wave 2 shell contract.

3. **Route-to-experience classification drift**
   - Some routes in denominator are aliases or redirects rather than distinct homepage experiences.

4. **Mixed-state rendering**
   - At least one first-screen Admin surface renders summary counts before its posture-copy loading state resolves.

## Foundation assessment

- **Shared foundations are largely stable.** `PortalShell`, `PortalStates`, sidebars, and Wave 2 guard components did not produce a verified multi-page failure in this pass.
- **One verified shared multi-page root cause exists in a reusable Wave 2 home widget path.**
  - `OiAttentionStrip.jsx` is a true cross-surface defect and is the only shared repair candidate that currently meets the threshold for a later authorized foundation-level change.
- **No evidence in this pass requires broader PortalShell, nav rail, or route-guard repair before the specific linked issues above.**

## Estimated repair effort

- WP16-W2-001: `0.5–1.0` engineer day
- WP16-W2-002: `0.25–0.5` engineer day
- WP16-W2-003: `0.25` engineer day
- WP16-W2-004: `1.0–1.5` engineer days
- WP16-W2-005: `0.1–0.25` engineer day
- **Estimated total:** `2.1–3.5 engineer days`, plus focused retest time

## Recommended repair sequencing

1. **WP16-W2-002** — resolve the Wave 2 PM root ownership gap first so homepage certification scope is truthful.
2. **WP16-W2-001** — repair the shared OI strip next because it affects multiple first-screen portal homes.
3. **WP16-W2-003** — fix the Admin OS posture mixed-state contradiction.
4. **WP16-W2-004** — normalize legacy/public home shell wrappers without changing route logic.
5. **WP16-W2-005** — close the control-only alias classification gap.

## Executive stop point

- Wave 2 7-Gate inspection is complete.
- Defects have been assigned / linked and entered into the live punch list.
- No repairs were performed.
- Await explicit repair authorization before changing code.