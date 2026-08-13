"""Fail-closed regression matrix for canonical deployable-content provenance.

Owner-locked contract (see docs/governance/release_content_fingerprint_contract.json
:: deployable_source_inputs). Covers the ~24-case matrix the owner requires.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lib import deployable_content_fingerprint as dcf

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_contract(root: Path, *, extra_roots=None, extra_globs=None):
    section = {
        "schema_version": "MASCI_DEPLOYABLE_SOURCE_INPUT_CONTRACT/v1",
        "algorithm_version": "dcf-1",
        "include_roots": ["backend/lib", "frontend/src", "frontend/package.json"] + list(extra_roots or []),
        "exclude_exact": [],
        "exclude_globs": ["**/*.log", "logs/**", "**/__pycache__/**"] + list(extra_globs or []),
        "normalize": {"line_endings": "lf"},
    }
    (root / dcf.CONTRACT_PATH).write_text(json.dumps({"deployable_source_inputs": section}))


@pytest.fixture
def repo(tmp_path: Path):
    (tmp_path / "docs/governance").mkdir(parents=True)
    (tmp_path / "backend/lib").mkdir(parents=True)
    (tmp_path / "frontend/src").mkdir(parents=True)
    (tmp_path / "logs").mkdir()
    (tmp_path / "docs/evidence").mkdir(parents=True)
    _write_contract(tmp_path)
    (tmp_path / "backend/lib/app.py").write_text("x = 1\n")
    (tmp_path / "frontend/src/index.js").write_text("console.log(1);\n")
    (tmp_path / "frontend/package.json").write_text('{"name":"masci"}\n')
    (tmp_path / "logs/run.log").write_text("noise\n")
    (tmp_path / "docs/evidence/report.md").write_text("evidence\n")
    return tmp_path


# 1
def test_deterministic_recompute_twice(repo):
    assert dcf.compute_deployable_fingerprint(repo) == dcf.compute_deployable_fingerprint(repo)


# 2
def test_included_backend_source_change_changes_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "backend/lib/app.py").write_text("x = 2\n")
    assert dcf.compute_deployable_fingerprint(repo) != f1


# 3
def test_included_frontend_source_change_changes_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "frontend/src/index.js").write_text("console.log(2);\n")
    assert dcf.compute_deployable_fingerprint(repo) != f1


# 4
def test_included_build_config_change_changes_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "frontend/package.json").write_text('{"name":"masci","v":2}\n')
    assert dcf.compute_deployable_fingerprint(repo) != f1


# 5
def test_excluded_log_change_does_not_change_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "logs/run.log").write_text("different noise\n")
    assert dcf.compute_deployable_fingerprint(repo) == f1


# 6 evidence/docs outside scope is not part of identity
def test_excluded_evidence_change_does_not_change_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "docs/evidence/report.md").write_text("new evidence\n")
    assert dcf.compute_deployable_fingerprint(repo) == f1


def test_line_ending_normalized(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / "backend/lib/app.py").write_bytes(b"x = 1\r\n")
    assert dcf.compute_deployable_fingerprint(repo) == f1


# 7
def test_missing_required_source_input_fails_closed(repo):
    _write_contract(repo, extra_roots=["backend/lib/required_missing.py"])
    with pytest.raises(dcf.MissingSourceInputError):
        dcf.compute_deployable_fingerprint(repo, strict=True)
    # non-strict still yields a fingerprint (no crash), but strict at build fails closed
    assert dcf.compute_deployable_fingerprint(repo, strict=False)


# 8
def test_contract_change_changes_digest(repo):
    d1 = dcf.contract_digest(repo)
    _write_contract(repo, extra_globs=["extra/**"])
    assert dcf.contract_digest(repo) != d1


# 9
def test_attestation_excluded_from_fingerprint(repo):
    f1 = dcf.compute_deployable_fingerprint(repo)
    (repo / dcf.ATTESTATION_PATH).write_text(json.dumps({"x": 1}))
    assert dcf.compute_deployable_fingerprint(repo) == f1  # no self-reference


# 10 + 11 attestation generation does not depend on / mutate tracked source
def test_generate_attestation_is_pure(repo):
    f_before = dcf.compute_deployable_fingerprint(repo, strict=True)
    att = dcf.generate_attestation(repo, "SHA_REAL_123")
    f_after = dcf.compute_deployable_fingerprint(repo, strict=True)
    assert f_before == f_after
    assert att["authorized_deployable_fingerprint"] == f_before
    assert att["authorized_saved_sha"] == "SHA_REAL_123"
    assert att["fingerprint_contract_digest"] == dcf.contract_digest(repo)


# 12
def test_missing_authorization_unproven(repo):
    r = dcf.evaluate_provenance(repo, build_fingerprint=dcf.compute_deployable_fingerprint(repo))
    assert r["release_provenance"] == dcf.UNPROVEN
    assert r["runtime_matches_intended_release"] is False


# 13
def test_wrong_build_fingerprint_mismatch(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    r = dcf.evaluate_provenance(repo, build_fingerprint="dcf-deadbeef", attestation=att)
    assert r["release_provenance"] == dcf.MISMATCH


# 14
def test_contract_digest_mismatch(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    att["fingerprint_contract_digest"] = "c-wrong"
    r = dcf.evaluate_provenance(repo, build_fingerprint=att["authorized_deployable_fingerprint"], attestation=att)
    assert r["release_provenance"] == dcf.CONTRACT_MISMATCH


# 15
def test_fe_be_stamp_disagreement(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    fp = att["authorized_deployable_fingerprint"]
    fe = {"authorized_saved_sha": "SHA123", "build_deployable_fingerprint": fp, "fingerprint_contract_digest": att["fingerprint_contract_digest"]}
    be = {"authorized_saved_sha": "SHA999", "build_deployable_fingerprint": fp, "fingerprint_contract_digest": att["fingerprint_contract_digest"]}
    r = dcf.evaluate_provenance(repo, build_fingerprint=fp, frontend_stamp=fe, backend_stamp=be, attestation=att)
    assert r["release_provenance"] == dcf.ARTIFACT_IDENTITY_MISMATCH


# 16 + 19
def test_matching_build_verified_with_genuine_sha(repo):
    att = dcf.generate_attestation(repo, "9b6b8e41e8b628ce004aef91028f5cbc024a65bc")
    r = dcf.evaluate_provenance(repo, build_fingerprint=att["authorized_deployable_fingerprint"], attestation=att)
    assert r["release_provenance"] == dcf.VERIFIED
    assert r["runtime_matches_intended_release"] is True
    assert r["provenance_method"] == "build_content_fingerprint_bound_to_saved_sha"
    assert r["authorized_saved_sha"] == "9b6b8e41e8b628ce004aef91028f5cbc024a65bc"


# 17 + 18 post-save / unsaved snapshot mutation is caught at build recompute
def test_post_save_source_mutation_mismatch(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    (repo / "backend/lib/app.py").write_text("x = 999\n")  # platform built mutated snapshot
    r = dcf.evaluate_provenance(repo, build_fingerprint=dcf.compute_deployable_fingerprint(repo), attestation=att)
    assert r["release_provenance"] == dcf.MISMATCH


# 20 the result never labels a source hash as a git commit / commit_source
def test_no_fake_commit_semantics(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    r = dcf.evaluate_provenance(repo, build_fingerprint=att["authorized_deployable_fingerprint"], attestation=att)
    assert "commit" not in r and "commit_source" not in r
    assert r["authorized_deployable_fingerprint"].startswith("dcf-")


# 21 runtime does not require intentionally omitted source-tree files
def test_runtime_does_not_require_source_tree(tmp_path):
    # A runtime container with NO source tree, only the contract + attestation:
    (tmp_path / "docs/governance").mkdir(parents=True)
    _write_contract(tmp_path)
    att = {
        "authorized_saved_sha": "SHA123",
        "authorized_deployable_fingerprint": "dcf-abc",
        "fingerprint_contract_digest": dcf.contract_digest(tmp_path),
        "attestation_format_version": "1",
    }
    r = dcf.evaluate_provenance(tmp_path, build_fingerprint="dcf-abc", attestation=att)
    assert r["release_provenance"] == dcf.VERIFIED  # no source-tree recompute needed


# 22 the broad workspace diagnostic manifest hash cannot satisfy deployable verification
def test_workspace_diagnostic_hash_cannot_verify(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    # A 64-hex workspace manifest sha (no dcf- prefix, different identity universe)
    workspace_manifest_sha = "8c892755d270929862729dd9daffffe378cfa0b7ab299cc6c52d0d1091099dba"
    r = dcf.evaluate_provenance(repo, build_fingerprint=workspace_manifest_sha, attestation=att)
    assert r["release_provenance"] == dcf.MISMATCH


# 23 an unrelated runtime artifact fingerprint cannot satisfy deployable-source verification
def test_runtime_artifact_fingerprint_cannot_verify(repo):
    att = dcf.generate_attestation(repo, "SHA123")
    r = dcf.evaluate_provenance(repo, build_fingerprint="artifact-md5-deadbeef", attestation=att)
    assert r["release_provenance"] == dcf.MISMATCH


# governance: the generated attestation path is gitignored in the real repo
def test_attestation_path_is_gitignored():
    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert dcf.ATTESTATION_PATH.as_posix() in ignore
    assert "frontend/public/release-provenance.json" in ignore


# real-repo: canonical contract section loads, digest + fingerprint compute strictly
def test_real_repo_contract_and_fingerprint_present():
    section = dcf.load_contract(REPO_ROOT)
    assert section.get("algorithm_version") == "dcf-1"
    assert dcf.contract_digest(REPO_ROOT).startswith("c-")
    entries, missing = dcf.enumerate_source_inputs(REPO_ROOT)
    assert not missing, f"required roots missing: {missing}"
    assert entries, "no source inputs enumerated"
    assert dcf.compute_deployable_fingerprint(REPO_ROOT, strict=True).startswith("dcf-")
