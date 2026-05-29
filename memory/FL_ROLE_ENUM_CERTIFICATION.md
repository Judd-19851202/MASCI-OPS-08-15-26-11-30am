# FL Role Enum — Certification

_Phase V.2 · 2026-05-29._

## Canonical enum (locked)

```python
FL_CANONICAL_ROLES = {
    "sr_superintendent": "Sr. Superintendent",
    "superintendent":    "Superintendent",
    "foreman":           "Foreman",
    "leadman":           "Leadman",
}
```

- Keys are canonical values used by **permissions / API / dashboard rules**.
- Values are display labels used by **UI**.
- Order in the dict is the ladder order (Sr. Super → Leadman).

## Alias map — HARD (confidently mapped)

```python
FL_ROLE_ALIASES_HARD = {
    "sr. superintendent":      "sr_superintendent",
    "sr superintendent":       "sr_superintendent",
    "senior superintendent":   "sr_superintendent",
    "superintendent":          "superintendent",
    "foreman":                 "foreman",
    "leadman":                 "leadman",
    "crew lead":               "leadman",
    "crewlead":                "leadman",
}
```

## Alias map — UNCERTAIN (operator review required)

```python
FL_ROLE_ALIASES_UNCERTAIN = {
    "general foreman":    ("foreman",        "operator review · could be Foreman or Leadman"),
    "field supervisor":   ("superintendent", "operator review · could be Superintendent or Foreman"),
    "truck boss":         ("leadman",        "operator review · trucking lead role · likely Leadman"),
    "working supervisor": ("foreman",        "operator review · field-working lead · likely Foreman"),
}
```

Each entry resolves to a **proposed canonical default**, but the public roster API surfaces `role_uncertain: true` + `role_uncertain_note: "..."` so the operator can confirm or override.

## Resolver — `_canonical_role(raw_role)`

| Input pattern | `value` | `label` | `uncertain` | `uncertain_note` |
|---|---|---|---|---|
| `"Foreman"` | `foreman` | Foreman | false | null |
| `"Sr. Superintendent"` | `sr_superintendent` | Sr. Superintendent | false | null |
| `"Senior Superintendent"` | `sr_superintendent` | Sr. Superintendent | false | null |
| `"Crew Lead"` | `leadman` | Leadman | false | null |
| `"Field Supervisor"` | `superintendent` | Superintendent | true | "operator review · could be Superintendent or Foreman" |
| `"Truck Boss"` | `leadman` | Leadman | true | "operator review · trucking lead role · likely Leadman" |
| `"Working Supervisor"` | `foreman` | Foreman | true | "operator review · field-working lead · likely Foreman" |
| `"General Foreman"` | `foreman` | Foreman | true | "operator review · could be Foreman or Leadman" |
| anything else | `unknown` | _raw value_ | true | "unrecognized legacy role · operator review required" |

Never raises. UI gets a renderable label regardless of input.

## Public API envelope

```
GET /api/field-leadership-roster
GET /api/field-leadership-roster?role=foreman
```

```jsonc
{
  "items": [
    {
      "name": "ANTHONY GOES",
      "role_value": "foreman",
      "role_label": "Foreman",
      "role_raw": "Foreman",
      "role_uncertain": false,
      "role_uncertain_note": null,
      "is_active": true,
      "role": "Foreman"          // legacy back-compat key
    }
  ],
  "count": 24,
  "canonical_roles": [
    {"value": "sr_superintendent", "label": "Sr. Superintendent"},
    {"value": "superintendent",    "label": "Superintendent"},
    {"value": "foreman",           "label": "Foreman"},
    {"value": "leadman",           "label": "Leadman"}
  ],
  "allowed_roles": [/* legacy back-compat list */]
}
```

## Verification

| Probe | Result |
|---|---|
| Endpoint returns canonical envelope | 🟢 |
| Hard aliases resolve cleanly | 🟢 |
| Uncertain aliases flagged | 🟢 (`Field Supervisor` → uncertain, note present) |
| Unknown roles do NOT silently auto-map | 🟢 (echo raw + `value=unknown`) |
| `?role=foreman` filters server-side | 🟢 |
| Legacy `role` key preserved for back-compat | 🟢 |

🛑 Stop condition: do not rename canonical values without operator authorization.

_End of FL_ROLE_ENUM_CERTIFICATION.md._
