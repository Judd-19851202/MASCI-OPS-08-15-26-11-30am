#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
    validate_release_gate_manifest,
    validate_workflows,
)


def _run(cmd: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "duration_seconds": round(time.perf_counter() - started, 3),
    }


def _copy_repo() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="masci-release-gate-"))
    dst = tmp_root / "repo"
    ignore = shutil.ignore_patterns(
        ".git", ".emergent", "node_modules", "frontend/node_modules", "frontend/build", "__pycache__", ".pytest_cache", "deploy_reports", "test_reports", "walkthrough_reports"
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
    return {
        "python_version": _run(["python3", "--version"], cwd=repo, timeout=60),
        "clean_install": install,
        "compileall": compileall,
        "import_server": import_server,
        "verify_release_identity": verify,
        "python_dependency_count": count,
        "passed": bool(install["returncode"] == 0 and compileall and compileall["returncode"] == 0 and import_server and import_server["returncode"] == 0 and verify and verify["returncode"] == 0),
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
    install = _run(["yarn", "install", "--frozen-lockfile", "--ignore-scripts"], cwd=repo / "frontend", timeout=1800)
    build = _run(["yarn", "build"], cwd=repo / "frontend", timeout=1800) if install["returncode"] == 0 else None
    package_json = json.loads((repo / "frontend" / "package.json").read_text())
    metrics = _frontend_metrics(repo) if build and build["returncode"] == 0 else {}
    return {
        "node_version": _run(["node", "--version"], cwd=repo, timeout=60),
        "yarn_version": _run(["yarn", "--version"], cwd=repo, timeout=60),
        "clean_install": install,
        "build": build,
        "node_dependency_count": len(package_json.get("dependencies", {})) + len(package_json.get("devDependencies", {})),
        "passed": bool(build and build["returncode"] == 0),
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
        "python3", "-m", "pytest", "-q",
        "/app/backend/tests/test_runtime_identity_contract.py",
        "/app/backend/tests/test_checkpoint_d2_runtime_truth_normalization.py",
        "/app/backend/tests/test_checkpoint_d3_database_authority.py",
        "/app/backend/tests/test_checkpoint_d4_dependency_governance.py",
        "/app/backend/tests/test_checkpoint_d5_d6_release_gate.py",
        "/app/backend/tests/test_checkpoint_d7_d8_performance_repairs.py",
    ], cwd=REPO_ROOT, timeout=1800)


def _secret_scan() -> dict[str, Any]:
    return _run(["python3", "-m", "pytest", "-q", "/app/backend/tests/test_track_15_80_no_secrets_in_repo.py"], cwd=REPO_ROOT, timeout=900)


def _prd_lint() -> dict[str, Any]:
    return _run(["python3", "/app/scripts/lint-iteration-summary.py"], cwd=REPO_ROOT, timeout=120)


def _release_identity_verifier() -> dict[str, Any]:
    return _run(["python3", "/app/backend/scripts/verify_release_identity.py", "--strict"], cwd=REPO_ROOT, timeout=600)


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
    return {"returncode": 0 if not errors else 1, "errors": errors}


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
    baseline = payloads.get("machine_readable_baseline") or {}
    for field in ["checkpoint", "captured_at", "backend", "frontend", "scheduler", "workspace_resources"]:
        if field not in baseline:
            errors.append(f"performance baseline missing {field}")
    return {"returncode": 0 if not errors else 1, "errors": errors, "baseline": baseline}


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
    if not branch:
        errors.append("git branch unavailable")
    elif branch not in governed:
        errors.append(f"branch {branch} is not governed for {target}")
    if not head:
        errors.append("git HEAD unavailable")
    pre_save = evaluate_pre_save_candidate(snapshot, manifest)
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