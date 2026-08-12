from __future__ import annotations

import json
from pathlib import Path


def test_frontend_release_identity_candidate_urls_prioritize_public_hosting_signals():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'build_frontend_effective_identity' in source
    assert 'frontend_identity_contracts_match' in source
    assert 'frontend_identity_mode' in source


def test_intended_release_uses_unsaved_candidate_semantics_when_git_is_dirty():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'UNSAVED_FINAL_CANDIDATE:UNPROVEN:' in source
    assert 'workspace_candidate_identity(' in source
    assert '_REPO_ROOT' in source
    assert 'env=os.environ' in source


def test_public_release_identity_file_contains_runtime_contract_not_tracked_sha():
    payload = json.loads(Path('/app/frontend/public/release-identity.json').read_text(encoding='utf-8'))
    assert payload['identity_mode'] == 'runtime-api-version'
    assert payload['identity_endpoint'] == '/api/version'
    assert payload['post_save_source_mutation_required'] is False
    assert payload['tracked_commit_embed_allowed'] is False


def test_stamp_script_writes_runtime_contract_not_embedded_commit():
    source = Path('/app/frontend/scripts/stamp-build-version.js').read_text(encoding='utf-8')
    assert 'runtime:/api/version' in source
    assert 'BUILD_TRACKED_COMMIT_EMBED_ALLOWED = false' in source


def test_server_version_contract_uses_runtime_contract_not_served_static_probe():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'frontend_identity_contracts_match' in source
    assert 'frontend_build_source' in source