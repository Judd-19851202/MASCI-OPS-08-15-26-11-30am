"""TRACK 22.9B · V1 Daily Report Photo Intelligence Wiring — lock envelope.

Locks the async photo intelligence pipeline:
  1. Backend module import + shape (analyzer signature respected).
  2. BackgroundTasks first-pass populates intel + closes jobs.
  3. Reconciler recovers jobs that BackgroundTasks lost (pod crash).
  4. Idempotency: same (report_id, photo_id) never analyzed twice.
  5. AI disabled → placeholder intel + status="unavailable" (never blocks).
  6. Analyzer exceptions → job marked failed, submit still succeeds.
  7. Frontend evidence bundle includes photo_observations.
  8. Photo-intel read endpoint is wired into daily_reports.py.

No live DB. No live LLM. In-memory fakes for both.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest


# Force flags so capability resolver returns enabled=True inside tests.
os.environ.setdefault("AI_GATEWAY_ENABLED", "true")
os.environ.setdefault("AI_PHOTO_VISION_ENABLED", "true")
os.environ.setdefault("TENANT_AI_ENABLED", "true")
os.environ.setdefault("TENANT_AI_PHOTO_INTELLIGENCE_ENABLED", "true")
os.environ.setdefault("AI_PROVIDER_OPENAI_ENABLED", "true")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


from services.photo_intelligence import pipeline as pi  # noqa: E402


# ── In-memory Mongo stub ─────────────────────────────────────────────

class _Cursor:
    def __init__(self, rows: List[Dict[str, Any]]):
        self._rows = rows

    def sort(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    async def to_list(self, length=None):
        return list(self._rows[: (length or len(self._rows))])


class _Coll:
    def __init__(self, name: str = "?"):
        self._name = name
        self.rows: List[Dict[str, Any]] = []

    async def create_index(self, *_a, **_kw):
        return None

    def _match(self, r: Dict[str, Any], q: Dict[str, Any]) -> bool:
        for k, v in q.items():
            if isinstance(v, dict):
                if "$in" in v and r.get(k) not in v["$in"]:
                    return False
                if "$lt" in v and not (str(r.get(k, "")) < str(v["$lt"])):
                    return False
                if "$lte" in v and not (str(r.get(k, "")) <= str(v["$lte"])):
                    return False
            elif k == "$or":
                if not any(self._match(r, sub) for sub in v):
                    return False
            elif r.get(k) != v:
                return False
        return True

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if self._match(r, q):
                return dict(r)
        return None

    def find(self, q=None, projection=None):
        q = q or {}
        return _Cursor([dict(r) for r in self.rows if self._match(r, q)])

    async def insert_one(self, doc):
        self.rows.append(dict(doc))

        class _R:
            inserted_id = "x"

        return _R()

    async def update_one(self, q, update, upsert=False):
        matched = None
        for r in self.rows:
            if self._match(r, q):
                matched = r
                break

        class _R:
            matched_count = 1 if matched else 0
            modified_count = 1 if matched else 0
            upserted_id = None

        if matched:
            if "$set" in update:
                matched.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    matched[k] = int(matched.get(k) or 0) + v
            if "$unset" in update:
                for k in update["$unset"]:
                    matched.pop(k, None)
            return _R()
        if upsert:
            new = {}
            # Extract equality keys from q
            for k, v in q.items():
                if not isinstance(v, dict) and k != "$or":
                    new[k] = v
            if "$setOnInsert" in update:
                new.update(update["$setOnInsert"])
            if "$set" in update:
                new.update(update["$set"])
            self.rows.append(new)
            r2 = _R()
            r2.upserted_id = "y"
            r2.matched_count = 0
            return r2
        return _R()

    async def update_many(self, q, update):
        n = 0
        for r in self.rows:
            if self._match(r, q):
                if "$set" in update:
                    r.update(update["$set"])
                if "$unset" in update:
                    for k in update["$unset"]:
                        r.pop(k, None)
                n += 1

        class _R:
            modified_count = n

        return _R()


class _DB:
    def __init__(self):
        self._colls: Dict[str, _Coll] = {}

    def __getitem__(self, name):
        if name not in self._colls:
            self._colls[name] = _Coll(name)
        return self._colls[name]

    def __getattr__(self, name):
        return self[name]


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def db():
    return _DB()


def _v1_doc() -> Dict[str, Any]:
    return {
        "id": "dr-v1-t22-9b-1",
        "doc_id": "DR-2026-90001",
        "report_number": "DR-2026-90001",
        "project_number": "20-07",
        "report_date": "2026-02-15",
        "prepared_by": "Chris Wright",
        "photos": ["photo://bucket/photos/2026/02/dr/a.jpg",
                   "photo://bucket/photos/2026/02/dr/b.jpg"],
        "masci_crews": [{"trade": "Concrete", "count": 6, "hours": 8.0}],
        "equipment": [{"unit": "P-104", "hours": 6.0}],
        "materials": [],
        "activities": [],
    }


# ── Analyzer stubs ───────────────────────────────────────────────────

class _StubEnvelope:
    def __init__(self, ai_available=True, obs=None, narrative="rebar visible"):
        self.ai_available = ai_available
        self.provider = "openai"
        self.model = "gpt-5.2-vision"
        self.narrative = narrative
        self.confidence = 0.85
        self.raw = {}
        self._obs = obs or [{"label": "rebar", "description": "installed",
                             "confidence": 0.85, "category": "work"}]

    def to_dict(self):
        return {
            "ai_available": self.ai_available,
            "provider": self.provider,
            "model": self.model,
            "narrative": self.narrative,
            "confidence": self.confidence,
            "observations": self._obs,
            "suggested_links": [],
            "questions": [],
            "conflicts": [],
        }


async def _fake_analyze_ok(**kwargs):
    return _StubEnvelope(ai_available=True)


async def _fake_analyze_ai_off(**kwargs):
    return _StubEnvelope(ai_available=False, obs=[], narrative="")


async def _fake_analyze_raise(**kwargs):
    raise RuntimeError("provider_boom")


async def _fake_read_photo_bytes(ref):
    return b"\xff\xd8\xff\xe0FAKEJPG"


@pytest.fixture(autouse=True)
def _patch_environment(monkeypatch):
    """Force the capability resolver + photo reader to succeed by default."""
    async def _fake_cap(*a, **kw):
        class _Cap:
            enabled = True
            reason_disabled = None
        return _Cap()

    monkeypatch.setattr(pi, "resolve_ai_capabilities", _fake_cap)
    monkeypatch.setattr(pi, "_read_photo_bytes_b64",
                        lambda ref: _fake_wrap_b64(ref))
    monkeypatch.setattr(pi, "analyze_photo", _fake_analyze_ok)
    monkeypatch.setattr(pi, "get_gateway", lambda: object())


async def _fake_wrap_b64(ref):
    return "ZmFrZS1qcGVn"  # "fake-jpeg"


# ── 1. Module + endpoint wiring ──────────────────────────────────────

def test_pipeline_module_exports():
    from services.photo_intelligence import (
        enqueue_v1_report, process_v1_report,
        reconcile_v1_once, v1_reconciler_loop,
        list_v1_report_intelligence, ensure_v1_pipeline_indexes,
        COLL_INTEL_JOBS,
    )
    assert COLL_INTEL_JOBS == "dr_v1_photo_intel_jobs"
    assert callable(enqueue_v1_report)
    assert callable(process_v1_report)
    assert callable(reconcile_v1_once)
    assert callable(v1_reconciler_loop)
    assert callable(list_v1_report_intelligence)
    assert callable(ensure_v1_pipeline_indexes)


def test_daily_reports_route_wires_photo_intel_read_endpoint():
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    assert "/daily-reports/{report_id}/photo-intelligence" in src, \
        "photo-intelligence read endpoint must be registered"
    assert "list_v1_report_intelligence" in src


def test_daily_reports_route_uses_background_tasks_for_photo_intel():
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    assert "BackgroundTasks" in src, "must depend on FastAPI BackgroundTasks"
    assert "background_tasks.add_task(process_v1_report" in src, \
        "process_v1_report must be scheduled via BackgroundTasks (async)"
    # Enqueue must fire BEFORE add_task so reconciler owns retries even if
    # the request-scope task never runs.
    idx_enqueue = src.index("enqueue_v1_report")
    idx_schedule = src.index("background_tasks.add_task(process_v1_report")
    assert idx_enqueue < idx_schedule, \
        "enqueue must precede BackgroundTasks scheduling"


def test_server_registers_reconciler_and_tenant_flag_seed():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert "_start_dr_v1_photo_intel_reconciler" in src
    assert "_seed_tenant_photo_intelligence_flag" in src
    assert "v1_reconciler_loop" in src


# ── 2. BackgroundTasks first-pass ────────────────────────────────────

@pytest.mark.asyncio
async def test_process_report_first_pass_writes_intel_and_marks_jobs(db):
    doc = _v1_doc()
    out = await pi.process_report(db, doc)
    assert out["ok"] is True
    assert out["photos"] == 2
    assert out["completed"] == 2

    intel = db["dr_v2_photo_intelligence"].rows
    assert len(intel) == 2
    assert all(r["analysis_status"] == "complete" for r in intel)

    jobs = db[pi.COLL_INTEL_JOBS].rows
    assert len(jobs) == 2
    assert all(j["status"] == "complete" for j in jobs)


@pytest.mark.asyncio
async def test_process_report_no_photos_is_noop(db):
    doc = _v1_doc()
    doc["photos"] = []
    out = await pi.process_report(db, doc)
    assert out["ok"] is True
    assert out["photos"] == 0
    assert db["dr_v2_photo_intelligence"].rows == []


# ── 3. Reconciler recovers dropped BackgroundTasks ───────────────────

@pytest.mark.asyncio
async def test_reconciler_recovers_lost_background_tasks(db):
    """Simulate the pod-crash scenario: enqueue jobs, DO NOT run
    process_report, then let the reconciler pick them up."""
    doc = _v1_doc()
    await pi.enqueue_report(db, doc)

    # Nothing analyzed yet.
    assert db["dr_v2_photo_intelligence"].rows == []
    jobs = db[pi.COLL_INTEL_JOBS].rows
    assert len(jobs) == 2
    assert all(j["status"] == "pending" for j in jobs)

    # Seed the parent report so the reconciler can look it up.
    await db["daily_reports"].insert_one(doc)

    result = await pi.reconcile_once(db)
    assert result["ok"] is True
    assert result["completed"] == 2

    intel = db["dr_v2_photo_intelligence"].rows
    assert len(intel) == 2
    assert all(r["analysis_status"] == "complete" for r in intel)


# ── 4. Idempotency ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_report_is_idempotent(db):
    doc = _v1_doc()
    await pi.process_report(db, doc)
    n_after_first = len(db["dr_v2_photo_intelligence"].rows)
    # Second call must NOT create new rows.
    await pi.process_report(db, doc)
    assert len(db["dr_v2_photo_intelligence"].rows) == n_after_first


@pytest.mark.asyncio
async def test_enqueue_never_duplicates_jobs(db):
    doc = _v1_doc()
    await pi.enqueue_report(db, doc)
    await pi.enqueue_report(db, doc)
    await pi.enqueue_report(db, doc)
    # 2 photos × 1 job each = 2 total, no duplicates.
    assert len(db[pi.COLL_INTEL_JOBS].rows) == 2


# ── 5. Graceful degradation when AI is off ───────────────────────────

@pytest.mark.asyncio
async def test_ai_disabled_writes_placeholder_intel(monkeypatch, db):
    async def _fake_cap_off(*a, **kw):
        class _Cap:
            enabled = False
            reason_disabled = "tenant_ai_disabled"
        return _Cap()

    monkeypatch.setattr(pi, "resolve_ai_capabilities", _fake_cap_off)
    doc = _v1_doc()
    out = await pi.process_report(db, doc)
    assert out["ok"] is True
    # Placeholder rows written so the read endpoint returns a stable shape.
    rows = db["dr_v2_photo_intelligence"].rows
    assert len(rows) == 2
    assert all(r["analysis_status"] == "unavailable" for r in rows)
    # Jobs closed as unavailable — reconciler must not retry them.
    jobs = db[pi.COLL_INTEL_JOBS].rows
    assert all(j["status"] == "unavailable" for j in jobs)


# ── 6. Analyzer failure never crashes the submit path ────────────────

@pytest.mark.asyncio
async def test_analyzer_exception_marks_job_failed_and_returns_ok(monkeypatch, db):
    monkeypatch.setattr(pi, "analyze_photo", _fake_analyze_raise)
    doc = _v1_doc()
    out = await pi.process_report(db, doc)
    # Even though every analyzer call raised, process_report returned OK.
    assert out["ok"] is True
    jobs = db[pi.COLL_INTEL_JOBS].rows
    assert all(j["status"] == "failed" for j in jobs)
    # And each row got a note explaining why.
    assert all("analyzer_error" in (j.get("last_note") or "") for j in jobs)


# ── 7. Read endpoint aggregation ─────────────────────────────────────

@pytest.mark.asyncio
async def test_list_report_intelligence_aggregates_observations(db):
    doc = _v1_doc()
    await pi.process_report(db, doc)
    out = await pi.list_v1_report_intelligence(db, doc["doc_id"]) \
        if False else await pi.list_report_intelligence(db, doc["doc_id"])
    assert out["report_id"] == doc["doc_id"]
    assert out["photo_count"] == 2
    assert out["analyzed"] == 2
    assert out["pending"] == 0
    # Each stubbed observation → one flat entry
    assert len(out["observations"]) >= 2
    # Grounded — must NOT lose the supervisor_confirmation guard.
    assert all(o.get("requires_supervisor_confirmation") is True
               for o in out["observations"])


# ── 8. Frontend evidence bundle wires photo observations ─────────────

def test_frontend_summary_assist_wires_photo_intel_into_evidence_bundle():
    src = Path("/app/frontend/src/components/daily-report/DailySummaryAssist.jsx") \
        .read_text(encoding="utf-8")
    assert "photo_observations" in src, \
        "evidence bundle must forward photo_observations from intel API"
    assert "/daily-reports/${" in src or "/daily-reports/" in src
    assert "photo-intelligence" in src, \
        "must fetch the /daily-reports/{id}/photo-intelligence endpoint"


# ── 9. Tenant flag seed step is registered ───────────────────────────

def test_photo_intelligence_flag_seed_targets_masci_tenant():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert "photo_intelligence_enabled" in src
    assert 'tenant_id": "masci"' in src or "tenant_id='masci'" in src
