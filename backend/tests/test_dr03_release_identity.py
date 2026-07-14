from __future__ import annotations

from pathlib import Path

import requests

from lib.release_identity import (
    build_fingerprint_paths,
    build_instance_fingerprint,
    commits_match,
    compute_source_hash,
    parse_frontend_build_identity_text,
    read_frontend_build_identity,
    release_identities_match,
    resolve_runtime_commit,
)


REPO_ROOT = Path("/app")
SERVER_PY = REPO_ROOT / "backend/server.py"
BUILD_FILE = REPO_ROOT / "frontend/src/buildVersion.generated.js"
LOCAL_API = "http://localhost:8001/api/version"


def test_api_version_uses_release_identity_module():
    src = SERVER_PY.read_text(encoding="utf-8")
    assert "resolve_runtime_commit(" in src
    assert '"frontend_backend_release_match"' in src
    assert '"instance_fingerprint"' in src
    assert '"source_hash_scope_files"' in src


def test_frontend_build_identity_parses_commit_and_timestamp():
    parsed = parse_frontend_build_identity_text(BUILD_FILE.read_text(encoding="utf-8"))
    assert parsed["version"]
    assert parsed["built_at"]
    assert parsed["source_hash"]
    assert parsed["commit"]
    assert len(parsed["commit"]) == 7


def test_resolve_runtime_commit_uses_env_commit_when_present():
    frontend_identity = read_frontend_build_identity(REPO_ROOT)
    env = {"GIT_COMMIT": "706e56d510c4"}
    commit, source = resolve_runtime_commit(
        REPO_ROOT,
        frontend_build_commit=frontend_identity.get("commit"),
        source_hash=compute_source_hash(REPO_ROOT),
        env=env,
    )
    assert source == "env:GIT_COMMIT"
    assert commit == "706e56d510c4"


def test_resolve_runtime_commit_falls_back_to_git_head_when_env_absent():
    frontend_identity = read_frontend_build_identity(REPO_ROOT)
    commit, source = resolve_runtime_commit(
        REPO_ROOT,
        frontend_build_commit=frontend_identity.get("commit"),
        source_hash=compute_source_hash(REPO_ROOT),
        env={},
    )
    assert source == "git:HEAD"
    assert len(commit) >= 12


def test_frontend_backend_match_detects_mismatch():
    assert commits_match("35f763df2cce", "35f763d") is True
    assert commits_match("35f763df2cce", "706e56d") is False
    assert release_identities_match(
        backend_commit="35f763df2cce",
        backend_source_hash="abc",
        frontend_commit="706e56d",
        frontend_source_hash="abc",
    ) is True
    assert release_identities_match(
        backend_commit="35f763df2cce",
        backend_source_hash="abc",
        frontend_commit="35f763d",
        frontend_source_hash="def",
    ) is False


def test_source_hash_includes_frontend_and_backend_release_files():
    release_hash = compute_source_hash(REPO_ROOT)
    rel_paths = [p.relative_to(REPO_ROOT).as_posix() for p in build_fingerprint_paths(REPO_ROOT)]
    assert len(release_hash) == 32
    for expected in (
        "frontend/src/app/routing/AppRoutes.jsx",
        "frontend/src/pages/NewDailyReportV3.jsx",
        "frontend/src/pages/DailyReportsDashboard.jsx",
        "backend/routes/daily_reports.py",
    ):
        assert expected in rel_paths


def test_instance_fingerprint_changes_when_runtime_identity_changes():
    a = build_instance_fingerprint("abc123", "hash1", "2026-07-14T00:00:00+00:00")
    b = build_instance_fingerprint("abc123", "hash2", "2026-07-14T00:00:00+00:00")
    c = build_instance_fingerprint("abc123", "hash2", "2026-07-14T00:01:00+00:00")
    assert a != b
    assert b != c


def test_generated_frontend_source_hash_matches_current_release_scope():
    parsed = parse_frontend_build_identity_text(BUILD_FILE.read_text(encoding="utf-8"))
    assert parsed["source_hash"] == compute_source_hash(REPO_ROOT)


def test_local_api_version_reports_frontend_backend_release_parity():
    r = requests.get(LOCAL_API, timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert body["frontend_backend_release_match"] is True
    assert body["frontend_build_source_hash"] == body["source_hash"]
    assert body["commit"].startswith(body["frontend_build_commit"])


def test_repeated_local_version_requests_keep_same_instance_fingerprint():
    first = requests.get(LOCAL_API, timeout=20).json()
    second = requests.get(LOCAL_API, timeout=20).json()
    assert first["instance_fingerprint"] == second["instance_fingerprint"]
    assert first["source_hash"] == second["source_hash"]