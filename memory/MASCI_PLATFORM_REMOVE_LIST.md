# MASCI Platform — Remove List (Track 13.4C · Deliverable #4)

**Mode:** documentation only. NOT a remove order — these items are catalogued for future decision-making.

Source findings: Master Findings Registry. Each row references its finding ID.

---

## Duplications

| Item | Where | Source finding | Rationale |
|---|---|---|---|
| `OperationsActionsTile` mounted on 6 of 7 portals | DispatchHub · PmHub · ShopHub · SafetyHub · FieldLeadershipHub · AdminHub | V-08 · R-06 | Cross-portal duplicate of each portal's native Tasks tile; HR removed in Track 13.4A |
| Two `StatusBadge.jsx` files (root + `oa/`) sharing the filename | `/components/StatusBadge.jsx` and `/components/oa/StatusBadge.jsx` | V-07 | Same name, different schema |
| 4 admin health pages with overlapping signals | `AdminPersistenceHealth` · `AdminProductionHealth` · `AdminStability` · `AdminClusterCapacity` | R-04 | Likely consolidatable into a single Platform Health surface |
| `AdminCompliance` + `AdminComplianceFindings` | Admin nav | R-05 | Two pages, one workflow |
| 8 distinct `*CommandCenter` pages | `AdminCommandCenter` · `PmCommandCenter` · `DispatchCommandCenter` · `OperationsCenterCommand` · `OperationalGuidanceCenter` · `OpsTrainingCenter` · `TrenchSafetyOpsCenter` · `OdrCenter` | V-09 · R-03 | Naming convention shared, layouts not; some likely deserve unique identities (Trench, ODR), some likely deserve consolidation (Admin · Operations · Ops Training Center) |
| 7 per-portal forgot-password / reset / change-password flows + master `/sign-in` (8 total) | per portal | R-01 | Same task, 8 places |
| 15 status-chip components | see Phase 2A §A.5 | V-07 | At minimum the duplicate `StatusBadge.jsx` resolution and a shared `<StatusChip>` primitive could subsume several |
| PO per-action email + PO digest | `po_requests.py` + `po_digest_admin.py` | R-07 | Same recipient gets the same PO twice |
| 1,146 unused Spanish dictionary keys | `i18n.js` | R-09 | Dead translation weight |

## Dead surfaces

| Item | Where | Source finding | Rationale |
|---|---|---|---|
| `guidance_search_misses` collection — accumulates but has no operator-visible audit view | Mongo | R-15 | Either surface it as a guidance-coverage card, or stop writing to it |
| `forgedops-logo.png` asset — exists, never used as primary brand mark | `/assets/` | W-16 | If parent brand isn't to be foregrounded yet, the asset is dead weight |
| Orphan ES entries that no `t()` site references (1,146 keys) | `i18n.js` | R-09 | Many likely became orphans when adjacent UI strings were edited |

## Wrong-role features

| Item | Where | Source finding | Rationale |
|---|---|---|---|
| `OperationsActionsTile` (cross-portal ops language) on every operator portal | 6 portals still | R-06 / V-08 | Operations Actions is a workflow, not a top-of-hub tile per role |
| `MotiveDrivers` cleanup tile on HR | HR | Phase 1 §D | Admin/ops cleanup language; HR may not be the right owner (kept temporarily per MCC-1 access extension) |
| `IntegrationHealthCard` historically on HR | HR (removed in Track 13.4A) | recorded for trace | Already removed |

## Clutter / Operational noise

| Item | Where | Source finding | Rationale |
|---|---|---|---|
| 4 admin health pages | Admin module | R-04 | Splits one signal into 4 |
| 8 `*CommandCenter` pages | per module | V-09 / R-03 | Title-collision creates the impression of overlapping signals even where domains differ |
| Cross-portal "Operations Center" surface in non-operational portals | (legacy import in `HrHub.jsx`, removed in 13.4A; still imported elsewhere) | Phase 1 + R-06 | Cross-portal language inside role portals is the recurring drift |

---

## NOT recommended for removal (recorded for clarity)

- **None of the `Trench Safety` pages** — Trench Safety is explicitly on the Preserve List.
- **None of the per-portal hub files** — they currently differ in size (V-05) but each is owned by a portal team; consolidation is a Rebuild candidate, not a Remove.
- **None of the integration-health, integration-events, or governance-health surfaces** — they're the platform's truth surfaces.

---

## Decision discipline

Removal of any item on this list requires:
1. Cross-check against the Preserve List.
2. Evidence that no live workflow depends on the surface.
3. Operator approval (per the Track 13.4 phased governance reset rule).
4. A migration note in the RC Certification Ledger.
