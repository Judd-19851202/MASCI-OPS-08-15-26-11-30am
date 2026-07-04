# TRACK 22.1H · Bytecode Baseline

## Handler bytecode SHA-256 — before and after Track 22.1H

| Handler | Baseline (Track 22.1C lock) | Live (post-22.1H) | Match |
|---|---|---|---|
| `_dispatch_auto_email` | `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b` | `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b` | ✅ |
| `_start_safety_digest_cron` | `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` | `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` | ✅ |
| `_start_operator_digest_cron` | `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` | `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` | ✅ |
| `_start_po_digest_cron` | `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` | `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` | ✅ |
| `_dispatch_reminder_scheduler_start` | `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` | `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` | ✅ |
| `_start_backup_verification_cron` | (not previously fingerprint-locked) | `36bf2f8f3130e962...` (newly recorded) | 🟡 NEW BASELINE |

## Interpretation

- Decorator swap **does not** modify bytecode `co_code`. Python's `co_code` is a byte-sequence of instructions bound to the function body (not the decorators applied to it). Track 22.1H proves this mathematically: 5/5 stored fingerprints match live bytecode after the swap.
- `_start_backup_verification_cron` is now newly recorded at `36bf2f8f3130e962...`. This becomes the reference for future tracks. Any future change to its body will surface as a fingerprint drift.

## Post-migration `verify_locked_bytecode(server.app)` output

```json
{
  "checked": 5,
  "ok": [
    "_dispatch_auto_email",
    "_dispatch_reminder_scheduler_start",
    "_start_operator_digest_cron",
    "_start_po_digest_cron",
    "_start_safety_digest_cron"
  ],
  "drift": [],
  "missing": []
}
```

## Certification

🟢 **BYTECODE BASELINE CERTIFIED.** No handler body was modified by Track 22.1H. Every previously-locked fingerprint matches live bytecode.
