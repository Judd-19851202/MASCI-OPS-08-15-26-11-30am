# TRACK 15.66 — Email Audit Drawer (Phase 2)

**Date:** 2026-06-22

## 1. Purpose
Solves *"I never got the email"* in 15 seconds. Admin opens the per-route audit drawer and immediately sees:

* When did the resolver fire for this route?
* What source did it resolve from (db / env / legacy / disabled / error)?
* How many recipients (`to / cc / bcc` counts)?
* Did Resend accept it (resend_message_id)?
* Was it a dry-run or a real send?
* Which calling module triggered it?

## 2. UI

Component: `AuditDrawer` inside `EmailRoutingV2Panel.jsx`.

* Opens from the "Audit" button on any V2 route row (`data-testid="v2-audit-{ROUTE_KEY}"`).
* Fetches `GET /api/admin/email-routing/v2/audit?route_key={KEY}&limit=100`.
* Renders a sticky-header table with columns: **When · Source · Status · To/CC/BCC · Module · Resend ID**.
* Status colour-coded — `failed / error` = rose, `dry_run` = sky, others = emerald.
* Empty state: *"No audit rows for this route yet. Run a dry-run test to create one."*
* Close button + click-on-backdrop both dismiss the drawer.

## 3. Backend

* `GET /api/admin/email-routing/v2/audit?route_key=&limit=` — admin-only, returns the last `limit` rows for the active tenant (and optional route filter), sorted DESC by `ts`.
* Backed by index `(tenant_key, ts desc)` already created by the Track 15.65 seed script.

## 4. Data hygiene
* Audit rows are append-only — never edited, never deleted.
* No body content stored — only counts, subject (truncated to 240 chars), and Resend ID.
* No recipient email addresses stored — counts only. This bounds the privacy footprint.

## 5. Operator scenarios

**"PM said they didn't get the safety form email"**
1. Open the Safety Forms route → Audit.
2. Most recent row dated 10 min ago, `source=db`, status=`resolved`, to=2 / cc=0.
3. Resend message ID present → email left the platform; the issue is in the PM's mailbox / spam filter, not the platform.

**"The health alert never fired"**
1. Open HEALTH_ALERTS → Audit.
2. No row in the last 24 hours → resolver was never called; the underlying monitor didn't trip.
3. Operator runs a dry-run from the same panel; the row appears with `status=dry_run` — proves the route's plumbing is intact end-to-end.

## 6. Hard-rule compliance (Phase 2 audit drawer)
* ✅ Every routing decision is auditable.
* ✅ No hidden recipients (counts and source displayed).
* ✅ No mystery sends (every send writes a row).
* ✅ Privacy preserved (no body, no recipient strings).
