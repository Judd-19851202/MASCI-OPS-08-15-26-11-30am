from __future__ import annotations

from datetime import datetime, timezone

from lib.restore_certification_evidence import (
    build_canonical_preview_fingerprint,
    build_collection_sample_verification,
    build_independent_qa_review,
    build_restore_evidence_skeleton,
    compare_fingerprints,
    mark_phase_status,
    normalize_verification_document,
    validate_restore_certification_evidence,
    verify_audit_data,
    verify_identity_role_data,
    verify_scheduler_state,
)


class _Collection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, *args, **kwargs):
        return list(self.docs)


class _DB:
    def __init__(self, mapping):
        self.mapping = {k: _Collection(v) for k, v in mapping.items()}

    def __getitem__(self, name):
        return self.mapping[name]

    def list_collection_names(self):
        return list(self.mapping.keys())


def _runtime_identity():
    return {
        "app_env": "preview",
        "db_name": "masci_safety_preview",
        "environment_fingerprint": "env-fp",
        "cluster_fingerprint": "cluster-fp",
    }


def test_same_state_produces_identical_fingerprints():
    data = {
        "daily_reports": [{"id": "b", "v": 2}, {"id": "a", "v": 1}],
        "ops8_drill_tmp__daily_reports": [{"id": "ignored"}],
        "backup_jobs": [{"job_id": "guard"}],
    }
    db1 = _DB(data)
    db2 = _DB({
        "backup_jobs": [{"job_id": "guard-2"}],
        "daily_reports": [{"id": "a", "v": 1}, {"id": "b", "v": 2}],
        "ops8_drill_tmp__daily_reports": [{"id": "ignored"}],
    })
    fp1 = build_canonical_preview_fingerprint(db1, runtime_identity=_runtime_identity())
    fp2 = build_canonical_preview_fingerprint(db2, runtime_identity=_runtime_identity())
    assert fp1["aggregate_fingerprint"] == fp2["aggregate_fingerprint"]
    assert "ops8_drill_tmp__daily_reports" in fp1["excluded_collections"]


def test_changed_record_changes_collection_and_aggregate_fingerprint():
    base = _DB({"daily_reports": [{"id": "a", "v": 1}]})
    changed = _DB({"daily_reports": [{"id": "a", "v": 2}]})
    fp1 = build_canonical_preview_fingerprint(base, runtime_identity=_runtime_identity())
    fp2 = build_canonical_preview_fingerprint(changed, runtime_identity=_runtime_identity())
    cmp = compare_fingerprints(fp1, fp2)
    assert cmp["match"] is False
    assert cmp["difference"]["collection_differences"][0]["collection"] == "daily_reports"


def test_phase_started_and_interrupted_are_truthful():
    evidence = build_restore_evidence_skeleton(
        drill_id="d1",
        namespace_prefix="ops8_d1",
        authorized_archive_key="k",
        requested_env="preview",
        target_db="masci_safety_preview",
        guard={"owner_token": "token-1"},
    )
    mark_phase_status(evidence, phase="preflight", status="started", owner_pid=1, owner_token="token-1")
    mark_phase_status(evidence, phase="preflight", status="completed", owner_pid=1, owner_token="token-1")
    mark_phase_status(evidence, phase="namespace_restore", status="started", owner_pid=1, owner_token="token-1")
    mark_phase_status(evidence, phase="namespace_restore", status="interrupted", owner_pid=1, owner_token="token-1")
    assert evidence["phase_history"]["preflight"]["phase_completed_at"] is not None
    assert evidence["phase_history"]["namespace_restore"]["phase_status"] == "interrupted"
    assert evidence["last_completed_phase"] == "preflight"


def test_representative_sample_is_reproducible_and_detects_content_change():
    expected = [{"id": str(i), "value": i} for i in range(10)]
    restored = [{"id": str(i), "value": i} for i in range(10)]
    ok = build_collection_sample_verification(collection="daily_reports", expected_docs=expected, restored_docs=restored)
    bad = build_collection_sample_verification(collection="daily_reports", expected_docs=expected, restored_docs=restored[:-1] + [{"id": "9", "value": 99}])
    assert ok["matched"] is True
    assert bad["matched"] is False
    assert ok["sample_identifiers"] == build_collection_sample_verification(collection="daily_reports", expected_docs=expected, restored_docs=restored)["sample_identifiers"]


def test_representative_sample_ignores_mongo_generated_id_field():
    expected = [{"id": "dr-1", "value": 1, "nested": {"a": 1}}]
    restored = [{"_id": "mongo-id", "id": "dr-1", "value": 1, "nested": {"a": 1}}]
    result = build_collection_sample_verification(collection="daily_reports", expected_docs=expected, restored_docs=restored)
    assert result["matched"] is True
    assert result["mismatches"] == []
    assert normalize_verification_document(restored[0]) == expected[0]


