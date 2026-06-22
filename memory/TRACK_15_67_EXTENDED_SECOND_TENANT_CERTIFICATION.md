# TRACK 15.67 · Phase 3 · Extended Second-Tenant Certification

_Status: ✅ CERTIFIED · 2026-06-22_

## Simulation script
`backend/scripts/track_15_67_second_tenant_simulation.py`

## Tenant
- `tenant_key="tenant_15_67_demo"`
- Branding: `Demo Construction LLC`, `noreply@demo-co.example`, etc.
- Routes: 7 demo routes wired (SAFETY_FORMS_TO, HEALTH_ALERTS,
  OUTAGE_ALERTS, BACKUP_ALERTS, SUPER_ADMIN_TO, COMPLIANCE_ALWAYS_CC,
  ADMIN_DEAD_LETTER_TO).

## Result
```
{
  "pass": 40,
  "fail": 0
}
```

## Coverage map

| # | Check | Status |
|---:|---|:---:|
| 1 | Tenant resolution returns demo | ✅ |
| 2-22 | All 7 routes are tenant-scoped, no MASCI recipients, critical routes non-empty (3 checks × 7 routes) | ✅ |
| 23 | Sender identity resolves from branding | ✅ |
| 24 | Sender carries no MASCI string | ✅ |
| 25 | `resolve_sender_email` compat helper returns demo addr | ✅ |
| 26 | `resolve_sender_email` no MASCI leak | ✅ |
| 27 | Audit rows carry the demo `tenant_key` | ✅ |
| 28 | Unknown route does not silently leak MASCI | ✅ |
| 29 | Safety seed empty for non-MASCI | ✅ |
| 30 | Shop seed empty for non-MASCI | ✅ |
| 31 | HR seed empty for non-MASCI | ✅ |
| 32 | Safety seed env path returns clean (non-MASCI) users | ✅ |
| 33 | PM_TABLE empty for non-MASCI | ✅ |
| 34 | ALWAYS_CC empty for non-MASCI | ✅ |
| 35 | Unresolved PM routes to ADMIN_DEAD_LETTER_TO (not MASCI office) | ✅ |
| 36 | Sender swap ignores env SENDER_EMAIL on non-MASCI | ✅ |
| 37 | Branding doc has no MASCI leak across 6 customer-visible fields | ✅ |
| 38 | Route Health — no red routes | ✅ |
| 39 | Route Health — all routes have recipients | ✅ |
| 40 | Sender refuses env fallback when no branding doc on non-MASCI | ✅ |

## Hard rules honoured
- ✅ NO real Resend send (every send is a dry-run / synthetic).
- ✅ Synthetic tenant cleaned up at end (refuses `--keep` unless flagged).
- ✅ MASCI parity (`track_15_65_parity_verify.py`) re-run: **19/19 match**.
- ✅ Env mutation (`SENDER_EMAIL`, `SAFETY_SEED_USERS`, etc.) reset
   at end of simulation.

## Customer #2 verdict
For every dimension required by the Phase 3 brief:
- Zero MASCI users — proven (seed checks 29-32).
- Zero MASCI PM routing — proven (checks 33-35).
- Zero MASCI senders — proven (checks 23-26, 36, 40).
- Zero MASCI branding — proven (check 37).
- Zero MASCI routes — proven (checks 2-22, 28).
- Audit rows tenant-scoped — proven (check 27).
- Dead-letter behaviour wired — proven (check 35).

**Customer #2 inherits ZERO MASCI from the email routing / sender /
branding subsystem.**
