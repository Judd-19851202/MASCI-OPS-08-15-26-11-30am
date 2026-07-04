# TRACK 22.1L · Bytecode Fingerprints

## Retired closure (pre-migration reference only)
| Function | SHA-256 |
|---|---|
| `build_command_center_router.<locals>._startup` (closure) | `9e1a377eddcdb931171303be1d0eaaf22bfd92d788affa6a71e658733176ad4e` |

This function no longer exists — the `@router.on_event("startup")` decorator and closure were removed.

## New locked fingerprint
| Handler | SHA-256 | Locked in track |
|---|---|---|
| `_command_center_seed_defaults` | `b2976f4460227c5402564de80fe32ee1d588f9f185ebd7ba97a39277989743cf` | **22.1L** |

## Complete locked set (post-22.1L · 8 fingerprints)
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

## Runtime verification
```json
{"checked": 8, "ok_count": 8, "drift_count": 0, "missing_count": 0, "clean": true}
```

## Storage
- `memory/BYTECODE_FINGERPRINTS/INDEX.json` (`_command_center_seed_defaults` key added)
- `memory/BYTECODE_FINGERPRINTS/_command_center_seed_defaults.sha256.txt`

## Why the new handler bytecode differs from the old closure
- Old closure: `co_freevars=('db',)` — reads `db` from enclosing scope via `LOAD_DEREF`.
- New handler: `co_freevars=()` — imports `_seed_defaults` locally inside try, reads `db` from module scope via `LOAD_GLOBAL`.
- **Semantic behavior**: identical — same idempotent seed, same silent-on-error, same argument.
- **Bytecode**: intentionally different (closure vs. module-level function compilation). This is expected and documented in `TRACK_22_1L_STARTUP_HANDLER_INVENTORY.md`.
