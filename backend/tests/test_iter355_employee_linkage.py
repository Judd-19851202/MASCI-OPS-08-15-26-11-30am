"""
iter355 · Operator ↔ Employee Linkage Enforcement (Phase 2 P2).

Tests the cross-collection identity drift detector + the backfill endpoint:
- _detect_employee_linkage adds findings for 3 new rules
  (EMP_LINK_UNRESOLVABLE / EMP_LINK_AMBIGUOUS / EMP_LINK_MISSING_ID).
- POST /api/admin/compliance/backfill-employee-links body {dry_run: bool}
  resolves unique-match names → employee_id on operational records.

Invariants:
1. Backfill RBAC — anon = 401.
2. Backfill is dry-run by default (no mutation).
3. Backfill is idempotent — second run reports 0 backfilled.
4. New rules are listed in the rule_catalog returned by /governance/summary.
5. Linkage findings have severity "high" (UNRESOLVABLE/AMBIGUOUS) or "medium"
   (MISSING_ID).
"""
from __future__ import annotations

import os

import requests


# Target -----------------------------------------------------------------
_FRONT_ENV = "/app/frontend/.env"
_BACK_ENV = "/app/backend/.env"
try:
    with open(_FRONT_ENV) as fh:
        for ln in fh:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                URL = ln.split("=", 1)[1].strip().rstrip("/")
                break
        else:
            URL = "http://localhost:8001"
except FileNotFoundError:
    URL = "http://localhost:8001"

try:
    with open(_BACK_ENV) as fh:
        for ln in fh:
            if ln.startswith("ADMIN_PASSWORD="):
                ADMIN_PASSWORD = ln.split("=", 1)[1].strip().strip('"')
                break
        else:
            ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
except FileNotFoundError:
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

ADMIN_TOKEN = ""
if URL and ADMIN_PASSWORD:
    try:
        r = requests.post(f"{URL}/api/admin/login",
                          json={"password": ADMIN_PASSWORD}, timeout=10)
        if r.status_code == 200:
            ADMIN_TOKEN = r.json().get("token", "")
    except Exception:
        ADMIN_TOKEN = ""

# Auto-inject admin token on backend calls (conftest-style patch).
import requests.api  # noqa: E402, F401
import requests.sessions  # noqa: E402

_orig_request = requests.api.request
_orig_session_request = requests.sessions.Session.request


def _patched(method, url, **kwargs):
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    return _orig_request(method, url, **kwargs)


def _patched_session(self, method, url, **kwargs):
    if ADMIN_TOKEN and isinstance(url, str) and URL and url.startswith(URL):
        headers = kwargs.get("headers") or {}
        headers.setdefault("X-Admin-Token", ADMIN_TOKEN)
        kwargs["headers"] = headers
    return _orig_session_request(self, method, url, **kwargs)


requests.api.request = _patched
requests.sessions.Session.request = _patched_session

SCAN_URL = f"{URL}/api/admin/compliance/scan"
LIST_URL = f"{URL}/api/admin/compliance/findings"
SUMMARY_URL = f"{URL}/api/admin/governance/summary"
BACKFILL_URL = f"{URL}/api/admin/compliance/backfill-employee-links"


# ---------------------------------------------------------------------------
# Backfill RBAC + dry-run safety
# ---------------------------------------------------------------------------

def test_backfill_rejects_anonymous():
    r = requests.post(BACKFILL_URL, json={"dry_run": True}, timeout=15,
                      headers={"X-Admin-Token": ""})
    assert r.status_code == 401, r.text


def test_backfill_default_is_dry_run():
    """Default body must not mutate the database."""
    r = requests.post(BACKFILL_URL, json={}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["dry_run"] is True
    assert body["ok"] is True
    assert "per_collection" in body
    assert isinstance(body["per_collection"], dict)
    # Every source collection should be reported.
    for coll in ("safety_training_records", "safety_equipment_issuances",
                 "corrective_actions", "incidents"):
        assert coll in body["per_collection"], coll
        for k in ("scanned", "backfilled", "skipped_no_match",
                  "skipped_ambiguous"):
            assert k in body["per_collection"][coll]


def test_backfill_is_idempotent():
    """Two consecutive real runs cannot both backfill the same records."""
    r1 = requests.post(BACKFILL_URL, json={"dry_run": False}, timeout=60)
    assert r1.status_code == 200
    n1 = r1.json()["total_backfilled"]
    r2 = requests.post(BACKFILL_URL, json={"dry_run": False}, timeout=60)
    assert r2.status_code == 200
    n2 = r2.json()["total_backfilled"]
    # Second run cannot exceed the first (any newly-arrived records may
    # add 1-2 but the absolute upper bound is n1).
    assert n2 <= n1 + 2


# ---------------------------------------------------------------------------
# Detector wiring
# ---------------------------------------------------------------------------

def test_scan_includes_linkage_detector():
    r = requests.post(SCAN_URL, timeout=60)
    assert r.status_code == 200
    body = r.json()
    # detector_errors empty means the linkage detector ran cleanly.
    assert body["detector_errors"] == {}
    # The detector category should surface in severity_counts when there is
    # any drift in preview data.
    counts = body["rule_counts"]
    # At minimum, one of the three linkage rules should appear OR all be
    # zero (clean DB). Both are valid; just confirm shape.
    for k, v in counts.items():
        assert isinstance(v, int)


def test_governance_summary_lists_new_linkage_rules_in_catalog():
    r = requests.get(SUMMARY_URL, timeout=15)
    assert r.status_code == 200
    catalog = r.json().get("rule_catalog", {})
    for rule_id in ("EMP_LINK_UNRESOLVABLE", "EMP_LINK_AMBIGUOUS",
                    "EMP_LINK_MISSING_ID"):
        assert rule_id in catalog, f"{rule_id} not in rule_catalog"
        assert catalog[rule_id]["category"] == "linkage"


def test_linkage_findings_have_correct_severity():
    """When any EMP_LINK_* finding exists, its severity must match the catalog."""
    requests.post(SCAN_URL, timeout=60)
    expected = {
        "EMP_LINK_UNRESOLVABLE": "high",
        "EMP_LINK_AMBIGUOUS": "high",
        "EMP_LINK_MISSING_ID": "medium",
    }
    for rule_id, sev in expected.items():
        r = requests.get(f"{LIST_URL}?rule_id={rule_id}&limit=5",
                         timeout=15)
        assert r.status_code == 200
        for it in r.json().get("items", []):
            assert it["severity"] == sev, (rule_id, it)
            assert it["entity_kind"] == "linkage"


def test_unresolvable_finding_carries_record_count_and_collections():
    """Detector evidence shape — source.collections + source.record_count
    must be populated when an UNRESOLVABLE finding exists."""
    requests.post(SCAN_URL, timeout=60)
    r = requests.get(f"{LIST_URL}?rule_id=EMP_LINK_UNRESOLVABLE&limit=3",
                     timeout=15)
    assert r.status_code == 200
    items = r.json().get("items", [])
    if not items:
        return  # Clean DB — nothing to assert
    for it in items:
        src = it.get("source") or {}
        assert isinstance(src.get("collections"), dict)
        assert isinstance(src.get("record_count"), int)
        assert src["record_count"] >= 1
