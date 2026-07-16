"""
Iteration 573 - Platform Integrity Fix Verification Tests

Tests for mascidocs.com platform integrity patch:
1. task_router uses default_text_model() for all 11 text task routes
2. default_text_model() fallback is claude-sonnet-4-5-20250929
3. daily_summary has 80-second timeout guard with deterministic fallback
4. photo_intelligence reconciler excludes draft_mode jobs
5. No hardcoded gpt-5.4/gpt-5.2 in live code paths
6. Rate limiter uses device-id/auth-token hash, not raw IP primary
7. PhotoEdgeCacheMiddleware catches call_next failures and returns generic 500
8. Preview .env has required parity flags and CORS origins
9. Senior superintendent persona and parallel per-photo loop preserved
"""

import pytest
import os
import sys
import re
import ast
import asyncio

# Add backend to path
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestTaskRouterDefaultTextModel:
    """Test 1: All 11 text task routes use default_text_model()"""
    
    def test_task_router_imports_default_text_model(self):
        """Verify task_router imports default_text_model from env"""
        with open('/app/backend/services/ai_gateway/task_router.py', 'r') as f:
            content = f.read()
        
        assert 'from .env import default_text_model' in content, \
            "task_router.py must import default_text_model from .env"
        print("PASS: task_router imports default_text_model from env")
    
    def test_task_routes_use_function_call(self):
        """Verify TASK_ROUTES uses default_text_model() function calls, not literals"""
        with open('/app/backend/services/ai_gateway/task_router.py', 'r') as f:
            content = f.read()
        
        # Find the TASK_ROUTES dict
        match = re.search(r'TASK_ROUTES.*?=\s*\{([^}]+)\}', content, re.DOTALL)
        assert match, "Could not find TASK_ROUTES dict"
        
        routes_content = match.group(1)
        
        # Count text task routes that should use default_text_model()
        text_tasks = [
            'operational_narrative', 'production_intelligence', 'delay_intelligence',
            'safety_intelligence', 'equipment_intelligence', 'pm_brief', 'executive_brief',
            'confidence_validation', 'evidence_trace', 'future_task', 'translation_es_en'
        ]
        
        for task in text_tasks:
            # Check that the task uses default_text_model() not a literal string
            pattern = rf'"{task}".*?default_text_model\(\)'
            assert re.search(pattern, routes_content), \
                f"Task '{task}' should use default_text_model() function call"
        
        # Verify no literal claude-sonnet-4-6 in TASK_ROUTES
        assert 'claude-sonnet-4-6' not in routes_content, \
            "TASK_ROUTES should not contain literal claude-sonnet-4-6"
        
        print(f"PASS: All {len(text_tasks)} text task routes use default_text_model()")
    
    def test_no_literal_claude_sonnet_4_6_in_task_router(self):
        """Verify no hardcoded claude-sonnet-4-6 in task_router.py"""
        with open('/app/backend/services/ai_gateway/task_router.py', 'r') as f:
            content = f.read()
        
        assert 'claude-sonnet-4-6' not in content, \
            "task_router.py should not contain literal claude-sonnet-4-6"
        print("PASS: No literal claude-sonnet-4-6 in task_router.py")


class TestEnvDefaultTextModel:
    """Test 2: default_text_model() fallback is claude-sonnet-4-5-20250929"""
    
    def test_default_text_model_fallback(self):
        """Verify default_text_model() returns claude-sonnet-4-5-20250929 as fallback"""
        with open('/app/backend/services/ai_gateway/env.py', 'r') as f:
            content = f.read()
        
        # Check the function definition
        pattern = r'def default_text_model\(\).*?return.*?"claude-sonnet-4-5-20250929"'
        assert re.search(pattern, content, re.DOTALL), \
            "default_text_model() should have claude-sonnet-4-5-20250929 as fallback"
        print("PASS: default_text_model() fallback is claude-sonnet-4-5-20250929")
    
    def test_env_helper_returns_correct_value(self):
        """Test the actual function returns expected value"""
        from services.ai_gateway.env import default_text_model
        
        # Clear env var to test fallback
        original = os.environ.get('AI_DEFAULT_TEXT_MODEL')
        try:
            os.environ.pop('AI_DEFAULT_TEXT_MODEL', None)
            result = default_text_model()
            assert result == 'claude-sonnet-4-5-20250929', \
                f"Expected claude-sonnet-4-5-20250929, got {result}"
            print(f"PASS: default_text_model() returns {result}")
        finally:
            if original:
                os.environ['AI_DEFAULT_TEXT_MODEL'] = original


