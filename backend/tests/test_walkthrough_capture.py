"""
test_walkthrough_capture.py — Phase V-Prelude · Observation Ledger.

Microscopic regression for the walkthrough capture script + the
ledger integration with the integrity probe.

Tests:
  * valid append shape
  * invalid scenario rejection
  * Z-suffix enforcement on the appended timestamp
  * JSON-list preservation
  * duplicate (timestamp, scenario, reviewer) rejection
  * malformed ledger rejection
  * empty/missing answer keys handled safely
  * integrity probe accepts the live ledger (clean)
  * integrity probe rejects a corrupted ledger
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest


CAPTURE_PATH = "/app/scripts/walkthrough_capture.py"
PROBE_PATH = "/app/scripts/trendline_integrity_probe.py"

Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def _import(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cap():
    return _import(CAPTURE_PATH, "walkthrough_capture")


@pytest.fixture(scope="module")
def probe():
    return _import(PROBE_PATH, "trendline_integrity_probe")


@pytest.fixture
def tmp_ledger(tmp_path):
    p = tmp_path / "OBSERVATION_LEDGER.json"
    p.write_text("[]\n")
    return p


# ── build_entry ──────────────────────────────────────────────────────


def _ans(extra=None):
    base = {
        "worked": "sidecar loaded instantly on mobile",
        "friction": "none",
        "chronology_helped": "yes",
        "would_help_real_ops": "yes",
    }
    if extra:
        base.update(extra)
    return base


def test_build_entry_valid(cap):
    entry = cap.build_entry(
        scenario="utility-conflict",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed=False,
    )
    for key in ("timestamp", "scenario", "reviewer", "answers",
                "freeze_trigger_observed", "notes"):
        assert key in entry
    assert Z_RE.match(entry["timestamp"]), entry["timestamp"]
    assert entry["scenario"] == "utility-conflict"
    assert entry["reviewer"] == "JJ"
    assert set(entry["answers"].keys()) == {
        "worked", "friction", "chronology_helped", "would_help_real_ops",
    }


def test_build_entry_invalid_scenario_rejected(cap):
    with pytest.raises(ValueError, match="invalid scenario"):
        cap.build_entry(
            scenario="wave-2-please",  # not in the closed enum
            reviewer="JJ",
            answers=_ans(),
            freeze_trigger_observed=False,
        )


def test_build_entry_requires_reviewer(cap):
    with pytest.raises(ValueError, match="reviewer is required"):
        cap.build_entry(
            scenario="utility-conflict",
            reviewer="",
            answers=_ans(),
            freeze_trigger_observed=False,
        )


def test_build_entry_requires_all_four_answers(cap):
    with pytest.raises(ValueError, match="missing answer for"):
        cap.build_entry(
            scenario="utility-conflict",
            reviewer="JJ",
            answers={"worked": "x"},  # missing 3 others
            freeze_trigger_observed=False,
        )


def test_build_entry_truncates_long_answers(cap):
    long = "x" * 2000
    entry = cap.build_entry(
        scenario="utility-conflict",
        reviewer="JJ",
        answers=_ans({"worked": long}),
        freeze_trigger_observed=False,
    )
    assert len(entry["answers"]["worked"]) == 500  # MAX_ANSWER_LEN


def test_build_entry_freeze_trigger_coerced_to_bool(cap):
    entry = cap.build_entry(
        scenario="utility-conflict",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed="truthy",  # type: ignore[arg-type]
    )
    assert entry["freeze_trigger_observed"] is True


# ── append_entry ─────────────────────────────────────────────────────


def test_append_preserves_json_list_shape(cap, tmp_ledger):
    entry = cap.build_entry(
        scenario="utility-conflict",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed=False,
    )
    cap.append_entry(entry, ledger_path=tmp_ledger)
    data = json.loads(tmp_ledger.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["scenario"] == "utility-conflict"


def test_append_rejects_duplicate_tuple(cap, tmp_ledger):
    entry = cap.build_entry(
        scenario="FAA-delay",
        reviewer="CW",
        answers=_ans(),
        freeze_trigger_observed=False,
        timestamp="2026-05-28T10:00:00.000Z",
    )
    cap.append_entry(entry, ledger_path=tmp_ledger)
    # Same (timestamp, scenario, reviewer) — must be rejected.
    with pytest.raises(SystemExit, match="duplicate"):
        cap.append_entry(entry, ledger_path=tmp_ledger)
    # Different reviewer with same timestamp+scenario — allowed.
    entry2 = cap.build_entry(
        scenario="FAA-delay",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed=False,
        timestamp="2026-05-28T10:00:00.000Z",
    )
    cap.append_entry(entry2, ledger_path=tmp_ledger)
    assert len(json.loads(tmp_ledger.read_text())) == 2


def test_append_rejects_object_shaped_ledger(cap, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "a list"}')
    entry = cap.build_entry(
        scenario="utility-conflict",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed=False,
    )
    with pytest.raises(SystemExit, match="not a JSON list"):
        cap.append_entry(entry, ledger_path=bad)


def test_append_creates_ledger_if_missing(cap, tmp_path):
    missing = tmp_path / "fresh.json"
    assert not missing.exists()
    entry = cap.build_entry(
        scenario="QC-failure",
        reviewer="JJ",
        answers=_ans(),
        freeze_trigger_observed=False,
    )
    cap.append_entry(entry, ledger_path=missing)
    assert missing.exists()
    assert json.loads(missing.read_text()) == [entry]


# ── Integration with trendline_integrity_probe ───────────────────────


def test_integrity_probe_accepts_live_ledger(probe):
    """The actual /app/memory/OBSERVATION_LEDGER.json must pass the
    probe (it's part of the standard inventory now)."""
    rep = probe._run(refresh=False)
    # find the OBSERVATION_LEDGER result
    led = next(
        r for r in rep["results"] if r["name"] == "OBSERVATION_LEDGER"
    )
    assert led["violations"] == [], led["violations"]


def test_integrity_probe_rejects_ledger_with_non_z_timestamp(probe, tmp_path):
    """Synthetic ledger with `+00:00` timestamp must trip the probe."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{
        "timestamp": "2026-05-28T10:00:00.000+00:00",
        "scenario": "utility-conflict",
        "reviewer": "JJ",
        "answers": {
            "worked": "x", "friction": "y",
            "chronology_helped": "z", "would_help_real_ops": "w",
        },
        "freeze_trigger_observed": False,
    }]))
    spec = {
        "name": "TEST",
        "path": bad,
        "required_keys": (
            "timestamp", "scenario", "reviewer",
            "answers", "freeze_trigger_observed",
        ),
        "ts_key": "timestamp",
        "id_key": "_dedup_composite",
    }
    res = probe._check_one(spec, refresh=False)
    assert any("not Z-suffixed" in v for v in res["violations"]), res


def test_integrity_probe_rejects_ledger_duplicate_composite(probe, tmp_path):
    """Two entries with identical (timestamp, scenario, reviewer) trip
    the composite-key duplicate check."""
    bad = tmp_path / "bad.json"
    dup = {
        "timestamp": "2026-05-28T10:00:00.000Z",
        "scenario": "utility-conflict",
        "reviewer": "JJ",
        "answers": {
            "worked": "x", "friction": "y",
            "chronology_helped": "z", "would_help_real_ops": "w",
        },
        "freeze_trigger_observed": False,
    }
    bad.write_text(json.dumps([dup, dup]))
    spec = {
        "name": "TEST",
        "path": bad,
        "required_keys": tuple(dup.keys()),
        "ts_key": "timestamp",
        "id_key": "_dedup_composite",
    }
    res = probe._check_one(spec, refresh=False)
    assert any("duplicate" in v for v in res["violations"]), res
