# TRACK 22.1I.1 · Bytecode Baseline

## New fingerprint added
| Handler | SHA-256 | Locked in track |
|---|---|---|
| `_start_backup_scheduler` | `c7d29e0072aa7578855271dfd5d63a048b0f10d0d0d7bbc6819488d35b378a73` | **22.1I.1** |

## Rationale
Backup scheduling is safety-critical. A silent edit to `_start_backup_scheduler` could delay or disable production backups without any visible symptom until data loss occurred. The SHA-256 lock ensures any body change fails CI.

## Storage
- `memory/BYTECODE_FINGERPRINTS/_start_backup_scheduler.sha256.txt`
- `memory/BYTECODE_FINGERPRINTS/INDEX.json` (`_start_backup_scheduler` key added)

## Complete locked set (post-22.1I.1 · 6 fingerprints)
| Handler | SHA-256 |
|---|---|
| `_dispatch_auto_email` | `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b` |
| `_dispatch_reminder_scheduler_start` | `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` |
| `_start_backup_scheduler` | `c7d29e0072aa7578855271dfd5d63a048b0f10d0d0d7bbc6819488d35b378a73` |
| `_start_operator_digest_cron` | `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` |
| `_start_po_digest_cron` | `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` |
| `_start_safety_digest_cron` | `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` |

## Runtime verification
`lib.scheduler_bootstrap.verify_locked_bytecode(app)` post-migration:
```json
{"checked": 6, "ok_count": 6, "drift_count": 0, "missing_count": 0, "clean": true}
```

## Update policy
Only ever update a fingerprint alongside an approved code change that has:
1. Its own track ID
2. A justified body edit
3. A parity harness proof
4. Testing subagent verification

Silent updates are forbidden.
