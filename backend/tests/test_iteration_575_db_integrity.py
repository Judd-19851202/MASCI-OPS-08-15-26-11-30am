"""
Iteration 575 - DB Integrity Fixes Verification Tests

Tests for production-targeted database integrity patch:
1. AsyncIOMotorClient uses maxPoolSize=50
2. Synchronous PyMongo client inside _build_complete_archive_on_disk uses maxPoolSize=10
3. Production bottleneck ensure-index hook creates usage_events indexes
4. usage_analytics ensure_usage_indexes also creates the new usage_events indexes
5. _build_complete_archive_on_disk explicitly excludes usage_events from the archive scan loop
6. Backend still starts cleanly after the DB integrity patch
"""
import pytest
import requests
import os
import re
import ast

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDBIntegrityCodeVerification:
    """Static code verification for DB integrity changes"""

    def test_async_motor_client_max_pool_size_50(self):
        """Verify AsyncIOMotorClient uses maxPoolSize=50"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the line with AsyncIOMotorClient and maxPoolSize
        pattern = r'AsyncIOMotorClient\([^)]*maxPoolSize\s*=\s*50[^)]*\)'
        match = re.search(pattern, content)
        assert match is not None, "AsyncIOMotorClient should use maxPoolSize=50"
        print("PASS: AsyncIOMotorClient uses maxPoolSize=50")

    def test_sync_pymongo_client_max_pool_size_10(self):
        """Verify synchronous PyMongo client in _build_complete_archive_on_disk uses maxPoolSize=10"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the _build_complete_archive_on_disk function and check for maxPoolSize=10
        # The sync client is created with _MC(..., maxPoolSize=10)
        pattern = r'_MC\([^)]*maxPoolSize\s*=\s*10[^)]*\)'
        matches = re.findall(pattern, content)
        assert len(matches) >= 1, "Synchronous PyMongo client should use maxPoolSize=10"
        print(f"PASS: Found {len(matches)} PyMongo client(s) with maxPoolSize=10")

    def test_production_bottleneck_indexes_function_exists(self):
        """Verify _ensure_production_bottleneck_indexes function exists"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        assert '_ensure_production_bottleneck_indexes' in content, \
            "_ensure_production_bottleneck_indexes function should exist"
        print("PASS: _ensure_production_bottleneck_indexes function exists")

    def test_production_bottleneck_indexes_creates_usage_events_indexes(self):
        """Verify _ensure_production_bottleneck_indexes creates the 3 new usage_events indexes"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the _ensure_production_bottleneck_indexes function
        func_start = content.find('async def _ensure_production_bottleneck_indexes')
        assert func_start != -1, "_ensure_production_bottleneck_indexes function not found"
        
        # Get the function body (until next function or class)
        func_end = content.find('\n@', func_start + 1)
        if func_end == -1:
            func_end = content.find('\nclass ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        # Check for the 3 usage_events indexes
        expected_indexes = [
            ('kind', 1), ('signal', 1), ('at', -1),  # Index 1
        ]
        
        # Verify usage_events indexes are created
        assert 'usage_events.create_index' in func_body, \
            "usage_events indexes should be created in _ensure_production_bottleneck_indexes"
        
        # Check for specific index patterns (using double quotes as in the actual code)
        assert '("kind", 1), ("signal", 1), ("at", -1)' in func_body, \
            "Index (kind, signal, at) should be created"
        assert '("kind", 1), ("signal", 1), ("at", -1), ("elapsed_ms", 1)' in func_body, \
            "Index (kind, signal, at, elapsed_ms) should be created"
        assert '("kind", 1), ("signal", 1), ("at", -1), ("dims.equipment_id", 1)' in func_body, \
            "Index (kind, signal, at, dims.equipment_id) should be created"
        
        print("PASS: _ensure_production_bottleneck_indexes creates all 3 usage_events indexes")

    def test_usage_analytics_ensure_indexes_creates_new_indexes(self):
        """Verify usage_analytics.ensure_usage_indexes creates the new indexes"""
        with open('/app/backend/routes/usage_analytics.py', 'r') as f:
            content = f.read()
        
        # Check for the 3 new usage_events indexes (using double quotes as in the actual code)
        assert '("kind", 1), ("signal", 1), ("at", -1)' in content, \
            "Index (kind, signal, at) should be in usage_analytics"
        assert '("kind", 1), ("signal", 1), ("at", -1), ("elapsed_ms", 1)' in content, \
            "Index (kind, signal, at, elapsed_ms) should be in usage_analytics"
        assert '("kind", 1), ("signal", 1), ("at", -1), ("dims.equipment_id", 1)' in content, \
            "Index (kind, signal, at, dims.equipment_id) should be in usage_analytics"
        
        print("PASS: usage_analytics.ensure_usage_indexes creates all 3 new indexes")

    def test_build_complete_archive_excludes_usage_events(self):
        """Verify _build_complete_archive_on_disk explicitly excludes usage_events"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the _build_complete_archive_on_disk function
        func_start = content.find('def _build_complete_archive_on_disk')
        assert func_start != -1, "_build_complete_archive_on_disk function not found"
        
        # Get the function body
        func_end = content.find('\ndef ', func_start + 10)
        if func_end == -1:
            func_end = content.find('\nasync def ', func_start + 10)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        # Check for explicit usage_events exclusion in the archive loop
        # The pattern should be: if coll_name == "usage_events" or ...
        assert 'coll_name == "usage_events"' in func_body, \
            "_build_complete_archive_on_disk should explicitly exclude usage_events"
        
        print("PASS: _build_complete_archive_on_disk explicitly excludes usage_events")

    def test_usage_events_in_backup_explicit_exclusions(self):
        """Verify usage_events is in BACKUP_EXPLICIT_EXCLUSIONS"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find BACKUP_EXPLICIT_EXCLUSIONS
        pattern = r'BACKUP_EXPLICIT_EXCLUSIONS\s*=\s*\{[^}]*"usage_events"[^}]*\}'
        match = re.search(pattern, content, re.DOTALL)
        
        # Also check if it's in a list/set
        if not match:
            pattern2 = r'BACKUP_EXPLICIT_EXCLUSIONS\s*=\s*\[[^\]]*"usage_events"[^\]]*\]'
            match = re.search(pattern2, content, re.DOTALL)
        
        assert match is not None, "usage_events should be in BACKUP_EXPLICIT_EXCLUSIONS"
        print("PASS: usage_events is in BACKUP_EXPLICIT_EXCLUSIONS")


class TestBackendHealthAfterPatch:
    """Live endpoint tests to verify backend starts cleanly"""

    def test_health_endpoint_responds(self):
        """Verify /api/health endpoint responds with ok=true"""
        import subprocess
        import json
        # Use subprocess with curl for more reliable testing
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", "http://127.0.0.1:8001/api/health"],
            capture_output=True, text=True, timeout=35
        )
        assert result.returncode == 0, f"curl failed with code {result.returncode}"
        data = json.loads(result.stdout)
        assert data.get('ok') is True, "Health endpoint should return ok=true"
        print(f"PASS: Health endpoint responds with ok=true, service={data.get('service')}")

    def test_version_endpoint_responds(self):
        """Verify /api/version endpoint responds"""
        import subprocess
        import json
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", "http://127.0.0.1:8001/api/version"],
            capture_output=True, text=True, timeout=35
        )
        assert result.returncode == 0, f"curl failed with code {result.returncode}"
        data = json.loads(result.stdout)
        assert 'version' in data or 'source_hash' in data, "Version endpoint should return version info"
        print(f"PASS: Version endpoint responds")

    def test_health_full_endpoint_responds(self):
        """Verify /api/health/full endpoint responds"""
        import subprocess
        import json
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", "http://127.0.0.1:8001/api/health/full"],
            capture_output=True, text=True, timeout=35
        )
        assert result.returncode == 0, f"curl failed with code {result.returncode}"
        data = json.loads(result.stdout)
        assert 'ok' in data, "Health/full endpoint should return ok field"
        assert 'mongo' in data, "Health/full endpoint should return mongo field"
        print(f"PASS: Health/full endpoint responds, mongo={data.get('mongo')}")


