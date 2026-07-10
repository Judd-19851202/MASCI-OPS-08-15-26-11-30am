"""TRACK 28.07 · Phase 17 · Permanent certification manifest coherence.

The manifest at ``lib/certification_manifest.py`` is the source of
truth for what's certified. This test is the machine-enforceable
contract that keeps it honest.

## Enforced invariants

1. Every entry has ``workflow_id``, ``domain``, ``owner``.
2. Every ``workflow_id`` is unique.
3. Every regression_tests path exists on disk.
4. Every PASS entry has ``last_certified_at`` + ``last_certified_commit``
   + non-empty ``regression_tests``.
5. Every dependency (`cross_domain_deps` entry) resolves to another
   manifest workflow_id.
6. NOT_CERTIFIED entries have empty ``last_certified_at`` (no lying).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from lib.certification_manifest import MANIFEST


REPO_ROOT = Path("/app")


def test_every_entry_has_required_fields():
    for e in MANIFEST:
        assert e.workflow_id, "empty workflow_id"
        assert e.domain, f"{e.workflow_id}: empty domain"
        assert e.owner, f"{e.workflow_id}: empty owner"


def test_workflow_ids_are_unique():
    seen = set()
    for e in MANIFEST:
        assert e.workflow_id not in seen, f"duplicate workflow_id: {e.workflow_id}"
        seen.add(e.workflow_id)


def test_regression_tests_exist_on_disk():
    for e in MANIFEST:
        for t in e.regression_tests:
            p = REPO_ROOT / t
            assert p.exists(), (
                f"{e.workflow_id}: declared regression test does not exist: {t}"
            )


def test_pass_entries_have_certification_metadata():
    for e in MANIFEST:
        if e.status == "PASS":
            assert e.last_certified_at, (
                f"{e.workflow_id} PASS but last_certified_at empty"
            )
            assert e.last_certified_commit, (
                f"{e.workflow_id} PASS but last_certified_commit empty"
            )
            assert e.regression_tests, (
                f"{e.workflow_id} PASS but no regression_tests declared"
            )
            assert e.evidence_location, (
                f"{e.workflow_id} PASS but no evidence_location"
            )


def test_dependencies_resolve_to_known_workflows():
    ids = {e.workflow_id for e in MANIFEST}
    for e in MANIFEST:
        for dep in e.cross_domain_deps:
            assert dep in ids, (
                f"{e.workflow_id}: cross_domain_deps '{dep}' is not a known "
                f"workflow_id. Known: {sorted(ids)}"
            )


def test_not_certified_entries_dont_claim_certification():
    for e in MANIFEST:
        if e.status == "NOT_CERTIFIED":
            assert not e.last_certified_at, (
                f"{e.workflow_id} NOT_CERTIFIED but claims last_certified_at="
                f"{e.last_certified_at!r} — this is a lie."
            )
            assert not e.last_certified_commit, (
                f"{e.workflow_id} NOT_CERTIFIED but claims a commit"
            )


def test_manifest_covers_all_track_28_prior_certifications():
    """Regression: every closed Track 28.x domain must have an entry."""
    ids = {e.workflow_id for e in MANIFEST}
    for required in [
        "hr.employee_lifecycle",
        "field_ops.daily_report",
        "field_leadership.records",
        "fleet.equipment_and_dispatch",
        "safety.incidents_and_forms",
        "training.qualifications_and_credentials",
        "platform.admin_auth_invariant",
    ]:
        assert required in ids, (
            f"Track 28 certified workflow missing from manifest: {required}"
        )
