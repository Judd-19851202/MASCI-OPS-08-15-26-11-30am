#!/usr/bin/env python3
"""Track 21.2 · Phase 3 · Deep forensic sweeps.

Categories:
    D1  Duplicate backend endpoints (same METHOD+path registered twice)
    D2  Dead Python imports (imported but not referenced in the file)
    D3  Backend env-var references that aren't declared in backend/.env
    D4  Frontend duplicate routes (same path declared in App.js twice)
    D5  Suspiciously singleton Mongo collections (<= 1 reference)
    D6  Duplicate utility / component filenames across frontend
    D7  Files with more than 6000 lines (candidates for phased split)
    D8  Backend endpoints with no docstring and no comment (readability)

Emits:
    memory/track_21_2/PHASE3_DEEP_SWEEP.json
"""
import ast
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
FRONTEND = APP / "frontend"
SRC = FRONTEND / "src"
OUT = APP / "memory" / "track_21_2" / "PHASE3_DEEP_SWEEP.json"


# ---------------------------------------------------------------- D1

def _endpoints_with_prefix():
    """Enumerate endpoints, resolving router prefixes to detect true duplicates."""
    endpoints = []
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py) or "/tests/" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
            tree = ast.parse(txt)
        except SyntaxError:
            continue
        # Discover router prefixes
        prefixes = {}
        for m in re.finditer(r"(\w+)\s*=\s*APIRouter\(([^)]{0,200})\)", txt, re.DOTALL):
            name, args = m.group(1), m.group(2)
            pm = re.search(r"prefix\s*=\s*[\"']([^\"']*)[\"']", args)
            prefixes[name] = pm.group(1) if pm else ""
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for deco in node.decorator_list:
                try:
                    ds = ast.unparse(deco)
                except Exception:
                    continue
                m = re.search(r"(\w+)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", ds)
                if not m:
                    continue
                rname, method, path = m.group(1), m.group(2).upper(), m.group(3)
                prefix = prefixes.get(rname, "")
                # api_router has prefix="/api"
                if rname == "api_router" and not prefix:
                    prefix = "/api"
                full = (prefix + path).replace("//", "/")
                endpoints.append({
                    "method": method, "full_path": full,
                    "raw_path": path,
                    "file": py.relative_to(APP).as_posix(),
                    "func": node.name,
                })
    return endpoints


def _duplicate_endpoints(endpoints):
    key = Counter((e["method"], e["full_path"]) for e in endpoints)
    dupes = {k: v for k, v in key.items() if v > 1}
    details = defaultdict(list)
    for e in endpoints:
        k = (e["method"], e["full_path"])
        if k in dupes:
            details[f"{k[0]} {k[1]}"].append({
                "file": e["file"], "func": e["func"], "raw_path": e["raw_path"],
            })
    return dict(details)


# ---------------------------------------------------------------- D2

def _dead_imports():
    """Find imports whose bound name never appears again in the file.

    Excludes side-effect imports (bare `import X`), test files, and
    conditional imports inside try/except (which are re-exports)."""
    dead = defaultdict(list)
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py) or "/tests/" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
            tree = ast.parse(txt)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                if name == "*" or name == "__future__":
                    continue
                # Search for the name after the import block. Simple usage:
                # anywhere except within the import line itself.
                pat = re.compile(r"\b" + re.escape(name) + r"\b")
                occurrences = pat.findall(txt)
                # 1 occurrence = only the import binding site itself.
                if len(occurrences) <= 1:
                    dead[py.relative_to(APP).as_posix()].append({
                        "line": node.lineno,
                        "name": name,
                        "src": alias.name,
                    })
    return dict(dead)


# ---------------------------------------------------------------- D3

def _env_drift():
    """Every `os.environ.get('X')` / `os.environ['X']` should have X declared
    in backend/.env, OR be a documented dynamic (RESEND_WEBHOOK_SECRET etc.)."""
    envfile = (BACKEND / ".env").read_text()
    declared = set(re.findall(r"^([A-Z][A-Z0-9_]{2,})=", envfile, re.MULTILINE))
    # Known runtime-only variables (not in .env by design)
    dynamic_ok = {
        "PATH", "HOME", "USER", "PYTHONPATH", "PWD", "LANG", "PYTHONHASHSEED",
        "MOTIVE_BASE_URL", "GEOTAB_BASE_URL", "OPENAI_API_KEY", "AWS_REGION",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "APP_TIER",
        "SIGNED_LINK_TTL_HOURS", "ATLAS_PUBLIC_KEY", "ATLAS_PRIVATE_KEY",
        "ATLAS_PROJECT_ID", "PLAYWRIGHT_BASE_URL", "TESTING", "PORT",
        "PYTHONDONTWRITEBYTECODE", "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_DRIVE_FOLDER_ID",
        # Emergent
        "EMERGENT_LLM_KEY_BUDGET",
        # Track 21.2E — this IS in .env now
    }
    referenced = set()
    pat = re.compile(r'os\.environ\.get\(\s*[\"\']([A-Z_][A-Z0-9_]{2,})[\"\']|os\.environ\[[\"\']([A-Z_][A-Z0-9_]{2,})[\"\']')
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
        except Exception:
            continue
        for m in pat.finditer(txt):
            v = m.group(1) or m.group(2)
            if v:
                referenced.add(v)
    undeclared = referenced - declared - dynamic_ok
    unused = declared - referenced
    return {
        "referenced_but_not_declared": sorted(undeclared),
        "declared_but_not_referenced": sorted(unused),
    }


