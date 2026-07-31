# WP-17B Executive Repair Register

## Repair findings
| ID | Priority | Surface | Finding | Disposition | Dependency |
|---|---|---|---|---|---|
| RR-001 | P0 | Admin navigation | Admin V2, Admin V3, and legacy Admin navigation compete | `MERGE` | `WP-17C`, `WP-17D` |
| RR-002 | P0 | Companion hubs | `hub_v2` and `hub_legacy` lanes remain structurally useful but not canonically governed | `HIDE` | `WP-17C` |
| RR-003 | P0 | Entry architecture | Sign-in and portal entry model exposes workspace structure over user intent | `REBUILD` | `WP-17C`, `WP-17F` |
| RR-004 | P0 | Transportation shell | Dual prefix and child-tab model create unnecessary relearning | `MERGE` | `WP-17C`, `WP-17D` |
| RR-005 | P0 | Terminology | Eight conflict groups still exist in live source | `STANDARDIZE` | `WP-17F` |
| RR-006 | P1 | Shop hub | High-value but overloaded command center | `SPLIT` | `WP-17E` |
| RR-007 | P1 | Admin IA | Operations/config/governance/recovery all compete at same depth | `MODERNIZE` | `WP-17C` |
| RR-008 | P1 | Form language | Success/error/required-field patterns differ by portal | `STANDARDIZE` | `WP-17D`, `WP-17E` |
| RR-009 | P1 | Table density | Tables vary widely in density and action affordance | `REFINE` | `WP-17D` |
| RR-010 | P1 | Coaching/help | Help placement and “Training Center” reachability vary by portal | `STANDARDIZE` | `WP-17F` |
| RR-011 | P1 | Executive discoverability | Executive surfaces rely too heavily on Admin path knowledge | `UNHIDE` | `WP-17C` |
| RR-012 | P1 | Historical intake | HR/Safety/Asset intake routes are valid but too easy to miss | `UNHIDE` | `WP-17C` |
| RR-013 | P2 | Internal preview routes | `_internal/*` surfaces should remain certification-only | `HIDE` | `WP-17H` |
| RR-014 | P2 | Retired placeholders | Limited legacy surfaces should be formally retired after route canon settles | `REMOVE` | `WP-17H` |
| RR-015 | P2 | Icon semantics | Some object/icon mappings differ by portal | `STANDARDIZE` | `WP-17D` |
| RR-016 | P2 | Leadership shell | Leadership and Field Leadership need clearer role framing | `MODERNIZE` | `WP-17C`, `WP-17F` |

## Findings by disposition
| Disposition | Count |
|---|---:|
| KEEP | 0 |
| REFINE | 1 |
| STANDARDIZE | 4 |
| MODERNIZE | 2 |
| MERGE | 2 |
| SPLIT | 1 |
| REMOVE | 1 |
| HIDE | 2 |
| UNHIDE | 2 |
| REBUILD | 1 |