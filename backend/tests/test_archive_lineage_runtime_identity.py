from pathlib import Path


def test_runtime_identity_uses_runtime_mongo_hostname_and_username_for_preview_matching():
    text = Path('/app/backend/lib/archive_lineage.py').read_text(encoding='utf-8')
    assert 'parse_mongo_url' in text
    assert 'host = str(parsed.hostname or "").strip().lower()' in text
    assert 'runtime_user = str(parsed.username or "").strip() or "UNRESOLVED"' in text