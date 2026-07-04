#!/usr/bin/env python3
"""Track 21.2 · Phase 2A forensic scan.

Reconciles every category in PLATFORM_MANIFEST.json against the live repo.
Emits an evidence report to /app/memory/track_21_2/PHASE2A_SCAN.json.

NO code is modified here. This is a discovery pass.
"""
import json, re, os, subprocess, sys, ast
from pathlib import Path
from collections import defaultdict, Counter

APP = Path("/app")
BACKEND = APP / "backend"
FRONTEND = APP / "frontend"
SRC = FRONTEND / "src"
MEM = APP / "memory"

out = {"generated_at": None, "findings": {}}

# ---------------------------------------------------------------- ENDPOINTS
endpoint_pat = re.compile(
    r'@(?:app|router|api_router|[a-zA-Z_]+_router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
    re.MULTILINE,
)
endpoints = []
for py in BACKEND.rglob("*.py"):
    if "__pycache__" in str(py) or "/tests/" in str(py):
        continue
    txt = py.read_text(errors="ignore")
    for m in endpoint_pat.finditer(txt):
        endpoints.append({"method": m.group(1).upper(), "path": m.group(2), "file": str(py.relative_to(APP))})
out["findings"]["endpoints"] = {
    "total": len(endpoints),
    "unique_paths": len({(e["method"], e["path"]) for e in endpoints}),
    "duplicates": [k for k, v in Counter((e["method"], e["path"]) for e in endpoints).items() if v > 1],
}

# ---------------------------------------------------------------- AUTH GATE COVERAGE
auth_deps = ["require_admin", "require_hr", "require_pm", "require_safety", "require_shop",
             "require_dispatch", "require_field", "require_admin_pm_or_hr_read",
             "require_admin_or_hr", "require_admin_or_pm", "require_multi_role",
             "require_admin_pm_hr", "require_admin_hr_pm", "get_current_admin",
             "get_current_user"]
auth_regex = re.compile(r"\b(" + "|".join(map(re.escape, auth_deps)) + r")\b")

unauth_endpoints = []
stale_hmac_users = []
STALE_HMAC = "require_admin_pm_or_hr_read"

# Parse each backend file: find endpoint decorators, and check if a Depends() with any auth gate
# is in the function signature. Use AST for precision.
def check_file(py):
    txt = py.read_text(errors="ignore")
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            deco_info = []
            for d in node.decorator_list:
                s = ast.unparse(d) if hasattr(ast, "unparse") else ""
                deco_info.append(s)
            deco_str = " ".join(deco_info)
            em = re.search(r"\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", deco_str)
            if not em:
                continue
            method, path = em.group(1).upper(), em.group(2)
            sig = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
            has_auth = bool(auth_regex.search(sig))
            has_stale = STALE_HMAC in sig
            rel = str(py.relative_to(APP))
            if not has_auth and not any(pub in path for pub in ["/health", "/branding/public", "/version", "/build-info", "/hazard-plans/public"]):
                unauth_endpoints.append({"method": method, "path": path, "file": rel, "func": node.name})
            if has_stale:
                stale_hmac_users.append({"method": method, "path": path, "file": rel, "func": node.name})

for py in BACKEND.rglob("*.py"):
    if "__pycache__" in str(py) or "/tests/" in str(py):
        continue
    check_file(py)

out["findings"]["unauth_endpoints"] = {
    "count": len(unauth_endpoints),
    "sample": unauth_endpoints[:25],
}
out["findings"]["stale_hmac_admin_helper_users"] = {
    "count": len(stale_hmac_users),
    "list": stale_hmac_users,
}

# ---------------------------------------------------------------- FRONTEND ROUTES
route_pat = re.compile(r"<Route\s+[^>]*path=[\"']([^\"']+)[\"']")
routes = set()
app_js = SRC / "App.js"
if app_js.exists():
    for m in route_pat.finditer(app_js.read_text(errors="ignore")):
        routes.add(m.group(1))
out["findings"]["frontend_routes"] = {"total": len(routes)}

# Check that every dynamic import target file exists
missing_imports = []
imp_pat = re.compile(r"lazy\(\s*\(\)\s*=>\s*import\(\s*[\"']([^\"']+)[\"']\s*\)")
raw = app_js.read_text(errors="ignore") if app_js.exists() else ""
for m in imp_pat.finditer(raw):
    target = m.group(1)
    # resolve relative to /app/frontend/src
    cand = (SRC / target.lstrip("./")).resolve()
    ok = False
    for ext in ("", ".jsx", ".js", ".tsx", ".ts", "/index.jsx", "/index.js"):
        p = Path(str(cand) + ext)
        if p.is_file():
            ok = True; break
    if not ok:
        missing_imports.append(target)
out["findings"]["frontend_missing_lazy_imports"] = {
    "count": len(missing_imports),
    "list": missing_imports[:25],
}

# ---------------------------------------------------------------- EMAIL PATHS
email_calls = []
email_fn_names = ["send_email", "_dispatch_auto_email", "send_mail", "dispatch_email",
                  "notify_email", "email_via_resend"]
email_pat = re.compile(r"\b(" + "|".join(email_fn_names) + r")\s*\(")
test_gate_pat = re.compile(r'(project_name|record\.get\("project_name"\))\s*[.\[]|TEST_|startswith\(["\']TEST_')

