#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path("/app")
REGISTRY = ROOT / "memory/WP17_ROUTE_GOVERNANCE_REGISTRY.csv"
FRONTEND_ROOT = ROOT / "frontend/src"
INDEX_GOVERNED_FILES = {
    "frontend/src/pages/transportation/TransportationApp.jsx",
}
REQUIRED_FIELDS = [
    "owner",
    "family",
    "intended_audience",
    "entry_path",
    "navigation_source",
    "role_requirements",
    "intentionally_hidden",
    "hidden_rationale",
    "canonical_relationship",
    "en_es_compliance",
    "responsive_compliance",
    "certification_evidence",
]


def parse_routes_from_source(path: Path, relative_path: str) -> list[tuple[str, int]]:
    routes: list[tuple[str, int]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if "<Route" not in line:
            idx += 1
            continue
        start_line = idx + 1
        tag_lines = [line]
        while ">" not in tag_lines[-1] and idx + 1 < len(lines):
            idx += 1
            tag_lines.append(lines[idx])
        tag = "\n".join(tag_lines)
        if relative_path in INDEX_GOVERNED_FILES and "index" in tag.split():
            routes.append(("(index)", start_line))
        marker = 'path="'
        if marker in tag:
            route = tag.split(marker, 1)[1].split('"', 1)[0]
            routes.append((route, start_line))
        idx += 1
    return routes


def discover_routes() -> list[dict[str, str]]:
    discovered: list[dict[str, str]] = []
    for path in sorted(FRONTEND_ROOT.rglob("*.jsx")):
        if "__tests__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "<Route" not in text:
            continue
        relative = path.relative_to(ROOT).as_posix()
        for route, line in parse_routes_from_source(path, relative):
            discovered.append({"source_file": relative, "declared_route": route, "source_line": str(line)})
    return discovered


def load_registry() -> list[dict[str, str]]:
    if not REGISTRY.exists():
        raise FileNotFoundError(f"Missing route governance registry: {REGISTRY}")
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_route_governance() -> list[str]:
    failures: list[str] = []
    registry_rows = load_registry()
    discovered_rows = discover_routes()
    registry_keys = {(row["source_file"], row["declared_route"]) for row in registry_rows}
    discovered_keys = {(row["source_file"], row["declared_route"]) for row in discovered_rows}

    missing_registry = sorted(discovered_keys - registry_keys)
    stale_registry = sorted(registry_keys - discovered_keys)
    if missing_registry:
        failures.append(
            "route_governance_missing_registry_rows: "
            + ", ".join(f"{source_file}:{route}" for source_file, route in missing_registry)
        )
    if stale_registry:
        failures.append(
            "route_governance_stale_registry_rows: "
            + ", ".join(f"{source_file}:{route}" for source_file, route in stale_registry)
        )

    seen = set()
    for row in registry_rows:
        key = (row["source_file"], row["declared_route"])
        if key in seen:
            failures.append(f"route_governance_duplicate_registry_row: {row['source_file']}:{row['declared_route']}")
            continue
        seen.add(key)
        for field in REQUIRED_FIELDS:
            if not row.get(field, "").strip():
                failures.append(f"route_governance_missing_field: {row['source_file']}:{row['declared_route']} missing {field}")
        if row.get("intentionally_hidden") not in {"YES", "NO"}:
            failures.append(
                f"route_governance_invalid_hidden_flag: {row['source_file']}:{row['declared_route']} "
                f"has '{row.get('intentionally_hidden', '')}'"
            )

    if len(discovered_rows) != len(registry_rows):
        failures.append(
            f"route_governance_count_mismatch: discovered {len(discovered_rows)} routes but registry has {len(registry_rows)} rows"
        )
    return failures


def main() -> int:
    failures = validate_route_governance()
    if failures:
        print("WP-17 route governance guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("WP-17 route governance guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())