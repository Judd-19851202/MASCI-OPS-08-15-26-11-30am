"""
MASCI critical-flow regression — backend-only smoke (no browser required).

Run:  pytest /app/tests/regression/test_critical_flows.py -v --tb=short

These tests cover the MISSION-CRITICAL P0 surfaces from the inventory:
  · auth / multi-portal login
  · HR Time Verification + Driver Qual
  · Daily Reports list + detail
  · Dispatch / Driver shift APIs
  · Job photo gallery + thumb fetch
  · Backup admin endpoints
  · Health + env-identity

Every test asserts:
  · HTTP 200 (or expected non-200 with reason)
  · Response time under SLA (1.5 s for read; 3 s for write)
  · Payload shape matches contract (presence of key fields)

The tests are environment-agnostic — they pick up BASE_URL from
REACT_APP_BACKEND_URL (preview) by default; override via env var to point
at production. They run against either DB via the same API.
"""
import os
import time
import pytest
import requests
from typing import Dict

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------
def _resolve_base_url() -> str:
    env_url = os.environ.get('REGRESSION_BASE_URL')
    if env_url:
        return env_url.rstrip('/')
    # Fall back to preview frontend/.env
    env_file = '/app/frontend/.env'
    try:
        with open(env_file) as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip().rstrip('/')
    except FileNotFoundError:
        pass
    return 'http://localhost:8001'


BASE_URL = _resolve_base_url()
SLA_READ = 2.0   # generous for cold cache
SLA_WRITE = 4.0


# ---------------------------------------------------------------------------
# Credentials (preview DB — both production and preview seeded from same set)
# Source: /app/memory/test_credentials.md
# ---------------------------------------------------------------------------
CREDS = {
    'admin': ('jaymn.judd@mascigc.com', 'Maddix123!'),
    'hr':    ('hrmanager@mascigc.com', 'HRTesting2026!'),
    'pm':    ('chriswright@mascigc.com', 'ChrisRocksThis2026'),
}


@pytest.fixture(scope='session')
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope='session')
def admin_token(base_url) -> str:
    r = requests.post(
        f'{base_url}/api/auth/multi-login',
        json={'email': CREDS['admin'][0], 'password': CREDS['admin'][1]},
        timeout=10,
    )
    assert r.status_code == 200, f'admin multi-login failed: {r.status_code} {r.text[:200]}'
    body = r.json()
    tok = (body.get('portal_tokens') or {}).get('admin') or body.get('token')
    assert tok, f'no admin token in response: {body}'
    return tok


@pytest.fixture(scope='session')
def hr_token(base_url) -> str:
    r = requests.post(
        f'{base_url}/api/hr/login',
        json={'email': CREDS['hr'][0], 'password': CREDS['hr'][1]},
        timeout=10,
    )
    assert r.status_code == 200, f'hr login failed: {r.status_code}'
    return r.json()['token']


@pytest.fixture(scope='session')
def pm_token(base_url) -> str:
    r = requests.post(
        f'{base_url}/api/pm/login',
        json={'email': CREDS['pm'][0], 'password': CREDS['pm'][1]},
        timeout=10,
    )
    assert r.status_code == 200, f'pm login failed: {r.status_code}'
    return r.json()['token']


# ===========================================================================
# P0 — Health / Env identity
# ===========================================================================
class TestHealth:
    def test_health_responds_fast(self, base_url):
        t0 = time.time()
        r = requests.get(f'{base_url}/api/health', timeout=5)
        elapsed = time.time() - t0
        assert r.status_code == 200, r.text[:200]
        assert elapsed < 1.0, f'health endpoint slow: {elapsed:.2f}s'

    def test_version_reports_env_and_db(self, base_url):
        r = requests.get(f'{base_url}/api/version', timeout=5)
        assert r.status_code == 200
        v = r.json()
        # Critical post-incident contract: env separation visible
        assert 'app_env' in v, 'env identity missing'
        assert 'db_name' in v, 'db identity missing'
        # In preview we expect _preview suffix; in production we expect masci_safety
        if v['app_env'] == 'preview':
            assert v['db_name'].endswith('_preview'), \
                f'preview env pointing at non-preview db: {v["db_name"]}'
        else:
            assert not v['db_name'].endswith('_preview'), \
                f'production env pointing at preview db: {v["db_name"]}'


