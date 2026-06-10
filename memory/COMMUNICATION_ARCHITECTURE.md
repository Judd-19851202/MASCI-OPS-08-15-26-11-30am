# COMMUNICATION ARCHITECTURE
**FORGEDOPS Dispatch Command Center V1 · 2026-02-10**
**Status:** Architecture-only · No code

> **Doctrine:** Most cross-portal updates are informational
> notifications, not tasks. Tasks only when an action is owed. SMS is
> the canonical channel to Drivers. In-app notifications + email are
> the channel between roles. There is **no in-app Driver chat in V1**.

---

## §1 · The Communication Question (literal)

Drivers must receive (and acknowledge):
1. Dispatches (assignment created → acknowledge tap)
2. Dispatch changes (revision created → re-acknowledge)
3. Updates (free-form dispatcher note)
4. Safety alerts (e.g. weather, road closure, incident nearby)
5. Shop alerts ("your DVIR was acknowledged", "your truck is back in
   service")
6. Special instructions (per assignment)
7. Road closures / Weather alerts (broadcast)

Cross-role:
- Dispatcher ↔ PM (haul activity, breakdown impact)
- Dispatcher ↔ Shop (defect cleared, OOS flip)
- Shop ↔ PM (asset impact on the project)
- Safety ↔ Operations (incident escalation)

---

## §2 · Channel Inventory (what exists today)

| Channel | Status | Module |
|---|---|---|
| **Twilio SMS to driver** | LIVE | `services/sms_provider.py` + magic-link in `dispatch_lifecycle.py:_issue_link_and_sms` |
| **Twilio status callback** | LIVE | `POST /api/dispatch/sms/twilio-status-callback` |
| **Resend email** | LIVE | `branded_portal_emails.py` + `routes/resend_webhook.py` |
| **In-app notifications bell** | LIVE | `routes/notifications.py` + `NotificationBell.jsx` |
| **Push notifications (mobile)** | NOT IMPLEMENTED | none |
| **Voice call** | NOT IMPLEMENTED | none |
| **Driver-to-Dispatcher reply** | NOT IMPLEMENTED (intentional — SMS is one-way today) | n/a |

---

## §3 · The Canonical Driver-Bound Channel: SMS

Per the audit doctrine (`MOTIVE_INTEGRATION_STRATEGY.md` + iter392
contract):
- **SMS is the canonical channel for everything urgent.**
- Magic-link in the SMS body deep-links into the driver shift surface
  (no app login required).
- The driver opens the link → sees the assignment → taps ACK → state
  records.

V1 will **extend** the existing magic-link SMS path to support:

| New SMS event | Trigger | Body template |
|---|---|---|
| `new_assignment` (exists) | `POST /api/dispatch/assignments` | "MASCI Dispatch · You have a new haul. Open: {magic_link}" |
| `assignment_revised` (exists as `_record_revision`) | `POST /api/dispatch/assignments/{id}/revise` | "MASCI Dispatch · Your haul was updated ({fields_changed}). Open: {magic_link}" |
| `assignment_cancelled` (audit only today) | `POST /api/dispatch/assignments/{id}/cancel` | "MASCI Dispatch · Your haul was cancelled ({reason})." |
| **NEW** — `broadcast_safety` | Operator action on Dispatch Command Center | "MASCI Safety · {message}" — sent to all drivers with active assignments |
| **NEW** — `broadcast_road_closure` | Operator action | "MASCI Dispatch · {road / area} closed. {detour}." |
| **NEW** — `shop_dvir_acknowledged` | Shop transitions defect from `open → acknowledged` for a defect that the driver reported | "MASCI Shop · Your DVIR defect was acknowledged ({item})." |

All SMS sends flow through `services/sms_provider.send_sms(...)` → all
results land in the assignment's `delivery_log[]` for audit.

---

## §4 · Cross-Portal Notification Spine

The existing `routes/notifications.py` digest engine produces a
role-scoped intelligence payload at:
- `GET /api/admin/notifications/digest`
- `GET /api/safety/notifications/digest`
- (PM / HR / Dispatch / FL digests are the named follow-up sprints — wired
  through the same engine; mechanical extension)

The digest is the **read-time** view. Cross-portal informational
notifications also write into the `notifications` collection, surfaced
through the `NotificationBell.jsx` component (one bell per portal hub).

### V1 additions

| Event | Audience | Channel |
|---|---|---|
| Breakdown reported | Shop + Dispatch | bell + email |
| OOS truck cleared | Dispatch + PM (on affected project) | bell |
| Asset transferred | Old PM + New PM | bell |
| Asset retired | Admin + Shop (if recent activity) | bell |
| Asset Spine duplicate detected | Admin | digest |
| Motive proposal queued > 24 h | Admin | digest |
| Incident reported | Safety + PM (on project) + Operations | bell + email |
| Driver acknowledges assignment | Dispatcher | bell (passive) |

All of these are **already plumbed** — V1 only needs to ensure the
Dispatch Command Center surfaces them as "Operator Attention" calm
strip at the top of the page.

---

## §5 · Broadcast SMS Tile (V1 — new operator surface)

**Where:** Dispatch Command Center (`DispatchCommandCenter.jsx`),
"Driver Comms" tile.

**Operator action:**
1. Click "Broadcast" → drawer opens.
2. Operator selects audience:
   - All drivers with active assignments today
   - Drivers on a specific project
   - A specific selection of drivers
3. Operator enters message (capped at 280 chars to stay under 2 SMS
   segments).
4. Operator clicks "Send."
5. SMS fans out via `services/sms_provider.send_sms` per recipient.
6. Each send writes a `delivery_log` row on a NEW lightweight collection
   `dispatch_broadcasts` for cross-day audit.

### `/api/dispatch/broadcast-sms`

Request:
```json
{
  "audience": "all_active" | "project:<num>" | "drivers:<id1,id2>",
  "message": "string ≤ 280",
  "kind": "safety_alert" | "road_closure" | "general"
}
```
Response includes per-driver `sms_result` rows.

**RBAC:** `require_dispatch_or_admin`.
**Rate-limiting:** max 5 broadcasts / 15 min per operator (soft guard).
**Audit:** `admin_audit_log` row per broadcast with the audience
fingerprint (hashed driver_ids).

---

## §6 · Driver Reply Path (DEFERRED)

V1 does **NOT** support driver SMS reply. If a driver needs to respond
they tap "Call Dispatcher" on their shift surface (the phone number
is configurable per tenant). Driver-initiated SMS conversations are a
**V2 backlog item** — they would require a number pool, inbound webhook
parsing, and a per-driver thread surface; substantial work.

---

## §7 · Email Communication

`branded_portal_emails.py` produces branded emails for:
- Password reset
- New invitation (per portal)
- Digest (Operations Center)
- Incident notification

V1 adds **no new** email templates. Operations Center digest already
covers cross-role visibility.

---

## §8 · Channel Selection Matrix

| Event | SMS | Email | In-App Bell | Operations Center |
|---|:---:|:---:|:---:|:---:|
| New assignment | ✅ | — | — | — |
| Assignment revised | ✅ | — | — | — |
| Assignment cancelled | ✅ | — | — | — |
| Safety broadcast | ✅ | — | — | — |
| Road closure broadcast | ✅ | — | — | — |
| DVIR fail (driver → Shop) | — | — | ✅ Shop | ✅ |
| OOS flip (Shop → Dispatch) | — | — | ✅ Dispatch | ✅ |
| Defect cleared (Dispatch ↔ Shop) | — | — | ✅ both | — |
| Incident reported | — | ✅ Safety | ✅ Safety + PM | ✅ |
| Asset Spine alert | — | — | ✅ Admin | ✅ |
| PO approval needed | — | ✅ Approver | ✅ Approver | ✅ |
| Doc expiration < 30 d | — | ✅ Owner | ✅ HR | ✅ |

---

## §9 · Tenant Configurability

| Tenant-configurable | V1 default |
|---|---|
| SMS provider | `SMS_PROVIDER=twilio` (only impl today) |
| Twilio sender number | `TWILIO_FROM_NUMBER` env (per tenant in V2) |
| SMS opt-in disclaimer | hardcoded English template; tenant template registry in V2 |
| Email sender | `SENDER_EMAIL` env; tenant brand in V2 |
| Broadcast rate-limit | 5/15min hardcoded; tenant override V2 |

---

## §10 · STOP Condition

V1 ships:
- One new endpoint: `POST /api/dispatch/broadcast-sms`.
- One new collection: `dispatch_broadcasts` (audit log).
- One new tile: "Driver Comms" in Dispatch Command Center.
- Wiring of three existing notification events to bell counter (already
  partially done; ensure complete).

NO driver chat. NO inbound SMS. NO voice. NO push.

---

## §11 · Pillar Scorecard

| Pillar | Why |
|---|---|
| Powerful | One-tap broadcast to all active drivers in seconds |
| Simple | One channel rule (SMS = drivers, bell = roles) |
| Beautiful | Existing `delivery_log` row visualization on assignment drawer |
| Trusted | Every send audited; rate-limited; structured per-driver outcome |
| Proven | Twilio path has been live since iter392 |
