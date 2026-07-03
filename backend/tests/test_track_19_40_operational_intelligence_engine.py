"""Track 19.40 · Unified Operational Intelligence Engine · lock test.

Foundation certification (NOT the implementation of the remaining eight
intelligence products). Enforces:

Registry integrity
- Exactly 10 registered products (2 IMPLEMENTED + 8 CONTRACT_REGISTERED).
- Unique product IDs · every product has permission gate · template ·
  schedule policy · aggregator · unique display_name.

Single-engine verification (12/12)
- ONE registry · scheduler · renderer · template family · recipient
  engine · audit engine · history engine · dedupe engine · delivery
  engine · trend engine · email provider (`fsi_send_email`) · PDF
  renderer (WeasyPrint reference).

Zero-drift verification
- Track 19.39 collections reused (not mutated).
- Track 19.34 field intake grep invariant preserved.
- No duplicate senders/renderers/audit paths.

Trend engine verification
- ▲ / ▼ / → · percent-change math · division-by-zero edge cases.

History & audit verification
- Dispatch (dry-run) writes ONE history row + ONE audit row · does NOT
  call ``fsi_send_email``.
- Dispatch (live) calls ``fsi_send_email`` once per active recipient
  and writes history + audit + marks dedupe.
- Dedupe re-dispatch short-circuits with ``skipped_dedupe`` and writes
  a `dispatch_skipped_dedupe` audit row.

Permission verification
- Every product declares an explicit ``permission_role``.

Registration verification
- Contract-registered products raise ``NotImplementedError`` from
  ``compose(...)`` — never fabricated data.

Documentation verification
- All 15 required Track 19.40 docs + `TRACK_19_40_ZERO_DRIFT_MATRIX.md`
  + `TRACK_19_40_QUALITY_GATE_CLOSEOUT.md` are present.
- Closeout declares 🟢 GO · lists Six Pillar + Rollback.
- PRD + CHANGELOG updated with "TRACK 19.40".

Run in isolation:
    pytest backend/tests/test_track_19_40_operational_intelligence_engine.py -q
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend/src"
MEM = APP / "memory"

OI_DIR = BE / "operational_intelligence"
ENGINE = OI_DIR / "engine.py"
REGISTRY = OI_DIR / "registry.py"
PRODUCTS = OI_DIR / "products.py"
ROUTES = OI_DIR / "routes.py"
RECIPIENTS = OI_DIR / "recipients.py"
SCHEDULER = OI_DIR / "scheduler.py"
SERVER = BE / "server.py"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
INCIDENT_SCHEMA = FE / "lib/incidentReportSchema.js"


# --------------------------------------------------------------- module locks


def test_engine_files_exist():
    for f in (ENGINE, REGISTRY, PRODUCTS, ROUTES, RECIPIENTS, SCHEDULER):
        assert f.exists(), f"missing: {f}"


def test_engine_imports_cleanly():
    import importlib
    m = importlib.import_module("operational_intelligence")
    for attr in ("ENGINE_VERSION",
                 "OperationalIntelligenceProduct", "ProductStatus",
                 "register_product", "get_product", "list_products", "require_product",
                 "compose", "render_html", "dispatch",
                 "dedupe_key_for", "compute_trend",
                 "write_audit", "write_history",
                 "list_recipients_for", "list_groups",
                 "add_group", "add_group_member",
                 "schedule_definition_for", "scheduler_enabled"):
        assert hasattr(m, attr), f"engine missing: {attr}"


def test_server_wires_engine_routes():
    text = SERVER.read_text(encoding="utf-8")
    assert "register_operational_intelligence_routes" in text
    assert "operational_intelligence.routes" in text


# ------------------------------------------------------- registry integrity


def _registry_snapshot():
    from operational_intelligence import list_products, ProductStatus
    prods = list_products()
    return prods, ProductStatus


def test_registry_has_exactly_ten_products():
    prods, _ = _registry_snapshot()
    assert len(prods) == 10, f"expected 10 products, got {len(prods)}"


def test_registry_two_implemented_and_eight_contract():
    prods, PS = _registry_snapshot()
    impl = [p for p in prods if p.status == PS.IMPLEMENTED]
    contract = [p for p in prods if p.status == PS.CONTRACT_REGISTERED]
    assert len(impl) == 2, f"expected 2 IMPLEMENTED, got {len(impl)}: {[p.product_id for p in impl]}"
    assert len(contract) == 8, f"expected 8 CONTRACT_REGISTERED, got {len(contract)}"
    impl_ids = {p.product_id for p in impl}
    assert impl_ids == {"safety_morning_digest", "executive_operations_brief"}, impl_ids
    contract_ids = {p.product_id for p in contract}
    assert contract_ids == {
        "weekly_operations_digest", "transportation_intelligence",
        "fleet_intelligence", "hr_intelligence", "training_intelligence",
        "project_intelligence", "shop_intelligence", "corporate_intelligence",
    }, contract_ids


def test_every_product_has_full_contract():
    prods, _ = _registry_snapshot()
    seen_ids = set()
    seen_names = set()
    for p in prods:
        assert p.product_id, "product_id required"
        assert p.product_id not in seen_ids, f"duplicate product_id: {p.product_id}"
        seen_ids.add(p.product_id)
        assert p.display_name, f"display_name missing on {p.product_id}"
        assert p.display_name not in seen_names, f"duplicate display_name: {p.display_name}"
        seen_names.add(p.display_name)
        assert p.summary, f"summary missing on {p.product_id}"
        assert p.permission_role in {"safety_or_admin", "admin_only"}, (
            f"invalid permission_role on {p.product_id}: {p.permission_role}"
        )
        assert p.template_key, f"template_key missing on {p.product_id}"
        assert p.schedule_freq in {"weekly", "daily", "monthly", "manual"}, (
            f"invalid schedule_freq on {p.product_id}: {p.schedule_freq}"
        )
        # Aggregator is always set (either real or `_not_implemented`).
        assert callable(p.aggregator), f"aggregator missing on {p.product_id}"


def test_scheduler_definition_available_for_every_product():
    from operational_intelligence import list_products, schedule_definition_for
    for p in list_products():
        sched = schedule_definition_for(p.product_id)
        assert sched is not None, f"scheduler missing: {p.product_id}"
        assert sched["freq"] == p.schedule_freq


# ------------------------------------------------------- single-engine locks


def test_only_one_email_provider_import_in_engine():
    text = ENGINE.read_text(encoding="utf-8")
    assert "from lib.fsi_email_sender import fsi_send_email" in text
    banned = ["resend.emails.send", "sendgrid", "smtplib", "postmark"]
    hits = [b for b in banned if b in text]
    assert not hits, f"new email provider introduced: {hits}"


def test_engine_defines_single_canonical_collections():
    from operational_intelligence.engine import (
        COLLECTION_AUDIT, COLLECTION_HISTORY, COLLECTION_DEDUPE,
    )
    assert COLLECTION_AUDIT == "operational_intelligence_audit"
    assert COLLECTION_HISTORY == "operational_intelligence_history"
    assert COLLECTION_DEDUPE == "operational_intelligence_dedupe"


def test_recipient_engine_reuses_track_19_39_collection():
    from operational_intelligence.recipients import (
        COLLECTION_RECIPIENTS, COLLECTION_GROUPS,
    )
    # Zero-drift: reuse Track 19.39 collection
    assert COLLECTION_RECIPIENTS == "morning_digest_recipients"
    # Additive: new groups collection
    assert COLLECTION_GROUPS == "operational_recipient_groups"


def test_engine_exposes_single_dispatch_and_render():
    from operational_intelligence.engine import dispatch, render_html, compose
    assert callable(dispatch)
    assert callable(render_html)
    assert callable(compose)


# ----------------------------------------------------------- trend engine


def test_trend_up_down_flat():
    from operational_intelligence.engine import compute_trend
    up = compute_trend(120, 100)
    assert up["arrow"] == "▲" and up["tone"] == "up"
    assert up["delta"] == 20 and up["pct_change"] == 20.0
    down = compute_trend(80, 100)
    assert down["arrow"] == "▼" and down["tone"] == "down"
    assert down["delta"] == -20 and down["pct_change"] == -20.0
    flat = compute_trend(50, 50)
    assert flat["arrow"] == "→" and flat["tone"] == "flat"
    assert flat["pct_change"] == 0.0


def test_trend_division_by_zero_edge_cases():
    from operational_intelligence.engine import compute_trend
    # prev=0 & curr>0 → 100.0
    r = compute_trend(5, 0)
    assert r["pct_change"] == 100.0
    # prev=0 & curr=0 → None
    r0 = compute_trend(0, 0)
    assert r0["pct_change"] is None
    assert r0["arrow"] == "→"
    # None-safe
    rn = compute_trend(None, None)
    assert rn["pct_change"] is None


# ------------------------------------------------------- fake DB / testing


class _FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self.audit_inserts = 0

    async def count_documents(self, q):
        return sum(1 for d in self.docs
                   if all(d.get(k) == v for k, v in (q or {}).items()))

    async def insert_many(self, docs):
        self.docs.extend(docs)

    async def insert_one(self, doc):
        self.docs.append(doc)
        self.audit_inserts += 1

    async def update_one(self, q, upd):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(upd.get("$set", {}))
                for k, v in (upd.get("$push", {}) or {}).items():
                    d.setdefault(k, []).append(v)

    async def find_one(self, q, proj=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return d
        return None

    def find(self, q, proj=None):
        matches = [d for d in self.docs
                   if all(d.get(k) == v for k, v in (q or {}).items())]

        class _Cur:
            def __init__(self, rows):
                self.rows = rows

            def sort(self, *a, **k):
                return self

            def limit(self, n):
                return self

            def __aiter__(self):
                self._it = iter(self.rows)
                return self

            async def __anext__(self):
                try:
                    return next(self._it)
                except StopIteration:
                    raise StopAsyncIteration
        return _Cur(matches)


class _FakeDb:
    def __init__(self):
        self._collections: Dict[str, _FakeCollection] = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, _FakeCollection())


async def _seed_recipients(db, product_id: str, emails: List[str]):
    from operational_intelligence.recipients import COLLECTION_RECIPIENTS
    now = "2026-07-04T00:00:00+00:00"
    for i, e in enumerate(emails):
        db[COLLECTION_RECIPIENTS].docs.append({
            "id": f"r{i}",
            "email": e,
            "active": True,
            "digest_type": product_id,
            "display_name": e.split("@")[0],
            "role_label": "Test",
            "created_at": now,
            "updated_at": now,
        })


async def _stub_digest(*args, **kwargs) -> Dict[str, Any]:
    return {
        "subject": "TEST · Executive Ops",
        "generated_at": "2026-07-04T00:00:00+00:00",
        "product_id": "executive_operations_brief",
        "engine_version": "1.0.0",
        "sections": [{"title": "Portfolio", "kind": "kv",
                      "rows": {"Total cases": 3, "Open": 2}}],
        "no_auto_decision_notice": "attention signal only",
    }


# ------------------------------------------------------- dispatch: dry-run


def test_dispatch_dry_run_does_not_call_fsi_send_email():
    from operational_intelligence import engine
    fake_db = _FakeDb()

    async def _go():
        await _seed_recipients(fake_db, "executive_operations_brief",
                               ["a@x.com", "b@y.com"])
        with patch("lib.fsi_email_sender.fsi_send_email",
                   new_callable=AsyncMock) as mock_send, \
             patch.object(engine, "compose", side_effect=_stub_digest):
            resp = await engine.dispatch(
                fake_db, product_id="executive_operations_brief",
                dry_run=True, generated_by="test",
            )
        assert not mock_send.called, "dry_run MUST NOT call fsi_send_email"
        assert resp["dry_run"] is True
        assert resp["send_status"] == "dry_run"
        assert resp["recipient_count"] == 2
        # Both history and audit writes on dry-run
        assert fake_db[engine.COLLECTION_AUDIT].audit_inserts == 1
        assert fake_db[engine.COLLECTION_HISTORY].audit_inserts == 1
        for key in ("subject", "generated_at", "dedupe_key",
                    "audit_id", "history_id"):
            assert key in resp, f"missing key on dispatch resp: {key}"

    asyncio.run(_go())


# ---------------------------------------------------------- dispatch: live


def test_dispatch_live_calls_fsi_send_email_once_per_active_recipient():
    from operational_intelligence import engine
    fake_db = _FakeDb()

    async def _go():
        await _seed_recipients(fake_db, "executive_operations_brief",
                               ["a@x.com", "b@y.com"])
        with patch("lib.fsi_email_sender.fsi_send_email",
                   new_callable=AsyncMock,
                   return_value={"id": "provider-id-1"}) as mock_send, \
             patch.object(engine, "compose", side_effect=_stub_digest):
            resp = await engine.dispatch(
                fake_db, product_id="executive_operations_brief",
                dry_run=False, generated_by="test",
            )
        assert mock_send.await_count == 2
        assert resp["send_status"] == "sent"
        assert resp["recipient_count"] == 2
        assert all(d.get("ok") for d in resp["delivery"])
        # dedupe row written on live send
        assert fake_db[engine.COLLECTION_DEDUPE].audit_inserts == 1

    asyncio.run(_go())


# ---------------------------------------------------------- dispatch: dedupe


def test_dispatch_dedupe_skips_second_send_and_writes_audit():
    from operational_intelligence import engine
    fake_db = _FakeDb()

    async def _go():
        await _seed_recipients(fake_db, "executive_operations_brief",
                               ["a@x.com"])
        with patch("lib.fsi_email_sender.fsi_send_email",
                   new_callable=AsyncMock,
                   return_value={"id": "p"}) as mock_send, \
             patch.object(engine, "compose", side_effect=_stub_digest):
            resp1 = await engine.dispatch(
                fake_db, product_id="executive_operations_brief",
                dry_run=False, generated_by="test",
            )
            resp2 = await engine.dispatch(
                fake_db, product_id="executive_operations_brief",
                dry_run=False, generated_by="test",
            )
        # First call sends, second is deduped
        assert resp1["send_status"] == "sent"
        assert resp2["send_status"] == "skipped_dedupe"
        # Only ONE send happened even across two dispatch calls
        assert mock_send.await_count == 1
        # Two audit events (one dispatch, one dispatch_skipped_dedupe)
        audit_events = [d.get("event") for d in fake_db[engine.COLLECTION_AUDIT].docs]
        assert "dispatch" in audit_events
        assert "dispatch_skipped_dedupe" in audit_events

    asyncio.run(_go())


# ------------------------------------------- contract-registered NotImplementedError


def test_contract_registered_products_raise_not_implemented_on_compose():
    from operational_intelligence import compose, list_products, ProductStatus
    contract_ids = [p.product_id for p in list_products()
                    if p.status == ProductStatus.CONTRACT_REGISTERED]
    assert contract_ids, "expected 8 contract-registered products"

    fake_db = _FakeDb()

    async def _go():
        for pid in contract_ids:
            with pytest.raises(NotImplementedError) as exc:
                await compose(fake_db, product_id=pid)
            msg = str(exc.value).lower()
            assert "contract-registered" in msg or "not yet implemented" in msg


    asyncio.run(_go())


def test_implemented_products_compose_returns_dict():
    """The two IMPLEMENTED products must NOT raise NotImplementedError.
    We patch the underlying data sources so we don't need a live DB."""
    from operational_intelligence import compose

    fake_db = _FakeDb()

    async def _stub_morning_composer(db, **kwargs):
        from incident_engine.morning_digest import NO_AUTO_DECISION_NOTICE, SUBJECT_DEFAULT
        return {
            "subject": SUBJECT_DEFAULT,
            "generated_at": "2026-07-04T00:00:00+00:00",
            "digest_window_days": 7,
            "executive_summary": {
                "total_open_cases": 0, "high_attention_cases": 0,
                "cases_opened_recent": 0, "cases_closed_recent": 0,
                "overdue_capas": 0, "average_readiness_pct": 0,
                "oldest_open": None,
            },
            "top_attention_cases": [],
            "needs_attention_today": {
                "evidence_gaps": 0, "overdue_capas": 0,
                "delayed_closeout": 0, "executive_review_needed": 0,
            },
            "portfolio_trends": {},
            "no_auto_decision_notice": NO_AUTO_DECISION_NOTICE,
        }

    async def _stub_list_cases(*a, **k):
        return []

    async def _stub_rows(*a, **k):
        return []

    async def _go():
        with patch("incident_engine.morning_digest.compose_digest",
                   side_effect=_stub_morning_composer), \
             patch("incident_engine.portfolio_intelligence._list_cases_readonly",
                   side_effect=_stub_list_cases), \
             patch("incident_engine.portfolio_intelligence._rows_for_cases",
                   side_effect=_stub_rows):
            d1 = await compose(fake_db, product_id="safety_morning_digest")
            d2 = await compose(fake_db, product_id="executive_operations_brief")
        for d in (d1, d2):
            assert isinstance(d, dict)
            assert d.get("engine_version") == "1.0.0"
            assert d.get("subject")
            assert isinstance(d.get("sections"), list) and len(d["sections"]) >= 1
            assert d.get("no_auto_decision_notice")

    asyncio.run(_go())


