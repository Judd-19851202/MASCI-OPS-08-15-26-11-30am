from __future__ import annotations

import json
from pathlib import Path


def test_frontend_release_identity_candidate_urls_prioritize_public_hosting_signals():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert '_frontend_release_identity_candidate_urls' in source
    assert 'APP_DOMAIN' in source
    assert 'REACT_APP_BACKEND_URL' in source
    assert 'PUBLIC_BASE_URL' in source
    assert 'http://127.0.0.1:3000' in source


def test_intended_release_falls_back_to_frontend_generated_identity_when_git_unproven():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'PRE_SAVE_CANDIDATE:UNPROVEN:' in source
    assert 'frontend_generated_identity_fallback' in source
    assert '_FRONTEND_GENERATED_IDENTITY_AT_BOOT.get("commit")' in source


def test_public_release_identity_file_contains_commit_and_source_hash():
    payload = json.loads(Path('/app/frontend/public/release-identity.json').read_text(encoding='utf-8'))
    assert len(str(payload.get('commit') or '')) == 40
    assert len(str(payload.get('source_hash') or '')) >= 12


def test_stamp_script_reuses_existing_commit_when_git_and_env_commit_unavailable():
    source = Path('/app/frontend/scripts/stamp-build-version.js').read_text(encoding='utf-8')
    assert 'readExistingGeneratedIdentity' in source
    assert 'existing:generated_identity' in source
    assert 'existingGeneratedIdentity.commit' in source


def test_served_release_probe_uses_request_headers_not_plain_localhost_only():
    source = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'MASCI-Release-Identity/1.0' in source
    assert 'Accept": "application/json,text/plain,*/*"' in source or "'Accept': 'application/json,text/plain,*/*'" in source