import json
from pathlib import Path


def test_future_complete_archive_manifest_writes_non_empty_archive_identity_fields():
    text = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'manifest["archive_key"] = r2_key' in text
    assert 'manifest["backup_bucket"] = _canonical_backup_bucket()' in text
    assert 'manifest["backup_prefix"] = _canonical_backup_prefix()' in text
    assert '"backup_id": uuid.uuid4().hex' in text
    assert '"release_identity": _SOURCE_HASH' in text
    assert '"manifest_version": BACKUP_MANIFEST_VERSION' in text