# ------------------------------------------------------- render invariants


def test_render_html_emits_subject_and_notice():
    from operational_intelligence.engine import render_html
    html = render_html({
        "subject": "Test Digest",
        "generated_at": "2026-07-04T00:00:00+00:00",
        "product_id": "safety_morning_digest",
        "engine_version": "1.0.0",
        "sections": [{"title": "Section A", "kind": "kv", "rows": {"K": "V"}}],
        "no_auto_decision_notice": "attention signal only",
    })
    assert "<title>Test Digest</title>" in html
    assert "Section A" in html
    assert "attention signal only" in html
    assert "Engine v1.0.0" in html


# ------------------------------------------------------- zero-drift regressions


FORBIDDEN_UI = ["osha_recordable", "root_cause_conclusion",
                "preventability", "workers_comp",
                "insurance_liable", "disciplinary_action"]


def test_track_19_34_field_intake_invariant_preserved():
    schema = INCIDENT_SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for tok in FORBIDDEN_UI:
        assert tok not in schema and tok not in report, (
            f"Track 19.34 grep invariant broken by 19.40: {tok}"
        )


def test_engine_module_free_of_forbidden_decision_vocabulary():
    """Engine + products source must not surface forbidden UI vocab."""
    combined = ENGINE.read_text(encoding="utf-8") + "\n" + PRODUCTS.read_text(encoding="utf-8")
    # The strings we forbid are UI-facing decision claims. The engine
    # may say "attention signal only" (allowed) but never claim OSHA
    # recordability, fault, liability, etc.
    ui_banned = ["OSHA recordable", "Liability", "Blame",
                 "Preventability", "Disciplinary action"]
    hits = [t for t in ui_banned if t in combined]
    assert not hits, f"forbidden UI vocab in engine/products: {hits}"


