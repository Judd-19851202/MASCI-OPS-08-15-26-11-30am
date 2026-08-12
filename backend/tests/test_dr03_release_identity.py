from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import requests

from lib.release_identity import (
    assert_release_identity_parity,
    build_fingerprint_paths,
    build_frontend_effective_identity,
    build_instance_fingerprint,
    commits_match,
    compute_source_hash,
    parse_frontend_build_identity_text,
    read_frontend_build_identity,
    read_release_fingerprint_relative_paths,
    release_identities_match,
    resolve_runtime_release_identity,
    workspace_candidate_identity,
)


REPO_ROOT = Path("/app")
SERVER_PY = REPO_ROOT / "backend/server.py"
BUILD_FILE = REPO_ROOT / "frontend/src/buildVersion.generated.js"
LOCAL_API = "http://127.0.0.1:8001/api/version"


def _write_contract(repo_root: Path) -> None:
    (repo_root / "docs/governance").mkdir(parents=True, exist_ok=True)
    (repo_root / "docs/governance/release_content_fingerprint_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "TEST/v1",
                "algorithm_version": "test-sha256-v1",
                "include_roots": ["."],
                "exclude_exact": [],
                "exclude_globs": [".git/**"],
                "normalize": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "frontend/src").mkdir(parents=True, exist_ok=True)
    (repo_root / "frontend/public").mkdir(parents=True, exist_ok=True)
    (repo_root / "frontend/src/buildVersion.generated.js").write_text(
        'export const BUILD_VERSION_LABEL = "runtime:/api/version";\n'
        'export const BUILD_IDENTITY_MODE = "runtime-api-version";\n'
        'export const BUILD_IDENTITY_ENDPOINT = "/api/version";\n'
        'export const BUILD_RUNTIME_BINDING_REQUIRED = true;\n'
        'export const BUILD_POST_SAVE_SOURCE_MUTATION_REQUIRED = false;\n'
        'export const BUILD_TRACKED_COMMIT_EMBED_ALLOWED = false;\n',
        encoding="utf-8",
    )
    (repo_root / "frontend/public/release-identity.json").write_text(
        json.dumps(
            {
                "schema_version": "MASCI_FRONTEND_RELEASE_IDENTITY_CONTRACT/v2",
                "version_label": "runtime:/api/version",
                "identity_mode": "runtime-api-version",
                "identity_endpoint": "/api/version",
                "runtime_binding_required": True,
                "post_save_source_mutation_required": False,
                "tracked_commit_embed_allowed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "app.py").write_text("print('ready')\n", encoding="utf-8")


def _init_git_repo(repo_root: Path) -> str:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()


def test_api_version_uses_runtime_release_identity_module() -> None:
    src = SERVER_PY.read_text(encoding="utf-8")
    assert "resolve_runtime_release_identity(" in src
    assert '"frontend_backend_release_match"' in src
    assert '"instance_fingerprint"' in src
    assert '"workspace_dirty"' in src


def test_frontend_build_identity_parses_runtime_contract() -> None:
    parsed = parse_frontend_build_identity_text(BUILD_FILE.read_text(encoding="utf-8"))
    assert parsed["identity_mode"] == "runtime-api-version"
    assert parsed["identity_endpoint"] == "/api/version"
    assert parsed["post_save_source_mutation_required"] is False
    assert parsed["tracked_commit_embed_allowed"] is False


def test_runtime_release_identity_clean_and_dirty_semantics(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_contract(repo_root)
    head = _init_git_repo(repo_root)

    clean = resolve_runtime_release_identity(repo_root, env={})
    assert clean["commit"] == head
    assert clean["workspace_dirty"] is False
    assert clean["identity_mismatch"] is False
    assert clean["version"].startswith("sha-")

    (repo_root / "app.py").write_text("print('dirty')\n", encoding="utf-8")
    dirty = resolve_runtime_release_identity(repo_root, env={})
    assert dirty["commit"] == head
    assert dirty["workspace_dirty"] is True
    assert dirty["version"].startswith("workspace-")


def test_runtime_release_identity_injected_and_mismatch_semantics(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_contract(repo_root)
    head = _init_git_repo(repo_root)

    plain_root = tmp_path / "plain"
    plain_root.mkdir()
    _write_contract(plain_root)
    (plain_root / "frontend/src").mkdir(parents=True, exist_ok=True)
    (plain_root / "frontend/public").mkdir(parents=True, exist_ok=True)
    (plain_root / "app.py").write_text("print('plain')\n", encoding="utf-8")
    injected_only = resolve_runtime_release_identity(plain_root, env={"DEPLOY_VERSION_HASH": "a" * 40})
    assert injected_only["commit"] == "a" * 40
    assert injected_only["identity_mismatch"] is False

    mismatch = resolve_runtime_release_identity(repo_root, env={"DEPLOY_VERSION_HASH": "b" * 40})
    assert mismatch["commit"] == "b" * 40
    assert mismatch["git_head_commit"] == head
    assert mismatch["identity_mismatch"] is True


def test_frontend_effective_identity_binds_to_runtime_without_tracked_sha(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_contract(repo_root)
    head = _init_git_repo(repo_root)

    runtime_release = resolve_runtime_release_identity(repo_root, env={})
    frontend_identity = build_frontend_effective_identity(repo_root, runtime_release=runtime_release)
    assert frontend_identity["commit"] == head
    assert frontend_identity["source_hash"] == runtime_release["source_hash"]
    assert frontend_identity["identity_mode"] == "runtime-api-version"
    assert frontend_identity["post_save_source_mutation_required"] is False


def test_next_owner_save_binds_new_sha_without_tracked_source_mutation(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_contract(repo_root)
    first_head = _init_git_repo(repo_root)

    build_before = (repo_root / "frontend/src/buildVersion.generated.js").read_text(encoding="utf-8")
    public_before = (repo_root / "frontend/public/release-identity.json").read_text(encoding="utf-8")

    (repo_root / "app.py").write_text("print('ready v2')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "owner save"], cwd=repo_root, check=True, capture_output=True)
    second_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()

    assert second_head != first_head
    assert (repo_root / "frontend/src/buildVersion.generated.js").read_text(encoding="utf-8") == build_before
    assert (repo_root / "frontend/public/release-identity.json").read_text(encoding="utf-8") == public_before

    runtime_release = resolve_runtime_release_identity(repo_root, env={})
    frontend_identity = build_frontend_effective_identity(repo_root, runtime_release=runtime_release)
    assert runtime_release["commit"] == second_head
    assert frontend_identity["commit"] == second_head
    assert frontend_identity["post_save_source_mutation_required"] is False
    assert frontend_identity["tracked_commit_embed_allowed"] is False


def test_frontend_backend_match_detects_mismatch() -> None:
    assert commits_match("35f763df2cce", "35f763d") is True
    assert commits_match("35f763df2cce", "706e56d") is False
    assert release_identities_match(
        backend_commit="35f763df2cce",
        backend_source_hash="abc",
        frontend_commit="706e56d",
        frontend_source_hash="abc",
    ) is False
    assert release_identities_match(
        backend_commit="35f763df2cce",
        backend_source_hash="abc",
        frontend_commit="35f763d",
        frontend_source_hash="abc",
    ) is True


def test_source_hash_includes_release_contract_and_runtime_owner() -> None:
    release_hash = compute_source_hash(REPO_ROOT)
    rel_paths = [p.relative_to(REPO_ROOT).as_posix() for p in build_fingerprint_paths(REPO_ROOT)]
    assert len(release_hash) == 64
    for expected in (
        "docs/governance/release_content_fingerprint_contract.json",
        "backend/lib/release_fingerprint.py",
        "backend/lib/release_identity.py",
        "backend/scripts/verify_release_identity.py",
        "frontend/scripts/stamp-build-version.js",
        "frontend/src/buildVersion.generated.js",
        "frontend/public/release-identity.json",
    ):
        assert expected in rel_paths


def test_release_scope_file_is_single_source_of_truth() -> None:
    rels = read_release_fingerprint_relative_paths(REPO_ROOT)
    assert "docs/governance/release_content_fingerprint_contract.json" in rels
    assert "backend/server.py" in rels
    assert "frontend/public/release-identity.json" in rels


def test_instance_fingerprint_changes_when_runtime_identity_changes() -> None:
    a = build_instance_fingerprint("abc123", "hash1", "2026-07-14T00:00:00+00:00")
    b = build_instance_fingerprint("abc123", "hash2", "2026-07-14T00:00:00+00:00")
    c = build_instance_fingerprint("abc123", "hash2", "2026-07-14T00:01:00+00:00")
    assert a != b
    assert b != c


def test_release_identity_parity_guard_raises_on_mismatch() -> None:
    with pytest.raises(RuntimeError, match="release identity mismatch"):
        assert_release_identity_parity(
            backend_commit="abc1234",
            backend_source_hash="hash-a",
            frontend_commit="abc1234",
            frontend_source_hash="hash-b",
        )


def test_release_identity_parity_guard_allows_exact_match() -> None:
    assert_release_identity_parity(
        backend_commit="abc1234",
        backend_source_hash="hash-a",
        frontend_commit="abc1234",
        frontend_source_hash="hash-a",
    )


def test_local_api_version_reports_frontend_backend_release_parity() -> None:
    try:
        r = requests.get(LOCAL_API, timeout=60)
    except requests.RequestException as exc:
        pytest.skip(f"local release endpoint unavailable under fail-closed preview: {exc}")
    assert r.status_code == 200
    body = r.json()
    assert body["frontend_backend_release_match"] is True
    assert body["frontend_build_source_hash"] == body["source_hash"]
    assert body["frontend_build_commit"] == body["commit"]
    assert body["frontend_identity_mode"] == "runtime-api-version"


def test_repeated_local_version_requests_keep_same_instance_fingerprint() -> None:
    try:
        first = requests.get(LOCAL_API, timeout=20).json()
        second = requests.get(LOCAL_API, timeout=20).json()
    except requests.RequestException as exc:
        pytest.skip(f"local release endpoint unavailable under fail-closed preview: {exc}")
    assert first["instance_fingerprint"] == second["instance_fingerprint"]
    assert first["source_hash"] == second["source_hash"]


def test_workspace_candidate_identity_honestly_labels_dirty_workspace() -> None:
    candidate, source, snapshot = workspace_candidate_identity(REPO_ROOT, env={})
    assert source in {"git:HEAD", "workspace:unsaved_final_candidate"}
    if snapshot.get("dirty"):
        assert candidate.startswith("UNSAVED_FINAL_CANDIDATE:")
    else:
        assert len(candidate) >= 12