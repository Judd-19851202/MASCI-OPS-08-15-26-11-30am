"""TRACK 16.05 · Transportation Onboarding & Compliance Center regression.

Locks the Phase 2 contract:

* Default rate schedule = $85.00/hour (active).
* Versioned rate schedule (draft → active retires previous active).
* Carrier + driver document collections store R2 keys (never bytes).
* Document review supports accepted / needs_correction / expired / not_applicable.
* Packet workflow has explicit allowed transitions.
* Packet cannot approve without rate schedule, missing required docs,
  expired docs, or needs-correction docs.
* Eligibility (Phase 2) honors packet, rate ack, docs, inspection, PPE.
* MASCI Hauler Truck Readiness Inspection exists, includes disclaimer,
  uses ready/pending_correction/not_ready/expired (NOT failed/rejected/
  denied), checklist items use pass/needs_correction/not_applicable/
  not_observed, photo evidence stored as R2 keys.
* Leased truck eligibility blocked without ready inspection / expired
  inspection / unresolved critical correction.
* Driver PPE issue can block driver eligibility.
* Admin-only writes; dispatch readiness routes are read-only.
* No public invite route in Phase 2.
* No forbidden status language; no ForgedOps Academy references.
* Track 16.04 tests still present.
* deployment_gate includes Track 16.05.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from lib import transport_eligibility as elig  # noqa: E402
from lib import transport_phase2 as p2  # noqa: E402

PHASE2_LIB = BACKEND / "lib" / "transport_phase2.py"
ROUTES = BACKEND / "routes" / "transportation_phase2.py"
SERVER = BACKEND / "server.py"
GATE = ROOT / "scripts" / "deployment_gate.py"
T16_04_TEST = BACKEND / "tests" / "test_track_16_04_transportation_foundation.py"
PAGE = ROOT / "frontend" / "src" / "pages" / "AdminTransportation.jsx"


# ───────────────── Rate schedule ─────────────────
def test_1_default_rate_is_85_dollars_per_hour():
    assert p2.DEFAULT_HOURLY_RATE == 85.00
    assert p2.DEFAULT_CURRENCY == "USD"


def test_2_only_versioned_rate_change_path():
    src = ROUTES.read_text()
    # POST creates draft · activate retires prior · PATCH guards retired
    assert '"status": "draft"' in src
    assert 'Retired schedules are read-only' in src
    assert 'rate-schedules/{rid}/activate' in src


def test_3_activate_retires_other_active():
    src = ROUTES.read_text()
    assert 'update_many(' in src and '"status": "retired"' in src


def test_4_packet_locks_rate_schedule_id_at_creation():
    src = ROUTES.read_text()
    assert '"rate_schedule_id": active_rate["id"]' in src
    assert 'No active rate schedule' in src


def test_5_packet_preserves_masci_payment_increment_language():
    txt = p2.PAYMENT_RULES_TEXT
    assert "0:15 to 2:00" in txt
    assert "2:01 to 4:00" in txt
    assert "4:01 to 6:00" in txt
    assert "6:01 and above" in txt
    assert "1 hour travel time" in txt
    assert "Standby" in txt
    # Ticket rules language
    assert "5 PM Tuesday" in p2.TICKET_RULES_TEXT
    assert "FleetWatcher" in p2.TICKET_RULES_TEXT
    # Deduction rules language
    assert "0.15-hour" in p2.DEDUCTION_RULES_TEXT
    assert "hot asphalt" in p2.DEDUCTION_RULES_TEXT


# ───────────────── Required document types ─────────────────
def test_6_required_carrier_document_types_exist():
    for t in ("sunbiz_certificate", "mcs_company_snapshot", "w9",
              "insurance_certificate", "hauling_agreement",
              "vehicle_registration", "lien_release_authorization",
              "payment_pickup_authorization"):
        assert t in p2.DOCUMENT_TYPES_CARRIER


def test_7_required_driver_document_types_include_cdl_medical_clearinghouse():
    for t in ("cdl", "medical_card", "clearinghouse"):
        assert t in p2.DOCUMENT_TYPES_DRIVER


def test_8_requirements_catalog_includes_masci_packet_baseline():
    keys = {r["requirement_key"] for r in p2.REQUIREMENTS_CATALOG}
    expected = {
        "company_info", "sunbiz_certificate", "mcs_company_snapshot",
        "w9", "insurance_certificate", "hauling_agreement",
        "lien_release_authorization", "payment_pickup_authorization",
        "rate_acknowledgement", "dispatch_rules_ack",
        "gps_fleetwatcher_ack", "safety_rules_ack",
        "driver_cdl", "driver_medical_card", "driver_clearinghouse",
        "truck_readiness_inspection",
    }
    assert expected.issubset(keys)


def test_9_document_upload_stores_r2_key_not_bytes():
    src = ROUTES.read_text()
    assert "upload_photo_bytes" in src
    assert "file_key" in src
    # Negative: no Mongo blob storage of bytes
    assert ".insert_one({" not in src or "Body=data" not in src.split(".insert_one")[0]


def test_10_document_review_supports_required_statuses():
    for s in ("accepted", "needs_correction", "expired", "not_applicable"):
        assert s in p2.REVIEW_STATUSES


# ───────────────── Packet workflow ─────────────────
def test_11_packet_status_transitions_are_valid():
    # Closed-set transitions; the table must be defined.
    assert set(p2.PACKET_STATUSES) == set(p2.PACKET_TRANSITIONS.keys()) | set()
    # approved → suspended legal; suspended → approved legal (re-instatement);
    # draft → approved illegal (must pass submitted/pending_review)
    assert "approved" not in p2.PACKET_TRANSITIONS["draft"]


def test_12_packet_cannot_approve_with_missing_required_docs():
    src = ROUTES.read_text()
    assert "missing required documents" in src


def test_13_packet_cannot_approve_without_rate_acknowledgement():
    src = ROUTES.read_text()
    assert "without rate schedule acknowledgement" in src


def test_14_packet_cannot_approve_with_expired_required_docs():
    src = ROUTES.read_text()
    assert "at least one required document is expired" in src


# ───────────────── Eligibility (Phase 2) ─────────────────
def test_15_eligibility_blocks_needs_correction_docs():
    r = elig.compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"docs_needs_correction": 2})
    assert r["state"] != "eligible"
    assert any(x["code"] == "documents_needs_correction" for x in r["reasons"])


def test_16_eligibility_blocks_expired_docs():
    r = elig.compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"expired_required_docs": 1})
    assert r["state"] in ("expired", "needs_correction", "not_dispatchable")
    assert any(x["code"] == "documents_expired" for x in r["reasons"])


def test_17_eligibility_blocks_missing_clearinghouse_when_required():
    # Modeled as missing required docs > 0 (the engine doesn't distinguish
    # which doc type is missing; the caller increments the count when any
    # required doc type — including Clearinghouse — is absent).
    r = elig.compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"missing_required_docs": 1})
    assert r["state"] != "eligible"
    assert any(x["code"] == "documents_missing" for x in r["reasons"])


# ───────────────── Audit ─────────────────
def test_18_audit_rows_written_for_packet_rate_doc_events():
    src = ROUTES.read_text()
    for kind in (
        "transport_rate_schedule_create",
        "transport_rate_schedule_update",
        "transport_rate_schedule_activate",
        "transport_packet_create",
        "transport_carrier_document_upload",
        "transport_driver_document_upload",
        "transport_inspection_started",
        "transport_inspection_completed",
    ):
        assert kind in src, f"audit kind {kind} missing"


# ───────────────── RBAC ─────────────────
def test_19_rbac_admin_required_for_writes():
    src = ROUTES.read_text()
    # Every @router.post/@router.patch must depend on require_admin_dep.
    write_lines = [m.start() for m in re.finditer(
        r"@router\.(post|patch)\(", src)]
    for pos in write_lines:
        window = src[pos: pos + 1500]
        assert "Depends(require_admin_dep)" in window, \
            f"write route at offset {pos} missing admin gate"


def test_20_dispatch_routes_are_read_only():
    src = ROUTES.read_text()
    # No /dispatch/transportation/* path with @router.post or @router.patch.
    for m in re.finditer(r"@router\.(post|patch)\(\"(/dispatch[^\"]+)\"", src):
        assert False, f"dispatch route is writeable: {m.group(2)}"


def test_21_no_public_invite_route():
    src = ROUTES.read_text()
    forbidden = ("/public/", "/invite/", "/carrier-portal/")
    for needle in forbidden:
        assert needle not in src, f"Phase 2 must not introduce {needle}"


# ───────────────── Status language ─────────────────
def test_22_status_language_avoids_punitive_terms():
    src = ROUTES.read_text() + "\n" + PHASE2_LIB.read_text() + "\n" + PAGE.read_text()
    for needle in ('"Failed"', '"Rejected"', '"Denied"',
                   "'Failed'", "'Rejected'", "'Denied'",
                   ">Failed<", ">Rejected<", ">Denied<"):
        assert needle not in src, f"forbidden status label {needle!r}"


# ───────────────── ForgedOps Academy isolation ─────────────────
def test_23_no_forgedops_academy_references():
    for p in (ROUTES, PHASE2_LIB, PAGE):
        text = p.read_text()
        assert "ForgedOps Academy" not in text
        assert "forgedops academy" not in text.lower()


# ───────────────── 16.04 preservation + gate wiring ─────────────────
def test_24_track_16_04_tests_still_present():
    assert T16_04_TEST.exists()


def test_25_deployment_gate_includes_16_05():
    assert "test_track_16_05" in GATE.read_text()


# ───────────────── MASCI Hauler Truck Readiness Inspection ─────────────────
def test_26_inspection_collection_exists():
    src = ROUTES.read_text()
    assert "transport_truck_inspections" in src


def test_27_inspection_explicitly_not_dot_inspection():
    txt = p2.INSPECTION_DISCLAIMER
    assert "does not replace" in txt.lower()
    assert "DOT" in txt and "FMCSA" in txt
    assert "operational readiness check" in txt.lower()


def test_28_inspection_checklist_has_all_required_categories():
    cats = {cat for (_k, cat, _l, _crit) in p2.INSPECTION_CHECKLIST}
    assert cats >= {"exterior", "lights", "markings", "cab", "ppe"}


def test_29_required_truck_exterior_items_exist():
    keys = set(p2.inspection_item_keys())
    for k in ("tires_serviceable", "lug_nuts_present", "tailgate_secure",
              "tarp_system_operational", "tarp_covers_bed",
              "no_major_fluid_leaks", "no_unsafe_body_damage", "mirrors_usable"):
        assert k in keys


def test_30_required_lights_warning_items_exist():
    keys = set(p2.inspection_item_keys())
    for k in ("headlights_working", "taillights_working", "brake_lights_working",
              "turn_signals_working", "four_way_flashers",
              "backup_alarm_present", "reflective_tape_visible"):
        assert k in keys


def test_31_required_marking_items_exist():
    keys = set(p2.inspection_item_keys())
    for k in ("company_logo_displayed", "truck_number_displayed",
              "license_plate_present", "registration_available"):
        assert k in keys


def test_32_required_ppe_items_exist():
    keys = set(p2.inspection_item_keys())
    for k in ("ppe_hard_hat", "ppe_high_vis", "ppe_safety_glasses",
              "ppe_work_boots", "ppe_long_pants", "ppe_shirt_required",
              "ppe_acknowledged"):
        assert k in keys


def test_33_result_statuses_use_canonical_set():
    assert set(p2.RESULT_STATUSES) == {"ready", "pending_correction",
                                       "not_ready", "expired"}


def test_34_item_statuses_use_canonical_set():
    assert set(p2.ITEM_STATUSES) == {"pass", "needs_correction",
                                     "not_applicable", "not_observed"}


def test_35_forbidden_inspection_words_absent():
    src = PHASE2_LIB.read_text()
    for w in ("failed", "rejected", "denied"):
        assert w not in src.lower(), f"forbidden word {w!r} in Phase 2 lib"


def test_36_photo_evidence_stored_as_r2_keys():
    src = ROUTES.read_text()
    assert "photo_keys" in src
    # The data model stores photo_keys (string list), never raw image bytes.
    # (Note: the substring `photo_bytes` appears as part of `upload_photo_bytes`
    # — the canonical R2 wrapper — so we check for the storage-blob class.)
    assert '"photo_b64"' not in src
    assert "image_b64" not in src


# ───────────────── Eligibility integration with inspection ─────────────────
def test_37_leased_truck_blocked_without_inspection():
    r = elig.compute_transport_eligibility(
        "truck", {"status": "active"},
        {"ownership": "leased_carrier", "inspection_result": None,
         "inspection_required": True})
    assert r["state"] != "eligible"
    assert any(x["code"] == "inspection_missing" for x in r["reasons"])


def test_38_leased_truck_blocked_by_expired_inspection():
    r = elig.compute_transport_eligibility(
        "truck", {"status": "active"},
        {"ownership": "leased_carrier", "inspection_result": "expired"})
    assert r["state"] == "expired"


def test_39_leased_truck_blocked_by_unresolved_critical_correction():
    r = elig.compute_transport_eligibility(
        "truck", {"status": "active"},
        {"ownership": "leased_carrier", "inspection_result": "not_ready"})
    assert r["state"] != "eligible"
    assert any(x["code"] == "inspection_not_ready" for x in r["reasons"])


def test_40_driver_ppe_issue_blocks_driver():
    r = elig.compute_transport_eligibility(
        "person", {"status": "active", "kind": "leased_driver"},
        {"ppe_issue": True})
    assert r["state"] == "not_dispatchable"
    assert any(x["code"] == "ppe_issue" for x in r["reasons"])


def test_41_admin_only_for_inspection_writes():
    src = ROUTES.read_text()
    # Every inspection-route decorator (POST/PATCH) must be backed by
    # require_admin_dep within the next 1200 chars (the handler body).
    write_decorators = list(re.finditer(
        r'@router\.(post|patch)\(\"/admin/transportation/(trucks/\{tid\}/inspections|inspections/\{iid\}[^\"]*)\"',
        src))
    assert len(write_decorators) >= 3, "expected inspection write decorators present"
    for m in write_decorators:
        window = src[m.start(): m.start() + 1500]
        assert "Depends(require_admin_dep)" in window, \
            f"inspection write at {m.start()} missing admin gate"


def test_42_dispatch_readiness_route_is_read_only():
    src = ROUTES.read_text()
    # GET /dispatch/transportation/trucks/{tid}/readiness exists, no POST/PATCH on same path.
    assert re.search(r"@router\.get\(\"/dispatch/transportation/trucks/\{tid\}/readiness\"", src)
    for m in re.finditer(r"@router\.(post|patch)\(\"(/dispatch[^\"]*readiness[^\"]*)\"", src):
        assert False, f"dispatch readiness must be read-only, found {m.group(2)}"


def test_43_inspection_lifecycle_audit_kinds_present():
    src = ROUTES.read_text()
    for k in ("transport_inspection_started",
              "transport_inspection_item_updated",
              "transport_inspection_completed"):
        assert k in src


def test_44_inspection_disclaimer_preserved_in_records():
    src = ROUTES.read_text()
    assert '"disclaimer": INSPECTION_DISCLAIMER' in src


def test_45_no_claim_replaces_dot_fmcsa():
    # Phrase must explicitly disclaim DOT/FMCSA replacement.
    assert "does not replace the carrier's required DOT/FMCSA" in p2.INSPECTION_DISCLAIMER


# ───────────────── Inspection triggers, frequency, scheduling ─────────────────
def test_46_inspection_triggers_cover_required_set():
    for t in ("initial_onboarding", "annual_recertification", "random",
              "safety_concern", "incident_or_accident", "management_requested",
              "dispatch_requested"):
        assert t in p2.INSPECTION_TRIGGERS


def test_47_annual_default_is_12_months_configurable():
    assert p2.INSPECTION_DEFAULT_EXPIRATION_MONTHS == 12
    # Configurable via expires_in_months on /complete (must exist in route source).
    src = ROUTES.read_text()
    assert "expires_in_months" in src


def test_48_dashboard_endpoint_exposes_due_and_overdue():
    src = ROUTES.read_text()
    assert "/dispatch/transportation/readiness-summary" in src
    for needle in ("due_within_30d", "due_within_14d", "due_within_7d",
                   "due_today", "overdue"):
        assert needle in src


# ───────────────── Bootstrap idempotency surface ─────────────────
def test_49_bootstrap_function_exists_and_is_idempotent():
    import inspect
    assert inspect.iscoroutinefunction(p2.bootstrap_track_16_05)
    src = PHASE2_LIB.read_text()
    assert "Idempotent" in src or "idempotent" in src
    # Re-running must not duplicate the default active rate schedule.
    # The bootstrap consults find_one() before insert.
    assert "existing_active = await db.transport_rate_schedules.find_one(" in src
    assert "if not existing_active:" in src


# ───────────────── Frontend page (Phase 2 sections present) ─────────────────
def test_50_admin_transportation_page_has_phase1_tabs():
    # Phase 2 may extend the page later; this lock guarantees the Phase 1
    # surface remains addressable. Track 16.06 reorganized the page into
    # nested routes under /admin/transportation/* — the Phase 1 surfaces
    # are now reachable via the TransportationSubNav (txnav-carriers etc.)
    # and via the individual list pages. Either form is acceptable.
    shared = ROOT / "frontend" / "src" / "pages" / "transportation" / "_shared.jsx"
    if shared.exists():
        src = shared.read_text()
        for label in ("Carriers", "Drivers", "Trucks"):
            assert f'"{label}"' in src
    else:
        src = PAGE.read_text()
        for tid in ("tab-carriers", "tab-drivers", "tab-trucks", "tab-eligibility"):
            assert f'data-testid="{tid}"' in src