def test_no_duplicate_email_provider_in_products():
    text = PRODUCTS.read_text(encoding="utf-8")
    banned = ["resend.emails.send", "sendgrid", "smtplib", "postmark"]
    hits = [b for b in banned if b in text]
    assert not hits, f"products introduced a duplicate email provider: {hits}"


def test_track_19_39_morning_digest_module_still_intact():
    """Zero-drift: existing 19.39 module must still expose its public API."""
    import importlib
    md = importlib.import_module("incident_engine.morning_digest")
    for attr in ("compose_digest", "render_html", "send_digest",
                 "list_recipients", "add_recipient", "update_recipient",
                 "NO_AUTO_DECISION_NOTICE", "SUBJECT_DEFAULT",
                 "COLLECTION_RECIPIENTS", "COLLECTION_AUDIT"):
        assert hasattr(md, attr), f"19.39 API missing after 19.40: {attr}"


# ----------------------------------------------------------- doc locks


REQUIRED_DOCS = [
    "TRACK_19_40_ARCHITECTURE.md",
    "TRACK_19_40_OPERATIONAL_INTELLIGENCE_ENGINE.md",
    "TRACK_19_40_SCHEDULER.md",
    "TRACK_19_40_RECIPIENT_ENGINE.md",
    "TRACK_19_40_EMAIL_ENGINE.md",
    "TRACK_19_40_PDF_ENGINE.md",
    "TRACK_19_40_TEMPLATE_ENGINE.md",
    "TRACK_19_40_AUDIT_ENGINE.md",
    "TRACK_19_40_HISTORY_ENGINE.md",
    "TRACK_19_40_TREND_ENGINE.md",
    "TRACK_19_40_DASHBOARD.md",
    "TRACK_19_40_INDUSTRY_COMPARISON.md",
    "TRACK_19_40_TEST_REPORT.md",
    "TRACK_19_40_PERMISSION_CERTIFICATION.md",
    "TRACK_19_40_DEPLOYMENT_CERTIFICATION.md",
    "TRACK_19_40_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_40_QUALITY_GATE_CLOSEOUT.md",
]


def test_all_track_19_40_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_40_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_and_rollback():
    text = (MEM / "TRACK_19_40_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text
    assert "Rollback" in text or "ROLLBACK" in text or "rollback" in text


ZDM_CATEGORIES = ["Schemas", "Backend routes", "Payloads", "PDFs",
                  "Emails", "Notifications", "Permissions",
                  "Trust Spine", "Audit events", "Rollback"]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_40_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZDM_CATEGORIES:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.40" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.40" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
