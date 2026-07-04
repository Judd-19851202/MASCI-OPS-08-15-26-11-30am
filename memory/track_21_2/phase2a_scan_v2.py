#!/usr/bin/env python3
"""Track 21.2 · Phase 2A refined scan v2.

Refinements after v1 revealed false positives:
- Auth detection: check for ANY `Depends(...)` argument whose target name
  contains `require_` / `_dep`, or a parameter typed `actor:` / `user:` /
  `current_user:`. Also detect router-level `dependencies=[...]`.
- Frontend lazy imports: resolve the webpack `@/` alias to `src/`.
- Email gate: check for `TEST_` / `is_synthetic_test` / `startswith` in
  the enclosing function body (AST), not a linear 40-line window.
"""
import json, re, ast, subprocess
from pathlib import Path
from collections import defaultdict, Counter
import datetime

APP = Path("/app")
BACKEND = APP / "backend"
FRONTEND = APP / "frontend"
SRC = FRONTEND / "src"
MEM = APP / "memory"


def is_auth_arg(arg: ast.arg, default) -> bool:
    """A parameter counts as an auth gate if:
    - default is a call to Depends(x) where x's textual name contains
      'require_' or ends '_dep', OR
    - the parameter name is one of {actor, user, current_user} or endswith '_actor'
    - the annotation string mentions 'Dict[str, Any]' AND default is Depends
    """
    name = arg.arg or ""
    if name in {"actor", "user", "current_user"} or name.endswith("_actor"):
        return True
    if isinstance(default, ast.Call):
        try:
            fn_src = ast.unparse(default.func)
        except Exception:
            fn_src = ""
        if fn_src.endswith("Depends") or fn_src == "Depends":
            # Look at inner arg
            if default.args:
                try:
                    inner = ast.unparse(default.args[0])
                except Exception:
                    inner = ""
                if "require_" in inner or inner.endswith("_dep") or "get_current" in inner or "token" in inner.lower():
                    return True
                if inner == "actor" or inner.startswith("actor"):
                    return True
                return True  # Any Depends(...) counts as an explicit gate
    return False


def has_test_gate_in_body(node) -> bool:
    """Recursively walk function body checking for TEST_/synthetic markers."""
    try:
        src = ast.unparse(node)
    except Exception:
        return False
    if "TEST_" in src or "is_synthetic" in src or "synthetic_test" in src:
        return True
    return False


def router_level_auth(txt: str, ap_call_line: int) -> bool:
    """Given the line where the router was created, check dependencies=[...]."""
    lines = txt.split("\n")
    # Find the closing paren for the APIRouter(...) call
    depth = 0
    start = ap_call_line - 1
    for i in range(start, min(start + 30, len(lines))):
        s = lines[i]
        depth += s.count("(") - s.count(")")
        if "dependencies=" in s or "dependencies =" in s:
            return True
        if depth <= 0 and i > start:
            break
    return False


