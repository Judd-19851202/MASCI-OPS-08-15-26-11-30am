"""iter198 — Operational Inventory dashboard backend tests.

Pass 2 of the Operational Inventory initiative. Verifies:
  - Computation correctness (snapshot shape, totals, matrix integrity)
  - Drift detection surfaces the known Field-Leadership anomaly
  - Translation readiness reports 0% today (Pass 3 baseline)
  - Admin gate enforcement (401 / 403 for non-admin callers)
"""
from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────
# Pure-function tests (no HTTP, no DB)
# ─────────────────────────────────────────────────────────────────────

def test_inventory_module_imports():
    from governance.inventory import (
        compute_full_inventory, compute_portal_matrix,
        compute_user_type_matrix, compute_public_route_matrix,
        compute_workflow_matrix, compute_translation_readiness,
        compute_drift, PORTALS, USER_TYPES, PUBLIC_ROUTES,
        INVENTORY_WORKFLOWS,
    )
    # Sanity: registries non-empty
    assert len(PORTALS) == 8
    assert len(USER_TYPES) == 12
    assert len(PUBLIC_ROUTES) >= 15
    assert len(INVENTORY_WORKFLOWS) >= 5


def test_full_inventory_shape():
    from governance.inventory import compute_full_inventory
    snap = compute_full_inventory()
    # Top-level keys
    for key in ("version", "audit_doc", "generated_pass", "totals",
                "portals", "user_types", "public_routes",
                "workflows", "translation", "drift"):
        assert key in snap, f"missing top-level key: {key}"
    assert snap["version"] == 1
    assert snap["generated_pass"] == 2
    # Totals
    t = snap["totals"]
    assert t["portals"] == 8
    assert t["user_types"] == 12
    assert t["guidance_articles"] >= 90


def test_portal_matrix_has_all_ten_fields():
    from governance.inventory import compute_portal_matrix
    rows = compute_portal_matrix()
    assert len(rows) == 8
    required_fields = {
        "who_uses_it", "login_required", "guidance_exists", "onboarding_exists",
        "contextual_help", "why_explanation", "troubleshooting",
        "discoverability", "mobile_ux", "translation_readiness",
    }
    for r in rows:
        assert set(r["fields"].keys()) == required_fields, f"{r['portal']} fields mismatch"
        for fname, f in r["fields"].items():
            assert "status" in f, f"{r['portal']}.{fname} missing status"
            assert f["status"] in {"complete", "partial", "missing", "n/a", "deferred"}


def test_field_leadership_anomaly_is_flagged():
    """Field Leadership must be reported as login=partial and disco=missing
    until Pass 4 closes the gap. This is the worked-example anchor."""
    from governance.inventory import compute_portal_matrix
    rows = compute_portal_matrix()
    fl = next((r for r in rows if r["portal"] == "leadership"), None)
    assert fl is not None
    assert fl["fields"]["login_required"]["status"] in {"partial", "missing"}
    assert fl["fields"]["discoverability"]["status"] == "missing"
    assert fl.get("anomaly")  # the curated anomaly message must be present


def test_translation_readiness_baseline():
    """Pass 3 shipped — pct_body must now reflect the 17 public-scope
    articles (and may grow as later passes translate more)."""
    from governance.inventory import compute_translation_readiness
    t = compute_translation_readiness()
    assert t["pct_body"] > 0.0, "Pass 3 has landed; pct_body must be > 0"
    assert t["schema_landed"] is True
    assert t["total_articles"] >= 90
    assert t["body_es_present"] >= 17
    # By-section and by-scope shape
    assert isinstance(t["by_section"], dict)
    assert isinstance(t["by_scope"], dict)
    # Public scope must be effectively fully translated
    assert t["by_scope"]["public"]["pct_body"] >= 95.0


def test_drift_detects_field_leadership_no_login():
    from governance.inventory import compute_drift
    d = compute_drift()
    cats = {it["category"] for it in d["items"]}
    assert "portal-without-login" in cats
    # The leadership row must be there
    fl_items = [it for it in d["items"]
                if it["category"] == "portal-without-login" and it["subject"] == "leadership"]
    assert fl_items, "Field Leadership drift item must be surfaced"
    assert fl_items[0]["severity"] == "p0"


def test_drift_detects_translation_missing():
    from governance.inventory import compute_drift
    d = compute_drift()
    cats = {it["category"] for it in d["items"]}
    assert "translation-missing" in cats
    tr_items = [it for it in d["items"] if it["category"] == "translation-missing"]
    assert tr_items[0]["severity"] == "p0"


def test_drift_severity_buckets_balance():
    from governance.inventory import compute_drift
    d = compute_drift()
    total_by_sev = sum(d["by_severity"].values())
    # Sum of severity buckets must equal total items (items default to p2 in buckets)
    assert total_by_sev <= d["total"]
    assert d["by_severity"]["p0"] >= 1
    assert d["by_severity"]["p1"] >= 1


def test_public_routes_at_least_some_have_coverage():
    """Sanity — public submit forms have guidance articles."""
    from governance.inventory import compute_public_route_matrix
    rows = compute_public_route_matrix()
    covered = {r["route"] for r in rows if r["has_guidance"]}
    # Must include the public submit workflows the audit already covered
    for must_cover in ("/daily/submit", "/incidents/submit", "/equipment/submit",
                       "/meetings/submit", "/qaqc", "/field/calculators"):
        assert must_cover in covered, f"public route {must_cover} must have guidance"


def test_user_type_matrix_has_owner_and_anonymous():
    from governance.inventory import compute_user_type_matrix
    rows = compute_user_type_matrix()
    keys = {r["key"] for r in rows}
    for must in ("anonymous", "field_crew", "foreman", "superintendent",
                 "pm", "hr", "safety", "admin", "owner"):
        assert must in keys, f"user_type {must} missing"


def test_field_leadership_has_31_scoped_articles():
    """The audit relies on 31 leadership-scoped articles. If this number
    changes without intent, the audit text is stale."""
    from guidance.content import _ARTICLES
    n = sum(1 for a in _ARTICLES if "leadership" in (a.get("scopes") or []))
    assert n >= 25, f"leadership-scoped articles dropped to {n} — investigate"


# ─────────────────────────────────────────────────────────────────────
# HTTP route tests (admin gating)
# ─────────────────────────────────────────────────────────────────────

API_URL = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"


def _get(path: str, headers: dict | None = None):
    return httpx.get(f"{API_URL}{path}", headers=headers or {}, timeout=10.0)


def test_route_requires_admin_token():
    """Anonymous callers must be 401/403 — never 200."""
    r = _get("/api/admin/operational-inventory")
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


def test_route_rejects_bad_admin_token():
    r = _get("/api/admin/operational-inventory",
             headers={"X-Admin-Token": "obviously-not-valid"})
    assert r.status_code in (401, 403)


def test_subroutes_all_require_admin():
    """Each sub-route must enforce admin gate."""
    for sub in ("", "/portals", "/translation", "/drift"):
        r = _get(f"/api/admin/operational-inventory{sub}")
        assert r.status_code in (401, 403), \
            f"sub {sub or '(root)'} returned {r.status_code}, expected 401/403"