class TestIndexCreationVerification:
    """Verify index creation patterns are correct"""

    def test_r2_inventory_indexes_in_bottleneck_function(self):
        """Verify r2_inventory indexes are created in bottleneck function"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the _ensure_production_bottleneck_indexes function
        func_start = content.find('async def _ensure_production_bottleneck_indexes')
        func_end = content.find('\n@', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        assert 'r2_inventory.create_index("size")' in func_body, \
            "r2_inventory size index should be created"
        assert 'r2_inventory.create_index("content_type")' in func_body, \
            "r2_inventory content_type index should be created"
        
        print("PASS: r2_inventory indexes (size, content_type) are created")

    def test_r2_references_index_in_bottleneck_function(self):
        """Verify r2_references index is created in bottleneck function"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        func_start = content.find('async def _ensure_production_bottleneck_indexes')
        func_end = content.find('\n@', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        assert 'r2_references.create_index("r2_key")' in func_body, \
            "r2_references r2_key index should be created"
        
        print("PASS: r2_references r2_key index is created")

    def test_daily_reports_index_in_bottleneck_function(self):
        """Verify daily_reports index is created in bottleneck function"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        func_start = content.find('async def _ensure_production_bottleneck_indexes')
        func_end = content.find('\n@', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        assert 'daily_reports.create_index("report_number")' in func_body, \
            "daily_reports report_number index should be created"
        
        print("PASS: daily_reports report_number index is created")


class TestPreviousStabilityFixesPreserved:
    """Verify previous stability fixes from iteration 574 are still intact"""

    def test_usage_analytics_uses_estimated_document_count(self):
        """Verify usage_analytics health endpoint uses estimated_document_count"""
        with open('/app/backend/routes/usage_analytics.py', 'r') as f:
            content = f.read()
        
        assert 'estimated_document_count' in content, \
            "usage_analytics should use estimated_document_count for health endpoint"
        print("PASS: usage_analytics uses estimated_document_count")

    def test_lifecycle_step_decorator_used(self):
        """Verify _ensure_production_bottleneck_indexes uses @register_lifecycle_step"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Find the decorator before the function
        pattern = r'@register_lifecycle_step\([^)]*\)\s*async def _ensure_production_bottleneck_indexes'
        match = re.search(pattern, content)
        assert match is not None, \
            "_ensure_production_bottleneck_indexes should use @register_lifecycle_step decorator"
        print("PASS: _ensure_production_bottleneck_indexes uses @register_lifecycle_step decorator")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
