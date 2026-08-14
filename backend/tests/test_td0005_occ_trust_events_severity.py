"""TD-0005 — OCC Trust Events "recent events / N critical" truth (SO-05).

Root cause (live production evidence, mascidocs.com, read-only):
- "Recent Platform Events" card (AdminGovernanceTrust unified-trust-events)
  showed counts.critical = 8 and status red.
- /api/admin/occ/trust-events counts.critical = 8 BUT only 6 critical events
  were enumerable in the returned `events` list — counts were tallied over the
  full pre-truncation merged population while `events` was `events[:limit]`.
- Every critical event was a HISTORICAL `deployment_verification` startup-check
  audit row (NO-GO, runtime_commit_does_not_match_intended_release), one per
  backend restart. Canonical /api/admin/deployment-readiness = pass, 0 blocking
  gates → zero CURRENT critical deploy conditions.

Truth invariants:
- deployment_verification audit rows are historical → severity "info", never a
  current critical (genuine current blockers flow as kind=deploy_blocker).
- per-severity counts describe EXACTLY the returned window → headline is
  always enumerable in the events list.
"""
from backend.routes.occ_trust_events import _classify_audit, _tally_window


def test_deployment_verification_audit_row_is_historical_info_not_critical():
    row = {
        "action": "deployment_verification",
        "outcome": "fail",
        "ts": "2026-08-13T22:29:58Z",
        "diff": {"go_no_go": "NO-GO", "failure_reason": "runtime_commit_does_not_match_intended_release"},
    }
    ev = _classify_audit(row)
    assert ev["kind"] == "deploy"
    assert ev["severity"] == "info"  # historical record, not a current critical


def test_genuine_auth_failure_still_critical():
    # Non-deploy audit failures keep their severity (no over-broad downgrade).
    row = {"action": "some_action", "outcome": "error", "ts": "2026-08-13T10:00:00Z"}
    assert _classify_audit(row)["severity"] == "critical"


def test_counts_match_returned_window_exactly():
    # 10 events, limit 4 → counts must describe only the 4 returned, so the
    # headline "N critical" is always enumerable in the returned list.
    events = (
        [{"severity": "critical", "kind": "ops_audit"} for _ in range(3)]
        + [{"severity": "info", "kind": "audit"} for _ in range(7)]
    )
    window, counts, _by_kind, _auth = _tally_window(events, limit=4)
    assert len(window) == 4
    assert counts["critical"] == sum(1 for e in window if e["severity"] == "critical")
    assert counts["critical"] + counts["warning"] + counts["info"] == len(window)


def test_historical_deploy_repeats_do_not_inflate_current_critical():
    # 6 historical deployment_verification NO-GO rows must all classify info,
    # so a "recent events" critical count is not inflated by restart history.
    rows = [
        {"action": "deployment_verification", "outcome": "fail", "ts": f"2026-08-13T2{i}:00:00Z"}
        for i in range(6)
    ]
    classified = [_classify_audit(r) for r in rows]
    _w, counts, _bk, _af = _tally_window(classified, limit=25)
    assert counts["critical"] == 0
    assert counts["info"] == 6
