"""iter311 · Drivers-on-Insurance backfill APPLY (operator-approved).

Rules locked by operator on iter311 dry-run review:
  - 67 exact-normalized matches → apply
  - 13 operator-approved name-variant matches (A + B) → apply by employee_id override
  - 6 unmatched-no-candidate → SKIP, report only, NO placeholder creation
  - Setters:
      approved_company_driver = True     (every imported row)
      cdl_holder              = True     (only when sheet CDL column == "CDL")
      driver_status           = "active" (only when CDL holder; otherwise leave unchanged)
  - NEVER overwrite: cdl_license_number, cdl_state, cdl_expiration,
    medical_card_expiration, endorsements, restrictions
  - Audit-log each update with source = "Drivers on Insurance and CDL Drivers.xlsx"
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from motor.motor_asyncio import AsyncIOMotorClient

SOURCE_LABEL = "Drivers on Insurance and CDL Drivers.xlsx"
SOURCE_OPERATOR = "iter311_backfill_operator_approved"

# Exact 86 spreadsheet rows
SPREADSHEET_ROWS = [
    ("ALAN DANFORD", None), ("ALEC PERKINS", None), ("ALEX STANSBURY", None),
    ("AMADO DELFIN", None), ("ANDREW HAYES", "CDL"), ("ANTHONY ROTELLA", None),
    ("BETH PUMA", None), ("BRAD CHESSMAN", None), ("BRETT HOFFMAN", "CDL"),
    ("BRIAN BULLARD", "CDL"), ("BROOKE POWELL", "CDL"), ("BRYAN WACZKOWSKI", None),
    ("CHRISTOPHER BENCKINI", "CDL"), ("CHRISTOPHER WRIGHT", None),
    ("CODY RAYBORN", "CDL"), ("COREY ANDERSON", "CDL"), ("DANA BOONE", "CDL"),
    ("DANIEL REYNOLDS", None), ("DANILE VALES", "CDL"), ("DANNY KRAMMER", "CDL"),
    ("DARREL AKINS", "CDL"), ("DAVID HOUT", None), ("DAVID JEWETT", None),
    ("DAVID LEMBKE", None), ("DAVID PUMA", None), ("DEDORIUS VARNES", "CDL"),
    ("DWAYNE THOMPSON", "CDL"), ("ENRIQUE VENTURA", None), ("ERIC REBELLO", None),
    ("FRANCIS WURST", "CDL"), ("GERALD RICE", "CDL"), ("GREGORY BATROSS", None),
    ("GUSTAVO BARROS", "CDL"), ("HARRY OLSON", "CDL"), ("JACKLYN BLOODWORTH", "CDL"),
    ("JAIME LICONA", None), ("JARED SARGENT", "CDL"), ("JAMEL VICTORY", None),
    ("JAMES BRISLIN", "CDL"), ("JAMES BUZARD", None), ("JAMES CASEY", "CDL"),
    ("JAMES OLORTEGUI", None), ("JAMIE TIRADO", None), ("JASON KROSLACK", "CDL"),
    ("JEFFREY MARVEL", None), ("JEFFRO MOLNAR", None), ("JERMIAH TINDLE", "CDL"),
    ("JERRY CORCHADO", None), ("JOHN BLANKENSHIP", None), ("JOHN THOENNES", "CDL"),
    ("JONATHAN BLAIR", "CDL"), ("JOSEPH ROTELLA", None), ("JOSEPH SZYMANEK", "CDL"),
    ("JOSHUA GILBERT", "CDL"), ("JULIAN JONES", "CDL"), ("KEITH CORBETT", "CDL"),
    ("KENNETH BURKHART", None), ("KENNETH HURD", "CDL"), ("KEVIN HILL", "CDL"),
    ("KYLE MCDANIELS", "CDL"), ("LEONARDO CHAVEZ", None), ("LOUIS HEYMANS", None),
    ("MANUEL TINOCO", None), ("MARGARET ROTELLA", None), ("MICHAEL BELL", None),
    ("MICHAEL GALKA", "CDL"), ("MICHAEL RIVERA", "CDL"), ("ORKUN BUYUKCULHA", None),
    ("RICHARD BENSON", "CDL"), ("RICHARD CALVERLEY", "CDL"),
    ("RICHARD SANCHEZ", None), ("RICHARD VIELE", "CDL"), ("ROBERT ADAMS", "CDL"),
    ("ROBERT CASTELLOW", "CDL"), ("RYAN HEIMS", None), ("SCOTT MCLANE", "CDL"),
    ("SHAN WILSON", "CDL"), ("SHERMAN MARTIN", None), ("TAMMY SCHNEIDER", None),
    ("TERRAL WILLIAMS", "CDL"), ("TERRANCE WILLIAMS", None),
    ("TYLER HARRISON", None), ("VINCENZA MASSARO", None), ("WESLEY BRUAW", None),
    ("WILLIAM FLETCHER", None), ("WILLIAM MUNDT", "CDL"),
]

# Operator-approved name-variant overrides (sheet name → DB name)
OPERATOR_APPROVED_VARIANTS = {
    "DANILE VALES":         "Daniel Vales",
    "JACKLYN BLOODWORTH":   "Jacqueline Bloodworth",
    "JAIME LICONA":         "Jaime Licona-montemayor",
    "JAMIE TIRADO":         "Jaime Tirado",
    "JEFFREY MARVEL":       "Jeffery W. Marvel",
    "JERMIAH TINDLE":       "Jeremiah L Tindle",
    "KYLE MCDANIELS":       "Kyle Mcdaniel",
    "TERRAL WILLIAMS":      "Terrall Williams",
    "VINCENZA MASSARO":     "Vinceenza Massaro",
    "WESLEY BRUAW":         "Wesley K Brauw",
    "ROBERT CASTELLOW":     "Robert Castellow Iii",
    "JOHN BLANKENSHIP":     "Johnny Blankenship",
    "DANIEL REYNOLDS":      "Danny C. Reynolds",
}

# Operator-approved skip list (no placeholder, report only)
OPERATOR_APPROVED_SKIP = {
    "ALAN DANFORD", "ANDREW HAYES", "DANA BOONE",
    "RYAN HEIMS", "CHRISTOPHER WRIGHT", "DAVID JEWETT",
}


def normalize(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip().upper())


def variants(name):
    norm = normalize(name)
    out = {norm}
    parts = norm.split()
    if len(parts) >= 2:
        out.add(f"{parts[0]} {parts[-1]}")
    return out


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    emps = await db.employees.find({}, {"_id": 0}).to_list(2000)

    # Build (name_form → list of employees) and (db_name_upper → employee) lookups
    by_form = {}
    by_full_upper = {}
    for e in emps:
        full = (e.get("name") or "").strip()
        if not full:
            continue
        by_full_upper[full.upper()] = e
        for f in variants(full):
            by_form.setdefault(f, []).append(e)

    plan_apply = []           # rows that will be updated
    skipped_unmatched = []    # operator-approved skip list (no candidate)
    skipped_other = []        # any row that didn't make it past pre-check

    for row_idx, (sheet_name, cdl_col) in enumerate(SPREADSHEET_ROWS, start=1):
        norm = normalize(sheet_name)

        # 1. Operator-approved skip list
        if norm in OPERATOR_APPROVED_SKIP:
            skipped_unmatched.append({
                "row": row_idx, "sheet_name": sheet_name, "cdl_column": cdl_col,
                "reason": "operator-approved skip · no DB candidate · requires HR resolution",
            })
            continue

        # 2. Operator-approved variant override
        if norm in OPERATOR_APPROVED_VARIANTS:
            db_name = OPERATOR_APPROVED_VARIANTS[norm]
            e = by_full_upper.get(db_name.upper())
            if not e:
                skipped_other.append({
                    "row": row_idx, "sheet_name": sheet_name, "cdl_column": cdl_col,
                    "reason": f"operator-approved variant '{db_name}' not found in DB",
                })
                continue
            plan_apply.append({"row": row_idx, "sheet_name": sheet_name, "cdl_col": cdl_col,
                               "e": e, "match_type": "operator_approved_variant"})
            continue

        # 3. Exact normalized match
        cands = by_form.get(norm, [])
        if not cands:
            parts = norm.split()
            if len(parts) >= 2:
                cands = by_form.get(f"{parts[0]} {parts[-1]}", [])
        if len(cands) == 1:
            plan_apply.append({"row": row_idx, "sheet_name": sheet_name, "cdl_col": cdl_col,
                               "e": cands[0], "match_type": "exact_normalized"})
        else:
            skipped_other.append({
                "row": row_idx, "sheet_name": sheet_name, "cdl_column": cdl_col,
                "reason": f"{len(cands)} candidates · unexpected fall-through",
            })

    # =================== APPLY ===================
    now = datetime.now(timezone.utc).isoformat()
    updated_full = []
    audit_docs = []
    for item in plan_apply:
        e = item["e"]
        eid = e.get("id")
        sheet_cdl = item["cdl_col"] == "CDL"
        before = {
            "approved_company_driver": e.get("approved_company_driver", False),
            "cdl_holder": e.get("cdl_holder", False),
            "driver_status": e.get("driver_status"),
        }
        # Compose update — preserve existing stronger data
        sets = {
            "approved_company_driver": True,
            "updated_at": now,
        }
        if sheet_cdl:
            sets["cdl_holder"] = True
            # Only set driver_status if not already a stronger active state
            if not e.get("driver_status"):
                sets["driver_status"] = "active"
        # If sheet says no CDL and DB already has cdl_holder=True → DO NOT overwrite (preserve stronger verified)
        # If sheet says no CDL and DB has cdl_holder=False/missing → leave as is (rule: blank CDL ≠ NOT a CDL)
        r = await db.employees.update_one({"id": eid}, {"$set": sets})
        # Re-fetch for the verification snapshot
        e2 = await db.employees.find_one({"id": eid}, {"_id": 0})
        after = {
            "approved_company_driver": e2.get("approved_company_driver", False),
            "cdl_holder": e2.get("cdl_holder", False),
            "driver_status": e2.get("driver_status"),
        }
        audit_docs.append({
            "id": f"iter311-{eid}-{int(datetime.now().timestamp())}",
            "ts": now,
            "actor": SOURCE_OPERATOR,
            "source": SOURCE_LABEL,
            "employee_id": eid,
            "employee_name": e2.get("name"),
            "sheet_row": item["row"],
            "sheet_name": item["sheet_name"],
            "sheet_cdl_column": item["cdl_col"],
            "match_type": item["match_type"],
            "before": before,
            "after": after,
            "changes_applied": list(sets.keys()),
            "operation": "driver_qualification_backfill",
        })
        updated_full.append({"row": item["row"], "sheet_name": item["sheet_name"],
                             "employee_id": eid, "employee_name": e2.get("name"),
                             "before": before, "after": after,
                             "match_type": item["match_type"]})

    if audit_docs:
        await db.driver_qualification_audit.insert_many(audit_docs)

    # =================== POST-IMPORT TOTALS ===================
    total_approved = await db.employees.count_documents({"approved_company_driver": True})
    total_cdl = await db.employees.count_documents({"cdl_holder": True})
    total_active_drivers = await db.employees.count_documents({"driver_status": "active"})

    report = {
        "source": SOURCE_LABEL,
        "applied_at": now,
        "totals_pre": "see dry-run baseline (matched=67, ambiguous=0, unmatched=19)",
        "spreadsheet_total_rows": len(SPREADSHEET_ROWS),
        "applied_count": len(updated_full),
        "skipped_unmatched_count": len(skipped_unmatched),
        "skipped_other_count": len(skipped_other),
        "audit_rows_written": len(audit_docs),
        "post_import_totals": {
            "approved_company_driver_TRUE": total_approved,
            "cdl_holder_TRUE": total_cdl,
            "driver_status_active": total_active_drivers,
        },
        "applied": updated_full,
        "skipped_unmatched": skipped_unmatched,
        "skipped_other": skipped_other,
    }
    out = Path("/tmp/iter311_apply_report.json")
    out.write_text(json.dumps(report, indent=2, default=str))
    print(f"Apply report → {out}")
    print(f"  spreadsheet rows:           {report['spreadsheet_total_rows']}")
    print(f"  applied:                    {report['applied_count']}")
    print(f"  skipped (no DB candidate):  {report['skipped_unmatched_count']}")
    print(f"  skipped (other):            {report['skipped_other_count']}")
    print(f"  audit rows written:         {report['audit_rows_written']}")
    print(f"  POST approved_company_driver=True: {total_approved}")
    print(f"  POST cdl_holder=True:              {total_cdl}")
    print(f"  POST driver_status=active:         {total_active_drivers}")


asyncio.run(main())
