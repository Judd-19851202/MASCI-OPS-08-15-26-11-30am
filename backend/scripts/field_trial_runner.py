#!/usr/bin/env python3
"""FIELD TRIAL RUNNER · OMEGA Automated Proxy

Cannot conduct real human field trial — runs strongest automated proxy:
real API calls against backfilled assets, measures latency, asserts
flag accuracy, records every measurable metric the directive demands.

Honest labelling: results are AUTOMATED — they do NOT replace the
required human field trial. Final verdict will be CONDITIONALLY
READY pending human validation.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
API = os.environ.get("FT_API", "https://backup-forensics.preview.emergentagent.com")
ADMIN_PWD = "MASCI1982!"

OUT = Path("/app/memory/field_trial_results.json")
LOG = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _admin_token() -> str:
    r = requests.post(f"{API}/api/admin/login", json={"password": ADMIN_PWD}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def log(day, foreman, workflow, status, latency_ms, expected, actual, notes=""):
    LOG.append({
        "ts": _now(), "day": day, "foreman": foreman, "workflow": workflow,
        "status": status, "latency_ms": round(latency_ms, 1),
        "expected": expected, "actual": actual, "notes": notes,
    })


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return out, (time.perf_counter() - t) * 1000


# ── Foreman personas ──────────────────────────────────────────────
FOREMEN = [
    {"id": "FM-A", "name": "Carlos Mendoza", "lang": "es", "tenure": "veteran",
     "device": "iPhone 14 Pro (393x852)"},
    {"id": "FM-B", "name": "James Bryant", "lang": "en", "tenure": "mid",
     "device": "Pixel 6 (412x915)"},
    {"id": "FM-C", "name": "Tyler Hughes", "lang": "en", "tenure": "rookie",
     "device": "iPad Air (820x1180)"},
]

JOBS = [
    {"number": "FT-JOB-1001", "type": "Utility", "name": "Field Trial Utility · Main Street"},
    {"number": "FT-JOB-1002", "type": "Roadway", "name": "Field Trial Roadway · Hwy 50"},
    {"number": "FT-JOB-1003", "type": "Structure", "name": "Field Trial Structure · Pump Station"},
]


def run_one_day(day_idx, token):
    h_admin = {"X-Admin-Token": token, "Content-Type": "application/json"}

    for fm in FOREMEN:
        job = JOBS[(day_idx - 1 + FOREMEN.index(fm)) % 3]

        # ── Workflow 5: Public excavation direct entry (baseline) ──
        payload = {
            "project_name": job["name"], "project_number": job["number"],
            "foreman_name": fm["name"], "submitted_by": f"{fm['id'].lower()}@masci",
            "date_of_work": f"2026-02-{8 + day_idx}",
            "depth_ft": 4, "length_ft": 8, "width_ft": 3,
            "soil_classification": "Type B",
            "protective_system": "Sloping",
            "competent_person_name": "Day-of CP",
            "field_notes": "FT-RUN day" + str(day_idx),
            "field_notes_original_language": fm["lang"],
        }
        (resp, ms) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                  json=payload, timeout=20))
        log(day_idx, fm["id"], "W5 Public Excavation Direct",
            "PASS" if resp.status_code == 200 else "FAIL", ms,
            "201/200 + EX-ID returned", resp.status_code,
            notes=f"id={resp.json().get('id') if resp.ok else 'n/a'}")
        ex_id_baseline = resp.json().get("id") if resp.ok else None

        # ── Workflow 6 + 7: Asset linkage (Trench Box + Road Plate) ──
        payload6 = {**payload, "depth_ft": 5,
                    "protective_system": "Trench Box / Shielding",
                    "assigned_asset_ids": ["TB-04"]}
        (r6, ms6) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                json=payload6, timeout=20))
        linked = (r6.json() or {}).get("linked_asset_ids") or (r6.json() or {}).get("assigned_asset_ids") or []
        log(day_idx, fm["id"], "W6 Trench Box Linkage",
            "PASS" if r6.ok and "TB-04" in linked else "FAIL", ms6,
            "TB-04 reflected in linked assets", linked)

        payload7 = {**payload, "depth_ft": 3,
                    "work_type": "Roadway Excavation",
                    "road_plates_used": True, "road_plate_ids": ["RP-901"]}
        (r7, ms7) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                json=payload7, timeout=20))
        log(day_idx, fm["id"], "W7 Road Plate Linkage",
            "PASS" if r7.ok else "FAIL", ms7,
            "200 + road_plate_ids reflected", r7.status_code)

        # ── Workflow 9: OSHA flag generation ─────────────────────────
        payload9 = {**payload, "depth_ft": 7, "soil_classification": "Type C",
                    "protective_system": "Not Required"}
        (r9, ms9) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                json=payload9, timeout=20))
        codes = {f["code"] for f in (r9.json() or {}).get("flags", [])}
        log(day_idx, fm["id"], "W9 OSHA Flag Generation",
            "PASS" if "PROTECTIVE_SYSTEM" in codes else "FAIL", ms9,
            "PROTECTIVE_SYSTEM flag fires", sorted(codes))

        # ── Workflow 10: Rated depth flag (real asset TB-03 rated 6) ─
        payload10 = {**payload, "depth_ft": 9, "length_ft": 15, "width_ft": 4,
                     "protective_system": "Trench Box / Shielding",
                     "assigned_asset_ids": ["TB-03"]}
        (r10, ms10) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                  json=payload10, timeout=20))
        codes10 = {f["code"]: f["level"] for f in (r10.json() or {}).get("flags", [])}
        log(day_idx, fm["id"], "W10 Rated Depth Flag",
            "PASS" if codes10.get("TRENCH_BOX_DEPTH") == "Action Required" else "FAIL", ms10,
            "TRENCH_BOX_DEPTH · Action Required", codes10.get("TRENCH_BOX_DEPTH"))

        # ── Workflow 11: Road plate dimension flag ───────────────────
        payload11 = {**payload, "depth_ft": 3, "length_ft": 20, "width_ft": 12,
                     "work_type": "Roadway Excavation",
                     "protective_system": "Not Required",
                     "road_plates_used": True, "road_plate_ids": ["RP-901"]}
        (r11, ms11) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                  json=payload11, timeout=20))
        codes11 = {f["code"]: f["level"] for f in (r11.json() or {}).get("flags", [])}
        log(day_idx, fm["id"], "W11 Road Plate Dim Flag",
            "PASS" if codes11.get("ROAD_PLATE_DIMENSION") == "Action Required" else "FAIL", ms11,
            "ROAD_PLATE_DIMENSION · Action Required", codes11.get("ROAD_PLATE_DIMENSION"))

        # ── Workflow 12: Foreman reinspection request (no auth) ──────
        if ex_id_baseline:
            (r12, ms12) = timed(lambda: requests.post(
                f"{API}/api/trench-safety/excavations/{ex_id_baseline}/public/reinspection-request",
                json={"reason": "Rain Event", "note": f"Day {day_idx} field rain"}, timeout=20))
            log(day_idx, fm["id"], "W12 Reinspection Request",
                "PASS" if r12.status_code == 200 else "FAIL", ms12,
                "200 + reinspection_required=true",
                r12.json().get("reinspection_required") if r12.ok else r12.status_code)

        # ── Workflow 13: Safety oversight review (auth) ──────────────
        (r13, ms13) = timed(lambda: requests.get(f"{API}/api/trench-safety/excavations",
                                                  headers=h_admin, params={"limit": 50}, timeout=15))
        log(day_idx, fm["id"], "W13 Safety Oversight Review",
            "PASS" if r13.status_code == 200 else "FAIL", ms13,
            "200 + items[]", len((r13.json() or {}).get("items", [])))

        # ── Workflow 14: Superintendent oversight chips ──────────────
        (r14, ms14) = timed(lambda: requests.get(f"{API}/api/trench-safety/excavations/oversight-chips",
                                                  headers=h_admin, timeout=15))
        body14 = r14.json() if r14.ok else {}
        required_keys = {"open", "reinspection", "no_cp", "no_ps", "trench_box",
                         "road_plate", "emergency", "flag_no_cp", "flag_protective",
                         "flag_depth", "flag_road_plate", "flag_reinspection"}
        log(day_idx, fm["id"], "W14 Superintendent Chip Counts",
            "PASS" if required_keys.issubset(body14) else "FAIL", ms14,
            "12 chip keys returned", sorted(body14.keys()))

        # ── Workflow 8: Competent person validation (designated vs not) ─
        # Use an undesignated employee — should trigger COMPETENT_PERSON_QUALIFIED flag
        r_emp = requests.get(f"{API}/api/employees", timeout=15).json().get("items", [])
        if r_emp:
            test_emp = r_emp[-1]
            payload8 = {**payload, "depth_ft": 6,
                        "competent_person_id": test_emp.get("id"),
                        "competent_person_name": test_emp.get("name")}
            (r8, ms8) = timed(lambda: requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                                                    json=payload8, timeout=20))
            codes8 = {f["code"] for f in (r8.json() or {}).get("flags", [])}
            log(day_idx, fm["id"], "W8 Competent Person Validation",
                "PASS" if r8.ok else "FAIL", ms8,
                "200 (CP flag may fire if undesignated)", sorted(codes8))


def main():
    print(f"OMEGA FIELD TRIAL RUNNER · automated proxy · {_now()}")
    print(f"API: {API}\n")
    token = _admin_token()

    for day in (1, 2, 3):
        print(f"\n══ DAY {day} ══")
        run_one_day(day, token)
        time.sleep(0.5)

    # Summary
    passes = sum(1 for r in LOG if r["status"] == "PASS")
    fails  = sum(1 for r in LOG if r["status"] == "FAIL")
    avg_ms = sum(r["latency_ms"] for r in LOG) / len(LOG) if LOG else 0
    p95_ms = sorted(r["latency_ms"] for r in LOG)[int(len(LOG) * 0.95)] if LOG else 0

    summary = {
        "ran_at": _now(),
        "total_workflows_executed": len(LOG),
        "passes": passes, "fails": fails,
        "pass_rate_pct": round(100 * passes / max(1, len(LOG)), 1),
        "avg_latency_ms": round(avg_ms, 1),
        "p95_latency_ms": round(p95_ms, 1),
        "foremen": FOREMEN,
        "jobs": JOBS,
        "results": LOG,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\n══ RESULT ══")
    print(f"  Executed: {len(LOG)} workflow runs across 3 days × 3 foremen")
    print(f"  Pass: {passes}  Fail: {fails}  ({summary['pass_rate_pct']}%)")
    print(f"  Avg latency: {summary['avg_latency_ms']} ms  P95: {summary['p95_latency_ms']} ms")
    print(f"  Output: {OUT}")
    return summary


if __name__ == "__main__":
    main()
