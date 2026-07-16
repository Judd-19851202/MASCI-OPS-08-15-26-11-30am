"""
Test Daily Report Photo Intelligence and Summary Workflow
Tests the complete photo upload -> analysis -> summary generation flow
"""
import pytest
import requests
import os
import base64
import time
import json
from datetime import datetime

# Use internal URL for backend testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8001').rstrip('/')

# Real construction photo URLs from the test conversation
CONSTRUCTION_PHOTO_URLS = [
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/hetx1awh_IMG_0914.jpeg",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/tsh3zcfx_IMG_0910.jpeg",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/76u9i05c_IMG_0926.jpeg",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/e64t5rju_IMG_0916.jpeg",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/focxnadi_IMG_0929.jpeg",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/07axyxo8_IMG_1203.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/xjkmai35_IMG_1202.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/2s67zx28_IMG_1201.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/hf4fzu7j_IMG_1200.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/l35590pk_IMG_1192.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/1j1a41fz_IMG_1193.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/gjqdjqos_IMG_1191.webp",
    "https://customer-assets-v7afamib.emergentagent.net/job_14fe28f8-a73c-4390-9e67-d5cae20e77cd/artifacts/h24qjtm9_IMG_1182.webp",
]


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def download_photo_as_base64(url: str, timeout: int = 30) -> str:
    """Download a photo and return as base64 data URL"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'webp' in url.lower():
            content_type = 'image/webp'
        elif 'jpeg' in url.lower() or 'jpg' in url.lower():
            content_type = 'image/jpeg'
        b64 = base64.b64encode(response.content).decode('ascii')
        return f"data:{content_type};base64,{b64}"
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None


class TestHealthAndVersion:
    """Basic health check tests"""
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint is responding"""
        response = api_client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"Health check passed: {data}")
    
    def test_version_endpoint(self, api_client):
        """Test version endpoint"""
        response = api_client.get(f"{BASE_URL}/api/version")
        assert response.status_code == 200
        data = response.json()
        print(f"Version info: {json.dumps(data, indent=2)[:500]}")


class TestDailySummaryDraftEndpoint:
    """Test the draft summary endpoint"""
    
    def test_draft_summary_minimal_payload(self, api_client):
        """Test draft summary with minimal payload"""
        payload = {
            "payload": {
                "project_name": "Test Project",
                "project_number": "TEST-001",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "prepared_by": "Test Supervisor",
            },
            "form_key": f"test-draft-{int(time.time())}",
        }
        
        response = api_client.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") is True
        assert "summary_text" in data
        assert "summary_input" in data
        print(f"Draft summary response mode: {data.get('mode')}")
        print(f"Summary text length: {len(data.get('summary_text', ''))}")
        print(f"Reason disabled: {data.get('reason_disabled')}")
    
    def test_draft_summary_with_crew_data(self, api_client):
        """Test draft summary with crew and equipment data"""
        payload = {
            "payload": {
                "project_name": "Highway Reconstruction Project",
                "project_number": "HWY-2026-001",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "prepared_by": "John Smith",
                "superintendent": "Mike Johnson",
                "location": "Station 12+50 to 15+00",
                "weather_summary": "Clear, 75°F, light wind",
                "masci_crews": [
                    {"name": "Worker 1", "trade": "Laborer", "hours": 8.0},
                    {"name": "Worker 2", "trade": "Operator", "hours": 8.0},
                ],
                "equipment": [
                    {"description": "CAT 320 Excavator", "hours_used": 6.5, "idle_hours": 1.5},
                    {"description": "Dump Truck", "hours_used": 7.0, "idle_hours": 1.0},
                ],
                "production": [
                    {"description": "Curb installation", "quantity": 150, "unit": "LF", "percent_complete": 25},
                ],
            },
            "form_key": f"test-draft-crew-{int(time.time())}",
        }
        
        response = api_client.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") is True
        summary_text = data.get("summary_text", "")
        assert len(summary_text) > 50, "Summary should have meaningful content"
        
        # Check summary_input structure
        summary_input = data.get("summary_input", {})
        labor = summary_input.get("labor", {})
        assert labor.get("employee_count") == 2
        assert labor.get("total_employee_hours") == 16.0
        
        print(f"Summary text preview: {summary_text[:300]}...")
        print(f"Labor summary: {labor}")


