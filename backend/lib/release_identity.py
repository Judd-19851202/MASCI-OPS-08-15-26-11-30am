from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from lib.release_fingerprint import build_release_manifest, load_contract


FRONTEND_BUILD_VERSION_FILE = Path("frontend/src/buildVersion.generated.js")
FRONTEND_PUBLIC_RELEASE_IDENTITY_FILE = Path("frontend/public/release-identity.json")
RELEASE_SCOPE_FILE = Path("docs/governance/release_content_fingerprint_contract.json")
DEPENDENCY_MANIFEST_RELATIVE_PATHS: Tuple[str, ...] = (
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/yarn.lock",
)
FRONTEND_IDENTITY_DEFAULT_MODE = "runtime-api-version"
FRONTEND_IDENTITY_DEFAULT_ENDPOINT = "/api/version"
_VERSION_LABEL_RE = re.compile(r'BUILD_VERSION_LABEL\s*=\s*"([^"]+)"')
_IDENTITY_MODE_RE = re.compile(r'BUILD_IDENTITY_MODE\s*=\s*"([^"]+)"')
_IDENTITY_ENDPOINT_RE = re.compile(r'BUILD_IDENTITY_ENDPOINT\s*=\s*"([^"]+)"')
_RUNTIME_BINDING_RE = re.compile(r'BUILD_RUNTIME_BINDING_REQUIRED\s*=\s*(true|false)')
_POST_SAVE_RE = re.compile(r'BUILD_POST_SAVE_SOURCE_MUTATION_REQUIRED\s*=\s*(true|false)')
_TRACKED_COMMIT_RE = re.compile(r'BUILD_TRACKED_COMMIT_EMBED_ALLOWED\s*=\s*(true|false)')
_MANIFEST_CACHE: Dict[str, Any] = {"key": None, "payload": None}


def collect_workspace_snapshot(repo_root: Path) -> Dict[str, Any]:
    def _run(*args: str) -> str:
        try:
            return subprocess.check_output(args, cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True).strip()
        except Exception:
            return ""

    status = _run("git", "status", "--porcelain=v1")
    lines = [line for line in status.splitlines() if line.strip()]
    return {
        "branch": _run("git", "branch", "--show-current"),
        "head": _run("git", "rev-parse", "HEAD"),
        "status_lines": lines,
        "dirty": bool(lines),
    }


def _stable_digest(repo_root: Path, relative_paths: Sequence[str]) -> str:
    hasher = hashlib.sha256()
    for rel in relative_paths:
        rel_clean = rel.strip().replace("\\", "/")
        hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
        path = repo_root / rel_clean
        if path.exists():
            hasher.update(path.read_bytes())
        else:
            hasher.update(b"MISSING:")
            hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def _status_path(line: str) -> str:
    return line[3:].strip() if len(line) >= 4 else line.strip()


def _path_state(repo_root: Path, rel_path: str) -> tuple[str, int, int]:
    path = repo_root / rel_path
    if not path.exists():
        return (rel_path, -1, -1)
    stat_result = path.stat()
    return (rel_path, int(stat_result.st_size), int(stat_result.st_mtime_ns))


def _manifest_cache_key(repo_root: Path, snapshot: Dict[str, Any]) -> tuple[Any, ...]:
    contract_path = repo_root / RELEASE_SCOPE_FILE
    contract_state = _path_state(repo_root, RELEASE_SCOPE_FILE.as_posix()) if contract_path.exists() else (RELEASE_SCOPE_FILE.as_posix(), -1, -1)
    status_lines = tuple(snapshot.get("status_lines") or [])
    changed_states = tuple(_path_state(repo_root, _status_path(line)) for line in status_lines)
    return (snapshot.get("head"), status_lines, changed_states, contract_state)


def _current_manifest(repo_root: Path) -> Dict[str, Any]:
    snapshot = collect_workspace_snapshot(repo_root)
    key = _manifest_cache_key(repo_root, snapshot)
    if _MANIFEST_CACHE.get("key") == key and isinstance(_MANIFEST_CACHE.get("payload"), dict):
        return _MANIFEST_CACHE["payload"]
    payload = build_release_manifest(repo_root)
    _MANIFEST_CACHE["key"] = key
    _MANIFEST_CACHE["payload"] = payload
    return payload


def compute_source_hash(repo_root: Path) -> str:
    return str(_current_manifest(repo_root)["manifest_sha256"])


def compute_dependency_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, list(DEPENDENCY_MANIFEST_RELATIVE_PATHS))


