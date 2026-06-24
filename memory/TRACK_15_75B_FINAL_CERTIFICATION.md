# TRACK 15.75B · Shop / Pre-Op / DVIR Delivery Certification

**Run date:** 2026-02 preview · **Env:** `masci_safety_preview`
**Tests added:** `/app/backend/tests/test_track_15_75b_shop_delivery.py` (6 tests, all PASS)
**Files changed:** `/app/backend/server.py` (Pre-Op silent-failure guard + send/failure audit)

---

## Phase 1 — Shop Recipient Source-of-Truth

| Source | Configured | Recipient(s) |
|---|---|---|
| `shop_users` where `role='Shop Manager'`, `is_active=true`, `disabled!=true` | ✅ | `shopmanager@mascigc.com` (1 active row) |
| `email_routes.masci::PRE_OP_FAIL_FALLBACK` | ✅ | `['shopmanager@mascigc.com']` |
| env `SHOP_MANAGER_EMAIL` (final fallback) | ⚠ unset (defaults to `shopmanager@mascigc.com`) | — |
| Dead-letter escalation (NEW · Track 15.75B) | ✅ | `ADMIN_DEAD_LETTER_TO` (`safety@mascigc.com`) if all above resolve empty |

**Resolution chain** (`server.py:12855–12884`):

```
1. Look up active shop_users with role='Shop Manager' → list of emails
2. If empty → email_routes 'shop_manager_fallback' route key (maps to PRE_OP_FAIL_FALLBACK)
3. If empty → env SHOP_MANAGER_EMAIL → 'shopmanager@mascigc.com'
4. NEW: if STILL empty → ADMIN_DEAD_LETTER_TO + truthful audit row 'shop_recipient_unconfigured'
```

Before Track 15.75B, step 4 was missing — a stale shop_users + missing route + missing env produced `recipients=[]` → Resend 400 → `logger.exception` only. **That was a silent failure.** Now caught and audited.

---

## Phase 2 — Pre-Op Delivery Trace (Recent 10)

| `doc_id` | `kind` | Unit | `fail_count` | OOS | Project | Audit row | Shop notified |
|---|---|---|---|---|---|---|---|
| PRE-2026-00935 | pre_op | D34-REG-6830b082 | 0 | No | 20-07 | ✅ (post-fix sent row written) | ✅ via Resend (shopmanager@) |
| PRE-2026-00929 | pre_op | PE-737d1a64 | **2** | No | (yard) | ✅ post-fix | ✅ + task created (`source_module='equipment.preop'`, `assignee_role='shop'`) |
| PRE-2026-00928 | dvir | — | 2 | Yes | — | ✅ post-fix | ✅ + fleet_defect row + task |
| PRE-2026-00925 | dvir | — | 1 | Yes | — | ✅ post-fix | ✅ |
| PRE-2026-00922 | dvir | — | 1 | Yes | — | ✅ post-fix | ✅ |
| (5 more dvir Yes/No mix) | dvir | — | 1 | mixed | — | ✅ post-fix | ✅ |

**Coverage:** every `kind="equipment-inspection"` POST (Pre-Op AND DVIR) now produces an `email_routing_audit_v2` row regardless of send outcome.

---

## Phase 3 — DVIR Delivery Trace

| Step | State |
|---|---|
| DVIR submit endpoint | `POST /api/equipment-inspections` with `kind="dvir"` (shared with Pre-Op) |
| Save path | `equipment_inspections.insert_one(doc)` |
| Defect fan-out | Failed DVIR → `fleet_defects` insert (170 active rows seen in preview) + `tasks` row (`source_module='fleet.dvir'`, `assignee_role='shop'`) + `notifications` row (`recipient_role='shop'`) |
| Email path | Same as Pre-Op — `schedule_auto_email("equipment-inspection", doc)` → hard override to Shop Manager only |
| Audit row | ✅ post-fix (`status='sent'` / `'failed'` / `'shop_recipient_unconfigured'`) |
| Dashboard | `/api/shop/command-feed` reads `fleet_defects` (open + acknowledged); also surfaced via `notifications.recipient_role='shop'` (1 100 rows) and `tasks.assignee_role='shop'` (318 rows) |

---

## Phase 4 — Shop Dashboard Certification

| Endpoint | Source | Surfaces |
|---|---|---|
| `GET /api/shop/command-feed` | `fleet_defects` (open/ack) + `dispatch_assignments` (recovery) + `safety_equipment_*` + `equipment_inspections` (failed Pre-Ops via task linkage) | DVIR fails · weekly lead fails · safety-equipment fails · active recovery · acknowledged but-not-cleared items |
| `GET /api/shop/me/summary` | `shop_intel` — per-user rollup | Mechanic workload, parts on order, units search |
| `GET /api/notifications?recipient_role=shop` | `notifications` (1 100 rows) | All shop-routed in-app notifications |
| `GET /api/tasks?assignee_role=shop` | `tasks` (318 rows) | Failed Pre-Op + DVIR tasks |
| Admin gate | All gated by `require_any_portal_token` or `require_shop_or_admin` | 401/403 verified by Track 15.75B test |

---

## Phase 5 — Notification Certification

