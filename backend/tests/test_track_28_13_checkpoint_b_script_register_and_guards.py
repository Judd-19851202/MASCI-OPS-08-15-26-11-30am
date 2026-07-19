from __future__ import annotations

from pathlib import Path


def test_seed_project_memberships_is_still_unguarded_and_registered():
    src = Path('/app/backend/scripts/seed_project_memberships.py').read_text(encoding='utf-8')
    reg = Path('/app/docs/governance/DANGEROUS_SCRIPT_REGISTER.md').read_text(encoding='utf-8')
    assert 'python3 /app/backend/scripts/seed_project_memberships.py' in src
    assert '--execute' not in src and '--apply' not in src
    assert 'seed_project_memberships.py' in reg


def test_seed_equipment_make_model_is_registered():
    reg = Path('/app/docs/governance/DANGEROUS_SCRIPT_REGISTER.md').read_text(encoding='utf-8')
    assert 'seed_equipment_make_model.py' in reg


def test_track_15_65_seed_email_routes_is_registered():
    reg = Path('/app/docs/governance/DANGEROUS_SCRIPT_REGISTER.md').read_text(encoding='utf-8')
    assert 'track_15_65_seed_email_routes.py' in reg


def test_migrate_local_project_docs_to_r2_is_registered():
    reg = Path('/app/docs/governance/DANGEROUS_SCRIPT_REGISTER.md').read_text(encoding='utf-8')
    assert 'migrate_local_project_docs_to_r2.py' in reg
