"""MOTIVE-DATA-003 · Operational Impact Command Card · regression suite.

Read-only verification:
 · Endpoint mounted at /api/admin/asset-mapping/operational-impact
 · Required JSON shape (current / potential / actions / readiness)
 · Readiness rules consistent with directive
 · No collection writes on repeated GETs
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8001")
API = f"{BACKEND}/api"
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


def _req(method, path, *, body=None, token=""):
    h = {"Content-Type": "application/json"}
    if token:
        h["X-Admin-Token"] = token
    d = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=d, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"status": r.status,
                    "json": json.loads(r.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}
        except Exception:
            return {"status": e.code, "json": {}}


@pytest.fixture(scope="module")
def tok():
    return _req("POST", "/admin/login", body={"password": ADMIN_PW})["json"]["token"]


def test_endpoint_requires_admin_token():
    r = _req("GET", "/admin/asset-mapping/operational-impact")
    assert r["status"] in (401, 403)


def test_operational_impact_shape(tok):
    r = _req("GET", "/admin/asset-mapping/operational-impact", token=tok)
    assert r["status"] == 200
    out = r["json"]
    assert out["ok"] is True
    for key in ("current", "potential", "actions",
                "readiness", "readiness_reason"):
        assert key in out, f"missing key {key}"
    for k in ("trust_score_pct", "coverage_pct", "mapped_assets",
              "unmapped_assets", "total_dispatch_trucks"):
        assert k in out["current"]
    for k in ("trust_score_pct", "coverage_pct",
              "mapped_assets", "unmapped_assets"):
        assert k in out["potential"]
    for k in ("high_confidence_waiting", "estimated_dispatches_impacted",
              "estimated_assets_confirmed"):
        assert k in out["actions"]


def test_readiness_value_in_enum(tok):
    out = _req("GET", "/admin/asset-mapping/operational-impact",
               token=tok)["json"]
    assert out["readiness"] in (
        "NOT_READY", "PARTIALLY_READY", "READY_FOR_ACTIVATION"
    )


def test_readiness_logic_consistent_with_directive(tok):
    """Directive rules:
       coverage >= 75 AND high == 0 → READY_FOR_ACTIVATION
       coverage > 25                → PARTIALLY_READY
       else                         → NOT_READY"""
    out = _req("GET", "/admin/asset-mapping/operational-impact",
               token=tok)["json"]
    cov = out["current"]["coverage_pct"]
    high = out["actions"]["high_confidence_waiting"]
    r = out["readiness"]
    if cov >= 75.0 and high == 0:
        assert r == "READY_FOR_ACTIVATION"
    elif cov > 25.0:
        assert r == "PARTIALLY_READY"
    else:
        assert r == "NOT_READY"


def test_projected_state_monotonic(tok):
    """Approving HIGH proposals can only increase mapped + coverage."""
    out = _req("GET", "/admin/asset-mapping/operational-impact",
               token=tok)["json"]
    assert out["potential"]["mapped_assets"] >= out["current"]["mapped_assets"]
    assert out["potential"]["coverage_pct"] >= out["current"]["coverage_pct"]
    assert out["potential"]["unmapped_assets"] <= out["current"]["unmapped_assets"]


def test_estimated_assets_confirmed_equals_high_waiting(tok):
    out = _req("GET", "/admin/asset-mapping/operational-impact",
               token=tok)["json"]
    assert (out["actions"]["estimated_assets_confirmed"] ==
            out["actions"]["high_confidence_waiting"])


def test_no_writes_on_repeated_get(tok):
    """Repeated GETs do not mutate the proposal collection."""
    a = _req("GET", "/admin/asset-mapping/queue", token=tok)["json"]
    _req("GET", "/admin/asset-mapping/operational-impact", token=tok)
    _req("GET", "/admin/asset-mapping/operational-impact", token=tok)
    b = _req("GET", "/admin/asset-mapping/queue", token=tok)["json"]
    assert a["counts"]["TOTAL"] == b["counts"]["TOTAL"]
    assert a["counts"].get("VERIFIED", 0) == b["counts"].get("VERIFIED", 0)
    assert a["counts"].get("REJECTED", 0) == b["counts"].get("REJECTED", 0)


def test_runbook_path_returned(tok):
    out = _req("GET", "/admin/asset-mapping/operational-impact",
               token=tok)["json"]
    assert out.get("runbook_path", "").endswith("MOTIVE_DAY1_ACTIVATION_RUNBOOK.md")


def test_no_httpx_no_motive_writes_in_router_source():
    """Constitutional guard: the router must not import httpx or motive_service
    (i.e., it cannot push to Motive)."""
    src_path = os.path.join(os.path.dirname(__file__), "..", "routes",
                             "asset_mapping_recon.py")
    src = open(os.path.abspath(src_path)).read()
    assert "import httpx" not in src
    assert "from services.motive_service" not in src
    assert "import services.motive_service" not in src
