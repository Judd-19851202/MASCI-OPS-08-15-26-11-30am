"""Canonical deployable-content fingerprint + provenance evaluation.

STAGE 1/3/6 library core (owner-locked architecture). Additive: does NOT alter
the existing release_identity gating.

The DEPLOYABLE_CONTENT_FINGERPRINT is computed over a governed, NARROW
SOURCE-INPUT scope (the `deployable_source_inputs` section of the release
content fingerprint contract) so it is deterministic across environments where
those inputs are expected to exist (freeze / post-save / build). It is a
DIFFERENT identity universe from the broad workspace diagnostic manifest and is
NEVER compared against it.

Runtime consumes the build stamp (STAGE 6) and never recreates the source tree.

Algorithm (must stay byte-identical to the pure-JS mirror in
frontend/scripts/deployable_content_fingerprint.js):
  fingerprint = "dcf-" + sha256_hex(
     ALGO + "\\0" +
     contract_digest + "\\0" +
     for each sorted rel path: rel + "\\0" + file_hash_hex_or_MISSING + "\\0"
  )
  file_hash_hex = sha256_hex(normalize(raw_bytes))
  normalize     = CRLF/CR -> LF
  contract_digest = "c-" + sha256_hex(normalize(raw_bytes_of_contract_file))
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FINGERPRINT_ALGORITHM_VERSION = "dcf-1"
ATTESTATION_FORMAT_VERSION = "1"
PROVENANCE_FORMAT_VERSION = "1"

CONTRACT_PATH = Path("docs/governance/release_content_fingerprint_contract.json")
CONTRACT_SECTION = "deployable_source_inputs"
# Generated, non-tracked, gitignored, excluded-from-fingerprint attestation.
ATTESTATION_PATH = Path("AUTHORIZED_RELEASE.json")

# Fail-closed provenance states.
VERIFIED = "VERIFIED"
UNPROVEN = "UNPROVEN"
MISMATCH = "MISMATCH"
CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
ARTIFACT_IDENTITY_MISMATCH = "ARTIFACT_IDENTITY_MISMATCH"

PROVENANCE_METHOD = "build_content_fingerprint_bound_to_saved_sha"


class MissingSourceInputError(RuntimeError):
    """Raised in strict mode when a governed required source input is absent."""


def _norm_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_contract(repo_root: Path) -> Dict[str, Any]:
    raw = json.loads((repo_root / CONTRACT_PATH).read_text(encoding="utf-8"))
    section = raw.get(CONTRACT_SECTION)
    if not isinstance(section, dict):
        raise MissingSourceInputError(
            f"contract missing required section '{CONTRACT_SECTION}'"
        )
    return section


def contract_digest(repo_root: Path) -> str:
    """Digest of the whole contract file (normalized bytes). Whole-file hashing
    is intentional: it is trivially reproducible in pure JS with zero JSON
    canonicalization risk, and any governed change to exclusion/scope rules
    changes the digest so a stale contract can never be called comparable."""
    raw = _norm_bytes((repo_root / CONTRACT_PATH).read_bytes())
    return "c-" + _sha_hex(raw)


def _fnmatch_any(rel: str, globs: List[str]) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def enumerate_source_inputs(repo_root: Path) -> Tuple[List[str], List[str]]:
    """Return (sorted in-scope source-input rel paths, missing_required_roots).

    Every declared include root is REQUIRED to exist; a missing root is a
    fail-closed signal (wrong checkout / stripped deployment snapshot)."""
    contract = load_contract(repo_root)
    roots = contract.get("include_roots") or ["."]
    exclude_exact = set(contract.get("exclude_exact") or [])
    exclude_globs = list(contract.get("exclude_globs") or [])
    exclude_exact.add(ATTESTATION_PATH.as_posix())

    found: List[str] = []
    missing_roots: List[str] = []
    for root in roots:
        base = repo_root / root
        if not base.exists():
            missing_roots.append(root)
            continue
        candidates = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for p in candidates:
            rel = p.relative_to(repo_root).as_posix()
            if rel in exclude_exact or _fnmatch_any(rel, exclude_globs):
                continue
            found.append(rel)
    return sorted(set(found)), sorted(set(missing_roots))


def compute_deployable_fingerprint(repo_root: Path, *, strict: bool = False) -> str:
    entries, missing_roots = enumerate_source_inputs(repo_root)
    if strict and missing_roots:
        raise MissingSourceInputError(
            "missing required source input root(s): " + ", ".join(missing_roots)
        )
    hasher = hashlib.sha256()
    hasher.update((FINGERPRINT_ALGORITHM_VERSION + "\0").encode("utf-8"))
    hasher.update((contract_digest(repo_root) + "\0").encode("utf-8"))
    for rel in entries:
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        p = repo_root / rel
        file_hex = _sha_hex(_norm_bytes(p.read_bytes())) if p.exists() else "MISSING"
        hasher.update(file_hex.encode("utf-8"))
        hasher.update(b"\0")
    return "dcf-" + hasher.hexdigest()


def read_attestation(repo_root: Path) -> Optional[Dict[str, Any]]:
    path = repo_root / ATTESTATION_PATH
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def evaluate_provenance(
    repo_root: Path,
    *,
    build_fingerprint: Optional[str] = None,
    frontend_stamp: Optional[Dict[str, Any]] = None,
    backend_stamp: Optional[Dict[str, Any]] = None,
    attestation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """STAGE 6 runtime evaluation. Consumes the build stamp; NEVER recreates the
    source tree. Fail-closed."""
    att = attestation if attestation is not None else read_attestation(repo_root)
    result: Dict[str, Any] = {
        "release_provenance": UNPROVEN,
        "runtime_matches_intended_release": False,
        "provenance_method": None,
        "authorized_saved_sha": None,
        "authorized_deployable_fingerprint": None,
        "build_deployable_fingerprint": build_fingerprint,
        "fingerprint_contract_digest": None,
        "fingerprint_algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
        "provenance_format_version": PROVENANCE_FORMAT_VERSION,
    }
    if not att:
        return result  # UNPROVEN — no owner-Save attestation

    result["authorized_saved_sha"] = att.get("authorized_saved_sha")
    result["authorized_deployable_fingerprint"] = att.get("authorized_deployable_fingerprint")
    result["fingerprint_contract_digest"] = att.get("fingerprint_contract_digest")

    live_contract = contract_digest(repo_root)
    if att.get("fingerprint_contract_digest") not in (None, live_contract):
        result["release_provenance"] = CONTRACT_MISMATCH
        return result

    if frontend_stamp and backend_stamp:
        for k in ("authorized_saved_sha", "build_deployable_fingerprint", "fingerprint_contract_digest"):
            if frontend_stamp.get(k) != backend_stamp.get(k):
                result["release_provenance"] = ARTIFACT_IDENTITY_MISMATCH
                return result

    if build_fingerprint is None:
        return result  # UNPROVEN — no build stamp to compare

    if build_fingerprint != att.get("authorized_deployable_fingerprint"):
        result["release_provenance"] = MISMATCH
        return result

    result["release_provenance"] = VERIFIED
    result["runtime_matches_intended_release"] = True
    result["provenance_method"] = PROVENANCE_METHOD
    return result


def generate_attestation(repo_root: Path, authorized_saved_sha: str) -> Dict[str, Any]:
    """STAGE 3 — build the (non-tracked) attestation payload. Caller writes it to
    ATTESTATION_PATH AFTER owner Save; it is gitignored and excluded from the
    fingerprint, so it never dirties tracked source or forces a second Save. No
    mutable timestamps are used as identity inputs."""
    return {
        "authorized_saved_sha": authorized_saved_sha,
        "authorized_deployable_fingerprint": compute_deployable_fingerprint(repo_root, strict=True),
        "fingerprint_algorithm_version": FINGERPRINT_ALGORITHM_VERSION,
        "fingerprint_contract_digest": contract_digest(repo_root),
        "attestation_format_version": ATTESTATION_FORMAT_VERSION,
    }


def _main(argv: List[str]) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    cmd = argv[0] if argv else "compute"
    if cmd == "compute":
        print(compute_deployable_fingerprint(repo_root, strict=("--strict" in argv)))
        return 0
    if cmd == "digest":
        print(contract_digest(repo_root))
        return 0
    if cmd == "enumerate":
        entries, missing = enumerate_source_inputs(repo_root)
        print(json.dumps({"count": len(entries), "missing_roots": missing, "entries": entries}, indent=2))
        return 0
    if cmd == "attest":
        sha = argv[1] if len(argv) > 1 else ""
        if not sha:
            print("attest requires <authorized_saved_sha>", file=sys.stderr)
            return 2
        print(json.dumps(generate_attestation(repo_root, sha), indent=2))
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
