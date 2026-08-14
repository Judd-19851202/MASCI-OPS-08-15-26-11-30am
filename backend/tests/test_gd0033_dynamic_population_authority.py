"""GD-0033 — DYNAMIC population-authority contract (extends the ONE canonical
guard in backend/lib/truth_population_guard.py).

Every human-visible master population from the LIVE production census
(memory/truth_program/LIVE_APPLICATION_MASTER_DATA_CENSUS.md) must derive its
total DYNAMICALLY from its canonical master collection at runtime — never a
hard-coded number, first-page length, capped-query count, or a shadow
population. This guard fails the release if any registered authority stops
deriving dynamically or a hard-coded total appears.

Also carries an OPTIONAL, env-gated PREVIEW propagation test proving
add -> N+1 -> soft-delete -> N against the live preview API (skipped in CI
unless PREVIEW_PROPAGATION_URL + creds are provided). The executable evidence
run lives at memory/truth_program/census_tools/preview_propagation_proof.py.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("/app/backend")))
from lib.truth_population_guard import (  # noqa: E402
    CANONICAL_POPULATION_AUTHORITIES,
    scan_authority_registry,
    served_backend_files,
    _find_fn_body,
)


def test_registry_covers_census_domains():
    domains = {a["domain"] for a in CANONICAL_POPULATION_AUTHORITIES}
    # human-visible master populations that MUST be dynamically enforced
    required = {
        "employees_active", "employees_master", "equipment_master",
        "equipment_status", "suppliers", "jobs", "users_stats",
        "transport_fleet", "eligible_drivers", "equipment_parts",
    }
    missing = required - domains
    assert not missing, f"census domains not registered for dynamic enforcement: {missing}"


def test_every_registered_authority_exists_in_source():
    by_path = {label: text for (label, text) in served_backend_files(Path("/app"))}
    problems = []
    for a in CANONICAL_POPULATION_AUTHORITIES:
        text = by_path.get(a["file"])
        if text is None:
            problems.append(f"{a['domain']}: file {a['file']} missing")
            continue
        if _find_fn_body(text, a["fn"]) is None:
            problems.append(f"{a['domain']}: fn {a['fn']} missing in {a['file']}")
    assert not problems, "registry drift (update registry deliberately WITH census artifact):\n" + "\n".join(problems)


def test_no_dynamic_authority_violations_in_served_code():
    violations = scan_authority_registry(served_backend_files(Path("/app")))
    assert not violations, "GD-0033 violations:\n" + "\n".join(sorted(v.message() for v in violations))


def test_guard_flags_hardcoded_total():
    bad = '''
async def list_equipment_master(category=None, search=None):
    docs = await db.equipment_master.find(q).to_list(5000)
    return {"items": docs, "count": len(docs), "total": 604}
'''
    msgs = [v.message() for v in scan_authority_registry([("backend/server.py", bad)])]
    assert any("hard-coded population total" in m for m in msgs), \
        "guard MUST flag a hard-coded literal population total"
    assert any("count_documents" in m for m in msgs), \
        "guard MUST flag loss of dynamic count_documents derivation"


def test_guard_flags_shadow_collection():
    bad = '''
async def list_equipment_master(category=None, search=None):
    docs = await db.some_other_shadow.find(q).to_list(5000)
    return {"items": docs, "count": len(docs), "total": await db.some_other_shadow.count_documents(q)}
'''
    msgs = [v.message() for v in scan_authority_registry([("backend/server.py", bad)])]
    assert any("canonical collection 'equipment_master'" in m for m in msgs), \
        "guard MUST flag a same-concept consumer reading a shadow collection"


# ── OPTIONAL live PREVIEW propagation proof (env-gated) ──────────────────────
_PURL = os.environ.get("PREVIEW_PROPAGATION_URL")
_PEMAIL = os.environ.get("MASCI_EMAIL")
_PPW = os.environ.get("MASCI_PASSWORD")


@pytest.mark.skipif(not (_PURL and _PEMAIL and _PPW),
                    reason="preview propagation env not provided (PREVIEW_PROPAGATION_URL/MASCI_EMAIL/MASCI_PASSWORD)")
def test_preview_equipment_population_propagates():
    import json
    import urllib.request
    import urllib.error
    base = _PURL.rstrip("/")

    def req(method, path, headers=None, body=None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Origin": base, "Referer": base + "/",
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}
        if data is not None:
            h["Content-Type"] = "application/json"
        if headers:
            h.update(headers)
        r = urllib.request.Request(base + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(r, timeout=45) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, {}

    st, login = req("POST", "/api/auth/multi-login", body={"email": _PEMAIL, "password": _PPW})
    assert st == 200 and login.get("ok"), "preview login failed"
    H = {"X-Admin-Token": (login.get("portal_tokens") or {}).get("admin"),
         "X-Directory-Token": login.get("session_token")}
    unit = "ZZ-GD0033-PROP"
    req("DELETE", f"/api/admin/equipment-master/{unit}", headers=H)

    def total():
        return req("GET", "/api/equipment-master", headers=H)[1].get("total")

    n0 = total()
    req("POST", "/api/admin/equipment-master", headers=H,
        body={"unit_number": unit, "make": "GD0033", "model": "PROP",
              "category": "Misc Equipment", "preop_equipment_type": "Other"})
    n1 = total()
    req("DELETE", f"/api/admin/equipment-master/{unit}", headers=H)
    n2 = total()
    assert n1 == n0 + 1, f"add did not propagate to canonical total ({n0}->{n1})"
    assert n2 == n0, f"soft-delete did not propagate back ({n1}->{n2})"
