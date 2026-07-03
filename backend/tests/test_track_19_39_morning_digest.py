"""Track 19.39 · Morning Safety Intelligence Digest · lock test.

Enforces:
- Digest module + routes module exist and import cleanly.
- Aggregator (19.38) + scorer (19.37) reuse; no local signal-rule
  reimplementation.
- Existing ``fsi_send_email`` used (no new email provider).
- Additive collection names locked.
- Default recipient seed contains Jaymn + Safety.
- Env override respected.
- Dry-run does NOT call ``fsi_send_email``.
- Live send iterates and calls ``fsi_send_email``.
- Response shape.
- Audit row written per send.
- Active-only filter excludes inactive.
- add/update input validation.
- Digest object structure + verbatim notice.
- Forbidden decision vocabulary absent from digest body.
- Top cases sorted DESC.
- Track 19.34 field-vs-safety grep invariant preserved.
- 7 required docs + PRD + CHANGELOG updated.

Run in isolation:
    pytest backend/tests/test_track_19_39_morning_digest.py -q
"""
from __future__ import annotations

import os
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend/src"
MEM = APP / "memory"

DIGEST = BE / "incident_engine/morning_digest.py"
ROUTES = BE / "incident_engine/morning_digest_routes.py"
SERVER = BE / "server.py"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
INCIDENT_SCHEMA = FE / "lib/incidentReportSchema.js"

FORBIDDEN = [
    "osha_recordable", "liability", "liable",
    "discipline", "disciplinary", "fault", "blame",
    "preventability", "root_cause_conclusion",
]


# --------------------------------------------------------------- module locks


def test_modules_exist():
    assert DIGEST.exists() and ROUTES.exists()


def test_modules_import_cleanly():
    import importlib
    m = importlib.import_module("incident_engine.morning_digest")
    for attr in ("compose_digest", "render_html", "send_digest",
                 "list_recipients", "add_recipient", "update_recipient",
                 "ensure_default_recipients_seeded",
                 "NO_AUTO_DECISION_NOTICE", "SUBJECT_DEFAULT",
                 "COLLECTION_RECIPIENTS", "COLLECTION_AUDIT",
                 "MORNING_DIGEST_MODEL_VERSION"):
        assert hasattr(m, attr), f"digest module missing: {attr}"
    r = importlib.import_module("incident_engine.morning_digest_routes")
    assert hasattr(r, "register_morning_digest_routes")


# ------------------------------------------------------ reuse + provider locks


def test_digest_reuses_aggregator():
    text = DIGEST.read_text(encoding="utf-8")
    assert "from .portfolio_intelligence import" in text
    assert "_list_cases_readonly" in text and "_rows_for_cases" in text


def test_digest_does_not_reimplement_signal_rules():
    text = DIGEST.read_text(encoding="utf-8")
    banned_defs = [
        "def _signal_injury", "def _signal_utility",
        "def _signal_vehicle_equipment", "def _signal_environmental",
        "def _signal_property_damage", "def _signal_public_exposure",
        "def _signal_police_agency", "def _signal_evidence_gap",
        "def _signal_delayed_closeout", "def _signal_overdue_capa",
        "def _signal_executive_review_needed",
    ]
    hits = [t for t in banned_defs if t in text]
    assert not hits, f"digest reimplemented scorer: {hits}"


def test_digest_uses_existing_email_provider_only():
    text = DIGEST.read_text(encoding="utf-8")
    assert "from lib.fsi_email_sender import fsi_send_email" in text
    # No other sender library imported.
    banned = ["resend.emails.send", "sendgrid", "smtplib", "postmark"]
    hits = [b for b in banned if b in text]
    assert not hits, f"new email provider introduced: {hits}"


def test_server_wires_routes():
    text = SERVER.read_text(encoding="utf-8")
    assert "register_morning_digest_routes" in text
    assert "morning_digest_routes" in text


def test_additive_collection_names():
    from incident_engine.morning_digest import (
        COLLECTION_RECIPIENTS, COLLECTION_AUDIT,
    )
    assert COLLECTION_RECIPIENTS == "morning_digest_recipients"
    assert COLLECTION_AUDIT == "morning_digest_audit"


# --------------------------------------------------- default recipient shape


