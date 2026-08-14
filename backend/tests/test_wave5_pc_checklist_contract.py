"""WAVE-5 PC-CHECKLIST canonical calculator contract (live PREVIEW, read-only).

Scope:
  * lib/kpi_percent_complete.checklist_percent governed `empty` semantics (unit).
  * GET /api/hr/employee-completeness -> completion_percent +
    trade_role/crew/supervisor_complete_percent all numeric, 0-100, 1dp, and
    internally consistent with their *_complete_count / total_active.
  * GET /api/asset-spine/assets/{id}/onboarding -> pct_complete numeric 0-100,
    1dp, == round(100 * completed_steps / len(steps), 1); no 500.

Auth: POST /api/auth/multi-login, then per-portal header fan-out
(X-Admin-Token) bound to the directory session (X-Directory-Token).
No writes are performed.
"""
import os

import pytest
import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
_base = os.environ.get("REACT_APP_BACKEND_URL") or _env.get("REACT_APP_BACKEND_URL")
if not _base:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
BASE_URL = _base.rstrip("/")

SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
TIMEOUT = 60
PCT_KEYS = (
    "completion_percent",
    "trade_role_complete_percent",
    "crew_complete_percent",
    "supervisor_complete_percent",
)


# ------------------------------------------------------------------ fixtures
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth(session):
    r = session.post(f"{BASE_URL}/api/auth/multi-login", json=SUPER_ADMIN, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"multi-login failed {r.status_code}: {r.text[:300]}")
    d = r.json()
    if not (d.get("portal_tokens") or {}).get("admin"):
        pytest.fail(f"no admin portal token minted: {list((d.get('portal_tokens') or {}))}")
    return d


@pytest.fixture(scope="module")
def admin_headers(auth):
    return {
        "X-Admin-Token": auth["portal_tokens"]["admin"],
        "X-Directory-Token": auth["session_token"],
    }