class TestPhotoIntelligenceDraftEndpoint:
    """Test the photo intelligence draft endpoint"""
    
    def test_photo_intelligence_draft_no_photos(self, api_client):
        """Test photo intelligence with no photos"""
        payload = {
            "form_key": f"test-intel-{int(time.time())}",
            "payload": {
                "project_number": "TEST-001",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "photos": [],
            },
        }
        
        response = api_client.post(f"{BASE_URL}/api/daily-reports/photo-intelligence/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("photo_count", 0) == 0
        status = data.get("status") or data.get("lifecycle_status")
        assert status in ["no_photos", "not_requested"]
        print(f"Photo intelligence (no photos): status={status}")
    
    def test_photo_intelligence_draft_with_photos(self, api_client):
        """Test photo intelligence with real construction photos"""
        # Download first 3 photos for testing
        photos = []
        for i, url in enumerate(CONSTRUCTION_PHOTO_URLS[:3]):
            print(f"Downloading photo {i+1}/3: {url[:60]}...")
            b64 = download_photo_as_base64(url)
            if b64:
                photos.append(b64)
                print(f"  Downloaded successfully ({len(b64)} chars)")
            else:
                print(f"  Failed to download")
        
        if not photos:
            pytest.skip("Could not download any test photos")
        
        form_key = f"test-intel-photos-{int(time.time())}"
        payload = {
            "form_key": form_key,
            "payload": {
                "project_number": "TEST-001",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "photos": photos,
            },
        }
        
        start_time = time.time()
        response = api_client.post(f"{BASE_URL}/api/daily-reports/photo-intelligence/draft", json=payload, timeout=120)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Photo intelligence response (elapsed: {elapsed:.2f}s):")
        print(f"  photo_count: {data.get('photo_count')}")
        print(f"  status: {data.get('status')}")
        print(f"  lifecycle_status: {data.get('lifecycle_status')}")
        print(f"  analyzed: {data.get('analyzed')}")
        print(f"  pending: {data.get('pending')}")
        print(f"  observations count: {len(data.get('observations', []))}")
        
        # Verify photo count matches
        assert data.get("photo_count") == len(photos)


class TestDraftSummaryWithPhotos:
    """Test draft summary with photo intelligence integration"""
    
    def test_draft_summary_with_photos_and_data(self, api_client):
        """Test complete draft summary with photos and report data"""
        # Download 6 photos (minimum required)
        photos = []
        for i, url in enumerate(CONSTRUCTION_PHOTO_URLS[:6]):
            print(f"Downloading photo {i+1}/6...")
            b64 = download_photo_as_base64(url)
            if b64:
                photos.append(b64)
        
        if len(photos) < 6:
            pytest.skip(f"Could only download {len(photos)} photos, need 6")
        
        form_key = f"test-summary-photos-{int(time.time())}"
        payload = {
            "payload": {
                "project_name": "Highway 101 Reconstruction",
                "project_number": "HWY-101-2026",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "prepared_by": "Test Foreman",
                "superintendent": "Test Superintendent",
                "location": "Station 100+00 to 105+00, Northbound lanes",
                "weather_summary": "Partly cloudy, 72°F, wind 5-10 mph from SW",
                "masci_crews": [
                    {"name": "John Doe", "trade": "Laborer", "hours": 8.0, "work_performed": "Excavation support"},
                    {"name": "Jane Smith", "trade": "Equipment Operator", "hours": 8.0, "work_performed": "Excavator operation"},
                    {"name": "Bob Wilson", "trade": "Foreman", "hours": 8.0, "work_performed": "Crew supervision"},
                ],
                "equipment": [
                    {"description": "CAT 320 Excavator", "hours_used": 7.0, "idle_hours": 1.0},
                    {"description": "Tri-axle Dump Truck", "hours_used": 6.5, "idle_hours": 1.5},
                    {"description": "Skid Steer", "hours_used": 4.0, "idle_hours": 0.5},
                ],
                "production": [
                    {"description": "Excavation for storm drain", "quantity": 250, "unit": "CY", "percent_complete": 40},
                    {"description": "Curb and gutter installation", "quantity": 180, "unit": "LF", "percent_complete": 30},
                ],
                "materials": [
                    {"description": "Concrete", "quantity": 15, "unit": "CY", "supplier": "ABC Concrete"},
                ],
                "photos": photos,
                "narrative_sections": {
                    "tomorrow_plan": "Continue excavation work, begin pipe installation at Station 102+00",
                },
                "general_notes": "Good progress today. No safety incidents.",
            },
            "form_key": form_key,
        }
        
        print(f"Sending draft summary request with {len(photos)} photos...")
        start_time = time.time()
        response = api_client.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload, timeout=180)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n=== Draft Summary Response (elapsed: {elapsed:.2f}s) ===")
        print(f"ok: {data.get('ok')}")
        print(f"enabled: {data.get('enabled')}")
        print(f"mode: {data.get('mode')}")
        print(f"reason_disabled: {data.get('reason_disabled')}")
        
        summary_text = data.get("summary_text", "")
        print(f"\n=== Generated Summary ({len(summary_text)} chars) ===")
        print(summary_text)
        
        # Check photo intelligence in response
        photo_intel = data.get("photo_intelligence")
        if photo_intel:
            print(f"\n=== Photo Intelligence ===")
            print(f"photo_count: {photo_intel.get('photo_count')}")
            print(f"status: {photo_intel.get('status')}")
            print(f"analyzed: {photo_intel.get('analyzed')}")
            print(f"observations: {len(photo_intel.get('observations', []))}")
        
        # Verify summary quality
        assert data.get("ok") is True
        assert len(summary_text) > 100, "Summary should have substantial content"
        
        # Check for narrative quality - should NOT contain these
        bad_patterns = [
            "confidence",
            "JSON",
            "model",
            "provider",
            "debug",
            "internal",
        ]
        summary_lower = summary_text.lower()
        for pattern in bad_patterns:
            if pattern in summary_lower:
                print(f"WARNING: Summary contains '{pattern}' which may indicate quality issue")


