#!/usr/bin/env python3
"""
M0.35 Reality Validation harness — Phase V.1 · 2026-05-29.

Drives 4 realistic ODR scenarios end-to-end against the live preview API:

  1. Airport — Taxiway Closure (FAA · escorts · FOD · paving)
  2. Drainage / Utility (locate delay · trench · pipe · safety observation)
  3. Asphalt Operation (trucking · tonnage · plant issue · MOT · density)
  4. Concrete / Structures (pour · weather · QC issue · amendment)

Output written to:
  /app/memory/M0_35_REALITY_VALIDATION_RAW.json

This script is the EVIDENCE SOURCE for ODR_REALITY_VALIDATION_REPORT.md
+ ODR_REALITY_GAP_AUDIT.md.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / "frontend" / ".env"
URL = ""
for line in ENV_FILE.read_text().splitlines():
    if line.startswith("REACT_APP_BACKEND_URL="):
        URL = line.split("=", 1)[1].strip().strip('"')
URL = URL.rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def login() -> str:
    r = requests.post(
        f"{URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


def H(token):
    return {"Content-Type": "application/json", "X-Admin-Token": token}


def scenario(name, payload_create, patches, headers, dry_obs):
    """Run one scenario. Returns dict with all timing + outputs."""
    t0 = time.time()
    obs = {"name": name, "started_at": utcnow(), "operations": []}

    # Create
    t = time.time()
    r = requests.post(f"{URL}/api/odr", json=payload_create, headers=headers, timeout=15)
    obs["operations"].append({"op": "create", "ms": int((time.time() - t) * 1000), "status": r.status_code})
    if r.status_code != 200:
        obs["error"] = r.text
        return obs
    odr = r.json()
    obs["doc_id"] = odr["doc_id"]
    obs["odr_id"] = odr["id"]

    # Apply each patch
    for label, patch_body in patches:
        t = time.time()
        r = requests.patch(
            f"{URL}/api/odr/{odr['id']}", json=patch_body, headers=headers, timeout=15,
        )
        obs["operations"].append({
            "op": f"patch:{label}",
            "ms": int((time.time() - t) * 1000),
            "status": r.status_code,
            "error": None if r.status_code == 200 else r.text[:200],
        })

    # Ack signature + submit
    t = time.time()
    r = requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"signature": {"foreman_acknowledgement": {
            "acknowledged": True,
            "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "I confirm this report is true and complete.",
        }}},
        headers=headers, timeout=15,
    )
    obs["operations"].append({"op": "patch:ack", "ms": int((time.time() - t) * 1000), "status": r.status_code})

    t = time.time()
    r = requests.post(f"{URL}/api/odr/{odr['id']}/submit", json={}, headers=headers, timeout=15)
    obs["operations"].append({"op": "submit", "ms": int((time.time() - t) * 1000), "status": r.status_code})
    if r.status_code == 200:
        obs["submitted"] = True
        obs["submit_payload"] = {
            "status": r.json().get("status"),
            "amend_until": r.json().get("amend_allowed_until_utc"),
            "readiness_score": (r.json().get("readiness") or {}).get("score"),
        }

    # Render PDFs for all 5 audiences
    obs["pdf_renders"] = {}
    for aud in ("foreman", "superintendent", "pm", "executive", "external"):
        t = time.time()
        r = requests.get(
            f"{URL}/api/odr/{odr['id']}/pdf?audience={aud}",
            headers=headers, timeout=20,
        )
        obs["pdf_renders"][aud] = {
            "ms": int((time.time() - t) * 1000),
            "status": r.status_code,
            "byte_size": len(r.content) if r.status_code == 200 else 0,
            "sha256": r.headers.get("X-ODR-SHA256"),
            "footer": r.headers.get("X-ODR-Footer"),
        }

    # M0.35 — exercise audience_profile mapping
    t = time.time()
    r = requests.get(
        f"{URL}/api/odr/{odr['id']}/pdf?audience_profile=external_dot",
        headers=headers, timeout=15,
    )
    obs["audience_profile_external_dot"] = {
        "ms": int((time.time() - t) * 1000),
        "status": r.status_code,
        "x_audience_returned": r.headers.get("X-ODR-Audience"),
        "x_audience_profile_returned": r.headers.get("X-ODR-Audience-Profile"),
    }

    # Mint public link (audience-locked to external by doctrine)
    t = time.time()
    r = requests.post(
        f"{URL}/api/odr/{odr['id']}/link",
        json={"link_scope": "project_crew"},
        headers=headers, timeout=10,
    )
    obs["public_link"] = {
        "ms": int((time.time() - t) * 1000),
        "status": r.status_code,
        "audience_profile_locked": (r.json() or {}).get("audience_profile_locked") if r.status_code == 200 else None,
    }
    link_id = (r.json() or {}).get("link_id") if r.status_code == 200 else None
    doc_id = obs["doc_id"]

    # Public viewer resolve (no auth)
    if link_id:
        t = time.time()
        r = requests.get(
            f"{URL}/api/odr/public/{doc_id}?link_id={link_id}",
            timeout=10,
        )
        obs["public_resolve"] = {
            "ms": int((time.time() - t) * 1000),
            "status": r.status_code,
            "leaks_telemetry": "completion_telemetry" in (r.text or ""),
            "leaks_consumer_dispatch": "consumer_dispatch" in (r.text or ""),
            "leaks_readiness": '"readiness"' in (r.text or ""),
        }

    # Append a non-trivial amendment (scenario 4 specifically · admin·in-window)
    if dry_obs.get("amend_field_path"):
        t = time.time()
        r = requests.post(
            f"{URL}/api/odr/{odr['id']}/amend",
            json={
                "field_path": dry_obs["amend_field_path"],
                "new_value": dry_obs["amend_new_value"],
                "reason": {"text": dry_obs["amend_reason"]},
            },
            headers=headers, timeout=10,
        )
        obs["amendment"] = {
            "ms": int((time.time() - t) * 1000),
            "status": r.status_code,
            "amendment_recorded": (r.json() or {}).get("amendment_recorded") if r.status_code == 200 else False,
        }

    obs["total_ms"] = int((time.time() - t0) * 1000)
    obs["finished_at"] = utcnow()
    return obs


def main() -> int:
    token = login()
    h = H(token)
    suite_id = uuid.uuid4().hex[:8]
    out = {"started_at": utcnow(), "suite_id": suite_id, "scenarios": []}

    # Scenario 1 — Airport · Taxiway Closure
    s1 = scenario(
        "Airport · Taxiway Closure",
        payload_create={
            "project": {
                "project_id": f"airport-{suite_id}",
                "project_number": "FLL-2025-AIRSIDE",
                "project_name": "FLL Taxiway Echo Reconstruction",
                "report_date": "2026-05-29",
                "foreman_uid": "foreman-airfield@mascigc.com",
                "foreman_name": "M. Reyes",
            },
            "crew_profile": {
                "crew_id": "crew-airfield-1",
                "crew_name": "Airfield Crew Alpha",
                "crew_type": "airfield",
                "primary_operation": "Taxiway Echo paving · stations 12+50 to 18+00",
            },
        },
        patches=[
            ("manpower", {"manpower": {
                "rows": [
                    {"employee_uid": "e-001", "name": "M. Reyes", "role": "Foreman", "hours": 11.0, "overtime_hours": 3.0, "present": True},
                    {"employee_uid": "e-002", "name": "J. Velez", "role": "Operator (paver)", "hours": 11.0, "overtime_hours": 3.0, "present": True},
                    {"employee_uid": "e-003", "name": "T. Brown", "role": "Operator (roller)", "hours": 10.0, "overtime_hours": 2.0, "present": True},
                    {"employee_uid": "e-004", "name": "A. Singh", "role": "Ground", "hours": 10.0, "overtime_hours": 2.0, "present": True},
                ],
                "total_hours": 42.0, "total_overtime": 10.0,
            }}),
            ("equipment", {"equipment": {"rows": [
                {"equipment_id": "PAV-12", "asset_tag": "PAV-12", "description": "Vögele Super 1700 paver", "hours": 10.0, "idle_hours": 1.0, "down_hours": 0.0, "utilization_pct": 91.0},
                {"equipment_id": "RLR-7",  "asset_tag": "RLR-7",  "description": "Hamm HD120 roller",       "hours": 9.5, "idle_hours": 1.5, "down_hours": 0.0, "utilization_pct": 86.4},
            ]}}),
            ("production", {"production_segments": [
                {"segment_id": "seg-1", "crew_type": "airfield", "primary_operation": "SP-9.5 paving · taxiway echo",
                 "started_at_utc": "2026-05-29T03:00:00Z", "ended_at_utc": "2026-05-29T08:00:00Z",
                 "body": {"paving": {"notes": {"text": "Mat 320°F at regulator · 295°F at paver"}, "quantities": [{"tons": 412.5, "lift": 1, "station_from": "12+50", "station_to": "18+00"}]}}},
            ]}),
            ("delays", {"delays": {"any_delays": True, "total_hours_lost": 1.25, "entries": [
                {"delay_type": "faa", "hours_lost": 1.25, "description": {"text": "FAA escort released runway 09L 25 minutes late · ATC coordination"}, "photos": []}
            ]}}),
            ("constraints", {"constraints": {"entries": [
                {"constraint_type": "access", "description": {"text": "Escort window 0300–0800 only · runway 09L active 0800–0300"}}
            ]}}),
            ("safety", {"safety": {"any_event": False, "accident": False, "incident": False, "near_miss": False, "property_damage": False, "environmental_release": False, "injury": False, "events": []}}),
            ("weather_impact", {"weather_impact": {"weather_impacted_work": False, "description": {"text": ""}}}),
            ("tomorrow", {"tomorrow": {"planned_work": {"text": "Continue SP-9.5 lift 1 stations 18+00 to 22+50 · need 380 tons · escort confirmed 0300–0800"}, "required_resources": ["asphalt-380t", "escort-window"], "concerns": ["weather window narrow"]}}),
        ],
        headers=h,
        dry_obs={},
    )
    out["scenarios"].append(s1)

    # Scenario 2 — Drainage / Utility
    s2 = scenario(
        "Drainage · Utility Conflict",
        payload_create={
            "project": {
                "project_id": f"drainage-{suite_id}",
                "project_number": "FDOT-43-217",
                "project_name": "US-1 Stormwater Improvements",
                "report_date": "2026-05-29",
                "foreman_uid": "foreman-pipe@mascigc.com",
                "foreman_name": "C. Ortiz",
            },
            "crew_profile": {
                "crew_id": "crew-pipe-2",
                "crew_name": "Pipe Crew Bravo",
                "crew_type": "pipe",
                "primary_operation": "RCP install MH-12 → MH-14",
            },
        },
        patches=[
            ("manpower", {"manpower": {"rows": [
                {"employee_uid": "p-001", "name": "C. Ortiz", "role": "Foreman", "hours": 9.0, "overtime_hours": 1.0, "present": True},
                {"employee_uid": "p-002", "name": "R. Diaz",  "role": "Operator (excavator)", "hours": 9.0, "overtime_hours": 1.0, "present": True},
                {"employee_uid": "p-003", "name": "L. Park",  "role": "Pipe layer", "hours": 9.0, "overtime_hours": 1.0, "present": True},
            ], "total_hours": 27.0, "total_overtime": 3.0}}),
            ("equipment", {"equipment": {"rows": [
                {"equipment_id": "EX-22", "asset_tag": "EX-22", "description": "CAT 336 excavator", "hours": 8.5, "idle_hours": 0.5, "down_hours": 0.0, "utilization_pct": 94.4},
            ]}}),
            ("production", {"production_segments": [
                {"segment_id": "seg-1", "crew_type": "pipe", "primary_operation": "RCP install · MH-12 → MH-14",
                 "body": {"pipe": {"runs": [{"pipe_size_in": 36, "pipe_material": "RCP", "lf_installed": 87.0, "from_structure": "MH-12", "to_structure": "MH-14", "backfill_type": "select fill", "compaction_pct": 96.0}],
                                   "structures_set": [{"label": "MH-13 type J", "quantity": 1}],
                                   "total_lf": 87.0, "total_structures": 1}}},
            ]}),
            ("delays", {"delays": {"any_delays": True, "total_hours_lost": 2.0, "entries": [
                {"delay_type": "utility", "hours_lost": 2.0, "description": {"text": "Sunshine 811 marked locate inaccurate · ATT fiber found 8 ft south of called location · stopped work · waited for utility rep"}, "photos": []}
            ]}}),
            ("constraints", {"constraints": {"entries": [
                {"constraint_type": "utility", "description": {"text": "ATT fiber locate variance · field-flagged for design RFI"}}
            ]}}),
            ("safety", {"safety": {"any_event": True, "near_miss": True, "accident": False, "incident": False, "property_damage": False, "environmental_release": False, "injury": False,
                                   "events": [{"event_id": "ev-1", "event_kind": "near_miss", "notified_safety": True, "incident_report_complete": True, "contact_name": "Jorge Safety", "contact_time_utc": "2026-05-29T15:30:00Z", "photos": []}]}}),
            ("tomorrow", {"tomorrow": {"planned_work": {"text": "Continue MH-14 → MH-16 if locates clear · contingency: bedding prep at MH-12"}, "required_resources": ["RCP-36-120lf", "select-fill-50cy"], "concerns": ["follow-on locate accuracy"]}}),
        ],
        headers=h,
        dry_obs={},
    )
    out["scenarios"].append(s2)

    # Scenario 3 — Asphalt Operation
    s3 = scenario(
        "Asphalt · Plant Issue + MOT",
        payload_create={
            "project": {
                "project_id": f"asphalt-{suite_id}",
                "project_number": "FDOT-44-321",
                "project_name": "I-95 Resurfacing MP 312–314",
                "report_date": "2026-05-29",
                "foreman_uid": "foreman-paving@mascigc.com",
                "foreman_name": "D. Lee",
            },
            "crew_profile": {
                "crew_id": "crew-paving-1",
                "crew_name": "Paving Crew One",
                "crew_type": "paving",
                "primary_operation": "FC-9.5 surface course MP 312.5 to 313.7",
            },
        },
        patches=[
            ("manpower", {"manpower": {"rows": [
                {"employee_uid": "a-001", "name": "D. Lee", "role": "Foreman", "hours": 12.0, "overtime_hours": 4.0, "present": True},
                {"employee_uid": "a-002", "name": "K. Pratt", "role": "Screed", "hours": 12.0, "overtime_hours": 4.0, "present": True},
                {"employee_uid": "a-003", "name": "M. Cole", "role": "Roller", "hours": 11.0, "overtime_hours": 3.0, "present": True},
            ], "total_hours": 35.0, "total_overtime": 11.0}}),
            ("equipment", {"equipment": {"rows": [
                {"equipment_id": "PAV-8", "asset_tag": "PAV-8", "description": "Caterpillar AP1055F", "hours": 9.0, "idle_hours": 2.5, "down_hours": 0.5, "utilization_pct": 75.0,
                 "maintenance_issue": {"severity": "warn", "description": "Augers chattering · scheduled for night-shift inspection", "photos": [], "auto_shop_ticket_id": None}},
            ]}}),
            ("materials", {"materials": [
                {"material_event_id": "mat-1", "kind": "delivered", "material_code": "FC-9.5", "description": {"text": "Plant Mix FC-9.5 surface course"}, "quantity": 540.0, "uom": "ton", "vendor": "MASCI Plant 3", "ticket_numbers": ["TKT-994122", "TKT-994123", "TKT-994124"], "photos": []},
                {"material_event_id": "mat-2", "kind": "rejected", "material_code": "FC-9.5", "description": {"text": "Load 994118 · arrived at 280°F · below spec"}, "quantity": 22.0, "uom": "ton", "vendor": "MASCI Plant 3", "ticket_numbers": ["TKT-994118"], "photos": [], "issue": "reject"},
            ]}),
            ("production", {"production_segments": [
                {"segment_id": "seg-1", "crew_type": "paving", "primary_operation": "FC-9.5 surface placement",
                 "body": {"paving": {"notes": {"text": "1.5 mat thickness · density acceptance pulled at sta 312+85, 313+25, 313+60"}, "quantities": [{"tons": 518.0, "lift_no": 1}]}}},
            ]}),
            ("delays", {"delays": {"any_delays": True, "total_hours_lost": 1.5, "entries": [
                {"delay_type": "material", "hours_lost": 1.0, "description": {"text": "Plant 3 burner trip at 11:42 · 45-minute restart"}, "photos": []},
                {"delay_type": "mot", "hours_lost": 0.5, "description": {"text": "Channelizer hit at sta 313+10 · replaced · no injuries"}, "photos": []},
            ]}}),
            ("safety", {"safety": {"any_event": False, "accident": False, "incident": False, "near_miss": False, "property_damage": False, "environmental_release": False, "injury": False, "events": []}}),
            ("tomorrow", {"tomorrow": {"planned_work": {"text": "FC-9.5 MP 313.7 to 314.5 · 480 tons · density cores at 313+85, 314+15"}, "required_resources": ["FC-9.5-480t"], "concerns": ["plant 3 burner reliability"]}}),
        ],
        headers=h,
        dry_obs={},
    )
    out["scenarios"].append(s3)

    # Scenario 4 — Concrete / Structures · with amendment
    s4 = scenario(
        "Concrete · Structures + Amendment",
        payload_create={
            "project": {
                "project_id": f"concrete-{suite_id}",
                "project_number": "CNTY-22-077",
                "project_name": "Bridge 22-077 Deck Replacement",
                "report_date": "2026-05-29",
                "foreman_uid": "foreman-concrete@mascigc.com",
                "foreman_name": "S. Patel",
            },
            "crew_profile": {
                "crew_id": "crew-concrete-1",
                "crew_name": "Structures Crew Alpha",
                "crew_type": "concrete",
                "primary_operation": "Class IV pour · deck panel 2",
            },
        },
        patches=[
            ("manpower", {"manpower": {"rows": [
                {"employee_uid": "c-001", "name": "S. Patel", "role": "Foreman", "hours": 11.0, "overtime_hours": 3.0, "present": True},
                {"employee_uid": "c-002", "name": "R. Soto", "role": "Finisher", "hours": 11.0, "overtime_hours": 3.0, "present": True},
                {"employee_uid": "c-003", "name": "T. Hayes", "role": "Pump operator", "hours": 11.0, "overtime_hours": 3.0, "present": True},
            ], "total_hours": 33.0, "total_overtime": 9.0}}),
            ("equipment", {"equipment": {"rows": [
                {"equipment_id": "PMP-3", "asset_tag": "PMP-3", "description": "Schwing concrete pump 36m", "hours": 8.0, "idle_hours": 1.0, "down_hours": 0.0, "utilization_pct": 88.9},
            ]}}),
            ("materials", {"materials": [
                {"material_event_id": "mc-1", "kind": "delivered", "material_code": "Class IV", "description": {"text": "Class IV concrete · 4500 PSI · 6% air"}, "quantity": 92.0, "uom": "cy", "vendor": "Coastal RM", "ticket_numbers": ["CR-77001","CR-77002","CR-77003","CR-77004"], "photos": []},
            ]}),
            ("production", {"production_segments": [
                {"segment_id": "seg-1", "crew_type": "concrete", "primary_operation": "Deck panel 2 pour",
                 "body": {"concrete": {"notes": {"text": "Slump 6-7\" · air 5.8% · cylinders cast at trucks 1, 4, 7 (7-day, 28-day, 56-day)"}, "quantities": [{"cy": 92.0, "panel": 2}]}}},
            ]}),
            ("weather_impact", {"weather_impact": {"weather_impacted_work": True, "hours_lost": 0.5, "description": {"text": "Brief afternoon shower · placed wet curing covers · resumed in 25 minutes"}}}),
            ("safety", {"safety": {"any_event": False, "accident": False, "incident": False, "near_miss": False, "property_damage": False, "environmental_release": False, "injury": False, "events": []}}),
            ("tomorrow", {"tomorrow": {"planned_work": {"text": "Deck panel 3 form prep · panel 2 cylinders to lab"}, "required_resources": ["form-lumber-60sf"], "concerns": ["cylinder transport timing"]}}),
            ("delays", {"delays": {"any_delays": False, "total_hours_lost": 0.0, "entries": []}}),
        ],
        headers=h,
        dry_obs={
            "amend_field_path": "production_segments[0].body.concrete.notes",
            "amend_new_value": {"text": "Slump 6-7\" · air 5.8% · cylinders cast at trucks 1, 4, 7 (7-day, 28-day, 56-day) · CORRECTION: cylinder set 28-day was actually pulled from truck 5 not truck 4 per QC log review."},
            "amend_reason": "QC log review · cylinder source truck mis-recorded at submit time",
        },
    )
    out["scenarios"].append(s4)

    # Aggregate metrics
    total_ms = sum(s.get("total_ms", 0) for s in out["scenarios"])
    out["aggregate"] = {
        "scenarios_run": len(out["scenarios"]),
        "submitted_count": sum(1 for s in out["scenarios"] if s.get("submitted")),
        "total_run_ms": total_ms,
        "avg_scenario_ms": total_ms // max(1, len(out["scenarios"])),
    }
    out["finished_at"] = utcnow()

    # Write
    out_path = REPO_ROOT / "memory" / "M0_35_REALITY_VALIDATION_RAW.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"WROTE: {out_path}")
    print(f"Scenarios: {out['aggregate']['scenarios_run']} · "
          f"submitted: {out['aggregate']['submitted_count']} · "
          f"total: {out['aggregate']['total_run_ms']}ms · "
          f"avg: {out['aggregate']['avg_scenario_ms']}ms")
    for s in out["scenarios"]:
        ok = "✅" if s.get("submitted") else "❌"
        print(f"  {ok} {s['name']} · {s.get('total_ms', 0)}ms · "
              f"{s.get('doc_id', 'no-doc-id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
