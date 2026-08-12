from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path("/app")


def test_stamp_script_uses_runtime_contract_not_tracked_sha() -> None:
    src = (REPO_ROOT / "frontend/scripts/stamp-build-version.js").read_text(encoding="utf-8")
    assert 'runtime-api-version' in src
    assert 'BUILD_POST_SAVE_SOURCE_MUTATION_REQUIRED = false' in src
    assert 'BUILD_TRACKED_COMMIT_EMBED_ALLOWED = false' in src
    assert 'BUILD_COMMIT' not in src


def test_release_identity_verifier_reports_one_canonical_sha() -> None:
    completed = subprocess.run(
        ["python3", "backend/scripts/verify_release_identity.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["canonical_release_commit"]
    assert payload["workspace_head_commit"] == payload["canonical_release_commit"]
    assert payload["frontend_commit"] == payload["canonical_release_commit"]
    assert payload["runtime_commit"] == payload["canonical_release_commit"]
    assert payload["workspace_head_matches_runtime"] is True
    assert payload["workspace_head_matches_frontend"] is True
    assert payload["frontend_matches_runtime"] is True


def test_public_release_identity_file_is_runtime_contract() -> None:
    payload = json.loads((REPO_ROOT / "frontend/public/release-identity.json").read_text(encoding="utf-8"))
    generated = (REPO_ROOT / "frontend/src/buildVersion.generated.js").read_text(encoding="utf-8")
    assert payload["identity_mode"] == "runtime-api-version"
    assert payload["identity_endpoint"] == "/api/version"
    assert payload["post_save_source_mutation_required"] is False
    assert payload["tracked_commit_embed_allowed"] is False
    assert 'BUILD_IDENTITY_MODE = "runtime-api-version"' in generated
    assert 'BUILD_IDENTITY_ENDPOINT = "/api/version"' in generated
    assert 'BUILD_COMMIT =' not in generated
    assert 'BUILD_WORKSPACE_DIRTY' not in generated