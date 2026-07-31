from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


RUNTIME_ROOTS = [
    "backend/server.py",
    "backend/routes",
    "backend/services",
    "backend/lib",
]

DISCOVERY_ROOTS = [
    "backend/server.py",
    "backend/routes",
    "backend/services",
    "backend/lib",
    "backend/operational_intelligence",
    "backend/tools",
    "backend/scripts",
    "backend/tests",
    "scripts",
    "tests",
]


def _iter_python_files(repo_root: Path, roots: Iterable[str]) -> Iterable[Path]:
    for rel in roots:
        root = repo_root / rel
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        for path in root.rglob("*.py"):
            yield path


def _is_runtime_file(rel_path: str) -> bool:
    return rel_path == "backend/server.py" or rel_path.startswith("backend/routes/") or rel_path.startswith("backend/services/") or rel_path.startswith("backend/lib/")


def _stable_id(rel_path: str, line: int, occurrence_type: str) -> str:
    raw = f"{rel_path}:{line}:{occurrence_type}"
    return f"dbc-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def _file_owner(rel_path: str) -> str:
    if rel_path == "backend/server.py":
        return "Platform Runtime"
    if rel_path.startswith("backend/routes/"):
        return "Route Owner"
    if rel_path.startswith("backend/services/"):
        return "Service Owner"
    if rel_path.startswith("backend/lib/"):
        return "Platform Library"
    if "/tests/" in rel_path or rel_path.startswith("backend/tests/"):
        return "Test Owner"
    return "Operator/Tooling"


def _classification(rel_path: str, symbol: str, occurrence_type: str) -> str:
    if rel_path == "backend/server.py" and symbol == "AsyncIOMotorClient":
        return "CANONICAL_RUNTIME_CLIENT"
    if rel_path == "backend/server.py" and symbol == "_MC":
        return "APPROVED_BACKUP_RESTORE_CLIENT"
    if rel_path == "backend/server.py" and occurrence_type == "database_handle_consumer":
        return "CANONICAL_RUNTIME_DATABASE_HANDLE"
    if rel_path == "backend/lib/identity_lookup_sync.py":
        return "APPROVED_SYNC_RUNTIME_HELPER"
    if rel_path == "backend/lib/async_jobs.py" and symbol == "AsyncIOMotorClient":
        return "APPROVED_SYNC_RUNTIME_HELPER"
    if rel_path.startswith("backend/operational_intelligence/"):
        return "CANONICAL_RUNTIME_DATABASE_HANDLE"
    if rel_path.startswith("backend/tools/"):
        name = Path(rel_path).name.lower()
        if "restore" in name:
            return "APPROVED_BACKUP_RESTORE_CLIENT"
        if any(token in name for token in ("rewrite", "migrate", "backfill", "seed")):
            return "OPERATOR_TOOL_CLIENT"
        return "READ_ONLY_DIAGNOSTIC_CLIENT"
    if rel_path.startswith("backend/tests/") or rel_path.startswith("tests/"):
        return "TEST_FIXTURE_CLIENT"
    if rel_path.startswith("backend/scripts/") or rel_path.startswith("scripts/"):
        name = Path(rel_path).name.lower()
        if any(token in name for token in ("restore", "drill", "rollback", "backup")):
            return "APPROVED_BACKUP_RESTORE_CLIENT"
        if any(token in name for token in ("seed", "migrate", "backfill")):
            return "MIGRATION_CLIENT"
        if any(token in name for token in ("verify", "probe", "audit", "inventory", "simulation", "scan")):
            return "READ_ONLY_DIAGNOSTIC_CLIENT"
        return "OPERATOR_TOOL_CLIENT"
    if rel_path.startswith("backend/routes/") or rel_path.startswith("backend/services/") or rel_path.startswith("backend/lib/"):
        if occurrence_type == "client_constructor":
            return "DUPLICATE_RUNTIME_CLIENT"
        return "CANONICAL_RUNTIME_DATABASE_HANDLE"
    return "UNKNOWN_DO_NOT_TOUCH"


def _risk(classification: str, rel_path: str) -> str:
    if classification in {"DUPLICATE_RUNTIME_CLIENT", "REQUEST_SCOPED_CLIENT_DEFECT", "UNSAFE_FALLBACK_CLIENT", "UNOWNED_CLIENT"}:
        return "P0"
    if classification in {"CANONICAL_RUNTIME_CLIENT", "CANONICAL_RUNTIME_DATABASE_HANDLE", "APPROVED_SYNC_RUNTIME_HELPER"}:
        return "P1"
    if classification in {"READ_ONLY_DIAGNOSTIC_CLIENT", "APPROVED_BACKUP_RESTORE_CLIENT", "OPERATOR_TOOL_CLIENT", "MIGRATION_CLIENT", "TEST_FIXTURE_CLIENT"}:
        return "P2"
    if rel_path.startswith("backend/routes/"):
        return "P1"
    return "P3"


