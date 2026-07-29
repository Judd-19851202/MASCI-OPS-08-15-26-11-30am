from lib.operational_health_engine import GOLDEN_PATH_MONITORS, classify_golden_path_signal


def test_golden_path_registry_covers_required_representative_workflows():
    expected = {
        "admin",
        "pm",
        "safety",
        "dispatch",
        "shop",
        "hr",
        "executive",
        "daily-reports",
        "equipment",
        "job-photos",
        "upload",
        "download",
        "export",
    }
    actual = {row["workflow_id"] for row in GOLDEN_PATH_MONITORS}
    assert actual == expected


def test_golden_path_signal_is_unknown_without_current_run():
    assert classify_golden_path_signal("red", has_current_run=False) == "unknown"


def test_golden_path_signal_uses_trust_band_when_current_run_exists():
    assert classify_golden_path_signal("green", has_current_run=True) == "green"
    assert classify_golden_path_signal("amber", has_current_run=True) == "yellow"
    assert classify_golden_path_signal("red", has_current_run=True) == "red"