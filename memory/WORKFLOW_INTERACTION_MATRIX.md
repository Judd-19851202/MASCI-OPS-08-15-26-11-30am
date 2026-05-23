# WORKFLOW INTERACTION MATRIX
**Audit date:** 2026-05-23
**Purpose:** Role × Workflow grid. CAN (currently has access) vs SHOULD (operator-policy-correct access).

Cells: `R` = read · `W` = write · `R*` = scoped read · `—` = none · `R/-` = current/should mismatch
🟢 = aligned with policy · 🔴 = current does not match should

---

## Matrix

| Workflow | Admin | HR | Safety | PM | FL | Dispatch | Shop |
|---|---|---|---|---|---|---|---|
| **Employee master** | W | W | R | R* | — | — | — |
| **Employee soft-delete** | W | — | — | — | — | — | — |
| **Employee lifecycle history** | W | W | R | R* | — | — | — |
| **Accountability timeline 🆕** | R | R | R | — | — | — | — |
| **Compliance Brief PDF 🆕** | R | R | R | — | — | — | — |
| **Safety training records (create)** | W | W 🆕 | W | — | — | — | — |
| **Safety training records (hard delete)** | W | — 🟢 | W | — | — | — | — |
| **Safety training records (read)** | R | R | R | **—/R\*** 🔴 | **—/R\*** 🔴 | — | — |
| **Safety documents (create/read)** | W | W 🆕 | W | **—/R\*** 🔴 | **—/R\*** 🔴 | — | — |
| **Equipment issuance / PPE (create)** | W | — | W | — | — | — | — |
| **Equipment issuance / PPE (read)** | R | R | R | **—/R\*** 🔴 | **—/R\*** 🔴 | — | — |
| **Equipment training (create)** | W | — | W | — | — | — | — |
| **Incidents (create)** | W | — | W | W | W (via leadership) | — | — |
| **Incidents (list)** | R | **—/R** 🔴 | R | R | **—/R\*** 🔴 | **—/R\*** 🔴 | — |
| **Incidents (closeout)** | W | — | W | — | — | — | — |
| **CAPAs (create + close)** | W | — | W | — | — | — | — |
| **CAPAs (read)** | R | **—/R** 🔴 | R | **—/R\*** 🔴 | — | — | — |
| **Field Leadership records (create)** | W | — | — | — | W | — | — |
| **Field Leadership records (read)** | R | R | R | R* | R* | — | — |
| **Daily Reports (submit)** | W | — | — | W | W | — | — |
| **Daily Reports (read)** | R | **—/R** 🔴 | — | R* | **—/R\*** 🔴 | **—/R 7d** 🔴 | — |
| **Equipment Inspections / Pre-Op (read)** | R | — | — | R* | **—/R\*** 🔴 | R | R |
| **Equipment Inspections (sign-off)** | W | — | — | — | — | — | W |
| **QA/QC inspections (read)** | R | — | R | R* | **—/R\*** 🔴 | — | — |
| **Driver Qualification dashboard (HR)** | R | R | — | — | — | — | — |
| **Driver Qualification dashboard (Dispatch) 🆕** | R | — 🟢 | — 🟢 | — 🟢 | — 🟢 | R | — 🟢 |
| **Driver Qualification dashboard (FL) 🆕** | R | — 🟢 | — 🟢 | — 🟢 | R | — 🟢 | — 🟢 |
| **CDL Roster Importer 🆕** | W | W | — | — | — | — | — |
| **"Drivers Available Right Now" 🆕** | R | — 🟢 | — 🟢 | — 🟢 | R | R | — 🟢 |
| **Notifications (read own role)** | R | R | R | R | **—/R** 🔴 | **—/R** 🔴 | — |
| **Tasks (read own role)** | R | R | R | R | **—/R** 🔴 | — | — |
| **Project list** | R | R | R | R* | R | R | R |
| **Asset transfers** | W | — | — | — | — | R | — |
| **Fleet status** | R | — | — | R* | R | R | R |

---

## Misaligned cells (🔴) summary

### Reads that SHOULD exist but DO NOT
1. **HR → Incidents list** (DE-3)
2. **HR → CAPAs** (DE-3 corollary)
3. **HR → Daily Reports** (payroll / labor audit)
4. **HR → Notifications fan-out** (training expiring, employee-tied alerts)
5. **PM → Safety training records (scoped to crew)** (DE-4)
6. **PM → Equipment issuance / PPE (scoped to crew)** (DE-4)
7. **PM → CAPAs (scoped to project)** (compliance visibility)
8. **FL → Safety training records (scoped)** (DE-2)
9. **FL → PPE issuance (scoped)** (DE-2)
10. **FL → Incidents on own site** (DE-2)
11. **FL → Equipment inspections on own job** (situational awareness)
12. **FL → Daily Reports (own submissions)** (self-audit)
13. **FL → QA/QC on own project** (foreman closeout owner)
14. **FL → Notifications + Tasks** (DE-5)
15. **Dispatch → Daily Reports 7d window** (asset/crew reconciliation)
16. **Dispatch → Notifications** (asset-hold alerts)

### Writes that should NOT exist (none found)
No portal currently has write authority where they shouldn't. iter353a-era hardening landed cleanly.

### Hard-delete authority correctly restricted
- HR cannot hard-delete safety records → ✅ (uses archive notes-prefix)
- HR cannot hard-delete employees → ✅ (only admin via `/api/admin/employees/{id}`)
- PM / Dispatch / FL / Shop → no delete authority on any compliance record ✅

---

## Color-coded policy alignment summary
- **🟢 ALIGNED (current = should):** 18 cells
- **🔴 MISALIGNED:** 16 cells (all are READS that should exist but don't — write boundaries are clean)
- **— Aligned (correctly absent):** balance

---

## Recommended remediation order
**Tier 1 (single iter · "FL Accountability Mini-Widget" + extension):** GAPS 8, 9, 10, 11, 12, 13, 14
**Tier 2 (single iter · "PM Crew Compliance Lens"):** GAPS 5, 6, 7
**Tier 3 (single iter · "HR OSHA & Labor Reach"):** GAPS 1, 2, 3, 4
**Tier 4 (single iter · "Dispatch Movement Reconciliation"):** GAPS 15, 16