def _status(classification: str) -> str:
    if classification in {"DUPLICATE_RUNTIME_CLIENT", "REQUEST_SCOPED_CLIENT_DEFECT", "UNSAFE_FALLBACK_CLIENT", "UNOWNED_CLIENT"}:
        return "REMEDIATION_REQUIRED"
    if classification == "UNKNOWN_DO_NOT_TOUCH":
        return "MANUAL_REVIEW_REQUIRED"
    return "GOVERNED"


def _read_write_authority(rel_path: str, classification: str) -> str:
    if classification == "READ_ONLY_DIAGNOSTIC_CLIENT":
        return "READ_ONLY"
    if classification == "APPROVED_BACKUP_RESTORE_CLIENT":
        return "OPERATOR_CONTROLLED"
    if classification == "MIGRATION_CLIENT":
        return "OPERATOR_CONTROLLED"
    if classification == "TEST_FIXTURE_CLIENT":
        return "READ_WRITE"
    if rel_path == "backend/lib/identity_lookup_sync.py":
        return "READ_ONLY"
    return "READ_WRITE"


def _env_restrictions(rel_path: str, classification: str) -> str:
    if classification == "CANONICAL_RUNTIME_CLIENT":
        return "Runtime Identity enforced fail-closed"
    if classification == "APPROVED_SYNC_RUNTIME_HELPER":
        return "Consumes canonical runtime identity and database authority"
    if classification == "TEST_FIXTURE_CLIENT":
        return "Test-only"
    if rel_path.startswith("backend/scripts/") or rel_path.startswith("scripts/"):
        return "Operator-controlled script scope"
    return "Bound to canonical runtime injection"


def _creation_frequency(classification: str, occurrence_type: str) -> str:
    if classification == "CANONICAL_RUNTIME_CLIENT":
        return "Once per process lifecycle"
    if classification == "APPROVED_SYNC_RUNTIME_HELPER":
        return "Lazy singleton per helper"
    if classification == "TEST_FIXTURE_CLIENT":
        return "Per test/fixture"
    if occurrence_type == "database_handle_consumer":
        return "Per route/service invocation via injected handle"
    return "Per tool/script invocation"


def _close_behavior(rel_path: str, classification: str) -> str:
    if classification == "CANONICAL_RUNTIME_CLIENT":
        return "Closed by shutdown_db_client exactly once"
    if rel_path == "backend/lib/identity_lookup_sync.py":
        return "Closed via database_authority sync-helper shutdown"
    if classification == "TEST_FIXTURE_CLIENT":
        return "Fixture/test managed"
    if rel_path.startswith("backend/scripts/") or rel_path.startswith("scripts/"):
        return "Script-owned / explicit close expected"
    return "No client constructed here"


