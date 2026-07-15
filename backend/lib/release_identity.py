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
_VERSION_RE = re.compile(r'BUILD_VERSION\s*=\s*"([^"]+)"')
_COMMIT_RE = re.compile(r'BUILD_COMMIT\s*=\s*"([^"]+)"')
_BUILT_AT_RE = re.compile(r'BUILT_AT_ISO\s*=\s*"([^"]+)"')
_SOURCE_HASH_RE = re.compile(r'BUILD_SOURCE_HASH\s*=\s*"([^"]+)"')
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


def compute_source_hash(repo_root: Path) -> str:
    h = hashlib.md5()
    for path in build_fingerprint_paths(repo_root):
        try:
            h.update(path.read_bytes())
        except OSError:
            h.update(b"MISSING:" + str(path).encode())
    return h.hexdigest()


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

    return {
        "version": version,
        "commit": commit,
        "built_at": built_at,
        "source_hash": source_hash,
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
