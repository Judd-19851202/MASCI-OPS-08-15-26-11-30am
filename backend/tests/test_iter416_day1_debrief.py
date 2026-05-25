"""iter416 · Phase 19.1 · Day-1 Live Ops Debrief Capture endpoint tests.

Follows the iter412 pattern: uses real HTTP against REACT_APP_BACKEND_URL
+ legacy /api/admin/login break-glass password (NOT TestClient · NOT
multi-login which requires the user_directory to be seeded).

Verifies:
1. GET /api/admin/dls/day-1-debrief/questions returns canonical 12.
2. POST /api/admin/dls/day-1-debrief writes markdown to /app/memory.
3. Markdown contains the date, admin marker, all question labels, answers.
4. Same-day re-submission OVERWRITES the file (idempotent).
5. RBAC: non-admin caller is rejected (401).
6. Oversized answers are truncated server-side to 4000 chars.
7. Filename format `DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md` is locked.
"""
from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"
MEMORY_DIR = Path("/app/memory")


def _admin_hdrs():
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "MASCI1982!"},
        timeout=15,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token in this env.")


def _anon_status(path: str, method: str = "GET", body: bytes | None = None) -> int:
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 (iter416 anon test)",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ════════════════════════════════════════════════════════════════════
# 1. RBAC / auth gate
# ════════════════════════════════════════════════════════════════════
def test_iter416_questions_list_anon_blocked():
    assert _anon_status("/admin/dls/day-1-debrief/questions") in (401, 403)


def test_iter416_submit_anon_blocked():
    assert _anon_status(
        "/admin/dls/day-1-debrief",
        method="POST",
        body=b'{"answers":{}}',
    ) in (401, 403)


def test_iter416_submit_bogus_admin_token_blocked():
    r = requests.post(
        f"{API}/admin/dls/day-1-debrief",
        json={"answers": {}},
        headers={"X-Admin-Token": "not-a-real-token-iter416"},
        timeout=10,
    )
    assert r.status_code in (401, 403), r.text


# ════════════════════════════════════════════════════════════════════
# 2. Canonical question list
# ════════════════════════════════════════════════════════════════════
def test_iter416_questions_list_admin_ok():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/admin/dls/day-1-debrief/questions", headers=hdrs, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    qs = data.get("questions")
    assert isinstance(qs, list)
    assert len(qs) == 12, f"expected 12 questions, got {len(qs)}"
    labels = [q["label"] for q in qs]
    # 10 doctrine questions + 2 anti-creep
    assert "Where did dispatch hesitate?" in labels
    assert "What felt unnecessary or overly complicated?" in labels
    assert "What should remain simple and untouched?" in labels


# ════════════════════════════════════════════════════════════════════
# 3. Submission writes markdown
# ════════════════════════════════════════════════════════════════════
def test_iter416_submit_writes_markdown_file():
    hdrs = _admin_hdrs()
    payload = {
        "answers": {
            "q1": "ITER416-MARKER · Dispatchers hesitated at equipment-move pickup.",
            "q3": "Drivers understood shift start after first scan.",
            "q11": "Nothing felt unnecessary today.",
            "q12": "Issue Work tiles should stay exactly as they are.",
        },
        "operational_notes": "Two trucks waited >30 min at plant A.",
        "doctrine_observations": "Restraint held — nobody asked for a chart.",
    }
    r = requests.post(f"{API}/admin/dls/day-1-debrief", json=payload, headers=hdrs, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    assert data["question_count"] == 12
    assert data["filename"].startswith("DLS_DAY1_LIVE_OPS_DEBRIEF_")
    assert data["filename"].endswith(".md")

    path = MEMORY_DIR / data["filename"]
    assert path.exists(), f"markdown not written: {path}"

    body = path.read_text(encoding="utf-8")
    assert "# DLS Day-1 Live Ops Debrief" in body
    assert "ITER416-MARKER" in body
    assert "What felt unnecessary or overly complicated?" in body
    assert "What should remain simple and untouched?" in body
    assert "## Operational notes" in body
    assert "## Doctrine observations" in body
    assert "Capture operational hesitation" in body  # doctrine reminder


# ════════════════════════════════════════════════════════════════════
# 4. Idempotent same-day overwrite
# ════════════════════════════════════════════════════════════════════
def test_iter416_submit_overwrites_same_day():
    hdrs = _admin_hdrs()
    today = _today()
    path = MEMORY_DIR / f"DLS_DAY1_LIVE_OPS_DEBRIEF_{today}.md"

    r1 = requests.post(
        f"{API}/admin/dls/day-1-debrief",
        json={"answers": {"q1": "FIRST-ITER416-marker"}},
        headers=hdrs,
        timeout=10,
    )
    assert r1.status_code == 200, r1.text
    assert "FIRST-ITER416-marker" in path.read_text(encoding="utf-8")

    r2 = requests.post(
        f"{API}/admin/dls/day-1-debrief",
        json={"answers": {"q1": "SECOND-ITER416-marker"}},
        headers=hdrs,
        timeout=10,
    )
    assert r2.status_code == 200, r2.text
    body2 = path.read_text(encoding="utf-8")
    assert "SECOND-ITER416-marker" in body2
    assert "FIRST-ITER416-marker" not in body2, "submission appended instead of overwrote"


# ════════════════════════════════════════════════════════════════════
# 5. Oversized answer truncation
# ════════════════════════════════════════════════════════════════════
def test_iter416_submit_truncates_oversized_answer():
    hdrs = _admin_hdrs()
    huge = "x" * 50_000
    r = requests.post(
        f"{API}/admin/dls/day-1-debrief",
        json={"answers": {"q1": huge}},
        headers=hdrs,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    today = _today()
    path = MEMORY_DIR / f"DLS_DAY1_LIVE_OPS_DEBRIEF_{today}.md"
    body = path.read_text(encoding="utf-8")
    # 4000 chars of 'x' should appear · NOT 50000
    # Count consecutive x runs
    long_run = max((len(g.group()) for g in re.finditer(r"x+", body)), default=0)
    assert 0 < long_run <= 4000, (
        f"answer not truncated: longest x-run = {long_run} chars"
    )


# ════════════════════════════════════════════════════════════════════
# 6. Filename format lock
# ════════════════════════════════════════════════════════════════════
def test_iter416_filename_format_locked():
    hdrs = _admin_hdrs()
    r = requests.post(
        f"{API}/admin/dls/day-1-debrief",
        json={"answers": {"q1": "filename-format-test"}},
        headers=hdrs,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert re.match(
        r"^DLS_DAY1_LIVE_OPS_DEBRIEF_\d{4}-\d{2}-\d{2}\.md$",
        data["filename"]
    ), f"filename drifted: {data['filename']}"


# ════════════════════════════════════════════════════════════════════
# 7. Doctrine guard · no database insert in the module source
# ════════════════════════════════════════════════════════════════════
def test_iter416_no_database_persistence_in_source():
    """Doctrine: this module must not insert/update any Mongo doc."""
    import inspect
    from routes import dispatch_day1_debrief as m
    src = inspect.getsource(m)
    forbidden_calls = [
        "insert_one", "insert_many", "update_one", "update_many",
        "replace_one", "find_one_and_update",
    ]
    for forbidden in forbidden_calls:
        assert forbidden not in src, f"doctrine breach · {forbidden} found in module"
