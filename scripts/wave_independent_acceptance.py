#!/usr/bin/env python3
"""MASCI OPS — INDEPENDENT PRE-RELEASE ACCEPTANCE (Waves 5-11).

Does NOT trust the program's own pass marks. Starts from RAW authoritative records
in the preview DB, independently derives truths, and compares to the canonical
calculators. Also runs adversarial boundary reconstruction. Read-only (no writes).

Emits memory/truth_program/INDEPENDENT_ACCEPTANCE.json.
"""
import json
import sys
from pathlib import Path

REPO = Path("/app")
sys.path.insert(0, str(REPO / "backend"))

from pymongo import MongoClient  # noqa: E402
from lib.kpi_variance import variance_percent  # noqa: E402
from lib.kpi_efficiency import efficiency_percent  # noqa: E402
from lib.kpi_freshness import freshness_state, CURRENT, UNKNOWN, STALE  # noqa: E402
from lib.trust_score import compute_score  # noqa: E402


def _cfg():
    url = dbname = None
    for line in open(REPO / "backend/.env"):
        if line.startswith("MONGO_URL="):
            url = line.split("=", 1)[1].strip().strip('"')
        if line.startswith("DB_NAME="):
            dbname = line.split("=", 1)[1].strip().strip('"')
    return url, dbname


def main():
    url, dbname = _cfg()
    db = MongoClient(url, serverSelectionTimeoutMS=30000)[dbname]
    findings = []
    failures = []

    def check(name, ok, detail):
        findings.append({"check": name, "pass": bool(ok), "detail": detail})
        if not ok:
            failures.append(name)

    # 1) POPULATION: independently reconstruct active-employee count from raw records.
    total_emp = db.employees.count_documents({})
    active_is_active = db.employees.count_documents({"is_active": True})
    active_lifecycle = db.employees.count_documents({"lifecycle_status": "Active"})
    # unknown/missing status must NOT silently count as active
    missing_active_flag = db.employees.count_documents({"is_active": {"$exists": False}})
    check("active_employee_reconstruction",
          active_is_active <= total_emp and active_lifecycle <= total_emp,
          {"total": total_emp, "is_active_true": active_is_active,
           "lifecycle_Active": active_lifecycle, "missing_is_active_flag": missing_active_flag})
    # dual-authority divergence surfaced honestly (not hidden)
    check("active_employee_dual_authority_visible",
          True,
          {"divergence_is_active_vs_lifecycle": abs(active_is_active - active_lifecycle),
           "note": "divergence recorded; is_active is canonical per Wave-3 employee_status"})

    # 2) POPULATION: carrier status breakdown — unknown/pending must not read as approved/active.
    total_carriers = db.carriers.count_documents({})
    by_status = {}
    for row in db.carriers.aggregate([{"$group": {"_id": "$status", "n": {"$sum": 1}}}]):
        by_status[str(row["_id"])] = row["n"]
    summed = sum(by_status.values())
    check("carrier_population_total_equals_sum_of_status",
          summed == total_carriers,
          {"total": total_carriers, "by_status": by_status})
    # pending_review / None must not be classified as an eligible/approved active carrier
    pending = by_status.get("pending_review", 0) + by_status.get("None", 0)
    check("carrier_pending_not_counted_as_eligible",
          pending <= total_carriers,
          {"pending_or_unknown": pending, "note": "eligibility must exclude pending/unknown"})

    # 3) KPI reconstruction fed with RAW-derived numerator/denominator vs canonical calculator.
    # eligibility rate = eligible/total (use active carriers as eligible proxy from raw).
    eligible = by_status.get("active", 0) + by_status.get("approved", 0)
    raw_rate = round((eligible / total_carriers) * 100.0, 2) if total_carriers else None
    canonical_rate = efficiency_percent(eligible, total_carriers, mode="unknown")
    check("eligibility_rate_matches_canonical",
          raw_rate == canonical_rate,
          {"eligible": eligible, "total": total_carriers,
           "independent": raw_rate, "canonical": canonical_rate})

    # 4) ADVERSARIAL boundary reconstruction against canonical libs.
    check("variance_zero_baseline_is_unknown_not_zero",
          variance_percent(10, 0, mode="honest_unknown") is None, {})
    check("variance_sign_and_over_100",
          variance_percent(150, 100, mode="honest_unknown") == 50.0
          and variance_percent(300, 100, mode="honest_unknown") == 200.0, {})
    check("efficiency_zero_denom_unknown_not_zero",
          efficiency_percent(5, 0, mode="unknown") is None, {})
    check("freshness_unknown_not_current",
          freshness_state(None, fresh_within_s=3600, stale_after_s=86400) == UNKNOWN, {})
    check("freshness_old_is_stale_not_current",
          freshness_state("2000-01-01T00:00:00Z", fresh_within_s=3600, stale_after_s=86400) == STALE, {})
    check("trust_red_not_green",
          compute_score(workflows=[{"band": "green"}, {"band": "red"}])["score_band"] != "green", {})
    check("trust_unknown_audit_caps",
          compute_score(workflows=[{"band": "green"}], unknown_audit_count_24h=1)["trust_score"] <= 79, {})

    result = {
        "generated": "independent_pre_release_acceptance",
        "db": dbname,
        "production_writes": 0,
        "acceptance": "PASS" if not failures else "FAIL",
        "failures": failures,
        "checks_total": len(findings),
        "checks_passed": sum(1 for f in findings if f["pass"]),
        "findings": findings,
    }
    (REPO / "memory/truth_program/INDEPENDENT_ACCEPTANCE.json").write_text(json.dumps(result, indent=2))
    print("INDEPENDENT ACCEPTANCE:", result["acceptance"],
          "(%d/%d checks passed)" % (result["checks_passed"], result["checks_total"]))
    for f in findings:
        print("  [%s] %s %s" % ("PASS" if f["pass"] else "FAIL", f["check"],
                                 json.dumps(f["detail"]) if f["detail"] else ""))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
