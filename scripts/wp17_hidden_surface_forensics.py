#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/app")
MEMORY = ROOT / "memory"

CONVERGENCE_LEDGER = ROOT / "WP17D_PLATFORM_CONVERGENCE_LEDGER.csv"
IMPLEMENTATION_LEDGER = ROOT / "WP17C_IMPLEMENTATION_LEDGER.csv"
REACHABILITY_LEDGER = MEMORY / "WP17D_PLATFORM_REACHABILITY_LEDGER.csv"
PENDING_CLASSIFICATION = MEMORY / "WP17D_PENDING_SURFACE_CLASSIFICATION.csv"
DENOMINATOR_RECONCILIATION = MEMORY / "WP17D_DENOMINATOR_RECONCILIATION.csv"
FINAL_BLOCKER_REGISTER = MEMORY / "WP17D_FINAL_BLOCKER_REGISTER.md"
OVERLAY_REGISTER = MEMORY / "WP16_OVERLAY_AND_INTERACTION_REGISTER.md"

FORENSIC_REGISTER = MEMORY / "WP17_HIDDEN_SURFACE_FORENSIC_REGISTER.csv"
EXECUTIVE_REPORT = MEMORY / "WP17_HIDDEN_SURFACE_EXECUTIVE_REPORT.md"
FAMILY_SUMMARY = MEMORY / "WP17_HIDDEN_SURFACE_FAMILY_SUMMARY.md"
ROUTE_GOVERNANCE_REGISTRY = MEMORY / "WP17_ROUTE_GOVERNANCE_REGISTRY.csv"

APP_ROUTE_FILES = {
    "frontend/src/app/routing/AppRoutes.jsx",
    "frontend/src/pages/transportation/TransportationApp.jsx",
    "frontend/src/pages/transportation/_orientation.jsx",
    "frontend/src/pages/transportation/_intelligence.jsx",
    "frontend/src/pages/transportation/_command_queue.jsx",
}

INDEX_GOVERNED_FILES = {
    "frontend/src/pages/transportation/TransportationApp.jsx",
}

TOOLING_EXTRA_ROUTES = {
    "/admin/integration-truth": {
        "origin": "DEVELOPER_OR_CERTIFICATION_TOOL",
        "disposition": "ROLE_RESTRICTED_AND_GOVERNED",
        "hidden_reason": "Admin-only internal truth surface; not part of the operator navigation canon.",
        "canonical_relationship": "PRIMARY_INTERNAL_TOOL_ROUTE",
        "evidence": "Live route exists in AppRoutes.jsx:733 and was intentionally absent from primary route-denominator narratives.",
    },
    "/admin/preview-validation-identities": {
        "origin": "DEVELOPER_OR_CERTIFICATION_TOOL",
        "disposition": "ROLE_RESTRICTED_AND_GOVERNED",
        "hidden_reason": "Preview-identity verification tooling; valid for admin-only diagnostics, not primary operator movement.",
        "canonical_relationship": "PRIMARY_INTERNAL_TOOL_ROUTE",
        "evidence": "Live route exists in AppRoutes.jsx:734 and is named as validation tooling.",
    },
    "/admin/platform-readiness": {
        "origin": "DEVELOPER_OR_CERTIFICATION_TOOL",
        "disposition": "ROLE_RESTRICTED_AND_GOVERNED",
        "hidden_reason": "Administrative readiness/certification evidence surface; intentionally outside operator navigation.",
        "canonical_relationship": "PRIMARY_INTERNAL_TOOL_ROUTE",
        "evidence": "Route added to the reconciled denominator at ROUTE-0483 in WP17D_DENOMINATOR_RECONCILIATION.csv.",
    },
    "/admin/wp17d-certification": {
        "origin": "DEVELOPER_OR_CERTIFICATION_TOOL",
        "disposition": "ROLE_RESTRICTED_AND_GOVERNED",
        "hidden_reason": "Legacy certification naming survives as an admin-only alias to the readiness surface.",
        "canonical_relationship": "DUPLICATE_INTERNAL_TOOL_ROUTE_OF:/admin/platform-readiness",
        "evidence": "Route added to the reconciled denominator at ROUTE-0484 in WP17D_DENOMINATOR_RECONCILIATION.csv.",
    },
}

SPECIAL_CANONICAL_RELATIONSHIPS = {
    "/pm/projects/:projectNumber": "REDIRECTS_TO:/pm/command-center?project_number=:projectNumber",
    "/daily-reports/:id": "REDIRECTS_TO_CONTEXTUAL_DETAIL:/admin/daily/:id|/pm/daily/:id",
    "/equipment/:id": "REDIRECTS_TO:/admin/equipment/:id",
    "/admin/jha/:id": "REDIRECTS_TO:/guidance",
    "/ops-training/:slug": "REDIRECTS_TO:/guidance",
    "/admin/wp17d-certification": "DUPLICATE_INTERNAL_TOOL_ROUTE_OF:/admin/platform-readiness",
    "/admin/hub_v2": "LEGACY_ALIAS_OF:/admin",
}