class TestDailySummaryTimeoutGuard:
    """Test 3: daily_summary has 80-second timeout guard with deterministic fallback"""
    
    def test_timeout_guard_present(self):
        """Verify asyncio.wait_for with 80.0 timeout is present"""
        with open('/app/backend/routes/daily_summary.py', 'r') as f:
            content = f.read()
        
        # Check for asyncio.wait_for with timeout=80.0
        assert 'asyncio.wait_for' in content, \
            "daily_summary.py should use asyncio.wait_for"
        assert 'timeout=80.0' in content, \
            "daily_summary.py should have timeout=80.0"
        print("PASS: 80-second timeout guard present in daily_summary.py")
    
    def test_timeout_fallback_function_exists(self):
        """Verify _compose_timeout_fallback function exists"""
        with open('/app/backend/routes/daily_summary.py', 'r') as f:
            content = f.read()
        
        assert 'def _compose_timeout_fallback' in content, \
            "daily_summary.py should have _compose_timeout_fallback function"
        print("PASS: _compose_timeout_fallback function exists")
    
    def test_timeout_error_handling(self):
        """Verify TimeoutError is caught and returns fallback"""
        with open('/app/backend/routes/daily_summary.py', 'r') as f:
            content = f.read()
        
        # Check for TimeoutError handling
        assert 'asyncio.TimeoutError' in content or 'TimeoutError' in content, \
            "daily_summary.py should handle TimeoutError"
        assert 'summary_timeout_80s' in content, \
            "daily_summary.py should return reason='summary_timeout_80s' on timeout"
        print("PASS: TimeoutError handling with deterministic fallback present")


class TestPhotoIntelligenceReconciler:
    """Test 4: photo_intelligence reconciler excludes draft_mode jobs"""
    
    def test_reconciler_excludes_draft_mode(self):
        """Verify reconciler query excludes draft_mode jobs"""
        with open('/app/backend/services/photo_intelligence/pipeline.py', 'r') as f:
            content = f.read()
        
        # Check for draft_mode exclusion in reconciler query
        assert '"draft_mode": {"$ne": True}' in content or "'draft_mode': {'$ne': True}" in content, \
            "Reconciler should exclude draft_mode jobs with $ne: True"
        print("PASS: Reconciler excludes draft_mode jobs")


class TestNoHardcodedGptModels:
    """Test 5: No hardcoded gpt-5.4/gpt-5.2 in live code paths"""
    
    def test_no_gpt_5_4_in_photo_intelligence(self):
        """Verify no gpt-5.4 in photo_intelligence pipeline"""
        with open('/app/backend/services/photo_intelligence/pipeline.py', 'r') as f:
            content = f.read()
        
        assert 'gpt-5.4' not in content, \
            "photo_intelligence/pipeline.py should not contain gpt-5.4"
        assert 'gpt-5.2' not in content, \
            "photo_intelligence/pipeline.py should not contain gpt-5.2"
        print("PASS: No hardcoded gpt-5.4/gpt-5.2 in photo_intelligence pipeline")
    
    def test_no_gpt_5_4_in_translation_service(self):
        """Verify no gpt-5.4 in translation service"""
        with open('/app/backend/services/translation/service.py', 'r') as f:
            content = f.read()
        
        assert 'gpt-5.4' not in content, \
            "translation/service.py should not contain gpt-5.4"
        assert 'gpt-5.2' not in content, \
            "translation/service.py should not contain gpt-5.2"
        print("PASS: No hardcoded gpt-5.4/gpt-5.2 in translation service")


