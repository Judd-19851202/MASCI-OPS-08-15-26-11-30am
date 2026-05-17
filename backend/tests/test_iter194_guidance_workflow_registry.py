"""iter194 — Operational Guidance · Phase C foundation
("Has Guidance" workflow registry + Coverage Dashboard extension, preview only).

Backend coverage:
  • /api/admin/guidance/workflow-coverage admin-strict, returns workflow map
  • Workflow map enumerates all registered workflows with primary article + alts
  • Gap rows surface workflows that don't yet have a primary article
  • All primary_article references resolve to existing articles
  • All alt_articles references resolve to existing articles
  • Totals + per_portal aggregates are consistent
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"


def _env(key: str) -> str:
    p = Path("/app/backend/.env")
    if not p.exists():
        return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


@pytest.fixture
def admin_token():
    pw = _env("ADMIN_PASSWORD")
    if not pw:
        pytest.skip("ADMIN_PASSWORD not configured")
    r = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture
def hr_token():
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"HR seed login unavailable (status={r.status_code})")
    return r.json()["token"]


# ─────────────────────────────────────────────────────────────────────
# Admin-only enforcement
# ─────────────────────────────────────────────────────────────────────
def test_workflow_coverage_anon_401():
    r = requests.get(f"{URL}/api/admin/guidance/workflow-coverage", timeout=10)
    assert r.status_code == 401


def test_workflow_coverage_hr_blocked(hr_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-HR-Token": hr_token},
        timeout=10,
    )
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────
# Shape + content
# ─────────────────────────────────────────────────────────────────────
def test_workflow_coverage_shape(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert "workflows" in d
    assert "totals" in d
    assert "per_portal" in d
    assert isinstance(d["workflows"], list)
    assert d["totals"]["total"] == len(d["workflows"])
    assert d["totals"]["total"] == d["totals"]["covered"] + d["totals"]["gaps"]


def test_workflow_coverage_covers_six_priority_forms(admin_token):
    """The six forms the operator named in Phase C all have entries
    in the registry with linked guidance."""
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    by_id = {w["id"]: w for w in r.json()["workflows"]}
    must_have = {
        "daily-report",
        "field-incident",        # or safety-incident
        "time-verification",
        "pre-op",
        "equipment-checkout",
        "corrective-action",
    }
    missing = must_have - set(by_id.keys())
    assert not missing, f"Phase-C priority forms missing from registry: {missing}"
    for wid in must_have:
        w = by_id[wid]
        assert w["has_guidance"], f"Phase-C form '{wid}' has no primary_article!"


def test_workflow_coverage_gaps_are_real_unguidanced_surfaces(admin_token):
    """Registered gaps should be surfaces we explicitly want admins to
    see as outstanding maintenance work."""
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    gaps = {w["id"] for w in r.json()["workflows"] if not w["has_guidance"]}
    # Operator-flagged future-content surfaces
    expected_gaps_subset = {
        "toolbox-meeting",
        "jha",
        "trench-box",
        "po-request",
        "document-expirations",
        "tasks-actions",
    }
    assert expected_gaps_subset.issubset(gaps), (
        f"Expected operator-flagged gaps to be registered as such; "
        f"missing {expected_gaps_subset - gaps}"
    )


def test_workflow_coverage_per_portal_aggregates(admin_token):
    """Per-portal totals must match the row counts."""
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    d = r.json()
    by_portal: dict[str, dict] = {}
    for w in d["workflows"]:
        b = by_portal.setdefault(w["portal"], {"total": 0, "covered": 0, "gaps": 0})
        b["total"] += 1
        if w["has_guidance"]:
            b["covered"] += 1
        else:
            b["gaps"] += 1
    for portal, agg in by_portal.items():
        assert d["per_portal"][portal] == agg, f"per_portal mismatch for {portal}"


def test_all_primary_articles_resolve(admin_token):
    """Every workflow with `has_guidance: True` must surface a primary_article
    with a valid id + title (i.e., the article exists in the registry)."""
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    for w in r.json()["workflows"]:
        if w["has_guidance"]:
            assert w["primary_article"], f"{w['id']} has_guidance but no primary_article"
            assert w["primary_article"].get("id")
            assert w["primary_article"].get("title")


def test_all_alt_articles_resolve(admin_token):
    """Every alt_article entry must resolve to an article."""
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    for w in r.json()["workflows"]:
        for alt in w.get("alt_articles") or []:
            assert alt.get("id")
            assert alt.get("title")


# ─────────────────────────────────────────────────────────────────────
# End-to-end cross-check: every linked article should actually fetch
# ─────────────────────────────────────────────────────────────────────
def test_every_primary_article_is_fetchable_as_admin(admin_token):
    r = requests.get(
        f"{URL}/api/admin/guidance/workflow-coverage",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    for w in r.json()["workflows"]:
        if not w["has_guidance"]:
            continue
        art_id = w["primary_article"]["id"]
        a = requests.get(
            f"{URL}/api/guidance/articles/{art_id}",
            headers={"X-Admin-Token": admin_token},
            timeout=10,
        )
        assert a.status_code == 200, f"primary_article {art_id} not fetchable"
