# Trench Safety Notification Plan (READ-ONLY — proposal, no code yet)
**Date:** 2026-02-07
**Stage:** Pre-implementation. Awaiting operator authorisation before any build.

This document describes **how Trench Safety should plug into the existing notification infrastructure**, using only what already exists. **Nothing here has been built.** Phase 7.5A delivered the Command Center foundation; notification wiring is a distinct sprint.

---

## 1 · Guiding rule
> Trench Safety MUST reuse the platform notification engines. It MUST NOT create a parallel notification collection, a parallel digest cron, a parallel email wrapper, or a parallel bell store.

---

## 2 · Recommended bell notifications (Engine 1 fanout)

Every row would call `lib/event_fanout.emit_notification(db, payload)` with the existing severity ladder (`Info` / `Warning` / `Critical`).

| Event | `type` | Recipient role(s) | Severity | Surface |
|---|---|---|---|---|
| Public damage report submitted | `trench_safety.damage_report` | safety | Warning | Bell + dashboard |
| Inspection recorded with `Fail` + Major/Critical | `trench_safety.inspection_failed` | safety, shop | Critical | Bell + dashboard |
| Hold opened (any kind) | `trench_safety.hold_opened` | safety | Warning (Safety/Cert) · Info (Inspection/Maintenance) | Bell |
| Hold cleared | `trench_safety.hold_cleared` | safety | Info | Bell |
| Certification ≤30 days | `trench_safety.cert_due_soon_30` | safety | Warning | Bell + dashboard |
| Certification expired | `trench_safety.cert_expired` | safety | Critical | Bell + dashboard |
| Certification uploaded | `trench_safety.cert_uploaded` | safety | Info | Bell |
| Repair completed → awaiting Safety verify | `trench_safety.awaiting_safety_verification` | safety | Warning | Bell + dashboard |
| Repair verified released | `trench_safety.repair_verified` | shop | Info | Bell |
| Asset retired | `trench_safety.asset_retired` | admin | Info | Bell |

Every type string follows the `trench_safety.<event>` convention to match the existing namespaces (`asset_transfer.*`, `inspection.*`, etc.).

---

## 3 · Recommended emails (Resend reuse)

Add a domain wrapper `_trench_send_email` modeled on `_safety_send_email` (same gating, same Resend SDK shim). Then wire these events:

| Event | Subject | Recipient | Renderer |
|---|---|---|---|
| Public damage report | `[MASCI · TRENCH] Damage Report — {asset_id}` | safety routing key | inline HTML (mirrors damage report fields) |
| Critical/Major inspection fail | `[MASCI · TRENCH] FAIL — {asset_id} · {severity}` | safety + shop | inline HTML |
| Cert ≤30d | `[MASCI · TRENCH] Cert Due Soon — {asset_id} · expires {date}` | safety | inline HTML |
| Cert expired | `[MASCI · TRENCH] Cert EXPIRED — {asset_id}` | safety | inline HTML |
| Repair awaiting safety verify | `[MASCI · TRENCH] Awaiting Verification — {asset_id}` | safety | inline HTML |
| Safety hold opened | `[MASCI · TRENCH] Safety Hold — {asset_id}` | safety + admin | inline HTML |

Subject tag: add `"trench-safety"` to `pdf_render.SUBJECT_TYPE_TAGS` mapped to `TRENCH` (so the `[MASCI · TRENCH]` prefix is centrally managed).

Optional PDF attachment: when a record has a useful PDF (e.g. inspection report, cert), reuse `render_record_pdf` with a new kind handler.

---

## 4 · Recommended weekly digest section
Add a `_safety_trench_section(db)` builder to the existing `safety_digest.py` payload (Engine 4 — Safety Digest). No new cron. Output goes inside the existing Mon 14:00 UTC email.

Section content (per directive):
- Total active trench assets
- Open holds (by kind)
- Certs expiring in the next 30 / 60 / 90 days
- Inspections completed this week
- Open repair queue depth
- Field reports received this week (resolved + open)

---

## 5 · Recommended digest aggregator section (Engine 2)
Add a `_build_safety_trench_section(db)` to `routes/notifications.py:_build_safety_digest`. Surfaces the same data as §4 but inside the on-demand `/api/safety/notifications/digest` payload — so the Safety Hub card refresh picks it up live.

---

## 6 · Recommended translations
For every new `trench_safety.*` notification, the EN→ES pair lands in `frontend/src/lib/i18n.js`. Naming pattern matches existing entries (`Asset transfer requested` → `Transferencia de activo solicitada`, etc.).

---

## 7 · Recommended audit
Every notification fanout already writes an `audit_events` row via `lib/event_fanout`. No additional audit code required.

---

## 8 · What this plan deliberately does NOT add
- ❌ No new notification collection.
- ❌ No new bell component.
- ❌ No new digest cron.
- ❌ No new Resend wrapper SDK setup (reuse the existing one).
- ❌ No new template engine.
- ❌ No new severity ladder.
- ❌ No new dashboard widget framework.

---

## 9 · Sequencing (when authorised)
1. Add `trench-safety` to `SUBJECT_TYPE_TAGS`.
2. Add `_trench_send_email` wrapper to `server.py` (mirror `_safety_send_email`).
3. Wire `notification_service.fanout` (or `lib/event_fanout.emit_notification`) at every Trench Safety write point listed in §2.
4. Wire `_trench_send_email` at every event listed in §3.
5. Extend `safety_digest.py` with the trench section (§4).
6. Extend `routes/notifications.py` Safety digest aggregator with a trench section (§5).
7. Add EN→ES translations (§6).
8. Pytest coverage: assert each `fanout` is fired on the matching write path + each email subject is built with the right TAG.

---

## 10 · Tier 5 dead-letter inheritance
`ADMIN_DEAD_LETTER_EMAIL=safety@mascigc.com` already points at the Safety team. Trench Safety emails inherit Tier 5 escalation for free once they flow through the same Resend webhook plumbing.

---

## End-state of plan
Read-only proposal. Zero code modifications performed. Authorisation required before implementation.
