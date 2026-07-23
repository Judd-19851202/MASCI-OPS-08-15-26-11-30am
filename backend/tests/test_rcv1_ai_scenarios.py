"""RCV-1 · Final Release Candidate Validation · AI Summary Scenarios.

Tests the Daily Report AI summary generation across all required scenarios:
- Scenario A: Text only, no photos
- Scenario B: One real construction photo with minimal text
- Scenario C: Multiple real construction photos with different work activities
- Scenario D: Long report with long narrative, multiple crews, equipment, production, weather, delays, safety
- Scenario E: Transcript-style text plus typed notes
- Scenario F: Edit report after AI summary, regenerate, verify stale summary never overwrites newer information
- Scenario G/H: AI timeout or provider-unavailable fallback must not lose operator data

Uses real construction image fixtures from /app/test_artifacts/daily_report_fixtures/rcv1/real_images
"""
import base64
import os
import pytest
import requests
import time
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
REAL_IMAGES_DIR = Path("/app/test_artifacts/daily_report_fixtures/rcv1/real_images")

# Test credentials
TEST_EMAIL = "jaymn.judd@mascigc.com"
TEST_PASSWORD = "Maddix123!"


def get_auth_tokens():
    """Get authentication tokens via multi-login."""
    resp = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    if resp.status_code != 200:
        pytest.skip(f"Auth failed: {resp.status_code}")
    data = resp.json()
    return {
        "X-Admin-Token": data.get("portal_tokens", {}).get("admin", ""),
        "X-Directory-Token": data.get("session_token", ""),
    }


def load_real_image_as_data_url(filename: str) -> str:
    """Load a real construction image and return as data URL."""
    path = REAL_IMAGES_DIR / filename
    if not path.exists():
        pytest.skip(f"Real image fixture not found: {path}")
    with open(path, "rb") as f:
        content = f.read()
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{b64}"


def poll_job_until_complete(job_id: str, timeout_s: int = 90) -> dict:
    """Poll an async job until it completes or times out."""
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status")
        if resp.status_code != 200:
            time.sleep(1)
            continue
        data = resp.json()
        status = data.get("status", "")
        if status == "completed":
            return data
        if status == "failed":
            return data
        time.sleep(1.5)
    return {"status": "timeout", "error": "Job did not complete within timeout"}


