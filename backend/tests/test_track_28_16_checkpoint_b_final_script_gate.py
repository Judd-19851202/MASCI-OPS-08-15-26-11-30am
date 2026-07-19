from __future__ import annotations

from pathlib import Path


OPEN_P1 = [
    '/app/backend/scripts/basecamp_import.py',
    '/app/backend/scripts/basecamp_import_big.py',
    '/app/backend/scripts/migrate_dr_v2_collections_to_daily_report.py',
    '/app/backend/scripts/track_15_28c_canonicalization_migration.py',
    '/app/backend/scripts/track_15_67_second_tenant_simulation.py',
    '/app/scripts/automated_drill.py',
    '/app/scripts/cleanup_production_contamination.py',
    '/app/scripts/r2_lifecycle_apply.py',
]


def test_all_open_p1_scripts_now_have_fail_closed_contracts():
    expected_tokens = {
        'basecamp_import.py': 'IMPORT_BASECAMP_DATA',
        'basecamp_import_big.py': 'IMPORT_BASECAMP_DATA',
        'migrate_dr_v2_collections_to_daily_report.py': 'MIGRATE_DR_V2_TO_DAILY_REPORTS',
        'track_15_28c_canonicalization_migration.py': 'RUN_CANONICALIZATION_MIGRATION',
        'automated_drill.py': 'RUN_ISOLATED_RECOVERY_DRILL',
        'cleanup_production_contamination.py': 'REMOVE_VERIFIED_PRODUCTION_CONTAMINATION',
        'r2_lifecycle_apply.py': 'APPLY_R2_LIFECYCLE_POLICY',
    }
    for path in OPEN_P1:
        src = Path(path).read_text(encoding='utf-8')
        if path.endswith('track_15_67_second_tenant_simulation.py'):
            assert 'Refusing second-tenant simulation against production semantics.' in src
            assert 'preview' in src.lower() or 'test' in src.lower()
            continue
        assert '--allow-production' in src or '--allow-prod' in src
        assert '--backup-ack' in src or 'backup_ack' in src
        assert '--execute' in src or '--apply' in src or 'args.live' in src
        token = expected_tokens[Path(path).name]
        assert token in src
