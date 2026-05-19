"""iter251 · Severity Table v1-approved-2026-05-19 · operator rulings.

Pins the 9 operator rulings into pytest so future agents can't silently
re-introduce the uncertain items or unwind the split-item logic.

Each ruling is encoded as: the OOS line is OOS · the Monitor counterpart
(where applicable) is Monitor · the old vague wording is gone.

Pure-function tests · no live HTTP · runs fast in regression.
"""
from __future__ import annotations
import pytest

import fleet_defect_severity as _sev


def test_severity_table_version_is_v1_approved():
    assert _sev.SEVERITY_TABLE_VERSION == "v1-approved-2026-05-19"
    assert _sev.SEVERITY_TABLE_APPROVAL["uncertainty_resolved"] is True
    assert _sev.SEVERITY_TABLE_APPROVAL["rulings_count"] == 9


def test_no_uncertain_items_remain():
    """All 9 operator rulings cleared uncertain flags · governance gate."""
    uncertain = [item for item, meta in _sev.FLEET_DEFECT_SEVERITY_META.items()
                 if meta.get("uncertain")]
    assert uncertain == [], (
        f"v1-approved must have zero uncertain items · found: {uncertain}"
    )


# ─── Ruling #1 · Power steering · split by drip rate ────────────────
def test_ruling_1_power_steering_split():
    oos_item = "Power steering — fluid AT or ABOVE MIN · normal effort · no active drip"
    monitor_item = "Power steering — stable seep / weep · normal effort · fluid AT MIN or above"
    assert _sev.classify(oos_item) == ("oos", "steering")
    assert _sev.classify(monitor_item) == ("monitor", "steering")
    # old vague wording must be gone
    assert "Power steering — no leaks · fluid at proper level · normal effort" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #2 · Headlights · day/night tier ────────────────────────
def test_ruling_2_headlights_high_beam_tier():
    strict = "Headlights — both low-beams functional · at least one high-beam functional"
    tier = "Headlights — single high-beam out · both low-beams functional · daylight-only ops"
    assert _sev.classify(strict) == ("oos", "lights")
    assert _sev.classify(tier) == ("monitor", "lights")
    assert "Headlights — high beam · both sides functional" \
        not in _sev.FLEET_DEFECT_SEVERITY
    # Low-beam line must remain strict OOS
    assert _sev.classify("Headlights — low beam · both sides functional") \
        == ("oos", "lights")


# ─── Ruling #3 · Strobes / beacons · work-zone upgrade ──────────────
def test_ruling_3_strobes_work_zone_oos():
    work_zone = "Strobes / beacons — all flash patterns operational (work-zone / lane closure / paving / shoulder / airport ops)"
    yard_only = "Strobes / beacons — partial pattern acceptable for yard-only / shop-shuffle moves"
    total_loss = "Strobes / beacons — at least one operational"
    assert _sev.classify(work_zone) == ("oos", "signals")
    assert _sev.classify(yard_only) == ("monitor", "signals")
    assert _sev.classify(total_loss) == ("oos", "signals")
    # old vague monitor-line is gone
    assert "Strobes / beacons — all flash patterns operational" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #4 · Wipers · driver-strict + passenger-conditional ─────
def test_ruling_4_wipers_split():
    driver = "Driver-side wiper — sweeps cleanly · no streaking · no torn blade"
    pass_rain = "Passenger-side wiper — sweeps cleanly when rain forecast in shift window"
    pass_dry = "Passenger-side wiper — minor streak acceptable · dry forecast in shift window · 3-day shop window"
    assert _sev.classify(driver) == ("oos", "wipers")
    assert _sev.classify(pass_rain) == ("oos", "wipers")
    assert _sev.classify(pass_dry) == ("monitor", "wipers")
    assert "Wipers — both blades sweep windshield cleanly · no streaking" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #5 · Body · 5-test objective rubric ─────────────────────
def test_ruling_5_body_objective_rubric():
    rubric = (
        "Body — no frame/cab-mount fracture · no projecting metal or sharp edge · "
        "no loose panel/door · no rust-through on cab floor or fuel tank · "
        "no damage blocking mirror or windshield visibility"
    )
    cosmetic = "Body — cosmetic dings · scrapes · paint"
    assert _sev.classify(rubric) == ("oos", "body")
    assert _sev.classify(cosmetic) == ("monitor", "body")
    # The 4 must-haves should be in the wording (rust-through is the 5th)
    for must_have in ("frame/cab-mount fracture", "projecting metal",
                      "loose panel", "rust-through", "blocking mirror or windshield"):
        assert must_have in rubric, f"rubric missing {must_have!r}"
    assert "Body — no severe damage affecting safe operation" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #6 · Hydraulic · drip-rate + circuit tier ───────────────
def test_ruling_6_hydraulic_tier():
    oos_h = "Hydraulic system — no active drip · no leak below MIN reservoir · no leak on bed-lift / boom / outrigger / brake-assist circuit"
    monitor_h = "Hydraulic system — stable seep / film without active drip · reservoir AT or ABOVE MIN · not on load-supporting circuit"
    assert _sev.classify(oos_h) == ("oos", "hydraulic")
    assert _sev.classify(monitor_h) == ("monitor", "hydraulic")
    # the load-supporting-circuit emphasis must be present in OOS line
    assert "bed-lift" in oos_h and "outrigger" in oos_h and "brake-assist" in oos_h
    assert "Hydraulic system — no visible leaks" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #7 · Defroster conditional · heater visibility-tier ─────
