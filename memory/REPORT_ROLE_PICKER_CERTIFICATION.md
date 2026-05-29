# Report Role Picker — Certification

_Phase V.2 · Daily Report Field-Logic Refinement · Fix 2 of 4 · 2026-05-29._

## 1 · Issue

The Daily Report header had two free-text inputs for
**Prepared By** and **Superintendent**. Field users had to type the
full name every day — slow on a glove-rated iPad, prone to spelling
drift, and produced no operational linkage to the existing Field
Leadership roster (`field_leadership_users` collection).

## 2 · Fix

Three surfaces touched:

### 2.1 · Backend — new public endpoint

```
GET /api/field-leadership-roster
GET /api/field-leadership-roster?role=Superintendent
```

- **No auth required.** Daily Report is a public form (`/daily/new`);
  the picker cannot demand admin / HR / FL tokens.
- Returns ONLY `name`, `role`, `is_active`. No emails, no phones, no
  password / session hints. No PII.
- Sorted by name (inherited from `list_fl_users`).
- Optional `role` query param filters server-side.
- Envelope: `{items: [...], count: N, allowed_roles: [...]}`.

Mounted inside `routes/field_leadership_portal.py` so the FL doctrine
boundary stays in one place. Only **active** users surface.

### 2.2 · Frontend — `components/FlUserCombo.jsx` (NEW)

Mirror of `EmployeeCombo` / `SupplierCombo` UX:

- Module-level cache (so a transient network blip doesn't poison
  every later render).
- Auto-retry up to 2× on empty fetch.
- `allowedRoles` prop — client-side filter (server filter is also
  available · doubled up for defensive UX when the picker is
  re-mounted with a different role list).
- **Manual fallback always allowed.** Even with `allowedRoles`
  set, the user can type any name and the form accepts it.
  Banner: _"Manual entry — not on field-leadership roster"_
  (slate · uppercase · monospace · non-punitive).
- 200-row visible cap; search box folds into the input itself.
- `data-testid` per option (`{testId}-option-{i}`), per toggle
  (`{testId}-toggle`), per input (`{testId}-input`).

### 2.3 · NewDailyReport.jsx wiring

```jsx
<FlUserCombo
  value={data.prepared_by}
  onChange={(v) => set("prepared_by", v)}
  placeholder="Foreman / General Foreman / Superintendent"
  testId="prepared-by"
  allowedRoles={[
    "Foreman", "General Foreman", "Field Supervisor",
    "Working Supervisor", "Truck Boss",
    "Superintendent", "Senior Superintendent",
  ]}
/>

<FlUserCombo
  value={data.superintendent}
  onChange={(v) => set("superintendent", v)}
  placeholder="Superintendent / Senior Super"
  testId="superintendent"
  allowedRoles={[
    "Superintendent", "Senior Superintendent", "Field Supervisor",
  ]}
/>
```

Stored data shape is **unchanged** — `prepared_by` and
`superintendent` remain free-text string fields on the
`daily_reports` document. Existing reports render untouched.

## 3 · Manual fallback contract (operator-mandated)

> _"Still allow manual fallback if name is not found. Do not block
> report submission if picker data is missing. Preserve existing
> stored text fields. Do not introduce schema-breaking changes."_

All four mandates honored:

| Mandate | Honored by |
|---|---|
| Manual fallback | `<Input>` accepts any typed string · banner appears but does not block |
| No submission block on missing picker data | `validate()` only requires `prepared_by.trim()` (existing rule) · picker absence/empty roster never blocks |
| Preserve stored text fields | `prepared_by`, `superintendent` remain string fields server-side |
| No schema-breaking changes | Zero migrations · zero new collections · zero new required fields |

## 4 · Allowed roles (current preview snapshot)

Server returns (from preview DB): `["Field Supervisor", "Foreman",
"Superintendent", "Truck Boss", "Working Supervisor"]` ·
24 active users.

The Prepared By picker also accepts `"General Foreman"` and
`"Senior Superintendent"` — once those roles are seeded into
`field_leadership_users` they appear immediately without any
frontend change.

## 5 · Verification

| Probe | Result |
|---|---|
| `GET /api/field-leadership-roster` returns 200 | 🟢 24 active users |
| Response is PII-free (no email · no phone · no password) | 🟢 |
| Prepared By picker opens, shows roster | 🟢 |
| Superintendent picker filters to super-tier | 🟢 |
| Manual fallback (typing a name not on roster) | 🟢 banner appears · submission still permitted |
| Existing saved reports render | 🟢 string field unchanged |
| Backend regression (89/89) | 🟢 |

## 6 · Stop condition

🛑 No further role-picker work. Future surface (PM picker · CEI
picker · Owner picker) requires operator authorization and a
matching public roster endpoint per role family.

---

_End of REPORT_ROLE_PICKER_CERTIFICATION.md._
