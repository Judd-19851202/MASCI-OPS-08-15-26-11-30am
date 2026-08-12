#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
SKIP_HEAVY_BUILDS = os.environ.get("RELEASE_GATE_SKIP_HEAVY_BUILDS") == "1"
SKIP_FOCUSED_REGRESSIONS = os.environ.get("RELEASE_GATE_SKIP_FOCUSED_REGRESSIONS") == "1"

from lib.release_gate_governance import (  # noqa: E402
    collect_git_snapshot,
    compute_dependency_manifest_hash,
    evaluate_pre_save_candidate,
    compute_migration_manifest_hash,
    compute_release_gate_manifest_hash,
    load_release_gate_manifest,
    one_body_contract_failures,
    evaluate_workspace_state_source_authority,
    validate_release_gate_manifest,
    validate_workflows,
)


def _run(cmd: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["RELEASE_GATE_RUNNING"] = "1"
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "duration_seconds": round(time.perf_counter() - started, 3),
    }


def _python_cmd(*args: str) -> list[str]:
    return [sys.executable, *args]


def _copy_repo() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="masci-release-gate-"))
    dst = tmp_root / "repo"
    ignore = shutil.ignore_patterns(
        ".git", ".emergent", "node_modules", "frontend/node_modules", "frontend/build", "frontend/.cache", ".cache", "__pycache__", ".pytest_cache", "deploy_reports", "test_reports", "walkthrough_reports"
    )
    shutil.copytree(REPO_ROOT, dst, ignore=ignore)
    return dst


def _backend_build_gate() -> dict[str, Any]:
    if SKIP_HEAVY_BUILDS:
        count = len([line for line in (REPO_ROOT / "backend" / "requirements.txt").read_text().splitlines() if line.strip() and not line.startswith("#")])
        return {
            "returncode": 0,
            "skipped": True,
            "reason": "RELEASE_GATE_SKIP_HEAVY_BUILDS=1",
            "python_dependency_count": count,
            "passed": True,
        }
    repo = _copy_repo()
    venv = repo.parent / "venv"
    install = _run(["bash", "-lc", f"python3 -m venv '{venv}' && . '{venv}/bin/activate' && pip install --no-cache-dir -r backend/requirements.txt"], cwd=repo, timeout=1800)
    compileall = _run(["bash", "-lc", f". '{venv}/bin/activate' && python -m compileall backend"], cwd=repo, timeout=1200) if install["returncode"] == 0 else None
    import_server = _run(["bash", "-lc", f". '{venv}/bin/activate' && PYTHONPATH=backend python -c \"import server; print('IMPORT_OK')\""], cwd=repo, timeout=1200) if install["returncode"] == 0 else None
    verify = _run(["bash", "-lc", f". '{venv}/bin/activate' && python backend/scripts/verify_release_identity.py --strict"], cwd=repo, timeout=1200) if install["returncode"] == 0 else None
    count = len([line for line in (repo / "backend" / "requirements.txt").read_text().splitlines() if line.strip() and not line.startswith("#")])
    passed = bool(install["returncode"] == 0 and compileall and compileall["returncode"] == 0 and import_server and import_server["returncode"] == 0 and verify and verify["returncode"] == 0)
    return {
        "returncode": 0 if passed else 1,
        "python_version": _run(["python3", "--version"], cwd=repo, timeout=60),
        "clean_install": install,
        "compileall": compileall,
        "import_server": import_server,
        "verify_release_identity": verify,
        "python_dependency_count": count,
        "passed": passed,
    }


def _frontend_metrics(repo: Path) -> dict[str, Any]:
    js_dir = repo / "frontend" / "build" / "static" / "js"
    chunks = []
    if js_dir.exists():
        for file in sorted(js_dir.glob("*.js")):
            chunks.append({"file": file.name, "size_bytes": file.stat().st_size})
    return {
        "bundle_size_bytes": sum(item["size_bytes"] for item in chunks),
        "largest_chunks": sorted(chunks, key=lambda item: item["size_bytes"], reverse=True)[:5],
        "sourcemap_count": len(list((repo / "frontend" / "build").rglob("*.map"))),
    }


