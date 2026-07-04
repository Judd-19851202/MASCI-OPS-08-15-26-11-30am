# TRACK 22.3 · OpenAPI / Validation Parity

## Runtime enumeration (before → after)
| Metric | Before | After | Δ |
|---|---:|---:|---:|
| Routes (endpoints) | 1,441 | 1,441 | 0 |
| Method count | 1,445 | 1,445 | 0 |
| OpenAPI paths | 1,264 | 1,264 | 0 |
| Middleware chain | 7 | 7 | 0 |
| CORS allow_origins config | unchanged | unchanged | 0 |
| CORS allow_origin_regex config | unchanged | unchanged | 0 |

## Validation-parity guarantee
For each of the 12 touched parameters:
- **Same regex string** (identical characters, including anchors and character-class delimiters).
- **Same escaping semantics** (raw-string prefix `r"..."` preserved where present).
- **Same required/optional status** (`Query(..., pattern=...)` still required, `Query(default=None, pattern=...)` still optional with `None` default, `Query("today", pattern=...)` still defaults to `"today"`).
- **Same alias / description / example fields** — none were changed.
- **Same order of Query/Path arguments** — none reordered.

## OpenAPI schema representation
Pydantic v2 emits the constraint under the `pattern` key in the OpenAPI parameter schema regardless of whether the source code used `regex=` (backward-compat) or `pattern=`. Therefore:
- OpenAPI JSON path count: unchanged.
- OpenAPI parameter `pattern` values: unchanged (same strings).
- OpenAPI required/optional flags: unchanged.

## Verdict
🟢 **Full parity certified.** No API contract change. No client-observable difference.