def discover_database_client_inventory(repo_root: str = "/app") -> List[Dict[str, Any]]:
    repo = Path(repo_root)
    rows: List[Dict[str, Any]] = []
    for path in _iter_python_files(repo, DISCOVERY_ROOTS):
        rel_path = str(path.relative_to(repo))
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        function_stack: List[ast.AST] = []

        class Visitor(ast.NodeVisitor):
            def generic_visit(self, node: ast.AST) -> None:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    function_stack.append(node)
                    super().generic_visit(node)
                    function_stack.pop()
                else:
                    super().generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in {"AsyncIOMotorClient", "MongoClient", "get_database"} or (rel_path == "backend/lib/database_authority.py" and name == "client_factory"):
                    owner = function_stack[-1].name if function_stack else "<module>"
                    occurrence_type = "client_constructor" if name != "get_database" else "connection_factory"
                    client_type = "AsyncIOMotorClient" if owner == "create_async_runtime_client" and name == "client_factory" else "MongoClient" if owner == "build_sync_helper_client" and name == "client_factory" else name
                    classification = (
                        "CANONICAL_RUNTIME_CLIENT"
                        if rel_path == "backend/lib/database_authority.py" and owner == "create_async_runtime_client"
                        else "APPROVED_SYNC_RUNTIME_HELPER"
                        if rel_path == "backend/lib/database_authority.py" and owner == "build_sync_helper_client"
                        else _classification(rel_path, name, occurrence_type)
                    )
                    rows.append({
                        "stable_id": _stable_id(rel_path, node.lineno, occurrence_type),
                        "occurrence_type": occurrence_type,
                        "file": rel_path,
                        "line": node.lineno,
                        "function_class_module": owner,
                        "client_type": client_type,
                        "async_sync": "async" if client_type == "AsyncIOMotorClient" else "sync",
                        "runtime_or_non_runtime": "runtime" if _is_runtime_file(rel_path) else "non_runtime",
                        "connection_source": "canonical_database_authority" if classification in {"CANONICAL_RUNTIME_CLIENT", "APPROVED_SYNC_RUNTIME_HELPER"} else "local_env_or_tooling",
                        "database_source": "canonical_runtime_identity" if classification in {"CANONICAL_RUNTIME_CLIENT", "CANONICAL_RUNTIME_DATABASE_HANDLE", "APPROVED_SYNC_RUNTIME_HELPER"} else "local_env_or_tooling",
                        "lifecycle_owner": _file_owner(rel_path),
                        "creation_frequency": _creation_frequency(classification, occurrence_type),
                        "close_behavior": _close_behavior(rel_path, classification),
                        "runtime_identity_integration": "YES" if classification in {"CANONICAL_RUNTIME_CLIENT", "CANONICAL_RUNTIME_DATABASE_HANDLE", "APPROVED_SYNC_RUNTIME_HELPER"} else "NO",
                        "environment_restrictions": _env_restrictions(rel_path, classification),
                        "read_write_authority": _read_write_authority(rel_path, classification),
                        "classification": classification,
                        "status_classification": _status(classification),
                        "risk": _risk(classification, rel_path),
                        "owner": _file_owner(rel_path),
                        "tests": [],
                        "disposition": "Retain under governance" if classification not in {"DUPLICATE_RUNTIME_CLIENT", "REQUEST_SCOPED_CLIENT_DEFECT", "UNSAFE_FALLBACK_CLIENT", "UNOWNED_CLIENT"} else "Remediate",
                    })
                elif name == "_MC":
                    owner = function_stack[-1].name if function_stack else "<module>"
                    occurrence_type = "client_constructor"
                    classification = _classification(rel_path, name, occurrence_type)
                    rows.append({
                        "stable_id": _stable_id(rel_path, node.lineno, occurrence_type),
                        "occurrence_type": occurrence_type,
                        "file": rel_path,
                        "line": node.lineno,
                        "function_class_module": owner,
                        "client_type": "MongoClient",
                        "async_sync": "sync",
                        "runtime_or_non_runtime": "runtime" if _is_runtime_file(rel_path) else "non_runtime",
                        "connection_source": "canonical_database_authority" if classification in {"CANONICAL_RUNTIME_CLIENT", "APPROVED_SYNC_RUNTIME_HELPER", "APPROVED_BACKUP_RESTORE_CLIENT"} else "local_env_or_tooling",
                        "database_source": "canonical_runtime_identity" if classification in {"CANONICAL_RUNTIME_CLIENT", "CANONICAL_RUNTIME_DATABASE_HANDLE", "APPROVED_SYNC_RUNTIME_HELPER", "APPROVED_BACKUP_RESTORE_CLIENT"} else "local_env_or_tooling",
                        "lifecycle_owner": _file_owner(rel_path),
                        "creation_frequency": _creation_frequency(classification, occurrence_type),
                        "close_behavior": _close_behavior(rel_path, classification),
                        "runtime_identity_integration": "YES" if classification in {"CANONICAL_RUNTIME_CLIENT", "CANONICAL_RUNTIME_DATABASE_HANDLE", "APPROVED_SYNC_RUNTIME_HELPER", "APPROVED_BACKUP_RESTORE_CLIENT"} else "NO",
                        "environment_restrictions": _env_restrictions(rel_path, classification),
                        "read_write_authority": _read_write_authority(rel_path, classification),
                        "classification": classification,
                        "status_classification": _status(classification),
                        "risk": _risk(classification, rel_path),
                        "owner": _file_owner(rel_path),
                        "tests": [],
                        "disposition": "Retain under governance" if classification not in {"DUPLICATE_RUNTIME_CLIENT", "REQUEST_SCOPED_CLIENT_DEFECT", "UNSAFE_FALLBACK_CLIENT", "UNOWNED_CLIENT"} else "Remediate",
                    })
                self.generic_visit(node)

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._visit_fn(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._visit_fn(node)

            def _visit_fn(self, node: ast.AST) -> None:
                args = getattr(getattr(node, "args", None), "args", [])
                if any(getattr(arg, "arg", None) == "db" for arg in args):
                    name = getattr(node, "name", "<callable>")
                    classification = _classification(rel_path, "db", "database_handle_consumer")
                    rows.append({
                        "stable_id": _stable_id(rel_path, node.lineno, "database_handle_consumer"),
                        "occurrence_type": "database_handle_consumer",
                        "file": rel_path,
                        "line": node.lineno,
                        "function_class_module": name,
                        "client_type": "database_handle",
                        "async_sync": "async" if isinstance(node, ast.AsyncFunctionDef) else "sync",
                        "runtime_or_non_runtime": "runtime" if _is_runtime_file(rel_path) else "non_runtime",
                        "connection_source": "injected_handle",
                        "database_source": "canonical_runtime_identity" if _is_runtime_file(rel_path) else "test_or_tool_injected",
                        "lifecycle_owner": _file_owner(rel_path),
                        "creation_frequency": _creation_frequency(classification, "database_handle_consumer"),
                        "close_behavior": _close_behavior(rel_path, classification),
                        "runtime_identity_integration": "YES" if _is_runtime_file(rel_path) else "NO",
                        "environment_restrictions": _env_restrictions(rel_path, classification),
                        "read_write_authority": _read_write_authority(rel_path, classification),
                        "classification": classification,
                        "status_classification": _status(classification),
                        "risk": _risk(classification, rel_path),
                        "owner": _file_owner(rel_path),
                        "tests": [],
                        "disposition": "Governed injection",
                    })
                self.generic_visit(node)

        Visitor().visit(tree)
    rows.sort(key=lambda row: (row["file"], row["line"], row["occurrence_type"]))
    return rows


def inventory_summary(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    client_rows = [row for row in rows if row["occurrence_type"] == "client_constructor"]
    return {
        "total_occurrences": len(rows),
        "total_clients": len(client_rows),
        "runtime": sum(1 for row in client_rows if row["runtime_or_non_runtime"] == "runtime"),
        "tool_migration": sum(1 for row in client_rows if row["classification"] in {"OPERATOR_TOOL_CLIENT", "MIGRATION_CLIENT", "APPROVED_BACKUP_RESTORE_CLIENT", "READ_ONLY_DIAGNOSTIC_CLIENT"}),
        "tests": sum(1 for row in client_rows if row["classification"] == "TEST_FIXTURE_CLIENT"),
        "async": sum(1 for row in client_rows if row["async_sync"] == "async"),
        "sync": sum(1 for row in client_rows if row["async_sync"] == "sync"),
        "duplicate": sum(1 for row in client_rows if row["classification"] == "DUPLICATE_RUNTIME_CLIENT"),
        "request_scoped": sum(1 for row in client_rows if row["classification"] == "REQUEST_SCOPED_CLIENT_DEFECT"),
        "unsafe": sum(1 for row in client_rows if row["classification"] == "UNSAFE_FALLBACK_CLIENT"),
        "unknown": sum(1 for row in client_rows if row["classification"] == "UNKNOWN_DO_NOT_TOUCH"),
    }


def render_register_markdown(rows: List[Dict[str, Any]]) -> str:
    client_rows = [row for row in rows if row["occurrence_type"] == "client_constructor"]
    lines = [
        "# DATABASE CLIENT AUTHORITY REGISTER",
        "",
        "Authoritative D3 governance record.",
        "",
        "## Client register",
        "",
        "| Client ID | Surface/Module | File | Runtime/Tool/Test | Async/Sync | Classification | Canonical Runtime Identity Consumer: YES/NO | Canonical Database Authority Consumer: YES/NO | Environment Decision Local: YES/NO | Database Decision Local: YES/NO | Read/Write Authority | Lifecycle Owner | Creation Frequency | Close Behavior | Approved Reason | Tests/Evidence | Owner | Status |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|",
    ]
    for row in client_rows:
        lines.append(
            "| {stable_id} | {function_class_module} | `{file}:{line}` | {runtime_or_non_runtime} | {async_sync} | {classification} | {rt} | {da} | {env_local} | {db_local} | {rwa} | {owner} | {freq} | {close} | {reason} | {tests} | {owner} | {status} |".format(
                stable_id=row["stable_id"],
                function_class_module=row["function_class_module"],
                file=row["file"],
                line=row["line"],
                runtime_or_non_runtime=row["runtime_or_non_runtime"],
                async_sync=row["async_sync"],
                classification=row["classification"],
                rt="YES" if row["runtime_identity_integration"] == "YES" else "NO",
                da="YES" if row["classification"] in {"CANONICAL_RUNTIME_CLIENT", "APPROVED_SYNC_RUNTIME_HELPER"} else ("YES" if row["classification"] == "TEST_FIXTURE_CLIENT" else "NO"),
                env_local="NO" if row["classification"] in {"CANONICAL_RUNTIME_CLIENT", "APPROVED_SYNC_RUNTIME_HELPER", "CANONICAL_RUNTIME_DATABASE_HANDLE"} else "YES",
                db_local="NO" if row["classification"] in {"CANONICAL_RUNTIME_CLIENT", "APPROVED_SYNC_RUNTIME_HELPER", "CANONICAL_RUNTIME_DATABASE_HANDLE"} else "YES",
                rwa=row["read_write_authority"],
                owner=row["lifecycle_owner"],
                freq=row["creation_frequency"],
                close=row["close_behavior"],
                reason=row["disposition"],
                tests=", ".join(row["tests"]) if row["tests"] else "D3 governance tests",
                status=row["status_classification"],
            )
        )
    lines.extend([
        "",
        "## Connection option register",
        "",
        "| Option | Current Value | Source/Default | Purpose | Environment Applicability | Risk | Recommended Status |",
        "|---|---|---|---|---|---|---|",
        "| serverSelectionTimeoutMS | 30000 | runtime env defaulted in canonical authority | bounded server selection | runtime + sync helper | low | KEEP |",
        "| connectTimeoutMS | 30000 | runtime env defaulted in canonical authority | bounded initial connect | runtime + sync helper | low | KEEP |",
        "| socketTimeoutMS | 30000 | runtime env defaulted in canonical authority | bounded socket wait | runtime + sync helper | low | KEEP |",
        "| retryReads | true | canonical authority | safe transient read retry | runtime + sync helper | low | KEEP |",
        "| retryWrites | runtime=true / sync-helper=false / ro-validation=false | canonical authority | avoid unsafe write retry in validation/helper paths | environment dependent | medium | KEEP |",
        "| maxPoolSize | 50 runtime / 10 sync helper | canonical authority | prevent unbounded growth | runtime + sync helper | medium | KEEP |",
        "| minPoolSize | not set | driver default | no proven defect | runtime + sync helper | low | NOT_APPLICABLE |",
        "| maxIdleTimeMS | not set | driver default | no production evidence yet | runtime + sync helper | low | NEEDS_PRODUCTION_EVIDENCE |",
        "| waitQueueTimeoutMS | not set | driver default | no proven lifecycle defect | runtime + sync helper | low | PERFORMANCE_TRACK_D7 |",
        "| appname | masci-runtime-authority / masci-sync-helper:* | canonical authority | traceability | runtime + sync helper | low | CHANGE_NOW |",
        "| TLS behavior | URI-driven | existing Mongo URI contract | preserve current transport semantics | runtime + sync helper | low | KEEP |",
        "| uuidRepresentation | standard | canonical authority | deterministic BSON UUID semantics | runtime + sync helper | low | CHANGE_NOW |",
        "| compressors | not set | driver default | no evidence to tune | runtime + sync helper | low | NOT_APPLICABLE |",
        "| readPreference | URI/driver default | existing URI contract | preserve known-good behavior | runtime + sync helper | medium | NEEDS_PRODUCTION_EVIDENCE |",
        "| writeConcern | URI/driver default | existing URI contract | preserve known-good behavior | runtime + sync helper | medium | NEEDS_PRODUCTION_EVIDENCE |",
        "| readConcern | driver default | existing driver default | no proven defect | runtime + sync helper | low | NOT_APPLICABLE |",
        "| heartbeatFrequencyMS | driver default | existing driver default | no proven defect | runtime + sync helper | low | PERFORMANCE_TRACK_D7 |",
        "| monitoring hooks | runtime lifecycle + state only | canonical authority | safe observability | runtime | low | KEEP |",
    ])
    return "\n".join(lines) + "\n"


def write_inventory_and_register(repo_root: str = "/app") -> Dict[str, Any]:
    repo = Path(repo_root)
    rows = discover_database_client_inventory(repo_root)
    inventory_path = repo / "docs/governance/database_client_inventory.json"
    register_path = repo / "docs/governance/DATABASE_CLIENT_AUTHORITY_REGISTER.md"
    inventory_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    register_path.write_text(render_register_markdown(rows), encoding="utf-8")
    return {
        "inventory_path": str(inventory_path),
        "register_path": str(register_path),
        "summary": inventory_summary(rows),
    }


__all__ = [
    "discover_database_client_inventory",
    "inventory_summary",
    "render_register_markdown",
    "write_inventory_and_register",
]