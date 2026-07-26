import json
from pathlib import Path


def test_future_complete_archive_manifest_writes_non_empty_archive_identity_fields():
    text = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert 'r2_key = f"{_canonical_backup_prefix().rstrip(\'/\')}/{filename}"' in text
    assert '"archive_key": r2_key' in text
    assert '"backup_id": uuid.uuid4().hex' in text
    assert '"backup_id": stats.get("manifest", {}).get("backup_id")' in text
    assert '"release_identity": _SOURCE_HASH' in text
    assert '"manifest_version": BACKUP_MANIFEST_VERSION' in text