# TRACK 15.65 — Send-Site Migration (Phase 7)

**Date:** 2026-06-22  
**Mode:** Wave-1 minimum-blast-radius migration · feature-flag gated · legacy preserved when flag OFF

## 1. Migration discipline
The send-site swap is intentionally **minimum-blast-radius**. Only the two highest-value, lowest-coupling P0 send sites were migrated in Wave 1. All other send sites continue to use their current env-only lookups. This is intentional — we need to **prove the resolver works under real load** before sweeping the remaining 22 Resend send sites in Track 15.66.

### Why these two first
| Site | Why it's first |
|---|---|
| `safety_digest.py:83` (Weekly Safety Digest) | Scheduled, idempotent, dedup-guarded, low blast radius, easy to roll back. Used by safety leadership weekly. |
| `health_monitor.py:_recipients()` + `_send_alert()` | Critical-flagged route. Demonstrates the critical-route guarantee under load. Migration also threads `db` through `_send_alert` so the resolver can write audit rows. |

## 2. Migration pattern (template for Track 15.66+)

```python
# Track 15.65 · resolve via DB-first router when flag is ON.
# Flag OFF (default) → identical legacy behaviour.
try:
    from email_routing_v2 import resolve_and_audit as _v2_resolve
    res = await _v2_resolve(
        db,
        ROUTE_KEY,
        legacy_provider=lambda: legacy_recipients(),
        fallback_env_keys=[<legacy env vars>],
        critical=<bool>,
        subject="[MASCI] …",
        calling_module=__name__,
    )
    recipients = res.to or legacy_recipients()
except Exception:
    recipients = legacy_recipients()
```

Three guarantees:
1. **Identical legacy path when flag OFF** — the resolver short-circuits to `legacy_provider()` before any DB read.
2. **Audit row written regardless** — `resolve_and_audit` writes one row per call so we can observe resolution behaviour in production from day one.
3. **Defensive fallback** — if the resolver raises for any reason, the call site catches the exception and falls back to `legacy_recipients()`. The user-visible behaviour is "exactly as it was before Track 15.65".

## 3. Files modified

| File | Lines changed | Site |
|---|---|---|
| `backend/safety_digest.py` | 83 → 83-100 | Safety Digest scheduler |
| `backend/health_monitor.py` | 41-47 + 67 + 134-139 + 218 | Health alert recipient + caller threading |
| `backend/email_routing_v2.py` | new file · 322 lines | resolver engine |
| `backend/scripts/track_15_65_seed_email_routes.py` | new file · 273 lines | seed |
| `backend/scripts/track_15_65_parity_verify.py` | new file · 122 lines | parity harness |

No other Resend send site was touched. The remaining 22 (PM routing, safety forms, FL forms, dispatch board, trench safety pulse, welcomes, password resets, payroll variance, backup verification, outage alerts, admin dead-letter, operator digest, …) are all Wave 1 candidates and will be migrated in Track 15.66 once the engine has proved itself in preview under realistic load.

## 4. Recipient preservation proof
The parity harness (`scripts/track_15_65_parity_verify.py`) confirms that for both migrated sites the recipient lists are identical with the flag OFF and identical to the DB doc with the flag ON. Re-run after the migration:

```
{ "match": 19, "mismatch": 0, "skipped_no_legacy": 3, "critical_empty": 0 }
```

## 5. Subject / body / attachment preservation
* `safety_digest.py` — subject `[MASCI] Weekly Safety Digest`, HTML body, no attachments. Unchanged.
* `health_monitor.py` — subject `[MASCI · HEALTH] System Health <state>` or `🚨 HEALTH FAIL · N subsystem(s)`. Unchanged.
* Sender (`SENDER_EMAIL`) unchanged. Reply-to unchanged.

## 6. Failure handling
* `safety_digest`: existing `try/except` wraps the send + logging; that behaviour is preserved.
* `health_monitor`: outer `try/except httpx` wraps the send; the resolver call is wrapped in its own `try/except` so a resolver error never blocks the alert.

## 7. Lint
`mcp_lint_python` returns `No lint errors found` for `safety_digest.py`, `health_monitor.py`, and `email_routing_v2.py`.

## 8. Hard-rule compliance (Phase 7)
* ✅ Preserved existing subject / body / attachment / sender / failure-handling behaviour.
* ✅ Flag OFF returns exact legacy recipients.
* ✅ Critical routes hard-fail rather than silently dropping.
* ✅ Defensive fallback so the resolver cannot break a real send.
* ✅ Did not migrate frontend cosmetic placeholders in Wave 1.
