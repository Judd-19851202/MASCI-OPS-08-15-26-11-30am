from pathlib import Path


def test_manifest_timeout_defaults_to_30_seconds_and_is_env_driven():
    text = Path('/app/backend/backup_verification.py').read_text(encoding='utf-8')
    assert 'BACKUP_R2_MANIFEST_TIMEOUT_SECONDS' in text
    assert 'R2_MANIFEST_TIMEOUT_SECONDS = float((os.environ.get("BACKUP_R2_MANIFEST_TIMEOUT_SECONDS") or "30").strip() or "30")' in text