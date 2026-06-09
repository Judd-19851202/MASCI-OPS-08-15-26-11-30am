"""DR-FIX-2 · Trust & Usability Remediation regression.

R7: superintendent auto-population helper endpoint.
R12: replace inert Close Window button with Done navigation.

Doctrine: /app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request

import pytest


BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"


def _req(method, path, *, body=None, token="", token_header="X-Admin-Token"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers[token_header] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return {"status": resp.status, "json": json.loads(raw.decode() or "{}")}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        try:
            parsed = json.loads(body_txt)
        except Exception:
            parsed = {"detail": body_txt}
        return {"status": e.code, "json": parsed}


@pytest.fixture(scope="module")
def admin_token():
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = _req("POST", "/admin/login", body={"password": pwd})
    assert r["status"] == 200
    return r["json"]["token"]


@pytest.fixture(scope="module")
def seed_dr_with_super(admin_token):
    """Submit a DR carrying a known superintendent for a unique project_number."""
    body = {
        "project_name": "DR-FIX-2 · R7 fixture",
        "project_number": "JOB-FIX2-R7",
        "location": "Test Yard",
        "report_date": "2026-06-08",
        "prepared_by": "Pytest Foreman",
        "superintendent": "Maria Test-Super",
        "photos": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII="
        ] * 6,
        "prepared_by_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII=",
    }
    r = _req("POST", "/daily-reports", token=admin_token, body=body)
    assert r["status"] == 200, r
    return r["json"]


# ── R7 ──────────────────────────────────────────────────────────────
def test_r7_recent_context_endpoint_returns_superintendent(seed_dr_with_super):
    """Public helper returns the most recent DR's superintendent for a project."""
    r = _req("GET", "/jobs/JOB-FIX2-R7/recent-context")
    assert r["status"] == 200
    assert r["json"]["superintendent"] == "Maria Test-Super"


def test_r7_recent_context_empty_project_returns_empty():
    r = _req("GET", "/jobs/UNKNOWN-JOB-XYZ/recent-context")
    assert r["status"] == 200
    assert r["json"]["superintendent"] == ""


def test_r7_recent_context_endpoint_is_public_no_token_required():
    """The helper must be reachable without authentication so the
    public /daily/submit form can call it before login."""
    import urllib.request as _ur
    req = _ur.Request(f"{API}/jobs/JOB-FIX2-R7/recent-context", method="GET")
    with _ur.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
    assert resp.status == 200
    assert "superintendent" in body


def test_r7_form_apply_job_source_level_guard():
    """Static guard: NewDailyReport.jsx applyJob must auto-fill
    `superintendent` from the job + fallback to /recent-context."""
    src = open("/app/frontend/src/pages/NewDailyReport.jsx", "r", encoding="utf-8").read()
    assert "superintendent_name || job.superintendent" in src, \
        "R7 jobs_master superintendent precedence missing"
    assert "/recent-context" in src, \
        "R7 fallback fetch missing"
    # Must NOT overwrite a foreman-typed value:
    assert "p.superintendent && p.superintendent.trim()" in src, \
        "R7 must preserve foreman override"


def test_r7_full_loop_dr_persists_super_and_pdf_renders_it(seed_dr_with_super, admin_token):
    """End-to-end: the DR persists the superintendent (no schema change)
    and the PDF body renders it."""
    r = _req("GET", f"/daily-reports/{seed_dr_with_super['id']}", token=admin_token)
    assert r["status"] == 200
    assert r["json"]["superintendent"] == "Maria Test-Super"
    from pdf_render import _render_daily  # noqa: PLC0415
    inner = _render_daily(r["json"])
    assert "Maria Test-Super" in inner, "R7 superintendent missing from PDF body"


# ── R12 ─────────────────────────────────────────────────────────────
def test_r12_thank_you_uses_navigation_not_window_close():
    """Static guard: ThankYou.jsx must not CALL window.close() and must
    render a Done button using react-router Link. (Doctrine comments
    that mention the deprecated pattern are permitted.)"""
    src = open("/app/frontend/src/pages/ThankYou.jsx", "r", encoding="utf-8").read()
    # Strip comments before checking — a doctrine note may legitimately
    # reference the deprecated call by name.
    import re as _re
    code_only = _re.sub(r"//.*", "", src)
    code_only = _re.sub(r"/\*.*?\*/", "", code_only, flags=_re.DOTALL)
    assert "window.close(" not in code_only, \
        "R12 window.close() call still present — inert button regression"
    assert 'data-testid="done-btn"' in src, "R12 done-btn testid missing"
    assert 'data-testid="close-btn"' not in src, \
        "R12 stale close-btn testid still present"
    # Done button must use Link to a real route, not <a href='#'>.
    assert '<Link to={homeHref}>' in src, \
        "R12 Done button must use react-router Link"
    assert 't("Done")' in src, "R12 label must be 'Done'"


def test_r12_home_href_routes_correctly():
    """Static guard: the homeHref derivation routes public submitters
    to /submit and everyone else to /."""
    src = open("/app/frontend/src/pages/ThankYou.jsx", "r", encoding="utf-8").read()
    assert 'returnTo.startsWith("/daily/submit")' in src, \
        "R12 public-submit branch missing"
    assert '"/submit"' in src and '"/"' in src
