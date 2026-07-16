"""
Iteration 572 - Daily Report Summary Timeout Hardening Verification

Tests:
1. task_router.py: operational_narrative uses default_text_model() (not hardcoded)
2. daily_summary.py: draft endpoint has 80s timeout guard with deterministic fallback
3. backend/.env: AI_PROVIDER_TIMEOUT_MS=30000, AI_PROVIDER_MAX_RETRIES=1
4. Preserved fixes: vision.py senior superintendent persona, api.js X-Device-Id header
"""
import os
import pytest
import requests
import inspect
import ast

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestTaskRouterConfiguration:
    """Verify task_router.py uses default_text_model() for operational_narrative"""

    def test_task_router_imports_default_text_model(self):
        """Verify task_router.py imports default_text_model from env"""
        task_router_path = "/app/backend/services/ai_gateway/task_router.py"
        with open(task_router_path, "r") as f:
            content = f.read()
        
        # Check import statement
        assert "from .env import default_text_model" in content, \
            "task_router.py must import default_text_model from .env"
        print("PASS: task_router.py imports default_text_model from .env")

    def test_operational_narrative_uses_default_text_model_function(self):
        """Verify operational_narrative route calls default_text_model() not hardcoded string"""
        task_router_path = "/app/backend/services/ai_gateway/task_router.py"
        with open(task_router_path, "r") as f:
            content = f.read()
        
        # Simple string-based verification that operational_narrative uses default_text_model()
        # The line should look like: "operational_narrative":  ("anthropic", default_text_model()),
        
        # Check that operational_narrative is present
        assert '"operational_narrative"' in content, \
            "operational_narrative key not found in TASK_ROUTES"
        
        # Check that it uses default_text_model() function call (not a hardcoded string)
        # The pattern should be: "operational_narrative": ... default_text_model()
        import re
        pattern = r'"operational_narrative":\s*\([^)]*default_text_model\(\)'
        match = re.search(pattern, content)
        
        assert match is not None, \
            "operational_narrative must use default_text_model() function call, not hardcoded string"
        
        # Also verify it's NOT using a hardcoded string like "claude-sonnet-4-6"
        # by checking the line doesn't have a quoted string as the second tuple element
        hardcoded_pattern = r'"operational_narrative":\s*\(\s*"[^"]+"\s*,\s*"[^"]+"\s*\)'
        hardcoded_match = re.search(hardcoded_pattern, content)
        
        assert hardcoded_match is None, \
            "operational_narrative should NOT use hardcoded model string"
        
        print("PASS: operational_narrative uses default_text_model() function call")


class TestDailySummaryTimeoutGuard:
    """Verify daily_summary.py has 80s timeout guard with deterministic fallback"""

    def test_draft_summary_has_asyncio_wait_for_timeout(self):
        """Verify draft_summary uses asyncio.wait_for with 80.0 timeout"""
        daily_summary_path = "/app/backend/routes/daily_summary.py"
        with open(daily_summary_path, "r") as f:
            content = f.read()
        
        # Check for asyncio.wait_for with timeout=80.0
        assert "asyncio.wait_for(" in content, \
            "daily_summary.py must use asyncio.wait_for()"
        assert "timeout=80.0" in content, \
            "daily_summary.py must have timeout=80.0 in asyncio.wait_for()"
        print("PASS: draft_summary uses asyncio.wait_for with timeout=80.0")

    def test_timeout_fallback_function_exists(self):
        """Verify _compose_timeout_fallback function exists"""
        daily_summary_path = "/app/backend/routes/daily_summary.py"
        with open(daily_summary_path, "r") as f:
            content = f.read()
        
        assert "def _compose_timeout_fallback(" in content, \
            "daily_summary.py must have _compose_timeout_fallback function"
        print("PASS: _compose_timeout_fallback function exists")

    def test_timeout_error_handling_returns_fallback(self):
        """Verify asyncio.TimeoutError is caught and returns fallback"""
        daily_summary_path = "/app/backend/routes/daily_summary.py"
        with open(daily_summary_path, "r") as f:
            content = f.read()
        
        assert "except asyncio.TimeoutError:" in content, \
            "daily_summary.py must catch asyncio.TimeoutError"
        assert "_compose_timeout_fallback(" in content, \
            "daily_summary.py must call _compose_timeout_fallback on timeout"
        assert 'reason="summary_timeout_80s"' in content, \
            "Timeout fallback must use reason='summary_timeout_80s'"
        print("PASS: TimeoutError is caught and returns deterministic fallback with correct reason")


