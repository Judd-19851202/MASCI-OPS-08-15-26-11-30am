# TRACK 22.1K · Bytecode Fingerprints

## New fingerprint
| Handler | SHA-256 | Track |
|---|---|---|
| `shutdown_db_client` | `a7db2b0122a4d9405610d78c2b44de8cd8314531ae688d554116b83e332e7c9b` | **22.1K** |

## Complete locked set (post-22.1K · 9 fingerprints)
| Handler | SHA-256 |
|---|---|
| `_command_center_seed_defaults` | `b2976f4460227c5402564de80fe32ee1d588f9f185ebd7ba97a39277989743cf` |
| `_dispatch_auto_email` | `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b` |
| `_dispatch_reminder_scheduler_start` | `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` |
| `_iter453_6_flip_ready_flag` | `3ad0b42c02c53519565c03606ae0024b903a6db7c71c42578e406541e89a8fc4` |
| `_start_backup_scheduler` | `c7d29e0072aa7578855271dfd5d63a048b0f10d0d0d7bbc6819488d35b378a73` |
| `_start_operator_digest_cron` | `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` |
| `_start_po_digest_cron` | `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` |
| `_start_safety_digest_cron` | `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` |
| `shutdown_db_client` | `a7db2b0122a4d9405610d78c2b44de8cd8314531ae688d554116b83e332e7c9b` |

## Runtime verification (post-migration)
```json
{"checked": 9, "ok_count": 9, "drift_count": 0, "missing_count": 0, "clean": true}
```

## Storage
- `memory/BYTECODE_FINGERPRINTS/INDEX.json` — new `shutdown_db_client` key.
- `memory/BYTECODE_FINGERPRINTS/shutdown_db_client.sha256.txt`

## Why the shutdown handler's bytecode is byte-identical
The migration was a **single decorator swap**: `@app.on_event("shutdown")` → `@register_shutdown_step("shutdown")`. The function body (`try: … cancel; except: pass; client.close()`) is unchanged. `co_code` compilation is identical because it depends only on the body, not the decorator.

## CI enforcement
`test_track_22_1k_shutdown_migration.py::test_bytecode_fingerprints_all_clean_at_9` fails if any of the 9 locked SHA-256 hashes drift. This means:
- Any silent edit to a safety-critical handler body fails CI.
- Any accidental replacement of a decorator that changes function identity fails CI.
- Adding a NEW locked fingerprint requires an explicit track (spec + audit + tests).