for py in BACKEND.rglob("*.py"):
    if "__pycache__" in str(py):
        continue
    txt = py.read_text(errors="ignore")
    for m in email_pat.finditer(txt):
        line_no = txt[:m.start()].count("\n") + 1
        # 40 lines of context up + 5 down
        lines = txt.split("\n")
        window_start = max(0, line_no - 40)
        context = "\n".join(lines[window_start:line_no + 5])
        gated = bool(re.search(r'TEST_|is_synthetic_test|synthetic', context))
        email_calls.append({
            "file": str(py.relative_to(APP)),
            "line": line_no,
            "fn": m.group(1),
            "synthetic_gate_within_40_lines": gated,
        })

out["findings"]["email_paths"] = {
    "count": len(email_calls),
    "ungated_within_40_lines": [c for c in email_calls if not c["synthetic_gate_within_40_lines"]],
    "sample_gated": [c for c in email_calls if c["synthetic_gate_within_40_lines"]][:5],
}

# ---------------------------------------------------------------- UPLOAD ENDPOINTS  
upload_endpoints = []
for py in BACKEND.rglob("*.py"):
    if "__pycache__" in str(py) or "/tests/" in str(py):
        continue
    txt = py.read_text(errors="ignore")
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            sig = ast.unparse(node.args) if hasattr(ast, "unparse") else ""
            if "UploadFile" in sig or "= File(" in sig:
                deco_info = " ".join(ast.unparse(d) if hasattr(ast, "unparse") else "" for d in node.decorator_list)
                em = re.search(r"\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", deco_info)
                if em:
                    upload_endpoints.append({
                        "method": em.group(1).upper(),
                        "path": em.group(2),
                        "file": str(py.relative_to(APP)),
                        "func": node.name,
                        "has_auth": bool(auth_regex.search(sig)),
                    })
out["findings"]["upload_endpoints"] = {
    "count": len(upload_endpoints),
    "without_auth": [u for u in upload_endpoints if not u["has_auth"]],
}

# ---------------------------------------------------------------- MONGO COLLECTIONS
collection_pat = re.compile(r'db\[?["\']?([a-z_][a-z0-9_]{2,60})["\']?\]?', re.MULTILINE)
db_attr_pat = re.compile(r'\bdb\.([a-z_][a-z0-9_]{2,60})\b')
collections = Counter()
collection_files = defaultdict(set)
for py in BACKEND.rglob("*.py"):
    if "__pycache__" in str(py):
        continue
    txt = py.read_text(errors="ignore")
    for m in collection_pat.finditer(txt):
        c = m.group(1)
        collections[c] += 1
        collection_files[c].add(str(py.relative_to(APP)))
    for m in db_attr_pat.finditer(txt):
        c = m.group(1)
        collections[c] += 1
        collection_files[c].add(str(py.relative_to(APP)))
# Filter out obvious noise (python method names)
noise = {"find", "find_one", "update", "update_one", "update_many", "insert", "insert_one",
         "insert_many", "delete", "delete_one", "delete_many", "count_documents", "aggregate",
         "create_index", "drop", "list_collection_names", "watch", "command", "database_name",
         "get_collection", "with_options", "count", "estimated_document_count", "find_one_and_update",
         "find_one_and_delete", "find_one_and_replace", "distinct", "replace_one", "bulk_write",
         "client", "name", "codec_options", "read_concern", "write_concern", "read_preference"}
collections = {k: v for k, v in collections.items() if k not in noise}
out["findings"]["collections"] = {
    "unique": len(collections),
    "top20_by_refs": Counter(collections).most_common(20),
    "singleton_referenced_once": [k for k, v in collections.items() if v == 1][:30],
}

# ---------------------------------------------------------------- FILES / TESTS
git_files = subprocess.run(["git", "-C", str(APP), "ls-files"], capture_output=True, text=True).stdout.splitlines()
out["findings"]["repo"] = {"tracked_files": len(git_files)}

test_files = [p for p in BACKEND.rglob("test_*.py") if "__pycache__" not in str(p)]
iter_tests = [p for p in test_files if re.search(r"iter\d+", p.name)]
out["findings"]["tests"] = {
    "total_files": len(test_files),
    "iter_prefixed_files": len(iter_tests),
    "iter_sample": [str(p.relative_to(APP)) for p in iter_tests[:15]],
}

# ---------------------------------------------------------------- FRONTEND STATS
jsx_files = list(SRC.rglob("*.jsx"))
js_files = list(SRC.rglob("*.js"))
out["findings"]["frontend"] = {
    "jsx": len(jsx_files),
    "js": len(js_files),
}

# ---------------------------------------------------------------- STALE ROOT MDs
stale_root_md = [p.name for p in APP.glob("*.md")]
out["findings"]["stale_root_docs"] = stale_root_md

# ---------------------------------------------------------------- BROKEN IMPORTS in tests
broken_test_imports = []
for tf in test_files:
    try:
        txt = tf.read_text(errors="ignore")
        if re.search(r"^from conftest import|from tests\.conftest import (ADMIN_TOKEN|URL)\b", txt, re.MULTILINE):
            broken_test_imports.append(str(tf.relative_to(APP)))
    except Exception:
        pass
out["findings"]["tests_with_broken_imports"] = {
    "count": len(broken_test_imports),
    "list": broken_test_imports,
}

# ---------------------------------------------------------------- DUMP
import datetime
out["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
outfile = MEM / "track_21_2" / "PHASE2A_SCAN.json"
outfile.parent.mkdir(parents=True, exist_ok=True)
outfile.write_text(json.dumps(out, indent=2, default=str))
print(f"Scan complete. {len(out['findings'])} categories emitted → {outfile}")
print(json.dumps({k: (v if isinstance(v, (int, list)) else {kk: (vv if isinstance(vv, (int, list, str, bool)) else "…") for kk, vv in v.items()}) for k, v in out["findings"].items()}, indent=2, default=str)[:4000])
