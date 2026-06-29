# Track 19.03 · Historical Snapshot Rules

## Rule

HR is the absolute source of truth for **current** employee identity.
Once an operational record (Daily Report, Safety Meeting, Pre-Op, JHP,
QA/QC inspection, Incident, Near Miss, Equipment Inspection, Training
Roster, Time Card, etc.) is **submitted**, the employee selection that
was captured at submit-time becomes the **historical snapshot** for
that record and **must never be retroactively rewritten**.

This means:

| Surface | Before submit | After submit |
| --- | --- | --- |
| Form picker / dropdown / autocomplete | Live HR roster (active only) | n/a |
| Submitted record display | n/a | The captured `name` / `employee_id` snapshot, **even if HR later changes the employee's name, lifecycle, or terminates them** |

## Why

Operational records are legal artefacts. A Daily Report dated
2025-09-12 listing "John Doe — Concrete Foreman · #5421" must continue
to say "John Doe — Concrete Foreman · #5421" forever, regardless of
whether John Doe is later terminated, renamed, or merged. Rewriting
historical attribution would destroy auditability and would be a
regulatory red flag for OSHA / DOT / insurance reviews.

The HR Source-of-Truth contract therefore makes a **strict
selection-time vs. submit-time distinction**:

* **Selection-time (picker)**: live read of HR roster. Active
  employees only. Inactive / Terminated / Resigned / Retired are
  hidden unless an operator explicitly enables `Show inactive`.
* **Submit-time (write)**: the record persists whatever
  `{ name, employee_id, role, trade, crew, lifecycle_status }`
  the picker provided at submit. Subsequent HR mutations do **not**
  rewrite this stored snapshot.

## Implementation

* The frontend pickers (`EmployeeCombo`, `trench/EmployeePicker`, and
  all dropdowns that subscribe to `lib/hrRoster.js`) call the
  canonical roster endpoint **only at selection time**. The
  selection produces a denormalized blob — the form stores both the
  free-text `name` and (where available) the canonical
  `employee_id` / `id` so the record is queryable later.
* The submit handler writes the selected blob to the record
  collection. It does **not** re-resolve the name via the live HR
  roster.
* The display path renders the **stored** name / id / role on the
  submitted record. No lookup against `db.employees`.
* HR mutations (rename, lifecycle change, reactivate) emit the
  `hr:roster-changed` bus event, which invalidates **picker** data
  only. It does **not** touch already-persisted record snapshots.

## Where historical drift CAN show up — and why that's OK

* **Daily Report list / preview pages**: render stored snapshot. A
  terminated employee shows their captured name. ✓ correct.
* **Safety Meeting attendance**: rendered from the stored attendee
  array. A renamed employee continues to show their old name on
  prior meetings, and their new name on subsequent meetings. ✓
  correct.
* **HR reports / lifecycle timeline**: walk forward through
  `employee_lifecycle_events` and `status_history` on the live
  `db.employees` document. Always reflect current truth. ✓ correct.
* **Accountability Timeline (employee-scoped)**: joins by
  `employee_id`, surfaces both stored snapshot text (for context)
  and live HR truth (for current state). ✓ correct.

## Selection vs. snapshot in code

```js
// Picker (live)
const items = await fetchHrRoster();         // /api/hr/employee-roster
const picked = items.find(/* ... */);

// Submit (snapshot)
await api.post("/daily-reports", {
  ...form,
  crew: [{
    name: picked.name,                       // captured at this moment
    employee_id: picked.employee_id || "",
    id: picked.id,
    role: picked.role || "",
  }],
});

// Display (stored)
report.crew.forEach(c => render(c.name));    // NEVER re-resolve via HR roster
```

## Non-goals

* No retroactive rename of historical records. HR Save NEVER mutates
  prior submissions.
* No tombstone records: terminated employees still appear on their
  historical work, with their historical name and metadata.
* No "current name overlay" toggle on historical records. The
  stored snapshot is the legal record.

## Lock-in test

`test_track_19_03_hr_roster_source_of_truth.py::test_historical_snapshot_doc_documents_rule`
asserts the existence of this document. The integration suite
(`testing_agent_v3_fork`) verifies HR rename does NOT mutate the
prior Daily Report's stored attendee name.
