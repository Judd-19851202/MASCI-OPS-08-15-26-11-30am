# TRACK 19.40 · Unified Operational Intelligence Engine · Zero-Drift Matrix

**Status:** 🟢 GREEN — 18/18 zero-drift categories preserved.

This matrix proves that Track 19.40 introduces the Unified Operational
Intelligence Engine as a **strictly additive** foundation. Every prior
schema, route, payload, permission, audit path, email provider, PDF
renderer, and rollback contract remains unchanged.

## Category matrix

| # | Category | Before 19.40 | After 19.40 | Drift? |
|---|---|---|---|---|
| 1 | Schemas — incident_cases | unmutated | unmutated | ❌ NONE |
| 2 | Schemas — morning_digest_recipients | live · with `digest_type` | REUSED as canonical recipient registry across all 10 products | ❌ NONE |
| 3 | Schemas — morning_digest_audit | live | REUSED alongside new `operational_intelligence_audit` (append-only) | ❌ NONE |
| 4 | Backend routes — Track 19.34–19.39 endpoints | live | untouched · continue serving | ❌ NONE |
| 5 | Backend routes — new (additive only) | n/a | 3 additive `/api/operational-intelligence/*` routes | ✅ ADDITIVE |
| 6 | Payloads — Track 19.39 digest v1 shape | live | preserved verbatim under `digest_object.legacy_v1_shape` when Safety Morning is composed via the engine | ❌ NONE |
| 7 | PDFs — WeasyPrint helper | one renderer | still one renderer (referenced from engine · unchanged) | ❌ NONE |
| 8 | Emails — provider (`fsi_send_email`) | one provider | still one provider (engine dispatch imports the same symbol) | ❌ NONE |
| 9 | Emails — Track 19.39 dry-run default | true | preserved · engine defaults `dry_run=True` on every dispatch | ❌ NONE |
| 10 | Notifications — Notification Center | untouched | untouched | ❌ NONE |
| 11 | Permissions — Safety+Admin gate on 19.39 | live | preserved · engine reuses `require_safety_or_admin` + `require_admin` | ❌ NONE |
| 12 | Trust Spine — Track 19.34 field intake grep invariant | green | still green (forbidden vocabulary absent from engine module & products) | ❌ NONE |
| 13 | Audit events — 19.39 `morning_digest_audit` writes | live | preserved · new `operational_intelligence_audit` is additive, not a rewrite | ❌ NONE |
| 14 | Dedupe — new engine collection | n/a | `operational_intelligence_dedupe` additive · scoped by `product_id:period:recipient_hash` | ✅ ADDITIVE |
| 15 | History — new engine collection | n/a | `operational_intelligence_history` additive · immutable inserts of digest objects | ✅ ADDITIVE |
| 16 | Frontend — routes / UI | unchanged | unchanged (backend-only foundation) | ❌ NONE |
| 17 | Rollback — 19.39 rollback contract | HIGH confidence | preserved · Track 19.40 rollback = delete `/app/backend/operational_intelligence/` + revert additive `server.py` block | ❌ NONE |
| 18 | Doctrine — no-auto-decision | verbatim on 19.39 | reused verbatim by engine renderer for every product | ❌ NONE |

## Single-engine invariants (12/12 locked)

| Invariant | Owner |
|---|---|
| ONE Operational Intelligence registry | `operational_intelligence/registry.py` (`_REGISTRY` dict) |
| ONE scheduler contract | `operational_intelligence/scheduler.py` (`schedule_definition_for`) |
| ONE renderer | `operational_intelligence/engine.py::render_html` |
| ONE template family | `_CSS` + section renderers in `engine.py` |
| ONE recipient engine | `operational_intelligence/recipients.py::list_recipients_for` |
| ONE audit engine | `engine.py::write_audit` → `operational_intelligence_audit` |
| ONE history engine | `engine.py::write_history` → `operational_intelligence_history` |
| ONE trend engine | `engine.py::compute_trend` |
| ONE dedupe engine | `engine.py::dedupe_key_for` + `dedupe_seen` + `dedupe_mark` |
| ONE delivery engine | `engine.py::dispatch` |
| ONE email provider | `lib.fsi_email_sender.fsi_send_email` (only import in engine) |
| ONE PDF renderer | existing WeasyPrint helper (referenced, not duplicated) |

## Duplicate-pipeline guard

There is exactly ONE composer per product (aggregator callable on the
registry). No shadow senders. No parallel schedulers. No product may
reintroduce its own renderer/sender/audit path — enforced by pytest
lock (`test_track_19_40_operational_intelligence_engine.py`).

## Regression matrix

| Track | Lock test | Post-19.40 status |
|---|---|---|
| 19.34 | test_track_19_34_incident_field_intake_modernization.py | 🟢 GREEN |
| 19.35 | test_track_19_35_safety_case_workspace.py | 🟢 GREEN |
| 19.36 | test_track_19_36_executive_intelligence.py | 🟢 GREEN |
| 19.37 | test_track_19_37_presence_scoring.py | 🟢 GREEN |
| 19.38 | test_track_19_38_portfolio_intelligence.py | 🟢 GREEN |
| 19.39 | test_track_19_39_morning_digest.py | 🟢 GREEN |
| 19.40 | test_track_19_40_operational_intelligence_engine.py | 🟢 GREEN (see closeout) |

## Rollback

```
rm -rf /app/backend/operational_intelligence/
# revert the additive block in /app/backend/server.py (the
# `_register_oi_routes(...)` import + call — ~14 lines)
```

Confidence: **HIGH**. Foundation is 100% additive. Track 19.39 email
digest continues to work through its own routes even if the engine is
removed.
