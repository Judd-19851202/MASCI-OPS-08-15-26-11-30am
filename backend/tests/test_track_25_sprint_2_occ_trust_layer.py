"""TRACK 25 · SPRINT 2 · OCC Trust Layer aggregator — contract tests.

These tests focus on the ``GET /api/admin/occ/health`` aggregator's
contract shape and honest-degradation behaviour. Individual evaluators
are unit-tested in isolation; the integration behaviour (auth
passthrough, fan-out) is covered by the frontend testing agent.
"""
from __future__ import annotations

from routes.occ_health_aggregator import (
    CARDS,
    SECTIONS,
    _eval_ai_gateway,
    _eval_api_health,
    _eval_backups_scheduler,
    _eval_draft_health,
    _eval_email_v2,
    _eval_governance,
    _eval_integrations,
    _eval_operations_overview,
    _eval_production_cert,
    _eval_recovery_snapshot,
    _eval_sessions,
    _eval_version,
    _worst_status,
)


NOW = "2026-07-09T23:30:00+00:00"


class TestManifest:
    def test_all_eight_required_sections_present(self):
        section_ids = {sid for sid, _ in SECTIONS}
        required = {
            "platform_runtime", "storage_recovery", "queues_workers",
            "communications", "ai_operations", "daily_reports",
            "identity_security", "integrations",
        }
        assert required == section_ids, (
            f"missing sections: {required - section_ids} · "
            f"extras: {section_ids - required}"
        )

    def test_every_card_maps_to_a_declared_section(self):
        section_ids = {sid for sid, _ in SECTIONS}
        for card in CARDS:
            assert card["section"] in section_ids, (
                f"card {card['id']} has unknown section {card['section']}"
            )

    def test_every_card_declares_endpoint_and_drilldown(self):
        for card in CARDS:
            assert card["endpoint"].startswith("/api/"), card
            assert card["drilldown"].startswith("/admin/"), card
            assert callable(card["evaluator"]), card

    def test_each_required_section_has_at_least_one_card(self):
        section_ids = {sid for sid, _ in SECTIONS}
        seen = {c["section"] for c in CARDS}
        assert section_ids == seen, (
            f"sections without a card: {section_ids - seen}"
        )


