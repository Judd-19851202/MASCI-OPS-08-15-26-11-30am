from __future__ import annotations

from pathlib import Path

from lib.trust_spine import canonical_workflows_for_event, workflow_family


def test_daily_report_workflow_family_includes_oppc_compatibility_chain():
    assert workflow_family("daily-report") == ["daily-report", "oppc-daily-report-proof-chain"]


def test_oppc_daily_report_events_roll_up_to_canonical_daily_report_workflow():
    targets = canonical_workflows_for_event("oppc-daily-report-proof-chain")
    assert "oppc-daily-report-proof-chain" in targets
    assert "daily-report" in targets


def test_admin_trust_spine_and_production_certification_both_use_workflow_family():
    admin_src = Path('/app/backend/routes/admin_trust_spine.py').read_text(encoding='utf-8')
    prod_src = Path('/app/backend/lib/production_certification.py').read_text(encoding='utf-8')
    assert 'workflow_family' in admin_src
    assert 'canonical_workflows_for_event' in admin_src
    assert 'workflow_family' in prod_src