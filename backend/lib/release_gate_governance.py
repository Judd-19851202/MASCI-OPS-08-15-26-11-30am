from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
POST_DEPLOY_SCHEMA_PATH = REPO_ROOT / "docs" / "recovery" / "POST_DEPLOY_CERTIFICATE_SCHEMA.json"
DEPENDENCY_MANIFEST_RELATIVE_PATHS = [
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/yarn.lock",
]

REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "manifest_id",
    "owner",
    "repository",
    "governed_branches",
    "release_identity_files",
    "mandatory_checks",
    "test_groups",
    "build_commands",
    "clean_install_commands",
    "source_exclusions",
    "secret_scan_contract",
    "runtime_identity_contract",
    "database_authority_contract",
    "dependency_authority_contract",
    "backup_dr_prerequisites",
    "performance_prerequisites",
    "preview_acceptance_gates",
    "production_acceptance_gates",
    "rollback_gates",
    "post_deploy_probes",
    "stop_conditions",
    "severity_rules",
    "expiration_review_date",
    "evidence_artifacts",
    "deployment_source_authority",
    "one_body_authorities",
}

REQUIRED_GATE_KEYS = {
    "gate_id",
    "description",
    "command_or_verifier",
    "execution_environment",
    "blocking_status",
    "timeout_seconds",
    "evidence_output",
    "owner",
    "failure_action",
    "applicability",
    "dependencies",
    "severity",
    "failure_message",
    "remediation_reference",
}

