from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from backend.lib.release_fingerprint import build_release_manifest, write_fingerprint_record


def _write_contract(repo_root: Path) -> None:
    contract_dir = repo_root / "docs/governance"
    contract_dir.mkdir(parents=True, exist_ok=True)
    (contract_dir / "release_content_fingerprint_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "TEST/v1",
                "algorithm_version": "test-sha256-v1",
                "include_roots": ["."],
                "exclude_exact": ["memory/PRE_SAVE_CONTENT_FINGERPRINT.json"],
                "exclude_globs": [".git/**", "**/*.log", "backend/.env", "frontend/.env", "backend/.env.*", "frontend/.env.*"],
                "normalize": {
                    ".emergent/emergent.yml": {
                        "format": "json",
                        "drop_keys": ["created_at"],
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_fixture_repo(repo_root: Path) -> None:
    _write_contract(repo_root)
    (repo_root / ".emergent").mkdir(parents=True, exist_ok=True)
    (repo_root / ".emergent" / "emergent.yml").write_text(
        json.dumps(
            {
                "env_image_name": "masci-preview:1",
                "job_id": "job-123",
                "created_at": "2026-08-11T10:00:00Z",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "frontend/src").mkdir(parents=True, exist_ok=True)
    (repo_root / "frontend/src" / "App.jsx").write_text("export const App = () => 'ready';\n", encoding="utf-8")
    (repo_root / "backend").mkdir(parents=True, exist_ok=True)
    (repo_root / "backend" / "server.py").write_text("APP = 'ready'\n", encoding="utf-8")
    (repo_root / "memory").mkdir(parents=True, exist_ok=True)


def test_release_fingerprint_is_reproducible_and_self_excluding(tmp_path: Path) -> None:
    _write_fixture_repo(tmp_path)
    first = build_release_manifest(tmp_path)
    second = build_release_manifest(tmp_path)
    assert first["manifest_sha256"] == second["manifest_sha256"]

    written = write_fingerprint_record(
        tmp_path,
        output_path=tmp_path / "memory" / "PRE_SAVE_CONTENT_FINGERPRINT.json",
        base_head="HEAD123",
        workspace_status_lines=["M frontend/src/App.jsx"],
    )
    third = build_release_manifest(tmp_path)
    assert third["manifest_sha256"] == first["manifest_sha256"]
    assert written["content_manifest_sha256"] == first["manifest_sha256"]

    app_path = tmp_path / "frontend/src/App.jsx"
    original = app_path.stat().st_mtime
    os.utime(app_path, (original + 60, original + 60))
    fourth = build_release_manifest(tmp_path)
    assert fourth["manifest_sha256"] == first["manifest_sha256"]


def test_release_fingerprint_changes_for_meaningful_content_only(tmp_path: Path) -> None:
    _write_fixture_repo(tmp_path)
    baseline = build_release_manifest(tmp_path)

    emergent = tmp_path / ".emergent" / "emergent.yml"
    payload = json.loads(emergent.read_text(encoding="utf-8"))
    payload["created_at"] = "2026-09-01T00:00:00Z"
    emergent.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    created_at_only = build_release_manifest(tmp_path)
    assert created_at_only["manifest_sha256"] == baseline["manifest_sha256"]

    payload["env_image_name"] = "masci-preview:2"
    emergent.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    meaningful_config = build_release_manifest(tmp_path)
    assert meaningful_config["manifest_sha256"] != baseline["manifest_sha256"]

    app_path = tmp_path / "frontend/src/App.jsx"
    app_path.write_text("export const App = () => 'repaired';\n", encoding="utf-8")
    source_change = build_release_manifest(tmp_path)
    assert source_change["manifest_sha256"] != meaningful_config["manifest_sha256"]


def test_release_fingerprint_contract_a_to_g(tmp_path: Path) -> None:
    _write_fixture_repo(tmp_path)

    # A/B: repeated computes without changes stay identical.
    first = build_release_manifest(tmp_path)
    second = build_release_manifest(tmp_path)
    third = build_release_manifest(tmp_path)
    assert second["manifest_sha256"] == first["manifest_sha256"]
    assert third["manifest_sha256"] == first["manifest_sha256"]

    # C: writing the fingerprint record must not alter the aggregate.
    record_path = tmp_path / "memory" / "PRE_SAVE_CONTENT_FINGERPRINT.json"
    write_fingerprint_record(
        tmp_path,
        output_path=record_path,
        base_head="HEAD123",
        workspace_status_lines=["M frontend/src/App.jsx"],
    )
    after_first_write = build_release_manifest(tmp_path)
    assert after_first_write["manifest_sha256"] == first["manifest_sha256"]

    write_fingerprint_record(
        tmp_path,
        output_path=record_path,
        base_head="HEAD123",
        workspace_status_lines=["M frontend/src/App.jsx", "M backend/server.py"],
    )
    after_second_write = build_release_manifest(tmp_path)
    assert after_second_write["manifest_sha256"] == first["manifest_sha256"]

    # D: mtime-only changes must not alter the aggregate.
    app_path = tmp_path / "frontend/src/App.jsx"
    original = app_path.stat().st_mtime
    os.utime(app_path, (original + 60, original + 60))
    after_mtime_touch = build_release_manifest(tmp_path)
    assert after_mtime_touch["manifest_sha256"] == first["manifest_sha256"]

    # F: normalize only the proven volatile platform metadata.
    emergent = tmp_path / ".emergent" / "emergent.yml"
    payload = json.loads(emergent.read_text(encoding="utf-8"))
    payload["created_at"] = "2026-09-01T00:00:00Z"
    emergent.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    after_created_at_only = build_release_manifest(tmp_path)
    assert after_created_at_only["manifest_sha256"] == first["manifest_sha256"]

    # G: meaningful platform config changes must still alter the aggregate.
    payload["env_image_name"] = "masci-preview:2"
    emergent.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    after_meaningful_platform_change = build_release_manifest(tmp_path)
    assert after_meaningful_platform_change["manifest_sha256"] != first["manifest_sha256"]

    # E: meaningful source-byte changes must alter the aggregate.
    app_path.write_text("export const App = () => 'final';\n", encoding="utf-8")
    after_source_change = build_release_manifest(tmp_path)
    assert after_source_change["manifest_sha256"] != after_meaningful_platform_change["manifest_sha256"]


def test_release_fingerprint_excludes_runtime_injected_env_bindings(tmp_path: Path) -> None:
    _write_fixture_repo(tmp_path)
    (tmp_path / "backend" / ".env").write_text("APP_ENV=preview\nJWT_SECRET=preview-secret\n", encoding="utf-8")
    (tmp_path / "frontend" / ".env").write_text("REACT_APP_BACKEND_URL=https://preview.example.test\n", encoding="utf-8")
    baseline = build_release_manifest(tmp_path)
    assert "backend/.env" not in [row["path"] for row in baseline["entries"]]
    assert "frontend/.env" not in [row["path"] for row in baseline["entries"]]

    (tmp_path / "backend" / ".env").write_text("APP_ENV=production\nJWT_SECRET=prod-secret\n", encoding="utf-8")
    (tmp_path / "frontend" / ".env").write_text("REACT_APP_BACKEND_URL=https://mascidocs.com\n", encoding="utf-8")
    changed = build_release_manifest(tmp_path)
    assert changed["manifest_sha256"] == baseline["manifest_sha256"]
