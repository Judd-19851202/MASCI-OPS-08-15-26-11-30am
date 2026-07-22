from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    strict = "--strict" in sys.argv
    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root / "backend"))

    from lib.release_identity import (  # noqa: WPS433
        assert_release_identity_parity,
        commits_match,
        compute_dependency_manifest_hash,
        compute_migration_manifest_hash,
        compute_release_gate_manifest_hash,
        compute_source_hash,
        read_frontend_build_identity,
        read_release_fingerprint_relative_paths,
        resolve_runtime_commit,
        workspace_candidate_identity,
    )

    frontend = read_frontend_build_identity(repo_root)
    source_hash = compute_source_hash(repo_root)
    workspace_candidate, workspace_source, workspace_snapshot = workspace_candidate_identity(repo_root, env={})
    workspace_head_commit = (workspace_snapshot.get("head") or "").strip() or None
    runtime_commit, _ = resolve_runtime_commit(
        repo_root,
        frontend_build_commit=frontend.get("commit"),
        source_hash=source_hash,
        env={},
    )

    if frontend.get("source_hash") != source_hash:
        raise RuntimeError(
            f"frontend generated source_hash {frontend.get('source_hash')} != backend computed source_hash {source_hash}"
        )

    dependency_hash = compute_dependency_manifest_hash(repo_root)
    migration_hash = compute_migration_manifest_hash(repo_root)
    manifest_hash = compute_release_gate_manifest_hash(repo_root)
    if frontend.get("dependency_manifest_hash") != dependency_hash:
        raise RuntimeError("frontend dependency manifest hash mismatch")
    if frontend.get("migration_manifest_hash") != migration_hash:
        raise RuntimeError("frontend migration manifest hash mismatch")
    if frontend.get("release_gate_manifest_hash") != manifest_hash:
        raise RuntimeError("frontend release gate manifest hash mismatch")

    workspace_dirty = bool(workspace_snapshot.get("dirty"))
    if workspace_dirty and frontend.get("workspace_dirty") is False:
        raise RuntimeError("frontend generated build identity falsely claims a clean workspace")

    if workspace_head_commit and frontend.get("commit") and not commits_match(workspace_head_commit, frontend.get("commit")):
        raise RuntimeError(
            f"workspace HEAD {workspace_head_commit} != frontend generated commit {frontend.get('commit')}"
        )

    if workspace_head_commit and not commits_match(workspace_head_commit, runtime_commit):
        raise RuntimeError(f"workspace HEAD {workspace_head_commit} != runtime commit {runtime_commit}")

    if frontend.get("commit") and not workspace_dirty and not commits_match(runtime_commit, frontend.get("commit")):
        raise RuntimeError(
            f"frontend generated commit {frontend.get('commit')} != runtime commit {runtime_commit}"
        )

    canonical_release_commit = workspace_head_commit or runtime_commit or frontend.get("commit")
    if canonical_release_commit and frontend.get("commit") and not commits_match(canonical_release_commit, frontend.get("commit")):
        raise RuntimeError(
            f"canonical release commit {canonical_release_commit} != frontend generated commit {frontend.get('commit')}"
        )

    scope_paths = read_release_fingerprint_relative_paths(repo_root)
    missing_scope_files = [rel for rel in scope_paths if not (repo_root / rel).exists()]
    scope_file_present = (repo_root / "release_identity_scope.json").exists()
    if strict and not scope_file_present:
        raise RuntimeError("release_identity_scope.json missing")
    if strict and missing_scope_files:
        raise RuntimeError("release identity scope references missing files: " + ", ".join(missing_scope_files))

    assert_release_identity_parity(
        backend_commit=runtime_commit,
        backend_source_hash=source_hash,
        frontend_commit=frontend.get("commit"),
        frontend_source_hash=frontend.get("source_hash"),
    )

    payload = {
        "ok": True,
        "canonical_release_commit": canonical_release_commit,
        "runtime_commit": runtime_commit,
        "workspace_head_commit": workspace_head_commit,
        "workspace_candidate": workspace_candidate,
        "workspace_candidate_source": workspace_source,
        "workspace_dirty": workspace_dirty,
        "frontend_commit": frontend.get("commit"),
        "workspace_head_matches_runtime": commits_match(workspace_head_commit, runtime_commit),
        "workspace_head_matches_frontend": commits_match(workspace_head_commit, frontend.get("commit")),
        "frontend_matches_runtime": commits_match(frontend.get("commit"), runtime_commit),
        "source_hash": source_hash,
        "dependency_manifest_hash": dependency_hash,
        "migration_manifest_hash": migration_hash,
        "release_gate_manifest_hash": manifest_hash,
        "frontend_built_at": frontend.get("built_at"),
        "scope_file_present": scope_file_present,
        "missing_scope_files": missing_scope_files,
        "branch": os.popen("git branch --show-current 2>/dev/null").read().strip() or None,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())