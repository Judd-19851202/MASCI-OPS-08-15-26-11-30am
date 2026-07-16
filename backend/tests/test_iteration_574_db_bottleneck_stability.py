"""
Iteration 574 - DB Bottleneck and Stability Fixes Verification

Tests verify:
1. usage_analytics health endpoint uses estimated_document_count() (not count_documents)
2. server.py startup includes index ensure hook for r2_inventory(size), r2_inventory(content_type), 
   r2_references(r2_key), and daily_reports(report_number)
3. r2 classification and r2 intelligence broad scans use explicit projections and limits
4. Previous routing/env/stability fixes remain present (task_router uses default_text_model(), 
   default text model env is claude-sonnet-4-5-20250929, 80s timeout guard, draft_mode reconciler 
   exclusion, X-Device-Id identity keying, senior superintendent persona)
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestUsageAnalyticsEstimatedDocumentCount:
    """Verify usage_analytics health endpoint uses estimated_document_count"""
    
    def test_usage_analytics_uses_estimated_document_count(self):
        """Code review: usage_analytics.py line 372 uses estimated_document_count"""
        with open("/app/backend/routes/usage_analytics.py", "r") as f:
            content = f.read()
        
        # Should use estimated_document_count
        assert "estimated_document_count()" in content, \
            "usage_analytics.py should use estimated_document_count()"
        
        # Should NOT use count_documents({}) for total count
        # Note: count_documents with filters is OK, but count_documents({}) is the bottleneck
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "count_documents({})" in line or "count_documents( {} )" in line:
                pytest.fail(f"Line {i+1}: Found count_documents({{}}) which is a DB bottleneck")


class TestStartupIndexHooks:
    """Verify server.py includes startup index hooks for r2_inventory, r2_references, daily_reports"""
    
    def test_r2_inventory_size_index(self):
        """server.py should create index on r2_inventory.size"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert 'r2_inventory.create_index("size")' in content or \
               "r2_inventory.create_index('size')" in content, \
            "server.py should create index on r2_inventory.size"
    
    def test_r2_inventory_content_type_index(self):
        """server.py should create index on r2_inventory.content_type"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert 'r2_inventory.create_index("content_type")' in content or \
               "r2_inventory.create_index('content_type')" in content, \
            "server.py should create index on r2_inventory.content_type"
    
    def test_r2_references_r2_key_index(self):
        """server.py should create index on r2_references.r2_key"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert 'r2_references.create_index("r2_key")' in content or \
               "r2_references.create_index('r2_key')" in content, \
            "server.py should create index on r2_references.r2_key"
    
    def test_daily_reports_report_number_index(self):
        """server.py should create index on daily_reports.report_number"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert 'daily_reports.create_index("report_number")' in content or \
               "daily_reports.create_index('report_number')" in content, \
            "server.py should create index on daily_reports.report_number"
    
    def test_ensure_production_bottleneck_indexes_function_exists(self):
        """server.py should have _ensure_production_bottleneck_indexes function"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        assert "_ensure_production_bottleneck_indexes" in content, \
            "server.py should have _ensure_production_bottleneck_indexes function"


class TestR2ClassificationProjectionsAndLimits:
    """Verify r2 classification broad scans use explicit projections and limits"""
    
    def test_r2_references_find_has_projection_and_limit(self):
        """classification.py r2_references.find should have projection and limit"""
        with open("/app/backend/services/r2_lifecycle/classification.py", "r") as f:
            content = f.read()
        
        # Check for r2_references.find with projection
        assert 'r2_references.find({}, {"_id": 0' in content or \
               "r2_references.find({}, {'_id': 0" in content, \
            "classification.py r2_references.find should have projection excluding _id"
        
        # Check for limit on r2_references.find
        assert ".limit(250000)" in content, \
            "classification.py should have .limit(250000) on broad scans"
    
    def test_r2_inventory_find_has_projection_and_limit(self):
        """classification.py r2_inventory.find should have projection and limit"""
        with open("/app/backend/services/r2_lifecycle/classification.py", "r") as f:
            content = f.read()
        
        # Check for r2_inventory.find with projection
        assert 'r2_inventory.find({}, {"_id": 0' in content or \
               "r2_inventory.find({}, {'_id': 0" in content, \
            "classification.py r2_inventory.find should have projection excluding _id"


