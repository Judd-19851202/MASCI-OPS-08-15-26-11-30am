from __future__ import annotations

import json
from pathlib import Path


ROOT = Path('/app')


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8', errors='ignore')


def test_frontend_build_script_remains_craco_build() -> None:
    pkg = json.loads(_read('frontend/package.json'))
    assert pkg['scripts']['build'] == 'craco build'


def test_ci_environment_would_fail_build_when_warnings_exist() -> None:
    src = _read('frontend/craco.config.js')
    assert '"react-hooks/exhaustive-deps": "warn"' in src


def test_known_warning_source_files_are_still_present_in_repo() -> None:
    offenders = [
        'frontend/src/components/AdminAccessStatsTile.jsx',
        'frontend/src/components/daily-report/DailySummaryAssist.jsx',
        'frontend/src/pages/NewDailyReportV3.jsx',
    ]
    for rel in offenders:
        assert (ROOT / rel).exists(), rel


def test_release_identity_prebuild_guard_is_part_of_frontend_build() -> None:
    pkg = json.loads(_read('frontend/package.json'))
    assert pkg['scripts']['prebuild'] == 'node scripts/stamp-build-version.js'
    script = _read('frontend/scripts/stamp-build-version.js')
    assert 'python3 backend/scripts/verify_release_identity.py' in script