class TestRateLimiterIdentity:
    """Test 6: Rate limiter uses device-id/auth-token hash, not raw IP primary"""
    
    def test_rate_limiter_checks_device_id_first(self):
        """Verify rate limiter checks x-device-id header first"""
        with open('/app/backend/lib/rate_limiting.py', 'r') as f:
            content = f.read()
        
        # Check for device_id header check
        assert 'x-device-id' in content, \
            "rate_limiting.py should check x-device-id header"
        assert 'device:' in content, \
            "rate_limiting.py should prefix device-based identity with 'device:'"
        print("PASS: Rate limiter checks x-device-id header")
    
    def test_rate_limiter_checks_auth_token_hash(self):
        """Verify rate limiter uses auth token hash as secondary identity"""
        with open('/app/backend/lib/rate_limiting.py', 'r') as f:
            content = f.read()
        
        # Check for auth token hashing
        assert 'sha256' in content or 'hashlib' in content, \
            "rate_limiting.py should hash auth tokens"
        assert 'auth:' in content, \
            "rate_limiting.py should prefix auth-based identity with 'auth:'"
        print("PASS: Rate limiter uses auth token hash")
    
    def test_rate_limiter_ip_is_fallback(self):
        """Verify IP is used as fallback, not primary"""
        with open('/app/backend/lib/rate_limiting.py', 'r') as f:
            content = f.read()
        
        # Check that IP is used as fallback (after device_id and auth checks)
        assert 'ip:' in content, \
            "rate_limiting.py should have IP fallback"
        
        # Verify the order: device_id first, then auth, then IP
        device_pos = content.find('x-device-id')
        auth_pos = content.find('auth_headers')
        ip_pos = content.find('x-forwarded-for')
        
        assert device_pos < auth_pos < ip_pos, \
            "Rate limiter should check device_id, then auth, then IP (in that order)"
        print("PASS: IP is fallback identity in rate limiter")


class TestPhotoEdgeCacheMiddleware:
    """Test 7: PhotoEdgeCacheMiddleware catches call_next failures"""
    
    def test_middleware_catches_call_next_exception(self):
        """Verify middleware catches exceptions from call_next"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find PhotoEdgeCacheMiddleware class
        match = re.search(r'class PhotoEdgeCacheMiddleware.*?(?=class|\Z)', content, re.DOTALL)
        assert match, "Could not find PhotoEdgeCacheMiddleware class"
        
        middleware_content = match.group(0)
        
        # Check for try/except around call_next
        assert 'try:' in middleware_content, \
            "PhotoEdgeCacheMiddleware should have try block"
        assert 'await call_next(request)' in middleware_content, \
            "PhotoEdgeCacheMiddleware should call call_next"
        assert 'except Exception:' in middleware_content or 'except:' in middleware_content, \
            "PhotoEdgeCacheMiddleware should catch exceptions"
        print("PASS: PhotoEdgeCacheMiddleware has try/except around call_next")
    
    def test_middleware_returns_generic_500(self):
        """Verify middleware returns generic 500 on failure"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find PhotoEdgeCacheMiddleware class
        match = re.search(r'class PhotoEdgeCacheMiddleware.*?(?=class|\Z)', content, re.DOTALL)
        assert match, "Could not find PhotoEdgeCacheMiddleware class"
        
        middleware_content = match.group(0)
        
        # Check for JSONResponse with 500 status
        assert 'JSONResponse' in middleware_content, \
            "PhotoEdgeCacheMiddleware should use JSONResponse"
        assert 'status_code=500' in middleware_content, \
            "PhotoEdgeCacheMiddleware should return status_code=500"
        assert 'internal_server_error' in middleware_content, \
            "PhotoEdgeCacheMiddleware should return generic error message"
        print("PASS: PhotoEdgeCacheMiddleware returns generic 500 on failure")


