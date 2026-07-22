from __future__ import annotations

import json
from pathlib import Path


def test_stamp_script_tracks_final_git_status_after_generation() -> None:
    src = Path('/app/frontend/scripts/stamp-build-version.js').read_text(encoding='utf-8')
    assert 'git status --short' in src
    assert 'BUILD_WORKSPACE_DIRTY' in src


def test_release_identity_scope_contains_canonical_files() -> None:
    scope = json.loads(Path('/app/release_identity_scope.json').read_text(encoding='utf-8'))
    required = {
        'backend/lib/release_identity.py',
        'backend/scripts/verify_release_identity.py',
        'frontend/scripts/stamp-build-version.js',
        'frontend/src/pages/NewDailyReportV3.jsx',
    }
    assert required.issubset(set(scope))


def test_release_identity_verifier_reports_one_canonical_sha() -> None:
    import subprocess

    completed = subprocess.run(
        ['python3', 'backend/scripts/verify_release_identity.py'],
        cwd='/app',
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload['ok'] is True
    assert payload['canonical_release_commit']
    assert payload['workspace_head_commit'] == payload['canonical_release_commit']
    assert payload['frontend_commit'] == payload['canonical_release_commit']
    assert payload['runtime_commit'] == payload['canonical_release_commit']
    assert payload['workspace_head_matches_runtime'] is True
    assert payload['workspace_head_matches_frontend'] is True
    assert payload['frontend_matches_runtime'] is True