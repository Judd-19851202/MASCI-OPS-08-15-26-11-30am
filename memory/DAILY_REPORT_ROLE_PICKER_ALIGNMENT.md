# Daily Report Role Picker Alignment

_Phase V.2 · 2026-05-29._

## Prepared By picker

| Allowed canonical | Allowed label |
|---|---|
| `leadman` | Leadman |
| `foreman` | Foreman |
| `superintendent` | Superintendent |
| `sr_superintendent` | Sr. Superintendent |

Filter accepts canonical values, display labels, OR raw legacy strings (case-insensitive). This means a legacy "Field Supervisor" user (uncertain alias → resolved to `superintendent`) still surfaces in the Prepared By dropdown until the operator finalizes its mapping.

Manual fallback always available — typing a name not on roster shows the banner _"Manual entry — not on field-leadership roster"_ but never blocks submission.

## Superintendent picker

| Allowed canonical | Allowed label |
|---|---|
| `superintendent` | Superintendent |
| `sr_superintendent` | Sr. Superintendent |

Only super-tier roles surface. Foremen / Leadmen do not appear in this picker. Field Supervisor surfaces because it currently aliases to `superintendent` (uncertain).

## Display format

Each option renders as a single line:

```
JOHN SMITH — FOREMAN
JAYMN JUDD — SR. SUPERINTENDENT
ALLEN SMATHERS — SUPERINTENDENT *
```

- Em-dash (`—`) separator.
- Role label is monospace, slate-500, uppercase, `tracking-[0.15em]`.
- An uncertain mapping is suffixed with `*` and rendered in amber-700 so the operator can spot it during review.

## Auto-populate

`NewDailyReport.jsx` reads `getFlUser()` on mount. If a FL user session exists AND the user's role resolves to one of {leadman, foreman, superintendent, sr_superintendent, plus legacy uncertain aliases} AND `data.prepared_by` is empty, the Prepared By field is pre-filled with the FL user's name.

The pre-fill never overwrites a value the foreman has already typed. Manual override remains a single-tap edit.

## Verification

| Probe | Result |
|---|---|
| Prepared By shows leadman + foreman + super + sr_super roles | 🟢 |
| Superintendent picker filters to super-tier | 🟢 (9 users in preview · all super-tier) |
| Display format "Name — Role" with em-dash | 🟢 |
| Uncertain marker `*` rendered | 🟢 |
| Auto-populate from FL user wired | 🟢 (code path verified · no FL session in public smoke) |
| Manual fallback always permitted | 🟢 |
| Existing saved reports render | 🟢 (prepared_by + superintendent are still string fields) |

## Stop condition

🛑 Do not extend pickers to additional roles without operator authorization. Foremen / Leadmen do NOT see super-tier pickers. PM / CEI / Owner pickers remain out of scope.

_End of DAILY_REPORT_ROLE_PICKER_ALIGNMENT.md._
