"""WAVE-5 KPI reconciliation contract (live PREVIEW, read-only, no writes).

Scope:
  * PC-COST-QUANTITY  -> lib.kpi_percent_complete.quantity_progress_percent
      - GET /api/pm/jobs                              (cost_code_progress_percent)
      - GET /api/cost-codes/projects/{pn}/progress    (overall_percent_complete)
  * KPI-UTILIZATION   -> lib.kpi_percent_complete.utilization_percent
      - GET /api/operations/utilization               (totals/fleet_size/rows)
      - GET /api/pm/projects/{pn}/operational-kpis    (equipment.utilization_percent)
  * KPI-EXPIRING-RATE -> lib.kpi_expiry.expiry_status
      - GET /api/document-expirations                 (status labels)
      - GET /api/document-expirations/summary         (expiring_30d / expired)
  * Regression: GET /api/hr/employee-completeness,
                GET /api/asset-spine/assets/{id}/onboarding

Auth: POST /api/auth/multi-login then per-portal X-<Portal>-Token fan-out
bound to X-Directory-Token (intentional session binding).
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
TIMEOUT = 90
EXPIRY_LABELS = {"Current", "Expiring Soon", "Expired", "Not Applicable"}


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


@pytest.fixture(scope="module")
def portal_headers(auth):
    """Fan out every minted portal token exactly like the SPA does."""
    h = {"X-Directory-Token": auth["session_token"]}
    for portal, token in (auth.get("portal_tokens") or {}).items():
        h[f"X-{portal.replace('_', '-').title()}-Token"] = token
    return h


@pytest.fixture(scope="module")
def pm_jobs(session, admin_headers):
    r = session.get(f"{BASE_URL}/api/pm/jobs", headers=admin_headers, timeout=TIMEOUT)
    assert r.status_code == 200, f"/api/pm/jobs {r.status_code}: {r.text[:300]}"
    return r.json()


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ==================== 1 · PC-COST-QUANTITY calculator (unit) ===============
class TestQuantityProgressCalculator:
    def test_overrun_not_clamped_by_default(self):
        from lib.kpi_percent_complete import quantity_progress_percent
        assert quantity_progress_percent(150, 100) == 150.0
        assert quantity_progress_percent(150, 100, clamp_max=100.0) == 100.0

    def test_zero_and_missing_denominator_governed_empty(self):
        from lib.kpi_percent_complete import quantity_progress_percent
        assert quantity_progress_percent(10, 0) == 0.0
        assert quantity_progress_percent(10, None) == 0.0
        assert quantity_progress_percent(10, -5) == 0.0
        assert quantity_progress_percent(10, 0, empty=None) is None

    def test_rounding_and_string_inputs(self):
        from lib.kpi_percent_complete import quantity_progress_percent
        assert quantity_progress_percent(1, 3) == 33.33
        assert quantity_progress_percent("50", "200") == 25.0
        assert quantity_progress_percent(None, 200) == 0.0


# ==================== 2 · PC-COST live endpoints ==========================
class TestCostQuantityProgressLive:
    def test_pm_jobs_returns_numeric_progress(self, pm_jobs):
        assert pm_jobs.get("ok") is True
        items = pm_jobs.get("items") or []
        assert isinstance(items, list) and items, "no jobs returned in preview"
        bad = [
            (j.get("project_number"), j.get("cost_code_progress_percent"))
            for j in items
            if not _num(j.get("cost_code_progress_percent"))
            or float(j.get("cost_code_progress_percent")) < 0
        ]
        assert not bad, f"non-numeric/negative cost_code_progress_percent: {bad[:5]}"

    def test_cost_code_progress_snapshot_contract(self, session, admin_headers, pm_jobs):
        items = pm_jobs.get("items") or []
        checked = 0
        overruns = []
        for job in items[:12]:
            pn = job.get("project_number") or ""
            if not pn:
                continue
            r = session.get(
                f"{BASE_URL}/api/cost-codes/projects/{pn}/progress",
                headers=admin_headers, timeout=TIMEOUT,
            )
            assert r.status_code == 200, f"{pn} progress {r.status_code}: {r.text[:200]}"
            body = r.json()
            snap = body.get("progress") if isinstance(body.get("progress"), dict) else body
            if not snap or "overall_percent_complete" not in snap:
                continue
            checked += 1
            overall = snap["overall_percent_complete"]
            assert _num(overall) and float(overall) >= 0, f"{pn} overall={overall!r}"
            auth_total = float(snap.get("total_authorized_quantity") or 0)
            inst_total = float(snap.get("total_installed_quantity") or 0)
            if auth_total > 0:
                assert abs(float(overall) - round(100.0 * inst_total / auth_total, 2)) <= 0.02, (
                    f"{pn} overall {overall} != installed/authorized"
                )
            else:
                assert float(overall) == 0.0, f"{pn} zero-denominator should be 0.0, got {overall}"
            for code in snap.get("codes") or []:
                pct = code.get("progress_percent")
                assert _num(pct) and float(pct) >= 0, f"{pn}/{code.get('code')} pct={pct!r}"
                if float(pct) > 100:
                    overruns.append((pn, code.get("code"), pct))
        assert checked > 0, "no project exposed a progress snapshot to validate"
        print(f"progress snapshots validated={checked}; overrun>100 samples={overruns[:5]}")

    def test_overrun_is_not_clamped_when_present(self, session, admin_headers, pm_jobs):
        """If any code has installed > authorized, its percent MUST exceed 100."""
        violations = []
        for job in (pm_jobs.get("items") or [])[:12]:
            pn = job.get("project_number") or ""
            if not pn:
                continue
            r = session.get(f"{BASE_URL}/api/cost-codes/projects/{pn}/progress",
                            headers=admin_headers, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            body = r.json()
            snap = body.get("progress") if isinstance(body.get("progress"), dict) else body
            for code in (snap or {}).get("codes") or []:
                inst = float(code.get("installed_quantity") or 0)
                auth_q = float(code.get("authorized_quantity") or 0)
                if auth_q > 0 and inst > auth_q and float(code.get("progress_percent") or 0) <= 100:
                    violations.append((pn, code.get("code"), inst, auth_q, code.get("progress_percent")))
        assert not violations, f"overrun clamped at 100: {violations[:5]}"

    def test_nonzero_progress_project_is_exact(self, session, admin_headers, pm_jobs):
        """Non-vacuous check: at least one preview project has installed > 0 and its
        percent must equal 100*installed/authorized (2 dp)."""
        nonzero = [
            j for j in (pm_jobs.get("items") or [])
            if float(j.get("cost_code_progress_percent") or 0) > 0
        ]
        if not nonzero:
            pytest.skip("no project with non-zero cost_code_progress_percent in preview")
        job = nonzero[0]
        pn = job["project_number"]
        r = session.get(f"{BASE_URL}/api/cost-codes/projects/{pn}/progress",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        snap = body.get("progress") if isinstance(body.get("progress"), dict) else body
        auth_q = float(snap.get("total_authorized_quantity") or 0)
        inst_q = float(snap.get("total_installed_quantity") or 0)
        assert auth_q > 0 and inst_q > 0, f"{pn} vacuous quantities auth={auth_q} inst={inst_q}"
        expected = round(100.0 * inst_q / auth_q, 2)
        assert float(snap["overall_percent_complete"]) == expected, (
            f"{pn} overall={snap['overall_percent_complete']} expected={expected}"
        )
        print(f"non-vacuous PC-COST: {pn} {inst_q}/{auth_q} -> {expected}%")

# ==================== 3 · KPI-UTILIZATION calculator (unit) ================
class TestUtilizationCalculator:
    def test_capacity_bounded_and_governed_empty(self):
        from lib.kpi_percent_complete import utilization_percent
        assert utilization_percent(120, 100) == 100.0
        assert utilization_percent(50, 100) == 50.0
        assert utilization_percent(5, 0) == 0.0
        assert utilization_percent(5, None) == 0.0
        assert utilization_percent(5, 0, empty=None) is None
        assert utilization_percent(1, 3, ndigits=6) == 33.333333


# ==================== 4 · KPI-UTILIZATION live endpoints ==================
class TestUtilizationLive:
    def test_operations_utilization_endpoint(self, session, portal_headers):
        r = session.get(f"{BASE_URL}/api/operations/utilization",
                        headers=portal_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"/operations/utilization {r.status_code}: {r.text[:300]}"
        d = r.json()
        assert _num(d.get("fleet_size")) and d["fleet_size"] >= 0, d.get("fleet_size")
        assert isinstance(d.get("totals"), dict), f"totals missing: {list(d)}"
        assert isinstance(d.get("rows"), list), f"rows missing: {list(d)}"
        total_bucketed = sum(v for v in d["totals"].values() if _num(v))
        print(f"fleet_size={d['fleet_size']} totals={d['totals']} rows={len(d['rows'])} "
              f"bucket_sum={total_bucketed}")

    def test_pm_operational_kpis_utilization_percent(self, session, admin_headers, pm_jobs):
        checked = 0
        for job in (pm_jobs.get("items") or [])[:8]:
            pn = job.get("project_number") or ""
            if not pn:
                continue
            r = session.get(
                f"{BASE_URL}/api/pm/projects/{pn}/operational-kpis?window=30d",
                headers=admin_headers, timeout=TIMEOUT,
            )
            assert r.status_code == 200, f"{pn} operational-kpis {r.status_code}: {r.text[:300]}"
            eq = (r.json() or {}).get("equipment") or {}
            up = eq.get("utilization_percent")
            assert _num(up), f"{pn} utilization_percent={up!r}"
            assert 0.0 <= float(up) <= 100.0, f"{pn} utilization_percent out of bounds: {up}"
            run = float(eq.get("total_run_hours") or 0)
            idle = float(eq.get("total_idle_hours") or 0)
            if run + idle > 0:
                assert abs(float(up) - round(100.0 * run / (run + idle), 1)) <= 0.15, (
                    f"{pn} utilization {up} != run/(run+idle) run={run} idle={idle}"
                )
            else:
                assert float(up) == 0.0, f"{pn} no hours observed but utilization={up}"
            checked += 1
        assert checked > 0, "no project operational-kpis payload validated"

    def test_nonzero_equipment_hours_utilization_is_exact(self, session, admin_headers, pm_jobs):
        """Non-vacuous KPI-UTILIZATION: find a project/window with run hours > 0 and
        assert utilization_percent == round(100*run/(run+idle), 1)."""
        for job in (pm_jobs.get("items") or []):
            pn = job.get("project_number") or ""
            if not pn:
                continue
            for window in ("ptd", "30d"):
                r = session.get(
                    f"{BASE_URL}/api/pm/projects/{pn}/operational-kpis?window={window}",
                    headers=admin_headers, timeout=TIMEOUT,
                )
                if r.status_code != 200:
                    continue
                eq = (r.json() or {}).get("equipment") or {}
                run = float(eq.get("total_run_hours") or 0)
                idle = float(eq.get("total_idle_hours") or 0)
                if run <= 0:
                    continue
                up = eq.get("utilization_percent")
                expected = round(100.0 * run / (run + idle), 1)
                assert _num(up) and float(up) == expected, (
                    f"{pn}/{window} utilization {up} != {expected} (run={run} idle={idle})"
                )
                assert 0.0 <= float(up) <= 100.0
                print(f"non-vacuous KPI-UTILIZATION: {pn}/{window} run={run} idle={idle} -> {up}%")
                return
        pytest.skip("no project/window with non-zero equipment run hours in preview")


# ==================== 5 · KPI-EXPIRING-RATE calculator (unit) ==============
class TestExpiryStatusCalculator:
    def test_governed_boundaries(self):
        from datetime import datetime, timedelta, timezone
        from lib.kpi_expiry import expiry_status
        now = datetime.now(timezone.utc)
        today = now.date()
        assert expiry_status(today.isoformat(), horizon_days=60, now=now) == "Expiring Soon"
        assert expiry_status((today - timedelta(days=1)).isoformat(), horizon_days=60, now=now) == "Expired"
        assert expiry_status((today + timedelta(days=60)).isoformat(), horizon_days=60, now=now) == "Expiring Soon"
        assert expiry_status((today + timedelta(days=61)).isoformat(), horizon_days=60, now=now) == "Current"

    def test_missing_is_not_applicable(self):
        from lib.kpi_expiry import expiry_status
        for bad in (None, "", "   ", "not-a-date", "0000-99-99"):
            assert expiry_status(bad) == "Not Applicable", bad


# ==================== 6 · KPI-EXPIRING-RATE live endpoints =================
class TestDocumentExpirationsLive:
    def test_list_status_labels_are_governed(self, session, portal_headers):
        r = session.get(f"{BASE_URL}/api/document-expirations?limit=500",
                        headers=portal_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"/document-expirations {r.status_code}: {r.text[:300]}"
        d = r.json()
        items = d.get("items")
        assert isinstance(items, list), f"items missing: {list(d)}"
        assert _num(d.get("count")) and d["count"] == len(items)
        unknown = sorted({
            str(i.get("status")) for i in items
            if str(i.get("status")) not in EXPIRY_LABELS and str(i.get("status")) != "Archived"
        })
        assert not unknown, f"non-governed status labels present: {unknown}"
        print(f"document_expirations items={len(items)}")

    def test_missing_expiration_date_is_not_applicable(self, session, portal_headers):
        r = session.get(f"{BASE_URL}/api/document-expirations?limit=500",
                        headers=portal_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        offenders = [
            (i.get("id"), i.get("expiration_date"), i.get("status"))
            for i in (r.json().get("items") or [])
            if not str(i.get("expiration_date") or "").strip()
            and str(i.get("status")) not in ("Not Applicable", "Archived")
        ]
        assert not offenders, f"missing expiration_date not 'Not Applicable': {offenders[:5]}"

    def test_status_matches_canonical_recompute(self, session, portal_headers):
        from lib.kpi_expiry import expiry_status
        r = session.get(f"{BASE_URL}/api/document-expirations?limit=500",
                        headers=portal_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        drift = []
        for i in r.json().get("items") or []:
            if str(i.get("status")) == "Archived":
                continue
            expected = expiry_status(i.get("expiration_date"), horizon_days=60)
            if str(i.get("status")) != expected:
                drift.append((i.get("id"), i.get("expiration_date"), i.get("status"), expected))
        assert not drift, (
            "persisted status drifted from canonical expiry_status (list endpoint returns the "
            f"stored value, it does not recompute): {drift[:5]} (total {len(drift)})"
        )

    def test_super_admin_can_see_existing_documents(self, session, admin_headers):
        """Data-visibility guard: preview DB holds document_expirations rows, so a
        Super-Admin read MUST NOT return an empty scope."""
        from pymongo import MongoClient
        benv = dotenv_values("/app/backend/.env")
        cli = MongoClient(benv["MONGO_URL"], serverSelectionTimeoutMS=8000)
        try:
            db_total = cli[benv["DB_NAME"]].document_expirations.count_documents({})
        finally:
            cli.close()
        if db_total == 0:
            pytest.skip("no document_expirations rows in preview db")
        r = session.get(f"{BASE_URL}/api/document-expirations?limit=500",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:200]
        count = r.json().get("count")
        assert count and count > 0, (
            f"Super Admin sees 0 of {db_total} document_expirations rows — _read_scope() reads "
            "context['permissions'] / context['is_super_admin'] / context['authority_level'], "
            "none of which resolve_governance_actor_context() returns (it returns "
            "governance_scope_mode='global' + direct_permissions/delegated_permissions), so every "
            "caller falls through to {'_unreachable': True}."
        )

    def test_summary_reflects_existing_documents(self, session, admin_headers):
        from pymongo import MongoClient
        benv = dotenv_values("/app/backend/.env")
        cli = MongoClient(benv["MONGO_URL"], serverSelectionTimeoutMS=8000)
        try:
            db_total = cli[benv["DB_NAME"]].document_expirations.count_documents({})
        finally:
            cli.close()
        if db_total == 0:
            pytest.skip("no document_expirations rows in preview db")
        r = session.get(f"{BASE_URL}/api/document-expirations/summary",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:200]
        by_status = r.json().get("by_status") or {}
        assert by_status, (
            f"summary by_status empty while {db_total} rows exist — same _read_scope() "
            "governance-context key mismatch blanks the summary."
        )

    def test_persisted_status_matches_canonical_expiry_status_db(self):
        """API scope is blind (see visibility test), so validate the migrated
        compute_status against the persisted rows directly. Archived is a lifecycle
        state, not an expiry bucket, so it is excluded."""
        from pymongo import MongoClient
        from lib.kpi_expiry import expiry_status
        benv = dotenv_values("/app/backend/.env")
        cli = MongoClient(benv["MONGO_URL"], serverSelectionTimeoutMS=8000)
        try:
            rows = list(cli[benv["DB_NAME"]].document_expirations.find(
                {}, {"_id": 0, "id": 1, "status": 1, "expiration_date": 1}))
        finally:
            cli.close()
        if not rows:
            pytest.skip("no document_expirations rows in preview db")
        drift, labels = [], set()
        for d in rows:
            st = str(d.get("status"))
            labels.add(st)
            if st == "Archived":
                continue
            expected = expiry_status(d.get("expiration_date"), horizon_days=60)
            if st != expected:
                drift.append((d.get("id"), d.get("expiration_date"), st, expected))
        assert not drift, f"persisted status != canonical expiry_status: {drift[:5]} of {len(rows)}"
        assert labels <= (EXPIRY_LABELS | {"Archived"}), f"ungoverned labels: {labels}"
        print(f"db rows={len(rows)} labels={sorted(labels)}")

    def test_summary_counts_numeric(self, session, portal_headers):
        r = session.get(f"{BASE_URL}/api/document-expirations/summary",
                        headers=portal_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"/summary {r.status_code}: {r.text[:300]}"
        d = r.json()
        assert isinstance(d.get("by_status"), dict), f"by_status missing: {list(d)}"
        for k in ("expiring_30d", "expired"):
            assert _num(d.get(k)) and d[k] >= 0, f"{k}={d.get(k)!r}"
        print(f"summary={d}")


# ==================== 7 · Regression (iteration_25 scope) =================
class TestWave5Regression:
    def test_hr_employee_completeness(self, session, admin_headers):
        r = session.get(f"{BASE_URL}/api/hr/employee-completeness",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"employee-completeness {r.status_code}: {r.text[:300]}"
        d = r.json()
        for k in ("completion_percent", "trade_role_complete_percent",
                  "crew_complete_percent", "supervisor_complete_percent"):
            assert _num(d.get(k)) and 0.0 <= float(d[k]) <= 100.0, f"{k}={d.get(k)!r}"

    def test_asset_onboarding_returns_pct_complete(self, session, admin_headers):
        lst = session.get(f"{BASE_URL}/api/asset-spine/assets?limit=5",
                          headers=admin_headers, timeout=TIMEOUT)
        assert lst.status_code == 200, f"assets list {lst.status_code}: {lst.text[:300]}"
        body = lst.json()
        assets = body if isinstance(body, list) else (body.get("items") or body.get("assets") or [])
        assert assets, f"no assets returned: {str(body)[:200]}"
        asset_id = assets[0].get("id") or assets[0].get("asset_id")
        r = session.get(f"{BASE_URL}/api/asset-spine/assets/{asset_id}/onboarding",
                        headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200, (
            f"onboarding {r.status_code} for existing asset {asset_id}: {r.text[:200]}"
        )
        pct = r.json().get("pct_complete")
        assert _num(pct) and 0.0 <= float(pct) <= 100.0, f"pct_complete={pct!r}"
