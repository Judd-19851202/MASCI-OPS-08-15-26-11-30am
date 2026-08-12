from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
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
    assert payload["canonical_release_source_hash"]
    assert payload["runtime_commit"]
    assert payload["frontend_commit"]
    assert payload["frontend_identity_mode"] == "runtime-api-version"
    assert payload["workspace_head_matches_runtime"] is True


def test_frontend_prebuild_invokes_build_guard() -> None:
    src = (REPO_ROOT / "frontend/scripts/stamp-build-version.js").read_text(encoding="utf-8")
    assert 'backend/scripts/verify_release_identity.py' in src
    assert 'process.env.VIRTUAL_ENV' in src
    assert 'pythonCandidates' in src
    assert 'spawnSync(pythonExecutable' in src
    assert 'runtime-api-version' in src


def test_frontend_prebuild_falls_back_when_python_env_points_to_missing_binary() -> None:
    completed = subprocess.run(
        ["node", "frontend/scripts/stamp-build-version.js"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**__import__('os').environ, 'PYTHON': '/definitely-missing/python'},
        check=True,
    )
    assert completed.returncode == 0


def _run_stamp_with_only_interpreter(executable_name: str) -> subprocess.CompletedProcess[str]:
    node_path = shutil.which("node")
    assert node_path, "node is required for the stamp script regression tests"

    with tempfile.TemporaryDirectory() as temp_dir:
        link_path = Path(temp_dir) / executable_name
        os.symlink(sys.executable, link_path)
        return subprocess.run(
            [node_path, "frontend/scripts/stamp-build-version.js"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "PATH": temp_dir,
                "PYTHON": "",
                "VIRTUAL_ENV": "",
                "npm_config_python": "",
            },
            check=True,
        )


def test_frontend_prebuild_falls_back_to_python3_when_no_virtualenv_is_available() -> None:
    completed = _run_stamp_with_only_interpreter("python3")
    assert completed.returncode == 0


def test_frontend_prebuild_falls_back_to_python_when_python3_is_unavailable() -> None:
    completed = _run_stamp_with_only_interpreter("python")
    assert completed.returncode == 0