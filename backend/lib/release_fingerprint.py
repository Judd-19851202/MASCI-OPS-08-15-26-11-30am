from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


CONTRACT_PATH = Path("docs/governance/release_content_fingerprint_contract.json")


@dataclass(frozen=True)
class FingerprintEntry:
    path: str
    file_type: str
    mode: str
    sha256: str
    bytes: int


def load_contract(repo_root: Path) -> Dict[str, Any]:
    raw = json.loads((repo_root / CONTRACT_PATH).read_text(encoding="utf-8"))
    return {
        "schema_version": raw["schema_version"],
        "algorithm_version": raw["algorithm_version"],
        "include_roots": tuple(raw.get("include_roots") or ["."]),
        "exclude_exact": tuple(raw.get("exclude_exact") or []),
        "exclude_globs": tuple(raw.get("exclude_globs") or []),
        "normalize": raw.get("normalize") or {},
        "contract_path": CONTRACT_PATH.as_posix(),
    }


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _is_excluded(path: str, contract: Dict[str, Any]) -> bool:
    if path in set(contract.get("exclude_exact") or ()):
        return True
    return _matches_any(path, contract.get("exclude_globs") or ())


def _normalize_bytes(path: str, payload: bytes, contract: Dict[str, Any]) -> bytes:
    rule = (contract.get("normalize") or {}).get(path)
    if not rule:
        return payload
    if rule.get("format") == "json":
        data = json.loads(payload.decode("utf-8"))
        for key in rule.get("drop_keys") or []:
            if isinstance(data, dict):
                data.pop(key, None)
        return (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return payload


def _executable_mode(path: Path) -> str:
    mode = stat.S_IMODE(path.lstat().st_mode)
    return oct(mode)


def _entry_from_fs(repo_root: Path, rel_path: str, contract: Dict[str, Any]) -> Optional[FingerprintEntry]:
    path = repo_root / rel_path
    if _is_excluded(rel_path, contract):
        return None
    if path.is_symlink():
        payload = path.readlink().as_posix().encode("utf-8")
        file_type = "symlink"
    elif path.is_file():
        payload = path.read_bytes()
        file_type = "file"
    else:
        return None
    normalized = _normalize_bytes(rel_path, payload, contract)
    return FingerprintEntry(
        path=rel_path,
        file_type=file_type,
        mode=_executable_mode(path),
        sha256=hashlib.sha256(normalized).hexdigest(),
        bytes=len(normalized),
    )


def _entry_from_git(repo_root: Path, rel_path: str, mode: str, contract: Dict[str, Any], ref: str) -> Optional[FingerprintEntry]:
    if _is_excluded(rel_path, contract):
        return None
    payload = subprocess.check_output(["git", "show", f"{ref}:{rel_path}"], cwd=repo_root)
    normalized = _normalize_bytes(rel_path, payload, contract)
    file_type = "symlink" if mode == "120000" else "file"
    return FingerprintEntry(
        path=rel_path,
        file_type=file_type,
        mode=mode,
        sha256=hashlib.sha256(normalized).hexdigest(),
        bytes=len(normalized),
    )


def _walk_workspace_files(repo_root: Path, contract: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for include_root in contract.get("include_roots") or (".",):
        root = (repo_root / include_root).resolve() if include_root != "." else repo_root.resolve()
        for path in sorted(root.rglob("*")):
            if not (path.is_file() or path.is_symlink()):
                continue
            rel = path.relative_to(repo_root).as_posix()
            if _is_excluded(rel, contract):
                continue
            paths.append(rel)
    return sorted(set(paths))


def _walk_git_ref_files(repo_root: Path, ref: str, contract: Dict[str, Any]) -> List[tuple[str, str]]:
    raw = subprocess.check_output(["git", "ls-tree", "-r", ref], cwd=repo_root, text=True)
    entries: List[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        left, rel_path = line.split("\t", 1)
        mode, _kind, _blob = left.split()
        if _is_excluded(rel_path, contract):
            continue
        entries.append((rel_path, mode))
    return entries


def build_release_manifest(
    repo_root: Path,
    *,
    contract: Optional[Dict[str, Any]] = None,
    git_ref: Optional[str] = None,
) -> Dict[str, Any]:
    contract = contract or load_contract(repo_root)
    entries: List[FingerprintEntry] = []
    if git_ref:
        for rel_path, mode in _walk_git_ref_files(repo_root, git_ref, contract):
            entry = _entry_from_git(repo_root, rel_path, mode, contract, git_ref)
            if entry:
                entries.append(entry)
    else:
        for rel_path in _walk_workspace_files(repo_root, contract):
            entry = _entry_from_fs(repo_root, rel_path, contract)
            if entry:
                entries.append(entry)
    entries.sort(key=lambda item: item.path)
    manifest = hashlib.sha256()
    for entry in entries:
        manifest.update(
            f"{entry.path}\0{entry.file_type}\0{entry.mode}\0{entry.sha256}\0{entry.bytes}\n".encode("utf-8")
        )
    return {
        "algorithm_version": contract["algorithm_version"],
        "schema_version": contract["schema_version"],
        "contract_path": contract["contract_path"],
        "git_ref": git_ref,
        "entry_count": len(entries),
        "manifest_sha256": manifest.hexdigest(),
        "entries": [entry.__dict__ for entry in entries],
        "contract": {
            "include_roots": list(contract.get("include_roots") or []),
            "exclude_exact": list(contract.get("exclude_exact") or []),
            "exclude_globs": list(contract.get("exclude_globs") or []),
            "normalize": contract.get("normalize") or {},
        },
    }


def write_fingerprint_record(
    repo_root: Path,
    *,
    output_path: Path,
    base_head: str,
    workspace_status_lines: Sequence[str],
) -> Dict[str, Any]:
    manifest = build_release_manifest(repo_root)
    payload = {
        "generated_at": subprocess.check_output(["date", "-Iseconds"], text=True).strip(),
        "candidate_label": "UNSAVED_FINAL_WORKSPACE_CANDIDATE",
        "git_head_before_owner_save": base_head,
        "workspace_status_lines": list(workspace_status_lines),
        "algorithm_version": manifest["algorithm_version"],
        "schema_version": manifest["schema_version"],
        "contract_path": manifest["contract_path"],
        "content_manifest_sha256": manifest["manifest_sha256"],
        "tracked_and_untracked_content_file_count": manifest["entry_count"],
        "contract": manifest["contract"],
        "entries": manifest["entries"],
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def compare_manifests(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    a_map = {row["path"]: row for row in a.get("entries") or []}
    b_map = {row["path"]: row for row in b.get("entries") or []}
    only_a = sorted(set(a_map) - set(b_map))
    only_b = sorted(set(b_map) - set(a_map))
    changed = sorted(
        path for path in set(a_map) & set(b_map)
        if (a_map[path].get("sha256"), a_map[path].get("mode"), a_map[path].get("file_type"), a_map[path].get("bytes"))
        != (b_map[path].get("sha256"), b_map[path].get("mode"), b_map[path].get("file_type"), b_map[path].get("bytes"))
    )
    return {
        "match": not only_a and not only_b and not changed and a.get("manifest_sha256") == b.get("manifest_sha256"),
        "only_a": only_a,
        "only_b": only_b,
        "changed": changed,
        "manifest_a": a.get("manifest_sha256"),
        "manifest_b": b.get("manifest_sha256"),
    }
