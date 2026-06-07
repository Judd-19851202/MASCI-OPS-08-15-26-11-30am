# Alert Engine Audit
**Mode:** READ-ONLY.
**Date:** 2026-02-07

The platform has THREE distinct alert engines. They do not duplicate; they layer.

---

## Engine 1 · Unified Task + Notification Engine
File: `backend/routes/tasks_notifications.py` · iter150.

- Collections: `db.tasks` + `db.notifications` (TTL on `closed_at`/`expires_at`).
- Surface: `NotificationBell` (bell + drawer) in every protected portal.
- Severity ladder: `Info`, `Warning`, `Critical`.
- Producers (every `notification_service.fanout` call discovered): see §6 of `NOTIFICATION_SYSTEM_FORENSIC_AUDIT.md`. 21 distinct `type` strings today.
- Consumers:
  - HTTP API: `/api/notifications`, `/api/notifications/unread-count`, `/api/notifications/{id}/read`, `/api/notifications/read-all`, `/api/notifications/{id}/acknowledge`.
  - Frontend: `NotificationBell.jsx` → `lib/tasksApi.js`.

This is the **operational** alert engine. It survives reboots, has read receipts, and is per-user.

---

## Engine 2 · Operational Intelligence Digest
File: `backend/routes/notifications.py` · separate from Engine 1.

- HTTP endpoints (read-only aggregator):
  - `GET /api/admin/notifications/digest`
  - `GET /api/safety/notifications/digest`
- Computes role-scoped findings on demand from detectors (governance, document expirations, payroll variance, daily-report gaps, etc.). **No source-of-truth collection.**
- Payload envelope:
  ```
  { ok, role, generated_at,
    summary: { critical, high, medium, low, total_open, score, score_label },
    sections: [ { key, severity, title, body, count, action_url, rule_ids, items: [...] }, ... ]
  }
  ```
- Surface: cards on Admin Hub / Safety Hub dashboards.

This is the **intelligence** layer — a curated digest of "what should I look at now?" without writing to `db.notifications`.

---

## Engine 3 · Derived alerts (per-domain views)
Per-domain on-demand computed views. Most relevant ones:

| File | Endpoint | What it returns |
|---|---|---|
| `routes/trench_safety/alerts.py` | `GET /api/trench-safety/alerts` | per-asset alerts derived from holds + certs + inspections + repairs (kinds: critical_damage, expired_certification, missing_certification, failed_inspection, hold_applied, due_soon_30, due_soon_60). |
| `routes/trench_safety/dashboard.py` | `GET /api/trench-safety/dashboard` | embedded `alerts` summary object surfaced on the Safety Trench Safety Hub. |
| `routes/document_expirations.py` | aggregates document expirations and **also** fanouts to Engine 1 with `type=document.expired`. |
| `routes/payroll_variance.py` | flag rows for review; surfaces in Engine 2 digest + Engine 1 fanout `payroll_variance.manual_run`. |
| `routes/po_requests.py` | approval visibility surfaces in Engine 1 (`po.approval_visibility`) + the PO digest cron (Engine 4 below). |
| `routes/safety_portal/corrective_actions.py` | corrective action overdue → Engine 1 + Engine 2. |

These engines **layer**: an event happens → optionally a `notification_service.fanout` (Engine 1) → optionally surfaces in the next Intelligence Digest (Engine 2) → optionally appears in the per-domain dashboard alerts view (Engine 3) → optionally triggers an email (Resend pipeline).

---

## Engine 4 · Weekly Digest Cron
Long-running asyncio tasks pinned via Mongo singleton-locks (`run_with_singleton_lock`):

| Task | File | Schedule | Recipients | Status |
|---|---|---|---|---|
| `safety_digest` | `safety_digest.py` | Mon 14:00 UTC | `SAFETY_DIGEST_TO_EMAIL` | active (preview = stub) |
| `operator_digest` | `lib/operator_digest.py` | Mon 14:00 UTC | `OPERATOR_DIGEST_RECIPIENTS` → falls back to Safety list | active |
| `po_digest` | `po_digest.py` | Mon 14:00 UTC | active PMs (scoped) + active HR users | active |
| `backup_verification` | `backup_verification.py` | weekly | `BACKUP_VERIFICATION_TO` → fallback | active |

All four senders fall through `_safety_send_email` / `_po_digest_send_email` so they inherit the `AUTO_EMAIL_REPORTS` gate.

---

## Engine 5 · System Alarms
Internal-only, NOT user-facing.

| Trigger | File | Recipient | Subject |
|---|---|---|---|
| Health failure (red card) | `health_monitor.py:109` | `BACKUP_EMAIL_TO` | `🚨 HEALTH FAIL · {n} subsystem(s)` |
| Platform outage detected | `outage_alerts.py` + `server.py:7879` | `OUTAGE_ALERT_TO` | `🚨 PLATFORM OUTAGE · {issue_key}` (15-min cooldown) |
| Backup silent | `server.py:5812` | `BACKUP_EMAIL_TO` | `[MASCI ALARM] Backup silent for {h}h — action needed` |

These do **not** write to `db.notifications` or the digest payloads — they go straight to ops email.

---

## Frontend surfaces tied to alert engines

| UI | Reads from |
|---|---|
| `NotificationBell` (every shell) | `/api/notifications`, `/api/notifications/unread-count` |
| Admin Hub cards | `/api/admin/notifications/digest` |
| Safety Hub cards | `/api/safety/notifications/digest` |
| Trench Safety Hub alerts strip | `/api/trench-safety/dashboard.alerts` |
| Document expirations panel | `/api/document-expirations` aggregator |

No frontend code talks to Engine 5 (system alarms are admin-email only).

---

## Trench Safety today
- **Has Engine 3** (`/api/trench-safety/alerts`, `/api/trench-safety/dashboard`) — derived on demand from canonical collections.
- **Does NOT touch Engine 1** — zero `notification_service.fanout` calls anywhere in `routes/trench_safety/`.
- **Does NOT touch Engine 2** — the intelligence digest aggregator has no Trench Safety section.
- **Does NOT touch Engine 4** — no Trench Safety weekly digest cron.
- **Does NOT touch Engine 5** — no health/outage hooks (correct — system-level only).
- **Does NOT touch Resend** — zero email paths.

The recommended reuse plan lives in `TRENCH_SAFETY_NOTIFICATION_PLAN.md` (read-only — no code yet).
