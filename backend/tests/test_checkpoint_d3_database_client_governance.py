from __future__ import annotations

import json
from pathlib import Path

from lib.database_client_governance import discover_database_client_inventory, inventory_summary


def test_generated_inventory_matches_checked_in_file() -> None:
    generated = discover_database_client_inventory("/app")
    checked_in = json.loads(Path("/app/docs/governance/database_client_inventory.json").read_text(encoding="utf-8"))
    assert generated == checked_in


def test_register_mentions_canonical_runtime_authority() -> None:
    register_text = Path("/app/docs/governance/DATABASE_CLIENT_AUTHORITY_REGISTER.md").read_text(encoding="utf-8")
    assert "CANONICAL_RUNTIME_CLIENT" in register_text
    assert "backend/lib/database_authority.py" in register_text


def test_runtime_client_summary_is_governed() -> None:
    summary = inventory_summary(discover_database_client_inventory("/app"))
    assert summary["runtime"] >= 1
    assert summary["duplicate"] == 0
    assert summary["request_scoped"] == 0
    assert summary["unsafe"] == 0
    assert summary["unknown"] == 0