"""
test_trendline_integrity_probe.py — Phase V-Prelude · Wave 1.1B.

Adversarial coverage for the trendline integrity probe. Each test
constructs a synthetic trendline + snapshot pair in a tmp dir, points
the probe's `_check_one` at it, and asserts the expected violation
shape.

This is the safety net that protects the safety net.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _import_probe():
    spec = importlib.util.spec_from_file_location(
        "trendline_integrity_probe",
        "/app/scripts/trendline_integrity_probe.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def probe():
    return _import_probe()


def _make_spec(path: Path) -> dict:
    return {
        "name": "SYNTH",
        "path": path,
        "required_keys": ("iteration", "timestamp", "score", "aggregate"),
        "ts_key": "timestamp",
        "id_key": "iteration",
    }


def _seed(path: Path, entries) -> None:
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ── Happy path ───────────────────────────────────────────────────────


def test_clean_trendline_returns_no_violations(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-2", "timestamp": "2026-01-02T00:00:00.000Z",
         "score": 0.1, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert res["violations"] == [], res["violations"]
    assert res["summary"]["entry_count"] == 2
    assert res["snapshot"] is not None
    assert res["snapshot"]["newest_ts"] == "2026-01-02T00:00:00Z"


# ── 1. Shape regression ──────────────────────────────────────────────


def test_object_shape_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    p.write_text(json.dumps({"not": "a list"}))
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("shape regression" in v for v in res["violations"]), res


def test_null_root_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    p.write_text("null")
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("shape regression" in v for v in res["violations"]), res


def test_malformed_json_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    p.write_text("{ not valid")
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("malformed JSON" in v for v in res["violations"]), res


# ── 2. Missing required keys ─────────────────────────────────────────


def test_missing_required_key_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "x", "timestamp": "2026-01-01T00:00:00.000Z"},
    ])  # missing score + aggregate
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("missing required key" in v for v in res["violations"]), res


# ── 3. Timestamp doctrine ────────────────────────────────────────────


def test_non_z_timestamp_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "x", "timestamp": "2026-01-01T00:00:00.000+00:00",
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("not Z-suffixed" in v for v in res["violations"]), res


def test_naive_timestamp_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "x", "timestamp": "2026-01-01T00:00:00",
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("not Z-suffixed" in v for v in res["violations"]), res


def test_non_string_timestamp_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "x", "timestamp": 1234567890,
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("must be a string" in v for v in res["violations"]), res


# ── 4. Chronology order ──────────────────────────────────────────────


def test_chronology_violation_caught(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "a", "timestamp": "2026-02-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "b", "timestamp": "2026-01-01T00:00:00.000Z",  # OLDER
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("chronology violation" in v for v in res["violations"]), res


# ── 5. Duplicate deployment ──────────────────────────────────────────


def test_duplicate_iteration_timestamp_rejected(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "iter-x", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-x", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("duplicate" in v for v in res["violations"]), res


# ── 6. Snapshot continuity ───────────────────────────────────────────


def test_silent_overwrite_detected(probe, tmp_path):
    """Trendline that USED TO have 5 entries now has 3 — count
    dropped → violation."""
    p = tmp_path / "synth.json"
    snap_path = p.with_suffix(".snapshot.json")
    snap_path.write_text(json.dumps({
        "entry_count": 5,
        "checksum_prefix": "deadbeef",
        "newest_ts": "2026-05-01T00:00:00.000Z",
        "oldest_ts": "2026-01-01T00:00:00.000Z",
        "refreshed_at": "2026-05-28T00:00:00.000Z",
        "trendline": "SYNTH",
    }))
    _seed(p, [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-2", "timestamp": "2026-01-02T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-3", "timestamp": "2026-01-03T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=False)
    assert any("silent overwrite" in v for v in res["violations"]), res


def test_historical_mutation_detected(probe, tmp_path):
    """Build a 2-entry trendline, snapshot it, then MUTATE the FIRST
    entry. The prefix checksum should diverge."""
    p = tmp_path / "synth.json"
    original = [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-2", "timestamp": "2026-01-02T00:00:00.000Z",
         "score": 0.1, "aggregate": {}},
    ]
    _seed(p, original)
    # First run — captures snapshot.
    res = probe._check_one(_make_spec(p), refresh=False)
    assert res["snapshot"] is not None
    p.with_suffix(".snapshot.json").write_text(
        json.dumps(res["snapshot"], indent=2)
    )
    # Mutate entry[0].score AFTER the fact.
    mutated = json.loads(json.dumps(original))
    mutated[0]["score"] = 99.9
    _seed(p, mutated)
    res2 = probe._check_one(_make_spec(p), refresh=False)
    assert any("historical mutation" in v for v in res2["violations"]), res2


def test_snapshot_refreshes_on_clean_run(probe, tmp_path):
    p = tmp_path / "synth.json"
    _seed(p, [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
    ])
    res1 = probe._check_one(_make_spec(p), refresh=False)
    assert res1["snapshot"] is not None
    first_checksum = res1["snapshot"]["checksum_prefix"]

    # Add another entry → snapshot prefix-checksum changes since the
    # FULL file checksum is captured (not just the previous prefix).
    _seed(p, [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
        {"iteration": "iter-2", "timestamp": "2026-01-02T00:00:00.000Z",
         "score": 0.1, "aggregate": {}},
    ])
    res2 = probe._check_one(_make_spec(p), refresh=False)
    assert res2["violations"] == [], res2["violations"]
    assert res2["snapshot"]["entry_count"] == 2
    assert res2["snapshot"]["checksum_prefix"] != first_checksum


def test_snapshot_not_refreshed_when_violations_present(probe, tmp_path):
    """If a probe run found violations, the snapshot returned in the
    report should still be None (probe must not auto-rebaseline a
    corrupted file)."""
    p = tmp_path / "synth.json"
    p.write_text("{ malformed")
    res = probe._check_one(_make_spec(p), refresh=False)
    assert res["snapshot"] is None
    assert res["violations"]


def test_refresh_snapshot_flag_re_baselines_even_with_violations(probe, tmp_path):
    """--refresh-snapshot is the operator's explicit "yes I know this
    changed" affirmation. The probe captures the new baseline even if
    violations are present."""
    p = tmp_path / "synth.json"
    snap_path = p.with_suffix(".snapshot.json")
    snap_path.write_text(json.dumps({
        "entry_count": 5,
        "checksum_prefix": "stale",
        "newest_ts": "2026-04-01T00:00:00.000Z",
        "oldest_ts": "2026-01-01T00:00:00.000Z",
        "refreshed_at": "2026-04-01T00:00:00.000Z",
        "trendline": "SYNTH",
    }))
    _seed(p, [
        {"iteration": "iter-1", "timestamp": "2026-01-01T00:00:00.000Z",
         "score": 0.0, "aggregate": {}},
    ])
    res = probe._check_one(_make_spec(p), refresh=True)
    assert res["snapshot"] is not None
    assert res["snapshot"]["entry_count"] == 1


# ── 7. Live governance memory still clean ────────────────────────────


def test_live_trendlines_are_clean(probe):
    """Run the probe against the actual live trendline files. After
    Wave 1.1B init they MUST be clean."""
    rep = probe._run(refresh=False)
    assert rep["total_violations"] == 0, rep["results"]
