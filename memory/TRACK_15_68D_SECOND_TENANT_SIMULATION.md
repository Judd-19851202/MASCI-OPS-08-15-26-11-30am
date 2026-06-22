# TRACK 15.68D · Second-Tenant Simulation

_Generated 2026-06-22_

## Command

```
cd /app/backend && python3 scripts/track_15_67_second_tenant_simulation.py
```

## Result

```
{
  "pass": 40,
  "fail": 0
}
```

40/40 probes pass for the synthetic `track_15_68_tenant_test_delete`
tenant. No probe routes a Customer #2 message to a MASCI recipient. No
probe leaks a MASCI email-address into a Customer #2 envelope.

## Refusal Doctrine Observed

For every personnel-seed table (safety_users, shop_users, hr_users,
pm_routing) the simulation log shows the backend refusing to fall back
to MASCI defaults when a non-MASCI tenant is asked to seed without an
explicit env override:

```
safety_users seed: SAFETY_SEED_USERS unset and tenant is not MASCI —
  refusing to seed MASCI personnel into a non-MASCI tenant.
shop_users  seed: SHOP_SEED_USERS  unset and tenant is not MASCI —
  refusing to seed MASCI personnel into a non-MASCI tenant.
hr_users    seed: HR_SEED_USERS    unset and tenant is not MASCI —
  refusing to seed MASCI personnel into a non-MASCI tenant.
pm_routing: PM_SEED_DIRECTORY unset and tenant is not MASCI —
  PM_TABLE will be empty; unresolved PM events route to
  ADMIN_DEAD_LETTER_TO.
```

This is the desired behavior — Customer #2 must explicitly supply its
own seed list. Track 15.68C added this guard rail; Track 15.68D
re-certifies it.

## Persisted Artefacts

- `/app/test_reports/track_15_67_second_tenant_simulation.json`

## Verdict

✅ **PASS** — second-tenant routing remains isolated. No live blast.