def test_default_recipient_seed_contains_jaymn_and_safety():
    from incident_engine.morning_digest import _default_recipients_from_env
    entries = _default_recipients_from_env()
    emails = [e["email"].lower() for e in entries]
    assert any("jaymn" in e for e in emails), f"Jaymn missing: {emails}"
    assert any("safety" in e for e in emails), f"Safety missing: {emails}"


def test_env_default_recipients_override():
    from incident_engine.morning_digest import _default_recipients_from_env
    with patch.dict(os.environ, {
        "MORNING_DIGEST_DEFAULT_RECIPIENTS": "a@x.com|A|Admin,b@y.com|B|Safety"
    }):
        entries = _default_recipients_from_env()
    assert [e["email"] for e in entries] == ["a@x.com", "b@y.com"]
    assert entries[0]["display_name"] == "A"
    assert entries[1]["role_label"] == "Safety"


# ------------------------------------------------------ send: dry-run / live


class _FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self.audit_inserts = 0

    async def count_documents(self, q):
        return sum(1 for d in self.docs if all(d.get(k) == v for k, v in q.items()))

    async def insert_many(self, docs):
        self.docs.extend(docs)

    async def insert_one(self, doc):
        self.docs.append(doc)
        self.audit_inserts += 1

    async def update_one(self, q, upd):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(upd.get("$set", {}))

    async def find_one(self, q, proj=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return d
        return None

    def find(self, q, proj=None):
        matches = [d for d in self.docs
                   if all(d.get(k) == v for k, v in (q or {}).items())]

        class _Cur:
            def __init__(self, rows): self.rows = rows
            def sort(self, *a, **k): return self
            def limit(self, n): return self
            def __aiter__(self):
                self._it = iter(self.rows)
                return self
            async def __anext__(self):
                try: return next(self._it)
                except StopIteration: raise StopAsyncIteration
        return _Cur(matches)

    async def delete_many(self, q):
        self.docs = [d for d in self.docs
                     if not all(d.get(k) == v for k, v in q.items())]

    async def delete_one(self, q):
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in q.items()):
                self.docs.pop(i)
                return


class _FakeDb:
    def __init__(self):
        self._collections: Dict[str, _FakeCollection] = {}
    def __getitem__(self, name):
        return self._collections.setdefault(name, _FakeCollection())


async def _seed_two_active(fake_db):
    from incident_engine.morning_digest import COLLECTION_RECIPIENTS
    now = "2026-07-03T00:00:00+00:00"
    fake_db[COLLECTION_RECIPIENTS].docs = [
        {"id": "r1", "email": "a@x.com", "active": True,
         "role_label": "Admin", "digest_type": "safety_morning_digest",
         "display_name": "A", "created_at": now, "updated_at": now,
         "added_by": "test", "notes": ""},
        {"id": "r2", "email": "b@y.com", "active": True,
         "role_label": "Safety", "digest_type": "safety_morning_digest",
         "display_name": "B", "created_at": now, "updated_at": now,
         "added_by": "test", "notes": ""},
        {"id": "r3", "email": "c@z.com", "active": False,
         "role_label": "Ops", "digest_type": "safety_morning_digest",
         "display_name": "C", "created_at": now, "updated_at": now,
         "added_by": "test", "notes": ""},
    ]


async def _stub_compose(*a, **k):
    return {
        "model_version": "1.0.0",
        "generated_at": "2026-07-03T00:00:00+00:00",
        "digest_window_days": 7,
        "subject": "MASCI Morning Safety Intelligence — Weekly Attention Brief",
        "executive_summary": {"total_open_cases": 0, "high_attention_cases": 0,
                              "cases_opened_recent": 0, "cases_closed_recent": 0,
                              "overdue_capas": 0, "average_readiness_pct": 0,
                              "oldest_open": None},
        "top_attention_cases": [],
        "needs_attention_today": {"evidence_gaps": 0, "overdue_capas": 0,
                                   "delayed_closeout": 0,
                                   "executive_review_needed": 0},
        "portfolio_trends": {},
        "no_auto_decision_notice":
            __import__("incident_engine.morning_digest", fromlist=["NO_AUTO_DECISION_NOTICE"]).NO_AUTO_DECISION_NOTICE,
    }


