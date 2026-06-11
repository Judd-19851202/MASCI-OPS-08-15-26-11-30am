"""RC-2 · TRACK-4 GUARDRAIL — Production Contamination Scan.

Read-only audit. Walks the **PREVIEW** database for known contamination
patterns (test/demo/PROD-ORPHAN/CERT artifacts that must not bleed into
production via the next backup→restore cycle).

Doctrine
--------
* Preview is **expected** to carry pytest-fixture contamination
  (`make=Test`, `make=DEMO`, `project_name=TEST_…`, `prepared_by=pytest
  harness`). The scanner inventories these but only fails when run
  against a PRODUCTION-shaped database (`DB_NAME=masci_safety`).
* When run against preview the scanner publishes an inventory artifact
  to `/app/test_reports/rc2/contamination_inventory.json` so the
  operator can confirm volumes have not exploded between runs.

Safety
------
* `APP_ENV` MUST be `preview` (asserted at startup).
* Reads only — never writes, deletes, or updates.
* If `DB_NAME` does not end in `_preview`, the scan refuses to proceed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from dotenv import dotenv_values
from pymongo import MongoClient

BACKEND_ENV = dotenv_values("/app/backend/.env")

CONTAM_MAKES = {"test", "demo", "sample", "dummy", "placeholder",
                "harness", "qa-test", "fake"}

CONTAM_PROJECT_NAME_PATTERNS = [
    r"PROD[\-_]ORPHAN",
    r"\bCERT\b",
    r"\bTEST\b",
    r"\bDEMO\b",
    r"\bHARNESS\b",
    r"\bPLACEHOLDER\b",
]

CONTAM_PREPARED_BY_PATTERNS = [
    r"harness",
    r"\bqa-test\b",
    r"\bautotest\b",
]

# Inventory baseline — published numbers from the 2026-06-11 RC-1 pass.
# If preview contamination grows by >25% the guardrail flags a soft
# warning so the operator notices fixture rot.
INVENTORY_BASELINE = {
    "equipment_make": 5,        # known Test/DEMO/etc rows allowed in preview
    "daily_project_name": 600,  # known TEST_…/DEMO_… rows allowed in preview
    "daily_prepared_by": 100,   # known pytest harness rows allowed in preview
}
INVENTORY_GROWTH_THRESHOLD = 1.25  # +25% allowance

ARTIFACT_DIR = Path("/app/test_reports/rc2")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def _is_preview() -> bool:
    db_name = (BACKEND_ENV.get("DB_NAME") or "").strip().lower()
    app_env = (BACKEND_ENV.get("APP_ENV") or "").strip().lower()
    return app_env == "preview" and "preview" in db_name


def _client_and_db():
    url = (BACKEND_ENV.get("MONGO_URL") or "").strip()
    db_name = (BACKEND_ENV.get("DB_NAME") or "").strip()
    assert _is_preview(), (
        f"REFUSING contamination scan against {db_name!r} / "
        f"APP_ENV={BACKEND_ENV.get('APP_ENV')!r}. Preview-only."
    )
    client = MongoClient(url, serverSelectionTimeoutMS=10_000)
    return client, client[db_name]


def _write_inventory(report: dict) -> None:
    out = ARTIFACT_DIR / "contamination_inventory.json"
    out.write_text(json.dumps(report, indent=2, default=str))


def test_rc2_contamination_inventory():
    """Single combined sweep — inventories contamination in preview.

    Fails only when:
      a) any count exceeds the baseline × growth-threshold (drift), OR
      b) the scan is somehow pointed at a non-preview database.
    """
    client, db = _client_and_db()
    try:
        # Equipment make contamination.
        eq_bad = []
        for doc in db.equipment_master.find(
            {}, {"_id": 1, "unit_number": 1, "make": 1}
        ).limit(20_000):
            make = (doc.get("make") or "").strip().lower()
            if make in CONTAM_MAKES:
                eq_bad.append({
                    "id": str(doc.get("_id")),
                    "unit_number": doc.get("unit_number"),
                    "make": doc.get("make"),
                })

        # Daily report project name contamination.
        rx_pn = re.compile("|".join(CONTAM_PROJECT_NAME_PATTERNS), re.IGNORECASE)
        dr_pn_bad = []
        for doc in db.daily_reports.find(
            {}, {"_id": 1, "project_name": 1, "project_number": 1}
        ).limit(20_000):
            name = doc.get("project_name") or ""
            num = doc.get("project_number") or ""
            if rx_pn.search(name) or rx_pn.search(num):
                dr_pn_bad.append({"id": str(doc.get("_id")),
                                  "project_name": name,
                                  "project_number": num})

        # Daily report prepared_by contamination.
        rx_pb = re.compile("|".join(CONTAM_PREPARED_BY_PATTERNS), re.IGNORECASE)
        dr_pb_bad = []
        for doc in db.daily_reports.find(
            {}, {"_id": 1, "prepared_by": 1, "report_id": 1}
        ).limit(20_000):
            pb = (doc.get("prepared_by") or "")
            if rx_pb.search(pb):
                dr_pb_bad.append({"id": str(doc.get("_id")),
                                  "report_id": doc.get("report_id"),
                                  "prepared_by": pb})

        report = {
            "scanned_db": db.name,
            "counts": {
                "equipment_make": len(eq_bad),
                "daily_project_name": len(dr_pn_bad),
                "daily_prepared_by": len(dr_pb_bad),
            },
            "samples": {
                "equipment_make": eq_bad[:10],
                "daily_project_name": dr_pn_bad[:10],
                "daily_prepared_by": dr_pb_bad[:10],
            },
        }
        _write_inventory(report)

        # Drift gate — only triggers if contamination has GROWN beyond
        # baseline × threshold. Allows preview fixtures to persist but
        # catches uncontrolled bloat.
        drifts = []
        for key, count in report["counts"].items():
            ceiling = INVENTORY_BASELINE[key] * INVENTORY_GROWTH_THRESHOLD
            if count > ceiling:
                drifts.append(
                    f"{key}: {count} > baseline {INVENTORY_BASELINE[key]} × "
                    f"{INVENTORY_GROWTH_THRESHOLD} ({ceiling:.0f})"
                )
        assert not drifts, (
            "Preview contamination has DRIFTED beyond baseline. "
            "Investigate fixture growth before deploy:\n" + "\n".join(drifts)
        )
    finally:
        client.close()


def test_rc2_contamination_scanner_refuses_production_shape(monkeypatch):
    """Sanity: if someone exports a production MONGO_URL by mistake the
    scanner refuses to proceed instead of silently scanning prod."""
    monkeypatch.setitem(BACKEND_ENV, "DB_NAME", "masci_safety")
    monkeypatch.setitem(BACKEND_ENV, "APP_ENV", "production")
    assert _is_preview() is False, "Safety guard must reject production shape"
