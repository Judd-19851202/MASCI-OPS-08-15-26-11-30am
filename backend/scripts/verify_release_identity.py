from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from lib.release_fingerprint import build_release_manifest  # noqa: E402
from lib import deployable_content_fingerprint as dcf  # noqa: E402
from lib.release_identity import (  # noqa: E402
    build_frontend_effective_identity,
    commits_match,
    frontend_identity_contracts_match,
    read_frontend_build_identity,
    read_frontend_public_identity,
    resolve_runtime_release_identity,
)
from lib.truth_population_guard import gate_violations as truth_population_gate_violations  # noqa: E402
from lib.truth_surface_guard import gate_violations as truth_surface_gate_violations  # noqa: E402


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

    # ── Canonical deployable-content source-input contract (fail-closed) ──
    deployable_contract_digest = None
    deployable_fingerprint = None
    deployable_missing_roots: list[str] = []
    try:
        dcf.load_contract(REPO_ROOT)
        deployable_contract_digest = dcf.contract_digest(REPO_ROOT)
        _entries, deployable_missing_roots = dcf.enumerate_source_inputs(REPO_ROOT)
        if deployable_missing_roots:
            errors.append(
                "deployable source-input roots missing: " + ", ".join(deployable_missing_roots)
            )
        else:
            deployable_fingerprint = dcf.compute_deployable_fingerprint(REPO_ROOT, strict=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"deployable source-input contract invalid: {type(exc).__name__}: {exc}")

    # ── Truth-Program population-truth pre-Save enforcement (fail-closed) ──
    # GD-0014 population/truncation contract sentinel + GD-0015 items/total filter
    # drift. Invokes the ONE canonical implementation in lib.truth_population_guard.
    truth_population_violations: list[str] = []
    try:
        truth_population_violations = truth_population_gate_violations(REPO_ROOT)
        errors.extend(truth_population_violations)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"GD-0014/GD-0015 population-truth guard failed to run: {type(exc).__name__}: {exc}")

    # ── Truth-Surface enumeration drift sentinel (GD-0025, fail-closed) ──
    # Canonical reproducible human-truth denominator; fails on invariant break,
    # OPEN/unclassified surface, or unregistered surface drift from baseline.
    truth_surface_violations: list[str] = []
    try:
        truth_surface_violations = truth_surface_gate_violations(REPO_ROOT)
        errors.extend(truth_surface_violations)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"GD-0025 truth-surface enumeration guard failed to run: {type(exc).__name__}: {exc}")

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
        "workspace_diagnostic_manifest_sha256": manifest.get("manifest_sha256"),
        "workspace_diagnostic_manifest_entry_count": manifest.get("entry_count"),
        # Legacy alias retained for existing consumers; same value, honest name above.
        "release_manifest_sha256": manifest.get("manifest_sha256"),
        "release_manifest_entry_count": manifest.get("entry_count"),
        "deployable_content_fingerprint": deployable_fingerprint,
        "deployable_fingerprint_contract_digest": deployable_contract_digest,
        "deployable_fingerprint_algorithm_version": dcf.FINGERPRINT_ALGORITHM_VERSION,
        "truth_population_gate_ok": not truth_population_violations,
        "truth_population_gate_violations": truth_population_violations,
        "truth_surface_gate_ok": not truth_surface_violations,
        "truth_surface_gate_violations": truth_surface_violations,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())