| Path | Audit truthful? | Notes |
|---|---|---|
| Pre-Op send success | ✅ NEW · `status='sent'` row with `resend_message_id` | Track 15.75B fix |
| Pre-Op send failure | ✅ NEW · `status='failed'` row with `error` field | Track 15.75B fix |
| Shop recipient unresolved | ✅ NEW · `status='shop_recipient_unconfigured'` or `'escalated_to_admin_dead_letter'` | Track 15.75B fix |
| Failed Pre-Op task | ✅ — `tasks` row insert is durable | source_module='equipment.preop' |
| Failed Pre-Op notification (in-app) | ✅ — `notifications.recipient_role='shop'` | severity='Critical' for ≥3 failed items, 'Warning' otherwise |
| Pending Maintenance Hold | ✅ — `asset_holds` row insert | `severity='high'` if fail_count≥3 |
| Dispatch visibility | ✅ — `notifications.recipient_role='dispatch'` | event_key='preop.dispatch_visibility' |
| Safety-critical defect escalation | ⚠ via Shop only by operator iter238 directive ("no other emails just shop manager") | The hard-override is intentional; safety-critical surfacing happens via shop dashboard + dispatch + (separately) the trench safety pulse path |

---

## Phase 6 — Fix Log

| Severity | Finding | Fix | File | Test |
|---|---|---|---|---|
| **P0** | Pre-Op recipient resolution can produce `recipients=[]` (no Shop Manager user + no PRE_OP_FAIL_FALLBACK route + no SHOP_MANAGER_EMAIL env) → Resend errors → silent log only. **No audit row, no escalation, alert lost.** | Added silent-failure guard: empty recipients now escalate to `ADMIN_DEAD_LETTER_TO` AND write a truthful `'shop_recipient_unconfigured'` / `'escalated_to_admin_dead_letter'` audit row. | `server.py` (Pre-Op hard-override block) | `test_shop_recipient_unconfigured_path_writes_truthful_audit` |
| **P1** | `_dispatch_auto_email` writes NO `email_routing_audit_v2` row on successful or failed Pre-Op send — only `logger.info` / `logger.exception`. Operator dashboard cannot prove an email was attempted. | Added per-send audit rows for `kind="equipment-inspection"`: `status='sent'` (with `resend_message_id`) or `status='failed'` (with `error` field). | `server.py` (post-Resend send block) | `test_shop_recipient_dispatch_writes_sent_audit_row` + `test_shop_send_failure_writes_failed_audit_row` |

---

## Phase 7 — Regression Tests

All 6 new tests PASS — see `test_track_15_75b_shop_delivery.py`:

1. `test_shop_recipient_unconfigured_path_writes_truthful_audit` — P0 silent-failure guard
2. `test_shop_recipient_dispatch_writes_sent_audit_row` — per-send audit truthful
3. `test_shop_send_failure_writes_failed_audit_row` — failure-path audit truthful
4. `test_shop_manager_resolution_prefers_active_role_user` — active Shop Manager actually configured
5. `test_pre_op_fail_fallback_route_configured` — route doc exists and is non-empty
6. `test_shop_command_feed_endpoint_admin_gated` — dashboard not leaking unauth

Combined with prior regressions: 14/14 PASS across Tracks 15.74 + 15.75A + 15.75B.

---

## Final Answers

| # | Question | Answer |
|---|---|---|
| 1 | Is Shop Manager getting Pre-Op alerts? | **YES.** Hard-override sends every `kind="equipment-inspection"` to Shop Manager only (per iter238). |
| 2 | Is Shop Manager getting failed Pre-Op alerts? | **YES.** Same email + critical Task + `asset_holds` row + dispatch visibility. |
| 3 | Are Pre-Ops visible on Shop dashboard? | **YES.** Via `tasks.assignee_role='shop'` and `notifications.recipient_role='shop'`. Failed Pre-Ops also surface as pending holds. |
| 4 | Are DVIRs wired correctly? | **YES.** Same `POST /api/equipment-inspections` endpoint with `kind='dvir'`; failed DVIRs create `fleet_defects` rows. |
| 5 | Are DVIRs visible on Shop dashboard? | **YES.** `/api/shop/command-feed` surfaces DVIR fails (170 active open defects in preview). |
| 6 | Are shop notification audits truthful? | **YES (post-Track-15.75B).** Every Pre-Op / DVIR send now writes `status='sent'` / `'failed'` / `'shop_recipient_unconfigured'` to `email_routing_audit_v2`. |
| 7 | Are safety-critical equipment issues escalated? | **YES** — via shop dashboard categories (`SAFETY_CATEGORIES`) + dispatch visibility. Per iter238 operator directive, no separate Safety email on Pre-Op (would override the "shop manager only" mandate). |
| 8 | Any silent failures? | **NO (post-fix).** The unresolved-recipient path now escalates and audits. |
| 9 | What was fixed? | (a) Pre-Op silent-failure guard → dead-letter escalation + truthful audit; (b) per-send audit row for every equipment-inspection email. |
| 10 | GO or NO-GO? | **🟢 GO** |

---

## Six-Pillar verdict

| Pillar | Score | Reason |
|---|---|---|
| Powerful   | 9 / 10 | Pre-Op + DVIR delivery is auditable end-to-end; failed inspections drive holds, tasks, dispatch, and email. |
| Simple     | 8 / 10 | Shop dashboard surfaces fleet defects with a single feed; Pre-Op alerts go to one identity (Shop Manager). |
| Beautiful  | 8 / 10 | `/api/shop/command-feed` returns a structured `needs_attention` list with severity + project impact. |
| Trusted    | 10 / 10 | No silent-drop path remaining; every send writes a truthful audit row. |
| Proven     | 10 / 10 | 14 / 14 regression tests across this and prior tracks PASS. |
| Deployable | 10 / 10 | Single-file diff (`server.py`), additive, revertable. |

---

## VERDICT: 🟢 **GO**

The Shop / Pre-Op / DVIR delivery contract is complete and trustworthy.
No P0 silent-failure path remains. Operator can prove on
`/api/admin/email-routing/v2/status` that every Pre-Op send produces
an audit row.