def test_ruling_7_defroster_visibility():
    defroster = "Defroster — functional when ambient ≤ 40°F or precipitation forecast in shift window"
    heater = "Cab heater — functional · escalates to OOS if window fogging affects visibility"
    assert _sev.classify(defroster) == ("oos", "interior")
    assert _sev.classify(heater) == ("monitor", "interior")
    assert "Cab — heater / defroster operational (cold/wet weather)" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #8 · Dash gauges · ECM-aware tier ───────────────────────
def test_ruling_8_dash_gauges_ecm_aware():
    strict = "Oil pressure & coolant temp gauges OR equivalent ECM warning system functional"
    fuel = "Fuel gauge — functional · driver may estimate by miles · 7-day shop window"
    ecm_tier = "Dash gauges (oil / temp) inop on units with ECM check-engine + fault display fully functional · 14-day shop window"
    assert _sev.classify(strict) == ("oos", "interior")
    assert _sev.classify(fuel) == ("monitor", "interior")
    assert _sev.classify(ecm_tier) == ("monitor", "interior")
    assert "Cab — dash gauges functional (oil pressure · temp · fuel)" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Ruling #9 · Tarp · 6"x6" + load-haul scope split ───────────────
def test_ruling_9_tarp_load_haul_split():
    oos_t = ("Tarp system — deploys + retracts · no tear > 6\"×6\" · "
             "functional on units assigned to aggregate / asphalt / "
             "dust-producing load haul")
    monitor_t = ("Tarp system — minor tear < 6\"×6\" OR unit assigned to "
                 "empty / equipment / non-dust haul · 5-day shop window")
    assert _sev.classify(oos_t) == ("oos", "tarp")
    assert _sev.classify(monitor_t) == ("monitor", "tarp")
    assert "Tarp system — deploys + retracts · no major tears" \
        not in _sev.FLEET_DEFECT_SEVERITY


# ─── Table-wide health checks after rulings ─────────────────────────
def test_table_size_grew_by_split_items():
    """9 vague items → 19 precise items · net +10 entries."""
    assert len(_sev.FLEET_DEFECT_SEVERITY) == 107
    assert len(_sev.FLEET_DEFECT_SEVERITY_META) == 107


def test_oos_monitor_ratio_still_conservative():
    """Even after adding 9 Monitor-tier items, ratio stays ≥ 2.0."""
    oos = sum(1 for s, _ in _sev.FLEET_DEFECT_SEVERITY.values() if s == "oos")
    mon = sum(1 for s, _ in _sev.FLEET_DEFECT_SEVERITY.values() if s == "monitor")
    ratio = oos / mon
    assert ratio >= 2.0, f"conservative bias violated · ratio = {ratio}"


def test_checklist_items_all_classify():
    """Every item emitted by every checklist function must classify."""
    import checklists_fleet as _ck
    for fn in (_ck.dvir_truck_items, _ck.dvir_trailer_items,
               _ck.dvir_emergency_items, _ck.dvir_weekly_lead_items):
        for item in fn():
            try:
                _sev.classify(item)
            except KeyError:
                pytest.fail(
                    f"checklist {fn.__name__} emits {item!r} but it has no "
                    f"severity entry · would HTTP 400 in production"
                )


# ─── Realistic field scenarios · v1-approved tier behaviour ─────────

def test_scenario_minor_power_steering_weep_is_monitor():
    """Operator philosophy: stable weep + normal effort = honest reporting · Monitor."""
    sev, cat = _sev.classify(
        "Power steering — stable seep / weep · normal effort · fluid AT MIN or above"
    )
    assert sev == "monitor"


def test_scenario_active_hydraulic_drip_is_oos():
    """Operator philosophy: active drip on load circuit = real risk · OOS."""
    sev, cat = _sev.classify(
        "Hydraulic system — no active drip · no leak below MIN reservoir · "
        "no leak on bed-lift / boom / outrigger / brake-assist circuit"
    )
    assert sev == "oos"


def test_scenario_modern_truck_inop_gauge_is_monitor():
    """Operator philosophy: ECM-equipped truck with fault display = supplementary gauges · Monitor."""
    sev, cat = _sev.classify(
        "Dash gauges (oil / temp) inop on units with ECM check-engine + "
        "fault display fully functional · 14-day shop window"
    )
    assert sev == "monitor"


def test_scenario_strobes_partial_work_zone_is_oos():
    """Operator philosophy: work-zone struck-by control · partial pattern in work zone = OOS."""
    sev, cat = _sev.classify(
        "Strobes / beacons — all flash patterns operational "
        "(work-zone / lane closure / paving / shoulder / airport ops)"
    )
    assert sev == "oos"


def test_scenario_passenger_wiper_dry_forecast_is_monitor():
    """Operator philosophy: dry forecast + minor streak passenger-side = Monitor."""
    sev, cat = _sev.classify(
        "Passenger-side wiper — minor streak acceptable · dry forecast "
        "in shift window · 3-day shop window"
    )
    assert sev == "monitor"


def test_scenario_tarp_empty_backhaul_is_monitor():
    """Operator philosophy: empty / non-dust haul + minor tarp tear = Monitor."""
    sev, cat = _sev.classify(
        "Tarp system — minor tear < 6\"×6\" OR unit assigned to "
        "empty / equipment / non-dust haul · 5-day shop window"
    )
    assert sev == "monitor"
