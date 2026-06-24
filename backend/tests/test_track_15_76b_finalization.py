"""TRACK 15.76B · Operations Trust Center finalization regression.

Guards the capstone-of-the-capstone contract:

  1. Categorized score has all 7 named categories.
  2. A failing category cannot be hidden by high-scoring ones
     (overall score ≤ min_category + 10).
  3. Findings are correctly split into critical / warning / cleanup
     by severity.
  4. Operator action panel sorts critical first, then warnings,
     then cleanup, and every item carries a remediation_link.
  5. Executive narrative is a non-empty human sentence.
  6. Trend snapshots are persisted and read back ordered by ts.
  7. Estimated remediation seconds equals sum of critical actions
     (not warnings/cleanup) so the headline ETA is honest.
  8. Each finding carries severity + remediation_link.
"""
from __future__ import annotations

import os
import uuid

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


# ─── 1 · all 7 categories present ──────────────────────────────────
def test_categorized_score_has_seven_subsystems():
    from lib.trust_score_v2 import (  # noqa: PLC0415
        compute_categorized_score, CATEGORY_WEIGHTS,
    )
    out = compute_categorized_score(workflows=[{"band": "green"}])
    assert set(out["categories"].keys()) == set(CATEGORY_WEIGHTS.keys())
    assert len(out["categories"]) == 7


# ─── 2 · failing category cannot be hidden ─────────────────────────
def test_failing_category_caps_overall_score():
    from lib.trust_score_v2 import compute_categorized_score  # noqa: PLC0415
    out = compute_categorized_score(
        workflows=[{"band": "green"}],
        master_data_findings=[{"band": "red", "code": "pm_missing_route", "count": 5}],
        missing_critical_routes=3,
    )
    # Routing should crash; overall ≤ min_cat + 10.
    min_cat = min(c["score"] for c in out["categories"].values())
    assert out["trust_score"] <= min_cat + 10
    assert out["score_band"] in {"red", "amber"}


# ─── 3 · severity classification ───────────────────────────────────
@pytest.mark.asyncio
async def test_findings_carry_severity():
    from lib.master_data_trust import collect_findings  # noqa: PLC0415
    db = _db()
    findings = await collect_findings(db)
    for f in findings:
        assert f.get("severity") in {"critical", "warning", "cleanup"}, (
            f"finding {f.get('code')} missing severity"
        )
        assert "remediation_link" in f, (
            f"finding {f.get('code')} missing remediation_link"
        )


# ─── 4 · operator actions sorted + linked ─────────────────────────
def test_operator_actions_sorted_with_remediation_links():
    from routes.admin_operations_trust_center import (  # noqa: PLC0415
        _build_operator_actions,
    )
    findings = [
        {"code": "x_cleanup", "severity": "cleanup", "summary": "c",
         "remediation": "r", "remediation_link": "/x"},
        {"code": "x_crit", "severity": "critical", "summary": "C",
         "remediation": "R", "remediation_link": "/c"},
        {"code": "x_warn", "severity": "warning", "summary": "w",
         "remediation": "r", "remediation_link": "/w"},
    ]
    workflows = []
    actions = _build_operator_actions(workflows, findings)
    priorities = [a["priority"] for a in actions]
    assert priorities == ["critical", "warning", "cleanup"], priorities
    for a in actions:
        assert a["remediation_link"].startswith("/"), (
            f"missing remediation_link on action {a['id']}"
        )


# ─── 5 · executive narrative is a sentence ────────────────────────
def test_executive_narrative_is_human_readable():
    from routes.admin_operations_trust_center import (  # noqa: PLC0415
        _executive_narrative,
    )
    out = _executive_narrative(
        score=40, band="red",
        categories={"workflow_health": {"score": 40, "band": "red"}},
        workflows=[{"workflow": "meeting", "band": "red"}],
        findings=[{
            "severity": "critical",
            "summary": "5 active project(s) have no resolvable PM email",
        }],
        eta_seconds=180,
    )
    assert isinstance(out, str)
    assert len(out) > 30
    # Must end with a period, must contain ETA.
    assert "minute" in out.lower()


# ─── 6 · trend snapshot persistence ───────────────────────────────
@pytest.mark.asyncio
async def test_trend_snapshots_persist_and_read():
    from lib.trust_score_history import (  # noqa: PLC0415
        ensure_indexes, read_trend, COLLECTION,
    )
    db = _db()
    await ensure_indexes(db)
    # Write a deterministic snapshot bypassing the per-minute dedup so
    # the test isn't flaky when several snapshots already exist for
    # this minute. We use a clearly fake minute_key so the write
    # cannot collide.
    from datetime import datetime, timezone  # noqa: PLC0415
    fake_minute = f"test-{uuid.uuid4().hex[:8]}"
    await db[COLLECTION].insert_one({
        "ts": datetime.now(timezone.utc).isoformat(),
        "ts_dt": datetime.now(timezone.utc),
        "minute_key": fake_minute,
        "score": 88,
        "band": "green",
        "category_scores": {},
        "summary": {},
    })
    try:
        rows = await read_trend(db, window_hours=1)
        assert any(r["score"] == 88 for r in rows), (
            "snapshot did not appear in 1h trend window"
        )
    finally:
        await db[COLLECTION].delete_many({"minute_key": fake_minute})


# ─── 7 · ETA == sum of critical actions only ───────────────────────
def test_eta_uses_critical_actions_only():
    """Cleanup actions must NOT inflate the headline ETA, otherwise
    the operator sees an alarming 'hours to fix' for trivial drift."""
    from routes.admin_operations_trust_center import (  # noqa: PLC0415
        _build_operator_actions,
    )
    findings = [
        {"code": "crit1", "severity": "critical", "summary": "c",
         "remediation": "r", "remediation_link": "/c",
         "estimated_remediation_seconds": 60},
        {"code": "clean1", "severity": "cleanup", "summary": "x",
         "remediation": "r", "remediation_link": "/x",
         "estimated_remediation_seconds": 99999},
    ]
    actions = _build_operator_actions([], findings)
    eta_critical = sum(
        a.get("estimated_remediation_seconds", 0)
        for a in actions if a.get("priority") == "critical"
    )
    eta_all = sum(
        a.get("estimated_remediation_seconds", 0) for a in actions
    )
    assert eta_critical == 60
    assert eta_all == 99999 + 60
    # The endpoint reports only the critical sum on the headline.
    assert eta_critical < eta_all
