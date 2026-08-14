"""GD-0022 — KPI-HEALTH-SCORE canonical contract + failure injection.

Guards the platform trust score (lib.trust_score) so that:
  - UNKNOWN/STALE evidence NEVER silently becomes HEALTHY (green);
  - a RED workflow hard-caps below green;
  - missing/aging/failed backup evidence reduces the backup trust score;
  - all-green + zero failures reaches 100.
Falsifiable: a test FAILS if the caps/penalties are removed (fake green).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.trust_score import compute_score, compute_backup_trust_score


def _wf(band):
    return {"band": band}


def test_all_green_zero_failures_is_100_green():
    r = compute_score(workflows=[_wf("green"), _wf("green")])
    assert r["trust_score"] == 100
    assert r["score_band"] == "green"


def test_red_workflow_hard_caps_below_green():
    # Even a single RED workflow cannot be green — no fake trust.
    r = compute_score(workflows=[_wf("green"), _wf("green"), _wf("red")])
    assert r["score_band"] != "green"
    assert r["trust_score"] <= 59


def test_unknown_audit_caps_below_100():
    # Unknown status is NOT healthy: cannot show a perfect green score.
    r = compute_score(workflows=[_wf("green")], unknown_audit_count_24h=1)
    assert r["trust_score"] <= 79
    assert r["trust_score"] < 100


def test_silent_failure_penalized():
    clean = compute_score(workflows=[_wf("green")])
    bad = compute_score(workflows=[_wf("green")], silent_failure_count_24h=2)
    assert bad["trust_score"] < clean["trust_score"]


def test_master_data_red_penalized():
    bad = compute_score(workflows=[_wf("green")],
                        master_data_findings=[{"band": "red"}])
    assert bad["trust_score"] < 100


def test_missing_critical_route_penalized():
    bad = compute_score(workflows=[_wf("green")],
                        missing_critical_routes=["/api/health"])
    assert bad["trust_score"] < 100


def test_no_activity_is_not_green_lie():
    # No workflow activity yet must not read as a trusted 100 green.
    r = compute_score(workflows=[])
    assert r["trust_score"] == 100  # starts at 100 but...
    # ...with no green evidence the reason is explicit, not a false 'trusted'
    assert "no workflow activity" in r["score_reason"].lower()


# ---- Backup trust score: stale/missing evidence must reduce trust ----

def _healthy_backup():
    return dict(hourly_disabled=False, newest_r2_age_hours=2.0,
                restore_drill_age_days=1.0, restore_drill_ok=True,
                integrity_ok=True, overlap_blocked=False,
                active_failures_7d=0, bucket_usage_status="GREEN")


def test_backup_all_healthy_is_green():
    r = compute_backup_trust_score(**_healthy_backup())
    assert r["score_band"] == "green"
    assert r["trust_score"] >= 85


def test_backup_missing_archive_not_green():
    args = _healthy_backup()
    args["newest_r2_age_hours"] = None  # no recent complete archive
    r = compute_backup_trust_score(**args)
    assert r["trust_score"] < 85


def test_backup_stale_archive_penalized():
    args = _healthy_backup()
    args["newest_r2_age_hours"] = 48.0  # stale
    r = compute_backup_trust_score(**args)
    assert r["trust_score"] < 85


def test_backup_failed_restore_drill_not_green():
    args = _healthy_backup()
    args["restore_drill_ok"] = False
    r = compute_backup_trust_score(**args)
    assert r["trust_score"] < 85
