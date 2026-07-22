"""Daily Report canonical consolidation checks.

These verify that canonical approved/PDF reads no longer depend on
the legacy DR V2 runtime endpoints.
"""

import json
import subprocess


def _login_tokens():
    proc = subprocess.run(
        [
            'curl', '-sS', '-H', 'Content-Type: application/json', '-X', 'POST',
            'http://localhost:8001/api/auth/multi-login',
            '-d', '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}',
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    obj = json.loads(proc.stdout)
    return (obj.get('portal_tokens') or {}).get('admin'), obj.get('session_token')


def _authed_get(path: str):
    admin, directory = _login_tokens()
    proc = subprocess.run(
        [
            'curl', '-sS',
            '-H', f'X-Admin-Token: {admin}',
            '-H', f'X-Directory-Token: {directory}',
            f'http://localhost:8001{path}',
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_approved_reports_are_canonical_only():
    payload = _authed_get('/api/daily-reports/approved')
    items = payload.get('items', [])
    assert isinstance(items, list)
    assert items, 'expected at least one approved daily report'
    assert all(item.get('source') == 'canonical' for item in items)


def test_daily_report_pdf_queue_uses_canonical_route_only():
    payload = _authed_get('/api/daily-reports/1/pdf')
    assert payload.get('ok') is True
    assert payload.get('kind') == 'daily_report_pdf'
    assert payload.get('status') == 'queued'