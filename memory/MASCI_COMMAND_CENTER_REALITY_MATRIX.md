# MASCI Command Center Reality Matrix

**Track 13.5B · Cross-portal "Center" surface reality classification**
**Mode:** Analysis only — no rename, no merge, no redesign.
**Generated:** 2026-06-12 (UTC)

> Cites: V-09 (Command-center sprawl — 8 distinct `*Center` pages with overlapping signals) and R-03 (Command-center sprawl reality lens) from `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`, plus the rebuild list §R-05.

---

## 1. The 8 Centers — verified by file inspection

| # | Object | File | Route | Owning portal | Role(s) | Backing API | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **AdminCommandCenter** | `pages/admin/AdminCommandCenter.jsx` | `/admin/command-center` | Admin | Super-admin | `/api/operations-center/*` | Operational |
| 2 | **OperationsCenterCommand** | `pages/OperationsCenterCommand.jsx` | `/operations-center` | Admin (cross-portal) | Super-admin · Ops | `/api/operations-center/*` | Operational |
| 3 | **DispatchCommandCenter** | `pages/DispatchCommandCenter.jsx` | `/dispatch-portal/command` | Dispatch | Dispatcher · Super-admin | `/api/dispatch/*` + `/api/operations-map/snapshot` | Operational |
| 4 | **PmCommandCenter** | `pages/PmCommandCenter.jsx` | `/pm/command-center` | PM | PM · Super-admin | `/api/pm/command-center/*` (7 sub-endpoints, `pm_command_center.py:215-642`) | Operational |
| 5 | **OdrCenter** | `pages/odr/OdrCenter.jsx` | `/odr/center` | ODR | Operator · ODR-issuer | `/api/odr/*` | Operational |
| 6 | **TrenchSafetyOpsCenter** | `pages/trench_safety/TrenchSafetyOpsCenter.jsx` | `/trench-safety/ops-center` | Trench Safety | Safety Mgr | `/api/trench-safety/*` | Operational |
| 7 | **OperationalGuidanceCenter** | `pages/guidance/OperationalGuidanceCenter.jsx` | `/guidance/center` | Guidance | Authoring | `/api/guidance/*` | Operational |
| 8 | **OpsTrainingCenter** | `pages/OpsTrainingCenter.jsx` | `/ops-training/center` | Training | Trainer / HR / Admin | `/api/training/*` | Operational |

Bonus: **AdminIntegrationCenter** (`/admin/integrations`) also carries the suffix and inflates the count to 9 surfaces using the word "Center" — see §3.

---

## 2. Five-question classification

For each Center, the directive asks: truly operational · duplicated · role-specific · unique value · creates confusion.

| Object | Truly operational? | Duplicated? | Role-specific? | Unique value? | Creates confusion? |
| --- | :-: | :-: | :-: | :-: | :-: |
| AdminCommandCenter | ✅ | ⚠ overlaps OperationsCenterCommand | super-admin only | partial — overlaps OCC | **YES** — both Admin pages call same endpoint family `/api/operations-center/*` |
| OperationsCenterCommand | ✅ | ⚠ overlaps AdminCommandCenter | super-admin · ops | partial | **YES** |
| DispatchCommandCenter | ✅ | ❌ | dispatcher | ✅ unique (only place with live fleet map + assignment board joined) | low |
| PmCommandCenter | ✅ | ❌ | PM | ✅ unique (Phase 4A APIs project-scoped) | low |
| OdrCenter | ✅ | ❌ | ODR operator | ✅ unique (ODR lifecycle) | medium — "Center" suffix invites comparison with role landings |
| TrenchSafetyOpsCenter | ✅ | ❌ | Safety Mgr | ✅ unique (trench-asset lens) | medium — same suffix issue |
| OperationalGuidanceCenter | ✅ | ❌ | Guidance authors | ✅ unique (authoring surface) | **HIGH** — "Center" here is a content-authoring tool, not a role landing |
| OpsTrainingCenter | ✅ | ❌ | Trainer | ✅ unique | medium |
| AdminIntegrationCenter | ✅ | ❌ | super-admin | unique | **HIGH** — uses "Center" as a noun for a settings page |

---

## 3. The naming problem — quantified

