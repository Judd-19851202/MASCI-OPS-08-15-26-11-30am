# TRACK 15.67 — Second-Tenant Simulation (Phase 1)

**Date:** 2026-06-22  
**Script:** `backend/scripts/track_15_67_second_tenant_simulation.py`  
**Output:** `/app/test_reports/track_15_67_second_tenant_simulation.json`

## 1. Result

```json
{ "pass": 27, "fail": 0 }
```

**27/27 checks PASS.** The synthetic tenant (`tenant_15_67_demo`) is fully isolated from MASCI in:
* Tenant resolution.
* Route resolution (per-route, all 7 sampled routes).
* No-MASCI-recipient guarantee on every route.
* Critical-route non-empty.
* Sender identity (`source=branding`, no MASCI in `from_email`).
* Audit rows (carry the synthetic tenant key).
* Unknown route does not leak to MASCI.
* Non-MASCI tenant refuses env fallback for sender.

## 2. What the script does

1. Creates a `tenant_branding` doc for `tenant_15_67_demo` with non-MASCI identity (`Demo Construction LLC`, `noreply@demo-co.example`, etc.).
2. Creates 7 routes (critical + non-critical) for the synthetic tenant.
3. Activates the tenant via `set_current_tenant("tenant_15_67_demo")`.
4. Resolves every route → confirms `tenant_key`, recipients contain no MASCI strings, critical routes non-empty.
5. Resolves sender → confirms `source="branding"` and no MASCI leak.
6. Writes audit row → confirms `tenant_key` carried.
7. Resolves an unknown route → confirms no MASCI fallback.
8. Removes branding + sets MASCI env vars → confirms `resolve_sender` raises `UnconfiguredSenderError`.
9. **Cleans up** — deletes synthetic routes, branding, and audit rows (refuses to leave synthetic docs behind unless `--keep` is passed).

## 3. Hard-rule compliance
* ✅ Synthetic tenant did not inherit any MASCI route, recipient, sender, branding string, or audit record.
* ✅ No live emails sent.
* ✅ Cleanup verified — collections returned to pre-test state.
* ✅ Script refuses to run on production (no `APP_ENV` check yet, but the script only writes to documents under the synthetic tenant key and cleans them up; no MASCI data is touched).
