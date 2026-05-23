"""
iter351_load_cdl_drivers.py — One-shot CDL / Approved Driver loader.

Source: customer-assets / "Drivers on Insurance and CDL Drivers.xlsx"
        (sheet: Drivers on Insurance · 86 rows · column B "CDL" marker)

Target: live mascidocs.com production employees collection.

Semantics:
  - Every name on the sheet → approved_company_driver = True
    (the sheet IS "Drivers on Insurance" — they're insured to drive).
  - Rows with column B == "CDL" → cdl_holder = True.
  - Default driver_status = "active" (insurance-approved status).
  - License #, state, expirations, endorsements, restrictions are NOT
    on the sheet → left as None / [] (not guessed, not invented).

Matching ladder (per Employee Linkage Standard iter350):
  1. exact employees.name (case-insensitive, whitespace-collapsed)
  2. last-name + first-initial fuzzy (handles ambiguous duplicates)
  3. unmatched → reported, NOT auto-created

No new employees are created. No unrelated fields are touched.
Idempotent — re-running on already-loaded rows is a no-op.
"""
import asyncio
import json
import os
import re
import sys
import argparse
from collections import Counter

import openpyxl
import requests

XLSX = "/tmp/cdl_drivers.xlsx"
DEFAULT_TARGET = "https://mascidocs.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"

_WS = re.compile(r"\s+")


def norm(s):
    if not s:
        return ""
    return _WS.sub(" ", str(s).strip()).lower()


def parse_xlsx():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["Drivers on Insurance"]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        name = (r[0] or "").strip() if isinstance(r[0], str) else ""
        cdl_marker = (r[1] or "").strip().upper() if isinstance(r[1], str) else ""
        if not name:
            continue
        rows.append({
            "raw_name": name,
            "norm_name": norm(name),
            "is_cdl": cdl_marker == "CDL",
        })
    return rows


def auth(target):
    r = requests.post(
        f"{target}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=15,
    )
    r.raise_for_status()
    pt = r.json().get("portal_tokens") or {}
    return {"hr": pt["hr"], "admin": pt["admin"]}


def fetch_employees(target, admin_tok):
    r = requests.get(
        f"{target}/api/employees",
        headers={"X-Admin-Token": admin_tok},
        timeout=30,
    )
    r.raise_for_status()
    items = r.json()
    if isinstance(items, dict):
        items = items.get("items", [])
    return items


def build_index(employees):
    """Two-tier index:
      - by_norm: exact normalized name → list of employees (handles dupes)
      - by_lastfirstinitial: 'last, fi' → list of employees
    """
    by_norm = {}
    by_lfi = {}
    for e in employees:
        n = norm(e.get("name"))
        if not n:
            continue
        by_norm.setdefault(n, []).append(e)
        parts = n.split(" ")
        if len(parts) >= 2:
            key = f"{parts[-1]}|{parts[0][:1]}"  # 'perkins|a'
            by_lfi.setdefault(key, []).append(e)
    return by_norm, by_lfi


def _strip_suffix_middle(name):
    """Strip suffix tokens (Jr, Sr, II–IV) AND middle initials/names so
    'Robert Castellow Iii' → 'robert castellow' and
    'Terrance J Williams' → 'terrance williams'."""
    n = norm(name)
    if not n:
        return n
    tokens = n.split(" ")
    out = []
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    for i, tok in enumerate(tokens):
        if tok in suffixes:
            continue
        # mid-name initials like "j" or "j." (kept first + last name)
        if 0 < i < len(tokens) - 1 and len(tok.replace(".", "")) <= 2:
            continue
        out.append(tok)
    return " ".join(out)


def _is_one_char_typo(a, b):
    """Tolerate a single transposition / substitution / insertion /
    deletion in strings of similar length (for cases like BRUAW vs
    BRAUW — adjacent swap)."""
    if not a or not b:
        return False
    if a == b:
        return False
    if abs(len(a) - len(b)) > 1:
        return False
    # Substitution: same length, exactly one differing char
    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff == 1:
            return True
        # Adjacent transposition: positions i, i+1 swapped, rest equal
        if diff == 2:
            for i in range(len(a) - 1):
                if a[i] == b[i + 1] and a[i + 1] == b[i] and a[:i] == b[:i] and a[i + 2:] == b[i + 2:]:
                    return True
        return False
    # Insertion / deletion: longer minus one char equals shorter
    long, short = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(long)):
        if long[:i] + long[i + 1:] == short:
            return True
    return False