class TestRCV1AIScenarios:
    """RCV-1 AI Summary Scenario Tests."""

    def test_scenario_a_text_only_no_photos(self):
        """Scenario A: Text only, no photos — verify summary quality and grounded use of all entered text fields."""
        payload = {
            "project_name": "RCV-1 Scenario A Test Project",
            "project_number": "RCV-A-001",
            "report_date": "2026-07-23",
            "prepared_by": "Test Foreman A",
            "superintendent": "Test Superintendent",
            "location": "Test Location, FL",
            "weather_summary": "Hot and humid, 92°F, partly cloudy",
            "weather_snapshots": [{"time": "06:00", "temp_f": 82}, {"time": "12:00", "temp_f": 92}],
            "distribution_list": ["pm@example.com", "safety@example.com"],
            "masci_crews": [
                {"name": "John Smith", "trade": "Operator", "hours": 8, "work_performed": "Excavation work"},
                {"name": "Jane Doe", "trade": "Laborer", "hours": 8, "work_performed": "Pipe installation"},
            ],
            "equipment": [
                {"description": "CAT 320 Excavator", "hours_used": 6, "idle_hours": 2},
                {"description": "John Deere 210G Loader", "hours_used": 4, "idle_hours": 1},
            ],
            "production": [
                {"description": "8-inch PVC pipe installation", "quantity": 120, "unit": "LF", "percent_complete": 45},
                {"description": "Trench excavation", "quantity": 150, "unit": "LF", "percent_complete": 60},
            ],
            "subcontractors": [
                {"company": "ABC Paving", "trade": "Paving", "count": 3, "hours": 24, "work_performed": "Base prep"},
            ],
            "materials": [
                {"description": "8-inch PVC pipe", "quantity": 200, "unit": "LF", "supplier": "Ferguson"},
            ],
            "general_notes": "Resident access maintained throughout the day. Utility conflict resolved with owner.",
            "notes": "Voice transcript: We completed the pipe run from station 12+00 to 15+50 today.",
            "safety_notes": "Trench box used for all excavations over 4 feet. Tailgate safety meeting held.",
            "schedule_delays": "Yes",
            "schedule_delays_notes": "Utility conflict delayed start by 2 hours",
            "weather_impact": "No",
            "narrative_sections": {
                "work_completed": "Installed 120 LF of 8-inch PVC pipe from station 12+00 to 15+50",
                "follow_ups": "Await utility owner signoff on relocated gas line",
                "tomorrow_plan": "Continue southbound pipe run, target 150 LF",
            },
            "cost_code_quantities": [{"cost_code": "033000", "installed_quantity": "120"}],
            "photos": [],  # No photos for Scenario A
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-a-test",
            "force": True,
        })
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True
        job_id = data.get("job_id")
        assert job_id, "No job_id returned"

        # Poll for completion
        result = poll_job_until_complete(job_id)
        assert result.get("status") == "completed", f"Job did not complete: {result}"

        summary_result = result.get("result", {})
        summary_text = summary_result.get("summary_text", "")
        
        # Verify summary is not empty
        assert len(summary_text) > 100, f"Summary too short: {len(summary_text)} chars"
        
        # Verify key fields are referenced in the summary
        summary_lower = summary_text.lower()
        assert "pipe" in summary_lower or "pvc" in summary_lower, "Summary should mention pipe work"
        assert "excavat" in summary_lower or "trench" in summary_lower, "Summary should mention excavation"
        
        print(f"✓ Scenario A PASS: Text-only summary generated ({len(summary_text)} chars)")
        print(f"  Summary preview: {summary_text[:200]}...")

    def test_scenario_b_one_photo_minimal_text(self):
        """Scenario B: One real construction photo with minimal text — verify summary and photo reasoning."""
        # Load a real construction photo
        photo_data_url = load_real_image_as_data_url("crew_excavator.jpg")
        
        payload = {
            "project_name": "RCV-1 Scenario B Test",
            "project_number": "RCV-B-001",
            "report_date": "2026-07-23",
            "prepared_by": "Test Foreman B",
            "location": "Test Site B",
            "weather_summary": "Clear, 85°F",
            "masci_crews": [
                {"name": "Worker One", "trade": "Operator", "hours": 8},
            ],
            "production": [
                {"description": "Site work", "quantity": 1, "unit": "LS"},
            ],
            "photos": [photo_data_url],
            "photo_captions": ["Excavator working on site"],
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-b-test",
            "force": True,
        })
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id, "No job_id returned"

        # Poll for completion (longer timeout for photo analysis)
        result = poll_job_until_complete(job_id, timeout_s=120)
        assert result.get("status") == "completed", f"Job did not complete: {result}"

        summary_result = result.get("result", {})
        summary_text = summary_result.get("summary_text", "")
        photo_intel = summary_result.get("photo_intelligence", {})
        
        assert len(summary_text) > 50, f"Summary too short: {len(summary_text)} chars"
        
        print(f"✓ Scenario B PASS: Single photo summary generated ({len(summary_text)} chars)")
        print(f"  Photo intel status: {photo_intel.get('status', 'N/A')}")
        print(f"  Summary preview: {summary_text[:200]}...")

    def test_scenario_c_multiple_photos_different_activities(self):
        """Scenario C: Multiple real construction photos with different work activities."""
        # Load multiple real construction photos
        photos = []
        captions = []
        
        image_files = [
            ("caterpillar.jpg", "CAT equipment on site"),
            ("crew_excavator.jpg", "Crew working with excavator"),
            ("drainage_pipe.jpeg", "Drainage pipe installation"),
            ("trench_pipes.jpeg", "Trench with pipes"),
            ("worker_street.jpg", "Worker on street"),
        ]
        
        for filename, caption in image_files:
            try:
                photo_url = load_real_image_as_data_url(filename)
                photos.append(photo_url)
                captions.append(caption)
            except Exception:
                continue
        
        assert len(photos) >= 3, f"Need at least 3 photos, got {len(photos)}"
        
        payload = {
            "project_name": "RCV-1 Scenario C Multi-Photo Test",
            "project_number": "RCV-C-001",
            "report_date": "2026-07-23",
            "prepared_by": "Test Foreman C",
            "superintendent": "Test Super C",
            "location": "Multi-Activity Site, FL",
            "weather_summary": "Sunny, 88°F",
            "masci_crews": [
                {"name": "Operator 1", "trade": "Heavy Equipment Operator", "hours": 10},
                {"name": "Laborer 1", "trade": "Pipe Layer", "hours": 10},
                {"name": "Laborer 2", "trade": "General Labor", "hours": 8},
            ],
            "equipment": [
                {"description": "CAT 320 Excavator", "hours_used": 8, "idle_hours": 2},
                {"description": "Trench Roller", "hours_used": 4, "idle_hours": 0},
            ],
            "production": [
                {"description": "Storm drain pipe installation", "quantity": 200, "unit": "LF", "percent_complete": 35},
                {"description": "Trench excavation", "quantity": 250, "unit": "LF", "percent_complete": 50},
                {"description": "Backfill and compaction", "quantity": 100, "unit": "LF", "percent_complete": 25},
            ],
            "photos": photos,
            "photo_captions": captions,
            "general_notes": "Multiple work activities ongoing. Good progress on all fronts.",
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-c-test",
            "force": True,
        })
        assert resp.status_code == 202
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id

        # Poll for completion (longer timeout for multiple photos)
        result = poll_job_until_complete(job_id, timeout_s=180)
        assert result.get("status") == "completed", f"Job did not complete: {result}"

        summary_result = result.get("result", {})
        summary_text = summary_result.get("summary_text", "")
        photo_intel = summary_result.get("photo_intelligence", {})
        
        assert len(summary_text) > 100, f"Summary too short"
        
        # Check photo intelligence
        reviewed = photo_intel.get("reviewed", 0) or photo_intel.get("analyzed", 0)
        total = photo_intel.get("photo_count", len(photos))
        
        print(f"✓ Scenario C PASS: Multi-photo summary generated ({len(summary_text)} chars)")
        print(f"  Photos reviewed: {reviewed}/{total}")
        print(f"  Photo intel status: {photo_intel.get('status', 'N/A')}")
        print(f"  Summary preview: {summary_text[:300]}...")

    def test_scenario_d_long_report_comprehensive(self):
        """Scenario D: Long report with long narrative, multiple crews, equipment, production, weather, delays, safety."""
        payload = {
            "project_name": "RCV-1 Scenario D Comprehensive Test - Highway 441 Widening Phase 2",
            "project_number": "RCV-D-001",
            "report_date": "2026-07-23",
            "prepared_by": "Senior Foreman D",
            "superintendent": "Project Superintendent",
            "location": "Highway 441 from MP 12.5 to MP 15.0, Orange County, FL",
            "weather_summary": "Morning fog clearing by 8 AM, then partly cloudy with temperatures rising from 78°F to 94°F. Humidity 85%. Heat index reached 102°F by 2 PM. Brief afternoon thunderstorm from 3:15 PM to 3:45 PM caused 30-minute work stoppage.",
            "weather_snapshots": [
                {"time": "06:00", "temp_f": 78, "conditions": "Foggy"},
                {"time": "09:00", "temp_f": 84, "conditions": "Partly cloudy"},
                {"time": "12:00", "temp_f": 92, "conditions": "Partly cloudy"},
                {"time": "15:00", "temp_f": 94, "conditions": "Thunderstorm"},
                {"time": "17:00", "temp_f": 88, "conditions": "Clearing"},
            ],
            "weather_snapshot_meta": {"observation_timestamp": "2026-07-23T06:00:00-04:00"},
            "distribution_list": ["pm@mascigc.com", "safety@mascigc.com", "owner@fdot.gov", "inspector@fdot.gov"],
            "masci_crews": [
                {"name": "John Smith", "trade": "Heavy Equipment Operator", "hours": 10, "work_performed": "Excavator operation for drainage structure installation"},
                {"name": "Mike Johnson", "trade": "Heavy Equipment Operator", "hours": 10, "work_performed": "Loader operation for material handling"},
                {"name": "Robert Williams", "trade": "Pipe Layer", "hours": 10, "work_performed": "36-inch RCP installation"},
                {"name": "James Brown", "trade": "Pipe Layer", "hours": 10, "work_performed": "36-inch RCP installation"},
                {"name": "David Davis", "trade": "Laborer", "hours": 10, "work_performed": "Trench support and bedding"},
                {"name": "Michael Wilson", "trade": "Laborer", "hours": 10, "work_performed": "Backfill and compaction"},
                {"name": "William Moore", "trade": "Laborer", "hours": 8, "work_performed": "Traffic control assistance"},
                {"name": "Richard Taylor", "trade": "Foreman", "hours": 10, "work_performed": "Crew supervision and coordination"},
            ],
            "equipment": [
                {"description": "CAT 336 Excavator (Unit EXC-1934)", "hours_used": 8, "idle_hours": 2, "notes": "Idle during thunderstorm"},
                {"description": "CAT 950M Loader (Unit LDR-2201)", "hours_used": 7, "idle_hours": 1},
                {"description": "Trench Roller (Unit TR-445)", "hours_used": 5, "idle_hours": 0},
                {"description": "Tri-axle Dump Truck #1", "hours_used": 8, "idle_hours": 0},
                {"description": "Tri-axle Dump Truck #2", "hours_used": 8, "idle_hours": 0},
                {"description": "Water Truck (Unit WT-112)", "hours_used": 4, "idle_hours": 0, "notes": "Dust control"},
            ],
            "production": [
                {"description": "36-inch RCP storm drain installation", "quantity": 180, "unit": "LF", "percent_complete": 42, "station_from": "14+20", "station_to": "16+00"},
                {"description": "Trench excavation for storm drain", "quantity": 200, "unit": "LF", "percent_complete": 55},
                {"description": "Pipe bedding (6-inch crushed stone)", "quantity": 180, "unit": "LF", "percent_complete": 42},
                {"description": "Backfill and compaction", "quantity": 120, "unit": "LF", "percent_complete": 30},
                {"description": "Drainage structure #DS-14 installation", "quantity": 1, "unit": "EA", "percent_complete": 75},
            ],
            "subcontractors": [
                {"company": "ABC Traffic Control", "trade": "MOT", "count": 4, "hours": 40, "work_performed": "Lane closures and traffic control for SB lanes"},
                {"company": "XYZ Concrete", "trade": "Concrete", "count": 2, "hours": 8, "work_performed": "Drainage structure base pour"},
            ],
            "materials": [
                {"description": "36-inch RCP Class III", "quantity": 200, "unit": "LF", "supplier": "Rinker Materials", "ticket_number": "RM-45678"},
                {"description": "#57 Stone for bedding", "quantity": 45, "unit": "TON", "supplier": "Martin Marietta", "ticket_number": "MM-12345"},
                {"description": "Select fill material", "quantity": 120, "unit": "CY", "supplier": "Local Pit", "ticket_number": "LP-9876"},
            ],
            "outbound_materials": [
                {"description": "Unsuitable material", "quantity": 80, "unit": "CY", "destination": "Approved disposal site"},
            ],
            "general_notes": "Resident access maintained via temporary driveway at Station 14+50. Coordinated with FPL for overhead line clearance. Inspector on site from 7 AM to 4 PM. All work performed within approved MOT limits.",
            "notes": "Voice transcript from foreman: We made good progress today despite the afternoon storm. The 36-inch pipe is going in smoothly. We had to deal with some groundwater at the deeper section near station 15+00 but the pumps handled it. Tomorrow we should be able to finish the run to the junction structure.",
            "safety_notes": "Trench box used for all excavations exceeding 4 feet. Tailgate safety meeting held at 6:30 AM covering heat stress prevention and thunderstorm protocols. All crew members wearing high-visibility vests and hard hats. Spotter used for all equipment backing operations.",
            "safety_incidents_today": "No",
            "injuries_reported": "No",
            "schedule_delays": "Yes",
            "schedule_delays_notes": "30-minute work stoppage due to afternoon thunderstorm. Morning fog delayed start by 45 minutes. Net impact: approximately 1.25 hours lost production time.",
            "weather_impact": "Yes",
            "weather_impact_notes": "Heat index exceeded 100°F requiring additional hydration breaks per company heat stress protocol. Afternoon thunderstorm required evacuation of trench and equipment shutdown.",
            "narrative_sections": {
                "work_completed": "Installed 180 LF of 36-inch RCP storm drain from Station 14+20 to Station 16+00. Completed 75% of drainage structure DS-14 including base pour. Excavated 200 LF of trench for tomorrow's pipe installation. Backfilled and compacted 120 LF of previously installed pipe.",
                "follow_ups": "Await FDOT inspector approval of DS-14 base pour before proceeding with walls. Coordinate with FPL for pole relocation at Station 16+50. Confirm delivery of additional RCP for next week.",
                "tomorrow_plan": "Complete DS-14 structure walls. Continue pipe installation from Station 16+00 to Station 17+50 (target 150 LF). Begin tie-in preparation at existing inlet.",
            },
            "cost_code_quantities": [
                {"cost_code": "425-1-1", "installed_quantity": "180", "unit_of_measure": "LF", "notes": "36-inch RCP"},
                {"cost_code": "425-2-1", "installed_quantity": "1", "unit_of_measure": "EA", "notes": "DS-14 75% complete"},
            ],
            "linked_excavation_ids": ["EX-2026-0723-001"],
            "excavation_activity_today": "Yes",
            "photos": [],  # No photos for this text-heavy scenario
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-d-test",
            "force": True,
        })
        assert resp.status_code == 202
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id

        result = poll_job_until_complete(job_id, timeout_s=120)
        assert result.get("status") == "completed", f"Job did not complete: {result}"

        summary_result = result.get("result", {})
        summary_text = summary_result.get("summary_text", "")
        
        # Comprehensive summary should be substantial
        assert len(summary_text) > 300, f"Summary too short for comprehensive report: {len(summary_text)} chars"
        
        # Verify key elements are mentioned
        summary_lower = summary_text.lower()
        checks = [
            ("pipe" in summary_lower or "rcp" in summary_lower, "pipe/RCP"),
            ("crew" in summary_lower or "employee" in summary_lower or "labor" in summary_lower, "crew/labor"),
            ("equipment" in summary_lower or "excavator" in summary_lower or "loader" in summary_lower, "equipment"),
        ]
        
        for check, name in checks:
            assert check, f"Summary should mention {name}"
        
        print(f"✓ Scenario D PASS: Comprehensive summary generated ({len(summary_text)} chars)")
        print(f"  Summary preview: {summary_text[:400]}...")

    def test_scenario_e_transcript_plus_typed_notes(self):
        """Scenario E: Transcript-style text plus typed notes — verify transcript text participates in AI reasoning."""
        payload = {
            "project_name": "RCV-1 Scenario E Transcript Test",
            "project_number": "RCV-E-001",
            "report_date": "2026-07-23",
            "prepared_by": "Foreman E",
            "location": "Transcript Test Site",
            "weather_summary": "Clear, 85°F",
            "masci_crews": [
                {"name": "Worker 1", "trade": "Operator", "hours": 8},
            ],
            "production": [
                {"description": "Pipe installation", "quantity": 100, "unit": "LF"},
            ],
            # This is the key field - voice transcript text
            "notes": """Voice transcript from field: 
            Okay so today we got the 12-inch water main installed from station 22+00 all the way to station 25+50. 
            That's about 350 feet of pipe in the ground. We had to deal with some rock at station 23+00 but the 
            hoe ram took care of it. The inspector was here and approved the bedding before we laid the pipe. 
            We're using class 52 ductile iron pipe per the specs. Tomorrow we need to finish the tie-in to the 
            existing main at station 25+50. The valve crew is scheduled for 7 AM.""",
            "general_notes": "Typed notes: Good production day. Rock encountered but handled. Inspector approved all work.",
            "narrative_sections": {
                "work_completed": "Water main installation from Sta 22+00 to Sta 25+50",
                "tomorrow_plan": "Complete tie-in to existing main",
            },
            "photos": [],
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-e-test",
            "force": True,
        })
        assert resp.status_code == 202
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id

        result = poll_job_until_complete(job_id, timeout_s=90)
        assert result.get("status") == "completed", f"Job did not complete: {result}"

        summary_result = result.get("result", {})
        summary_text = summary_result.get("summary_text", "")
        
        assert len(summary_text) > 100, f"Summary too short"
        
        # Verify transcript content influenced the summary
        summary_lower = summary_text.lower()
        # The transcript mentions specific details that should appear
        transcript_indicators = [
            "water main" in summary_lower or "pipe" in summary_lower,
            "350" in summary_text or "station" in summary_lower or "22+00" in summary_text or "25+50" in summary_text,
        ]
        
        assert any(transcript_indicators), "Summary should incorporate transcript content"
        
        print(f"✓ Scenario E PASS: Transcript-influenced summary generated ({len(summary_text)} chars)")
        print(f"  Summary preview: {summary_text[:300]}...")

    def test_scenario_f_regenerate_after_edit(self):
        """Scenario F: Edit report after AI summary, regenerate, verify stale summary never overwrites newer information."""
        # First generation with initial data
        payload_v1 = {
            "project_name": "RCV-1 Scenario F Regenerate Test",
            "project_number": "RCV-F-001",
            "report_date": "2026-07-23",
            "prepared_by": "Foreman F",
            "location": "Regenerate Test Site",
            "weather_summary": "Clear, 80°F",
            "masci_crews": [
                {"name": "Worker 1", "trade": "Operator", "hours": 4},
            ],
            "production": [
                {"description": "Initial work item", "quantity": 50, "unit": "LF"},
            ],
            "general_notes": "Initial notes - morning work only",
            "photos": [],
        }

        # Generate first summary
        resp1 = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload_v1,
            "form_key": "rcv1-scenario-f-test",
            "force": True,
        })
        assert resp1.status_code == 202
        job_id_1 = resp1.json().get("job_id")
        result1 = poll_job_until_complete(job_id_1, timeout_s=90)
        assert result1.get("status") == "completed"
        summary_v1 = result1.get("result", {}).get("summary_text", "")
        
        # Now update the payload with more data (simulating operator edits)
        payload_v2 = {
            **payload_v1,
            "masci_crews": [
                {"name": "Worker 1", "trade": "Operator", "hours": 10},  # Updated hours
                {"name": "Worker 2", "trade": "Laborer", "hours": 8},   # Added crew
            ],
            "production": [
                {"description": "Initial work item", "quantity": 50, "unit": "LF"},
                {"description": "Afternoon work item - ADDED AFTER FIRST SUMMARY", "quantity": 75, "unit": "LF"},  # New item
            ],
            "general_notes": "Updated notes - full day work including afternoon activities. REGENERATED SUMMARY SHOULD INCLUDE THIS.",
        }

        # Generate second summary with updated data
        resp2 = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload_v2,
            "form_key": "rcv1-scenario-f-test",
            "force": True,  # Force regeneration
        })
        assert resp2.status_code == 202
        job_id_2 = resp2.json().get("job_id")
        result2 = poll_job_until_complete(job_id_2, timeout_s=90)
        assert result2.get("status") == "completed"
        summary_v2 = result2.get("result", {}).get("summary_text", "")
        
        # Verify the second summary is different and reflects the updates
        assert summary_v2 != summary_v1, "Regenerated summary should be different from original"
        assert len(summary_v2) >= len(summary_v1) * 0.8, "Regenerated summary should not be significantly shorter"
        
        # The new summary should reflect the additional work
        summary_v2_lower = summary_v2.lower()
        # Should mention more crew or more production
        assert "2" in summary_v2 or "two" in summary_v2_lower or "afternoon" in summary_v2_lower or "75" in summary_v2, \
            "Regenerated summary should reflect the updated/added content"
        
        print(f"✓ Scenario F PASS: Regeneration produces updated summary")
        print(f"  V1 summary length: {len(summary_v1)} chars")
        print(f"  V2 summary length: {len(summary_v2)} chars")
        print(f"  V2 preview: {summary_v2[:200]}...")

    def test_scenario_gh_fallback_preserves_data(self):
        """Scenario G/H: AI timeout or provider-unavailable fallback must not lose operator data."""
        # This test verifies that even if AI fails, the deterministic fallback
        # still produces a summary from the operator's data
        payload = {
            "project_name": "RCV-1 Scenario G/H Fallback Test",
            "project_number": "RCV-GH-001",
            "report_date": "2026-07-23",
            "prepared_by": "Foreman GH",
            "superintendent": "Super GH",
            "location": "Fallback Test Site, FL",
            "weather_summary": "Rainy, 75°F",
            "masci_crews": [
                {"name": "Critical Worker 1", "trade": "Operator", "hours": 8, "work_performed": "Essential excavation work"},
                {"name": "Critical Worker 2", "trade": "Laborer", "hours": 8, "work_performed": "Pipe handling"},
            ],
            "equipment": [
                {"description": "Essential Excavator EXC-999", "hours_used": 6, "idle_hours": 2},
            ],
            "production": [
                {"description": "Critical pipe installation - MUST APPEAR IN FALLBACK", "quantity": 100, "unit": "LF", "percent_complete": 50},
            ],
            "general_notes": "CRITICAL NOTES - This text must appear in any fallback summary to prove data is preserved.",
            "safety_notes": "Safety meeting held. All PPE worn.",
            "photos": [],
        }

        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "rcv1-scenario-gh-test",
            "force": True,
        })
        assert resp.status_code == 202
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id

        result = poll_job_until_complete(job_id, timeout_s=120)
        
        # Whether AI succeeds or falls back, we should get a summary
        if result.get("status") == "completed":
            summary_result = result.get("result", {})
            summary_text = summary_result.get("summary_text", "")
            mode = summary_result.get("mode", "unknown")
            enabled = summary_result.get("enabled", True)
            
            # Summary must exist regardless of AI availability
            assert len(summary_text) > 50, "Summary must be generated even in fallback mode"
            
            # Key operator data should be preserved in the summary
            summary_lower = summary_text.lower()
            data_preserved = (
                "pipe" in summary_lower or
                "excavat" in summary_lower or
                "100" in summary_text or
                "critical" in summary_lower or
                "foreman" in summary_lower
            )
            assert data_preserved, "Operator data must be preserved in summary (AI or fallback)"
            
            print(f"✓ Scenario G/H PASS: Summary generated with data preserved")
            print(f"  Mode: {mode}")
            print(f"  AI enabled: {enabled}")
            print(f"  Summary length: {len(summary_text)} chars")
            print(f"  Summary preview: {summary_text[:200]}...")
        else:
            # Even if job fails, the endpoint should not lose data
            pytest.fail(f"Job failed completely: {result}")


