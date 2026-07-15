from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path("/app")


def test_build_guard_script_passes_for_current_tree() -> None:
    completed = subprocess.run(
        ["python3", "backend/scripts/verify_release_identity.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["source_hash"]
    assert payload["runtime_commit"]
    assert payload["frontend_commit"]


def test_frontend_prebuild_invokes_build_guard() -> None:
    src = (REPO_ROOT / "frontend/scripts/stamp-build-version.js").read_text(encoding="utf-8")
    assert 'python3 backend/scripts/verify_release_identity.py' in src
    assert 'const SCOPE_FILE = path.join(REPO_ROOT, "release_identity_scope.json");' in src