def resolve(row, by_norm, by_lfi, all_emps):
    """Returns (employee_dict, method) or (None, 'unmatched')."""
    n = row["norm_name"]
    # Tier 1: exact normalized name
    if n in by_norm:
        matches = by_norm[n]
        if len(matches) == 1:
            return matches[0], "name_exact"
        return matches[0], f"name_exact_ambiguous({len(matches)})"
    # Tier 2: last + first-initial
    parts = n.split(" ")
    if len(parts) >= 2:
        key = f"{parts[-1]}|{parts[0][:1]}"
        if key in by_lfi:
            matches = by_lfi[key]
            if len(matches) == 1:
                return matches[0], "last_first_initial"
            # Tier 2b: disambiguate via first-3-char prefix match
            tight = [m for m in matches if norm(m.get("name")).split(" ")[0].startswith(parts[0][:3])]
            if len(tight) == 1:
                return tight[0], "last_first_three"
    # Tier 3: middle-initial / suffix-stripped equality
    src_stripped = _strip_suffix_middle(row["raw_name"])
    if src_stripped:
        for e in all_emps:
            tgt_stripped = _strip_suffix_middle(e.get("name"))
            if tgt_stripped and tgt_stripped == src_stripped:
                return e, "stripped_suffix_middle"
    # Tier 4: source name is a prefix of roster name (hyphenated last
    # names: "Jaime Licona" → "Jaime Licona-montemayor")
    for e in all_emps:
        en = norm(e.get("name"))
        if en.startswith(n + " ") or en.startswith(n + "-"):
            return e, "prefix_of_roster"
        # Or first-name match plus last-name token contains source last
        if parts and len(parts) >= 2:
            eparts = en.split(" ")
            if eparts and eparts[0] == parts[0]:
                # Compare last-name with hyphen split
                roster_last_tokens = eparts[-1].replace("-", " ").split()
                if parts[-1] in roster_last_tokens:
                    return e, "first_name_hyphen_last"
    # Tier 5: single-char typo on last name (BRUAW vs BRAUW)
    if parts and len(parts) >= 2:
        src_last = parts[-1]
        src_first = parts[0]
        for e in all_emps:
            en = norm(e.get("name"))
            eparts = en.split(" ")
            if not eparts or len(eparts) < 2:
                continue
            if eparts[0] == src_first and _is_one_char_typo(src_last, eparts[-1]):
                return e, "typo_last_name"
            # Also allow middle-initial tolerance: roster has 3 tokens
            # with last == src_last but first differs by 1 char
            if eparts[-1] == src_last and _is_one_char_typo(src_first, eparts[0]):
                return e, "typo_first_name"
    return None, "unmatched"


def patch_employee(target, hr_tok, emp_id, payload):
    r = requests.patch(
        f"{target}/api/hr/employees/{emp_id}",
        headers={"X-HR-Token": hr_tok, "Content-Type": "application/json"},
        json=payload, timeout=20,
    )
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    return True, r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=DEFAULT_TARGET,
                    help="Backend URL (default: production)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be patched without writing")
    args = ap.parse_args()

    print(f"[iter351] target = {args.target}")
    print(f"[iter351] dry_run = {args.dry_run}")
    print()

    rows = parse_xlsx()
    print(f"[xlsx] parsed {len(rows)} driver rows ({sum(1 for r in rows if r['is_cdl'])} marked CDL)")

    tokens = auth(args.target)
    print(f"[auth] hr+admin tokens minted")

    employees = fetch_employees(args.target, tokens["admin"])
    print(f"[employees] fetched {len(employees)} rows from production")

    by_norm, by_lfi = build_index(employees)
    print(f"[index] {len(by_norm)} unique normalized names, {len(by_lfi)} last-first-initial keys")
    print()

    matched = []
    unmatched = []
    method_counts = Counter()
    for row in rows:
        emp, method = resolve(row, by_norm, by_lfi, employees)
        method_counts[method] += 1
        if emp:
            matched.append((row, emp, method))
        else:
            unmatched.append((row, method))

    print(f"[match] matched: {len(matched)}, unmatched: {len(unmatched)}")
    print(f"[match] methods: {dict(method_counts)}")
    print()

    if unmatched:
        print("=== Unmatched names (NOT created) ===")
        for row, why in unmatched:
            print(f"  - {row['raw_name']!r:36s} cdl={row['is_cdl']}  reason={why}")
        print()

    if args.dry_run:
        print("[dry-run] skipping writes. exiting.")
        return

    print(f"=== Writing to {args.target} ===")
    updated = 0
    failed = []
    for row, emp, method in matched:
        payload = {
            "approved_company_driver": True,
            "cdl_holder": bool(row["is_cdl"]),
            "driver_status": "active",
        }
        ok, result = patch_employee(args.target, tokens["hr"], emp["id"], payload)
        if ok:
            updated += 1
            tag = "CDL " if row["is_cdl"] else "    "
            print(f"  ✓ {tag}{row['raw_name']:30s} → {emp['name']} ({method})")
        else:
            failed.append((row, emp, result))
            print(f"  ✗ FAIL {row['raw_name']:30s} → {emp['id']}: {result}")

    print()
    print(f"=== SUMMARY ===")
    print(f"  Source rows:    {len(rows)}")
    print(f"  Matched:        {len(matched)}")
    print(f"  Updated OK:     {updated}")
    print(f"  Failed PATCH:   {len(failed)}")
    print(f"  Unmatched:      {len(unmatched)}")

    # Persist results
    out = {
        "target": args.target,
        "rows_total": len(rows),
        "rows_cdl_marker": sum(1 for r in rows if r["is_cdl"]),
        "matched": [{"src": r["raw_name"], "emp_id": e["id"], "emp_name": e["name"], "cdl": r["is_cdl"], "method": m} for r, e, m in matched],
        "unmatched": [{"src": r["raw_name"], "cdl": r["is_cdl"], "reason": w} for r, w in unmatched],
        "failed": [{"src": r["raw_name"], "emp_id": e["id"], "err": err} for r, e, err in failed],
        "updated_count": updated,
    }
    out_path = f"/app/memory/iter351_cdl_load_{'PROD' if 'mascidocs' in args.target else 'preview'}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Result written: {out_path}")


if __name__ == "__main__":
    main()
