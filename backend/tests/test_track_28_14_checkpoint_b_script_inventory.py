from __future__ import annotations

import re
from pathlib import Path


WRITE_PATTERNS = [
    r"\binsert_one\(", r"\binsert_many\(", r"\bupdate_one\(", r"\bupdate_many\(",
    r"\breplace_one\(", r"\bbulk_write\(", r"\bdelete_one\(", r"\bdelete_many\(",
    r"\bdrop_database\(", r"\bdrop_collection\(", r"\bcreate_index\(", r"\bdrop_index\(",
    r"\brename_collection\(", r"\bput_object\(", r"\bupload_file\(", r"\bcopy_object\(",
    r"\bdelete_object\(", r"\bdelete_objects\(", r"\.unlink\(", r"\brmtree\(",
    r"\.write_text\(", r"\.write_bytes\(", r"requests\.(post|put|patch|delete)\(",
    r"httpx\.(post|put|patch|delete)\(",
]


def _discover_write_capable_scripts() -> set[str]:
    out: set[str] = set()
    for root in [Path('/app/backend/scripts'), Path('/app/scripts')]:
        for path in root.rglob('*'):
            if not path.is_file() or path.suffix not in {'.py', '.sh', '.js'}:
                continue
            src = path.read_text(encoding='utf-8', errors='ignore')
            if any(re.search(pat, src) for pat in WRITE_PATTERNS):
                out.add(str(path.relative_to('/app')))
    return out


def _registered_scripts() -> set[str]:
    text = Path('/app/docs/governance/DANGEROUS_SCRIPT_REGISTER.md').read_text(encoding='utf-8')
    return set(re.findall(r'`((?:backend/scripts|scripts)/[^`]+)`', text))


def test_discovered_write_capable_scripts_are_registered():
    discovered = _discover_write_capable_scripts()
    registered = _registered_scripts()
    missing = sorted(discovered - registered)
    assert not missing, f'Unregistered write-capable scripts: {missing}'


def test_known_p1_scripts_are_guarded_fail_closed():
    expected = {
        '/app/backend/scripts/seed_project_memberships.py': 'SEED_PROJECT_MEMBERSHIPS',
        '/app/backend/scripts/seed_equipment_make_model.py': 'SEED_EQUIPMENT_MAKE_MODEL',
        '/app/backend/scripts/migrate_local_project_docs_to_r2.py': 'MIGRATE_LOCAL_PROJECT_DOCS_TO_R2',
        '/app/backend/scripts/track_15_65_seed_email_routes.py': 'SEED_EMAIL_ROUTES',
    }
    for path, token in expected.items():
        src = Path(path).read_text(encoding='utf-8')
        assert token in src
        assert '--backup-ack' in src or 'backup_ack' in src
        assert '--allow-production' in src or '--allow-prod' in src
        assert '--execute' in src or '--apply' in src
