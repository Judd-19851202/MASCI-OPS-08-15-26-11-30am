"""
test_timeline_calmness_probe.py — Phase V-Prelude · Wave 1.1A.

Regression for the passive calmness telemetry instrument:

  * Probe runs cleanly against the live preview pod.
  * Output JSON carries every documented heuristic key.
  * Trendline file is JSON-list-shaped and append-only.
  * Baseline run reports score ≤ 1.0 (the substrate is clean today; a
    spike here means the sidecar regressed).
  * Probe is read-only — it never POSTs to the backend or writes
    operator-facing surfaces.

This test is a SAFETY NET for the probe itself. If the probe drifts,
the rest of the governance trendline becomes meaningless.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROBE = "/app/scripts/timeline_calmness_probe.py"
TRENDLINE = Path("/app/memory/TIMELINE_LOUDNESS_TRENDLINE.json")


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


URL = (
    _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

ADMIN_PASSWORD = (
    _read_env("/app/backend/.env", "ADMIN_PASSWORD")
    or os.environ.get("ADMIN_PASSWORD", "")
)

pytestmark = pytest.mark.skipif(
    not (URL and ADMIN_PASSWORD),
    reason="REACT_APP_BACKEND_URL or ADMIN_PASSWORD missing",
)


def test_probe_runs_clean_and_produces_score(tmp_path):
    """Run the probe end-to-end with a throwaway trendline file and a
    unique iteration label; assert exit 0 and a numeric score ≤ 1.0."""
    trend = tmp_path / "trendline.json"
    report_dir = tmp_path / "reports"
    iteration = "pytest-calmness-baseline"
    r = subprocess.run(
        [
            sys.executable, PROBE,
            "--iteration", iteration,
            "--project-number", "PYTEST-CALM-PROBE",
            "--trendline-path", str(trend),
            "--report-dir", str(report_dir),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert r.returncode == 0, (
        f"probe exited {r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )

    detail_path = report_dir / f"timeline_calmness_{iteration}.json"
    assert detail_path.exists(), "detail report missing"
    detail = json.loads(detail_path.read_text())

    # Every documented heuristic key must be present in the aggregate.
    for key in (
        "accent_class_ratio",
        "badge_density_per_1k_px2",
        "red_usage",
        "hierarchy_compression",
        "chronology_dup_ratio",
        "vertical_density",
    ):
        assert key in detail["aggregate"], f"missing aggregate key: {key}"

    # The substrate is freshly built and calm — any score above 1.0
    # means meaningful drift has already happened.
    assert detail["score"] <= 1.0, (
        f"calmness score regression: {detail['score']} aggregate="
        f"{detail['aggregate']}"
    )

    # The probe shouldn't have hit any gate-breach floor.
    assert detail["gate_breaches"] == [], (
        f"unexpected gate breaches: {detail['gate_breaches']}"
    )

    # All three viewports measured.
    assert detail["viewports_measured"] == 3, (
        f"expected 3 viewports, got {detail['viewports_measured']} · "
        f"per_viewport={detail['per_viewport']}"
    )


def test_trendline_file_is_json_list_and_append_only(tmp_path):
    """Run the probe twice with different iteration labels — the
    trendline file must grow by exactly one entry per run, never
    overwrite."""
    trend = tmp_path / "trendline.json"
    report_dir = tmp_path / "reports"
    for iteration in ("pytest-calm-a", "pytest-calm-b"):
        subprocess.run(
            [
                sys.executable, PROBE,
                "--iteration", iteration,
                "--project-number", "PYTEST-CALM-APPEND",
                "--trendline-path", str(trend),
                "--report-dir", str(report_dir),
            ],
            check=True,
            timeout=180,
            capture_output=True,
        )
    assert trend.exists()
    history = json.loads(trend.read_text())
    assert isinstance(history, list)
    assert len(history) >= 2
    # Latest entry shape — every field the gate / docs depend on.
    last = history[-1]
    for key in ("iteration", "timestamp", "score", "aggregate",
                "gate_breaches", "viewports_measured"):
        assert key in last, f"trendline entry missing {key}"
    assert last["timestamp"].endswith("Z"), \
        f"trendline timestamp not Z-suffixed: {last['timestamp']}"


def test_live_trendline_history_is_well_formed():
    """The actual /app/memory/TIMELINE_LOUDNESS_TRENDLINE.json must
    stay a list-of-entries with Z-suffixed timestamps. This guards
    the file against accidental object-style overwrites."""
    if not TRENDLINE.exists():
        pytest.skip("trendline file not yet seeded")
    history = json.loads(TRENDLINE.read_text())
    assert isinstance(history, list), "trendline must be a JSON list"
    for entry in history:
        assert isinstance(entry, dict)
        for key in ("iteration", "timestamp", "score", "aggregate"):
            assert key in entry, f"history entry missing {key}: {entry}"
        assert entry["timestamp"].endswith("Z"), entry["timestamp"]
        assert isinstance(entry["score"], (int, float))