ONE_BODY_REQUIRED_AUTHORITIES = {
    "runtime_identity": "backend/lib/runtime_identity.py",
    "database_authority": "backend/lib/database_authority.py",
    "dependency_authority": "docs/governance/dependency_inventory.json",
    "trust_spine": "backend/lib/trust_spine.py",
    "backup_recovery": "backend/routes/recovery_dashboard.py",
    "deployment": "scripts/release_gate.py",
    "runtime_health": "backend/lib/runtime_reliability.py",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _stable_digest(repo_root: Path, relative_paths: list[str]) -> str:
    hasher = hashlib.sha256()
    for rel in relative_paths:
        rel_clean = rel.strip().replace("\\", "/")
        hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
        abs_path = repo_root / rel_clean
        if abs_path.exists():
            hasher.update(abs_path.read_bytes())
        else:
            hasher.update(b"MISSING:")
            hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def compute_dependency_manifest_hash(repo_root: Path = REPO_ROOT) -> str:
    return _stable_digest(repo_root, DEPENDENCY_MANIFEST_RELATIVE_PATHS)


def compute_migration_manifest_hash(repo_root: Path = REPO_ROOT) -> str:
    return _stable_digest(repo_root, ["docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md"])


def compute_release_gate_manifest_hash(repo_root: Path = REPO_ROOT) -> str:
    return _stable_digest(repo_root, ["docs/governance/release_gate_manifest.json"])


def load_release_gate_manifest(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads(_read(repo_root / "docs" / "governance" / "release_gate_manifest.json"))


def collect_git_snapshot(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    def _run(*args: str) -> str:
        try:
            return subprocess.check_output(args, cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True).strip()
        except Exception:
            return ""

    status = _run("git", "status", "--short")
    try:
        emergent = json.loads(_read(repo_root / ".emergent" / "emergent.yml"))
    except Exception:
        emergent = None
    return {
        "workspace": str(repo_root),
        "repository_root": _run("git", "rev-parse", "--show-toplevel") or str(repo_root),
        "branch": _run("git", "branch", "--show-current"),
        "head": _run("git", "rev-parse", "HEAD"),
        "upstream": _run("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
        "dirty": bool(status.strip()),
        "status_lines": [line for line in status.splitlines() if line.strip()],
        "remote_configuration": [line for line in _run("git", "remote", "-v").splitlines() if line.strip()],
        "emergent_workspace_identity": emergent,
    }


def workflow_inventory(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not WORKFLOW_ROOT.exists() or yaml is None:
        return rows
    for path in sorted(WORKFLOW_ROOT.glob("*.yml")):
        raw = _read(path)
        parsed = yaml.safe_load(raw)
        on_block = parsed.get("on") if "on" in parsed else parsed.get(True)
        rows.append(
            {
                "path": str(path.relative_to(repo_root)),
                "name": parsed.get("name"),
                "triggers": sorted((on_block or {}).keys()) if isinstance(on_block, dict) else [],
                "continue_on_error_present": "continue-on-error: true" in raw,
                "uses_manifest_gate": "release_gate.py" in raw,
            }
        )
    return rows


def validate_workflows(repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    if yaml is None:
        return ["PyYAML unavailable"]
    for row in workflow_inventory(repo_root):
        if row["continue_on_error_present"]:
            errors.append(f"workflow {row['path']} uses continue-on-error")
    return errors


def one_body_contract_failures(manifest: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[str]:
    failures: list[str] = []
    actual = manifest.get("one_body_authorities") or {}
    for key, expected in ONE_BODY_REQUIRED_AUTHORITIES.items():
        if actual.get(key) != expected:
            failures.append(f"{key} expected {expected} got {actual.get(key)}")
        if not (repo_root / expected).exists():
            failures.append(f"missing authority file {expected}")
    return failures


def validate_release_gate_manifest(manifest: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_MANIFEST_KEYS - set(manifest.keys()))
    if missing:
        errors.append(f"missing manifest keys: {', '.join(missing)}")
    gates = manifest.get("mandatory_checks") or []
    if not isinstance(gates, list) or not gates:
        errors.append("mandatory_checks must be non-empty")
        return errors
    gate_ids: list[str] = []
    for gate in gates:
        missing_gate = sorted(REQUIRED_GATE_KEYS - set(gate.keys()))
        if missing_gate:
            errors.append(f"gate {gate.get('gate_id')} missing keys: {', '.join(missing_gate)}")
        gate_id = str(gate.get("gate_id") or "")
        if gate_id:
            gate_ids.append(gate_id)
        if not gate.get("owner"):
            errors.append(f"gate {gate_id or '<missing>'} has no owner")
    dupes = sorted({gid for gid in gate_ids if gate_ids.count(gid) > 1})
    if dupes:
        errors.append(f"duplicate gate ids: {', '.join(dupes)}")
    gate_id_set = set(gate_ids)
    for gate in gates:
        gid = str(gate.get("gate_id") or "")
        for dep in gate.get("dependencies") or []:
            if dep not in gate_id_set:
                errors.append(f"gate {gid} depends on unknown gate id {dep}")
    preview = set(manifest.get("preview_acceptance_gates") or [])
    production = set(manifest.get("production_acceptance_gates") or [])
    missing_preview_gate_ids = sorted(preview - gate_id_set)
    missing_production_gate_ids = sorted(production - gate_id_set)
    if missing_preview_gate_ids:
        errors.append(f"preview acceptance gates missing definitions: {', '.join(missing_preview_gate_ids)}")
    if missing_production_gate_ids:
        errors.append(f"production acceptance gates missing definitions: {', '.join(missing_production_gate_ids)}")
    if not production > preview:
        errors.append("production acceptance gates must be strictly stronger than preview")
    backup = manifest.get("backup_dr_prerequisites") or {}
    for key in (
        "latest_scheduled_backup_completed_successfully",
        "r2_destination_reachable",
        "restore_metadata_present",
        "backup_integrity_hash_verification_passed",
        "restore_drill_certification_current",
        "no_backup_job_currently_failing",
    ):
        if key not in backup:
            errors.append(f"backup_dr_prerequisites missing {key}")
    schema_path = repo_root / POST_DEPLOY_SCHEMA_PATH.relative_to(REPO_ROOT)
    if not schema_path.exists():
        errors.append("post-deploy certificate schema missing")
    else:
        try:
            schema = json.loads(_read(schema_path))
            props = ((schema.get("items") or {}).get("properties") or {})
            required = set((schema.get("items") or {}).get("required") or [])
            for field in ("probe_id", "timestamp", "environment", "source_sha", "result", "evidence", "blocker_severity"):
                if field not in props or field not in required:
                    errors.append(f"post-deploy schema missing {field}")
        except Exception as exc:
            errors.append(f"invalid post-deploy schema: {exc}")
    return errors


def parse_frontend_build_identity_text(text: str) -> dict[str, Any]:
    patterns = {
        "version": r'BUILD_VERSION\s*=\s*"([^"]+)"',
        "commit": r'BUILD_COMMIT\s*=\s*"([^"]+)"',
        "built_at": r'BUILT_AT_ISO\s*=\s*"([^"]+)"',
        "source_hash": r'BUILD_SOURCE_HASH\s*=\s*"([^"]+)"',
        "dependency_manifest_hash": r'BUILD_DEPENDENCY_MANIFEST_HASH\s*=\s*"([^"]+)"',
        "migration_manifest_hash": r'BUILD_MIGRATION_MANIFEST_HASH\s*=\s*"([^"]+)"',
        "release_gate_manifest_hash": r'RELEASE_GATE_MANIFEST_HASH\s*=\s*"([^"]+)"',
        "release_gate_manifest_version": r'RELEASE_GATE_MANIFEST_VERSION\s*=\s*"([^"]+)"',
        "release_gate_manifest_id": r'RELEASE_GATE_MANIFEST_ID\s*=\s*"([^"]+)"',
        "repository": r'BUILD_REPOSITORY\s*=\s*"([^"]+)"',
        "branch": r'BUILD_BRANCH\s*=\s*"([^"]+)"',
        "workspace_dirty": r'BUILD_WORKSPACE_DIRTY\s*=\s*(true|false)',
    }
    out: dict[str, Any] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            out[key] = value if key != "workspace_dirty" else value == "true"
    return out


def read_frontend_build_identity(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    path = repo_root / "frontend" / "src" / "buildVersion.generated.js"
    if not path.exists():
        return {}
    return parse_frontend_build_identity_text(_read(path))