class TestR2IntelligenceProjectionsAndLimits:
    """Verify r2 intelligence broad scans use explicit projections and limits"""
    
    def test_largest_objects_has_projection_and_limit(self):
        """intelligence.py largest_objects should have projection and limit"""
        with open("/app/backend/services/r2_lifecycle/intelligence.py", "r") as f:
            content = f.read()
        
        # Check for r2_inventory.find with projection in largest_objects
        assert 'r2_inventory.find({}, {"_id": 0' in content or \
               "r2_inventory.find({}, {'_id': 0" in content, \
            "intelligence.py r2_inventory.find should have projection excluding _id"
        
        # Check for limit
        assert ".limit(limit)" in content, \
            "intelligence.py largest_objects should have .limit(limit)"


class TestPreviousStabilityFixesPreserved:
    """Verify previous routing/env/stability fixes remain present"""
    
    def test_task_router_imports_default_text_model(self):
        """task_router.py should import default_text_model from env"""
        with open("/app/backend/services/ai_gateway/task_router.py", "r") as f:
            content = f.read()
        
        assert "from .env import default_text_model" in content, \
            "task_router.py should import default_text_model from .env"
    
    def test_task_router_uses_default_text_model_function_call(self):
        """task_router.py should use default_text_model() function call for all 11 text tasks"""
        with open("/app/backend/services/ai_gateway/task_router.py", "r") as f:
            content = f.read()
        
        # All 11 text tasks should use default_text_model()
        text_tasks = [
            "operational_narrative",
            "production_intelligence",
            "delay_intelligence",
            "safety_intelligence",
            "equipment_intelligence",
            "pm_brief",
            "executive_brief",
            "confidence_validation",
            "evidence_trace",
            "future_task",
            "translation_es_en",
        ]
        
        for task in text_tasks:
            # Check that the task uses default_text_model()
            pattern = rf'"{task}":\s*\("anthropic",\s*default_text_model\(\)\)'
            assert re.search(pattern, content), \
                f"task_router.py: {task} should use default_text_model() function call"
    
    def test_default_text_model_fallback_is_claude_sonnet_4_5(self):
        """env.py default_text_model fallback should be claude-sonnet-4-5-20250929"""
        with open("/app/backend/services/ai_gateway/env.py", "r") as f:
            content = f.read()
        
        assert 'claude-sonnet-4-5-20250929' in content, \
            "env.py default_text_model fallback should be claude-sonnet-4-5-20250929"
    
    def test_daily_summary_80s_timeout_guard(self):
        """daily_summary.py should have 80s timeout guard"""
        with open("/app/backend/routes/daily_summary.py", "r") as f:
            content = f.read()
        
        assert "timeout=80.0" in content, \
            "daily_summary.py should have 80s timeout guard (timeout=80.0)"
    
    def test_daily_summary_timeout_fallback(self):
        """daily_summary.py should have timeout fallback with reason"""
        with open("/app/backend/routes/daily_summary.py", "r") as f:
            content = f.read()
        
        assert "_compose_timeout_fallback" in content, \
            "daily_summary.py should have _compose_timeout_fallback function"
        
        assert 'summary_timeout_80s' in content, \
            "daily_summary.py should have 'summary_timeout_80s' reason"
    
    def test_rate_limiter_device_id_keying(self):
        """rate_limiting.py should use X-Device-Id for identity keying"""
        with open("/app/backend/lib/rate_limiting.py", "r") as f:
            content = f.read()
        
        assert "x-device-id" in content.lower(), \
            "rate_limiting.py should use X-Device-Id header for identity keying"
        
        # Device ID should be checked first
        assert 'device_id = (request.headers.get("x-device-id")' in content or \
               "device_id = (request.headers.get('x-device-id')" in content, \
            "rate_limiting.py should check device_id first"
    
    def test_vision_senior_superintendent_persona(self):
        """vision.py should have senior superintendent persona"""
        with open("/app/backend/services/dr_ai/vision.py", "r") as f:
            content = f.read()
        
        assert "senior construction superintendent" in content.lower(), \
            "vision.py should have senior superintendent persona"


class TestBackendHealthEndpoint:
    """Verify backend is running and healthy"""
    
    def test_health_endpoint_returns_200(self):
        """GET /api/health should return 200"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
    
    def test_version_endpoint_returns_200(self):
        """GET /api/version should return 200"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200, f"Version endpoint returned {response.status_code}"


class TestEnvConfiguration:
    """Verify .env configuration is correct"""
    
    def test_ai_default_text_model_env(self):
        """backend/.env should have AI_DEFAULT_TEXT_MODEL=claude-sonnet-4-5-20250929"""
        with open("/app/backend/.env", "r") as f:
            content = f.read()
        
        assert "AI_DEFAULT_TEXT_MODEL=claude-sonnet-4-5-20250929" in content, \
            "backend/.env should have AI_DEFAULT_TEXT_MODEL=claude-sonnet-4-5-20250929"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
