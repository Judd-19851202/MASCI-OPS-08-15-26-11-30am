# TRACK 22.1D · Email Safety Recertification

**Verdict:** 🟢 **CERTIFIED.** Three-layer envelope intact after lifespan migration. All 5 bytecode fingerprints re-verified. Zero live emails during Track 22.1D.

## Boot-order invariant preserved

The Resend SDK monkey-patch installed at `server.py` L~105-142 fires at **module import time**, which is **before** the `FastAPI(lifespan=...)` constructor is called. This means:

1. `import server` runs.
2. `_EMAIL_SAFETY_MODE = "strict"` is read from `.env`.
3. `_resend_boot.Emails.send` is replaced by `_blocked_send`.
4. `_resend_boot.send` is replaced by `_blocked_send`.
5. Boot log records `[Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.`
6. **THEN** `FastAPI(..., lifespan=create_lifespan())` runs — the lifespan callable is captured for later invocation.
7. Uvicorn later invokes `orchestrated_lifespan(app)`, which iterates 51 startup handlers.

**At every point in this sequence, `resend.Emails.send` is the safety stub.** No handler in `app.router.on_startup` can obtain the unpatched Resend module.

## Runtime probe (post-Track 22.1D)

```
python -c "import resend; import server; print(resend.Emails.send({'from':'x','to':['y'],'subject':'s','html':'<p/>'}))"
→ {'id': 'blocked_by_email_safety_mode', 'status': 'skipped'}
```

Verified via `test_all_bytecode_fingerprints_still_match_live` which imports `server` and probes.

## SDK-import-order re-verification (lib module hygiene)

`lib/lifespan_bootstrap.py` AST-verified: **does not `import resend`** at module scope. Asserted by `test_lifespan_bootstrap_does_not_import_resend`.

## Fingerprint index re-verification

`verify_locked_bytecode(server.app)` post-22.1D returns:

| Handler | Stored SHA-256 | Live SHA-256 | Match |
|---|---|---|---|
| `_dispatch_auto_email` | `ebf5259dd6b8987d3c5a4ffff9a63abb5898f774711851c293e55672403f6a5b` | (same) | ✅ |
| `_start_safety_digest_cron` | `9aabbd4f4d5f0d1c0b7fede9ef7c35a5ae2640aec49c471182b2857bd7be8604` | (same) | ✅ |
| `_start_operator_digest_cron` | `8f28a846fd2fa23f8b76cc154855a83f547ceeeaf59af2e23f863fa10a241e12` | (same) | ✅ |
| `_start_po_digest_cron` | `5158200a64be314b070e9946fbead935035e5ea823b106a97a60f57ee3528c38` | (same) | ✅ |
| `_dispatch_reminder_scheduler_start` | `5a6e39868e2200962b6ab0cdd0cc200d6b104e18faecd280e62d73a07ae81b75` | (same) | ✅ |

## Three-layer envelope

| Layer | Status |
|---|---|
| 1 · SDK monkey patch at `server.py` L~105-142 | ✅ Position untouched (still before all decorators) |
| 2 · `_dispatch_auto_email` strict / TEST_ short-circuit | ✅ Bytecode fingerprint verified |
| 3 · `TEST_` payload prefix guardrail (Track 21.2E-1) | ✅ Enforced by `test_track_21_2e1_payload_canonicalization.py` |

## Boot log evidence

```
2026-07-04 16:37:36 - server - WARNING - [Track 21.2] EMAIL_SAFETY_MODE=strict — Resend SDK patched. No live email can leave this pod.
...
2026-07-04 16:37:51,360 - lib.lifespan_bootstrap - INFO - [track-22.1d] lifespan.startup: complete
```

The Resend patch log line comes **before** any lifespan handler runs — proving import-order safety.

## Verdict

🟢 **EMAIL SAFETY RECERTIFIED.** SDK patch position untouched. All fingerprints match. Zero live emails during the 207-test lock envelope.
