from __future__ import annotations

import hashlib
import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from lib.release_identity import parse_frontend_build_identity_text as canonical_parse_frontend_build_identity_text

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
    "performance_baseline": "docs/performance/performance_baseline.json",
    "performance_evidence": "docs/performance/ATLAS_ALERT_EVIDENCE_REGISTER.md",
}

_STATUS_LINE_RE = re.compile(
    r"^(?P<index>.)(?P<worktree>.)(?:\s+)(?P<path>.+?)(?:\s+->\s+(?P<renamed_to>.+))?$"
)


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


def _status_code_to_label(code: str) -> Optional[str]:
    mapping = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "U": "unmerged",
        "T": "type_changed",
        "?": "untracked",
        "!": "ignored",
        " ": None,
    }
    return mapping.get(code, "unknown")


def parse_git_status_line(raw_line: str) -> dict[str, Any]:
    line = (raw_line or "").rstrip("\n")
    if not line:
        return {
            "raw": raw_line,
            "path": "",
            "path_display": "",
            "index_status": None,
            "worktree_status": None,
            "change_labels": [],
            "renamed_from": None,
            "renamed_to": None,
            "parse_error": "empty status line",
        }
    if line.startswith("?? "):
        path = line[3:].strip()
        return {
            "raw": raw_line,
            "path": path,
            "path_display": path,
            "index_status": None,
            "worktree_status": "?",
            "change_labels": ["untracked"],
            "renamed_from": None,
            "renamed_to": None,
            "parse_error": None,
        }
    if len(line) >= 3 and line[1] == " ":
        path = line[2:].strip()
        label = _status_code_to_label(line[0])
        return {
            "raw": raw_line,
            "path": path,
            "path_display": path,
            "index_status": None,
            "worktree_status": line[0],
            "change_labels": [label] if label else [],
            "renamed_from": None,
            "renamed_to": None,
            "parse_error": None,
        }
    match = _STATUS_LINE_RE.match(line)
    if not match:
        return {
            "raw": raw_line,
            "path": line[3:].strip() if len(line) > 3 else line.strip(),
            "path_display": line,
            "index_status": None,
            "worktree_status": None,
            "change_labels": ["unknown"],
            "renamed_from": None,
            "renamed_to": None,
            "parse_error": "unparseable git status line",
        }
    renamed_from = (match.group("path") or "").strip()
    renamed_to = (match.group("renamed_to") or "").strip() or None
    final_path = renamed_to or renamed_from
    labels = []
    for code in (match.group("index"), match.group("worktree")):
        label = _status_code_to_label(code)
        if label and label not in labels:
            labels.append(label)
    return {
        "raw": raw_line,
        "path": final_path,
        "path_display": final_path,
        "index_status": match.group("index"),
        "worktree_status": match.group("worktree"),
        "change_labels": labels,
        "renamed_from": renamed_from if renamed_to else None,
        "renamed_to": renamed_to,
        "parse_error": None,
    }


