"""GD-0018 — canonical EXPIRING-RATE contract guard (Wave 5, KPI-EXPIRING-RATE).

Pins the ONE governed boundary/timezone/missing-date/rate semantics of lib.kpi_expiry so
scattered expiry consumers cannot silently diverge. Includes failure fixtures proving a
divergent boundary (treating "expires today" as expired, or missing as expiring) is detected.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("/app/backend")))
from lib.kpi_expiry import (  # noqa: E402
    expiry_days, expiry_status, expiry_bucket, classify_expiries, expiring_rate,
    STATUS_EXPIRED, STATUS_EXPIRING, STATUS_CURRENT, STATUS_MISSING,
)

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
def iso(days): return (NOW + timedelta(days=days)).date().isoformat()


# -------------------- boundary --------------------
def test_expired_is_strictly_past_today_is_not_expired():
    assert expiry_status(iso(-1), now=NOW) == STATUS_EXPIRED
    assert expiry_status(iso(0), now=NOW) == STATUS_EXPIRING     # expires today = still valid, expiring
    assert expiry_status(iso(1), now=NOW) == STATUS_EXPIRING
    assert expiry_days(iso(0), now=NOW) == 0


def test_horizon_end_is_inclusive():
    assert expiry_status(iso(30), horizon_days=30, now=NOW) == STATUS_EXPIRING   # 30 inclusive
    assert expiry_status(iso(31), horizon_days=30, now=NOW) == STATUS_CURRENT
    assert expiry_status(iso(200), horizon_days=30, now=NOW) == STATUS_CURRENT


def test_missing_is_its_own_bucket_never_expiring_or_current():
    assert expiry_status(None, now=NOW) == STATUS_MISSING
    assert expiry_status("", now=NOW) == STATUS_MISSING
    assert expiry_status("garbage", now=NOW) == STATUS_MISSING
    assert expiry_days(None, now=NOW) is None
    assert expiry_bucket(None, now=NOW) == "MISSING"


# -------------------- timezone / parsing --------------------
def test_timestamp_and_iso_string_agree_via_utc():
    assert expiry_days("2026-06-20", now=NOW) == 5
    assert expiry_days("2026-06-20T23:59:59Z", now=NOW) == 5
    assert expiry_days(datetime(2026, 6, 20, 1, 0, tzinfo=timezone.utc), now=NOW) == 5


# -------------------- buckets --------------------
def test_finest_bucket_selection():
    assert expiry_bucket(iso(-2), now=NOW) == "EXPIRED"
    assert expiry_bucket(iso(5), horizons=(7, 30, 60, 90), now=NOW) == "EXPIRING_7"
    assert expiry_bucket(iso(20), horizons=(7, 30, 60, 90), now=NOW) == "EXPIRING_30"
    assert expiry_bucket(iso(120), horizons=(7, 30, 60, 90), now=NOW) == "CURRENT"


def test_classify_population_counts_are_cumulative_and_exclude_missing():
    dates = [iso(-3), iso(0), iso(5), iso(20), iso(45), iso(200), None, "bad"]
    c = classify_expiries(dates, horizons=(7, 30, 60), now=NOW)
    assert c["total"] == 8
    assert c["missing"] == 2
    assert c["eligible_total"] == 6              # missing excluded
    assert c["expired"] == 1                     # iso(-3)
    assert c["expiring_7d"] == 2                 # iso(0), iso(5)
    assert c["expiring_30d"] == 3                # <=30: iso(0),iso(5),iso(20)  (cumulative)
    assert c["expiring_60d"] == 4                # <=60: + iso(45)
    assert c["current"] == 1                     # iso(200)


# -------------------- rate semantics --------------------
def test_expiring_rate_modes_differ_and_require_explicit_mode():
    dates = [iso(-10), iso(-5), iso(10), iso(200), None]   # 2 expired, 1 expiring(<=30), 1 current, 1 missing
    eligible = 4                                            # missing excluded
    soon = expiring_rate(dates, mode="expiring_soon", horizon_days=30, now=NOW)
    at_risk = expiring_rate(dates, mode="at_risk", horizon_days=30, now=NOW)
    assert soon == round(100 * 1 / eligible, 1)            # 25.0
    assert at_risk == round(100 * (1 + 2) / eligible, 1)   # 75.0
    assert soon != at_risk
    with pytest.raises(ValueError):
        expiring_rate(dates, mode="whatever", now=NOW)


def test_empty_eligible_rate_is_unknown_not_zero():
    assert expiring_rate([None, "", "bad"], mode="at_risk", now=NOW) is None
    assert expiring_rate([], mode="expiring_soon", now=NOW) is None


# -------------------- failure fixtures (divergent boundary detected) --------------------
def test_divergent_boundary_treating_today_as_expired_is_detected():
    canonical = expiry_status(iso(0), now=NOW)          # Expiring Soon (today still valid)
    divergent = STATUS_EXPIRED if 0 < 0 else (           # a buggy `days <= 0 -> expired` rule
        STATUS_EXPIRED if 0 <= 0 else STATUS_EXPIRING)
    assert canonical == STATUS_EXPIRING
    assert canonical != divergent                        # buggy rule would mislabel today as expired


def test_divergent_missing_treated_as_expiring_is_detected():
    canonical = classify_expiries([None, None, iso(10)], horizons=(30,), now=NOW)
    assert canonical["expiring_30d"] == 1                # only the real date
    assert canonical["missing"] == 2
    # a divergent rule that counted missing as expiring would report 3 — caught here.