def test_dry_run_does_not_call_fsi_send_email():
    from incident_engine import morning_digest as md
    fake_db = _FakeDb()

    async def _go():
        await _seed_two_active(fake_db)
        with patch("lib.fsi_email_sender.fsi_send_email",
                   new_callable=AsyncMock) as mock_send, \
             patch.object(md, "compose_digest", side_effect=_stub_compose):
            resp = await md.send_digest(fake_db, dry_run=True, generated_by="test")
        assert not mock_send.called, "dry_run MUST NOT call fsi_send_email"
        assert resp["send_status"] == "dry_run"
        assert resp["dry_run"] is True
        assert resp["recipient_count"] == 2
        for key in ("recipients", "subject", "top_case_count", "generated_at",
                    "digest_window", "send_status", "audit_id"):
            assert key in resp, f"missing key: {key}"
        # audit row written even on dry-run
        assert fake_db[md.COLLECTION_AUDIT].audit_inserts == 1

    asyncio.run(_go())


def test_live_send_calls_fsi_send_email_once_per_active_recipient():
    from incident_engine import morning_digest as md
    fake_db = _FakeDb()

    async def _go():
        await _seed_two_active(fake_db)
        with patch("lib.fsi_email_sender.fsi_send_email",
                   new_callable=AsyncMock,
                   return_value={"id": "provider-id-123"}) as mock_send, \
             patch.object(md, "compose_digest", side_effect=_stub_compose):
            resp = await md.send_digest(fake_db, dry_run=False, generated_by="test")
        # 2 active recipients (r3 is inactive).
        assert mock_send.await_count == 2, (
            f"expected 2 calls, got {mock_send.await_count}"
        )
        assert resp["send_status"] == "sent"
        assert resp["recipient_count"] == 2
        assert all(d["ok"] for d in resp["delivery"])

    asyncio.run(_go())


def test_active_only_filter_excludes_inactive():
    from incident_engine import morning_digest as md
    fake_db = _FakeDb()

    async def _go():
        await _seed_two_active(fake_db)
        rows = await md.list_recipients(fake_db, active_only=True)
        emails = {r["email"] for r in rows}
        assert "c@z.com" not in emails, "inactive recipient leaked into send list"
        assert emails == {"a@x.com", "b@y.com"}

    asyncio.run(_go())


def test_add_recipient_rejects_invalid_email():
    from incident_engine import morning_digest as md
    fake_db = _FakeDb()

    async def _go():
        with pytest.raises(ValueError):
            await md.add_recipient(fake_db, email="not-an-email")

    asyncio.run(_go())


def test_update_recipient_allow_list():
    """Only display_name / role_label / active / notes are mutable."""
    from incident_engine import morning_digest as md
    fake_db = _FakeDb()

    async def _go():
        await _seed_two_active(fake_db)
        # Attempt to mutate a forbidden field alongside a permitted one.
        row = await md.update_recipient(
            fake_db, recipient_id="r1",
            patch={"active": False, "email": "hacked@x.com",
                   "digest_type": "hacked"},
        )
        assert row["active"] is False
        assert row["email"] == "a@x.com"  # unchanged
        assert row["digest_type"] == "safety_morning_digest"  # unchanged

    asyncio.run(_go())


# --------------------------------------------------------- doctrine locks


def test_notice_constant_matches_doctrine():
    from incident_engine.morning_digest import NO_AUTO_DECISION_NOTICE
    n = NO_AUTO_DECISION_NOTICE.lower()
    assert "attention signal only" in n
    assert "safety owns investigation" in n
    for tok in ["osha", "root cause", "liability", "fault", "discipline"]:
        assert tok in n, f"notice must name domain platform does NOT decide: {tok}"


