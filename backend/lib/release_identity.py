from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_RELEASE_FINGERPRINT_RELATIVE_PATHS: Tuple[str, ...] = (
    "release_identity_scope.json",
    "backend/lib/release_identity.py",
    "docs/governance/release_gate_manifest.json",
    "backend/server.py",
    "backend/pdf_render.py",
    "backend/training_pdf.py",
    "backend/routes/daily_reports.py",
    "backend/routes/dr_v2.py",
    "backend/routes/dr_v2_canonicalize.py",
    "backend/routes/dr_v2_pdf.py",
    "backend/routes/dr_v2_photos.py",
    "backend/routes/dispatch_portal_auth.py",
    "backend/services/photo_intelligence/pipeline.py",
    "backend/scripts/verify_release_identity.py",
    "frontend/scripts/stamp-build-version.js",
    "frontend/src/app/routing/AppRoutes.jsx",
    "frontend/src/pages/NewDailyReportV3.jsx",
    "frontend/src/pages/DailyReportsDashboard.jsx",
    "frontend/src/pages/ViewDailyReport.jsx",
)

FRONTEND_BUILD_VERSION_FILE = Path("frontend/src/buildVersion.generated.js")
RELEASE_SCOPE_FILE = Path("release_identity_scope.json")
DEPENDENCY_MANIFEST_RELATIVE_PATHS: Tuple[str, ...] = (
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/yarn.lock",
)
_VERSION_RE = re.compile(r'BUILD_VERSION\s*=\s*"([^"]+)"')
_COMMIT_RE = re.compile(r'BUILD_COMMIT\s*=\s*"([^"]+)"')
_BUILT_AT_RE = re.compile(r'BUILT_AT_ISO\s*=\s*"([^"]+)"')
_SOURCE_HASH_RE = re.compile(r'BUILD_SOURCE_HASH\s*=\s*"([^"]+)"')
_DEPENDENCY_HASH_RE = re.compile(r'BUILD_DEPENDENCY_MANIFEST_HASH\s*=\s*"([^"]+)"')
_MIGRATION_HASH_RE = re.compile(r'BUILD_MIGRATION_MANIFEST_HASH\s*=\s*"([^"]+)"')
_MANIFEST_HASH_RE = re.compile(r'RELEASE_GATE_MANIFEST_HASH\s*=\s*"([^"]+)"')
_MANIFEST_VERSION_RE = re.compile(r'RELEASE_GATE_MANIFEST_VERSION\s*=\s*"([^"]+)"')
_MANIFEST_ID_RE = re.compile(r'RELEASE_GATE_MANIFEST_ID\s*=\s*"([^"]+)"')
_REPOSITORY_RE = re.compile(r'BUILD_REPOSITORY\s*=\s*"([^"]+)"')
_BRANCH_RE = re.compile(r'BUILD_BRANCH\s*=\s*"([^"]+)"')
_DIRTY_RE = re.compile(r'BUILD_WORKSPACE_DIRTY\s*=\s*(true|false)')
_HEXISH_RE = re.compile(r"^[a-f0-9]{7,40}$", re.IGNORECASE)


def read_release_fingerprint_relative_paths(repo_root: Path) -> List[str]:
    try:
        raw = json.loads((repo_root / RELEASE_SCOPE_FILE).read_text(encoding="utf-8"))
    except Exception:
        return list(DEFAULT_RELEASE_FINGERPRINT_RELATIVE_PATHS)
    if not isinstance(raw, list) or not all(isinstance(x, str) and x.strip() for x in raw):
        return list(DEFAULT_RELEASE_FINGERPRINT_RELATIVE_PATHS)
    return [x.strip() for x in raw]


def build_fingerprint_paths(repo_root: Path) -> List[Path]:
    return [repo_root / rel for rel in read_release_fingerprint_relative_paths(repo_root)]


def _stable_digest(repo_root: Path, relative_paths: Iterable[str], *, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    for rel in relative_paths:
        rel_clean = rel.strip().replace("\\", "/")
        hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
        path = repo_root / rel_clean
        try:
            hasher.update(path.read_bytes())
        except OSError:
            hasher.update(b"MISSING:")
            hasher.update(rel_clean.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def compute_source_hash(repo_root: Path) -> str:
    rels = [str(path.relative_to(repo_root)).replace("\\", "/") for path in build_fingerprint_paths(repo_root)]
    return _stable_digest(repo_root, rels, algorithm="md5")


def compute_dependency_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, list(DEPENDENCY_MANIFEST_RELATIVE_PATHS), algorithm="sha256")


def compute_migration_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, ["docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md"], algorithm="sha256")