def _frontend_build_gate() -> dict[str, Any]:
    if SKIP_HEAVY_BUILDS:
        package_json = json.loads((REPO_ROOT / "frontend" / "package.json").read_text())
        return {
            "returncode": 0,
            "skipped": True,
            "reason": "RELEASE_GATE_SKIP_HEAVY_BUILDS=1",
            "node_dependency_count": len(package_json.get("dependencies", {})) + len(package_json.get("devDependencies", {})),
            "passed": True,
        }
    repo = _copy_repo()
    cache_dir = repo.parent / "yarn-cache"
    install = _run(["yarn", "install", "--frozen-lockfile", "--ignore-scripts", "--cache-folder", str(cache_dir)], cwd=repo / "frontend", timeout=1800)
    build = _run(["yarn", "build"], cwd=repo / "frontend", timeout=1800) if install["returncode"] == 0 else None
    package_json = json.loads((repo / "frontend" / "package.json").read_text())
    metrics = _frontend_metrics(repo) if build and build["returncode"] == 0 else {}
    passed = bool(build and build["returncode"] == 0)
    return {
        "returncode": 0 if passed else 1,
        "node_version": _run(["node", "--version"], cwd=repo, timeout=60),
        "yarn_version": _run(["yarn", "--version"], cwd=repo, timeout=60),
        "clean_install": install,
        "build": build,
        "node_dependency_count": len(package_json.get("dependencies", {})) + len(package_json.get("devDependencies", {})),
        "passed": passed,
        **metrics,
    }


def _focused_regressions() -> dict[str, Any]:
    if SKIP_FOCUSED_REGRESSIONS:
        return {
            "skipped": True,
            "reason": "RELEASE_GATE_SKIP_FOCUSED_REGRESSIONS=1",
            "returncode": 0,
        }
    return _run([
        *_python_cmd("-m", "pytest", "-q"),
        "/app/backend/tests/test_operator_language_premerge_guard.py",
        "/app/backend/tests/test_runtime_identity_contract.py",
        "/app/backend/tests/test_checkpoint_d2_runtime_truth_normalization.py",
        "/app/backend/tests/test_checkpoint_d3_database_authority.py",
        "/app/backend/tests/test_checkpoint_d4_dependency_governance.py",
        "/app/backend/tests/test_checkpoint_d5_d6_release_gate.py",
        "/app/backend/tests/test_checkpoint_d7_d8_performance_repairs.py",
        "/app/backend/tests/test_prec10_corrective_action_truth_governance.py",
        "/app/backend/tests/test_prec10_schedule_truth_chain_independent.py",
        "/app/backend/tests/test_prec10_platform_truth_integrity.py",
    ], cwd=REPO_ROOT, timeout=1800)


def _secret_scan() -> dict[str, Any]:
    return _run([*_python_cmd("-m", "pytest", "-q"), "/app/backend/tests/test_track_15_80_no_secrets_in_repo.py"], cwd=REPO_ROOT, timeout=900)


def _prd_lint() -> dict[str, Any]:
    return _run([*_python_cmd("/app/scripts/lint-iteration-summary.py")], cwd=REPO_ROOT, timeout=120)


def _release_identity_verifier() -> dict[str, Any]:
    return _run([*_python_cmd("/app/backend/scripts/verify_release_identity.py", "--strict")], cwd=REPO_ROOT, timeout=600)


def _workflow_gate() -> dict[str, Any]:
    errors = validate_workflows(REPO_ROOT)
    return {"returncode": 0 if not errors else 1, "errors": errors}


def _manifest_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    errors = validate_release_gate_manifest(manifest, REPO_ROOT)
    return {"returncode": 0 if not errors else 1, "errors": errors}


