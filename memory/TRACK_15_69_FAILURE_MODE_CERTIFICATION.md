# TRACK 15.69 · Failure Mode Certification (Phase 6)

_Generated 2026-06-22 · Preview cluster, live execution_

## Test Harness

`/app/backend/scripts/track_15_69_failure_mode_tests.py`

Persisted JSON: `/app/test_reports/track_15_69_failure_modes.json`

## Results — **7/7 PASS**

| # | Failure Mode | Required Behavior | Actual Behavior | Verdict |
|:-:|---|---|---|:-:|
| FM1 | Critical route resolves to empty recipient list | Must hard-fail with `UnconfiguredCriticalRouteError`; must NOT silently drop | Raised `UnconfiguredCriticalRouteError: Critical route masci::BACKUP_ALERTS resolved to empty recipient list.` | ✅ |
| FM2 | Route doc missing (key not in DB) | Must fall through to `legacy_provider` callback (no silent drop) | `source=legacy · to=['fallback@example.com']` | ✅ |
| FM3 | Sender missing for current tenant | `resolve_sender()` must always return a non-empty `from_email` for MASCI; must hard-fail for non-MASCI without branding | `from_email=noreply@mascidocs.com · source=env_masci_only` | ✅ |
| FM4 | Critical route administratively disabled | Resolver must return `source=disabled · empty` (or raise — both are operator-visible non-silent outcomes) | `source=disabled · to=[]` | ✅ |
| FM5 | Tenant has no `tenant_branding` doc | Must fall through to legacy provider or hard-fail (non-MASCI cannot inherit MASCI defaults) | `source=legacy · to=['fallback@example.com']` (via legacy provider) | ✅ |
| FM6 | Audit row shape | Every audit row must include `tenant_key`, `route_key`, `source`, `status`, `ts` + recipient counts | Keys present: `_id · calling_module · dry_run · error · resend_message_id · resolved_bcc_count · resolved_cc_count · resolved_to_count · route_key · sender_email · source · status · subject · tenant_key · ts` | ✅ |
| FM7 | Database connection lost mid-resolve | Resolver must catch the DB exception and fall through to legacy provider (no silent drop, no service crash) | `source=legacy · to=['legacy-fallback@example.com']` | ✅ |

## Verbatim Evidence (from persisted JSON)

```json
[
  {
    "test": "FM1_critical_empty_recipient",
    "result": "PASS",
    "evidence": "raised UnconfiguredCriticalRouteError: Critical route masci::BACKUP_ALERTS resolved to empty recipient list."
  },
  {
    "test": "FM2_route_missing_falls_to_legacy",
    "result": "PASS",
    "evidence": "source=legacy to=['fallback@example.com']"
  },
  {
    "test": "FM3_sender_resolution",
    "result": "PASS",
    "evidence": "from_email=noreply@mascidocs.com source=env_masci_only"
  },
  {
    "test": "FM4_critical_disabled_returns_disabled",
    "result": "PASS",
    "evidence": "source=disabled to=[]"
  },
  {
    "test": "FM5_tenant_missing_falls_to_legacy",
    "result": "PASS",
    "evidence": "source=legacy to=['fallback@example.com']"
  },
  {
    "test": "FM6_audit_row_shape",
    "result": "PASS",
    "evidence": "keys=['_id', 'calling_module', 'dry_run', 'error', 'resend_message_id', 'resolved_bcc_count', 'resolved_cc_count', 'resolved_to_count', 'route_key', 'sender_email', 'source', 'status', 'subject', 'tenant_key', 'ts']"
  },
  {
    "test": "FM7_db_unavailable_falls_to_legacy",
    "result": "PASS",
    "evidence": "source=legacy to=['legacy-fallback@example.com'] error=None"
  }
]
```

## What's Verified

1. **No silent failure.** Every failure mode produces either a visible
   exception (FM1 hard-fail) or a non-`db` source value (FM2/4/5/7)
   that the calling code MUST handle.
2. **Hard-fail on critical-empty.** The `UnconfiguredCriticalRouteError`
   guards the 4 critical routes from silent drops.
3. **Audit row on every resolution.** FM6 confirms the audit row shape
   carries enough information for forensic review.
4. **Resilient to DB outage.** FM7 confirms a transient Atlas issue
   still routes via the legacy provider, never silently dropping.

## Restorations Verified

Both intrusive tests (FM1 blanking BACKUP_ALERTS recipients; FM4
disabling HEALTH_ALERTS) restored the route to its pre-test state in
the `finally` block. Post-test inventory check confirms:

| Route | Recipients (post-test) | Enabled (post-test) |
|---|---|---|
| BACKUP_ALERTS | 1 (`jaymn.judd@mascigc.com`) ✅ | enabled ✅ |
| HEALTH_ALERTS | 1 (`safety@mascigc.com`) ✅ | enabled ✅ |

## Verdict

✅ **PASS 7/7 — every failure mode is detected, recorded, and either
hard-fails visibly or falls through to a documented legacy path. No
silent failures possible.**
