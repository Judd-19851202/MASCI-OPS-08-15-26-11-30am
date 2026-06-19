# TRACK 15.43 · Executive Audit

**Verdict:** 🟡 **YELLOW** — 30-second comprehension partially achievable; visibility gaps documented (NOT built).

## Surfaces today

| Surface | Page | Backend |
|---|---|---|
| Leadership Hub V2 | `LeadershipHubV2.jsx` | `routes/operations_center` |
| Field Leadership Portal | `FieldLeadershipPortalDashboard.jsx` | `routes/field_leadership` |
| Admin Hub V2 | `AdminHubV2.jsx` | `routes/admin_ops` |
| Project Health | `ProjectHealth.jsx` (referenced in Admin nav) | `routes/operations` |
| Document Expirations | `DocumentExpirations.jsx` | `routes/hr_portal` |
| Dispatch Command Center | `DispatchCommandCenter.jsx` | `routes/dispatch_lifecycle` |
| Safety hub list pages | various | various |

## 30-second test (Nacho logs in for 30 seconds, what can he immediately understand?)

### Already comprehensible at-a-glance (🟢)
1. **Project list with active count** — Leadership Hub V2 surfaces.
2. **Equipment status** — `AdminLeadershipEquipment.jsx` surfaces.
3. **Safety summary** — exists via `safety_exports::export_executive` (PDF) + safety hub.
4. **Open notifications count** — global bell badge.

### Visibility gaps (DOCUMENTED · NOT BUILT per directive)
1. **VIS-GAP-001 — Jobs at risk single-screen:** No unified "jobs at risk" composite (DR cadence + safety incidents + crew compliance + holds). Today Nacho must check Daily Reports, Safety, Holds, Compliance separately. **Impact:** HIGH.
2. **VIS-GAP-002 — Overdue items rollup:** Overdue Daily Reports, overdue field leadership records, overdue training renewals exist as separate pages but no exec-level "Overdue (N)" tile that breaks down by category.  **Impact:** HIGH.
3. **VIS-GAP-003 — Staffing-issues callout:** Team assignments are project-scoped. No org-wide "X projects missing a Foreman" / "Y projects missing a PM" exec tile.  **Impact:** MEDIUM.
4. **VIS-GAP-004 — Unresolved actions (CAPA, action items, holds):** Exists in lists but not composite. The notification bell is the closest analog and works well.  **Impact:** MEDIUM.

### Recommendation (next track, NOT this one)
A read-only `ExecutiveOverview.jsx` that COMPOSES existing data into 4-6 tiles. Pure aggregation — no schema changes, no new collections. This is exactly the kind of thing the directive said not to build during 15.43.

## Pass Criteria
* Nacho can understand jobs at risk in 30s: 🟡 PARTIAL — possible via Leadership Hub V2 but requires drill-down.
* Overdue items: 🟡 PARTIAL — visible but scattered.
* Staffing issues: 🟡 PARTIAL — requires per-project drill.
* Safety/Equipment: 🟢 GOOD — central tiles exist.
* Unresolved actions: 🟢 via notifications.

🟡 **YELLOW — verdict honestly reflects the gap. The Five-Pillar "Proven" standard requires evidence; the evidence here is that composite exec-level rollups don't yet exist.** Gaps documented for a future read-only aggregation track.
