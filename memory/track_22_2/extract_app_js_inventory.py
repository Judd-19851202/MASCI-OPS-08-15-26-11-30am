#!/usr/bin/env python3
"""Track 22.2 · App.js route + import + provider inventory extractor.

Read-only. Zero code change. Produces canonical JSON artifacts for Phase B.
Regex-based line parser tuned to the current App.js structure. Same script
will run post-refactor against the new modular tree — output must be identical.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import defaultdict

APP_JS = Path("/app/frontend/src/App.js")
OUT_DIR = Path("/app/memory/track_22_2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Track 22.2 Phase B · post-extraction — the routes now live in this companion file.
APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")
sources = [APP_JS]
if APP_ROUTES.is_file():
    sources.append(APP_ROUTES)

src = "\n".join(p.read_text(encoding="utf-8") for p in sources)
lines = src.splitlines()

# ─────────────────────────────────────────────────────────────────
# 1. Imports (eager + lazy)
# ─────────────────────────────────────────────────────────────────
RE_EAGER = re.compile(r'^import\s+(?:{[^}]+}|[\w*]+)(?:\s*,\s*{[^}]+})?\s+from\s+["\']([^"\']+)["\'];?')
RE_EAGER_NAMED = re.compile(r'^import\s+(\w+)\s+from\s+["\']([^"\']+)["\']')
RE_EAGER_MULTI = re.compile(r'^import\s+\{\s*([^}]+)\s*\}\s+from\s+["\']([^"\']+)["\']')
RE_LAZY = re.compile(r'^const\s+(\w+)\s*=\s*React\.lazy\(\s*\(\)\s*=>\s*import\(\s*["\']([^"\']+)["\']\)(?:\.then\([^)]+\))?\s*\);?')

eager_imports = []  # {names:[], module}
lazy_imports = []   # {name, module}

for i, ln in enumerate(lines, 1):
    stripped = ln.strip()
    if stripped.startswith("//"):
        continue
    m = RE_LAZY.match(stripped)
    if m:
        lazy_imports.append({"line": i, "name": m.group(1), "module": m.group(2)})
        continue
    m = RE_EAGER_NAMED.match(stripped)
    if m:
        eager_imports.append({"line": i, "names": [m.group(1)], "module": m.group(2), "kind": "default"})
        continue
    m = RE_EAGER_MULTI.match(stripped)
    if m:
        names = [n.strip().split(" as ")[0].strip() for n in m.group(1).split(",")]
        eager_imports.append({"line": i, "names": names, "module": m.group(2), "kind": "named"})
        continue

# ─────────────────────────────────────────────────────────────────
# 2. Guard functions (const A = (el) => <RequireAdmin>{el}</RequireAdmin>;)
# ─────────────────────────────────────────────────────────────────
RE_GUARD = re.compile(r'^const\s+(\w+)\s*=\s*\(el\)\s*=>\s*<(Require\w+)>')
guards = []  # {alias, component}
for i, ln in enumerate(lines, 1):
    m = RE_GUARD.match(ln.strip())
    if m:
        guards.append({"line": i, "alias": m.group(1), "component": m.group(2)})

# ─────────────────────────────────────────────────────────────────
# 3. Routes — every `<Route path="..." element={...} />`
#    Multi-line supported. We capture: path, raw_element, guard_alias, target_component.
# ─────────────────────────────────────────────────────────────────
# Normalize: collapse Route JSX blocks into one line for regex.
# We'll walk line by line and, when we see `<Route`, capture until the closing `/>` or `</Route>`.
routes = []
i = 0
n = len(lines)
route_re = re.compile(r'<Route\s+path=["\']([^"\']+)["\']\s+element=\{([\s\S]+?)\}\s*/>')
# First pass: build a normalized single-line string of the JSX region only.
# It's simpler to just concat everything and regex globally.
joined = "\n".join(lines)
for match in route_re.finditer(joined):
    raw_path = match.group(1)
    raw_el = match.group(2).strip()
    # Locate line number of the match start
    line_no = joined.count("\n", 0, match.start()) + 1

    # Determine guard alias: leading token if single-letter guard function.
    guard_alias = None
    target_component = None
    lazy_kind = None
    # Pattern 1: `A(<Foo ... />)` or `SF(<Foo />)`
    m1 = re.match(r'^([A-Z]{1,4})\s*\(\s*<(\w+)', raw_el)
    if m1 and any(g["alias"] == m1.group(1) for g in guards):
        guard_alias = m1.group(1)
        target_component = m1.group(2)
    else:
        # Pattern 2: bare `<Foo .../>`, possibly `<Navigate to="..." replace />`
        m2 = re.match(r'^<(\w+)', raw_el)
        if m2:
            target_component = m2.group(1)

    # Classify lazy vs eager based on target_component appearing in lazy_imports vs eager_imports
    lazy_names = {li["name"] for li in lazy_imports}
    eager_names = {n for ei in eager_imports for n in ei["names"]}
    if target_component in lazy_names:
        lazy_kind = "lazy"
    elif target_component in eager_names:
        lazy_kind = "eager"
    else:
        lazy_kind = "inline_or_local"  # e.g. Navigate, RedirectWithId, InspectionLegacyRedirect (defined in App.js)

    routes.append({
        "line": line_no,
        "path": raw_path,
        "guard_alias": guard_alias,
        "guard_component": next((g["component"] for g in guards if g["alias"] == guard_alias), None),
        "target_component": target_component,
        "load": lazy_kind,
        "element_raw": raw_el[:200],
    })

# ─────────────────────────────────────────────────────────────────
# 4. Providers / Context refs in App() render tree
# ─────────────────────────────────────────────────────────────────
RE_PROVIDER = re.compile(r'<(\w+Provider)\b')
providers = []
seen_prov = set()
for i, ln in enumerate(lines, 1):
    for m in RE_PROVIDER.finditer(ln):
        p = m.group(1)
        if p not in seen_prov:
            seen_prov.add(p)
            providers.append({"line": i, "component": p})

# ─────────────────────────────────────────────────────────────────
# 5. Top-level chrome components (BrandingProvider, SplashOverlay, Toaster, banners...)
# ─────────────────────────────────────────────────────────────────
chrome_names = ["SplashOverlay", "Toaster", "QueueStatusPill", "OfflineBanner",
                "GlobalKeepalive", "BackendStatusBanner", "ClusterCapacityBanner",
                "EnvBanner", "BannerStrip", "BrowserRouter", "ScrollToTop",
                "EnforcePortalScope", "MultiPortalHydrator", "IdleTimeout",
                "SessionStatusOverlay"]
chrome_present = []
for name in chrome_names:
    if re.search(r'<' + re.escape(name) + r'\b', src):
        chrome_present.append(name)

# ─────────────────────────────────────────────────────────────────
# 6. Usage cross-reference: any imported name never referenced in JSX or code body?
# ─────────────────────────────────────────────────────────────────
all_imports = []
for ei in eager_imports:
    for n in ei["names"]:
        all_imports.append({"name": n, "module": ei["module"], "kind": "eager"})
for li in lazy_imports:
    all_imports.append({"name": li["name"], "module": li["module"], "kind": "lazy"})

# usage: any occurrence outside the import line itself
route_components = {r["target_component"] for r in routes if r["target_component"]}
usage_map = {}
for imp in all_imports:
    name = imp["name"]
    # crude count: how many times name appears in src minus once (the import line)
    hits = len(re.findall(r'\b' + re.escape(name) + r'\b', src))
    # subtract 1 for the import line itself (approximation — accurate enough for dead detection when hits=1)
    usage_map[name] = {
        "hits": hits,
        "in_routes": name in route_components,
        "module": imp["module"],
        "kind": imp["kind"],
    }

dead_candidates = [
    {"name": name, **info}
    for name, info in usage_map.items()
    if info["hits"] <= 1 and not info["in_routes"]
]

# ─────────────────────────────────────────────────────────────────
# 7. Path uniqueness check
# ─────────────────────────────────────────────────────────────────
path_counts = defaultdict(list)
for r in routes:
    path_counts[r["path"]].append(r["line"])
duplicate_paths = {p: v for p, v in path_counts.items() if len(v) > 1}

# ─────────────────────────────────────────────────────────────────
# Emit artifacts
# ─────────────────────────────────────────────────────────────────
inventory = {
    "source_file": str(APP_JS),
    "source_size_bytes": len(src),
    "source_lines": len(lines),
    "counts": {
        "eager_imports": len(eager_imports),
        "lazy_imports": len(lazy_imports),
        "guards": len(guards),
        "routes": len(routes),
        "providers": len(providers),
        "chrome_components": len(chrome_present),
        "dead_import_candidates": len(dead_candidates),
        "duplicate_paths": len(duplicate_paths),
        "unique_paths": len(set(r["path"] for r in routes)),
    },
    "guards": guards,
    "providers": providers,
    "chrome_components": chrome_present,
    "eager_imports": eager_imports,
    "lazy_imports": lazy_imports,
    "routes": routes,
    "dead_import_candidates": dead_candidates,
    "duplicate_paths": duplicate_paths,
}

(OUT_DIR / "APP_JS_INVENTORY.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")

# Print summary
print(f"source_lines={len(lines)}")
print(f"eager_imports={len(eager_imports)}")
print(f"lazy_imports={len(lazy_imports)}")
print(f"guards={len(guards)} — aliases: {sorted(g['alias'] for g in guards)}")
print(f"routes={len(routes)}  unique_paths={len(set(r['path'] for r in routes))}  duplicate_paths={len(duplicate_paths)}")
print(f"providers={len(providers)}")
print(f"chrome_components={len(chrome_present)}")
print(f"dead_import_candidates={len(dead_candidates)}")
print(f"guard_distribution:")
by_guard = defaultdict(int)
for r in routes:
    by_guard[r["guard_alias"] or "PUBLIC"] += 1
for k in sorted(by_guard, key=lambda x: -by_guard[x]):
    print(f"  {k}: {by_guard[k]}")
print(f"load_distribution:")
by_load = defaultdict(int)
for r in routes:
    by_load[r["load"] or "unknown"] += 1
for k in by_load:
    print(f"  {k}: {by_load[k]}")

if duplicate_paths:
    print("\nDUPLICATE PATHS:")
    for p, ls in duplicate_paths.items():
        print(f"  {p}: lines={ls}")
