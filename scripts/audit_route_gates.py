"""
audit_route_gates.py v2 — line-based parser
For each @router.METHOD("path") line, look ahead up to 15 lines and
extract any Depends(require_*) found. Fall back to router-level deps
or factory params.
"""
import re
import pathlib
from collections import Counter

ROUTES = pathlib.Path("/app/backend/routes")
DEC_RE = re.compile(r'^\s*@router\.(get|post|patch|put|delete)\(\s*"([^"]+)"(.*)$')
DEPENDS_RE = re.compile(r"Depends\(\s*(\w*require_\w+)\s*\)")

def find_factory_default(src):
    """Router-level dependencies passed at APIRouter construction."""
    m = re.search(r"APIRouter\(.*?dependencies\s*=\s*\[([^\]]+)\]", src, re.DOTALL)
    if m:
        g = DEPENDS_RE.search(m.group(1))
        if g:
            return g.group(1)
    return None

rows = []
for f in sorted(ROUTES.rglob("*.py")):
    if "__pycache__" in str(f):
        continue
    short = str(f).replace("/app/backend/routes/", "").replace(".py", "")
    lines = f.read_text().splitlines()
    factory_default = find_factory_default("\n".join(lines))

    for i, line in enumerate(lines):
        dm = DEC_RE.match(line)
        if not dm:
            continue
        method, path = dm.group(1), dm.group(2)
        # Collect this line + decorator-line trailing args until function def
        slice_ = "\n".join(lines[i:i + 25])  # decorator + small lookahead
        gate_m = DEPENDS_RE.search(slice_)
        gate = gate_m.group(1) if gate_m else (factory_default or "(unknown)")
        rows.append((short, method.upper(), path, gate))

# Stats
gate_counts = Counter(r[3] for r in rows)
print(f"Total routes parsed: {len(rows)}\n")
print("=== Gate distribution ===")
for g, n in gate_counts.most_common():
    print(f"  {n:4d}  {g}")

def cat(g):
    if g == "(unknown)":
        return "UNKNOWN"
    g = g.lower()
    if "admin_strict" in g: return "ADMIN_STRICT"
    if "hr_or_admin" in g: return "HR+ADMIN"
    if "safety_or_hr_or_admin" in g: return "SAFETY+HR+ADMIN"
    if "safety_or_admin" in g: return "SAFETY+ADMIN"
    if "safety_or_hr" in g: return "SAFETY+HR"
    if "shop_or_admin" in g: return "SHOP+ADMIN"
    if "dispatch_or_admin" in g: return "DISPATCH+ADMIN"
    if "admin" in g: return "ADMIN"
    if "hr" in g: return "HR"
    if "safety" in g: return "SAFETY"
    if "shop" in g: return "SHOP"
    if "dispatch" in g: return "DISPATCH"
    if "fl" in g or "leadership" in g: return "FIELD_LEADERSHIP"
    if "pm" in g: return "PM"
    if "qa" in g: return "QAQC"
    if "any_portal" in g: return "ANY_PORTAL"
    if "signed" in g or "public" in g: return "SIGNED_OR_PUBLIC"
    if "caller" in g: return "CALLER"
    if "write" in g: return "WRITE"
    if "token" in g: return "TOKEN_GENERIC"
    return "OTHER"

cat_counts = Counter(cat(r[3]) for r in rows)
print("\n=== Gate category distribution ===")
for c, n in cat_counts.most_common():
    print(f"  {n:4d}  {c}")

unknowns = [r for r in rows if r[3] == "(unknown)"]
print(f"\n=== {len(unknowns)} routes with no detectable gate (router-level dep or different pattern) ===")
ufiles = Counter(r[0] for r in unknowns)
for f, n in ufiles.most_common(20):
    print(f"  {n:3d}  {f}")

# Save
with open("/tmp/routes_audit_v2.csv", "w") as f:
    f.write("file,method,path,gate,category\n")
    for r in rows:
        line = ",".join(str(x).replace(",", "%2C") for x in r)
        f.write(f"{line},{cat(r[3])}\n")

# Per-file gate breakdown for the matrix
print("\n=== Per-file gate breakdown (top 10) ===")
by_file = {}
for r in rows:
    by_file.setdefault(r[0], []).append(r[3])
for f, gates in sorted(by_file.items(), key=lambda x: -len(x[1])):
    c = Counter(gates)
    line = " | ".join(f"{g}:{n}" for g, n in c.most_common(3))
    print(f"  {len(gates):3d}  {f:42s}  {line}")
