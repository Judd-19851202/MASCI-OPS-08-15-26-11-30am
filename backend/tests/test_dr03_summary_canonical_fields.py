from pathlib import Path


DAILY_SUMMARY = Path("/app/backend/routes/daily_summary.py")


def test_daily_summary_accept_writes_canonical_ai_summary_fields():
    src = DAILY_SUMMARY.read_text(encoding="utf-8")
    assert '"ai_accepted_summary"' in src
    assert '"ai_accepted_summary_meta"' in src


def test_daily_summary_accept_keeps_legacy_fields_only_as_compatibility():
    src = DAILY_SUMMARY.read_text(encoding="utf-8")
    assert '"daily_operational_summary"' in src
    assert 'Legacy compatibility read fields retained temporarily.' in src
