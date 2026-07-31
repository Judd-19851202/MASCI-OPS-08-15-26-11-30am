# WP-17B Terminology Standard

## Exact conflict groups: `8`

| Conflict group | Current source occurrences | Canonical standard | Disposition |
|---|---|---|---|
| Employee vs Worker | employee `1148` / worker `260` | Use **Employee** in product UI; reserve Worker for legal/source-context only | `STANDARDIZE` |
| Project vs Job | project `1514` / job `927` | Use **Project** for navigation/pages; keep Job Number as identifier | `STANDARDIZE` |
| Incident vs Issue | incident `672` / issue `175` | Use **Incident** for safety events; Issue only for generic defects | `STANDARDIZE` |
| Archive vs Delete | archive `250` / delete `394` | Archive for retained records, Delete only for irreversible removal | `STANDARDIZE` |
| Orientation vs Onboarding | orientation `87` / onboarding `42` | Transportation uses **Orientation**; broader HR language may say Onboarding only where not cert-specific | `REFINE` |
| Driver vs Operator | driver `866` / operator `612` | Driver for Transportation/Dispatch; Operator for equipment/use-role contexts only | `REFINE` |
| Dispatch vs Transportation | dispatch `1253` / transportation `402` | Product family = **Transportation Operations**; Dispatch = live-board function within it | `MERGE` |
| Meeting vs Toolbox | meeting `229` / toolbox `50` | Canonical label = **Safety Meeting** with Toolbox indexed as alias | `STANDARDIZE` |

## Executive rule
- No new portal, nav, or dashboard label may be approved in WP-17C unless it conforms to this file.