class TestBackendEnvConfiguration:
    """Verify backend .env has correct AI provider timeout and retry settings"""

    def test_ai_provider_timeout_ms_is_30000(self):
        """Verify AI_PROVIDER_TIMEOUT_MS=30000 in .env"""
        env_path = "/app/backend/.env"
        with open(env_path, "r") as f:
            content = f.read()
        
        assert "AI_PROVIDER_TIMEOUT_MS=30000" in content, \
            "backend/.env must have AI_PROVIDER_TIMEOUT_MS=30000"
        print("PASS: AI_PROVIDER_TIMEOUT_MS=30000 is set in .env")

    def test_ai_provider_max_retries_is_1(self):
        """Verify AI_PROVIDER_MAX_RETRIES=1 in .env"""
        env_path = "/app/backend/.env"
        with open(env_path, "r") as f:
            content = f.read()
        
        assert "AI_PROVIDER_MAX_RETRIES=1" in content, \
            "backend/.env must have AI_PROVIDER_MAX_RETRIES=1"
        print("PASS: AI_PROVIDER_MAX_RETRIES=1 is set in .env")

    def test_env_helper_returns_correct_timeout(self):
        """Verify env.py provider_timeout_ms() returns 30000"""
        import sys
        sys.path.insert(0, "/app/backend")
        
        # Set the env var to ensure it's read
        os.environ["AI_PROVIDER_TIMEOUT_MS"] = "30000"
        
        from services.ai_gateway.env import provider_timeout_ms
        timeout = provider_timeout_ms()
        
        assert timeout == 30000, f"provider_timeout_ms() should return 30000, got {timeout}"
        print(f"PASS: provider_timeout_ms() returns {timeout}")

    def test_env_helper_returns_correct_max_retries(self):
        """Verify env.py provider_max_retries() returns 1"""
        import sys
        sys.path.insert(0, "/app/backend")
        
        # Set the env var to ensure it's read
        os.environ["AI_PROVIDER_MAX_RETRIES"] = "1"
        
        from services.ai_gateway.env import provider_max_retries
        retries = provider_max_retries()
        
        assert retries == 1, f"provider_max_retries() should return 1, got {retries}"
        print(f"PASS: provider_max_retries() returns {retries}")


class TestPreservedFixes:
    """Verify preserved fixes remain in code"""

    def test_vision_senior_superintendent_persona(self):
        """Verify vision.py has senior superintendent persona in system prompt"""
        vision_path = "/app/backend/services/dr_ai/vision.py"
        with open(vision_path, "r") as f:
            content = f.read()
        
        assert "senior construction superintendent" in content.lower(), \
            "vision.py must have senior superintendent persona"
        assert "forensic jobsite photo analyst" in content.lower(), \
            "vision.py must have forensic jobsite photo analyst persona"
        print("PASS: vision.py has senior superintendent persona preserved")

    def test_vision_async_gather_loop(self):
        """Verify vision.py has async gather loop for parallel per-photo vision"""
        vision_path = "/app/backend/services/dr_ai/vision.py"
        with open(vision_path, "r") as f:
            content = f.read()
        
        assert "asyncio.gather(" in content, \
            "vision.py must use asyncio.gather for parallel processing"
        assert "asyncio.Semaphore(" in content, \
            "vision.py must use Semaphore for concurrency control"
        print("PASS: vision.py has async gather loop with semaphore preserved")

    def test_frontend_x_device_id_header(self):
        """Verify frontend api.js injects X-Device-Id header"""
        api_path = "/app/frontend/src/lib/api.js"
        with open(api_path, "r") as f:
            content = f.read()
        
        assert "X-Device-Id" in content, \
            "api.js must inject X-Device-Id header"
        assert "getDeviceId" in content, \
            "api.js must use getDeviceId function"
        print("PASS: frontend api.js has X-Device-Id header injection preserved")


class TestDraftSummaryEndpointLive:
    """Live endpoint tests for draft summary"""

    def test_draft_summary_endpoint_responds(self):
        """Verify POST /api/daily-reports/summary/draft returns 200"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        url = f"{BASE_URL}/api/daily-reports/summary/draft"
        payload = {
            "payload": {
                "project_name": "Test Project",
                "project_number": "TEST-001",
                "report_date": "2026-01-15",
                "prepared_by": "Test Supervisor",
                "masci_crews": [
                    {"name": "John Doe", "trade": "Laborer", "hours": 8}
                ],
                "production": [
                    {"description": "Concrete pour", "quantity": 50, "unit": "CY"}
                ]
            },
            "language": "en"
        }
        
        response = requests.post(url, json=payload, timeout=90)
        
        assert response.status_code == 200, \
            f"Draft summary endpoint should return 200, got {response.status_code}"
        
        data = response.json()
        assert "ok" in data, "Response must have 'ok' field"
        assert data["ok"] is True, "Response 'ok' must be True"
        assert "summary_text" in data, "Response must have 'summary_text' field"
        assert "mode" in data, "Response must have 'mode' field"
        
        print(f"PASS: Draft summary endpoint responds with mode={data.get('mode')}")
        print(f"  - enabled: {data.get('enabled')}")
        print(f"  - reason_disabled: {data.get('reason_disabled')}")

    def test_draft_summary_returns_deterministic_fallback_structure(self):
        """Verify draft summary returns proper fallback structure"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        url = f"{BASE_URL}/api/daily-reports/summary/draft"
        payload = {
            "payload": {
                "project_name": "Fallback Test Project",
                "project_number": "FALLBACK-001",
                "report_date": "2026-01-15"
            },
            "language": "en"
        }
        
        response = requests.post(url, json=payload, timeout=90)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches expected fallback format
        required_fields = ["ok", "enabled", "reason_disabled", "mode", "summary_text", 
                          "language", "warnings", "evidence_refs", "sentence_count"]
        
        for field in required_fields:
            assert field in data, f"Response must have '{field}' field"
        
        # Mode should be either 'live_ai' or 'deterministic_fallback'
        assert data["mode"] in ["live_ai", "deterministic_fallback"], \
            f"Mode must be 'live_ai' or 'deterministic_fallback', got {data['mode']}"
        
        print(f"PASS: Draft summary returns proper structure with mode={data['mode']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