class TestEvaluatorDegradation:
    """A failing child probe must never invent GREEN."""

    def test_api_health_none_is_red(self):
        r = _eval_api_health(None, "conn refused", NOW)
        assert r["status"] == "MISMATCH"
        assert "not reachable" in r["summary"].lower()

    def test_version_none_is_unknown(self):
        r = _eval_version(None, "timeout", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_operations_registry_none_is_unknown(self):
        r = _eval_operations_overview(None, "auth", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_recovery_snapshot_none_is_unknown(self):
        r = _eval_recovery_snapshot(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_backups_scheduler_none_is_unknown(self):
        r = _eval_backups_scheduler(None, "no body", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_integrations_none_is_unknown(self):
        r = _eval_integrations(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_email_v2_none_is_unknown(self):
        r = _eval_email_v2(None, "timeout", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_ai_gateway_none_is_unknown(self):
        r = _eval_ai_gateway(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_draft_health_none_is_unknown(self):
        r = _eval_draft_health(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_sessions_none_is_unknown(self):
        r = _eval_sessions(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_governance_none_is_unknown(self):
        r = _eval_governance(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"

    def test_production_cert_none_is_unknown(self):
        r = _eval_production_cert(None, "http 500", NOW)
        assert r["status"] == "UNVERIFIABLE"


class TestEvaluatorTruth:
    def test_api_health_ok_is_green(self):
        r = _eval_api_health({"ok": True, "service": "svc", "ts": NOW}, None, NOW)
        assert r["status"] == "VERIFIED"

    def test_api_health_ok_false_is_red(self):
        r = _eval_api_health({"ok": False, "service": "svc"}, None, NOW)
        assert r["status"] == "MISMATCH"

    def test_operations_overview_critical_ops_produce_red(self):
        body = {"operations": [
            {"status_snapshot": {"status": "critical"}},
            {"status_snapshot": {"status": "healthy"}},
        ]}
        assert _eval_operations_overview(body, None, NOW)["status"] == "MISMATCH"

    def test_operations_overview_all_healthy_is_green(self):
        body = {"operations": [
            {"status_snapshot": {"status": "healthy"}},
            {"status_snapshot": {"status": "healthy"}},
        ]}
        assert _eval_operations_overview(body, None, NOW)["status"] == "VERIFIED"

    def test_recovery_pill_maps_directly(self):
        for pill, expected in (("GREEN", "VERIFIED"), ("YELLOW", "DEGRADED"), ("RED", "MISMATCH")):
            body = {"pill": pill, "backup_age_minutes": 5,
                    "backup_age_target_minutes": 1440,
                    "archive_count": {"r2_total": 10}}
            assert _eval_recovery_snapshot(body, None, NOW)["status"] == expected

    def test_scheduler_alive_is_green(self):
        r = _eval_backups_scheduler({"scheduler": {"alive": True}}, None, NOW)
        assert r["status"] == "VERIFIED"

    def test_scheduler_dormant_low_resurrects_is_yellow(self):
        r = _eval_backups_scheduler(
            {"scheduler": {"alive": False, "resurrect_count": 1}}, None, NOW,
        )
        assert r["status"] == "DEGRADED"

    def test_scheduler_many_resurrects_is_red(self):
        r = _eval_backups_scheduler(
            {"scheduler": {"alive": False, "resurrect_count": 10}}, None, NOW,
        )
        assert r["status"] == "MISMATCH"

    def test_email_v2_empty_critical_route_is_red(self):
        r = _eval_email_v2({"critical_empty_route_keys": ["po"], "band": "green",
                            "mode": "v2"}, None, NOW)
        assert r["status"] == "MISMATCH"

    def test_email_v2_yellow_band_no_empty_is_yellow(self):
        r = _eval_email_v2({"critical_empty_route_keys": [], "band": "yellow",
                            "mode": "v2"}, None, NOW)
        assert r["status"] == "DEGRADED"

    def test_ai_gateway_off_is_yellow(self):
        r = _eval_ai_gateway({"gateway_enabled": False}, None, NOW)
        assert r["status"] == "DEGRADED"

    def test_ai_gateway_on_provider_unavailable_is_red(self):
        r = _eval_ai_gateway({
            "gateway_enabled": True,
            "resolved_provider_available": False,
            "resolved_selected_provider": "anthropic",
        }, None, NOW)
        assert r["status"] == "MISMATCH"

    def test_ai_gateway_on_provider_available_is_green(self):
        r = _eval_ai_gateway({
            "gateway_enabled": True,
            "resolved_provider_available": True,
        }, None, NOW)
        assert r["status"] == "VERIFIED"

    def test_draft_health_failed_drafts_is_red(self):
        r = _eval_draft_health(
            {"buckets": {"failed_last_24h": 1, "abandoned_gt_24h": 0}},
            None, NOW,
        )
        assert r["status"] == "MISMATCH"

    def test_draft_health_zero_is_green(self):
        r = _eval_draft_health({"buckets": {}}, None, NOW)
        assert r["status"] == "VERIFIED"

    def test_sessions_timeouts_off_is_yellow(self):
        r = _eval_sessions({"count": 10, "timeouts_enabled": False}, None, NOW)
        assert r["status"] == "DEGRADED"

    def test_governance_last_scan_object_does_not_break_checked_at(self):
        """Regression: `last_scan` in the governance summary is a nested
        dict, not an ISO string. Must be safely forwarded into evidence,
        not into `checked_at` (which is used for local-time formatting)."""
        r = _eval_governance(
            {"severity_counts": {"high": 5, "critical": 0},
             "health_label": "warning",
             "last_scan": {"started_at": NOW, "detected_total": 5}},
            None, NOW,
        )
        assert r["checked_at"] == NOW  # falls back to the fresh probe time
        assert isinstance(r["evidence"]["last_scan"], dict)

    def test_governance_no_scan_is_green(self):
        r = _eval_governance({"severity_counts": {}, "health_label": "healthy"},
                              None, NOW)
        assert r["status"] == "VERIFIED"


class TestWorstStatus:
    def test_empty_returns_green(self):
        assert _worst_status([]) == "NOT_APPLICABLE"

    def test_red_wins_over_yellow_and_green(self):
        assert _worst_status([
            {"status": "green"}, {"status": "yellow"}, {"status": "red"},
        ]) == "MISMATCH"

    def test_yellow_wins_over_green_and_unknown(self):
        assert _worst_status([
            {"status": "green"}, {"status": "unknown"}, {"status": "yellow"},
        ]) == "UNVERIFIABLE"

    def test_unknown_wins_over_green(self):
        assert _worst_status([{"status": "green"}, {"status": "unknown"}]) == "UNVERIFIABLE"
