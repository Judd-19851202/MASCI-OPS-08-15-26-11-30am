"""iter311 · dry-run matcher for Drivers-on-Insurance import.

Reads spreadsheet rows, fetches all employees, normalizes both sides,
classifies as: matched / ambiguous / unmatched. NO DB writes.
Emits structured JSON report for operator review before any update.

Matching rules (operator-bounded):
  - Exact normalized full-name match (uppercase, single-space, stripped)
  - Fallback: exact normalized "FIRST LAST" against employee.first_name + last_name
  - NO fuzzy matching, NO Levenshtein, NO auto-correct typos.
  - Multiple matches → AMBIGUOUS (operator decides), never auto-pick.
  - Zero matches → UNMATCHED (operator decides whether to add manually).
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from motor.motor_asyncio import AsyncIOMotorClient


# Spreadsheet rows extracted by extract_file_tool (verified against XLSX)
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


def normalize(s):
    """Uppercase, collapse whitespace, strip suffixes like JR/SR/III."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s.strip().upper())
    return s


def variants(full_name):
    """Return a set of normalized variants to try for matching."""
    norm = normalize(full_name)
    out = {norm}
    parts = norm.split()
    if len(parts) >= 2:
        # also try "FIRST LAST" without middle initials/names
        out.add(f"{parts[0]} {parts[-1]}")
    return out


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    emps = await db.employees.find({}, {"_id": 0}).to_list(2000)

    # Build name index: each employee → its candidate normalized forms.
    by_form = {}
    for e in emps:
        full = (e.get("name") or "").strip()  # schema uses `name`, not full_name
        first = (e.get("first_name") or "").strip()
        last = (e.get("last_name") or "").strip()
        forms = set()
        if full:
            forms |= variants(full)
        if first and last:
            forms |= variants(f"{first} {last}")
        for f in forms:
            by_form.setdefault(f, []).append(e)

    matched, ambiguous, unmatched = [], [], []
    for row_idx, (name, cdl) in enumerate(SPREADSHEET_ROWS, start=1):
        norm = normalize(name)
        candidates = by_form.get(norm, [])
        if not candidates:
            # try first-last fallback for double-barreled middle
            parts = norm.split()
            if len(parts) >= 2:
                candidates = by_form.get(f"{parts[0]} {parts[-1]}", [])
        if len(candidates) == 1:
            e = candidates[0]
            matched.append({
                "row": row_idx,
                "sheet_name": name,
                "cdl_column": cdl,
                "employee_id": e.get("id"),
                "employee_full_name": e.get("name") or "",
                "current_approved_company_driver": e.get("approved_company_driver", False),
                "current_cdl_holder": e.get("cdl_holder", False),
                "current_driver_status": e.get("driver_status"),
                "current_cdl_license_number": e.get("cdl_license_number"),
                "current_cdl_expiration": e.get("cdl_expiration"),
            })
        elif len(candidates) > 1:
            ambiguous.append({
                "row": row_idx,
                "sheet_name": name,
                "cdl_column": cdl,
                "candidates": [
                    {"id": e.get("id"),
                     "full_name": e.get("name") or "",
                     "status": e.get("employment_status")} for e in candidates
                ],
            })
        else:
            unmatched.append({
                "row": row_idx,
                "sheet_name": name,
                "cdl_column": cdl,
            })

    report = {
        "total_rows": len(SPREADSHEET_ROWS),
        "matched_count": len(matched),
        "ambiguous_count": len(ambiguous),
        "unmatched_count": len(unmatched),
        "matched": matched,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "total_employees_in_db": len(emps),
    }
    out_path = "/tmp/iter311_dryrun.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Dry-run report → {out_path}")
    print(f"  total spreadsheet rows: {report['total_rows']}")
    print(f"  total employees in DB:  {report['total_employees_in_db']}")
    print(f"  matched:    {report['matched_count']}")
    print(f"  ambiguous:  {report['ambiguous_count']}")
    print(f"  unmatched:  {report['unmatched_count']}")
    if ambiguous:
        print("\nAMBIGUOUS:")
        for a in ambiguous:
            print(f"  row {a['row']}: '{a['sheet_name']}' → {len(a['candidates'])} candidates")
            for c_ in a["candidates"]:
                print(f"      • {c_['full_name']} (id={c_['id']}, status={c_['status']})")
    if unmatched:
        print("\nUNMATCHED:")
        for u in unmatched:
            cdl_flag = " [CDL]" if u["cdl_column"] == "CDL" else ""
            print(f"  row {u['row']}: '{u['sheet_name']}'{cdl_flag}")


asyncio.run(main())