def evaluate_pre_save_candidate(snapshot: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    policy = manifest.get("pre_save_candidate_policy") or {}
    tracked_entries = policy.get("allowed_dirty_entries") or []
    tracked_by_path: dict[str, dict[str, Any]] = {}
    tracked_patterns: list[dict[str, Any]] = []
    inventory_errors: list[str] = []
    for entry in tracked_entries:
        path = str((entry or {}).get("path") or "").strip()
        path_pattern = str((entry or {}).get("path_pattern") or "").strip()
        mission = str((entry or {}).get("mission_ref") or "").strip()
        rationale = str((entry or {}).get("rationale") or "").strip()
        if not path and not path_pattern:
            inventory_errors.append("pre_save_candidate_policy contains an entry with no path or path_pattern")
            continue
        if not mission or not rationale:
            inventory_errors.append(f"pre_save_candidate_policy entry {(path or path_pattern)} is missing mission_ref or rationale")
            continue
        if path:
            if path in tracked_by_path:
                inventory_errors.append(f"pre_save_candidate_policy duplicates path {path}")
                continue
            tracked_by_path[path] = {
                "path": path,
                "mission_ref": mission,
                "rationale": rationale,
            }
        else:
            tracked_patterns.append({
                "path_pattern": path_pattern,
                "mission_ref": mission,
                "rationale": rationale,
            })

    parsed_files = [parse_git_status_line(line) for line in (snapshot.get("status_lines") or [])]
    unknown_files: list[dict[str, Any]] = []
    matched_files: list[dict[str, Any]] = []
    parse_failures = [item for item in parsed_files if item.get("parse_error")]

    for item in parsed_files:
        path = str(item.get("path") or "").strip()
        if not path:
            unknown_files.append(item)
            continue
        governed = tracked_by_path.get(path)
        if governed is None:
            for entry in tracked_patterns:
                pattern = str(entry.get("path_pattern") or "")
                if pattern and fnmatch.fnmatch(path, pattern):
                    governed = {
                        "path": path,
                        "path_pattern": pattern,
                        "mission_ref": entry.get("mission_ref"),
                        "rationale": entry.get("rationale"),
                    }
                    break
        if not governed:
            unknown_files.append(item)
            continue
        matched_files.append({**item, **governed})

    allowed = bool(policy.get("allow_dirty_workspace_for_certification"))
    classification = "DIRTY_UNGOVERNED"
    dirty_candidate_label = str(policy.get("classification_label") or "UNSAVED_FINAL_CANDIDATE").strip() or "UNSAVED_FINAL_CANDIDATE"
    passed = False
    errors = list(inventory_errors)
    if parse_failures:
        errors.extend(item["parse_error"] for item in parse_failures if item.get("parse_error"))
    if unknown_files:
        errors.append(
            "dirty workspace contains uninventoried files: "
            + ", ".join(sorted({str(item.get('path_display') or item.get('raw') or '<unknown>') for item in unknown_files}))
        )
    if not snapshot.get("dirty"):
        classification = "CLEAN_SHA"
        passed = True
    elif allowed and not errors and matched_files:
        classification = dirty_candidate_label
        passed = True

    return {
        "policy_enabled": allowed,
        "classification": classification,
        "passed": passed,
        "deployable_clean_sha_required": bool(policy.get("deployed_source_must_be_clean_sha")),
        "dirty_file_count": len(parsed_files),
        "dirty_inventory": matched_files,
        "unknown_dirty_files": unknown_files,
        "errors": errors,
    }


def evaluate_workspace_state_source_authority(
    snapshot: dict[str, Any],
    manifest: dict[str, Any],
    *,
    target: str,
) -> dict[str, Any]:
    deployment = manifest.get("deployment_source_authority") or {}
    workspace_source_key = f"{target}_source"
    workspace_state = str(deployment.get(workspace_source_key) or "").strip() == "workspace_state"
    head = str(snapshot.get("head") or "").strip()
    branch = str(snapshot.get("branch") or "").strip()
    dirty = bool(snapshot.get("dirty"))
    emergent_identity = snapshot.get("emergent_workspace_identity") or {}
    has_emergent_identity = isinstance(emergent_identity, dict) and bool(emergent_identity)
    detached_clean_sha = workspace_state and not branch and bool(head) and not dirty
    deployable_clean_sha_required = bool((manifest.get("pre_save_candidate_policy") or {}).get("deployed_source_must_be_clean_sha"))
    passed = detached_clean_sha and has_emergent_identity and deployable_clean_sha_required
    reason = None
    if not passed:
        if not workspace_state:
            reason = f"{workspace_source_key}_not_workspace_state"
        elif branch:
            reason = "branch_present_standard_governance_applies"
        elif not head:
            reason = "git_head_unavailable"
        elif dirty:
            reason = "workspace_dirty"
        elif not has_emergent_identity:
            reason = "emergent_workspace_identity_missing"
        elif not deployable_clean_sha_required:
            reason = "clean_sha_requirement_not_enabled"
        else:
            reason = "detached_workspace_state_unproven"
    return {
        "passed": passed,
        "classification": "DETACHED_WORKSPACE_STATE_CLEAN_SHA" if passed else "NOT_APPLICABLE",
        "reason": reason,
        "details": {
            "target": target,
            "workspace_source_key": workspace_source_key,
            "workspace_state": workspace_state,
            "head": head or None,
            "branch": branch or None,
            "dirty": dirty,
            "has_emergent_workspace_identity": has_emergent_identity,
            "deployable_clean_sha_required": deployable_clean_sha_required,
        },
    }


def workflow_inventory(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not WORKFLOW_ROOT.exists():
        return rows
    for path in sorted(WORKFLOW_ROOT.glob("*.yml")):
        raw = _read(path)
        if yaml is not None:
            parsed = yaml.safe_load(raw) or {}
            on_block = parsed.get("on") if "on" in parsed else parsed.get(True)
            name = parsed.get("name")
            triggers = sorted((on_block or {}).keys()) if isinstance(on_block, dict) else []
        else:
            parsed = {}
            name_match = re.search(r"^name:\s*(.+)$", raw, re.MULTILINE)
            name = name_match.group(1).strip() if name_match else None
            triggers = []
            if re.search(r"^\s*push:\s*$", raw, re.MULTILINE):
                triggers.append("push")
            if re.search(r"^\s*pull_request:\s*$", raw, re.MULTILINE):
                triggers.append("pull_request")
            if re.search(r"^\s*workflow_dispatch:\s*$", raw, re.MULTILINE):
                triggers.append("workflow_dispatch")
        rows.append(
            {
                "path": str(path.relative_to(repo_root)),
                "name": name,
                "triggers": triggers,
                "continue_on_error_present": "continue-on-error: true" in raw,
                "uses_manifest_gate": "release_gate.py" in raw,
            }
        )
    return rows


def validate_workflows(repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
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
    perf = manifest.get("performance_prerequisites") or {}
    for key in (
        "authority_route",
        "machine_readable_baseline",
        "query_inventory",
        "atlas_evidence_register",
        "index_query_recommendation_register",
        "safe_self_healing_contract",
        "regression_thresholds",
    ):
        if key not in perf:
            errors.append(f"performance_prerequisites missing {key}")
    for rel_path in (
        perf.get("authority_route"),
        perf.get("machine_readable_baseline"),
        perf.get("query_inventory"),
        perf.get("atlas_evidence_register"),
        perf.get("index_query_recommendation_register"),
        perf.get("safe_self_healing_contract"),
    ):
        if rel_path and not (repo_root / rel_path).exists():
            errors.append(f"performance authority missing {rel_path}")
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
    return canonical_parse_frontend_build_identity_text(text)


def read_frontend_build_identity(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    path = repo_root / "frontend" / "src" / "buildVersion.generated.js"
    if not path.exists():
        return {}
    return parse_frontend_build_identity_text(_read(path))