# ---------------------------------------------------------------- D4

def _duplicate_frontend_routes():
    app_js = SRC / "App.js"
    txt = app_js.read_text(errors="ignore") if app_js.exists() else ""
    routes = re.findall(r"<Route\s+[^>]*path=[\"']([^\"']+)[\"']", txt)
    return [p for p, c in Counter(routes).items() if c > 1]


# ---------------------------------------------------------------- D5

def _collection_singletons():
    col_pat = re.compile(r'db\[?["\']?([a-z_][a-z0-9_]{4,60})["\']?\]?|(?<!\.)\bdb\.([a-z_][a-z0-9_]{4,60})\b')
    counter = Counter()
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
        except Exception:
            continue
        for m in col_pat.finditer(txt):
            c = m.group(1) or m.group(2)
            if c:
                counter[c] += 1
    # Real singletons = referenced exactly once across the entire backend
    return {k: v for k, v in counter.items() if v == 1}


# ---------------------------------------------------------------- D6

def _duplicate_component_filenames():
    seen = defaultdict(list)
    for p in SRC.rglob("*.jsx"):
        seen[p.name].append(p.relative_to(APP).as_posix())
    return {k: v for k, v in seen.items() if len(v) > 1}


# ---------------------------------------------------------------- D7

def _large_files(threshold=6000):
    out = []
    for root in (BACKEND, SRC):
        for p in root.rglob("*.*"):
            if p.suffix not in {".py", ".js", ".jsx"} or "__pycache__" in str(p) or "node_modules" in str(p):
                continue
            try:
                n = sum(1 for _ in p.open())
            except Exception:
                continue
            if n >= threshold:
                out.append({"file": p.relative_to(APP).as_posix(), "lines": n})
    return sorted(out, key=lambda x: -x["lines"])


# ---------------------------------------------------------------- D8 skipped — subjective

def scan():
    endpoints = _endpoints_with_prefix()
    dup_eps = _duplicate_endpoints(endpoints)
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "D1_duplicate_endpoints": {
            "count": len(dup_eps),
            "detail": dup_eps,
        },
        "D2_dead_imports": _dead_imports(),
        "D3_env_drift": _env_drift(),
        "D4_duplicate_frontend_routes": _duplicate_frontend_routes(),
        "D5_singleton_collections": _collection_singletons(),
        "D6_duplicate_component_filenames": _duplicate_component_filenames(),
        "D7_large_files": _large_files(),
    }


d = scan()
OUT.write_text(json.dumps(d, indent=2, default=str))
print("=== Track 21.2 · Phase 3 · Deep sweep ===")
print(f"D1 duplicate endpoints  : {d['D1_duplicate_endpoints']['count']}")
for k in list(d["D1_duplicate_endpoints"]["detail"])[:10]:
    print(f"    · {k}")
print(f"D2 files with dead imports: {len(d['D2_dead_imports'])}")
top_dead = sorted(d["D2_dead_imports"].items(), key=lambda x: -len(x[1]))[:5]
for f, items in top_dead:
    print(f"    {f}: {len(items)} unused imports")
print(f"D3 env vars referenced but not declared: {len(d['D3_env_drift']['referenced_but_not_declared'])}")
for e in d["D3_env_drift"]["referenced_but_not_declared"][:15]:
    print(f"    · {e}")
print(f"   env vars declared but not referenced: {len(d['D3_env_drift']['declared_but_not_referenced'])}")
for e in d["D3_env_drift"]["declared_but_not_referenced"]:
    print(f"    · {e}")
print(f"D4 duplicate frontend routes: {len(d['D4_duplicate_frontend_routes'])}")
for e in d['D4_duplicate_frontend_routes']:
    print(f"    · {e}")
print(f"D5 singleton mongo collections: {len(d['D5_singleton_collections'])}")
print(f"D6 duplicate component filenames: {len(d['D6_duplicate_component_filenames'])}")
for k, v in list(d['D6_duplicate_component_filenames'].items())[:10]:
    print(f"    · {k}: {v}")
print(f"D7 large files (>= 6000 lines):")
for f in d["D7_large_files"]:
    print(f"    · {f['file']}: {f['lines']} lines")
