#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.error
BASE="https://mascidocs.com"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
def _req(method,path,headers=None,body=None):
    data=json.dumps(body).encode() if body is not None else None
    h={"User-Agent":UA,"Origin":BASE,"Referer":BASE+"/"}
    if data is not None: h["Content-Type"]="application/json"
    if headers: h.update(headers)
    r=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=40) as resp: return resp.status,json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code,json.loads(e.read().decode())
        except: return e.code,{"_e":"nonjson"}
    except Exception as e: return 0,{"_e":str(e)}
st,login=_req("POST","/api/auth/multi-login",body={"email":os.environ["MASCI_EMAIL"],"password":os.environ["MASCI_PASSWORD"]})
DIR=login["session_token"]; ADMIN=(login.get("portal_tokens") or {}).get("admin")
H={"X-Admin-Token":ADMIN,"X-Directory-Token":DIR}

# Equipment categories (trucks/trailers/numbered/parts)
st,eqs=_req("GET","/api/admin/equipment-master/status",headers=H)
print("EQUIPMENT categories:", json.dumps(eqs.get("categories",{}),indent=0))

# Equipment-master full items -> derive truck/trailer/numbered by category & fields
st,eq=_req("GET","/api/equipment-master",headers=H)
items=eq.get("items",[])
cat={}; numbered=0; sample_fields=set()
for it in items:
    c=it.get("category","(none)"); cat[c]=cat.get(c,0)+1
    sample_fields.update(it.keys())
    if it.get("unit_number"): numbered+=1
print("EQUIP total items:",len(items),"| with unit_number:",numbered)
print("EQUIP category counts:",cat)
print("EQUIP fields:",sorted(sample_fields))

# Supplier vendor_type distribution
st,sup=_req("GET","/api/suppliers",headers=H)
vt={}
for it in sup.get("items",[]):
    v=it.get("vendor_type") or "(empty)"; vt[v]=vt.get(v,0)+1
print("SUPPLIER vendor_type:",vt)

# Fleet units detail
st,fu=_req("GET","/api/fleet/units",headers=H)
fitems=fu.get("items",[])
fcat={}; ffields=set()
for it in (fitems or []):
    ffields.update(it.keys())
    c=it.get("category") or it.get("type") or it.get("asset_type") or "(none)"; fcat[c]=fcat.get(c,0)+1
print("FLEET units:",len(fitems),"| breakdown:",fcat)
print("FLEET fields:",sorted(ffields))

# Transport fleet equipment detail (136) - what concept
st,tfe=_req("GET","/api/admin/transportation/fleet/equipment",headers=H)
te=tfe.get("items",[])
tcat={}; tfields=set()
for it in (te or []):
    tfields.update(it.keys())
    c=it.get("category") or it.get("equipment_type") or it.get("type") or "(none)"; tcat[c]=tcat.get(c,0)+1
print("TRANSPORT fleet equipment:",len(te),"| breakdown:",tcat)
print("TRANSPORT fleet equip fields:",sorted(tfields))
print("TRANSPORT fleet equip top keys of response:",[k for k in tfe.keys() if k!='items'])

# Projects list - check cap
st,pj=_req("GET","/api/admin/projects/list",headers=H)
print("PROJECTS keys:",[k for k in pj.keys() if k!='items'],"count:",pj.get("count"))
