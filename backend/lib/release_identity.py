from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


RELEASE_FINGERPRINT_RELATIVE_PATHS: Tuple[str, ...] = (
    "backend/server.py",
    "backend/pdf_render.py",
    "backend/training_pdf.py",
    "backend/routes/daily_reports.py",
    "backend/routes/dr_v2.py",
    "backend/routes/dr_v2_canonicalize.py",
    "backend/routes/dr_v2_pdf.py",
    "backend/routes/dr_v2_photos.py",
    "frontend/src/app/routing/AppRoutes.jsx",
    "frontend/src/pages/NewDailyReportV3.jsx",
    "frontend/src/pages/DailyReportsDashboard.jsx",
)

FRONTEND_BUILD_VERSION_FILE = Path("frontend/src/buildVersion.generated.js")
_VERSION_RE = re.compile(r'BUILD_VERSION\s*=\s*"([^"]+)"')
_BUILT_AT_RE = re.compile(r'BUILT_AT_ISO\s*=\s*"([^"]+)"')
_SOURCE_HASH_RE = re.compile(r'BUILD_SOURCE_HASH\s*=\s*"([^"]+)"')
_HEXISH_RE = re.compile(r"^[a-f0-9]{7,40}$", re.IGNORECASE)


def build_fingerprint_paths(repo_root: Path) -> List[Path]:
    return [repo_root / rel for rel in RELEASE_FINGERPRINT_RELATIVE_PATHS]


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


def build_instance_fingerprint(commit: str, source_hash: str, process_started_at: str) -> str:
    raw = f"{commit}|{source_hash}|{process_started_at}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()