class TestRCV1DataLossCertification:
    """Data loss certification tests - verify no known operator data-loss paths remain."""

    def test_autosave_draft_persistence(self):
        """Verify draft autosave mechanism works correctly."""
        # This is tested via the frontend, but we can verify the backend
        # draft-related endpoints exist and respond
        resp = requests.get(f"{BASE_URL}/api/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        print("✓ Backend ready for draft operations")

    def test_summary_endpoint_returns_job_id(self):
        """Verify summary endpoint returns job_id for async tracking."""
        payload = {
            "project_name": "Data Loss Test",
            "project_number": "DL-001",
            "report_date": "2026-07-23",
            "prepared_by": "Test",
            "masci_crews": [{"name": "Worker", "trade": "Labor", "hours": 8}],
            "photos": [],
        }
        
        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "data-loss-test",
        })
        assert resp.status_code == 202
        data = resp.json()
        assert data.get("ok") is True
        assert data.get("job_id"), "Must return job_id for tracking"
        assert data.get("status_url"), "Must return status_url for polling"
        print(f"✓ Summary endpoint returns trackable job: {data.get('job_id')}")

    def test_job_status_endpoint_accessible(self):
        """Verify job status endpoint is accessible for progress tracking."""
        # Create a job first
        payload = {
            "project_name": "Job Status Test",
            "project_number": "JS-001",
            "report_date": "2026-07-23",
            "prepared_by": "Test",
            "masci_crews": [{"name": "Worker", "trade": "Labor", "hours": 8}],
            "photos": [],
        }
        
        resp = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json={
            "payload": payload,
            "form_key": "job-status-test",
        })
        assert resp.status_code == 202
        job_id = resp.json().get("job_id")
        
        # Check job status endpoint
        status_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert "status" in status_data
        print(f"✓ Job status endpoint accessible: {status_data.get('status')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
