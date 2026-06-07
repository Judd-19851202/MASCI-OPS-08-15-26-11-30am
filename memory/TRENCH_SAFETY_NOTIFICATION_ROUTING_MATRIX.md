# Phase 7.5C · Notification Routing Matrix
**Single source of truth:** `backend/routes/trench_safety/notifications.py:ROUTING_MATRIX`.

## Event → (Roles · Severity · Email · Digest)

| Routing key | Roles | Severity | Email | Digest |
|---|---|---|---|---|
| `trench_safety.hold_opened.safety` | safety, shop, dispatch, admin | Critical | ✅ | ✅ |
| `trench_safety.hold_opened.certification` | safety, admin | Warning | ✅ | ✅ |
| `trench_safety.hold_opened.inspection` | safety | Warning | ❌ | ✅ |
| `trench_safety.hold_opened.maintenance` | safety, shop | Info | ❌ | ✅ |
| `trench_safety.hold_cleared` | safety | Info | ❌ | ❌ |
| `trench_safety.inspection_failed.critical` | safety, shop | Critical | ✅ | ✅ |
| `trench_safety.inspection_failed.major` | safety, shop | Warning | ❌ | ✅ |
| `trench_safety.damage_report` | safety | Warning | ❌ | ✅ |
| `trench_safety.unsafe_condition` | safety | Warning | ❌ | ✅ |
| `trench_safety.cert_due_soon_30` | safety | Info | ❌ | ✅ |
| `trench_safety.cert_due_soon_14` | safety | Warning | ✅ | ✅ |
| `trench_safety.cert_due_soon_7` | safety, admin | Critical | ✅ | ✅ |
| `trench_safety.cert_expired` | safety, shop, admin | Critical | ✅ | ✅ |
| `trench_safety.repair_awaiting_safety` | safety | Warning | ❌ | ✅ |
| `trench_safety.asset_returned_to_service` | safety, shop, dispatch | Info | ❌ | ✅ |

## Directive coverage map

| Directive event | Matrix row(s) |
|---|---|
| Safety Hold Opened — bell + email + digest | `trench_safety.hold_opened.safety` (severity Critical, 4 roles) |
| Critical Inspection Failure — bell + email + digest | `trench_safety.inspection_failed.critical` |
| Major Inspection Failure — bell + digest | `trench_safety.inspection_failed.major` |
| Damage Report — bell + digest | `trench_safety.damage_report` |
| Unsafe Condition — bell + digest | `trench_safety.unsafe_condition` |
| Cert Expiring 30/14/7 days — bell (always) + email at 14/7 | `cert_due_soon_30`, `cert_due_soon_14`, `cert_due_soon_7` |
| Cert Expired — bell + email + auto Certification Hold | `cert_expired` + existing `recompute_certification_hold` engine |
| Repair Completed Awaiting Verification — bell | `repair_awaiting_safety` |
| Asset Returned to Service — bell + digest | `asset_returned_to_service` |

## Role-to-email resolution
`backend/routes/trench_safety/notifications.py:_resolve_email_recipients`:
| Role | Env / source |
|---|---|
| safety | `SAFETY_DIGEST_TO_EMAIL` → fallback `SUPER_ADMIN_EMAIL` |
| shop | `SHOP_MANAGER_EMAIL` |
| dispatch | `DISPATCH_EMAIL` → fallback `SUPER_ADMIN_EMAIL` |
| admin | `SUPER_ADMIN_EMAIL` |

This mirrors the existing platform pattern (other domains read the same envs).

## How to change the matrix
- Add a row to `ROUTING_MATRIX` with `roles`, `severity`, `email`, `digest`.
- No other code change required — the emitter fans out automatically.
- Tests pin the structural shape (`test_routing_matrix_keys_are_consistent`).