def test_audit_verification_compares_reference_field_presence_between_expected_and_restored():
    expected = {
        "audit_events": [{
            "id": "evt-1",
            "actor_id": "user-1",
            "created_at": "2026-07-01T00:00:00Z",
            "type": "update",
            "linked_task_id": "task-1",
        }]
    }
    restored = {
        "audit_events": [{
            "_id": "mongo-id",
            "id": "evt-1",
            "actor_id": "user-1",
            "created_at": "2026-07-01T00:00:00Z",
            "type": "update",
            "linked_task_id": "task-1",
        }]
    }
    result = verify_audit_data(expected, restored)
    assert result["state"] == "PASS"
    assert result["collections"]["audit_events"]["entity_references_survived"] is True


def test_compare_fingerprints_ignores_runtime_mutable_notification_collection_drift():
    before = {
        "aggregate_fingerprint": "before",
        "per_collection_record_counts": {"notifications": 10, "users": 2},
        "per_collection_fingerprints": {
            "notifications": {"collection_fingerprint": "notif-a"},
            "users": {"collection_fingerprint": "users-a"},
        },
    }
    after = {
        "aggregate_fingerprint": "after",
        "per_collection_record_counts": {"notifications": 9, "users": 2},
        "per_collection_fingerprints": {
            "notifications": {"collection_fingerprint": "notif-b"},
            "users": {"collection_fingerprint": "users-a"},
        },
    }
    cmp = compare_fingerprints(before, after)
    assert cmp["match"] is True
    assert cmp["difference"]["collection_differences"] == []
    assert "notifications" in cmp["difference"]["ignored_runtime_mutable_collections"]


def test_independent_qa_precheck_allows_review_to_be_created_before_qa_exists():
    evidence = build_restore_evidence_skeleton(
        drill_id="drill-1",
        namespace_prefix="ops8_drill_test",
        authorized_archive_key="backups/x.zip",
        requested_env="preview",
        target_db="masci_safety_preview",
        guard={"owner_token": "token-1"},
    )
    evidence.update({
        "source_authority": {"environment": "preview"},
        "explicit_key_resolution": {"remote_manifest_fanout_enabled": False, "remote_manifest_reads_attempted": 0, "embedded_manifest_loaded": True, "embedded_manifest_reconciled": True, "checksum_validated": True},
        "canonical_before_fingerprint": {"aggregate_fingerprint": "a"},
        "canonical_after_fingerprint": {"aggregate_fingerprint": "a"},
        "canonical_fingerprint_match": True,
        "restore_results": {"collections": {"users": {"expected_record_count": 1}}, "totals": {"parity_result": True}},
        "representative_content_verification": {"state": "PASS", "collections": {}},
        "audit_verification": {"state": "PASS", "collections": {}},
        "identity_role_verification": {"identity_verification_state": "PASS", "role_verification_state": "PASS", "assignment_verification_state": "PASS", "reference_integrity_state": "PASS", "collections": {}},
        "scheduler_state_verification": {"state": "PASS", "scheduler_execution_triggered": False, "collections": {}},
        "photo_object_verification": {"state": "PASS"},
        "cleanup": {"state": "PASS", "orphan_restore_collections": 0},
        "final_health": {"state": "PASS"},
        "guard_release": {"state": "PASS", "released_at": "2026-07-01T00:00:00Z"},
    })
    review = build_independent_qa_review(evidence, reviewer_mode="independent-observer")
    assert review["qa_outcome"] == "PASS"


def test_audit_identity_and_scheduler_verification_fail_closed():
    expected = {
        "audit_events": [{"id": "e1", "actor_id": "u1", "ts": "2026", "kind": "edit", "entity_id": "x1"}],
        "user_directory": [{"id": "u1", "email": "a@test.com"}],
        "role_templates": [{"id": "r1", "name": "admin"}],
        "project_team_assignments": [{"id": "a1", "user_id": "u1"}],
        "scheduler_runs": [{"id": "s1", "state": "queued"}],
    }
    restored_bad = {
        "audit_events": [{"id": "e1", "actor_id": "u2", "ts": "2026", "kind": "edit", "entity_id": "x1"}],
        "user_directory": [{"id": "u9", "email": "b@test.com"}],
        "role_templates": [{"id": "r1", "name": "admin"}],
        "project_team_assignments": [{"id": "a1", "user_id": "missing"}],
        "scheduler_runs": [{"id": "s1", "state": "running"}],
    }
    assert verify_audit_data(expected, restored_bad)["state"] == "FAIL"
    ident = verify_identity_role_data(expected, restored_bad)
    assert ident["identity_verification_state"] == "FAIL" or ident["reference_integrity_state"] == "FAIL"
    sched = verify_scheduler_state(expected, restored_bad)
    assert sched["scheduler_execution_triggered"] is False


