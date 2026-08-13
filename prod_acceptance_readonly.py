#!/usr/bin/env python3
"""Read-only production acceptance probe. NO mutations. Evidence-only."""
import requests, json, sys

BASE = "https://mascidocs.com"
EMAIL = "jaymn.judd@mascigc.com"
PW = "Maddix123!"

s = requests.Session()
r = s.post(f"{BASE}/api/auth/multi-login", json={"email": EMAIL, "password": PW}, timeout=30)
d = r.json()
pt = d.get("portal_tokens", {})
adm = pt.get("admin")
st = d.get("session_token")
print("LOGIN ok=%s portals=%s" % (d.get("ok"), list(pt.keys())))

H = {"X-Admin-Token": adm, "X-Directory-Token": st}

# (label, method, path, portal_header)
GETS = [
    ("admin.executive-summary", "/api/admin/executive-summary"),
    ("admin.analytics.summary", "/api/admin/analytics/summary"),
    ("admin.system-health", "/api/admin/system-health"),
    ("admin.safety.overview", "/api/admin/safety/overview"),
    ("admin.employees", "/api/admin/employees"),
    ("admin.equipment-master", "/api/admin/equipment-master"),
    ("admin.governance.summary", "/api/admin/governance/summary"),
    ("admin.trust-spine", "/api/admin/trust-spine"),
    ("admin.operations-trust-center", "/api/admin/operations-trust-center"),
    ("admin.backups-scheduler-state", "/api/admin/backups-scheduler-state"),
    ("admin.backup-verification.state", "/api/admin/backup-verification/state"),
    ("admin.operational-attachments.storage-summary", "/api/admin/operational-attachments/storage-summary"),
    ("admin.photo-storage.health", "/api/admin/photo-storage/health"),
    ("admin.daily-report-health", "/api/admin/daily-report-health"),
    ("safety.company.safety-kpis", "/api/safety/company/safety-kpis"),
    ("safety.company.trench-safety-kpis", "/api/safety/company/trench-safety-kpis"),
    ("dispatch.command.summary", "/api/dispatch/command/summary"),
    ("dispatch.assignments.board", "/api/dispatch/assignments/board"),
    ("dispatch.transportation.readiness-summary", "/api/dispatch/transportation/readiness-summary"),
    ("hr.transportation-readiness", "/api/admin/hr/transportation-readiness"),
    ("daily-reports.list", "/api/daily-reports"),
    ("daily-reports.summary.draft", "/api/daily-reports/summary/draft"),
    ("document-expirations.summary", "/api/document-expirations/summary"),
    ("asset-care.summary", "/api/asset-care/summary"),
]

def summarize(js):
    if isinstance(js, list):
        return f"list[{len(js)}]" + (f" first_keys={list(js[0].keys())[:6]}" if js and isinstance(js[0], dict) else "")
    if isinstance(js, dict):
        keys = list(js.keys())
        # count list-valued fields
        counts = {k: len(v) for k, v in js.items() if isinstance(v, list)}
        cs = f" counts={counts}" if counts else ""
        return f"dict keys={keys[:10]}{cs}"
    return str(js)[:80]

results = {"ok": [], "empty": [], "fail": []}
for label, path in GETS:
    try:
        rr = s.get(f"{BASE}{path}", headers=H, timeout=40)
        sc = rr.status_code
        if sc == 200:
            try:
                js = rr.json()
                summ = summarize(js)
                empty = (isinstance(js, list) and len(js) == 0) or (isinstance(js, dict) and not js)
                print(f"[200] {label:52s} {summ}")
                (results["empty"] if empty else results["ok"]).append(label)
            except Exception:
                print(f"[200] {label:52s} non-json len={len(rr.content)}")
                results["ok"].append(label)
        else:
            print(f"[{sc}] {label:52s} {rr.text[:100]}")
            results["fail"].append((label, sc))
    except Exception as e:
        print(f"[ERR] {label:52s} {e}")
        results["fail"].append((label, "ERR"))

print("\n==== SUMMARY ====")
print("200-with-data:", len(results["ok"]))
print("200-empty:", results["empty"])
print("non-200/fail:", results["fail"])