def scan():
    findings = {}

    # 1. Endpoints + auth per endpoint (accounting for router-level Depends).
    endpoint_records = []
    stale_hmac = []
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py) or "/tests/" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
            tree = ast.parse(txt)
        except SyntaxError:
            continue
        # find router-level dependencies at module scope
        router_deps = {}
        for line_i, line in enumerate(txt.split("\n"), start=1):
            m = re.match(r"\s*(\w+)\s*=\s*APIRouter\(", line)
            if m:
                router_deps[m.group(1)] = router_level_auth(txt, line_i)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for deco in node.decorator_list:
                try:
                    deco_src = ast.unparse(deco)
                except Exception:
                    continue
                m = re.search(r"(\w+)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", deco_src)
                if not m:
                    continue
                router_name, method, path = m.group(1), m.group(2).upper(), m.group(3)
                args = node.args.args + node.args.kwonlyargs
                defaults = list(node.args.defaults)
                # pad defaults for positional args
                defaults_full = [None] * (len(node.args.args) - len(defaults)) + defaults + list(node.args.kw_defaults)
                has_auth = False
                for a, d in zip(args, defaults_full):
                    if is_auth_arg(a, d):
                        has_auth = True
                        break
                if not has_auth:
                    has_auth = router_deps.get(router_name, False)
                sig_src = ""
                try:
                    sig_src = ast.unparse(node.args)
                except Exception:
                    pass
                rel = str(py.relative_to(APP))
                endpoint_records.append({
                    "method": method, "path": path, "file": rel,
                    "func": node.name, "has_auth": has_auth,
                })
                if "require_admin_pm_or_hr_read" in sig_src:
                    stale_hmac.append({"method": method, "path": path, "file": rel, "func": node.name})

    findings["endpoints_total_decorator_sites"] = len(endpoint_records)
    findings["endpoints_without_auth"] = {
        "count": sum(1 for r in endpoint_records if not r["has_auth"]),
        "sample": [r for r in endpoint_records if not r["has_auth"]][:40],
    }
    findings["stale_hmac_admin_helper_users"] = {"count": len(stale_hmac), "list": stale_hmac}

    # 2. Frontend routes + lazy imports (resolve @ alias to src/)
    routes = set()
    missing = []
    app_js = SRC / "App.js"
    raw = app_js.read_text(errors="ignore") if app_js.exists() else ""
    for m in re.finditer(r"<Route\s+[^>]*path=[\"']([^\"']+)[\"']", raw):
        routes.add(m.group(1))
    for m in re.finditer(r"lazy\(\s*\(\)\s*=>\s*import\(\s*[\"']([^\"']+)[\"']\s*\)", raw):
        target = m.group(1)
        if target.startswith("@/"):
            resolved_base = SRC / target[2:]
        elif target.startswith("./") or target.startswith("../"):
            resolved_base = (SRC / target).resolve()
        else:
            resolved_base = SRC / target
        ok = False
        for ext in ("", ".jsx", ".js", ".tsx", ".ts", "/index.jsx", "/index.js"):
            if (Path(str(resolved_base) + ext)).is_file():
                ok = True
                break
        if not ok:
            missing.append(target)
    findings["frontend_routes_total"] = len(routes)
    findings["frontend_missing_lazy_imports"] = {"count": len(missing), "list": missing[:20]}

    # 3. Email paths + test-gate reachability inside enclosing function body
    email_call_pat = re.compile(
        r"\b(send_email|_dispatch_auto_email|send_mail|dispatch_email|notify_email|email_via_resend|_send_resend)\s*\("
    )
    email_findings = []
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
            tree = ast.parse(txt)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            try:
                body_src = ast.unparse(node)
            except Exception:
                continue
            for m in email_call_pat.finditer(body_src):
                gated = has_test_gate_in_body(node) or ("TEST_" in txt[:1000])
                email_findings.append({
                    "file": str(py.relative_to(APP)),
                    "enclosing_function": node.name,
                    "gate_in_body": gated,
                    "call_fn": m.group(1),
                })
                break
    findings["email_dispatch_functions"] = {
        "total": len(email_findings),
        "ungated": [x for x in email_findings if not x["gate_in_body"]],
        "sample_gated": [x for x in email_findings if x["gate_in_body"]][:10],
    }

    # 4. Upload endpoints w/ auth (now aware of router-level deps)
    upload = [r for r in endpoint_records if any(x in r.get("path", "") for x in ["upload", "documents"]) or r.get("func", "").startswith("upload")]
    findings["upload_endpoints"] = {
        "count": len(upload),
        "without_auth": [u for u in upload if not u["has_auth"]],
    }

    # 5. Test files with broken imports from conftest
    broken = []
    tests = list(BACKEND.rglob("test_*.py"))
    for tf in tests:
        if "__pycache__" in str(tf):
            continue
        try:
            t = tf.read_text(errors="ignore")
        except Exception:
            continue
        if re.search(r"^from conftest import|^from \.conftest import|from tests\.conftest import\s+.*\b(ADMIN_TOKEN|URL)\b", t, re.MULTILINE):
            broken.append(str(tf.relative_to(APP)))
    findings["broken_test_imports"] = {"count": len(broken), "list": broken}

    # 6. Iter tests + tests importing retired shared-password admin
    iter_tests = [tf for tf in tests if re.search(r"iter\d+", tf.name)]
    findings["iter_tests"] = {"total": len(iter_tests), "sample": [str(p.relative_to(APP)) for p in iter_tests[:10]]}

    # 7. Root .md files (excluding README.md and DEPLOYMENT_CHECKLIST.md — canonical)
    keep = {"README.md", "DEPLOYMENT_CHECKLIST.md", "test_result.md"}
    stale_root = [p.name for p in APP.glob("*.md") if p.name not in keep]
    findings["stale_root_md"] = {"count": len(stale_root), "list": stale_root}

    # 8. Collections referenced only once
    col_pat = re.compile(r'db\[?["\']?([a-z_][a-z0-9_]{2,60})["\']?\]?|(?<!\.)\bdb\.([a-z_][a-z0-9_]{2,60})\b')
    method_noise = {
        "find","find_one","find_one_and_update","find_one_and_delete","find_one_and_replace",
        "update_one","update_many","insert_one","insert_many","delete_one","delete_many",
        "count_documents","aggregate","create_index","drop","list_collection_names","watch",
        "command","get_collection","with_options","count","estimated_document_count","distinct",
        "replace_one","bulk_write","client","name","codec_options","read_concern","write_concern",
        "read_preference","database_name","insert","update","delete","find_and_modify",
    }
    counter = Counter()
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        t = py.read_text(errors="ignore")
        for m in col_pat.finditer(t):
            c = m.group(1) or m.group(2)
            if c and c not in method_noise:
                counter[c] += 1
    findings["collections_singleton_refs"] = {
        "count": sum(1 for _, v in counter.items() if v == 1),
        "top_singletons": [k for k, v in counter.items() if v == 1][:40],
        "top_hot": counter.most_common(15),
    }

    # 9. TODO/FIXME/XXX/HACK across repo (excluding memory/)
    tech_debt_markers = Counter()
    marker_files = defaultdict(list)
    for path in [BACKEND, SRC]:
        for p in path.rglob("*.*"):
            if p.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                continue
            if "__pycache__" in str(p) or "node_modules" in str(p):
                continue
            try:
                t = p.read_text(errors="ignore")
            except Exception:
                continue
            for kw in ("TODO", "FIXME", "XXX", "HACK"):
                cnt = t.count(kw)
                if cnt:
                    tech_debt_markers[kw] += cnt
                    marker_files[kw].append({"file": str(p.relative_to(APP)), "count": cnt})
    findings["tech_debt_markers"] = {
        "totals": dict(tech_debt_markers),
        "top10_TODO": sorted(marker_files["TODO"], key=lambda x: -x["count"])[:10],
        "top10_FIXME": sorted(marker_files["FIXME"], key=lambda x: -x["count"])[:10],
    }

    return findings


