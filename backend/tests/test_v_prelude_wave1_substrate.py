"""
test_v_prelude_wave1_substrate.py — Phase V-Prelude · Wave 1.

End-to-end backend regression for the Wave 1 substrate (operational
constraints · operational links · timeline · photo governance).

Covers the 10 governance probes mandated by OPERATIONAL_LINKING_RULES.md
§10 plus the constraint-foundation API surface and the timeline
aggregation contract.

We attach the admin token via a module-level `requests.Session` rather
than relying on the conftest monkey-patch — the patch only fires when
the test module imports cleanly, and this file's fixtures need it
deterministically.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

ADMIN_PASSWORD = (
    _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD")
    or os.environ.get("ADMIN_PASSWORD", "")
)

ADMIN_TOKEN = ""
if URL and ADMIN_PASSWORD:
    try:
        _r = requests.post(
            f"{URL}/api/admin/login",
            json={"password": ADMIN_PASSWORD},
            timeout=10,
        )
        if _r.status_code == 200:
            ADMIN_TOKEN = _r.json().get("token", "")
    except Exception:
        ADMIN_TOKEN = ""

pytestmark = pytest.mark.skipif(
    not (URL and ADMIN_TOKEN),
    reason="REACT_APP_BACKEND_URL or admin login not available",
)


@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"X-Admin-Token": ADMIN_TOKEN})
    return sess


@pytest.fixture(scope="module")
def project_id() -> str:
    return f"P-VPW1-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def created():
    return {"constraints": [], "links": []}


@pytest.fixture(scope="module", autouse=True)
def _cleanup(project_id):
    yield
    try:
        from pymongo import MongoClient  # noqa: PLC0415
        mongo = _read_kv(Path("/app/backend/.env"), "MONGO_URL")
        db_name = _read_kv(Path("/app/backend/.env"), "DB_NAME") or "masci_safety_preview"
        if mongo:
            cli = MongoClient(mongo)
            db = cli[db_name]
            db.operational_constraints.delete_many({"project_id": project_id})
            db.operational_links.delete_many({"project_id": project_id})
            cli.close()
    except Exception:
        pass


# ── Constraint surface ───────────────────────────────────────────────


def test_constraint_create_and_chronology(s, project_id, created):
    body = {
        "project_id": project_id,
        "title": "Utility conflict at STA 144+50",
        "discipline": "utilities",
        "kind": "utility-conflict",
        "severity": "high",
        "owner": "FPL",
        "operational_impact": "East lane closed",
        "notes": "Awaiting locate ticket.",
    }
    r = s.post(f"{URL}/api/constraints", json=body, timeout=10)
    assert r.status_code == 200, r.text
    doc = r.json()
    created["constraints"].append(doc["id"])
    assert doc["status"] == "open"
    assert doc["severity"] == "high"
    assert doc["chronology"][0]["action"] == "created"
    assert doc["created_at"].endswith("Z")
    assert "_id" not in doc


def test_constraint_invalid_enums_rejected(s, project_id):
    bad = {
        "project_id": project_id,
        "title": "x",
        "discipline": "invalid",
        "kind": "utility-conflict",
        "severity": "medium",
    }
    r = s.post(f"{URL}/api/constraints", json=bad, timeout=10)
    assert r.status_code == 422


def test_constraint_list_filters(s, project_id, created):
    r = s.get(
        f"{URL}/api/constraints",
        params={"project_id": project_id, "status": "open"},
        timeout=10,
    )
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert any(c["id"] in created["constraints"] for c in rows)


def test_constraint_resolve_appends_chronology(s, project_id, created):
    r = s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": project_id,
            "title": "QC failure density STA 140+00",
            "discipline": "QC",
            "kind": "QC-fail",
            "severity": "medium",
        },
        timeout=10,
    )
    cid = r.json()["id"]
    created["constraints"].append(cid)

    r = s.post(
        f"{URL}/api/constraints/{cid}/resolve",
        json={"resolution_note": "Re-rolled · density verified by lab."},
        timeout=10,
    )
    assert r.status_code == 200
    doc = r.json()
    assert doc["status"] == "resolved"
    assert doc["resolved_at"] is not None
    assert any(e["action"] == "resolved" for e in doc["chronology"])


def test_constraint_chronology_append(s, project_id, created):
    r = s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": project_id,
            "title": "FPL hold N. parcel",
            "discipline": "utilities",
            "kind": "owner-hold",
            "severity": "low",
        },
        timeout=10,
    )
    cid = r.json()["id"]
    created["constraints"].append(cid)
    r = s.post(
        f"{URL}/api/constraints/{cid}/chronology",
        json={"action": "owner contacted", "note": "Spoke w/ FPL coord 9:15a"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    chrono = r.json()["chronology"]
    assert any(e["action"] == "owner contacted" for e in chrono)


# ── Operational Links — §10 governance probes ────────────────────────


def test_link_audit_metadata_completeness(s, project_id, created):
    r = s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": project_id,
            "title": "Audit-field probe constraint",
            "discipline": "subcontractor",
            "kind": "owner-hold",
            "severity": "low",
        },
        timeout=10,
    )
    cid = r.json()["id"]
    created["constraints"].append(cid)

    body = {
        "source_type": "photo",
        "source_id": f"PH-{uuid.uuid4().hex[:8]}",
        "target_type": "operational_constraint",
        "target_id": cid,
        "relationship": "evidence_for",
        "project_id": project_id,
        "reason": "GPR sweep showing the unmapped duct.",
        "visibility": "internal",
    }
    r = s.post(f"{URL}/api/operational-links", json=body, timeout=10)
    assert r.status_code == 200, r.text
    link = r.json()
    created["links"].append(link["id"])
    for field in (
        "id", "source_type", "source_id", "target_type", "target_id",
        "relationship", "reason", "visibility", "project_id", "status",
        "created_at", "created_by",
    ):
        assert field in link, f"missing audit field {field}"
    assert "_id" not in link
    assert link["created_at"].endswith("Z")
    assert link["status"] == "active"


def test_link_invalid_artifact_type_rejected(s, project_id):
    body = {
        "source_type": "WHATEVER",
        "source_id": "x",
        "target_type": "operational_constraint",
        "target_id": "y",
        "relationship": "evidence_for",
        "project_id": project_id,
    }
    r = s.post(f"{URL}/api/operational-links", json=body, timeout=10)
    assert r.status_code == 422


def test_link_invalid_relationship_rejected(s, project_id):
    body = {
        "source_type": "photo",
        "source_id": "PH-1",
        "target_type": "operational_constraint",
        "target_id": "CO-1",
        "relationship": "loves",
        "project_id": project_id,
    }
    r = s.post(f"{URL}/api/operational-links", json=body, timeout=10)
    assert r.status_code == 422


def test_link_forbidden_inverse_rejected(s, project_id):
    for inv in ("blocked_by", "impacted_by", "escalated_to"):
        body = {
            "source_type": "future_schedule_activity",
            "source_id": "ACT-1",
            "target_type": "operational_constraint",
            "target_id": "CO-1",
            "relationship": inv,
            "project_id": project_id,
        }
        r = s.post(f"{URL}/api/operational-links", json=body, timeout=10)
        assert r.status_code == 422, f"expected reject for {inv}"


def test_link_self_link_rejected(s, project_id):
    body = {
        "source_type": "operational_constraint",
        "source_id": "C-1",
        "target_type": "operational_constraint",
        "target_id": "C-1",
        "relationship": "supersedes",
        "project_id": project_id,
    }
    r = s.post(f"{URL}/api/operational-links", json=body, timeout=10)
    assert r.status_code == 422


def test_link_circular_resulted_in_rejected(s, project_id, created):
    a = f"INC-A-{uuid.uuid4().hex[:6]}"
    b = f"RFI-B-{uuid.uuid4().hex[:6]}"
    body1 = {
        "source_type": "incident",
        "source_id": a,
        "target_type": "future_rfi",
        "target_id": b,
        "relationship": "resulted_in",
        "project_id": project_id,
    }
    r = s.post(f"{URL}/api/operational-links", json=body1, timeout=10)
    assert r.status_code == 200, r.text
    created["links"].append(r.json()["id"])

    body2 = {
        "source_type": "future_rfi",
        "source_id": b,
        "target_type": "incident",
        "target_id": a,
        "relationship": "resulted_in",
        "project_id": project_id,
    }
    r = s.post(f"{URL}/api/operational-links", json=body2, timeout=10)
    assert r.status_code == 409, r.text


def test_link_no_hard_delete_only_status(s, created):
    if not created["links"]:
        pytest.skip("no link created in this run")
    link_id = created["links"][0]
    r = s.delete(f"{URL}/api/operational-links/{link_id}", timeout=10)
    assert r.status_code in {404, 405}, r.status_code

    r = s.patch(
        f"{URL}/api/operational-links/{link_id}/status",
        json={"status": "archived", "reason": "test"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "archived"
    assert r.json()["status_changed_at"] is not None


def test_link_supersedes_cascades_and_terminal_blocked(s, project_id, created):
    a = f"INSP-A-{uuid.uuid4().hex[:6]}"
    b = f"INSP-B-{uuid.uuid4().hex[:6]}"
    r1 = s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "inspection",
            "source_id": a,
            "target_type": "inspection",
            "target_id": b,
            "relationship": "references",
            "project_id": project_id,
        },
        timeout=10,
    )
    assert r1.status_code == 200, r1.text
    created["links"].append(r1.json()["id"])

    r2 = s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "inspection",
            "source_id": f"INSP-C-{uuid.uuid4().hex[:6]}",
            "target_type": "inspection",
            "target_id": a,
            "relationship": "supersedes",
            "project_id": project_id,
        },
        timeout=10,
    )
    assert r2.status_code == 200, r2.text
    created["links"].append(r2.json()["id"])

    r3 = s.get(
        f"{URL}/api/operational-links/{r1.json()['id']}",
        timeout=10,
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "superseded"

    # Terminal — cannot transition out of superseded.
    r4 = s.patch(
        f"{URL}/api/operational-links/{r1.json()['id']}/status",
        json={"status": "active"},
        timeout=10,
    )
    assert r4.status_code == 409, r4.text


def test_link_create_does_not_mutate_target(s, project_id, created):
    r = s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": project_id,
            "title": "Survey conflict",
            "discipline": "survey",
            "kind": "survey",
            "severity": "medium",
        },
        timeout=10,
    )
    cid = r.json()["id"]
    created["constraints"].append(cid)

    before = s.get(f"{URL}/api/constraints/{cid}", timeout=10).json()

    r = s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "photo",
            "source_id": f"PH-{uuid.uuid4().hex[:6]}",
            "target_type": "operational_constraint",
            "target_id": cid,
            "relationship": "evidence_for",
            "project_id": project_id,
        },
        timeout=10,
    )
    assert r.status_code == 200
    created["links"].append(r.json()["id"])

    after = s.get(f"{URL}/api/constraints/{cid}", timeout=10).json()
    # Doctrine §3 — link create must NOT mutate the target.
    assert before["title"] == after["title"]
    assert before["status"] == after["status"]
    assert before["chronology"] == after["chronology"]
    assert before["severity"] == after["severity"]
    assert before["notes"] == after["notes"]


def test_link_project_scope_filter(s, project_id):
    r = s.get(
        f"{URL}/api/operational-links",
        params={"project_id": project_id},
        timeout=10,
    )
    assert r.status_code == 200
    rows = r.json()
    assert all(r["project_id"] == project_id for r in rows)


# ── Timeline ────────────────────────────────────────────────────────


def test_timeline_aggregates_and_sorts(s, project_id):
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["project_id"] == project_id
    assert body["generated_at"].endswith("Z")
    ats = [it["at"] for it in body["items"]]
    assert ats == sorted(ats, reverse=True), "timeline must sort newest first"
    assert len(body["items"]) <= 200


def test_timeline_requires_project_id(s):
    r = s.get(f"{URL}/api/timeline", timeout=10)
    assert r.status_code in {400, 422}


# ── Auth — unauthenticated reject ─────────────────────────────────────


def test_constraint_endpoint_requires_token():
    """Use urllib to bypass conftest's `requests` monkey-patch which
    auto-attaches the admin token."""
    import urllib.request
    import urllib.error
    req = urllib.request.Request(f"{URL}/api/constraints", method="GET")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("expected auth rejection")
    except urllib.error.HTTPError as e:
        assert e.code in {401, 403}, e.code


def test_operational_links_endpoint_requires_token():
    import urllib.request
    import urllib.error
    req = urllib.request.Request(
        f"{URL}/api/operational-links?project_id=x", method="GET"
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("expected auth rejection")
    except urllib.error.HTTPError as e:
        assert e.code in {401, 403}, e.code
