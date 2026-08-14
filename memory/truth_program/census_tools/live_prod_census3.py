#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
BASE="https://mascidocs.com"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
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
DIR=login["session_token"]; ADMIN=(login.get("portal_tokens") or {}).get("admin")
H={"X-Admin-Token":ADMIN,"X-Directory-Token":DIR}

# Jobs/Projects canonical master (jobs_master)
st,jm=_req("GET","/api/jobs-master",headers=H)
allj=jm if isinstance(jm,list) else jm.get("items",[])
statuses={}
for j in allj:
    s=j.get("status") or "(none)"; statuses[s]=statuses.get(s,0)+1
print("JOBS-MASTER (all):",len(allj),"| status dist:",statuses)
st,jl=_req("GET","/api/public/jobs-lookup",headers=H)
print("JOBS active (public-lookup): count=%s total=%s"%(jl.get("count"),jl.get("total")))
st,ji=_req("GET","/api/jobs",headers=H)
print("JOBS active (internal /api/jobs): items=%s"%len(ji.get("items",[])))

# Equipment parts
st,ep=_req("GET","/api/admin/equipment-parts/status",headers=H)
print("EQUIPMENT-PARTS status:",{k:ep.get(k) for k in ep if k!='items'})

# Driver reconciliation - raise limit, confirm stable
for lim in (200,1000):
    st,dr=_req("GET",f"/api/admin/transportation/eligible-hr-cdl-drivers?limit={lim}",headers=H)
    print(f"ELIGIBLE-CDL-DRIVERS limit={lim}: count={dr.get('count')}")
st,dri=_req("GET","/api/admin/transportation/eligible-hr-cdl-drivers?include_linked=true&limit=1000",headers=H)
print("ELIGIBLE-CDL-DRIVERS include_linked=true:",dri.get("count"))

# Transport fleet equipment reconciliation - raise limit
for lim in (500,2000):
    st,fe=_req("GET",f"/api/admin/transportation/fleet/equipment?limit={lim}",headers=H)
    print(f"TRANSPORT-FLEET-EQUIP limit={lim}: count={fe.get('count')} summary={fe.get('summary')}")

# Equipment category-sum reconciliation vs total
st,eqs=_req("GET","/api/admin/equipment-master/status",headers=H)
cats=eqs.get("categories",{})
print("EQUIP category-sum:",sum(cats.values()),"vs status count:",eqs.get("count"))
# truck/trailer derivation from categories
TRUCK_CATS={"Dump Trucks","Service Trucks","Tractor Trailer Trucks","Pickup Trucks","Water Trucks","Misc Trucks","Flatbed Trucks","Supervisor / Mgmt Trucks"}
trucks=sum(v for k,v in cats.items() if k in TRUCK_CATS)
trailers=cats.get("Trailers",0)
print("Derived TRUCKS:",trucks,"| TRAILERS:",trailers)