"Center" today carries **at least four different meanings** in MASCI:

| Meaning | Examples | Operator interpretation risk |
| --- | --- | --- |
| Role landing | AdminCommandCenter · PmCommandCenter · DispatchCommandCenter | Low if you're already in the role |
| Cross-portal aggregator | OperationsCenterCommand | High (collides with AdminCommandCenter) |
| Domain ops view | TrenchSafetyOpsCenter · OdrCenter | Medium |
| Authoring / settings | OperationalGuidanceCenter · AdminIntegrationCenter | High (these are not role landings at all) |

This is the precise problem the rebuild list `R-05` flags:

> "Either one 'Center' per role with a strict role-first contract, or rename non-role centers (Trench, ODR, Operational Guidance) to non-'Center' nouns so the word 'Center' reliably means 'primary role landing for portal X'."

No action required in this track — only classification.

---

## 4. Five-Pillar verdict per Center

| Object | Powerful | Simple | Beautiful | Trusted | Proven | Notes |
| --- | :-: | :-: | :-: | :-: | :-: | --- |
| DispatchCommandCenter | 9 | 8 | 8 | 7 | 8 | Post-13.4A canvas guardrail PASS; D-01 keeps Trusted < 9 until production verified. |
| PmCommandCenter | 9 | 7 | 7 | 7 | 7 | Phase 4A APIs validated by `test_pm_command_center_phase_4a.py` (7 endpoints). |
| OperationsCenterCommand | 8 | 5 | 7 | 7 | 6 | Real but overlaps AdminCommandCenter. |
| AdminCommandCenter | 8 | 5 | 6 | 7 | 6 | Same APIs, different name. |
| TrenchSafetyOpsCenter | 9 | 8 | 9 | 9 | 9 | Module cited as exemplary in `MASCI_VISUAL_IDENTITY_AUDIT.md`. |
| OdrCenter | 8 | 7 | 7 | 7 | 7 | Backed by ODR lifecycle. |
| OperationalGuidanceCenter | 7 | 5 | 6 | 7 | 6 | Authoring tool labelled as "Center" creates IA confusion. |
| OpsTrainingCenter | 7 | 7 | 7 | 7 | 7 | Real. |
| AdminIntegrationCenter | 7 | 5 | 6 | 7 | 6 | Settings page using "Center" noun. |

Centers ranked highest-to-lowest five-pillar avg:

1. TrenchSafetyOpsCenter — **8.8**
2. DispatchCommandCenter — **8.0**
3. PmCommandCenter — **7.4**
4. OdrCenter — **7.2**
5. OpsTrainingCenter — **7.0**
6. OperationsCenterCommand — **6.6**
7. AdminCommandCenter — **6.4**
8. OperationalGuidanceCenter — **6.2**
9. AdminIntegrationCenter — **6.2**

---

## 5. Reality classifications

- **Keep as-is** (highest score, lowest confusion): TrenchSafetyOpsCenter · DispatchCommandCenter · PmCommandCenter · OdrCenter.
- **Operational but duplicated** (naming/scope overlap): AdminCommandCenter ↔ OperationsCenterCommand (both consume `/api/operations-center/*`).
- **Use of "Center" creates confusion** (rename in a future track, NOT here): OperationalGuidanceCenter · AdminIntegrationCenter.
- **Visual / placeholder / dead / broken**: NONE — all 8 (+1) Centers are operationally backed by real APIs.

---

## 6. What this matrix does NOT do

- Does not rename anything.
- Does not propose a target IA.
- Does not collapse the two Admin Centers into one.
- Does not introduce a new "Center" naming registry.

It records the truth as found in the codebase and the existing audits. Rename / collapse work, if ever authorized, belongs to rebuild list §R-05 and a future implementation track.

---

## 7. First implementation priority (if authorized)

Operator decision: collapse **AdminCommandCenter ↔ OperationsCenterCommand**. They share the same backing API family (`/api/operations-center/*`), the same role audience (super-admin), and the same conceptual purpose (cross-portal ops glance). Collapsing them removes one full surface from the inventory, simplifies the IA, and costs nothing in operator capability.

This recommendation is **stated for the priority list, not actioned here**.

Standing rules: No deploy. No GitHub save. No merge.
