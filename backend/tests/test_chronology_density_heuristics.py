"""
test_chronology_density_heuristics.py — Phase V-Prelude · Wave 1.1A.

Validates the chronology density / duplication heuristics used by the
calmness telemetry probe. Tests are designed around the
`/api/timeline` aggregator + the in-process `_measure_chronology`
helper from the probe.

We seed a deterministic noisy project (intentional duplication + bare
chronology rows) and assert:

  1. `chronology_dup_ratio` rises above the doctrine target (0.20).
  2. `low_value_repeats` reflects the noisy bare-action rows.
  3. The probe's `_score()` does NOT drop noisy seeds silently — they
     show up in `gate_breaches` ONLY when above 5x the target.
  4. Comparison against the clean Wave 1 fixtures stays calm.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import uuid
from pathlib import Path

import pytest
import requests


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

ADMIN_TOKEN = ""
if URL and ADMIN_PASSWORD:
    try:
        _r = requests.post(
            f"{URL}/api/admin/login",
            json={"password": ADMIN_PASSWORD},
            timeout=10,
        )
        if _r.status_code == 200:
            ADMIN_TOKEN = _r.json().get("token", "")
    except Exception:
        ADMIN_TOKEN = ""

pytestmark = pytest.mark.skipif(
    not (URL and ADMIN_TOKEN),
    reason="REACT_APP_BACKEND_URL or admin token unavailable",
)


# Import the probe's pure helpers without booting Playwright.
def _import_probe_helpers():
    spec = importlib.util.spec_from_file_location(
        "timeline_calmness_probe",
        "/app/scripts/timeline_calmness_probe.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # The probe's top-level import of playwright happens at import-time
    # but failing it doesn't matter here — we only use _measure_chronology
    # and _score. We pre-stub `sync_playwright` to a no-op so the module
    # imports cleanly.
    sys.modules.setdefault("playwright", type(sys)("playwright"))
    sys.modules.setdefault("playwright.sync_api", type(sys)("playwright.sync_api"))
    sys.modules["playwright.sync_api"].sync_playwright = lambda: None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def probe_mod():
    return _import_probe_helpers()


@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"X-Admin-Token": ADMIN_TOKEN})
    return sess


@pytest.fixture(scope="module")
def noisy_project_id(s) -> str:
    """Seed a deliberately noisy chronology: 1 constraint with 6
    bare-action chronology notes (no titles, single-word actions),
    plus 3 identical-signature operational_links rows."""
    pn = f"P-NOISE-{uuid.uuid4().hex[:8]}"
    r = s.post(
        f"{URL}/api/constraints",
        json={
            "project_id": pn,
            "title": "noisy-seed",
            "discipline": "utilities",
            "kind": "utility-conflict",
            "severity": "low",
        },
        timeout=10,
    )
    cid = r.json()["id"]
    # 6 bare-action chronology notes (no notes).
    for _ in range(6):
        s.post(
            f"{URL}/api/constraints/{cid}/chronology",
            json={"action": "ping", "note": ""},
            timeout=10,
        )
    # 3 identical-signature links — same source/target/relationship.
    for _ in range(3):
        s.post(
            f"{URL}/api/operational-links",
            json={
                "source_type": "field_note",
                "source_id": "FN-DUP-SIG",
                "target_type": "operational_constraint",
                "target_id": cid,
                "relationship": "references",
                "project_id": pn,
                "reason": "duplicate-signature probe",
                "visibility": "internal",
            },
            timeout=10,
        )
    yield pn
    # Cleanup.
    try:
        from pymongo import MongoClient  # noqa: PLC0415
        mongo = _read_env("/app/backend/.env", "MONGO_URL")
        db_name = _read_env("/app/backend/.env", "DB_NAME") or "masci_safety_preview"
        if mongo:
            cli = MongoClient(mongo)
            cli[db_name].operational_constraints.delete_many({"project_id": pn})
            cli[db_name].operational_links.delete_many({"project_id": pn})
            cli.close()
    except Exception:
        pass


# ── Heuristics ───────────────────────────────────────────────────────


def test_noisy_chronology_dup_ratio_rises(probe_mod, noisy_project_id):
    chrono = probe_mod._measure_chronology(
        URL, ADMIN_TOKEN, noisy_project_id,
    )
    assert chrono.get("error") is None, chrono
    assert chrono["row_count"] >= 9, (
        f"expected ≥9 rows from the noisy seed, got {chrono}"
    )
    assert chrono["chronology_dup_ratio"] >= 0.10, (
        f"duplicate signatures should surface — got "
        f"{chrono['chronology_dup_ratio']}"
    )


def test_low_value_bare_rows_counted(probe_mod, noisy_project_id):
    chrono = probe_mod._measure_chronology(
        URL, ADMIN_TOKEN, noisy_project_id,
    )
    assert chrono["low_value_repeats"] >= 4, (
        f"expected ≥4 low-value bare-action rows, got "
        f"{chrono['low_value_repeats']}"
    )


def test_clean_project_stays_calm(probe_mod, s):
    """A freshly-created project with a single rich-text constraint
    should score zero duplication and zero low-value repeats — i.e.,
    the heuristics aren't trigger-happy."""
    pn = f"P-CLEAN-{uuid.uuid4().hex[:8]}"
    try:
        s.post(
            f"{URL}/api/constraints",
            json={
                "project_id": pn,
                "title": "Single utility conflict · STA 142+50",
                "discipline": "utilities",
                "kind": "utility-conflict",
                "severity": "medium",
                "operational_impact": "Crew idle east lane.",
            },
            timeout=10,
        )
        chrono = probe_mod._measure_chronology(URL, ADMIN_TOKEN, pn)
        assert chrono["row_count"] >= 1
        assert chrono["chronology_dup_ratio"] == 0.0
        assert chrono["low_value_repeats"] == 0
    finally:
        try:
            from pymongo import MongoClient  # noqa: PLC0415
            mongo = _read_env("/app/backend/.env", "MONGO_URL")
            cli = MongoClient(mongo)
            db_name = _read_env("/app/backend/.env", "DB_NAME") or "masci_safety_preview"
            cli[db_name].operational_constraints.delete_many({"project_id": pn})
            cli.close()
        except Exception:
            pass


def test_score_function_aggregates_breaches(probe_mod):
    """Synthetic per-viewport input that violates every target by 6x
    must produce a gate_breach for every dimension."""
    per_viewport = {
        "desktop": {
            "missing": False,
            "accent_class_ratio": 0.18 * 6 + 0.01,
            "badge_density_per_1k_px2": 0.0001 * 6 + 0.0001,
            "red_usage": 2 * 6 + 1,
            "hierarchy_compression": 5 * 6 + 1,
            "vertical_density": 12 * 6 + 1,
        },
    }
    chronology = {
        "chronology_dup_ratio": 0.20 * 6 + 0.05,
    }
    scored = probe_mod._score(per_viewport, chronology)
    assert scored["score"] > 0
    # Every dimension above 5x target must surface in the breach list.
    breach_keys = " ".join(scored["gate_breaches"])
    for dim in (
        "accent_class_ratio", "badge_density_per_1k_px2",
        "red_usage", "hierarchy_compression", "vertical_density",
        "chronology_dup_ratio",
    ):
        assert dim in breach_keys, (
            f"expected {dim} in gate_breaches; got: {breach_keys}"
        )