def test_digest_body_free_of_forbidden_vocabulary():
    """Grep the digest module for hard-coded forbidden strings in the
    section-composition code paths (excluding the notice constant)."""
    text = DIGEST.read_text(encoding="utf-8")
    # Strip the NO_AUTO_DECISION_NOTICE definition and everything up to
    # its closing quote — that constant is EXPECTED to name the domains.
    m = re.search(
        r'NO_AUTO_DECISION_NOTICE\s*=\s*\((?:[^)]|\n)+\)', text
    )
    if m:
        text_wo_notice = text.replace(m.group(0), "")
    else:
        text_wo_notice = text
    # 'root_cause' is used inside the aggregator/scorer sources cited in
    # docstrings; we care about UI-facing decision strings appearing in
    # section labels or subject/rendered HTML. Restrict this grep to the
    # visible-copy tokens.
    ui_forbidden = ["Liability", "OSHA recordable", "Fault", "Blame",
                    "Discipline", "Preventability"]
    hits = [t for t in ui_forbidden if t in text_wo_notice]
    assert not hits, f"forbidden UI vocabulary in digest module: {hits}"


def test_top_cases_sorted_desc_by_attention_score():
    """Behavioural — feed the digest a mocked aggregator and verify
    top_attention_cases comes back sorted."""
    from incident_engine import morning_digest as md

    async def _go():
        fake_rows = [
            {"case_id": "a", "case_number": "A", "attention_score": 10,
             "attention_level": "low", "days_open": 3, "readiness_band": "low",
             "capa_open": 0, "job_number": "J1", "incident_type": "utility_strike",
             "state": "OPEN", "submitted_at": "2026-06-25T00:00:00+00:00",
             "_attention_full": {"signals": []}},
            {"case_id": "b", "case_number": "B", "attention_score": 90,
             "attention_level": "high", "days_open": 1, "readiness_band": "low",
             "capa_open": 1, "job_number": "J2", "incident_type": "employee_injury",
             "state": "OPEN", "submitted_at": "2026-07-01T00:00:00+00:00",
             "_attention_full": {"signals": [
                 {"signal_key": "possible_injury_presence", "score": 0.85,
                  "rationale": "medical entry"}]}},
            {"case_id": "c", "case_number": "C", "attention_score": 45,
             "attention_level": "medium", "days_open": 7, "readiness_band": "medium",
             "capa_open": 2, "job_number": "J3", "incident_type": "vehicle_accident",
             "state": "OPEN", "submitted_at": "2026-06-28T00:00:00+00:00",
             "_attention_full": {"signals": []}},
        ]

        async def _stub_list(*a, **k): return [{"id": r["case_id"]} for r in fake_rows]
        async def _stub_rows(*a, **k): return fake_rows

        # Patch in the digest module's namespace (where it was imported).
        with patch.object(md, "_list_cases_readonly", side_effect=_stub_list), \
             patch.object(md, "_rows_for_cases", side_effect=_stub_rows):
            d = await md.compose_digest(_FakeDb())
        order = [r["case_id"] for r in d["top_attention_cases"]]
        assert order == ["b", "c", "a"], f"expected b,c,a; got {order}"

    asyncio.run(_go())


# ---------------------------------------------------- doctrine regression


def test_track_19_34_field_intake_invariant_preserved():
    forbidden = ["osha_recordable", "root_cause", "preventability",
                 "workers_comp", "insurance_liable", "disciplinary_action"]
    schema = INCIDENT_SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for f in forbidden:
        assert f not in schema and f not in report, (
            f"Track 19.34 grep invariant broken by 19.39: {f}"
        )


# ------------------------------------------------------------- doc locks


REQUIRED_DOCS = [
    "TRACK_19_39_MORNING_SAFETY_DIGEST.md",
    "TRACK_19_39_RECIPIENT_MANAGEMENT.md",
    "TRACK_19_39_EMAIL_ROUTING_AND_DRY_RUN.md",
    "TRACK_19_39_NO_AUTO_DECISION_DOCTRINE.md",
    "TRACK_19_39_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_39_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_39_TEST_REPORT.md",
]


def test_all_track_19_39_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_39_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_and_rollback():
    text = (MEM / "TRACK_19_39_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text
    assert "Rollback" in text or "ROLLBACK" in text


ZDM_CATEGORIES = ["Schemas", "Backend routes", "Payloads", "PDFs",
                  "Emails", "Notifications", "Permissions",
                  "Trust Spine", "Audit events", "Rollback"]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_39_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZDM_CATEGORIES:
        assert cat in text


def test_prd_updated():
    assert "TRACK 19.39" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.39" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
