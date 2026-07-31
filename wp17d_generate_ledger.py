import csv
from pathlib import Path


ROOT = Path("/app")
SRC = ROOT / "WP17C_IMPLEMENTATION_LEDGER.csv"
OUT = ROOT / "WP17D_PLATFORM_CONVERGENCE_LEDGER.csv"

FIELDS = [
    "Permanent surface ID",
    "Portal/family",
    "Route or launch point",
    "Parent route",
    "Surface type",
    "Active/hidden/detail/public/external state",
    "Current visual generation",
    "Current shell",
    "Current header",
    "Current sidebar/navigation",
    "Current background",
    "Current component family",
    "Current icon family",
    "Current terminology",
    "Current coaching",
    "Current footer",
    "Current mobile state",
    "Current functional status",
    "Current runtime errors",
    "WP-17B disposition",
    "Required migration action",
    "Required functional repair",
    "Target canonical components",
    "Files affected",
    "Dependencies",
    "Status",
    "Evidence",
    "Final certification",
]

CONVERGED_PORTALS = {
    "public_shared",
    "admin",
    "pm",
    "hr",
    "safety",
    "transportation",
    "dispatch",
    "shop",
    "field_leadership",
    "training_guidance",
    "executive",
    "driver",
}
REPAIR_WAVE_PORTALS = {"transportation", "hr", "public_shared"}


def current_state(route: str, source_status: str, portal: str) -> str:
    if portal == "dev":
        return "HIDDEN"
    if route.startswith("http"):
      return "EXTERNAL"
    if source_status in {"HIDDEN", "DETAIL"}:
        return source_status
    if portal == "public_shared" and any(token in route for token in ["invite", "verify", "/d/"]):
        return "EXTERNAL"
    return "ACTIVE"


def visual_generation(portal: str, source_id: str) -> str:
    if portal in CONVERGED_PORTALS:
        return "WP17D_CANONICAL_WAVE"
    if source_id.startswith(("FORM-", "TABLE-", "OVERLAY-")):
        return "WP17D_SHARED_COMPONENT_PASS"
    return "LEGACY_MIXED"


def current_shell(portal: str, route: str, files: str) -> str:
    if portal == "public_shared":
        return "WP17 public shell" if any(x in files or x in route for x in ["SignIn", "Hub", "login", "/sign-in", "/"]) else "public/external shell"
    if portal in {"admin", "pm", "hr", "safety", "transportation"}:
        return "PortalShell (canonical wp17d wave)"
    if "FormShell" in files:
        return "FormShell (canonical wp17d wave)"
    return "Legacy or portal-specific shell"


def current_header(portal: str) -> str:
    if portal in CONVERGED_PORTALS:
        return "Canonical glass header"
    return "Mixed / legacy header"


def current_sidebar(portal: str, surface_type: str) -> str:
    if surface_type == "navigation_item":
        return "Canonical nav item under convergence"
    if portal in {"admin", "pm", "hr", "safety", "transportation"}:
        return "Canonical sidebar in wave migration"
    return "Mixed or contextual navigation"


def current_background(portal: str, route: str) -> str:
    if portal in CONVERGED_PORTALS or route in {"/", "/sign-in"}:
        return "Layered light base + navy grid + restrained glass"
    return "Flat / mixed background system"


def component_target(source_type: str) -> str:
    mapping = {
        "navigation_item": "WP17D_CANONICAL_NAVIGATION_ITEM",
        "form_surface": "WP17D_CANONICAL_FORM",
        "table_surface": "WP17D_CANONICAL_TABLE",
        "detail_route": "WP17D_CANONICAL_DETAIL_PAGE",
        "route_screen": "WP17D_CANONICAL_PAGE",
        "redirect_route": "WP17D_CANONICAL_REDIRECT",
        "index_route": "WP17D_CANONICAL_PAGE",
        "pdf_source_surface": "WP17D_CANONICAL_PDF_EXPORT",
        "email_template_surface": "WP17D_CANONICAL_EMAIL_TEMPLATE",
        "notification_surface": "WP17D_CANONICAL_NOTIFICATION",
        "coaching_surface": "WP17D_CANONICAL_COACHING",
        "white_label_surface": "WP17D_CANONICAL_BRANDING",
    }
    return mapping.get(source_type, "WP17D_CANONICAL_COMPONENT")


def required_migration_action(portal: str, source_type: str, route: str) -> str:
    if portal in REPAIR_WAVE_PORTALS:
        return "FIRST_WAVE_REPAIR_AND_CONVERGENCE"
    if source_type == "navigation_item":
        return "NAVIGATION_CONVERGENCE"
    if source_type in {"form_surface", "table_surface"}:
        return "SHARED_COMPONENT_CONVERGENCE"
    if route.startswith("/_internal") or route.startswith("/dev"):
        return "INTENTIONAL_HIDE_OR_REDIRECT"
    return "PORTAL_MIGRATION"