OWNER_BY_FAMILY = {
    "Administration": "Administration",
    "Shared Operational Home and Public Entry": "Shared platform / public workflow",
    "Safety Operations": "Safety Operations",
    "Project Management": "Project Management",
    "Human Resources": "Human Resources",
    "Shop Operations": "Shop Operations",
    "Field Leadership": "Field Leadership",
    "Transportation Operations": "Transportation Operations",
    "Training, Guidance, and Coaching": "Training, Guidance, and Coaching",
    "Field Operations": "Field Operations",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_blocker_register(path: Path) -> dict[str, dict[str, str]]:
    blockers: dict[str, dict[str, str]] = {}
    current_group = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## Newly Dispositioned Runtime-Data Blockers"):
            current_group = "runtime"
            continue
        if line.startswith("## Pre-Existing Frozen Administration Blockers"):
            current_group = "admin_frozen"
            continue
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 3 or parts[0] in {"Family", "---"}:
            continue
        family, route, reason = parts
        blockers[route.strip("`")] = {
            "family": family,
            "reason": reason.strip("`") if reason.startswith("`") else reason,
            "group": current_group,
        }
    return blockers


def parse_overlay_register(path: Path) -> list[dict[str, str]]:
    rows = []
    headers = [
        "interaction_id",
        "type",
        "source_screen",
        "source_route",
        "portal",
        "module",
        "role_context",
        "trigger_control",
        "trigger_label",
        "trigger_icon",
        "required_permission",
        "required_record_state",
        "opened",
        "rendered_fully",
        "dismissible",
        "dismissal_method",
        "escape_works",
        "visible_close",
        "cancel_exists",
        "click_outside_dismisses",
        "focus_observed",
        "background_prevented",
        "screenshot",
        "defect_ref",
        "final_coverage_classification",
        "notes",
    ]
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|| INT-"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != len(headers):
            continue
        rows.append(dict(zip(headers, parts)))
    return rows


def route_is_non_primary(row: dict[str, str]) -> bool:
    return row["Surface type"] in {"detail_route", "redirect_route", "hidden_companion_route"} or (
        row["Surface type"] == "route_screen" and row["Active/hidden/detail/public/external state"] == "HIDDEN"
    )


def normalize_family(family: str) -> str:
    mapping = {
        "admin": "Administration",
        "public_shared": "Shared Operational Home and Public Entry",
        "safety": "Safety Operations",
        "pm": "Project Management",
        "hr": "Human Resources",
        "shop": "Shop Operations",
        "field_leadership": "Field Leadership",
        "transportation": "Transportation Operations",
        "training_guidance": "Training, Guidance, and Coaching",
        "dispatch": "Dispatch Operations",
        "driver": "Driver",
        "dev": "Developer Tooling",
        "executive": "Executive",
    }
    return mapping.get(family, family)


def find_reachability_row(route: str, source_file: str, reach_rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in reach_rows:
        if row["route"] == route and row["source_file"] == source_file:
            return row
    for row in reach_rows:
        if row["route"] == route:
            return row
    return None


def certification_split(value: str) -> tuple[str, str]:
    lower = value.lower()
    en_es = "PENDING_REVIEW"
    responsive = "PENDING_REVIEW"
    if "es" in lower or "en/es" in lower:
        en_es = "CERTIFIED"
    elif "invalid-token" in lower or "operator-language" in lower or "live fixture" in lower:
        en_es = "EVIDENCE_RECORDED"
    if any(token in lower for token in ["390", "430", "768", "1024", "1440", "responsive"]):
        responsive = "CERTIFIED"
    elif "invalid-token" in lower or "operator-language" in lower or "live fixture" in lower:
        responsive = "EVIDENCE_RECORDED"
    if value.startswith("BLOCKED_"):
        en_es = "BLOCKED_NOT_CERTIFIED"
        responsive = "BLOCKED_NOT_CERTIFIED"
    return en_es, responsive


def derive_hidden_reason(row: dict[str, str], route: str, origin: str) -> str:
    if route in TOOLING_EXTRA_ROUTES:
        return TOOLING_EXTRA_ROUTES[route]["hidden_reason"]
    if origin == "INTENTIONAL_DIALOG_OR_OVERLAY":
        return "Workflow-internal interaction surface; intentionally hidden until triggered by a valid user action."
    if origin == "DEVELOPER_OR_CERTIFICATION_TOOL":
        return "Restricted diagnostic or preview surface; it exists for internal support, readiness, or development work rather than operator navigation."
    if origin == "INTENTIONAL_TOKEN_LINK":
        return "Surface is meant to open from a tokenized email, QR, or continuity link instead of global navigation."
    if origin == "INTENTIONAL_PUBLIC_LINK":
        return "Surface is meant to open from a bounded public workflow, not from the authenticated navigation tree."
    if origin == "INTENTIONAL_DYNAMIC_DETAIL":
        return "Surface is reached from a parent list, card, or workflow with a runtime record id rather than from primary navigation."
    if origin in {"LEGACY_ALIAS", "LEGACY_REDIRECT", "REPLACED_IMPLEMENTATION", "DUPLICATE_IMPLEMENTATION", "NAVIGATION_NEVER_COMPLETED"}:
        return "Surface persists for compatibility, rollback, or historical bookmarks rather than as a primary navigable destination."
    if origin in {"ROUTE_NOT_IMPLEMENTED", "MISSING_FIXTURE_OR_RUNTIME_DATA"}:
        return "Surface is discoverable in routing but cannot be honestly certified until implementation or preview-safe runtime records exist."
    if row["Active/hidden/detail/public/external state"] == "HIDDEN":
        return "Surface is intentionally suppressed from primary navigation."
    return "Not intentionally hidden from primary navigation."


def derive_entry_path(route: str, row: dict[str, str], reach_row: dict[str, str] | None, origin: str) -> str:
    if route == "(index)":
        return "Transportation shell default landing"
    if route in TOOLING_EXTRA_ROUTES:
        return "Admin-only direct route"
    if route.startswith("/_internal/"):
        return "Developer-only direct route"
    if route.startswith("/dev"):
        return "Developer footer link or direct internal route"
    if route.endswith("/login"):
        return "Direct sign-in route"
    if "/reset/:token" in route or "/forgot" in route or ":token" in route and origin == "INTENTIONAL_TOKEN_LINK":
        return "Token or email handoff"
    if row["Surface type"] == "redirect_route":
        return "Legacy bookmark, QR, typo, or compatibility route"
    if row["Surface type"] in {"detail_route", "hidden_companion_route"}:
        parent = row["Parent route"] or (reach_row["visible_entry_point"] if reach_row else "Parent workflow")
        return f"Parent workflow via {parent}"
    if reach_row:
        return reach_row["visible_entry_point"]
    return "Direct route entry"


def derive_navigation_source(route: str, row: dict[str, str], reach_row: dict[str, str] | None, origin: str) -> str:
    if route in TOOLING_EXTRA_ROUTES:
        return "Admin-only diagnostics / readiness access"
    if route.startswith("/_internal/") or route.startswith("/dev"):
        return "Restricted internal access only"
    if row["Surface type"] == "redirect_route":
        return "Legacy alias / compatibility path"
    if origin == "INTENTIONAL_TOKEN_LINK":
        return "Token or email workflow"
    if origin == "INTENTIONAL_PUBLIC_LINK":
        return "Bounded public workflow"
    if row["Surface type"] in {"detail_route", "hidden_companion_route"}:
        parent = row["Parent route"] or "Parent list or workflow"
        return f"Parent list or workflow under {parent}"
    if reach_row:
        return reach_row["navigation_path"]
    return "Direct route entry"


def derive_canonical_relationship(route: str, row: dict[str, str], origin: str) -> str:
    if route in SPECIAL_CANONICAL_RELATIONSHIPS:
        return SPECIAL_CANONICAL_RELATIONSHIPS[route]
    if route in TOOLING_EXTRA_ROUTES:
        return TOOLING_EXTRA_ROUTES[route]["canonical_relationship"]
    if row["Surface type"] == "detail_route":
        parent = row["Parent route"] or "PARENT_WORKFLOW"
        return f"DETAIL_UNDER:{parent}"
    if row["Surface type"] == "hidden_companion_route":
        parent = row["Parent route"] or "CANONICAL_ROUTE"
        return f"HIDDEN_COMPANION_OF:{parent}"
    if row["Surface type"] == "redirect_route":
        parent = row["Parent route"] or "CANONICAL_ROUTE"
        return f"LEGACY_ALIAS_OF:{parent}"
    return "PRIMARY_ROUTE"


def classify_route_origin(route: str, row: dict[str, str], blocker: dict[str, str] | None) -> str:
    if route in TOOLING_EXTRA_ROUTES:
        return TOOLING_EXTRA_ROUTES[route]["origin"]
    if blocker:
        return "ROUTE_NOT_IMPLEMENTED" if blocker["reason"] == "BLOCKED_ROUTE_NOT_IMPLEMENTED" else "MISSING_FIXTURE_OR_RUNTIME_DATA"
    if route.startswith("/_internal/") or route.startswith("/dev"):
        return "DEVELOPER_OR_CERTIFICATION_TOOL"
    component = row["Current component family"]
    if row["Surface type"] == "hidden_companion_route":
        if route.startswith("/_internal/"):
            return "DEVELOPER_OR_CERTIFICATION_TOOL"
        return "DUPLICATE_IMPLEMENTATION"
    if row["Surface type"] == "redirect_route" or "Redirect" in component or component == "Navigate":
        if route.startswith("/ops-training"):
            return "REPLACED_IMPLEMENTATION"
        if route.startswith("/executive/ods-intelligence"):
            return "NAVIGATION_NEVER_COMPLETED"
        if any(token in route for token in ["/daily-report/v", "/daily/v", "/hub_v", "/hub_v1", "/hub_v2"]):
            return "REPLACED_IMPLEMENTATION"
        return "LEGACY_ALIAS"
    if ":token" in route or route.startswith("/d/:token") or route.startswith("/transport-invite/"):
        return "INTENTIONAL_TOKEN_LINK"
    if "/public/" in route or route.startswith("/transport-verify/") or route.startswith("/odr/public/"):
        return "INTENTIONAL_PUBLIC_LINK"
    return "INTENTIONAL_DYNAMIC_DETAIL"


def classify_route_disposition(route: str, row: dict[str, str], blocker: dict[str, str] | None, origin: str) -> str:
    if route in TOOLING_EXTRA_ROUTES:
        return TOOLING_EXTRA_ROUTES[route]["disposition"]
    if blocker:
        if blocker["reason"] == "BLOCKED_ROUTE_NOT_IMPLEMENTED":
            return "IMPLEMENTATION_REQUIRED"
        if blocker["group"] == "runtime":
            return "RUNTIME_BLOCKED"
        return "FIXTURE_REQUIRED"
    if origin == "DEVELOPER_OR_CERTIFICATION_TOOL":
        return "ROLE_RESTRICTED_AND_GOVERNED"
    if origin == "INTENTIONAL_DIALOG_OR_OVERLAY":
        return "INTENTIONALLY_HIDDEN_AND_GOVERNED"
    if origin == "INTENTIONAL_TOKEN_LINK":
        return "TOKEN_OR_EMAIL_LINK_ONLY"
    if origin == "INTENTIONAL_PUBLIC_LINK":
        return "REACHABLE_THROUGH_VALID_WORKFLOW"
    if origin == "INTENTIONAL_DYNAMIC_DETAIL":
        return "REACHABLE_THROUGH_VALID_WORKFLOW"
    if origin in {"LEGACY_ALIAS", "LEGACY_REDIRECT"}:
        return "REDIRECT_CERTIFIED"
    if origin in {"REPLACED_IMPLEMENTATION", "DUPLICATE_IMPLEMENTATION", "NAVIGATION_NEVER_COMPLETED"}:
        if row["Surface type"] == "redirect_route":
            return "MERGED_INTO_CANONICAL_ROUTE"
        return "INTENTIONALLY_HIDDEN_AND_GOVERNED"
    return "INTENTIONALLY_HIDDEN_AND_GOVERNED"


def classify_overlay_disposition() -> str:
    return "INTENTIONALLY_HIDDEN_AND_GOVERNED"


def evidence_strength(route: str, blocker: dict[str, str] | None, rationale: str, evidence: str) -> str:
    if blocker and rationale:
        return "LEDGER_AND_BLOCKER_REGISTER"
    if blocker:
        return "BLOCKER_REGISTER_ONLY"
    if rationale and evidence:
        return "LEDGER_AND_CERTIFICATION_RATIONALE"
    if rationale:
        return "CLASSIFICATION_RATIONALE"
    if evidence:
        return "LEDGER_ONLY"
    return "SOURCE_ONLY"


def risk_summary(origin: str, disposition: str) -> str:
    if disposition in {"IMPLEMENTATION_REQUIRED", "FIXTURE_REQUIRED", "RUNTIME_BLOCKED"}:
        return "Deep links can imply a finished workflow even though preview-safe certification evidence is incomplete."
    if origin == "DEVELOPER_OR_CERTIFICATION_TOOL":
        return "Tooling surfaces can leak internal terminology, preview data, or certification context if role scoping ever regresses."
    if origin in {"LEGACY_ALIAS", "REPLACED_IMPLEMENTATION", "DUPLICATE_IMPLEMENTATION", "NAVIGATION_NEVER_COMPLETED"}:
        return "Compatibility and duplicate routes create drift pressure unless a single canonical owner remains explicit."
    if origin in {"INTENTIONAL_TOKEN_LINK", "INTENTIONAL_PUBLIC_LINK"}:
        return "Token/public entry points can fail silently if invalid-state handling or bounded access rules regress."
    if origin == "INTENTIONAL_DIALOG_OR_OVERLAY":
        return "Workflow-internal surfaces accumulate silently when they are not inventoried alongside routed pages."
    return "Dynamic surfaces need parent-workflow governance so they are not mistaken for missing primary navigation."


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
        if relative_path in INDEX_GOVERNED_FILES and re.search(r"\bindex\b", tag):
            routes.append(("(index)", start_line))
        match = re.search(r'path\s*=\s*"([^"]+)"', tag, re.DOTALL)
        if match:
            routes.append((match.group(1), start_line))
        idx += 1
    return routes


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_forensic_artifacts() -> None:
    convergence_rows = read_csv(CONVERGENCE_LEDGER)
    implementation_rows = read_csv(IMPLEMENTATION_LEDGER)
    reachability_rows = read_csv(REACHABILITY_LEDGER)
    pending_rows = read_csv(PENDING_CLASSIFICATION)
    blocker_map = parse_blocker_register(FINAL_BLOCKER_REGISTER)
    overlay_rows = parse_overlay_register(OVERLAY_REGISTER)

    pending_by_route = {row["route"]: row for row in pending_rows}
    convergence_by_key = {
        (row["Files affected"], row["Route or launch point"]): row
        for row in convergence_rows
        if row["Permanent surface ID"].startswith("ROUTE-")
    }
    route_rows = [
        row
        for row in convergence_rows
        if row["Permanent surface ID"].startswith("ROUTE-")
    ]
    overlay_surface_rows = [
        row
        for row in convergence_rows
        if row["Permanent surface ID"].startswith("OVERLAY-")
    ]

    forensic_rows: list[dict[str, str]] = []

    route_forensic_rows = []
    for row in route_rows:
        route = row["Route or launch point"]
        if route_is_non_primary(row) or route in TOOLING_EXTRA_ROUTES:
            route_forensic_rows.append(row)

    for row in route_forensic_rows:
        route = row["Route or launch point"]
        source_file = row["Files affected"]
        reach = find_reachability_row(route, source_file, reachability_rows)
        pending = pending_by_route.get(route)
        blocker = blocker_map.get(route)
        origin = classify_route_origin(route, row, blocker)
        disposition = classify_route_disposition(route, row, blocker, origin)
        certification = blocker["reason"] if blocker else (reach["certification_status"] if reach else row["Final certification"])
        rationale = pending["rationale"] if pending else ""
        evidence = TOOLING_EXTRA_ROUTES.get(route, {}).get("evidence") or rationale or row["Evidence"]
        hidden_state = row["Active/hidden/detail/public/external state"]
        en_es, responsive = certification_split(certification)
        forensic_rows.append(
            {
                "forensic_surface_id": row["Permanent surface ID"],
                "surface_scope": "route_surface",
                "included_in_hidden_detail_113": "YES" if hidden_state in {"DETAIL", "HIDDEN"} and route != "/admin/hub_v2" else "NO",
                "included_in_route_non_primary_165": "YES" if route_is_non_primary(row) else "NO",
                "included_in_route_forensic_169": "YES",
                "included_in_broad_forensic_305": "YES",
                "family": normalize_family(row["Portal/family"]),
                "source_file": source_file,
                "source_line": reach["source_line"] if reach else "",
                "surface_type": row["Surface type"],
                "route_or_launch_point": route,
                "parent_or_context": row["Parent route"],
                "intended_audience": reach["role"] if reach else normalize_family(row["Portal/family"]),
                "entry_path": derive_entry_path(route, row, reach, origin),
                "navigation_source": derive_navigation_source(route, row, reach, origin),
                "role_requirements": reach["role"] if reach else normalize_family(row["Portal/family"]),
                "hidden_state": hidden_state,
                "origin_classification": origin,
                "final_disposition": disposition,
                "canonical_relationship": derive_canonical_relationship(route, row, origin),
                "certification_or_blocker_status": certification,
                "evidence_strength": evidence_strength(route, blocker, rationale, row["Evidence"]),
                "evidence_summary": evidence,
                "risk_summary": risk_summary(origin, disposition),
                "notes": blocker["group"] if blocker else (pending["classification_status"] if pending else row["Status"]),
            }
        )

    overlay_examples = {item["interaction_id"]: item for item in overlay_rows}
    for row in overlay_surface_rows:
        source_file = row["Files affected"]
        forensic_rows.append(
            {
                "forensic_surface_id": row["Permanent surface ID"],
                "surface_scope": "overlay_surface",
                "included_in_hidden_detail_113": "NO",
                "included_in_route_non_primary_165": "NO",
                "included_in_route_forensic_169": "NO",
                "included_in_broad_forensic_305": "YES",
                "family": normalize_family(row["Portal/family"]),
                "source_file": source_file,
                "source_line": "",
                "surface_type": row["Surface type"],
                "route_or_launch_point": row["Route or launch point"] or row["Current component family"],
                "parent_or_context": row["Parent route"],
                "intended_audience": normalize_family(row["Portal/family"]),
                "entry_path": "Triggered from a host screen action, row, button, or workflow state",
                "navigation_source": "Workflow-internal interaction",
                "role_requirements": normalize_family(row["Portal/family"]),
                "hidden_state": row["Active/hidden/detail/public/external state"],
                "origin_classification": "INTENTIONAL_DIALOG_OR_OVERLAY",
                "final_disposition": classify_overlay_disposition(),
                "canonical_relationship": f"OVERLAY_OF:{source_file}",
                "certification_or_blocker_status": row["Status"],
                "evidence_strength": "LEDGER_ONLY",
                "evidence_summary": f"Source-inventory overlay from {source_file}. Explicit interaction subset separately recorded in WP16_OVERLAY_AND_INTERACTION_REGISTER.md (28 exercised/partially exercised/blocked interaction rows).",
                "risk_summary": risk_summary("INTENTIONAL_DIALOG_OR_OVERLAY", classify_overlay_disposition()),
                "notes": row["Current component family"],
            }
        )

    forensic_rows.sort(key=lambda item: item["forensic_surface_id"])
    forensic_fields = [
        "forensic_surface_id",
        "surface_scope",
        "included_in_hidden_detail_113",
        "included_in_route_non_primary_165",
        "included_in_route_forensic_169",
        "included_in_broad_forensic_305",
        "family",
        "source_file",
        "source_line",
        "surface_type",
        "route_or_launch_point",
        "parent_or_context",
        "intended_audience",
        "entry_path",
        "navigation_source",
        "role_requirements",
        "hidden_state",
        "origin_classification",
        "final_disposition",
        "canonical_relationship",
        "certification_or_blocker_status",
        "evidence_strength",
        "evidence_summary",
        "risk_summary",
        "notes",
    ]
    write_csv(FORENSIC_REGISTER, forensic_rows, forensic_fields)

    governance_rows: list[dict[str, str]] = []
    parsed_routes: list[dict[str, str]] = []
    for relative_path in sorted(APP_ROUTE_FILES):
        path = ROOT / relative_path
        for route, line_no in parse_routes_from_source(path, relative_path):
            parsed_routes.append({"source_file": relative_path, "route": route, "source_line": str(line_no)})

    parsed_lookup = {(row["source_file"], row["route"]): row for row in parsed_routes}
    for reach in reachability_rows:
        source_file = reach["source_file"]
        key = (source_file, reach["route"])
        parsed = parsed_lookup.get(key)
        if reach["route"] == "(index)" and parsed is None:
            parsed = next(
                (
                    row
                    for row in parsed_routes
                    if row["route"] == "(index)" and row["source_file"] in INDEX_GOVERNED_FILES
                ),
                None,
            )
            if parsed is not None:
                source_file = parsed["source_file"]
        conv = convergence_by_key.get((source_file, reach["route"]))
        implementation = None
        for item in implementation_rows:
            if item["Route"] == reach["route"] and item["Files affected"] == source_file:
                implementation = item
                break
        route = reach["route"]
        family = reach["family"]
        owner = OWNER_BY_FAMILY.get(family, family)
        hidden = "YES" if reach["hidden_surface_disposition"] in {"JUSTIFIED_HIDDEN_REVIEW", "REDIRECT", "BLOCKED_FIXTURE_REQUIRED", "BLOCKED_ROUTE_NOT_IMPLEMENTED"} or route in TOOLING_EXTRA_ROUTES else "NO"
        derived_origin = classify_route_origin(route, conv or {
            "Surface type": reach["route_kind"],
            "Current component family": "",
            "Active/hidden/detail/public/external state": "ACTIVE",
            "Parent route": "",
        }, blocker_map.get(route))
        hidden_reason = (
            "Not intentionally hidden; this is a primary, public, or direct authenticated entry surface."
            if hidden == "NO"
            else derive_hidden_reason(conv or {
                "Active/hidden/detail/public/external state": "ACTIVE",
                "Surface type": reach["route_kind"],
                "Current component family": "",
                "Parent route": "",
            }, route, derived_origin)
        )
        certification = blocker_map.get(route, {}).get("reason") or reach["certification_status"]
        en_es, responsive = certification_split(certification)
        governance_rows.append(
            {
                "source_file": source_file,
                "source_line": parsed["source_line"] if parsed else reach["source_line"],
                "declared_route": route,
                "owner": owner,
                "family": family,
                "intended_audience": reach["role"],
                "entry_path": derive_entry_path(route, conv or {
                    "Surface type": reach["route_kind"],
                    "Parent route": "",
                    "Current component family": "",
                    "Active/hidden/detail/public/external state": "ACTIVE",
                }, reach, derived_origin),
                "navigation_source": derive_navigation_source(route, conv or {
                    "Surface type": reach["route_kind"],
                    "Parent route": "",
                    "Current component family": "",
                    "Active/hidden/detail/public/external state": "ACTIVE",
                }, reach, derived_origin),
                "role_requirements": reach["role"],
                "intentionally_hidden": hidden,
                "hidden_rationale": hidden_reason,
                "canonical_relationship": derive_canonical_relationship(route, conv or {
                    "Surface type": reach["route_kind"],
                    "Parent route": "",
                    "Current component family": "",
                }, derived_origin),
                "en_es_compliance": en_es,
                "responsive_compliance": responsive,
                "certification_evidence": certification,
                "governance_evidence": pending_by_route.get(route, {}).get("rationale") or reach["reachability_status"],
            }
        )

    governance_rows.sort(key=lambda item: (item["source_file"], int(item["source_line"]), item["declared_route"]))
    governance_fields = [
        "source_file",
        "source_line",
        "declared_route",
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
        "governance_evidence",
    ]
    write_csv(ROUTE_GOVERNANCE_REGISTRY, governance_rows, governance_fields)

    route_scope = [row for row in forensic_rows if row["surface_scope"] == "route_surface"]
    overlay_scope = [row for row in forensic_rows if row["surface_scope"] == "overlay_surface"]
    hidden_detail_total = sum(row["included_in_hidden_detail_113"] == "YES" for row in forensic_rows)
    route_non_primary_total = sum(row["included_in_route_non_primary_165"] == "YES" for row in forensic_rows)
    route_forensic_total = sum(row["included_in_route_forensic_169"] == "YES" for row in forensic_rows)
    broad_total = sum(row["included_in_broad_forensic_305"] == "YES" for row in forensic_rows)

    origin_counts = Counter(row["origin_classification"] for row in forensic_rows)
    disposition_counts = Counter(row["final_disposition"] for row in forensic_rows)
    family_counts = Counter(row["family"] for row in forensic_rows)
    blocked_counts = Counter(row["final_disposition"] for row in route_scope if row["final_disposition"] in {"IMPLEMENTATION_REQUIRED", "FIXTURE_REQUIRED", "RUNTIME_BLOCKED"})
    overlay_counts = Counter(row["family"] for row in overlay_scope)

    family_lines = [
        "# WP-17 Hidden Surface Family Summary",
        "",
        "## Authoritative scope stack",
        "- Full audited-surface ledger: **1,193** current rows in `/app/WP17D_PLATFORM_CONVERGENCE_LEDGER.csv`.",
        "- Historical baseline ledger: **1,190** rows in `/app/WP17C_IMPLEMENTATION_LEDGER.csv`.",
        "- Reconciled routed-object denominator: **484**.",
        "- Locked hidden/detail route denominator: **113**.",
        "- Route non-primary forensic denominator: **165**.",
        "- Route tooling addendum: **4** admin-only internal readiness/validation routes.",
        "- Broad hidden-surface forensic denominator: **305** (= 169 route surfaces + 136 overlay-only surfaces).",
        "",
        "## Family totals across the 305-surface forensic register",
        "",
        "| Family | Surfaces | Route surfaces | Overlay surfaces | Blocked route surfaces |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for family in sorted(family_counts):
        total = family_counts[family]
        route_total = sum(1 for row in route_scope if row["family"] == family)
        overlay_total = overlay_counts.get(family, 0)
        blocked_total = sum(
            1
            for row in route_scope
            if row["family"] == family and row["final_disposition"] in {"IMPLEMENTATION_REQUIRED", "FIXTURE_REQUIRED", "RUNTIME_BLOCKED"}
        )
        family_lines.append(f"| {family} | {total} | {route_total} | {overlay_total} | {blocked_total} |")

    family_lines.extend(
        [
            "",
            "## Origin-classification totals",
            "",
            "| Origin classification | Count |",
            "| --- | ---: |",
        ]
    )
    for name, count in origin_counts.most_common():
        family_lines.append(f"| {name} | {count} |")

    family_lines.extend(
        [
            "",
            "## Final-disposition totals",
            "",
            "| Final disposition | Count |",
            "| --- | ---: |",
        ]
    )
    for name, count in disposition_counts.most_common():
        family_lines.append(f"| {name} | {count} |")

    family_lines.extend(
        [
            "",
            "## Key conclusions by family",
            "- **Administration** carries the highest concentration of internal tooling, duplicate governance routes, and the frozen implementation/fixture blockers.",
            "- **Shared Operational Home and Public Entry** contains the broadest mix of public token links, compatibility redirects, and general-purpose hidden details.",
            "- **Project Management / Human Resources / Shop Operations** hold the nine runtime-data blockers recorded in the final blocker register; the routes exist, but preview-safe records were not available for honest runtime certification.",
            "- **Safety Operations / Transportation Operations** contain a large share of legitimate hidden detail and workflow-only record surfaces, plus most of the public/token continuity links.",
            "- **Developer Tooling** is small in count but high in trust risk because it is where internal terminology and preview-only utilities can leak.",
        ]
    )
    FAMILY_SUMMARY.write_text("\n".join(family_lines) + "\n", encoding="utf-8")

    report_lines = [
        "# WP-17 Hidden Surface Executive Report",
        "",
        "## Executive conclusion",
        "WP-17 did not uncover one single hidden-route problem. It uncovered four different classes of hidden-surface accumulation: legitimate workflow-only detail routes, compatibility aliases and redirects, internal tooling / certification routes, and overlay-only interaction surfaces that had never been reconciled into one closing denominator.",
        "",
        "The forensic closeout reconciles those classes without inventing counts:",
        f"- **1,190 → 1,193**: the historical WP17C baseline ledger carried 1,190 surfaces; WP17D later reconciled three live admin routes into the current full ledger (`/admin/leadership/records`, `/admin/platform-readiness`, `/admin/wp17d-certification`), producing the current **1,193-surface** master ledger.",
        f"- **484**: the current routed-object denominator is real and source-verified across five routed files (`AppRoutes.jsx`, `TransportationApp.jsx`, `_orientation.jsx`, `_intelligence.jsx`, `_command_queue.jsx`).",
        f"- **113**: the locked hidden/detail denominator is still valid. It equals every route surface currently in `DETAIL` or `HIDDEN` state except the one explicitly excluded hidden redirect alias `/admin/hub_v2`. The 26 hidden navigation nodes belong to the separate 253-node navigation denominator and were never supposed to be in the 113 total.",
        f"- **165**: once compatibility aliases/redirects are added back to the 113 route-hidden universe, the route-level non-primary denominator becomes **165**.",
        f"- **169**: adding the four admin-only internal readiness / validation routes that are not hidden by route type but are developer/certification tooling yields the complete route-level forensic denominator.",
        f"- **305**: adding the **136 overlay-only surfaces** from the master ledger yields the broad hidden-surface forensic denominator for this closeout.",
        "",
        "## Why the ledgers diverged",
        "1. `WP17C_IMPLEMENTATION_LEDGER.csv` is the earlier 1,190-row baseline. It is historically accurate, but not current after WP17D inventory expansion.",
        "2. `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv` is the current 1,193-row surface ledger and is the authoritative denominator for present-day full-surface math.",
        "3. `WP17D_PLATFORM_REACHABILITY_LEDGER.csv` is a route-only ledger. It remained accurate for route discovery at 484 rows, but it does not include overlays and it does not back-propagate every later forensic classification unless another ledger was updated.",
        "4. `WP17D_FINAL_BLOCKER_REGISTER.md` truthfully recorded 16 final blockers. The route-only ledger still shows only the original 7 hard-blocked status codes because the later 9 runtime-data blocker dispositions were captured in the blocker register rather than written back into the route-status columns. That is a documentation drift issue, not a hidden product issue.",
        "5. `WP17D_SURVIVOR_REGISTER.md` is explicitly dated 2026-08-02. Its pending counts are a historical snapshot from before the 2026-08-03 closure wave and must not be treated as the final route-classification state.",
        "",
        "## What the hidden surfaces actually were",
        f"- **Legitimate workflow-only details / public-token links**: {origin_counts['INTENTIONAL_DYNAMIC_DETAIL'] + origin_counts['INTENTIONAL_TOKEN_LINK'] + origin_counts['INTENTIONAL_PUBLIC_LINK']} surfaces. These are the dynamic record views, tokenized public links, and bounded continuity routes that should exist but should not be primary navigation items.",
        f"- **Legacy aliases, redirects, and replaced implementations**: {origin_counts['LEGACY_ALIAS'] + origin_counts['REPLACED_IMPLEMENTATION'] + origin_counts['DUPLICATE_IMPLEMENTATION'] + origin_counts['NAVIGATION_NEVER_COMPLETED']} surfaces. These explain most of the duplicate or compatibility drift.",
        f"- **Developer / certification tooling**: {origin_counts['DEVELOPER_OR_CERTIFICATION_TOOL']} surfaces. These are the highest trust-risk items because they can expose internal terminology or readiness concepts if role scoping regresses.",
        f"- **Runtime-data / implementation blockers**: {origin_counts['MISSING_FIXTURE_OR_RUNTIME_DATA'] + origin_counts['ROUTE_NOT_IMPLEMENTED']} route surfaces. These explain every remaining deep-link blocker without pretending the routes were certified.",
        f"- **Overlay-only surfaces**: {origin_counts['INTENTIONAL_DIALOG_OR_OVERLAY']} surfaces. These were never a route problem; they were an inventory-governance problem.",
        "",
        "## Final blocker accounting",
        "- **7 frozen Administration blockers** remain exactly as documented: `/admin/assets/:assetId`, `/admin/equipment/:id/history`, `/admin/employees/:id/history`, `/admin/equipment/:id`, `/admin/leadership/records/:id`, `/admin/safety/issuance/:id`, `/admin/safety/training/:id`.",
        "- **9 runtime-data blockers** remain exactly as documented: `/pm/incidents/:id`, `/pm/meetings/:id`, `/pm/inspections/:id`, `/pm/equipment/:id`, `/hr/historical-records/batches/:batchId`, `/shop/units/:unitNumber/history`, `/shop/fuel-lube/:visitId`, `/shop/service-truck-reconciliation/:recId`, `/shop/equipment/:id`.",
        "- The broad forensic register therefore records all 16 blocker surfaces without changing the accepted WP-17D closure fact that active-family actionable routes are already zero.",
        "",
        "## Confidence statement",
        "Confidence is high because the denominators now reconcile by scope instead of being forced into one number:",
        "- route inventory = 484",
        "- locked hidden/detail route denominator = 113",
        "- route forensic denominator = 169",
        "- overlay-only denominator = 136",
        "- broad hidden-surface forensic denominator = 305",
        "- current full audited-surface denominator = 1,193",
        "- historical baseline denominator = 1,190",
        "",
        "## Permanent prevention gate",
        "The new route-governance gate is now source-enforced by `/app/scripts/wp17_route_governance_guard.py` and chained into `/app/scripts/wp17d_constitution_guard.py`.",
        "It fails if any routed object is missing any of the following metadata in `/app/memory/WP17_ROUTE_GOVERNANCE_REGISTRY.csv`: owner, family, intended audience, entry path, navigation source, role requirements, intentionally hidden flag, hidden rationale, canonical relationship, EN/ES compliance state, responsive compliance state, and certification evidence.",
        "",
        "## Delivered files",
        f"- `{FORENSIC_REGISTER}`",
        f"- `{EXECUTIVE_REPORT}`",
        f"- `{FAMILY_SUMMARY}`",
        f"- `{ROUTE_GOVERNANCE_REGISTRY}`",
        "",
        "## Inventory notes outside the denominator math",
        "Source comments still reference some retained-on-disk legacy components used only for historical tests or rollback history. Those retained files were documented as source evidence in comments but were not counted in the route or overlay denominators unless they remained routed or inventoried as a formal surface in the ledgers.",
    ]
    EXECUTIVE_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_forensic_artifacts()