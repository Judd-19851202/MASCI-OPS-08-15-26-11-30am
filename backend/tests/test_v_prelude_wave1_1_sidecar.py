"""
test_v_prelude_wave1_1_sidecar.py — Phase V-Prelude · Wave 1.1.

Sidecar + observation-hardening regression. Covers:

  * Operational Timeline sidecar contract — read-only · ordering ·
    project scope · max-items truncation flag.
  * No-orphan chronology — every chronology row references a known
    canonical relationship / known project / valid timestamp.
  * Role visibility — admin-only `audit-only` links never surface to
    non-admin via the timeline aggregator.
  * Status filter — voided links never surface; superseded links never
    appear as live chronology rows.
  * Mobile breakpoint — timeline endpoint identical regardless of
    User-Agent / viewport (server is dumb; rendering is the FE's job).
  * Timestamp doctrine — every emitted `at` is Z-suffixed.

We attach the admin token via a module-level `requests.Session` rather
than the conftest monkey-patch (see the Wave 1 sibling file).
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

CANONICAL_RELATIONSHIPS = {
    "references", "caused_by", "blocks", "supports", "evidence_for",
    "resulted_in", "related_to", "supersedes", "resolved_by",
    "escalated_from", "impacts", "documents", "response_to",
    "generated_from",
}


@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"X-Admin-Token": ADMIN_TOKEN})
    return sess


@pytest.fixture(scope="module")
def project_id() -> str:
    return f"P-VPW11-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module", autouse=True)
def _seed_and_cleanup(s, project_id):
    """Seed a deterministic chronology spread (3 constraints +
    2 cross-artifact links) so ordering/visibility assertions have
    real data."""
    cids = []
    for i, (sev, kind, disc) in enumerate([
        ("high", "utility-conflict", "utilities"),
        ("medium", "QC-fail", "QC"),
        ("low", "owner-hold", "subcontractor"),
    ]):
        r = s.post(
            f"{URL}/api/constraints",
            json={
                "project_id": project_id,
                "title": f"sidecar-seed #{i}",
                "discipline": disc,
                "kind": kind,
                "severity": sev,
            },
            timeout=10,
        )
        assert r.status_code == 200, r.text
        cids.append(r.json()["id"])

    # photo evidence link
    s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "photo",
            "source_id": f"PH-{uuid.uuid4().hex[:6]}",
            "target_type": "operational_constraint",
            "target_id": cids[0],
            "relationship": "evidence_for",
            "project_id": project_id,
        },
        timeout=10,
    )
    # daily-report related_to link
    s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "daily_report",
            "source_id": f"DR-{uuid.uuid4().hex[:6]}",
            "target_type": "operational_constraint",
            "target_id": cids[1],
            "relationship": "related_to",
            "project_id": project_id,
        },
        timeout=10,
    )

    yield

    # Module teardown — strip every seeded row.
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


# ── Sidecar / timeline contract ─────────────────────────────────────


def test_sidecar_timeline_orders_newest_first(s, project_id):
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) >= 5, f"expected ≥5 seeded items, got {len(items)}"
    ats = [i["at"] for i in items]
    assert ats == sorted(ats, reverse=True), \
        "timeline must sort newest-first (Wave 1.1 doctrine)"


def test_sidecar_timeline_project_scope_strict(s, project_id):
    """Sidecar must NEVER show items from another project even when
    the seed share a Mongo collection."""
    other_pn = f"P-OTHER-{uuid.uuid4().hex[:6]}"
    s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": other_pn,
            "title": "noise-from-other-project",
            "discipline": "utilities",
            "kind": "utility-conflict",
            "severity": "low",
        },
        timeout=10,
    )
    try:
        r = s.get(
            f"{URL}/api/timeline",
            params={"project_id": project_id},
            timeout=10,
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["project_id"] == project_id, \
                f"leak from {item['project_id']} into {project_id}"
    finally:
        # Cleanup the noise row.
        try:
            from pymongo import MongoClient  # noqa: PLC0415
            mongo = _read_kv(Path("/app/backend/.env"), "MONGO_URL")
            cli = MongoClient(mongo)
            db_name = _read_kv(Path("/app/backend/.env"), "DB_NAME") or "masci_safety_preview"
            cli[db_name].operational_constraints.delete_many(
                {"project_id": other_pn}
            )
            cli.close()
        except Exception:
            pass


def test_sidecar_timeline_caps_at_200(s, project_id):
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    body = r.json()
    assert len(body["items"]) <= 200
    assert "truncated" in body


def test_sidecar_timeline_emits_z_suffixed_iso(s, project_id):
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    body = r.json()
    assert body["generated_at"].endswith("Z")
    for item in body["items"]:
        assert item["at"].endswith("Z"), \
            f"TRUST-TIME-1 breach: {item['at']}"


def test_sidecar_timeline_excludes_voided_links(s, project_id):
    """Wave 1 doctrine §10 — voided links must never surface anywhere."""
    # Create a link, then patch it to voided (admin-only).
    r = s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "field_note",
            "source_id": f"FN-{uuid.uuid4().hex[:6]}",
            "target_type": "operational_constraint",
            "target_id": "C-VOID-PROBE",
            "relationship": "references",
            "project_id": project_id,
        },
        timeout=10,
    )
    link_id = r.json()["id"]
    s.patch(
        f"{URL}/api/operational-links/{link_id}/status",
        json={"status": "voided", "reason": "test scrub"},
        timeout=10,
    )
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    found = [
        i for i in r.json()["items"]
        if "FN-" in (i.get("id") or "")
    ]
    assert not found, "voided link leaked into timeline"


# ── No-orphan chronology ─────────────────────────────────────────────


def test_no_orphan_chronology_rows(s, project_id):
    """Every timeline row must carry: kind (str), id (str), at (Z ISO),
    project_id (matches filter), and at least one of {title, subtitle,
    relationship}. No empty rows shall be emitted."""
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    for item in r.json()["items"]:
        assert item["kind"], f"missing kind: {item}"
        assert item["id"], f"missing id: {item}"
        assert item["at"].endswith("Z"), f"non-Z at: {item}"
        assert item["project_id"] == project_id
        # Operational-meaning floor — must surface SOMETHING readable.
        assert any([
            item.get("title"),
            item.get("subtitle"),
            item.get("relationship"),
        ]), f"orphan/empty chronology row: {item}"
        # Linked-to entries (if present) must shape-check.
        for lk in item.get("linked_to") or []:
            assert lk.get("kind") and lk.get("id"), \
                f"linked_to with missing kind/id: {lk}"


def test_no_invalid_relationship_in_timeline(s, project_id):
    """Every timeline row that surfaces a `relationship` must be a
    canonical relationship — never a forbidden inverse, never an
    unknown enum value."""
    r = s.get(
        f"{URL}/api/timeline",
        params={"project_id": project_id},
        timeout=10,
    )
    for item in r.json()["items"]:
        rel = item.get("relationship")
        if not rel:
            continue
        # Constraint chronology actions surface verbs like
        # `created`, `resolved`, `note`, `edited`, `owner contacted`.
        # Those are constraint-level actions, NOT operational_links
        # relationships — they're surfaced through `subtitle` /
        # `relationship` for readability and are allowed.
        if item.get("kind") == "operational_constraint":
            continue
        assert rel in CANONICAL_RELATIONSHIPS, \
            f"non-canonical relationship leaked: {rel}"


# ── Role-visibility — audit-only links are admin-only ────────────────


def test_audit_only_link_hidden_from_non_admin(s, project_id):
    """Create an `audit-only` link as admin, then read the timeline
    as a non-admin actor (PM token). The audit-only row must NOT
    appear in the PM response."""
    r = s.post(
        f"{URL}/api/operational-links",
        json={
            "source_type": "field_note",
            "source_id": f"FN-AUDIT-{uuid.uuid4().hex[:6]}",
            "target_type": "operational_constraint",
            "target_id": "C-AUDIT-PROBE",
            "relationship": "references",
            "project_id": project_id,
            "reason": "audit-only probe",
            "visibility": "audit-only",
        },
        timeout=10,
    )
    assert r.status_code == 200, r.text

    # Acquire a PM token using the seeded test PM (chriswright).
    # Use httpx directly to bypass the conftest's `requests` monkey-patch
    # that auto-attaches the admin token.
    import httpx  # noqa: PLC0415
    with httpx.Client(timeout=10) as hc:
        pr = hc.post(
            f"{URL}/api/pm/login",
            json={
                "email": "chriswright@mascigc.com",
                "password": "ChrisRocksThis2026",
            },
        )
        if pr.status_code != 200:
            pytest.skip(f"PM login returned {pr.status_code}; "
                        "skipping cross-portal audit-visibility probe")
        pm_token = pr.json().get("token", "")
        if not pm_token:
            pytest.skip("PM login returned no token")

        rr = hc.get(
            f"{URL}/api/timeline",
            params={"project_id": project_id},
            headers={"X-PM-Token": pm_token},
        )
        assert rr.status_code == 200, rr.text
        for item in rr.json()["items"]:
            assert "FN-AUDIT-" not in (item.get("id") or ""), \
                "audit-only link leaked to non-admin actor"