def _one_body_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    errors = one_body_contract_failures(manifest, REPO_ROOT)
    return {"returncode": 0 if not errors else 1, "errors": errors}


def _backup_contract_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    contract = manifest.get("backup_verification_contract") or {}
    required = contract.get("required_checks") or []
    errors = []
    if contract.get("verification_only") is not True:
        errors.append("backup verification contract must be verification_only")
    if contract.get("no_backup_or_restore_execution") is not True:
        errors.append("backup verification contract must forbid backup/restore execution")
    authority_route = contract.get("authority_route")
    if not authority_route or not (REPO_ROOT / authority_route).exists():
        errors.append("backup verification authority route missing")
    missing = [field for field in required if field not in (manifest.get("backup_dr_prerequisites") or {})]
    if missing:
        errors.append("backup prerequisites missing required checks: " + ", ".join(missing))
    runtime = _backup_runtime_freshness()
    if runtime.get("error"):
        errors.append(runtime["error"])
    else:
        if not runtime.get("latest_backup_ts"):
            errors.append("no successful complete-r2 backup found in canonical runtime history")
        elif runtime.get("backup_age_minutes") is None or runtime.get("backup_age_minutes") > runtime.get("backup_age_target_minutes", 60):
            errors.append(
                "latest successful complete-r2 backup is stale "
                f"({runtime.get('backup_age_minutes')} min vs target <= {runtime.get('backup_age_target_minutes', 60)} min)"
            )
        if not runtime.get("latest_restore_drill_ts"):
            errors.append("no successful restore drill found in canonical runtime history")
        elif runtime.get("restore_drill_age_hours") is None or runtime.get("restore_drill_age_hours") > runtime.get("restore_drill_age_target_hours", 24):
            errors.append(
                "latest successful restore drill is stale "
                f"({runtime.get('restore_drill_age_hours')} h vs target <= {runtime.get('restore_drill_age_target_hours', 24)} h)"
            )
    return {"returncode": 0 if not errors else 1, "errors": errors, "runtime": runtime}


def _backup_runtime_freshness() -> dict[str, Any]:
    try:
        from pymongo import MongoClient  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover
        return {"error": f"pymongo unavailable: {type(exc).__name__}"}

    env_path = REPO_ROOT / "backend" / ".env"
    env = {}
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    except OSError as exc:
        return {"error": f"backend env unreadable: {type(exc).__name__}"}

    mongo_url = env.get("MONGO_URL")
    db_name = env.get("DB_NAME")
    if not mongo_url or not db_name:
        return {"error": "MONGO_URL or DB_NAME missing from backend env"}

    def _parse_ts(value: Any):
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            text = str(value)
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return datetime.fromisoformat(text)
        except Exception:
            return None

    now = datetime.now(timezone.utc)
    backup_age_target = int(os.environ.get("BACKUP_RPO_TARGET_MINUTES", env.get("BACKUP_RPO_TARGET_MINUTES") or "60") or "60")
    restore_age_target = int(os.environ.get("RESTORE_DRILL_MAX_AGE_HOURS", env.get("RESTORE_DRILL_MAX_AGE_HOURS") or "24") or "24")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        db = client[db_name]
        latest_backup = db.backup_health.find_one(
            {"mode": "complete-r2", "ok": True},
            {"_id": 0, "ts": 1, "filename": 1},
            sort=[("ts", -1)],
        )
        latest_drill = db.drill_runs.find_one(
            {"state": "done", "outcome": "OK"},
            {"_id": 0, "finished_at": 1, "started_at": 1, "archive_filename": 1, "duration_minutes": 1},
            sort=[("started_at", -1)],
        )
    except Exception as exc:  # pragma: no cover
        return {"error": f"backup runtime query failed: {type(exc).__name__}"}
    finally:
        client.close()

    backup_dt = _parse_ts((latest_backup or {}).get("ts"))
    drill_dt = _parse_ts((latest_drill or {}).get("finished_at") or (latest_drill or {}).get("started_at"))
    return {
        "latest_backup_ts": (latest_backup or {}).get("ts"),
        "latest_backup_filename": (latest_backup or {}).get("filename"),
        "backup_age_minutes": round((now - backup_dt).total_seconds() / 60.0, 2) if backup_dt else None,
        "backup_age_target_minutes": backup_age_target,
        "latest_restore_drill_ts": (latest_drill or {}).get("finished_at") or (latest_drill or {}).get("started_at"),
        "latest_restore_archive_filename": (latest_drill or {}).get("archive_filename"),
        "latest_restore_duration_minutes": (latest_drill or {}).get("duration_minutes"),
        "restore_drill_age_hours": round((now - drill_dt).total_seconds() / 3600.0, 2) if drill_dt else None,
        "restore_drill_age_target_hours": restore_age_target,
    }


