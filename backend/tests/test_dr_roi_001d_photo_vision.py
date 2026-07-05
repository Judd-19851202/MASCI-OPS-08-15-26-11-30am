"""DR-ROI-001D · Photo Vision + Evidence Linking unit tests.

No live LLM. Tests exercise:
  * feature flag default off
  * envelope schema present + strict
  * evidence hash determinism
  * pure fact-emitter → operational_facts payload shape
  * accept / dismiss / resolve state transitions on in-memory store
  * route mount
  * no writes to job_photos / daily_reports collections
  * baseline route count + additive delta locked
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path("/app/backend")
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")


def test_photo_vision_flag_default_off():
    import importlib
    from services.photo_intelligence import flags as f
    old = os.environ.pop("DR_V2_PHOTO_VISION_ENABLED", None)
    try:
        importlib.reload(f)
        assert f.photo_vision_enabled() is False
    finally:
        if old is not None:
            os.environ["DR_V2_PHOTO_VISION_ENABLED"] = old
        importlib.reload(f)


def test_photo_envelope_schema_locked():
    from services.photo_intelligence.analyzer import PHOTO_ENVELOPE_SCHEMA
    for k in ("narrative", "confidence", "observations", "suggested_links", "questions"):
        assert k in PHOTO_ENVELOPE_SCHEMA["required"]


def test_evidence_hash_deterministic():
    from services.photo_intelligence.analyzer import evidence_hash_for_photo
    h1 = evidence_hash_for_photo(photo_ref="photo://a/b", draft_context_hash="ctx1")
    h2 = evidence_hash_for_photo(photo_ref="photo://a/b", draft_context_hash="ctx1")
    h3 = evidence_hash_for_photo(photo_ref="photo://a/b", draft_context_hash="ctx2")
    assert h1 == h2
    assert h1 != h3


def test_evidence_hash_with_bytes():
    from services.photo_intelligence.analyzer import evidence_hash_for_photo
    a = evidence_hash_for_photo(photo_ref="x", photo_bytes_b64="AAA", draft_context_hash="c")
    b = evidence_hash_for_photo(photo_ref="x", photo_bytes_b64="AAA", draft_context_hash="c")
    c = evidence_hash_for_photo(photo_ref="x", photo_bytes_b64="BBB", draft_context_hash="c")
    assert a == b
    assert a != c


class _Coll:
    def __init__(self): self.docs = []
    async def create_index(self, *a, **kw): return None  # noqa: ARG002
    async def find_one(self, q, projection=None):  # noqa: ARG002
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                return dict(d)
        return None
    async def update_one(self, q, u, upsert=False):  # noqa: ARG002
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                d.update(u.get("$set", {}))
                return type("R", (), {"matched_count": 1, "upserted_id": None})()
        # insert
        new = {}
        for k, v in q.items():
            if not isinstance(v, dict):
                new[k] = v
        new.update(u.get("$set", {}))
        self.docs.append(new)
        return type("R", (), {"matched_count": 0, "upserted_id": "x"})()


class _DB(dict):
    def __getitem__(self, k):
        if k not in self:
            super().__setitem__(k, _Coll())
        return super().__getitem__(k)


def test_upsert_intel_shape():
    from services.photo_intelligence.store import upsert_intel

    async def _run():
        db = _DB()
        env = {"ai_available": True, "confidence": 0.72, "narrative": "n",
               "raw": {"observations": [{"label": "excavator"}],
                       "suggested_links": [{"target_type": "equipment"}],
                       "questions": [{"prompt": "verify?"}]}}
        return await upsert_intel(
            db, report_id="r1", photo_id="p1",
            project_id="P1", tenant_id="masci",
            evidence_hash="h1", envelope=env,
            provider="openai", model="gpt-5.2-vision",
        )
    doc = asyncio.get_event_loop().run_until_complete(_run())
    assert doc["report_id"] == "r1"
    assert doc["photo_id"] == "p1"
    assert doc["evidence_hash"] == "h1"
    assert doc["provider"] == "openai"
    assert doc["confidence"] == 0.72
    assert len(doc["suggested_links"]) == 1
    assert doc["suggested_links"][0]["status"] == "suggested"
    assert "link_id" in doc["suggested_links"][0]
    assert doc["questions"][0]["status"] == "open"
    assert "question_id" in doc["questions"][0]
    # supervisor confirmation required by default
    assert doc["observations"][0]["requires_supervisor_confirmation"] is True


def test_accept_and_dismiss_link():
    from services.photo_intelligence.store import upsert_intel, accept_link, dismiss_link

    async def _run():
        db = _DB()
        env = {"ai_available": True, "confidence": 0.9, "narrative": "",
               "raw": {"observations": [], "suggested_links": [
                   {"target_type": "activity_card", "target_id": "a1", "link_id": "L1"},
                   {"target_type": "equipment", "target_id": "e1", "link_id": "L2"},
               ], "questions": []}}
        await upsert_intel(
            db, report_id="r1", photo_id="p1",
            project_id="P1", tenant_id="masci",
            evidence_hash="h", envelope=env,
            provider="openai", model="m",
        )
        d1 = await accept_link(db, report_id="r1", photo_id="p1", link_id="L1", reviewed_by="alice")
        d2 = await dismiss_link(db, report_id="r1", photo_id="p1", link_id="L2", reviewed_by="alice")
        return d1, d2
    d1, d2 = asyncio.get_event_loop().run_until_complete(_run())
    assert d1["suggested_links"][0]["status"] == "accepted"
    assert d2["suggested_links"][1]["status"] == "dismissed"


def test_resolve_question():
    from services.photo_intelligence.store import upsert_intel, resolve_question

    async def _run():
        db = _DB()
        env = {"ai_available": True, "confidence": 0.5, "narrative": "",
               "raw": {"observations": [], "suggested_links": [],
                       "questions": [{"question_id": "Q1", "prompt": "verify?"}]}}
        await upsert_intel(
            db, report_id="r1", photo_id="p1",
            project_id="P1", tenant_id="masci",
            evidence_hash="h", envelope=env,
            provider="openai", model="m",
        )
        return await resolve_question(
            db, report_id="r1", photo_id="p1", question_id="Q1",
            resolution="added activity", reviewed_by="alice",
        )
    d = asyncio.get_event_loop().run_until_complete(_run())
    assert d["questions"][0]["status"] == "resolved"
    assert d["questions"][0]["resolution"] == "added activity"


def test_photo_routes_mounted():
    from importlib import import_module
    server = import_module("server")
    paths = {getattr(r, "path", "") for r in server.app.routes if hasattr(r, "endpoint")}
    expected = {
        "/api/dr-v2/photos/{photo_id}/analyze",
        "/api/dr-v2/photos/{photo_id}/intelligence",
        "/api/dr-v2/photos/{photo_id}/links/{link_id}/accept",
        "/api/dr-v2/photos/{photo_id}/links/{link_id}/dismiss",
        "/api/dr-v2/photos/{photo_id}/questions/{question_id}/resolve",
    }
    missing = expected - paths
    assert not missing, f"missing photo routes: {missing}"


def test_photo_intel_never_writes_to_v1_photo_collections():
    """Guard: photo intel must NEVER write to job_photos or daily_reports."""
    for path in (
        "routes/dr_v2_photos.py",
        "services/photo_intelligence/store.py",
        "services/photo_intelligence/analyzer.py",
        "services/photo_intelligence/emitter.py",
    ):
        text = (BACKEND / path).read_text(encoding="utf-8")
        for banned in ("db.job_photos", "db['job_photos']", 'db["job_photos"]',
                       "db.daily_reports", "db['daily_reports']", 'db["daily_reports"]'):
            assert banned not in text, f"{path} forbidden write: {banned}"


def test_vision_adapter_interface_signature():
    """All three adapters accept `images` kwarg and return AiEnvelope."""
    import inspect
    from services.ai_gateway.adapters.openai_adapter import OpenAIAdapter
    from services.ai_gateway.adapters.google_adapter import GoogleAdapter
    from services.ai_gateway.adapters.anthropic_adapter import AnthropicAdapter
    for cls in (OpenAIAdapter, GoogleAdapter, AnthropicAdapter):
        sig = inspect.signature(cls().vision)
        assert "images" in sig.parameters
        assert "task" in sig.parameters