def _is_pct(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 <= float(v) <= 100.0


def _one_dp(v):
    return round(float(v), 1) == float(v)


# ============================ 1 · canonical calculator (unit) ==============
class TestChecklistPercentCalculator:
    def test_governed_empty_semantics(self):
        from lib.kpi_percent_complete import checklist_percent
        assert checklist_percent(0, 0, empty=100.0) == 100.0
        assert checklist_percent(0, 0, empty=0.0) == 0.0
        assert checklist_percent(0, 0, empty=None) is None

    def test_ratio_rounding_and_clamp(self):
        from lib.kpi_percent_complete import checklist_percent
        assert checklist_percent(1, 3) == 33.3
        assert checklist_percent(2, 3) == 66.7
        assert checklist_percent(7, 12) == 58.3
        assert checklist_percent(12, 12) == 100.0
        assert checklist_percent(-5, 10) == 0.0
        assert checklist_percent(50, 10) == 100.0

    def test_hr_endpoint_uses_empty_100(self):
        """Guards the governed empty=100.0 choice for the fleet-wide HR scope
        (total_active==0 must be vacuously complete, not 0)."""
        src = open("/app/backend/routes/employee_lifecycle.py", encoding="utf-8").read()
        idx = src.find("trade_role_complete_percent\": checklist_percent")
        assert idx > 0, "trade_role_complete_percent not computed via checklist_percent"
        window = src[idx - 900:idx + 600]
        assert window.count("empty=100.0") >= 4, (
            "all four HR completeness percents must pass empty=100.0; "
            f"found {window.count('empty=100.0')}"
        )


# ============================ 2 · HR employee completeness ================
class TestHrEmployeeCompleteness:
    @pytest.fixture(scope="class")
    def payload(self, session, admin_headers):
        r = session.get(f"{BASE_URL}/api/hr/employee-completeness",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        return r.json()

    def test_requires_auth(self, session):
        r = session.get(f"{BASE_URL}/api/hr/employee-completeness", timeout=TIMEOUT)
        assert r.status_code in (401, 403), f"unauthenticated read allowed: {r.status_code}"

    def test_all_four_percents_present_numeric_1dp(self, payload):
        for k in PCT_KEYS:
            assert k in payload, f"missing field {k}"
            v = payload[k]
            assert _is_pct(v), f"{k} not numeric 0-100: {v!r}"
            assert _one_dp(v), f"{k} not 1 decimal place: {v!r}"

    def test_completion_percent_matches_counts(self, payload):
        total = payload["total_active"]
        assert isinstance(total, int)
        if total > 0:
            expected = round(100.0 * payload["complete_count"] / total, 1)
            assert payload["completion_percent"] == expected
        else:
            assert payload["completion_percent"] == 100.0

    @pytest.mark.parametrize("field", ["trade_role", "crew", "supervisor"])
    def test_per_field_percent_matches_counts(self, payload, field):
        total = payload["total_active"]
        cnt = payload[f"{field}_complete_count"]
        assert isinstance(cnt, int) and cnt >= 0
        got = payload[f"{field}_complete_percent"]
        if total > 0:
            assert cnt <= total, f"{field}_complete_count {cnt} > total_active {total}"
            assert got == round(100.0 * cnt / total, 1)
        else:
            assert got == 100.0

    def test_fully_complete_le_each_subfield(self, payload):
        for f in ("trade_role", "crew", "supervisor"):
            assert payload["complete_count"] <= payload[f"{f}_complete_count"]

    def test_status_band_consistent(self, payload):
        pct = payload["completion_percent"]
        expected = "green" if pct >= 95 else ("amber" if pct >= 75 else "red")
        assert payload["status_band"] == expected


# ============================ 3 · asset onboarding checklist ==============
class TestAssetOnboardingPctComplete:
    @pytest.fixture(scope="class")
    def asset_ids(self, session, admin_headers):
        r = session.get(f"{BASE_URL}/api/asset-spine/assets?limit=25",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"assets list {r.status_code}: {r.text[:400]}"
        body = r.json()
        rows = body if isinstance(body, list) else (
            body.get("assets") or body.get("items") or body.get("data") or []
        )
        ids = [
            a.get("id") or a.get("asset_id")
            for a in rows
            if isinstance(a, dict) and (a.get("id") or a.get("asset_id"))
        ]
        if not ids:
            pytest.fail(f"no asset ids in preview asset-spine list: {str(body)[:400]}")
        return ids[:5]

    def test_requires_portal_auth(self, session, asset_ids):
        r = session.get(f"{BASE_URL}/api/asset-spine/assets/{asset_ids[0]}/onboarding",
                        timeout=TIMEOUT)
        assert r.status_code in (401, 403), f"unauthenticated read allowed: {r.status_code}"

    def test_existing_asset_onboarding_is_not_404(self, session, admin_headers, asset_ids):
        """DEFECT GUARD: an asset readable via GET /assets/{id} must not 404 on
        /onboarding. Root cause when it does: find_one(..., {"_id":0,"onboarding":1})
        returns a FALSY {} for assets with no `onboarding` field, and the handler
        tests `if not doc` instead of `if doc is None`."""
        aid = asset_ids[0]
        base = session.get(f"{BASE_URL}/api/asset-spine/assets/{aid}",
                           headers=admin_headers, timeout=TIMEOUT)
        assert base.status_code == 200, f"asset {aid} not readable: {base.status_code}"
        ob = session.get(f"{BASE_URL}/api/asset-spine/assets/{aid}/onboarding",
                         headers=admin_headers, timeout=TIMEOUT)
        assert ob.status_code == 200, (
            f"existing asset {aid} -> /onboarding {ob.status_code}: {ob.text[:200]}"
        )

    def test_pct_complete_formula_over_canonical_steps(self):
        """Pure verification of the migrated expression against the real
        ONBOARDING_STEPS list (reachable without any write)."""
        from services.asset_spine import AssetSpine
        from lib.kpi_percent_complete import checklist_percent
        steps = list(AssetSpine.ONBOARDING_STEPS)
        assert len(steps) == 12, f"expected 12 canonical steps, got {len(steps)}"
        for done_n in range(len(steps) + 1):
            ob = {s: True for s in steps[:done_n]}
            got = checklist_percent(sum(1 for s in steps if ob.get(s)), len(steps),
                                    ndigits=1, empty=0.0)
            assert got == round(100.0 * done_n / len(steps), 1)
            assert 0.0 <= got <= 100.0

    def test_pct_complete_contract(self, session, admin_headers, asset_ids):
        checked = 0
        for aid in asset_ids:
            r = session.get(f"{BASE_URL}/api/asset-spine/assets/{aid}/onboarding",
                            headers=admin_headers, timeout=TIMEOUT)
            assert r.status_code == 200, f"{aid} -> {r.status_code}: {r.text[:300]}"
            d = r.json()
            steps = d["steps"]
            assert isinstance(steps, list) and len(steps) > 0
            completed = d["completed"]
            assert set(completed) == set(steps), "completed map must cover exactly steps"
            done = sum(1 for s in steps if completed.get(s))
            pct = d["pct_complete"]
            assert _is_pct(pct), f"{aid} pct_complete not numeric 0-100: {pct!r}"
            assert _one_dp(pct), f"{aid} pct_complete not 1dp: {pct!r}"
            assert pct == round(100.0 * done / len(steps), 1), (
                f"{aid}: pct_complete {pct} != {round(100.0 * done / len(steps), 1)} "
                f"({done}/{len(steps)})"
            )
            assert "_id" not in d
            checked += 1
        assert checked >= 1

    def test_unknown_asset_404_not_500(self, session, admin_headers):
        r = session.get(f"{BASE_URL}/api/asset-spine/assets/WAVE5-NOPE-000/onboarding",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:200]}"


# ============================ 4 · frontend no re-derivation ===============
def test_tile_renders_backend_percents_not_math_round():
    src = open("/app/frontend/src/components/HrCompletenessTile.jsx", encoding="utf-8").read()
    for tid in ("hr-completeness-metric-trade", "hr-completeness-metric-crew",
                "hr-completeness-metric-supervisor", "hr-completeness-metric-fully"):
        assert tid in src, f"missing data-testid {tid}"
    for k in PCT_KEYS:
        assert k in src, f"tile does not consume backend field {k}"
    # All four Metric call sites must pass a backend percent prop.
    assert src.count("percent={snap.") >= 4, "not all four metrics receive a backend percent prop"
    # The rendered string must prefer the backend percent over any local ratio.
    assert "percent !== undefined ? `${percent}%`" in src, (
        "Metric render does not prefer the backend-supplied percent"
    )