def required_functional_repair(portal: str, route: str, source_type: str) -> str:
    if portal == "transportation":
        return "Repair auth/runtime drift, duplicate navigation, and mixed shell behavior"
    if portal == "hr":
        return "Repair partial shell migration and inconsistent detail/form/list behavior"
    if portal == "public_shared" and any(token in route for token in ["invite", "verify", "/d/"]):
        return "Repair external/public workflow consistency, mobile-first layout, and powered-by boundary"
    if source_type in {"form_surface", "table_surface"}:
        return "Converge onto governed shared component behavior"
    return "Inspect and repair defects encountered during migration"


def ledger_status(portal: str, route: str, source_status: str, source_type: str) -> str:
    if portal == "dev":
        return "HIDDEN"
    if source_status == "HIDDEN":
        return "HIDDEN"
    if source_type == "redirect_route":
        return "REDIRECTED"
    if portal in REPAIR_WAVE_PORTALS:
        return "MIGRATING"
    if portal in {"admin", "pm", "safety", "dispatch", "shop", "field_leadership", "training_guidance", "executive", "driver"}:
        return "IMPLEMENTED"
    if source_type in {"form_surface", "table_surface", "navigation_item", "notification_surface"}:
        return "MIGRATING"
    return "INSPECTING"


def current_functional_status(portal: str, source_status: str) -> str:
    if source_status == "HIDDEN":
        return "Intentionally hidden or internal"
    if portal in REPAIR_WAVE_PORTALS:
        return "Under active convergence repair"
    return "Operational; convergence verification pending"


def runtime_errors(portal: str) -> str:
    if portal == "transportation":
        return "Inspecting valid-session auth/runtime failures and mixed layout regressions"
    return "None observed in current wave or pending inspection"


def mobile_state(portal: str) -> str:
    if portal in CONVERGED_PORTALS:
        return "Canonical responsive shell in wave rollout"
    return "Pending responsive convergence"


def footer_state(portal: str) -> str:
    if portal in {"public_shared", "admin", "pm", "hr", "safety", "transportation"}:
        return "Canonical footer boundary in wave rollout"
    return "Mixed footer treatment"


def evidence(source_row: dict, portal: str) -> str:
    parts = ["Imported from WP17C ledger"]
    if portal in CONVERGED_PORTALS:
        parts.append("Shared shell/token convergence wave active")
    if portal in REPAIR_WAVE_PORTALS:
        parts.append("Executive first-priority repair wave")
    if source_row.get("Files affected"):
        parts.append(source_row["Files affected"])
    return " · ".join(parts)


def main() -> None:
    rows = []
    with SRC.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            source_id = source_row["Surface ID"]
            portal = source_row["Portal/family"]
            route = source_row["Route"]
            source_type = source_row["Surface type"]
            visibility = source_row["Hidden/detail/public status"]
            files = source_row["Files affected"]
            row = {
                "Permanent surface ID": source_id,
                "Portal/family": portal,
                "Route or launch point": route,
                "Parent route": source_row["Parent route"],
                "Surface type": source_type,
                "Active/hidden/detail/public/external state": current_state(route, visibility, portal),
                "Current visual generation": visual_generation(portal, source_id),
                "Current shell": current_shell(portal, route, files),
                "Current header": current_header(portal),
                "Current sidebar/navigation": current_sidebar(portal, source_type),
                "Current background": current_background(portal, route),
                "Current component family": source_row["Current component family"],
                "Current icon family": "lucide-react (canonical wrapper convergence)",
                "Current terminology": source_row["Terminology action"],
                "Current coaching": source_row["Coaching action"],
                "Current footer": footer_state(portal),
                "Current mobile state": mobile_state(portal),
                "Current functional status": current_functional_status(portal, visibility),
                "Current runtime errors": runtime_errors(portal),
                "WP-17B disposition": source_row["WP-17B disposition"],
                "Required migration action": required_migration_action(portal, source_type, route),
                "Required functional repair": required_functional_repair(portal, route, source_type),
                "Target canonical components": source_row["Target component family"] or component_target(source_type),
                "Files affected": files,
                "Dependencies": source_row["Dependency"],
                "Status": ledger_status(portal, route, visibility, source_type),
                "Evidence": evidence(source_row, portal),
                "Final certification": "PENDING",
            }
            rows.append(row)

    if len(rows) != 1190:
        raise SystemExit(f"Expected 1190 rows, found {len(rows)}")

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUT} with {len(rows)} rows")


if __name__ == "__main__":
    main()