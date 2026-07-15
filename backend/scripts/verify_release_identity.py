from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root / "backend"))

    from lib.release_identity import (  # noqa: WPS433
        assert_release_identity_parity,
        commits_match,
        compute_source_hash,
        read_frontend_build_identity,
        resolve_runtime_commit,
    )

    frontend = read_frontend_build_identity(repo_root)
    source_hash = compute_source_hash(repo_root)
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

    if frontend.get("commit") and not commits_match(runtime_commit, frontend.get("commit")):
        raise RuntimeError(
            f"frontend generated commit {frontend.get('commit')} != runtime commit {runtime_commit}"
        )

    assert_release_identity_parity(
        backend_commit=runtime_commit,
        backend_source_hash=source_hash,
        frontend_commit=frontend.get("commit"),
        frontend_source_hash=frontend.get("source_hash"),
    )

    payload = {
        "ok": True,
        "runtime_commit": runtime_commit,
        "frontend_commit": frontend.get("commit"),
        "source_hash": source_hash,
        "frontend_built_at": frontend.get("built_at"),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())