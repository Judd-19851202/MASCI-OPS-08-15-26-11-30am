from __future__ import annotations

import os
import re


WORKFLOW_PATH = "/app/.github/workflows/production-health-probe.yml"
SCRIPT_PATH = "/app/tools/verify-production.sh"
SERVER_PATH = "/app/backend/server.py"
RUNTIME_ROUTE_PATH = "/app/backend/routes/admin_runtime_reliability.py"


def test_probe_workflow_captures_headers_and_timings():
    src = open(WORKFLOW_PATH, encoding="utf-8").read()
    assert "cf-ray" in src.lower()
    assert "time_namelookup" in src
    assert "time_appconnect" in src
    assert "remote_ip" in src
    assert "/api/ready" in src


def test_verify_production_script_checks_version_and_classifies_failures():
    src = open(SCRIPT_PATH, encoding="utf-8").read()
    assert "/api/version" in src
    assert "/api/ready" in src
    assert "PROBE_CLASSIFICATION" in src
    assert "cloudflare_edge_origin_error" in src
    assert "PROBE_HEADERS_EXCERPT" in src


def test_verify_production_script_keeps_no_retry_contract():
    src = open(SCRIPT_PATH, encoding="utf-8").read()
    active_lines = [line for line in src.splitlines() if not line.strip().startswith("#")]
    assert "--retry" not in "\n".join(active_lines)


def test_hourly_complete_archive_uses_dynamic_activation_truth_in_server_source():
    src = open(SERVER_PATH, encoding="utf-8").read()
    assert 'requested_raw=os.environ.get("BACKUP_R2_HOURLY")' in src
    assert 'r2_hourly = bool(activation_state.get("r2_hourly_effective"))' in src
    assert '"r2_hourly_effective": bool(activation_state.get("r2_hourly_effective"))' in src


def test_backup_scheduler_state_exposes_hourly_archive_lock_truth():
    src = open(SERVER_PATH, encoding="utf-8").read()
    assert '"r2_hourly_requested"' in src
    assert '"r2_hourly_effective"' in src
    assert '"r2_hourly_locked_off"' in src


def test_runtime_forensics_admin_routes_exist_in_source():
    src = open(RUNTIME_ROUTE_PATH, encoding="utf-8").read()
    assert '/runtime-health' in src
    assert '/incident-forensics' in src