def _performance_baseline_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    perf = manifest.get("performance_prerequisites") or {}
    errors = []
    payloads = {}
    required_paths = {
        "machine_readable_baseline": perf.get("machine_readable_baseline"),
        "query_inventory": perf.get("query_inventory"),
        "atlas_evidence_register": perf.get("atlas_evidence_register"),
        "index_query_recommendation_register": perf.get("index_query_recommendation_register"),
        "safe_self_healing_contract": perf.get("safe_self_healing_contract"),
        "performance_budget_register": perf.get("performance_budget_register"),
    }
    for key, rel in required_paths.items():
        if not rel:
            errors.append(f"performance prerequisite missing path for {key}")
            continue
        path = REPO_ROOT / rel
        if not path.exists():
            errors.append(f"missing performance artifact: {rel}")
            continue
        if path.suffix == ".json":
            try:
                payloads[key] = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"invalid json in {rel}: {type(exc).__name__}")
        elif path.suffix == ".csv":
            try:
                with path.open(encoding="utf-8", newline="") as handle:
                    payloads[key] = list(csv.DictReader(handle))
            except Exception as exc:
                errors.append(f"invalid csv in {rel}: {type(exc).__name__}")
    baseline = payloads.get("machine_readable_baseline") or {}
    for field in ["checkpoint", "captured_at", "backend", "frontend", "scheduler", "workspace_resources"]:
        if field not in baseline:
            errors.append(f"performance baseline missing {field}")
    budget_rows = payloads.get("performance_budget_register") or []
    if not budget_rows:
        errors.append("performance budget register missing rows")
    else:
        required_budget_keys = list(perf.get("required_budget_keys") or [])
        seen_budget_keys = {str((row or {}).get("budget_key") or "").strip() for row in budget_rows}
        missing_budget_keys = [key for key in required_budget_keys if key not in seen_budget_keys]
        if missing_budget_keys:
            errors.append("performance budget register missing keys: " + ", ".join(missing_budget_keys))
        failing_rows = []
        for row in budget_rows:
            budget_key = str((row or {}).get("budget_key") or "").strip()
            status = str((row or {}).get("status") or "").strip().upper()
            if not budget_key:
                errors.append("performance budget row missing budget_key")
                continue
            if status != "PASS":
                failing_rows.append({
                    "budget_key": budget_key,
                    "status": status or "MISSING",
                    "measured": (row or {}).get("measured"),
                    "target": (row or {}).get("target"),
                })
        if failing_rows:
            errors.append(
                "performance budget register contains non-pass rows: "
                + ", ".join(f"{row['budget_key']}={row['status']}" for row in failing_rows)
            )
    return {
        "returncode": 0 if not errors else 1,
        "errors": errors,
        "baseline": baseline,
        "budget_rows": budget_rows,
    }


