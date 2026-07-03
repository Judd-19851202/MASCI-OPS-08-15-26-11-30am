# TRACK 19.41 · Purchase Order Weekly Digest — Forensic Audit + Consolidation

**Status:** 🟢 ACTIVE · CONSOLIDATED (additive · zero drift).

## Discovery

Found in three locations:

1. **Composer**: `/app/backend/po_digest.py` (465 lines · iter246 F3 / iter437 IV-BETA.3A).
2. **Admin routes**: `/app/backend/routes/po_digest_admin.py` (86 lines · iter380 P4D).
3. **Scheduler wiring**: `/app/backend/server.py` L11935–L12001 (`po_digest_scheduler_loop` + `_start_po_digest_cron` + `build_po_digest_admin_router`).

## Where it lives · What it does

| Property | Value |
|---|---|
| Code owner | `po_digest.py::po_digest_scheduler_loop` |
| Trigger | asyncio background task started at server startup (see `_start_po_digest_cron`) |
| Cron rhythm | `_seconds_until_next_send()` — sleeps until next configured (weekday, hour) UTC slot |
| Default schedule | **Monday 14:00 UTC** (`PO_DIGEST_WEEKDAY=0`, `PO_DIGEST_HOUR_UTC=14`) |
| Env toggles | `PO_DIGEST_ENABLED` (default `true`) · `PO_DIGEST_WEEKDAY` · `PO_DIGEST_HOUR_UTC` · `PO_DIGEST_EXCLUDE_DOMAINS` · `PO_DIGEST_SEND_EMPTY_SCOPE_PMS` (default `false`) · `AUTO_EMAIL_REPORTS` (must be `true` to actually send) |
| Data source | `db.po_requests` (PO documents · statuses filtered by `PO_OPEN_STATUSES`) · scope resolved from `db.jobs_master` (PM email = `pm_email` OR `co_pm_emails` match) |
| PO statuses tracked | `Submitted`, `Pending Approval`, `Clarification Needed`, `Approved`, `Pending Receipt`, `Overdue Receipt` |
| Recipients | (a) All PMs in `db.project_managers` where `disabled ∉ {true}`. Scoped to their `pm_email` + `co_pm_emails` project set. (b) All HR users in `db.hr_users` where `disabled ∉ {true} AND is_active ≠ false`. HR sees all POs (cross-portal read). |
| Empty-scope PMs | Skipped by default (zero jobs assigned). Override with `PO_DIGEST_SEND_EMPTY_SCOPE_PMS=true`. |
| Test/preview domain guard | `_email_is_production()` filters out `.test`, `example.com/org/net`, and any domain in `PO_DIGEST_EXCLUDE_DOMAINS`. |
| Provider | `_po_digest_send_email` (server.py L11940) → `fsi_send_email` (existing Resend wrapper) |
| Subject | `"[MASCI · PO] Weekly Request PO Digest · YYYY-MM-DD"` (iter437 IV-BETA.3A) |
| Layout | Custom indigo-branded HTML (mobile-safe) with 4 metric cards (Pending Approval · Pending Receipt · Overdue Receipt · Total Open) + Status Breakdown table + Top Vendors table + CTA button |
| Dry-run | ✅ Supported via `send_po_digest_once(..., dry_run=True)` — returns same per-recipient summary, ZERO Resend quota consumed |
| Dedupe | ✅ **Two-layer defense**: (1) `singleton_scheduler` heartbeat lock (cancels orphans on hb-loss) · (2) `scheduler_runs` collection with unique compound index on `(scheduler, slot_key)` where `slot_key` = ISO timestamp of the Monday 14:00 UTC fire time. Second fire in same slot → `claim_slot()` returns `None` and skips. |
| Audit trail | `scheduler_runs` collection · rows include `pm_attempted`, `pm_sent`, `hr_attempted`, `hr_sent`, `skipped` metadata via `mark_completed(...)`. Failures recorded via `mark_failed(...)`. |
| Preview endpoint | `GET /api/admin/po-digest/preview` — admin-strict; returns per-recipient summary; dry_run=True hard-coded. |
| Manual fire endpoint | `POST /api/admin/po-digest/run-now?dry_run=<bool>` — admin-strict; live send when `dry_run=false`. |
| Recipient management | ❌ Not directly manageable via API — recipient set is derived from `project_managers` + `hr_users` collections. Add/remove flows through the admin PM/HR user panels. |
| Trend math | ❌ None — snapshot only. |
| Operational Score | ❌ None (added under Track 19.41 wrapper). |
| Product-contract tests | ✅ NEW under Track 19.41 (`test_track_19_41_intelligence_standardization.py`). Pre-existing coverage: `tests/test_iter246_po_digest.py` · `tests/test_iter380_381_extraction.py` · `tests/test_iter437_communication_unification.py` · `tests/test_iter445_scheduler_hardening.py`. |