def compute_migration_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, ["docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md"])


def compute_release_gate_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, ["docs/governance/release_gate_manifest.json"])


def read_release_fingerprint_relative_paths(repo_root: Path) -> List[str]:
    return [row["path"] for row in _current_manifest(repo_root)["entries"]]


def build_fingerprint_paths(repo_root: Path) -> List[Path]:
    return [repo_root / rel for rel in read_release_fingerprint_relative_paths(repo_root)]


def workspace_candidate_identity(repo_root: Path, *, env: Optional[Dict[str, str]] = None) -> Tuple[str, str, Dict[str, Any]]:
    snapshot = collect_workspace_snapshot(repo_root)
    source_hash = compute_source_hash(repo_root)
    env_commit, env_source = _env_commit(env)
    if env_commit:
        return env_commit, env_source or "env", snapshot
    head = snapshot.get("head") or ""
    if head and not snapshot.get("dirty"):
        return head, "git:HEAD", snapshot
    if head:
        return f"UNSAVED_FINAL_CANDIDATE:{head}:{source_hash[:12]}", "workspace:unsaved_final_candidate", snapshot
    return f"UNSAVED_FINAL_CANDIDATE:UNPROVEN:{source_hash[:12]}", "workspace:unsaved_final_candidate", snapshot


def parse_frontend_build_identity_text(text: str) -> Dict[str, Any]:
    return {
        "version": (_VERSION_LABEL_RE.search(text or "") or [None])[1] if _VERSION_LABEL_RE.search(text or "") else None,
        "commit": None,
        "commit_source": None,
        "built_at": None,
        "source_hash": None,
        "dependency_manifest_hash": None,
        "migration_manifest_hash": None,
        "release_gate_manifest_hash": None,
        "release_gate_manifest_version": None,
        "release_gate_manifest_id": None,
        "repository": None,
        "branch": None,
        "workspace_dirty": None,
        "identity_mode": (_IDENTITY_MODE_RE.search(text or "") or [None])[1] if _IDENTITY_MODE_RE.search(text or "") else FRONTEND_IDENTITY_DEFAULT_MODE,
        "identity_endpoint": (_IDENTITY_ENDPOINT_RE.search(text or "") or [None])[1] if _IDENTITY_ENDPOINT_RE.search(text or "") else FRONTEND_IDENTITY_DEFAULT_ENDPOINT,
        "runtime_binding_required": ((_RUNTIME_BINDING_RE.search(text or "") or [None])[1] == "true") if _RUNTIME_BINDING_RE.search(text or "") else True,
        "post_save_source_mutation_required": ((_POST_SAVE_RE.search(text or "") or [None])[1] == "true") if _POST_SAVE_RE.search(text or "") else False,
        "tracked_commit_embed_allowed": ((_TRACKED_COMMIT_RE.search(text or "") or [None])[1] == "true") if _TRACKED_COMMIT_RE.search(text or "") else False,
        "source": "contract:frontend/src/buildVersion.generated.js",
    }


