from __future__ import annotations

import os
import re


WORKFLOW_PATH = "/app/.github/workflows/production-health-probe.yml"
SCRIPT_PATH = "/app/tools/verify-production.sh"
SERVER_PATH = "/app/backend/server.py"


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


def test_hourly_complete_archive_is_hard_locked_off_in_server_source():
    src = open(SERVER_PATH, encoding="utf-8").read()
    assert '"r2_hourly_effective": False' in src
    assert '"r2_hourly_locked_off": True' in src
    assert 'r2_hourly = False' in src