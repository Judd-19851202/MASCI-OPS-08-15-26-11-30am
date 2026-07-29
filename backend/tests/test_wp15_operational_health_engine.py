from lib.operational_health_engine import (
    aggregate_operational_status,
    build_status_engine_fixture_results,
    normalize_operational_status,
)


def test_normalize_operational_status_maps_expected_values():
    assert normalize_operational_status("amber") == "yellow"
    assert normalize_operational_status("VERIFIED") == "green"
    assert normalize_operational_status("MISMATCH") == "red"
    assert normalize_operational_status(None) == "unknown"


def test_aggregate_operational_status_prefers_highest_severity():
    assert aggregate_operational_status(["green", "green"]) == "green"
    assert aggregate_operational_status(["green", "unknown"]) == "unknown"
    assert aggregate_operational_status(["green", "yellow"]) == "yellow"
    assert aggregate_operational_status(["unknown", "yellow", "red"]) == "red"


def test_status_engine_fixtures_all_pass():
    fixtures = build_status_engine_fixture_results()
    assert fixtures
    assert all(fixture["pass"] for fixture in fixtures)