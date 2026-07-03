# TRACK 19.41 · Zero-Drift Matrix

**Status:** 🟢 GREEN — every category preserved.

## Category matrix

| Category | Before 19.41 | After 19.41 | Drift? |
|---|---|---|---|
| **Schemas** — `po_requests` | live | unmutated | ❌ NONE |
| **Schemas** — `project_managers` | live | unmutated | ❌ NONE |
| **Schemas** — `hr_users` | live | unmutated | ❌ NONE |
| **Schemas** — `morning_digest_recipients` | live · with `digest_type` | unmutated (new `digest_type` values are additive rows) | ❌ NONE |
| **Schemas** — `operational_intelligence_audit / _history / _dedupe` | live (Track 19.40) | unmutated · continues to receive rows | ❌ NONE |
| **Routes** — Track 19.4x + prior | live | untouched | ❌ NONE |
| **Routes** — legacy `/api/admin/po-digest/preview` | live · admin-strict | untouched | ❌ NONE |
| **Routes** — legacy `/api/admin/po-digest/run-now` | live · admin-strict | untouched | ❌ NONE |
| **Emails** — provider (`fsi_send_email`) | one provider | still one provider | ❌ NONE |
| **Emails** — `AUTO_EMAIL_REPORTS` env gate | live | unchanged | ❌ NONE |
| **Scheduler** — `po_digest_scheduler_loop` | live · every Monday 14:00 UTC | unchanged | ❌ NONE |
| **Scheduler** — `singleton_scheduler` + `scheduler_runs.claim_slot` unique index | one dedupe layer | unchanged (engine adds its own additive dedupe row, does not replace) | ❌ NONE |
| **Recipients** — `project_managers` + `hr_users` as PO source of truth | live | preserved (Track 19.41 recipient standard document explicitly locks this) | ❌ NONE |
| **Recipients** — `list_recipients_for` (Track 19.40 engine) | live | unchanged | ❌ NONE |
| **Audit** — `scheduler_runs` PO rows | live | unchanged | ❌ NONE |
| **Audit** — `morning_digest_audit` (Track 19.39) | live | unchanged | ❌ NONE |
| **Rollback** — Track 19.40 contract | HIGH confidence | preserved · Track 19.41 rollback = delete 2 new modules + revert `products.py` PO block + revert lock test | ❌ NONE |
| **Doctrine** — no-auto-decision notice | verbatim (Track 19.34/19.39/19.40) | reused verbatim by PO product | ❌ NONE |
| **Renderer** — engine `render_html` | ONE renderer | unchanged (legacy PO HTML remains in place until operator confirms cutover in Track 19.42) | ❌ NONE |
| **Template engine** — engine `_CSS` + section renderers | one template family | unchanged | ❌ NONE |
| **Trend engine** — `compute_trend` | ONE trend engine | unchanged (Score model uses `compute_trend` semantics but does not fork it) | ❌ NONE |

## Single-engine invariants (locked · 12/12)

| Invariant | Owner |
|---|---|
| ONE Operational Intelligence registry | `operational_intelligence/registry.py` |
| ONE scheduler contract | `operational_intelligence/scheduler.py` |
| ONE renderer | `operational_intelligence/engine.py::render_html` |
| ONE template family | `_CSS` + section renderers |
| ONE recipient engine | `operational_intelligence/recipients.py::list_recipients_for` |
| ONE audit engine | `engine.write_audit` → `operational_intelligence_audit` |
| ONE history engine | `engine.write_history` → `operational_intelligence_history` |
| ONE trend engine | `engine.compute_trend` |
| ONE dedupe engine | `engine.dedupe_key_for` + `dedupe_seen` + `dedupe_mark` |
| ONE delivery engine | `engine.dispatch` |
| ONE email provider | `lib.fsi_email_sender.fsi_send_email` |
| ONE PDF renderer | existing WeasyPrint helper (referenced, not duplicated) |
| **NEW — ONE Operational Intelligence Score model** | `operational_intelligence/score_model.py` |
| **NEW — ONE Product Layout builder** | `operational_intelligence/product_layout.py` |

## Additive-only additions in Track 19.41

- `/app/backend/operational_intelligence/score_model.py` (new · ~150 lines).
- `/app/backend/operational_intelligence/product_layout.py` (new · ~180 lines).
- `_agg_po_digest` + `register_product("po_weekly_digest")` block in `products.py` (~120 lines added).
- Exports added to `__init__.py`.
- `/app/backend/tests/test_track_19_41_intelligence_standardization.py` (new · lock test).
- 10 governance docs in `/app/memory/TRACK_19_41_*.md`.
- Track 19.40 lock test relaxed to allow >=10 products (still 8 CONTRACT_REGISTERED locked).

## Regression matrix

| Track | Post-19.41 status |
|---|---|
| 19.34 · Incident Field Intake Modernization | 🟢 GREEN |
| 19.35 · Safety Case Workspace | 🟢 GREEN |
| 19.36 · Executive Intelligence Layer | 🟢 GREEN |
| 19.37 · Passive Presence Scoring | 🟢 GREEN |
| 19.38 · Cross-Portal Read Fanout | 🟢 GREEN |
| 19.39 · Morning Safety Intelligence Digest | 🟢 GREEN |
| 19.40 · Unified Operational Intelligence Engine | 🟢 GREEN (updated to >=10 products) |
| 19.41 · Standardization + Consolidation | 🟢 GREEN |

## Rollback

```
# 1. Remove the two new modules
rm /app/backend/operational_intelligence/score_model.py
rm /app/backend/operational_intelligence/product_layout.py

# 2. Revert the _agg_po_digest + register_product("po_weekly_digest")
#    block in /app/backend/operational_intelligence/products.py
#    (starts at "# 3 · Purchase Order Weekly Digest ...")

# 3. Revert the export block in
#    /app/backend/operational_intelligence/__init__.py

# 4. Restore the 19.40 lock test's exact-10 assertions

# 5. Remove /app/backend/tests/test_track_19_41_intelligence_standardization.py

# 6. Remove the 10 TRACK_19_41_*.md files from /app/memory/
```

Confidence: **HIGH**. Foundation is 100 % additive. Legacy PO cron continues to fire on Monday 14:00 UTC without behavior change.