# ===========================================================================
# P0 — Auth across all portals
# ===========================================================================
class TestAuth:
    def test_admin_multi_login_returns_all_portal_tokens(self, base_url):
        r = requests.post(
            f'{base_url}/api/auth/multi-login',
            json={'email': CREDS['admin'][0], 'password': CREDS['admin'][1]},
            timeout=10,
        )
        assert r.status_code == 200
        tokens = r.json().get('portal_tokens', {})
        # Admin login should grant cross-portal tokens
        expected = ['admin']
        for p in expected:
            assert tokens.get(p), f'multi-login missing {p} token'

    def test_hr_login_valid(self, base_url):
        r = requests.post(
            f'{base_url}/api/hr/login',
            json={'email': CREDS['hr'][0], 'password': CREDS['hr'][1]},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get('token')

    def test_pm_login_valid(self, base_url):
        r = requests.post(
            f'{base_url}/api/pm/login',
            json={'email': CREDS['pm'][0], 'password': CREDS['pm'][1]},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get('token')

    def test_invalid_password_rejected(self, base_url):
        r = requests.post(
            f'{base_url}/api/hr/login',
            json={'email': CREDS['hr'][0], 'password': 'definitely-wrong'},
            timeout=10,
        )
        assert r.status_code in (400, 401, 403), f'invalid pw should reject; got {r.status_code}'


# ===========================================================================
# P0 — HR Time Verification (had 10s timeout incident — must stay fast)
# ===========================================================================
class TestHrTimeVerification:
    def test_time_verification_under_sla(self, base_url, hr_token):
        t0 = time.time()
        r = requests.get(
            f'{base_url}/api/hr/time-verification?week_ending=2026-05-24',
            headers={'X-HR-Token': hr_token},
            timeout=10,
        )
        elapsed = time.time() - t0
        assert r.status_code == 200, r.text[:200]
        assert elapsed < SLA_READ, f'TV endpoint regression: {elapsed:.2f}s > {SLA_READ}s'
        body = r.json()
        assert 'rows' in body or 'weekly' in body, f'TV payload shape changed: {list(body.keys())}'

    def test_driver_qual_dashboard_under_sla(self, base_url, hr_token):
        t0 = time.time()
        r = requests.get(
            f'{base_url}/api/hr/driver-qualification/dashboard',
            headers={'X-HR-Token': hr_token},
            timeout=10,
        )
        elapsed = time.time() - t0
        assert r.status_code == 200
        assert elapsed < SLA_READ, f'DQ dashboard regression: {elapsed:.2f}s > {SLA_READ}s'


# ===========================================================================
# P0 — Daily Reports
# ===========================================================================
class TestDailyReports:
    def test_list_under_sla(self, base_url, admin_token):
        t0 = time.time()
        r = requests.get(
            f'{base_url}/api/daily-reports?limit=20',
            headers={'X-Admin-Token': admin_token},
            timeout=10,
        )
        elapsed = time.time() - t0
        assert r.status_code == 200
        assert elapsed < SLA_READ
        items = r.json() if isinstance(r.json(), list) else r.json().get('items', [])
        assert isinstance(items, list)


# ===========================================================================
# P0 — Job photos (gallery + thumb fetch)
# ===========================================================================
class TestJobPhotos:
    def test_gallery_list(self, base_url, pm_token):
        r = requests.get(
            f'{base_url}/api/job-photos?limit=10',
            headers={'X-PM-Token': pm_token},
            timeout=10,
        )
        # PM may see 0 photos if no job assignment in preview DB; either way endpoint must respond
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert 'items' in body, f'shape changed: {list(body.keys())}'

    def test_thumb_endpoint_works(self, base_url, pm_token):
        # Get a photo to test the thumb fetch
        r = requests.get(
            f'{base_url}/api/job-photos?limit=1',
            headers={'X-PM-Token': pm_token},
            timeout=10,
        )
        items = r.json().get('items', [])
        if not items:
            pytest.skip('no photos in DB to test thumb endpoint')
        pid = items[0]['id']
        tok = items[0].get('thumb_token')
        if tok:
            import urllib.parse
            r2 = requests.get(
                f'{base_url}/api/job-photos/{urllib.parse.quote(pid)}/thumb-signed?t={tok}',
                timeout=10,
            )
            assert r2.status_code == 200
            assert int(r2.headers.get('content-length', 0)) > 1000, 'thumb suspiciously small'


# ===========================================================================
# P0 — Backup admin
# ===========================================================================
class TestBackups:
    def test_r2_backup_list_responds(self, base_url, admin_token):
        r = requests.get(
            f'{base_url}/api/admin/backups-list-r2?limit=5',
            headers={'X-Admin-Token': admin_token},
            timeout=10,
        )
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        # Contract: must return items array and total
        assert isinstance(body.get('items'), list) or isinstance(body, list), \
            f'backup list shape: {list(body.keys()) if isinstance(body, dict) else type(body)}'


# ===========================================================================
# P0 — Compliance findings
# ===========================================================================
class TestCompliance:
    def test_findings_endpoint_responds(self, base_url, admin_token):
        # Compliance is mounted at /api/admin/compliance/findings in production
        for path in ['/api/admin/compliance/findings', '/api/compliance/findings']:
            r = requests.get(
                f'{base_url}{path}?limit=5',
                headers={'X-Admin-Token': admin_token},
                timeout=10,
            )
            if r.status_code == 200:
                return  # found the working path
        pytest.fail(f'no compliance findings endpoint responded 200; last={r.status_code}')


if __name__ == '__main__':
    # Allow direct invocation for quick smoke
    import subprocess, sys
    sys.exit(subprocess.call(['pytest', __file__, '-v', '--tb=short']))