## Active-in-production check

- `PO_DIGEST_ENABLED` defaults to `true`. Both preview and production env have not disabled it.
- Preview env is protected from live-send via `AUTO_EMAIL_REPORTS=false` (see test_credentials.md · Auto-Email Safety Switch section).
- Production env has `AUTO_EMAIL_REPORTS=true` → live-send is active on Mondays.
- Verified in `iter446_evidence/07_scheduler_runs_po.txt` — recent PO slot claims are present.

## Metrics currently included

- Total open POs.
- Count by status (6 statuses).
- Combined "Pending Approval" (Pending Approval + Clarification Needed).
- Combined "Pending Receipt" (Pending Receipt + Approved).
- Overdue Receipt count.
- Top 5 vendors with open POs.
- Scoped job count (PM only).
- Per-recipient CTA link to `/po-requests`.

## Gaps identified

| Gap | Impact | Remediation |
|---|---|---|
| No Operational Intelligence Score | Ops leaders can't triage PO health at a glance | ✅ Added in Track 19.41 wrapper (contributors: high open volume · wide PM impact) |
| No trend math (previous week comparison) | Can't tell if PO load is growing or shrinking | 🟡 History rows begin accumulating from Track 19.41 onward via engine `write_history`. Trend engages Track 19.42+. |
| No preview via the OI Engine | Two preview paths (legacy admin route + engine preview) | ✅ Engine preview added under `/api/operational-intelligence/po_weekly_digest/preview` |
| No engine-level dedupe rows | Duplicate dispatch through engine could double-send | ✅ Engine `dispatch()` writes to `operational_intelligence_dedupe` alongside legacy `scheduler_runs` |
| Recipient model tied to `project_managers` + `hr_users` (not the unified recipient registry) | Adds/removes only via user admin panels | 🟡 KEEP as-is · PM/HR roster IS the source of truth for who gets PO visibility. Additive: admins can also register direct recipients in `morning_digest_recipients` with `digest_type="po_weekly_digest"` under the Track 19.40 recipient engine. |

## Consolidation plan (Track 19.41 · executed)

Track 19.41 consolidates the PO Digest into the Unified Operational
Intelligence Engine **without disabling or altering the legacy cron.**

### What changed

1. New IMPLEMENTED product registration in
   `/app/backend/operational_intelligence/products.py`:
   ```python
   register_product(Product(
       product_id="po_weekly_digest",
       display_name="Weekly Purchase Order Digest",
       ...,
       aggregator=_agg_po_digest,   # wraps send_po_digest_once(dry_run=True)
   ))
   ```
2. New aggregator `_agg_po_digest`:
   - Calls `send_po_digest_once(db, None, portal_url="", dry_run=True)` to gather the per-recipient summary — **no live send**.
   - Reshapes results into the canonical Track 19.41 **14-section standard layout**.
   - Computes an Operational Intelligence Score with 3 contributors.
   - Preserves the legacy no-auto-decision doctrine ("attention signal only").
   - Emits deep-links to `/po-requests` + `/admin/po-digest/preview` (legacy preview).
3. Track 19.40 registry count grew from 10 → 11 products.
4. Track 19.40 lock test relaxed to `>=10 total` + `exactly 8 CONTRACT_REGISTERED` (preserves the eight contract IDs that Track 19.40 locked).

### What did NOT change (zero-drift proof)

- `po_digest.py` — untouched.
- `routes/po_digest_admin.py` — untouched.
- `server.py::_start_po_digest_cron` + `po_digest_scheduler_loop` wiring — untouched. Monday 14:00 UTC cron still fires and sends via Resend as before.
- `scheduler_runs` unique index + `claim_slot()` semantics — untouched.
- Recipient collections (`project_managers`, `hr_users`) — untouched.
- Env toggles (`PO_DIGEST_ENABLED`, `AUTO_EMAIL_REPORTS`, etc.) — untouched.
- Existing PO digest tests (iter246, iter380, iter437, iter445) — untouched · continue to pass.

### Rollback

Delete the `_agg_po_digest` block + `register_product("po_weekly_digest")` block from `products.py`. Registry drops back to 10 products. Legacy cron unaffected. Confidence: **HIGH**.

## Verdict

🟢 **Consolidated safely under Unified Operational Intelligence Engine.** Legacy Monday-morning cron continues to serve production without behavior change. New engine endpoint provides the standard product layout, Score model, and dry-run preview under one governance envelope.
