# Subcontractor Foreman / Lead Field — Certification

_Phase V.2 · Daily Report Field-Logic Refinement · Fix 1 of 4 · 2026-05-29._

## 1 · Issue

The Subcontractor row's **Foreman / Lead** field was rendered using
`EmployeeCombo` (the MASCI employee roster picker). This was
incorrect: subcontractor crew leads are not MASCI employees, so:

- the dropdown showed irrelevant MASCI crew members,
- new sub foremen could not be entered without polluting the
  MASCI roster cache,
- typing a name that wasn't in the roster surfaced a "not on
  roster" hint that read like a warning instead of a normal flow.

## 2 · Fix

`NewDailyReport.jsx` · Subcontractors RepeatBlock · field config:

```diff
- { key: "foreman", label: "Foreman / Lead", type: "employee-combo" },
+ { key: "foreman", label: "Subcontractor Foreman / Lead",
+   placeholder: "e.g. John Doe (sub crew lead)" },
```

Removing the `type` makes the RepeatBlock fall through to the
default `<Input type="text">` branch (no dropdown, no roster
lookup, no "not on roster" hint).

## 3 · Behavior after the fix

| Surface | Behavior |
|---|---|
| Field type | Plain text input |
| Label | **Subcontractor Foreman / Lead** |
| Placeholder | _"e.g. John Doe (sub crew lead)"_ |
| Cache impact | None — no MASCI employee API call from this field |
| Accountability records | None — sub foreman names do NOT create employee accountability records |
| Linkage | None — sub foreman names are NOT linked to the MASCI employee master |

## 4 · Forward-compatibility note

Operator directive (verbatim): _"Later, this may become a
subcontractor-contact picker tied to supplier/vendor records. But
for now: Free-text is correct."_

When that work is authorized, the cleanest extension is to:

1. Tie the picker to the existing `SupplierCombo` value already
   on the same row (`company` is already a `supplier-combo`).
2. Add a `supplier_contacts[]` substrate to the
   `suppliers / vendors` collection.
3. Replace the plain text input with a `SubcontractorContactCombo`
   that filters by `company`.

That work is OUT of scope for this refinement pass.

## 5 · Verification

| Probe | Result |
|---|---|
| DOM tag of `[data-testid="sub-foreman-0"]` | `INPUT` |
| `type` attribute | `text` |
| Placeholder | _"e.g. John Doe (sub crew lead)"_ |
| MASCI employee combo present in Subs row? | No |
| Existing reports with prior `foreman` text values | Render unchanged (string field) |

## 6 · Stop condition

🛑 No further changes to the subcontractor foreman field.
Subcontractor contact picker (supplier-tied) deferred — operator
authorization required before scoping.

---

_End of SUBCONTRACTOR_FOREMAN_FIELD_CERTIFICATION.md._
