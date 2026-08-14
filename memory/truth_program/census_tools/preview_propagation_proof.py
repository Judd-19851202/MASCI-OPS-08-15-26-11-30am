#!/usr/bin/env python3
"""PREVIEW-ONLY dynamic propagation proof for the Equipment Master population.
Proves total is derived dynamically (add -> N+1, soft-delete -> N). Synthetic marker unit.
"""
import json, os, urllib.request, urllib.error
BASE=os.environ["PREVIEW_URL"].rstrip("/")
UA="census-propagation-preview"
def _req(method,path,headers=None,body=None):
    data=json.dumps(body).encode() if body is not None else None
    h={"User-Agent":UA,"Origin":BASE,"Referer":BASE+"/"}
    if data is not None: h["Content-Type"]="application/json"
    if headers: h.update(headers)
    r=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=45) as resp: return resp.status,json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code,json.loads(e.read().decode())
        except: return e.code,{"_e":"nonjson"}
    except Exception as e: return 0,{"_e":str(e)}
st,login=_req("POST","/api/auth/multi-login",body={"email":os.environ["MASCI_EMAIL"],"password":os.environ["MASCI_PASSWORD"]})
assert st==200 and login.get("ok"), ("login",st,login)
DIR=login["session_token"]; ADMIN=(login.get("portal_tokens") or {}).get("admin")
H={"X-Admin-Token":ADMIN,"X-Directory-Token":DIR}
UNIT="ZZ-CENSUS-PROP-01"

def eq_total():
    s,d=_req("GET","/api/equipment-master",headers=H); return d.get("total"),d.get("count")
def emp_active_total():
    s,d=_req("GET","/api/employees",headers=H); return d.get("total")

# cleanup any leftover first
_req("DELETE",f"/api/admin/equipment-master/{UNIT}",headers=H)

n0,c0=eq_total(); print("EQUIP baseline total:",n0)
st,cr=_req("POST","/api/admin/equipment-master",headers=H,body={"unit_number":UNIT,"make":"CENSUS","model":"PROP","category":"Misc Equipment","preop_equipment_type":"Other"})
print("  add status:",st,"| unit created:",cr.get("unit_number") or cr.get("id") or cr.get("ok") or cr.get("detail"))
n1,c1=eq_total(); print("EQUIP after add total:",n1,"| expected:",(n0+1) if n0 is not None else "?")
st,dl=_req("DELETE",f"/api/admin/equipment-master/{UNIT}",headers=H)
print("  soft-delete status:",st)
n2,c2=eq_total(); print("EQUIP after delete total:",n2,"| expected back to:",n0)
print("PROPAGATION add->N+1:", "PASS" if n1==(n0+1) else "FAIL",
      "| delete->N:", "PASS" if n2==n0 else "FAIL")
