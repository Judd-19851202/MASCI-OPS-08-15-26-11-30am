"""Downstream verification with proper portal-token header schemes."""
import json, requests, os

BASE = "https://backup-forensics.preview.emergentagent.com"
CRED = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}

r = requests.post(f"{BASE}/api/auth/multi-login", json=CRED, timeout=30).json()
pt = r["portal_tokens"]

ADMIN_H = {"X-Admin-Token": pt["admin"]}
PM_H = {"X-PM-Token": pt["pm"]}
SAFETY_H = {"X-Safety-Token": pt["safety"]}

results = json.load(open("/app/test_reports/track_26_03/results.json"))
downstream = {}

for k, v in results.items():
    rid = v.get("report_id")
    if not rid:
        continue
    d = {"report_id": rid, "report_number": (v.get("submit", {}).get("body") or {}).get("report_number")}

    # PDF via dr-v2
    pdf_ok = False
    for path in [f"/api/dr-v2/reports/{rid}/pdf", f"/api/daily-reports/{rid}/pdf"]:
        rr = requests.get(BASE + path, headers=ADMIN_H, timeout=60)
        if rr.status_code == 200 and rr.content[:4] == b"%PDF":
            d["pdf"] = {"path": path, "status": 200, "size": len(rr.content), "ok": True, "header_sample": rr.content[:8].decode(errors="ignore")}
            pdf_ok = True
            break
    if not pdf_ok:
        d["pdf"] = {"status": rr.status_code, "ok": False}

    # GET report
    rr = requests.get(f"{BASE}/api/daily-reports/{rid}", headers=ADMIN_H, timeout=30)
    j = rr.json() if rr.status_code == 200 else {}
    prod = j.get("production", []) if isinstance(j, dict) else []
    cons = j.get("constraints", []) if isinstance(j, dict) else []
    d["get_report"] = {
        "status": rr.status_code,
        "units": [p.get("unit") for p in prod],
        "custom_labels": [p.get("custom_unit_label") for p in prod],
        "constraint_types": [c.get("constraint_type") for c in cons],
    }

    # Admin list
    rr = requests.get(f"{BASE}/api/daily-reports", headers=ADMIN_H, timeout=30, params={"limit": 50})
    items = rr.json() if rr.status_code == 200 else []
    if isinstance(items, dict):
        items = items.get("items") or items.get("reports") or []
    found = any((it.get("id") == rid or it.get("_id") == rid) for it in items) if isinstance(items, list) else False
    d["admin_list"] = {"status": rr.status_code, "found": found, "count": len(items) if isinstance(items, list) else -1}

    # PM feed
    rr = requests.get(f"{BASE}/api/daily-reports", headers=PM_H, timeout=30, params={"limit": 50})
    items = rr.json() if rr.status_code == 200 else []
    if isinstance(items, dict):
        items = items.get("items") or items.get("reports") or []
    pm_found = any((it.get("id") == rid or it.get("_id") == rid) for it in items) if isinstance(items, list) else False
    d["pm_feed"] = {"status": rr.status_code, "found": pm_found, "count": len(items) if isinstance(items, list) else -1}

    # Safety feed
    rr = requests.get(f"{BASE}/api/safety/daily-reports", headers=SAFETY_H, timeout=30)
    d["safety_feed"] = {"status": rr.status_code}

    # Forensics
    rr = requests.get(f"{BASE}/api/admin/daily-report-delivery/forensics", headers=ADMIN_H, params={"report_id": rid}, timeout=30)
    d["forensics"] = {"status": rr.status_code, "body_len": len(rr.text), "body_head": rr.text[:300]}

    downstream[k] = d
    print(f"{k}: PDF={d['pdf'].get('size')}b PDF_ok={d['pdf'].get('ok')} get={d['get_report']['status']} units={d['get_report']['units']} ctypes={d['get_report']['constraint_types']} admin={d['admin_list']['status']}/{d['admin_list']['found']} pm={d['pm_feed']['status']}/{d['pm_feed']['found']} safety={d['safety_feed']['status']} forensics={d['forensics']['status']}")

json.dump(downstream, open("/app/test_reports/track_26_03/downstream.json", "w"), indent=2)
print("\nWrote /app/test_reports/track_26_03/downstream.json")