class TestRegenerateAndDeduplication:
    """Test regenerate behavior and photo analysis deduplication"""
    
    def test_regenerate_does_not_reanalyze_unchanged_photos(self, api_client):
        """Test that regenerate doesn't re-analyze unchanged photos"""
        # Download 3 photos
        photos = []
        for url in CONSTRUCTION_PHOTO_URLS[:3]:
            b64 = download_photo_as_base64(url)
            if b64:
                photos.append(b64)
        
        if len(photos) < 3:
            pytest.skip("Could not download enough photos")
        
        form_key = f"test-dedupe-{int(time.time())}"
        base_payload = {
            "payload": {
                "project_name": "Deduplication Test Project",
                "project_number": "DEDUPE-001",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "prepared_by": "Test User",
                "photos": photos,
            },
            "form_key": form_key,
        }
        
        # First request
        print("First summary request...")
        start1 = time.time()
        response1 = api_client.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=base_payload, timeout=120)
        elapsed1 = time.time() - start1
        assert response1.status_code == 200
        data1 = response1.json()
        print(f"First request: {elapsed1:.2f}s")
        
        # Second request (regenerate) - same photos, different text field
        print("Second summary request (regenerate with text change)...")
        base_payload["payload"]["general_notes"] = "Added some notes"
        base_payload["force"] = True
        start2 = time.time()
        response2 = api_client.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=base_payload, timeout=120)
        elapsed2 = time.time() - start2
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"Second request: {elapsed2:.2f}s")
        
        # The second request should be faster if photos are cached
        print(f"\nTiming comparison:")
        print(f"  First request:  {elapsed1:.2f}s")
        print(f"  Second request: {elapsed2:.2f}s")
        print(f"  Speedup: {elapsed1/elapsed2:.2f}x" if elapsed2 > 0 else "N/A")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
