"""
tests/test_integration_honesty_and_archive_origin.py
Track 14.0-I1 · Integration Honesty + Archive Origin Verification.

Static-analysis and live-API regression guards for:

  * The platform-standard honesty vocabulary
    (LIVE / CONFIGURED / PARTIAL / DISCONNECTED / ERROR) is applied
    to every integration probe.
  * The honesty mapper never reports LIVE for a mocked integration
    nor LIVE for an integration with no credentials.
  * Backup archives carry a manifest with `environment` /
    `database_name` / `backup_id` so the restore endpoint can verify
    origin before touching data.
  * The `/api/exports/restore` endpoint refuses to import an archive
    whose `environment` disagrees with the running worker's APP_ENV
    (the last manual-checklist item from Track 14.0-P0).
  * Every restore attempt — accepted OR rejected — emits an
    `exports_restore` audit row.

Closure ledger:
/app/memory/TRACK_14_0_I1_INTEGRATION_HONESTY_AND_ARCHIVE_ORIGIN_VERIFICATION_CLOSURE.md
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path("/app")
SERVER = REPO / "backend/server.py"
HEALTH = REPO / "backend/routes/integration_health.py"


# ── Load _normalize_honesty_status without booting FastAPI ────────


def _load_health_module():
    spec = importlib.util.spec_from_file_location(
        "_integration_health_test", HEALTH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_integration_health_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Honesty status vocabulary ─────────────────────────────────────


@pytest.mark.parametrize("probe,expected", [
    # (raw probe dict, expected honesty status)
    ({"status": "ok"},                                                 "LIVE"),
    ({"status": "ok", "mocked": False},                                "LIVE"),
    ({"status": "ok", "api_key_present": True},                        "LIVE"),
    ({"status": "ok", "mocked": True},                                 "DISCONNECTED"),  # mocked overrides
    ({"status": "disabled", "mocked": True},                           "DISCONNECTED"),
    ({"status": "disabled", "api_key_present": True},                  "CONFIGURED"),
    ({"status": "disabled", "api_key_present": False},                 "DISCONNECTED"),
    ({"status": "degraded", "webhook_secret_present": True},           "PARTIAL"),
    ({"status": "degraded", "api_key_present": True},                  "PARTIAL"),
    ({"status": "degraded", "api_key_present": False},                 "ERROR"),
    ({"status": "down", "api_key_present": True},                      "ERROR"),
    ({"status": "down"},                                               "ERROR"),
    ({"status": "unknown"},                                            "ERROR"),
])
def test_honesty_status_vocabulary(probe, expected):
    mod = _load_health_module()
    assert mod._normalize_honesty_status(probe) == expected


def test_no_fake_live_for_mocked_integration():
    """Triple-check the most dangerous misreport: a `mocked` integration
    must NEVER carry honesty_status=LIVE because that would lie to
    the admin about real connectivity."""
    mod = _load_health_module()
    # MaintainX-shape (the canonical mocked integration today).
    out = mod._normalize_honesty_status({
        "id": "maintainx", "status": "disabled", "mocked": True,
    })
    assert out == "DISCONNECTED"
    # Even with a fake "ok" status — mocked still wins.
    out = mod._normalize_honesty_status({
        "id": "future_mock", "status": "ok", "mocked": True,
    })
    assert out == "DISCONNECTED"


def test_no_live_without_some_credential_signal():
    """An integration probe whose raw status is `disabled` with no
    credential evidence must never report LIVE."""
    mod = _load_health_module()
    out = mod._normalize_honesty_status({
        "id": "future_int", "status": "disabled",
        "api_key_present": False, "mocked": False,
    })
    assert out == "DISCONNECTED"


def test_runtime_probe_payload_emits_honesty_status():
    """The run_all_probes() output must stamp every probe with
    honesty_status so the admin Integration Health Center can render
    the unified vocabulary without re-implementing the mapper."""
    text = HEALTH.read_text()
    assert "honesty_status" in text and "_normalize_honesty_status" in text, (
        "integration_health.run_all_probes must stamp honesty_status "
        "on every probe. Restore the normalize call.")


# ── Archive Origin Verification — manifest + restore gate ─────────


def test_backup_manifest_records_environment():
    """The `backup_manifest.json` emitted by /api/exports/full-backup
    must include `environment` + `database_name` + `backup_id`. Without
    these fields the restore endpoint cannot verify the archive
    origin and must fall back to the legacy-archive code path."""
    text = SERVER.read_text()
    # The manifest writer block must reference all three keys.
    assert '"environment": _app_env' in text, (
        "Backup manifest no longer records `environment`. Without it, "
        "restore cannot enforce origin verification.")
    assert '"database_name": _db_name' in text, (
        "Backup manifest no longer records `database_name`. Without "
        "it, db-mismatch protection is impossible.")
    assert '"backup_id":' in text and '"manifest_schema":' in text, (
        "Backup manifest no longer carries a backup_id or schema "
        "version. Audit traceability lost.")


def test_restore_endpoint_rejects_environment_mismatch():
    """The /api/exports/restore handler must read manifest.environment
    and compare against the running APP_ENV, raising HTTPException(400)
    on mismatch. Static-analyze the handler body to confirm the gate
    survives future refactors."""
    text = SERVER.read_text()
    # Pull the function body for exports_restore.
    start = text.find("async def exports_restore(")
    assert start > 0, "exports_restore endpoint missing"
    body = text[start:start + 8000]
    for needle in (
        'archive_env',
        'archive_env != current_env',
        'Archive originated from the',
        'archive_db != current_db',
        'manifest.get("environment")',
    ):
        assert needle in body, (
            f"exports_restore lost the origin-verification gate "
            f"(missing {needle!r}). Restore the Track 14.0-I1 check.")


def test_restore_endpoint_audits_every_attempt():
    """Both accept and reject paths in /api/exports/restore must write
    an `exports_restore` audit row. Without this, a rejected
    cross-environment restore would leave no operational trace."""
    text = SERVER.read_text()
    start = text.find("async def exports_restore(")
    # The restore handler is long — grab a generous window so the
    # success-audit at the end falls inside.
    body = text[start:start + 30000]
    assert '"kind": "exports_restore"' in body, (
        "exports_restore audit document tag missing."
    )
    assert "_record_audit" in body, (
        "exports_restore no longer calls the local _record_audit helper."
    )
    assert '"rejected"' in body and '"accepted"' in body, (
        "exports_restore audit must capture both `accepted` and "
        "`rejected` results."
    )


def test_restore_legacy_archive_in_production_is_rejected():
    """Archives generated before the Track 14.0-I1 manifest standard
    have no `environment` field. The handler must REJECT them in
    production (better safe than sorry) and ACCEPT-with-warning in
    preview so historical regression archives stay usable."""
    text = SERVER.read_text()
    start = text.find("async def exports_restore(")
    body = text[start:start + 8000]
    assert "if not archive_env:" in body, (
        "Legacy-archive (no environment field) branch missing."
    )
    assert 'current_env == "production"' in body, (
        "Legacy-archive branch no longer fails closed in production."
    )
    assert "missing-environment-field" in body, (
        "Legacy-archive rejection reason tag missing in audit body."
    )