def test_completeness_gate_and_independent_qa_rules():
    evidence = build_restore_evidence_skeleton(
        drill_id="d2",
        namespace_prefix="ops8_d2",
        authorized_archive_key="k",
        requested_env="preview",
        target_db="masci_safety_preview",
        guard={"owner_token": "token-2"},
    )
    incomplete = validate_restore_certification_evidence(evidence)
    assert incomplete["certification_eligible"] is False
    evidence.update({
        "source_authority": {"environment": "preview"},
        "explicit_key_resolution": {
            "remote_manifest_fanout_enabled": False,
            "remote_manifest_reads_attempted": 0,
            "embedded_manifest_loaded": True,
            "embedded_manifest_reconciled": True,
            "checksum_validated": True,
            "persisted_checksum": "abc",
            "computed_checksum": "abc",
        },
        "canonical_before_fingerprint": {"aggregate_fingerprint": "x", "per_collection_record_counts": {}, "per_collection_fingerprints": {}},
        "canonical_after_fingerprint": {"aggregate_fingerprint": "x", "per_collection_record_counts": {}, "per_collection_fingerprints": {}},
        "canonical_fingerprint_match": True,
        "restore_results": {"collections": {"daily_reports": {}}, "totals": {"parity_result": True}},
        "representative_content_verification": {"state": "PASS"},
        "audit_verification": {"state": "PASS"},
        "identity_role_verification": {"identity_verification_state": "PASS", "role_verification_state": "PASS", "assignment_verification_state": "PASS", "reference_integrity_state": "PASS"},
        "scheduler_state_verification": {"state": "PASS", "scheduler_execution_triggered": False},
        "photo_object_verification": {"state": "PASS"},
        "cleanup": {"state": "PASS", "orphan_restore_collections": 0},
        "final_health": {"state": "PASS"},
        "guard_release": {"state": "PASS", "released_at": datetime.now(timezone.utc).isoformat()},
    })
    still_pending = validate_restore_certification_evidence(evidence)
    assert still_pending["certification_eligible"] is False
    review = build_independent_qa_review({**evidence, **still_pending}, reviewer_mode="test")
    assert review["qa_outcome"] == "PASS"
    evidence["qa_reviews"] = [review]
    final = validate_restore_certification_evidence(evidence)
    assert final["certification_eligible"] is True
    assert final["evidence_completeness_state"] == "COMPLETE"


def test_complete_evidence_state_uses_complete_label():
    evidence = build_restore_evidence_skeleton(
        drill_id="d3",
        namespace_prefix="ops8_d3",
        authorized_archive_key="k",
        requested_env="preview",
        target_db="masci_safety_preview",
        guard={"owner_token": "token-3"},
    )
    evidence.update({
        "source_authority": {"environment": "preview"},
        "explicit_key_resolution": {
            "remote_manifest_fanout_enabled": False,
            "remote_manifest_reads_attempted": 0,
            "embedded_manifest_loaded": True,
            "embedded_manifest_reconciled": True,
            "checksum_validated": True,
            "persisted_checksum": "abc",
            "computed_checksum": "abc",
        },
        "canonical_before_fingerprint": {"aggregate_fingerprint": "x", "per_collection_record_counts": {}, "per_collection_fingerprints": {}},
        "canonical_after_fingerprint": {"aggregate_fingerprint": "x", "per_collection_record_counts": {}, "per_collection_fingerprints": {}},
        "canonical_fingerprint_match": True,
        "restore_results": {"collections": {"daily_reports": {}}, "totals": {"parity_result": True}},
        "representative_content_verification": {"state": "PASS"},
        "audit_verification": {"state": "PASS"},
        "identity_role_verification": {"identity_verification_state": "PASS", "role_verification_state": "PASS", "assignment_verification_state": "PASS", "reference_integrity_state": "PASS"},
        "scheduler_state_verification": {"state": "PASS", "scheduler_execution_triggered": False},
        "photo_object_verification": {"state": "PASS"},
        "cleanup": {"state": "PASS", "orphan_restore_collections": 0},
        "final_health": {"state": "PASS"},
        "guard_release": {"state": "PASS", "released_at": datetime.now(timezone.utc).isoformat()},
    })
    review = {"qa_outcome": "PASS"}
    evidence["qa_reviews"] = [review]
    final = validate_restore_certification_evidence(evidence)
    assert final["evidence_completeness_state"] == "COMPLETE"