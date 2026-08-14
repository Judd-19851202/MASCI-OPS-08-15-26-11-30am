"""GD-0034 — environment-aware release-guard architecture.

P0 doctrine: PREVIEW EXECUTABILITY != RELEASE AUTHORIZATION.
A dev-server start (NODE_ENV != production) must SERVE an unattested/mismatched
candidate (so it can be QA'd) while honestly reporting deploy_authorized=false.
A production build (NODE_ENV == production) and any deploy gate (RELEASE_HARD_FAIL=1)
must keep the HARD fail-close on a fingerprint mismatch.

These tests invoke the real frontend stamp script against the real repo, whose
current attestation is a genuine MISMATCH vs the repaired candidate — exactly the
state this architecture must handle. The dev variant is run LAST so the emitted
public/release-provenance.json ends in the correct PREVIEW state.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path("/app")
STAMP = REPO / "frontend" / "scripts" / "stamp-build-version.js"
PROV = REPO / "frontend" / "public" / "release-provenance.json"
ATTESTATION = REPO / "AUTHORIZED_RELEASE.json"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(not NODE or not STAMP.exists(),
                                reason="node or stamp script unavailable")


def _run(env_extra):
    env = dict(os.environ)
    env.pop("RELEASE_HARD_FAIL", None)
    env.update(env_extra)
    return subprocess.run([NODE, str(STAMP)], cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=120)


def _attestation_is_mismatch():
    """The whole matrix depends on the repo currently carrying a MISMATCHED
    attestation (repaired candidate not yet re-Saved)."""
    if not ATTESTATION.exists():
        return False
    att = json.loads(ATTESTATION.read_text())
    prov = json.loads(PROV.read_text()) if PROV.exists() else {}
    return att.get("authorized_deployable_fingerprint") != prov.get("build_deployable_fingerprint")


def test_production_build_mismatch_hard_fails():
    if not _attestation_is_mismatch():
        pytest.skip("attestation matches candidate — mismatch matrix not applicable")
    r = _run({"NODE_ENV": "production"})
    assert r.returncode != 0, "PRODUCTION build MUST hard-fail on fingerprint mismatch"
    assert "fail-closed" in (r.stdout + r.stderr).lower()


def test_deploy_gate_mismatch_hard_fails():
    if not _attestation_is_mismatch():
        pytest.skip("attestation matches candidate — mismatch matrix not applicable")
    r = _run({"NODE_ENV": "development", "RELEASE_HARD_FAIL": "1"})
    assert r.returncode != 0, "DEPLOY gate MUST hard-fail on fingerprint mismatch"


def test_preview_mismatch_serves_as_unattested():
    # run LAST-ish so the emitted provenance ends in PREVIEW state
    r = _run({"NODE_ENV": "development"})
    assert r.returncode == 0, (
        "PREVIEW dev-serve MUST NOT hard-fail on an unattested candidate.\n"
        + r.stdout + r.stderr)
    prov = json.loads(PROV.read_text())
    assert prov["environment"] == "PREVIEW"
    assert prov["release_provenance"] == "UNATTESTED_CANDIDATE"
    assert prov["runtime_matches_authorized_release"] is False
    assert prov["deploy_authorized"] is False
    assert prov["current_candidate_fingerprint"]
    assert prov["authorized_saved_fingerprint"]


def test_preview_provenance_never_forges_authorization():
    prov = json.loads(PROV.read_text())
    # preview must never fake VERIFIED / deploy authorization for a mismatch
    if prov.get("release_provenance") == "UNATTESTED_CANDIDATE":
        assert prov.get("deploy_authorized") is False
        assert prov.get("runtime_matches_authorized_release") is False