def read_frontend_build_identity(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / FRONTEND_BUILD_VERSION_FILE
    if not path.exists():
        return parse_frontend_build_identity_text("")
    return parse_frontend_build_identity_text(path.read_text(encoding="utf-8"))


def normalize_frontend_release_identity_payload(payload: Optional[Dict[str, Any]], *, source: str) -> Dict[str, Any]:
    data = payload or {}
    commit = data.get("commit") or None
    if isinstance(commit, str):
        commit = commit.strip().lower() or None
    return {
        "version": data.get("version") or data.get("build_version") or data.get("version_label") or None,
        "commit": commit,
        "commit_source": data.get("commit_source") or None,
        "built_at": data.get("built_at") or data.get("built_at_iso") or None,
        "source_hash": data.get("source_hash") or data.get("build_source_hash") or None,
        "dependency_manifest_hash": data.get("dependency_manifest_hash") or None,
        "migration_manifest_hash": data.get("migration_manifest_hash") or None,
        "release_gate_manifest_hash": data.get("release_gate_manifest_hash") or None,
        "release_gate_manifest_version": data.get("release_gate_manifest_version") or None,
        "release_gate_manifest_id": data.get("release_gate_manifest_id") or None,
        "repository": data.get("repository") or None,
        "branch": data.get("branch") or None,
        "workspace_dirty": data.get("workspace_dirty") if isinstance(data.get("workspace_dirty"), bool) else None,
        "identity_mode": data.get("identity_mode") or FRONTEND_IDENTITY_DEFAULT_MODE,
        "identity_endpoint": data.get("identity_endpoint") or FRONTEND_IDENTITY_DEFAULT_ENDPOINT,
        "runtime_binding_required": data.get("runtime_binding_required") if isinstance(data.get("runtime_binding_required"), bool) else True,
        "post_save_source_mutation_required": data.get("post_save_source_mutation_required") if isinstance(data.get("post_save_source_mutation_required"), bool) else False,
        "tracked_commit_embed_allowed": data.get("tracked_commit_embed_allowed") if isinstance(data.get("tracked_commit_embed_allowed"), bool) else False,
        "source": source,
    }


def read_frontend_public_identity(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / FRONTEND_PUBLIC_RELEASE_IDENTITY_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return normalize_frontend_release_identity_payload(None, source="missing")
    return normalize_frontend_release_identity_payload(
        payload if isinstance(payload, dict) else None,
        source="contract:frontend/public/release-identity.json",
    )


def _env_commit(env: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
    source = env or os.environ
    for var in (
        "DEPLOY_VERSION_HASH",
        "DEPLOY_VERSION",
        "GIT_COMMIT",
        "RAILWAY_GIT_COMMIT_SHA",
        "VERCEL_GIT_COMMIT_SHA",
    ):
        value = (source.get(var) or "").strip()
        if value:
            return value, f"env:{var}"
    return None, None


def _git_head_commit(repo_root: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None, None
    return (value or None), ("git:HEAD" if value else None)


def _git_commit_timestamp(repo_root: Path, commit: Optional[str]) -> Optional[str]:
    if not commit:
        return None
    try:
        value = subprocess.check_output(["git", "show", "-s", "--format=%cI", commit], cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None
    return value or None


def _release_version_label(commit: Optional[str], source_hash: str, dirty: bool) -> str:
    if commit:
        return f"{'workspace' if dirty else 'sha'}-{commit[:8]}{'-dirty' if dirty else ''}"
    return f"source-{source_hash[:12]}"


def resolve_runtime_release_identity(repo_root: Path, *, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    env_commit, env_source = _env_commit(env)
    git_commit, git_source = _git_head_commit(repo_root)
    source_hash = compute_source_hash(repo_root)
    snapshot = collect_workspace_snapshot(repo_root)
    mismatch = bool(env_commit and git_commit and commits_match(env_commit, git_commit) is False)
    commit = env_commit or git_commit or source_hash[:12]
    commit_source = env_source or git_source or "workspace_diagnostic_manifest_prefix"
    return {
        "commit": commit,
        "commit_source": commit_source,
        "env_commit": env_commit,
        "git_head_commit": git_commit,
        "identity_mismatch": mismatch,
        "identity_mismatch_detail": f"env commit {env_commit} != git head {git_commit}" if mismatch else None,
        "source_hash": source_hash,
        "dependency_manifest_hash": compute_dependency_manifest_hash(repo_root),
        "migration_manifest_hash": compute_migration_manifest_hash(repo_root),
        "release_gate_manifest_hash": compute_release_gate_manifest_hash(repo_root),
        "workspace_dirty": bool(snapshot.get("dirty")),
        "workspace_snapshot": snapshot,
        "built_at": _git_commit_timestamp(repo_root, git_commit if git_commit and commits_match(commit, git_commit) else None),
        "version": _release_version_label(commit, source_hash, bool(snapshot.get("dirty"))),
        "contract_path": str(RELEASE_SCOPE_FILE),
        "contract_hash": hashlib.sha256((repo_root / RELEASE_SCOPE_FILE).read_bytes()).hexdigest() if (repo_root / RELEASE_SCOPE_FILE).exists() else None,
    }


def resolve_runtime_commit(
    repo_root: Path,
    *,
    frontend_build_commit: Optional[str],
    source_hash: str,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    resolved = resolve_runtime_release_identity(repo_root, env=env)
    return str(resolved["commit"]), str(resolved["commit_source"])


def build_frontend_effective_identity(
    repo_root: Path,
    *,
    runtime_release: Optional[Dict[str, Any]] = None,
    frontend_build_contract: Optional[Dict[str, Any]] = None,
    frontend_public_contract: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    runtime_release = runtime_release or resolve_runtime_release_identity(repo_root)
    frontend_build_contract = frontend_build_contract or read_frontend_build_identity(repo_root)
    frontend_public_contract = frontend_public_contract or read_frontend_public_identity(repo_root)
    endpoint = frontend_build_contract.get("identity_endpoint") or frontend_public_contract.get("identity_endpoint") or FRONTEND_IDENTITY_DEFAULT_ENDPOINT
    return {
        "version": runtime_release.get("version"),
        "commit": runtime_release.get("commit"),
        "commit_source": runtime_release.get("commit_source"),
        "built_at": runtime_release.get("built_at"),
        "source_hash": runtime_release.get("source_hash"),
        "dependency_manifest_hash": runtime_release.get("dependency_manifest_hash"),
        "migration_manifest_hash": runtime_release.get("migration_manifest_hash"),
        "release_gate_manifest_hash": runtime_release.get("release_gate_manifest_hash"),
        "release_gate_manifest_version": None,
        "release_gate_manifest_id": None,
        "repository": "runtime:/api/version",
        "branch": runtime_release.get("workspace_snapshot", {}).get("branch"),
        "workspace_dirty": runtime_release.get("workspace_dirty"),
        "identity_mode": frontend_build_contract.get("identity_mode") or frontend_public_contract.get("identity_mode") or FRONTEND_IDENTITY_DEFAULT_MODE,
        "identity_endpoint": endpoint,
        "runtime_binding_required": True,
        "post_save_source_mutation_required": False,
        "tracked_commit_embed_allowed": False,
        "source": f"runtime_contract:{endpoint}",
    }


def frontend_identity_contracts_match(build_contract: Optional[Dict[str, Any]], public_contract: Optional[Dict[str, Any]]) -> bool:
    left = build_contract or {}
    right = public_contract or {}
    return (
        (left.get("identity_mode") or FRONTEND_IDENTITY_DEFAULT_MODE) == (right.get("identity_mode") or FRONTEND_IDENTITY_DEFAULT_MODE)
        and (left.get("identity_endpoint") or FRONTEND_IDENTITY_DEFAULT_ENDPOINT) == (right.get("identity_endpoint") or FRONTEND_IDENTITY_DEFAULT_ENDPOINT)
        and bool(left.get("runtime_binding_required", True)) is bool(right.get("runtime_binding_required", True))
        and bool(left.get("post_save_source_mutation_required", False)) is bool(right.get("post_save_source_mutation_required", False))
        and bool(left.get("tracked_commit_embed_allowed", False)) is bool(right.get("tracked_commit_embed_allowed", False))
    )


def commits_match(a: Optional[str], b: Optional[str]) -> Optional[bool]:
    aa = (a or "").strip().lower()
    bb = (b or "").strip().lower()
    if not aa or not bb:
        return None
    return aa.startswith(bb) or bb.startswith(aa)


def intended_release_matches_runtime(
    intended_release: Optional[str],
    runtime_commit: Optional[str],
    *,
    source_hash: Optional[str] = None,
) -> Optional[bool]:
    intended = (intended_release or "").strip()
    runtime = (runtime_commit or "").strip()
    if not intended or not runtime:
        return None
    if intended.startswith("UNSAVED_FINAL_CANDIDATE:"):
        parts = intended.split(":", 2)
        if len(parts) != 3:
            return False
        _, head, source_prefix = parts
        if head == "UNPROVEN":
            return False
        if commits_match(head, runtime) is not True:
            return False
        if source_prefix and source_hash:
            return str(source_hash).startswith(source_prefix)
        return True
    return commits_match(intended, runtime)


def release_identities_match(
    *,
    backend_commit: Optional[str],
    backend_source_hash: Optional[str],
    frontend_commit: Optional[str],
    frontend_source_hash: Optional[str],
) -> Optional[bool]:
    if backend_source_hash and frontend_source_hash:
        return backend_source_hash == frontend_source_hash and commits_match(backend_commit, frontend_commit) is not False
    return commits_match(backend_commit, frontend_commit)


def assert_release_identity_parity(
    *,
    backend_commit: Optional[str],
    backend_source_hash: Optional[str],
    frontend_commit: Optional[str],
    frontend_source_hash: Optional[str],
) -> None:
    matched = release_identities_match(
        backend_commit=backend_commit,
        backend_source_hash=backend_source_hash,
        frontend_commit=frontend_commit,
        frontend_source_hash=frontend_source_hash,
    )
    if matched is False:
        raise RuntimeError("release identity mismatch: frontend and backend are serving different release identities")


def build_instance_fingerprint(commit: str, source_hash: str, process_started_at: str) -> str:
    raw = f"{commit}|{source_hash}|{process_started_at}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def read_release_contract(repo_root: Path) -> Dict[str, Any]:
    return load_contract(repo_root)
