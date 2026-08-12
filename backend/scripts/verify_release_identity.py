from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from lib.release_fingerprint import build_release_manifest  # noqa: E402
from lib.release_identity import (  # noqa: E402
    build_frontend_effective_identity,
    commits_match,
    frontend_identity_contracts_match,
    read_frontend_build_identity,
    read_frontend_public_identity,
    resolve_runtime_release_identity,
)


def main() -> int:
    runtime_release = resolve_runtime_release_identity(REPO_ROOT)
    frontend_build_contract = read_frontend_build_identity(REPO_ROOT)
    frontend_public_contract = read_frontend_public_identity(REPO_ROOT)
    frontend_effective = build_frontend_effective_identity(
        REPO_ROOT,
        runtime_release=runtime_release,
        frontend_build_contract=frontend_build_contract,
        frontend_public_contract=frontend_public_contract,
    )
    manifest = build_release_manifest(REPO_ROOT)
    workspace_head = ((runtime_release.get("workspace_snapshot") or {}).get("head") or "")
    workspace_head_available = bool(workspace_head)
    workspace_dirty = bool(runtime_release.get("workspace_dirty"))

    workspace_head_matches_runtime = commits_match(workspace_head, runtime_release.get("commit")) is True
    workspace_head_matches_frontend = commits_match(workspace_head, frontend_effective.get("commit")) is True
    frontend_matches_runtime = commits_match(frontend_effective.get("commit"), runtime_release.get("commit")) is True
    contracts_match = frontend_identity_contracts_match(frontend_build_contract, frontend_public_contract)

    errors = []
    if runtime_release.get("identity_mismatch"):
        errors.append(str(runtime_release.get("identity_mismatch_detail") or "runtime release identity mismatch"))
    if not contracts_match:
        errors.append("frontend release identity contracts disagree")
    if frontend_build_contract.get("tracked_commit_embed_allowed"):
        errors.append("tracked frontend build contract still allows embedded commit")
    if frontend_build_contract.get("post_save_source_mutation_required"):
        errors.append("frontend build contract still requires post-save tracked source mutation")
    if frontend_build_contract.get("identity_mode") != "runtime-api-version":
        errors.append("frontend build contract is not runtime-api-version")
    if not frontend_matches_runtime:
        errors.append("frontend effective identity does not match runtime commit")
    if workspace_head_available and not workspace_head_matches_runtime:
        errors.append("workspace HEAD does not match runtime commit")
    if workspace_head_available and not workspace_head_matches_frontend:
        errors.append("workspace HEAD does not match frontend effective commit")
    if not workspace_head_available and workspace_dirty:
        errors.append("workspace HEAD unavailable while workspace is dirty")
    if not manifest.get("manifest_sha256"):
        errors.append("release fingerprint manifest unavailable")

    payload = {
        "ok": not errors,
        "canonical_release_commit": runtime_release.get("commit"),
        "canonical_release_source_hash": runtime_release.get("source_hash"),
        "workspace_head_commit": workspace_head,
        "workspace_head_available": workspace_head_available,
        "workspace_dirty": workspace_dirty,
        "frontend_commit": frontend_effective.get("commit"),
        "runtime_commit": runtime_release.get("commit"),
        "workspace_head_matches_runtime": workspace_head_matches_runtime,
        "workspace_head_matches_frontend": workspace_head_matches_frontend,
        "frontend_matches_runtime": frontend_matches_runtime,
        "frontend_contracts_match": contracts_match,
        "frontend_identity_mode": frontend_effective.get("identity_mode"),
        "frontend_identity_endpoint": frontend_effective.get("identity_endpoint"),
        "release_manifest_sha256": manifest.get("manifest_sha256"),
        "release_manifest_entry_count": manifest.get("entry_count"),
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())