def _migration_contract_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    path = REPO_ROOT / "docs" / "governance" / "MIGRATION_COMPATIBILITY_REGISTER.md"
    errors = []
    if not path.exists():
        errors.append("migration compatibility register missing")
    else:
        text = path.read_text(encoding="utf-8")
        for needle in ["BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW", "Migration ID", "Backward compatibility", "Forward compatibility"]:
            if needle not in text:
                errors.append(f"migration register missing {needle}")
    return {"returncode": 0 if not errors else 1, "errors": errors}


def _operator_language_gate() -> dict[str, Any]:
    outcome = _run([*_python_cmd("scripts/operator_language_gate.py", "--json")], cwd=REPO_ROOT, timeout=600)
    payload: dict[str, Any] = {}
    stdout_tail = outcome.get("stdout_tail") or ""
    if stdout_tail.strip():
        try:
            payload = json.loads(stdout_tail)
        except Exception:
            payload = {
                "parse_error": "operator language gate did not emit valid json",
                "raw_stdout": stdout_tail[-2000:],
            }
    return {
        **outcome,
        **payload,
        "returncode": 0 if outcome.get("returncode") == 0 else 1,
    }


def _runtime_screenshot_ledger_gate() -> dict[str, Any]:
    outcome = _run([*_python_cmd("scripts/runtime_screenshot_ledger_gate.py", "--json")], cwd=REPO_ROOT, timeout=1800)
    payload: dict[str, Any] = {}
    stdout_tail = outcome.get("stdout_tail") or ""
    if stdout_tail.strip():
        try:
            payload = json.loads(stdout_tail)
        except Exception:
            payload = {
                "parse_error": "runtime screenshot ledger did not emit valid json",
                "raw_stdout": stdout_tail[-2000:],
            }
    return {
        **outcome,
        **payload,
        "returncode": 0 if outcome.get("returncode") == 0 else 1,
    }


def _post_deploy_contract_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    schema = REPO_ROOT / "docs" / "recovery" / "POST_DEPLOY_CERTIFICATE_SCHEMA.json"
    errors = []
    if not schema.exists():
        errors.append("post deploy certificate schema missing")
    else:
        payload = json.loads(schema.read_text(encoding="utf-8"))
        required = set((payload.get("items") or {}).get("required") or [])
        expected = {"probe_id", "timestamp", "environment", "source_sha", "result", "evidence", "blocker_severity"}
        missing = sorted(expected - required)
        if missing:
            errors.append("post deploy schema missing required fields: " + ", ".join(missing))
    return {"returncode": 0 if not errors else 1, "errors": errors}


def _source_authority_gate(manifest: dict[str, Any], target: str) -> dict[str, Any]:
    snapshot = collect_git_snapshot(REPO_ROOT)
    errors = []
    env_mode = os.environ.get("RELEASE_GATE_SOURCE_AUTHORITY_MODE") == "clean_checkout_proof"
    env_branch = (os.environ.get("RELEASE_GATE_SOURCE_BRANCH") or "").strip()
    env_head = (os.environ.get("RELEASE_GATE_SOURCE_HEAD") or "").strip()
    env_dirty_raw = (os.environ.get("RELEASE_GATE_SOURCE_DIRTY") or "").strip().lower()
    env_dirty = env_dirty_raw in {"1", "true", "yes"}
    branch = env_branch if env_mode and env_branch else (snapshot.get("branch") or "")
    head = env_head if env_mode and env_head else (snapshot.get("head") or "")
    dirty = env_dirty if env_mode else bool(snapshot.get("dirty"))
    governed = set((manifest.get("governed_branches") or {}).get(target) or [])
    pre_save = evaluate_pre_save_candidate(snapshot, manifest)
    detached_workspace_state = evaluate_workspace_state_source_authority(snapshot, manifest, target=target)
    detached_pre_save_candidate = bool(not branch and head and pre_save.get("passed"))
    if branch:
        if branch not in governed:
            errors.append(f"branch {branch} is not governed for {target}")
    elif not detached_workspace_state.get("passed") and not detached_pre_save_candidate:
        errors.append(f"branch {branch} is not governed for {target}")
    if not head:
        errors.append("git HEAD unavailable")
    if dirty and not pre_save.get("passed"):
        errors.extend(pre_save.get("errors") or [])
        if not any("dirty workspace" in err for err in errors):
            errors.append("workspace is dirty")
    if env_mode:
        snapshot["clean_checkout_proof"] = {
            "declared_branch": env_branch,
            "declared_head": env_head,
            "declared_dirty": env_dirty,
        }
    snapshot["evaluated_branch"] = branch
    snapshot["evaluated_head"] = head
    snapshot["evaluated_dirty"] = dirty
    snapshot["detached_workspace_state_authority"] = detached_workspace_state
    snapshot["detached_pre_save_candidate_authority"] = {
        "passed": detached_pre_save_candidate,
        "classification": "DETACHED_PRE_SAVE_CANDIDATE" if detached_pre_save_candidate else "NOT_APPLICABLE",
    }
    return {
        "returncode": 0 if not errors else 1,
        "snapshot": snapshot,
        "pre_save_candidate": pre_save,
        "errors": errors,
    }


