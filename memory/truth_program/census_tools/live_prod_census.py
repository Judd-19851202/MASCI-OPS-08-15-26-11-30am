#!/usr/bin/env python3
"""MASCI OPS — LIVE PRODUCTION read-only master-data census.
READ-ONLY. Only POST used is the normal /api/auth/multi-login session establishment.
Tokens are held in memory and NEVER printed. No business-data writes.
"""
import json
import os
import sys
import urllib.request
import urllib.error

BASE = "https://mascidocs.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
EMAIL = os.environ["MASCI_EMAIL"]
PASSWORD = os.environ["MASCI_PASSWORD"]


def _req(method, path, headers=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    h = {"User-Agent": UA, "Origin": BASE, "Referer": BASE + "/"}
    if data is not None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"_error": "non-json"}
    except Exception as e:
        return 0, {"_error": str(e)}


# 1. Login (only permitted POST)
st, login = _req("POST", "/api/auth/multi-login", body={"email": EMAIL, "password": PASSWORD})
if st != 200 or not login.get("ok"):
    print("LOGIN FAILED", st, login.get("mfa_required"), login.get("detail"))
    sys.exit(1)
DIR = login["session_token"]
ADMIN = (login.get("portal_tokens") or {}).get("admin")
H = {"X-Admin-Token": ADMIN, "X-Directory-Token": DIR}
print("SESSION OK — portals:", [k for k, v in (login.get("portal_tokens") or {}).items() if v])
print("=" * 70)

# 2. Canonical read endpoints per domain
ENDPOINTS = [
    ("EMPLOYEES · master status", "/api/admin/employees/status"),
    ("EMPLOYEES · active roster", "/api/employees"),
    ("EMPLOYEES/EQUIP · master-lookup audit", "/api/master-lookup/audit"),
    ("EQUIPMENT · master list", "/api/equipment-master"),
    ("EQUIPMENT · master status board", "/api/admin/equipment-master/status"),
    ("SUPPLIERS · public list", "/api/suppliers"),
    ("SUPPLIERS · admin status", "/api/admin/suppliers/status"),
    ("FLEET · meta", "/api/fleet/_meta"),
    ("FLEET · units", "/api/fleet/units"),
    ("TRANSPORT · carriers", "/api/admin/transportation/carriers"),
    ("TRANSPORT · persons", "/api/admin/transportation/persons"),
    ("TRANSPORT · trucks", "/api/admin/transportation/trucks"),
    ("TRANSPORT · fleet equipment", "/api/admin/transportation/fleet/equipment"),
    ("TRANSPORT · eligible HR CDL drivers", "/api/admin/transportation/eligible-hr-cdl-drivers"),
    ("DISPATCH · eligible drivers", "/api/dispatch/transportation/eligible-drivers"),
    ("PROJECTS · admin list", "/api/admin/projects/list"),
    ("USERS · directory stats", "/api/admin/directory/k4/stats"),
    ("USERS · directory list", "/api/admin/directory/k4/users"),
]

for label, path in ENDPOINTS:
    st, d = _req("GET", path, headers=H)
    if not isinstance(d, dict):
        print(f"[{st}] {label:42s} {path}\n     -> non-dict: {str(d)[:120]}")
        continue
    # extract population-relevant keys
    keys = {}
    for k in ("count", "total", "active", "archived", "page_size",
              "employees_total", "equipment_master_total"):
        if k in d:
            keys[k] = d[k]
    items = d.get("items")
    if isinstance(items, list):
        keys["items_len"] = len(items)
    other = [k for k in d.keys() if k not in keys and k not in
             ("items", "grouped", "categories", "kpi_metadata", "filter",
              "contract_version", "public", "last_updated", "seed_file")]
    print(f"[{st}] {label:42s} {path}")
    print(f"      {keys}")
    if d.get("_error"):
        print(f"      ERROR: {d['_error']}")
    if other:
        # show scalar-ish extras only
        extras = {k: d[k] for k in other if isinstance(d[k], (int, float, str, bool))}
        if extras:
            print(f"      extras: {extras}")

print("=" * 70)
# Inspect supplier type distribution for vendor/subcontractor differentiation
st, sup = _req("GET", "/api/suppliers", headers=H)
if isinstance(sup, dict) and isinstance(sup.get("items"), list):
    types = {}
    fields = set()
    for it in sup["items"]:
        fields.update(it.keys())
        t = it.get("type") or it.get("category") or it.get("kind") or "(none)"
        types[t] = types.get(t, 0) + 1
    print("SUPPLIER type distribution:", types)
    print("SUPPLIER sample fields:", sorted(fields))