class TestPreviewEnvParityFlags:
    """Test 8: Preview .env has required parity flags and CORS origins"""
    
    def test_tenant_ai_enabled(self):
        """Verify TENANT_AI_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'TENANT_AI_ENABLED=true' in content, \
            ".env should have TENANT_AI_ENABLED=true"
        print("PASS: TENANT_AI_ENABLED=true")
    
    def test_ai_admin_intelligence_enabled(self):
        """Verify AI_ADMIN_INTELLIGENCE_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'AI_ADMIN_INTELLIGENCE_ENABLED=true' in content, \
            ".env should have AI_ADMIN_INTELLIGENCE_ENABLED=true"
        print("PASS: AI_ADMIN_INTELLIGENCE_ENABLED=true")
    
    def test_ai_pm_intelligence_enabled(self):
        """Verify AI_PM_INTELLIGENCE_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'AI_PM_INTELLIGENCE_ENABLED=true' in content, \
            ".env should have AI_PM_INTELLIGENCE_ENABLED=true"
        print("PASS: AI_PM_INTELLIGENCE_ENABLED=true")
    
    def test_ai_safety_intelligence_enabled(self):
        """Verify AI_SAFETY_INTELLIGENCE_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'AI_SAFETY_INTELLIGENCE_ENABLED=true' in content, \
            ".env should have AI_SAFETY_INTELLIGENCE_ENABLED=true"
        print("PASS: AI_SAFETY_INTELLIGENCE_ENABLED=true")
    
    def test_ai_translation_enabled(self):
        """Verify AI_TRANSLATION_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'AI_TRANSLATION_ENABLED=true' in content, \
            ".env should have AI_TRANSLATION_ENABLED=true"
        print("PASS: AI_TRANSLATION_ENABLED=true")
    
    def test_scheduler_enabled(self):
        """Verify SCHEDULER_ENABLED=true"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        assert 'SCHEDULER_ENABLED=true' in content, \
            ".env should have SCHEDULER_ENABLED=true"
        print("PASS: SCHEDULER_ENABLED=true")
    
    def test_cors_origins_pinned_to_mascidocs(self):
        """Verify CORS_ORIGINS is pinned to mascidocs domains"""
        with open('/app/backend/.env', 'r') as f:
            content = f.read()
        
        # Check for mascidocs.com in CORS_ORIGINS
        assert 'CORS_ORIGINS=' in content, \
            ".env should have CORS_ORIGINS"
        assert 'mascidocs.com' in content, \
            "CORS_ORIGINS should include mascidocs.com"
        print("PASS: CORS_ORIGINS pinned to mascidocs domains")


class TestSeniorSuperintendentPersona:
    """Test 9: Senior superintendent persona and parallel per-photo loop preserved"""
    
    def test_senior_superintendent_persona_in_vision(self):
        """Verify senior superintendent persona in vision.py"""
        with open('/app/backend/services/dr_ai/vision.py', 'r') as f:
            content = f.read()
        
        assert 'senior construction superintendent' in content, \
            "vision.py should have senior construction superintendent persona"
        assert 'forensic jobsite photo analyst' in content, \
            "vision.py should have forensic jobsite photo analyst persona"
        print("PASS: Senior superintendent persona preserved in vision.py")
    
    def test_parallel_per_photo_loop_preserved(self):
        """Verify parallel per-photo loop with asyncio.gather"""
        with open('/app/backend/services/dr_ai/vision.py', 'r') as f:
            content = f.read()
        
        # Check for asyncio.gather for parallel processing
        assert 'asyncio.gather' in content, \
            "vision.py should use asyncio.gather for parallel processing"
        assert 'asyncio.Semaphore' in content, \
            "vision.py should use Semaphore for concurrency control"
        assert 'VISION_MAX_CONCURRENCY' in content, \
            "vision.py should have VISION_MAX_CONCURRENCY constant"
        print("PASS: Parallel per-photo loop preserved in vision.py")


class TestLiveEndpoints:
    """Live endpoint tests against the running backend"""
    
    def test_health_endpoint(self):
        """Verify backend is running"""
        import requests
        
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"PASS: Health endpoint returns 200")
    
    def test_draft_summary_endpoint_exists(self):
        """Verify draft summary endpoint is accessible"""
        import requests
        
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        # Send minimal payload to test endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json={"payload": {}, "language": "en"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Should return 200 (even with empty payload, it returns deterministic fallback)
        assert response.status_code == 200, f"Draft summary endpoint failed: {response.status_code}"
        
        data = response.json()
        assert 'ok' in data, "Response should have 'ok' field"
        assert 'mode' in data, "Response should have 'mode' field"
        print(f"PASS: Draft summary endpoint returns 200 with mode={data.get('mode')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