def compute_release_gate_manifest_hash(repo_root: Path) -> str:
    return _stable_digest(repo_root, ["docs/governance/release_gate_manifest.json"], algorithm="sha256")


def parse_frontend_build_identity_text(text: str) -> Dict[str, Optional[str]]:
    version = None
    built_at = None
    commit = None
    source_hash = None

    version_match = _VERSION_RE.search(text or "")
    if version_match:
        version = version_match.group(1)
        suffix = version.rsplit("-", 1)[-1] if "-" in version else ""
        if _HEXISH_RE.fullmatch(suffix or ""):
            commit = suffix.lower()

    commit_match = _COMMIT_RE.search(text or "")
    if commit_match:
        commit = commit_match.group(1).lower()

    built_at_match = _BUILT_AT_RE.search(text or "")
    if built_at_match:
        built_at = built_at_match.group(1)

    source_hash_match = _SOURCE_HASH_RE.search(text or "")
    if source_hash_match:
        source_hash = source_hash_match.group(1)
    dependency_hash_match = _DEPENDENCY_HASH_RE.search(text or "")
    migration_hash_match = _MIGRATION_HASH_RE.search(text or "")
    manifest_hash_match = _MANIFEST_HASH_RE.search(text or "")
    manifest_version_match = _MANIFEST_VERSION_RE.search(text or "")
    manifest_id_match = _MANIFEST_ID_RE.search(text or "")
    repository_match = _REPOSITORY_RE.search(text or "")
    branch_match = _BRANCH_RE.search(text or "")
    dirty_match = _DIRTY_RE.search(text or "")

    return {
        "version": version,
        "commit": commit,
        "built_at": built_at,
        "source_hash": source_hash,
        "dependency_manifest_hash": dependency_hash_match.group(1) if dependency_hash_match else None,
        "migration_manifest_hash": migration_hash_match.group(1) if migration_hash_match else None,
        "release_gate_manifest_hash": manifest_hash_match.group(1) if manifest_hash_match else None,
        "release_gate_manifest_version": manifest_version_match.group(1) if manifest_version_match else None,
        "release_gate_manifest_id": manifest_id_match.group(1) if manifest_id_match else None,
        "repository": repository_match.group(1) if repository_match else None,
        "branch": branch_match.group(1) if branch_match else None,
        "workspace_dirty": (dirty_match.group(1) == "true") if dirty_match else None,
        "source": "generated:frontend/src/buildVersion.generated.js" if (version or built_at) else "missing",
    }


def read_frontend_build_identity(repo_root: Path) -> Dict[str, Optional[str]]:
    path = repo_root / FRONTEND_BUILD_VERSION_FILE
    try:
        return parse_frontend_build_identity_text(path.read_text(encoding="utf-8"))
    except OSError:
        return {
            "version": None,
            "commit": None,
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
            "source": "missing",
        }


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
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None, None
    return (value or None), ("git:HEAD" if value else None)


def resolve_runtime_commit(
    repo_root: Path,
    *,
    frontend_build_commit: Optional[str],
    source_hash: str,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    env_commit, env_source = _env_commit(env)
    if env_commit:
        return env_commit, env_source or "env"

    git_commit, git_source = _git_head_commit(repo_root)
    if git_commit:
        return git_commit, git_source or "git:HEAD"

    if frontend_build_commit:
        return frontend_build_commit, "frontend_build_version"

    return source_hash[:12], "source_hash_prefix"


def commits_match(a: Optional[str], b: Optional[str]) -> Optional[bool]:
    aa = (a or "").strip().lower()
    bb = (b or "").strip().lower()
    if not aa or not bb:
        return None
    return aa.startswith(bb) or bb.startswith(aa)


def release_identities_match(
    *,
    backend_commit: Optional[str],
    backend_source_hash: Optional[str],
    frontend_commit: Optional[str],
    frontend_source_hash: Optional[str],
) -> Optional[bool]:
    if backend_source_hash and frontend_source_hash:
        return backend_source_hash == frontend_source_hash
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
        raise RuntimeError(
            "release identity mismatch: frontend and backend are serving different release identities"
        )


def build_instance_fingerprint(commit: str, source_hash: str, process_started_at: str) -> str:
    raw = f"{commit}|{source_hash}|{process_started_at}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()