CHECK_RUNNERS = {
    "source-authority": _source_authority_gate,
    "release-identity-verifier": lambda manifest, target: _release_identity_verifier(),
    "release-gate-manifest": lambda manifest, target: _manifest_gate(manifest),
    "one-body-authorities": lambda manifest, target: _one_body_gate(manifest),
    "operator-language-hard-fail": lambda manifest, target: _operator_language_gate(),
    "runtime-screenshot-ledger": lambda manifest, target: _runtime_screenshot_ledger_gate(),
    "performance-baseline-contract": lambda manifest, target: _performance_baseline_gate(manifest),
    "workflow-audit": lambda manifest, target: _workflow_gate(),
    "backup-verification-contract": lambda manifest, target: _backup_contract_gate(manifest),
    "migration-compatibility-contract": lambda manifest, target: _migration_contract_gate(manifest),
    "post-deploy-certificate-contract": lambda manifest, target: _post_deploy_contract_gate(manifest),
    "secret-scan": lambda manifest, target: _secret_scan(),
    "prd-governance-lint": lambda manifest, target: _prd_lint(),
    "clean-backend-build": lambda manifest, target: _backend_build_gate(),
    "clean-frontend-build": lambda manifest, target: _frontend_build_gate(),
    "focused-regressions": lambda manifest, target: _focused_regressions(),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical D5/D6 release gate")
    parser.add_argument("--target", choices=["preview", "production"], default="preview")
    parser.add_argument("--json", action="store_true", dest="emit_json")
    args = parser.parse_args()
    manifest = load_release_gate_manifest(REPO_ROOT)
    gates = []
    failed = False
    for gate in manifest.get("mandatory_checks", []):
        if args.target not in (gate.get("applicability") or []):
            continue
        gate_id = gate.get("gate_id")
        runner = CHECK_RUNNERS.get(gate_id)
        if runner is None:
            continue
        outcome = runner(manifest, args.target)
        passed = outcome.get("returncode", 1) == 0
        failed = failed or not passed
        gates.append({
            "gate_id": gate_id,
            "severity": gate.get("severity"),
            "owner": gate.get("owner"),
            "passed": passed,
            "failure_message": gate.get("failure_message"),
            "remediation_reference": gate.get("remediation_reference"),
            "outcome": outcome,
        })
    payload = {
        "manifest_id": manifest.get("manifest_id"),
        "manifest_version": manifest.get("schema_version"),
        "target": args.target,
        "decision": "fail" if failed else "pass",
        "dependency_manifest_hash": compute_dependency_manifest_hash(REPO_ROOT),
        "migration_manifest_hash": compute_migration_manifest_hash(REPO_ROOT),
        "release_gate_manifest_hash": compute_release_gate_manifest_hash(REPO_ROOT),
        "gates": gates,
    }
    print(json.dumps(payload, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())