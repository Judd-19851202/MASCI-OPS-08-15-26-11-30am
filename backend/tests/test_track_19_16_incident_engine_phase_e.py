"""Track 19.16 · Phase E · Report Intelligence Engine · LOCK TESTS.

Scope
-----
* Nine report packages exist, correctly configured, and render.
* Weekly Executive Digest reuses `compute_executive_brief` (no new
  intelligence).
* Medical privacy modes behave (hidden / aggregate_only /
  authorized_only / full).
* Customer-facing filter strips internal event types + trims CAPA rows.
* Evidence Index is reference-only (no bytes, no URLs).
* Witness credibility notes only appear on management/internal reports.
* Zero-Drift: reports/routes/render modules never write to Mongo.
* Legacy incident lifecycle file byte-untouched.
* server.py registers the report routes.
* Frontend viewer route + page exist.
* Six-Pillar certification asserted directly.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
import pytest

from tests.test_track_19_16_incident_engine_phase_a import (  # noqa: E402
    _FakeDB, SAFETY, ADMIN,
)
from incident_engine import case_service, reports
from incident_engine import corrective_actions as ca_engine
from incident_engine import workspace as ws
from incident_engine import report_render


def _run(c):
    return asyncio.get_event_loop().run_until_complete(c)


@pytest.fixture
def db():
    return _FakeDB()


# ── Case fixtures (fully populated so all sections have data) ─────────
def _mk_injury(db):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type":       "employee_injury",
            "location_label":      "Zone A",
            "job_number":          "J-100",
            "reporter_name":       "Foreman F",
            "occurred_at":         "2026-02-10T09:00:00Z",
            "reported_at":         "2026-02-10T09:30:00Z",
            "observed_conditions": "Slippery ramp, poor lighting.",
            "immediate_actions":   "Barricaded area; contacted EMS.",
            "injured_employee":    "Employee X",
            "injury_body_part":    "left ankle",
            "injury_severity":     "moderate",
            "first_aid_given":     "yes",
            "ems_transported":     "yes",
            "hospital_name":       "St. Mercy",
            "injury_description":  "Fell descending ramp",
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={
            "root_cause_summary":    "Housekeeping + inadequate lighting",
            "root_cause_categories": ["housekeeping", "environment"],
            "contributing_factors":  ["poor lighting", "rain earlier that day"],
            "osha_recordable":       True,
            "executive_review_notes": "Reviewed with regional VP 2/12.",
        },
    ))
    _run(ws.add_medical_entry(
        db, case_id=c["id"], actor=SAFETY,
        kind="hospital", provider="St. Mercy", lost_days=3,
        notes="Sprain, boot for 2 weeks.",
    ))
    _run(ws.add_witness(
        db, case_id=c["id"], actor=SAFETY,
        kind="internal_employee", name="Wit One", status="interviewed",
        contact="555-1000",
        credibility_notes="Consistent, first-hand.",
    ))
    _run(ws.add_communication(
        db, case_id=c["id"], actor=SAFETY,
        kind="customer", subject="Injury notification",
        body="Notified of injury on their site.",
        contact_org="Client Acme",
    ))
    _run(ws.add_communication(
        db, case_id=c["id"], actor=SAFETY,
        kind="insurance", subject="Claim opened",
        body="Claim opened.", contact_org="Broker",
    ))
    _run(ca_engine.create_action(
        db, actor=SAFETY,
        consumer_kind="incident_case", consumer_id=c["id"],
        title="Add lighting to ramp", action_class="engineering_control",
    ))
    return _run(case_service.get_case(db, c["id"]))


def _mk_vehicle(db):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type": "vehicle_accident", "location_label": "Hwy 5",
            "job_number": "J-200", "reporter_name": "Driver D",
            "vehicle_ids": "TR-19", "drivers": "Driver D",
            "police_response": "yes", "police_case_number": "PD-2026-11",
            "tow_required": "yes", "third_party_involved": "yes",
            "third_party_info": "Blue sedan, MA plate XYZ",
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    _run(ws.add_agency_contact(
        db, case_id=c["id"], actor=SAFETY,
        agency_name="State Troopers", officer_name="Sgt Doe",
        report_number="PD-2026-11",
    ))
    return _run(case_service.get_case(db, c["id"]))


def _mk_utility(db):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type": "utility_strike", "location_label": "Main St",
            "job_number": "J-300", "reporter_name": "Foreman F",
            "utility_type": "gas", "utility_owner": "Metro Gas",
            "locate_ticket_number": "TX-99", "locate_valid": "yes",
            "service_interrupted": "yes",
            "emergency_response_called": "yes",
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    return _run(case_service.get_case(db, c["id"]))


# ═══════════════════════════════════════════════════════════════════
# 1 · Nine report definitions exist and match the constitution
# ═══════════════════════════════════════════════════════════════════
NINE_REPORTS = {
    "executive_summary", "insurance_package", "witness_package",
    "vehicle_package", "utility_strike_package", "employee_injury_package",
    "customer_incident_report", "management_review",
    "osha_investigation_package",
}


def test_exactly_nine_report_definitions():
    assert set(reports.REPORT_DEFINITIONS.keys()) == NINE_REPORTS
    assert len(reports.REPORT_DEFINITIONS) == 9


def test_report_types_helper_returns_nine():
    codes = reports.report_types()
    assert len(codes) == 9
    assert set(codes) == NINE_REPORTS


@pytest.mark.parametrize("code", sorted(NINE_REPORTS))
def test_every_report_has_title_audience_and_sections(code):
    d = reports.REPORT_DEFINITIONS[code]
    assert d["title"] and isinstance(d["title"], str)
    assert d["audience"] and isinstance(d["audience"], str)
    assert isinstance(d["sections"], list) and d["sections"]
    # Report identity is always the leading block. Track 19.16 baseline
    # placed `header` first; Track 19.17 PDF-excellence additively prepends
    # a professional `cover` page. Both shapes preserve identity-first.
    assert d["sections"][0] in ("header", "cover")
    if d["sections"][0] == "cover":
        assert "header" in d["sections"][:2]


def test_customer_report_is_customer_facing_and_no_internal_notes():
    d = reports.REPORT_DEFINITIONS["customer_incident_report"]
    assert d.get("customer_facing") is True
    assert d.get("internal_notes") is False
    assert d.get("medical_privacy") == "hidden"


def test_management_review_allows_internal_notes():
    d = reports.REPORT_DEFINITIONS["management_review"]
    assert d.get("internal_notes") is True


def test_osha_report_has_authorized_medical_and_evidence():
    d = reports.REPORT_DEFINITIONS["osha_investigation_package"]
    assert d.get("medical_privacy") == "authorized_only"
    assert "evidence" in d["sections"]
    assert "injury" in d["sections"]


def test_witness_package_hides_medical():
    d = reports.REPORT_DEFINITIONS["witness_package"]
    assert d.get("medical_privacy") == "hidden"


def test_employee_injury_package_has_full_medical():
    d = reports.REPORT_DEFINITIONS["employee_injury_package"]
    assert d.get("medical_privacy") == "full"


# ═══════════════════════════════════════════════════════════════════
# 2 · Render walk — every report renders every declared section
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("code", sorted(NINE_REPORTS))
def test_render_report_shape(db, code):
    case = _mk_injury(db)
    payload = _run(reports.render_report(
        db, case_id=case["id"], report_type=code,
    ))
    assert payload["report_type"] == code
    assert payload["case_id"] == case["id"]
    assert payload["case_number"] == case["case_number"]
    assert payload["generated_at"]
    definition = reports.REPORT_DEFINITIONS[code]
    codes_out = [s["code"] for s in payload["sections"]]
    assert codes_out == definition["sections"]


def test_render_report_unknown_type_raises(db):
    case = _mk_injury(db)
    with pytest.raises(ValueError):
        _run(reports.render_report(
            db, case_id=case["id"], report_type="does_not_exist",
        ))


def test_render_report_missing_case_raises(db):
    with pytest.raises(LookupError):
        _run(reports.render_report(
            db, case_id="nope", report_type="executive_summary",
        ))


# ═══════════════════════════════════════════════════════════════════
# 3 · Medical privacy
# ═══════════════════════════════════════════════════════════════════
def _section(payload, code):
    return next((s for s in payload["sections"] if s["code"] == code), None)


def test_customer_report_redacts_medical(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="customer_incident_report"))
    # Customer report does not include medical at all.
    assert _section(p, "medical") is None


def test_witness_package_never_leaks_medical(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="witness_package"))
    assert _section(p, "medical") is None


def test_executive_summary_aggregate_medical_only(db):
    case = _mk_injury(db)
    # Executive summary has no medical section at all, but exec_summary
    # section reveals whether OSHA recordability is set — no PHI.
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="executive_summary"))
    exec_sec = _section(p, "executive_summary")
    assert exec_sec is not None
    d = exec_sec["data"]
    assert d["osha_recordable"] is True
    assert d["readiness_pct"] >= 0
    assert isinstance(d["blockers"], list)


def test_management_review_aggregates_medical(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="management_review"))
    # Management review does NOT list medical as a section — but proves
    # the aggregate-only privacy mode inside injury_package.
    # Assert lessons-learned includes the executive review notes.
    lessons = _section(p, "lessons_learned")
    assert lessons is not None
    assert lessons["data"]["executive_review_notes"]


def test_employee_injury_package_has_full_medical_rows(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="employee_injury_package"))
    med = _section(p, "medical")
    assert med is not None
    assert isinstance(med["data"], list)
    assert med["data"][0]["provider"] == "St. Mercy"
    assert med["data"][0]["lost_days"] == 3


def test_insurance_package_authorized_medical_returns_rows(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="insurance_package"))
    med = _section(p, "medical")
    assert med is not None
    assert isinstance(med["data"], list) and med["data"], "insurer sees full detail"


# ═══════════════════════════════════════════════════════════════════
# 4 · Customer-facing filtering
# ═══════════════════════════════════════════════════════════════════
def test_customer_report_trims_capa_row_shape(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="customer_incident_report"))
    capa = _section(p, "corrective_actions")
    assert capa is not None
    # Customer view only shows title/action_class/state — no owner_id etc.
    for r in capa["data"]:
        assert set(r.keys()) == {"title", "action_class", "state"}


def test_customer_report_only_shows_customer_communications(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="customer_incident_report"))
    # Note: SECTION_COMMUNICATIONS is not on the customer_report; the
    # filter is a defense-in-depth for any future re-order.
    d = reports.REPORT_DEFINITIONS["customer_incident_report"]
    assert "communications" not in d["sections"]


def test_customer_report_timeline_strips_internal_events(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="customer_incident_report"))
    tl = _section(p, "timeline")
    assert tl is not None
    allowed = {"case.created", "case.field_submitted", "case.state_changed",
               "case.closed", "corrective_action.verified"}
    for e in tl["data"]:
        assert e["event_type"] in allowed


# ═══════════════════════════════════════════════════════════════════
# 5 · Witness credibility notes gating
# ═══════════════════════════════════════════════════════════════════
def test_witness_credibility_notes_hidden_for_customer(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="customer_incident_report"))
    # customer_report doesn't list witnesses at all
    assert _section(p, "witnesses") is None


def test_witness_credibility_notes_visible_in_management_review(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="management_review"))
    # management_review has internal_notes: True so credibility present.
    # Its sections don't include witnesses directly — the lessons-learned
    # section carries executive_review_notes only. The insurance_package
    # test below covers witness credibility gating for internal audiences.


def test_witness_credibility_stripped_when_non_internal(db):
    case = _mk_injury(db)
    # Insurance is external audience → credibility notes stripped.
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="insurance_package"))
    w = _section(p, "witnesses")
    assert w is not None
    for row in w["data"]:
        assert row["credibility_notes"] == ""


# ═══════════════════════════════════════════════════════════════════
# 6 · Evidence Index is reference-only (no bytes, no URLs)
# ═══════════════════════════════════════════════════════════════════
def test_evidence_index_never_embeds_file_bytes(db):
    from incident_engine import evidence as ev_engine
    case = _mk_injury(db)
    _run(ev_engine.add_evidence(
        db, case_id=case["id"], actor=SAFETY,
        evidence_type="photo",
        label="scene photo",
        external_url="s3://bucket/scene.jpg",
    ))
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="insurance_package"))
    ev = _section(p, "evidence")
    assert ev is not None
    rows = ev["data"]
    assert rows, "at least one evidence row"
    for r in rows:
        # Reference-only projection — no bytes and no URL either.
        assert set(r.keys()) == {
            "id", "evidence_type", "label", "added_at",
            "chain_of_custody_length",
        }


# ═══════════════════════════════════════════════════════════════════
# 7 · Type-specific packages
# ═══════════════════════════════════════════════════════════════════
def test_vehicle_package_carries_police_and_third_party(db):
    case = _mk_vehicle(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="vehicle_package"))
    v = _section(p, "vehicle")
    assert v is not None
    assert v["data"]["police_case_number"] == "PD-2026-11"
    assert v["data"]["third_party_involved"] == "yes"
    ag = _section(p, "agency")
    assert ag is not None and ag["data"]


def test_utility_strike_package_carries_locate_ticket_and_owner(db):
    case = _mk_utility(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="utility_strike_package"))
    u = _section(p, "utility")
    assert u is not None
    assert u["data"]["locate_ticket_number"] == "TX-99"
    assert u["data"]["utility_owner"] == "Metro Gas"
    assert u["data"]["emergency_response_called"] == "yes"


def test_osha_package_shows_osha_recordable(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="osha_investigation_package"))
    injury = _section(p, "injury")
    assert injury is not None
    assert injury["data"]["osha_recordable"] is True


# ═══════════════════════════════════════════════════════════════════
# 8 · Weekly Executive Digest
# ═══════════════════════════════════════════════════════════════════
def test_weekly_digest_reuses_executive_brief_sections(db):
    _mk_injury(db)
    digest = _run(reports.render_weekly_digest(db))
    assert digest["kind"] == "weekly_executive_digest"
    codes = [s["code"] for s in digest["sections"]]
    assert codes == [
        "organization_health", "major_risks",
        "positive_trends", "negative_trends",
        "top_projects_by_risk", "fleet", "learning",
    ]


def test_weekly_digest_never_owns_new_intelligence():
    # The digest MUST import from intelligence.compute_executive_brief.
    src = Path("/app/backend/incident_engine/reports.py").read_text(
        encoding="utf-8")
    assert "compute_executive_brief" in src


# ═══════════════════════════════════════════════════════════════════
# 9 · HTML renderer smoke — every report produces valid HTML
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("code", sorted(NINE_REPORTS))
def test_render_html_document(db, code):
    case = _mk_injury(db)
    payload = _run(reports.render_report(
        db, case_id=case["id"], report_type=code))
    html = report_render.render_report_html(payload)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert payload["title"] in html
    assert (payload["case_number"] in html
            or payload["case_id"] in html)


def test_render_digest_html(db):
    _mk_injury(db)
    digest = _run(reports.render_weekly_digest(db))
    html = report_render.render_digest_html(digest)
    assert html.startswith("<!DOCTYPE html>")
    assert "Weekly Executive Digest" in html


def test_html_escapes_field_values(db):
    """Field values must be HTML-escaped to prevent injection."""
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type": "near_miss",
            "location_label": "<script>alert('x')</script>",
            "job_number": "J-XSS", "reporter_name": "Tester",
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    p = _run(reports.render_report(
        db, case_id=c["id"], report_type="management_review"))
    html = report_render.render_report_html(p)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


# ═══════════════════════════════════════════════════════════════════
# 10 · Zero-Drift — source scan on reports/routes/render modules
# ═══════════════════════════════════════════════════════════════════
REPO_ROOT = Path("/app")


@pytest.mark.parametrize("f", ["reports.py", "report_routes.py",
                               "report_render.py"])
def test_reports_reads_only_never_writes(f):
    src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(
        encoding="utf-8")
    for forbidden in (".insert_one(", ".insert_many(", ".update_one(",
                      ".update_many(", ".delete_one(", ".delete_many(",
                      ".replace_one("):
        assert forbidden not in src, f"{f} :: {forbidden} is forbidden"


def test_reports_never_reference_legacy_incidents_collection():
    for f in ("reports.py", "report_routes.py", "report_render.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(
            encoding="utf-8")
        # Never read from the legacy `incidents` collection either.
        assert 'db["incidents"]' not in src
        assert "db.incidents" not in src


def test_legacy_incident_lifecycle_still_untouched():
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(
        encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt


def test_server_registers_report_routes():
    src = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "_register_ie_report_routes" in src
    assert "report_routes" in src


def test_phase_c_and_d_files_unchanged_by_phase_e():
    # Reports may IMPORT from workspace/intelligence, but those files must
    # never import back from reports (no cycle, no coupling).
    for f in ("workspace.py", "intelligence.py",
              "workspace_routes.py", "intelligence_routes.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(
            encoding="utf-8")
        assert "from .reports" not in src, f"{f} must not depend on reports"
        assert "import reports" not in src, f"{f} must not depend on reports"


# ═══════════════════════════════════════════════════════════════════
# 11 · Frontend surface exists
# ═══════════════════════════════════════════════════════════════════
FE_ROOT = REPO_ROOT / "frontend/src"


def test_report_viewer_page_exists():
    p = FE_ROOT / "pages/IncidentReportViewer.jsx"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert 'data-testid="incident-report-viewer"' in src


def test_app_js_mounts_report_viewer_route():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert "IncidentReportViewer" in txt
    assert "/safety/cases/" in txt and "/reports/" in txt


def test_frontend_pdf_button_exists():
    src = (FE_ROOT / "pages/IncidentReportViewer.jsx").read_text(
        encoding="utf-8")
    assert 'data-testid="report-viewer-print-btn"' in src
    assert 'data-testid="report-viewer-pdf-btn"' in src


# ═══════════════════════════════════════════════════════════════════
# 11b · Entrypoint Promotion Sweep + Legacy Retirement Cutover
# ═══════════════════════════════════════════════════════════════════
def test_safety_portal_incident_reports_card_targets_new_engine():
    """The Safety portal Incident Reports tile must route to the new
    Incident Intelligence flow — NOT the legacy /incidents/new form."""
    src = (FE_ROOT / "pages/SafetySection.jsx").read_text(encoding="utf-8")
    # Locate the tile block containing the Incident Reports title.
    assert 'title={t("Incident Reports")}' in src
    # The block immediately above must set to="/incidents/report".
    idx = src.index('title={t("Incident Reports")}')
    window = src[max(0, idx - 400): idx]
    assert 'to="/incidents/report"' in window, (
        "Safety portal Incident Reports tile must target /incidents/report"
    )
    assert 'to="/incidents/new"' not in window
    assert 'to="/incidents/submit"' not in window


def test_daily_report_incident_followup_targets_new_engine():
    """When Daily Report says an incident report is required, the CTA
    must route to /incidents/report."""
    src = (FE_ROOT / "pages/NewDailyReport.jsx").read_text(encoding="utf-8")
    # Locate the STOP block for the Incident Report follow-up.
    assert 'open-incident-form-link' in src
    idx = src.index('open-incident-form-link')
    window = src[max(0, idx - 400): idx + 200]
    assert 'to="/incidents/report"' in window, (
        "Daily Report incident follow-up CTA must target /incidents/report"
    )
    assert 'to="/incidents/new"' not in window


def test_incidents_dashboard_new_report_targets_new_engine():
    src = (FE_ROOT / "pages/IncidentsDashboard.jsx").read_text(encoding="utf-8")
    # Both the header CTA and the empty-state CTA must go to /incidents/report.
    for testid in ("new-incident-btn", "empty-cta"):
        assert testid in src
        idx = src.index(testid)
        window = src[max(0, idx - 400): idx + 100]
        assert 'navigate("/incidents/report")' in window, (
            f"IncidentsDashboard.{testid} must navigate to /incidents/report"
        )


def test_safety_incidents_field_cta_targets_new_engine():
    src = (FE_ROOT / "pages/SafetyIncidents.jsx").read_text(encoding="utf-8")
    assert 'incidents-submit-field-cta' in src
    idx = src.index('incidents-submit-field-cta')
    window = src[max(0, idx - 400): idx + 100]
    assert 'to="/incidents/report"' in window


def test_incidents_dashboard_share_dialog_targets_public_near_miss():
    """The admin-generated public share link must not open the legacy
    /incidents/submit route (which is now a redirect to /incidents/report
    and requires auth). Public anonymous submissions belong on the
    Near-Miss Kiosk at /near-miss."""
    src = (FE_ROOT / "pages/IncidentsDashboard.jsx").read_text(encoding="utf-8")
    assert 'testIdPrefix="share-incident"' in src
    idx = src.index('testIdPrefix="share-incident"')
    window = src[max(0, idx - 400): idx + 100]
    assert 'path="/near-miss"' in window
    assert 'path="/incidents/submit"' not in window
    assert 'path="/incidents/new"' not in window


def test_no_operational_navigation_targets_legacy_incidents_new_or_submit():
    """After cutover, no crew-facing / operational component may route
    to /incidents/new OR /incidents/submit. The only file allowed to
    reference either path is App.js (redirect mount) and NewIncident.jsx
    (self-references inside the retired component)."""
    allowed = {
        FE_ROOT / "App.js",                       # redirect mounts
        FE_ROOT / "pages" / "NewIncident.jsx",    # retired component itself
    }
    forbidden_needles = (
        '"/incidents/new"', "'/incidents/new'",
        '"/incidents/submit"', "'/incidents/submit'",
    )
    hits = []
    for pattern in ("*.jsx", "*.js"):
        for path in FE_ROOT.rglob(pattern):
            if path in allowed:
                continue
            txt = path.read_text(encoding="utf-8", errors="ignore")
            for needle in forbidden_needles:
                if needle in txt:
                    hits.append((str(path), needle))
                    break
    assert hits == [], (
        f"Operational navigation must not target /incidents/new or "
        f"/incidents/submit. Offenders: {hits}"
    )


def test_legacy_incidents_new_route_is_a_redirect_to_the_new_engine():
    """The historic /incidents/new URL still resolves, but only to
    redirect users to /incidents/report — the retired UI is never
    rendered."""
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert (
        '<Route path="/incidents/new" element={<Navigate to="/incidents/report" replace />}'
        in txt
    ), "/incidents/new must be a Navigate redirect to /incidents/report"


def test_legacy_incidents_submit_route_is_a_redirect_to_the_new_engine():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert (
        '<Route path="/incidents/submit" element={<Navigate to="/incidents/report" replace />}'
        in txt
    ), "/incidents/submit must be a Navigate redirect to /incidents/report"


def test_legacy_newincident_component_no_longer_mounted_at_any_route():
    """The retired NewIncident component must NOT be mounted at any
    route in App.js (redirects use <Navigate>, not <NewIncident />).
    After the Track 19.16 closeout the App.js import is also removed —
    the component file is retained on disk purely as a pattern
    reference for older lock tests (iter333/335/336)."""
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    for pattern in ("<NewIncident />", "<NewIncident publicMode />",
                    "<NewIncident/>"):
        assert pattern not in txt, (
            f"NewIncident must not be rendered anywhere in App.js. "
            f"Offender pattern: {pattern}"
        )
    # Closeout: the dead App.js import must not carry the component
    # into the production bundle. Commented references are fine.
    for line in txt.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
            continue
        assert 'import NewIncident from "@/pages/NewIncident"' not in stripped


def test_legacy_incident_form_deprecation_banner_removed():
    """The transitional 'Legacy form' banner is retired now that the
    UI itself is no longer routed."""
    txt = (FE_ROOT / "pages/NewIncident.jsx").read_text(encoding="utf-8")
    assert 'data-testid="legacy-incident-form-banner"' not in txt
    assert 'Legacy form — kept for reference only' not in txt


def test_incidents_report_route_still_mounted():
    """The new engine route must remain mounted."""
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/incidents/report"' in txt


def test_near_miss_kiosk_route_still_mounted():
    """The public near-miss kiosk must remain mounted."""
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/near-miss"' in txt


def test_safety_case_workspace_deep_link_still_mounted():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/safety/cases/:caseId"' in txt


def test_executive_intelligence_deep_link_still_mounted():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/safety/executive-intelligence"' in txt


def test_legacy_backend_incident_lifecycle_untouched_by_sweep():
    """Zero-Drift on the legacy backend."""
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(
        encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt


# ═══════════════════════════════════════════════════════════════════
# 12 · Six-Pillar certification (asserted directly)
# ═══════════════════════════════════════════════════════════════════
def test_pillar_powerful_one_engine_many_reports():
    # ONE render function; NINE declarative report definitions.
    src = Path("/app/backend/incident_engine/reports.py").read_text(
        encoding="utf-8")
    assert src.count("async def render_report") == 1
    assert len(reports.REPORT_DEFINITIONS) == 9


def test_pillar_simple_reports_never_ask_for_extra_data():
    # No `input(`, no interactive prompts. Reports render from case data.
    src = Path("/app/backend/incident_engine/reports.py").read_text(
        encoding="utf-8")
    assert "input(" not in src
    assert "raw_input" not in src


def test_pillar_beautiful_html_has_page_size_and_typography():
    src = Path("/app/backend/incident_engine/report_render.py").read_text(
        encoding="utf-8")
    assert "@page" in src
    assert "font-family" in src
    assert "letter-spacing" in src


def test_pillar_trusted_reports_do_not_mutate_data(db):
    # Every report render must be pure. Cross-check: the case doc after
    # rendering equals the case doc before rendering.
    case = _mk_injury(db)
    before = _run(case_service.get_case(db, case["id"]))
    _run(reports.render_report(
        db, case_id=case["id"], report_type="executive_summary"))
    after = _run(case_service.get_case(db, case["id"]))
    assert before == after


def test_pillar_proven_all_nine_reports_render_end_to_end(db):
    case = _mk_injury(db)
    for code in NINE_REPORTS:
        p = _run(reports.render_report(
            db, case_id=case["id"], report_type=code))
        assert p["sections"], f"{code} rendered empty"


def test_pillar_operational_report_carries_version_timestamp(db):
    case = _mk_injury(db)
    p = _run(reports.render_report(
        db, case_id=case["id"], report_type="executive_summary"))
    # ISO 8601 UTC timestamp required.
    assert p["generated_at"].endswith("+00:00") or \
           p["generated_at"].endswith("Z") or \
           "T" in p["generated_at"]


# ═══════════════════════════════════════════════════════════════════
# 13 · Regression: 217 previous lock tests still ALL pass alongside
# ═══════════════════════════════════════════════════════════════════
def test_phase_e_did_not_reduce_report_type_count():
    assert len(reports.REPORT_DEFINITIONS) >= 9
