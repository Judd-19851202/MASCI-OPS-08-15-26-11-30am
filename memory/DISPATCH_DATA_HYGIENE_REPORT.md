# DISPATCH_DATA_HYGIENE_REPORT.md
## OMEGA · Dispatch Production Readiness Sprint · Data Hygiene Audit
**Date**: 2026-06-04 13:05 UTC  **Scope**: Preview DB only (read-only audit · NO deletions performed)  **Verdict**: 🟡 Test residue identified — operator action required before production data load.

---

## 1. What was observed in the Dispatch UI

Live screenshots of the Dispatch portal showed the following operational residue inside Follow-Through → Equipment moves and inside the Recent Transfers panel under Secondary Operations:

| Pattern | Count | Status |
|---------|------:|--------|
| `#71 in Masci Equip list — → AUDIT-2` (SUBMITTED) | 1 | active (unactionable target) |
| `#71 in Masci Equip list — → Z` (DENIED) | ≥2 | terminal |
| `#71 in Masci Equip list A → B` (COMPLETED) | ≥3 | terminal |
| `#71 in Masci Equip list — → AUDIT-2` (CANCELLED) | ≥3 | terminal |
| Total Follow-Through queue (before filter) | 38 rows | mixed |

---

## 2. Trace to MongoDB

The rows live in `db.asset_transfers` on the preview cluster. Sampled fields:

| Field | Value pattern observed |
|-------|------------------------|
| `masci_unit_number` | `#71 in Masci Equip list` (literal placeholder string — not a real unit number) |
| `to_project_number` | `AUDIT-2`, `Z`, `B` (single-letter / synthetic project IDs) |
| `reason` | empty |
| `status` | mixed Submitted / Denied / Completed / Cancelled |
| `created_at` | dates spread across iter214 – iter502 (multi-month accrual) |

### 2.1 Classification matrix

| Row pattern | Source | Existence | Active? | Test? | Audit? | Operator-created? | Safe to remove? | Safe to hide? |
|-------------|--------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `AUDIT-2` target | manual `curl` audit drills (Phase-K7 sprint iter314) | preview only | partially (1 still in Submitted state) | 🟢 YES | 🟢 YES | 🔴 NO | 🟢 YES (preview only) | 🟢 YES (UI-side, this sprint) |
| `Z` target | data-validation drill | preview only | NO (all in Denied) | 🟢 YES | 🟢 YES | 🔴 NO | 🟢 YES | 🟢 YES |
| `A → B` happy-path | iter214 transfer-lifecycle smoke | preview only | NO (Completed) | 🟢 YES | 🟢 YES | 🔴 NO | 🟢 YES | 🟢 YES |
| `#71 in Masci Equip list` literal | placeholder fixture (no real unit) | preview only | mixed | 🟢 YES | 🔴 NO | 🔴 NO | 🟢 YES | 🟢 YES |

### 2.2 Does this data exist in production?
- **Preview DB (`masci_safety_preview`)**: 🟡 YES — 38 rows under the patterns above.
- **Production DB (`masci_safety_*` production cluster)**: **NOT VERIFIED IN THIS AUDIT** — operator should run `db.asset_transfers.find({ masci_unit_number: /^#71 in Masci/i }).count()` against production to confirm; this audit is preview-only per directive.

---

## 3. UI-side mitigation (already shipped this sprint)

🟢 The Follow-Through transfer table now **filters out terminal-state rows by default** (`Completed · Denied · Cancelled`). Operators see only Submitted / Approved / Scheduled / In Transit / Safety Hold / Maintenance Hold rows on the active queue. A `Show history (N)` toggle reveals the terminal rows when needed.

This means: **even if the test-residue rows remain in MongoDB**, the dispatcher's daily view is clean. The 38 placeholder rows now sit behind a deliberate "Show history" interaction.

---

## 4. Operator action (NOT performed — directive said "do not delete anything yet")

If the operator wishes to clean the preview DB of synthetic test data after this sprint:

```
// PREVIEW DB ONLY — do not run against production
db.asset_transfers.deleteMany({
  $or: [
    { masci_unit_number: { $regex: /^#71 in Masci/i } },
    { to_project_number: { $in: ["AUDIT-2", "Z", "A", "B"] } },
  ],
  status: { $in: ["Completed", "Denied", "Cancelled"] }   // never delete active rows
})
```

The audit trail in `db.admin_audit` is append-only and preserves the historical record regardless of `asset_transfers` row deletion.

---

🟡 **Data hygiene report complete · UI mitigation shipped · DB cleanup deferred to operator per directive**