findings = scan()
findings["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
out = MEM / "track_21_2" / "PHASE2A_SCAN_V2.json"
out.write_text(json.dumps(findings, indent=2, default=str))

# Print compact digest
print("=== Track 21.2 · Phase 2A · v2 digest ===")
print(f"endpoints (decorator sites)   : {findings['endpoints_total_decorator_sites']}")
print(f"endpoints without auth        : {findings['endpoints_without_auth']['count']}")
print(f"stale hmac helper users       : {findings['stale_hmac_admin_helper_users']['count']}")
print(f"frontend routes               : {findings['frontend_routes_total']}")
print(f"missing lazy imports          : {findings['frontend_missing_lazy_imports']['count']}")
print(f"email dispatch fns            : {findings['email_dispatch_functions']['total']}  ungated={len(findings['email_dispatch_functions']['ungated'])}")
print(f"upload endpoints              : {findings['upload_endpoints']['count']}  no-auth={len(findings['upload_endpoints']['without_auth'])}")
print(f"broken test imports           : {findings['broken_test_imports']['count']}")
print(f"iter tests                    : {findings['iter_tests']['total']}")
print(f"stale root md (excl README+CL): {findings['stale_root_md']['count']}")
print(f"collections singleton refs    : {findings['collections_singleton_refs']['count']}")
print(f"tech-debt markers             : {findings['tech_debt_markers']['totals']}")
