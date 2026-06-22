# TRACK 15.65 — Parity Verification (Phases 8 + 9)

**Date:** 2026-06-22  
**Harness:** `backend/scripts/track_15_65_parity_verify.py`

## 1. What the harness does
For every seeded route, the harness resolves recipients twice — once with `EMAIL_ROUTING_V2=false` (legacy env path) and once with `EMAIL_ROUTING_V2=true` (DB-first path) — and compares the recipient sets. The harness:

* Sends ZERO real emails.
* Writes ZERO audit rows (uses bare `resolve(...)`, not `resolve_and_audit(...)`).
* Returns exit `0` only when `mismatch == 0` AND `critical_empty == 0`.
* Persists a machine-readable JSON to `/app/test_reports/track_15_65_parity.json`.
* Persists a markdown summary to `/app/memory/track_15_65_data/parity_summary.md`.

## 2. Latest result (2026-06-22 14:59 UTC)

```json
{
  "match": 19,
  "mismatch": 0,
  "skipped_no_legacy": 3,
  "critical_empty": 0
}
```

**19/19 routes match. 0 mismatches. 0 critical routes resolving to empty under V2.**

The 3 `skipped_no_legacy` rows are routes that intentionally have no legacy env-only equivalent (`EXECUTIVE_DIGEST`, `ACCOUNT_INVITES_FROM`, `PASSWORD_RESET_MONITORING_TO`) — the DB doc is the only source of truth. The harness reports them as `match: true` and `skipped: true` so the route count reconciles to 19.

## 3. Per-route summary (excerpt)

| Route | crit | match | flag-off src | flag-on src |
|---|---|---|---|---|
| `COMPLIANCE_ALWAYS_CC` | False | ✅ | legacy | db |
| `SAFETY_FORMS_TO` | False | ✅ | legacy | db |
| `BACKUP_ALERTS` | **True** | ✅ | legacy | db |
| `HEALTH_ALERTS` | **True** | ✅ | legacy | db |
| `OUTAGE_ALERTS` | **True** | ✅ | legacy | db |
| `SUPER_ADMIN_TO` | **True** | ✅ | legacy | db |
| `PASSWORD_RESET_MONITORING_TO` | False | ✅ | disabled | disabled |

Full table at `/app/memory/track_15_65_data/parity_summary.md`.

## 4. Route test-send safety (Phase 9)

The Wave-1 design forbids automated harnesses from triggering real Resend sends:

1. The parity harness uses `v2.resolve(...)` only — no audit row, no send.
2. Send-site migration code paths still respect `AUTO_EMAIL_REPORTS=false` (preview default) before any Resend API call.
3. The existing `/api/admin/email-routing/test` endpoint requires an admin token and an explicit `to` address; it cannot blast a production distribution list.
4. The migrated `safety_digest.py` and `health_monitor.py` send paths sit behind the existing `AUTO_EMAIL_REPORTS` kill-switch — preview is `false`, so even with the V2 flag ON, no real email fires.

## 5. Empty critical route guarantee
* Seed script refuses to write a critical route with empty `to`.
* Resolver raises `UnconfiguredCriticalRouteError` if V2 lands on empty.
* Parity harness counts critical-empty separately and fails on non-zero.

The combination ensures **no path leaves a critical route silently unconfigured**.

## 6. Hard-rule compliance (Phases 8 + 9)
* ✅ No live emails sent during testing.
* ✅ No real distribution list blasted.
* ✅ Pass/fail criteria documented.
* ✅ Critical-route empty count tracked and gated.
* ✅ Output JSON + markdown for reproducibility.
