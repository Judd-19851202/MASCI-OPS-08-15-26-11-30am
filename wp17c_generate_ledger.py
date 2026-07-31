import csv
import json
import re
from pathlib import Path


ROOT = Path("/app")
MEMORY = ROOT / "memory"
FRONTEND = ROOT / "frontend" / "src"

ROUTE_CENSUS = json.loads((MEMORY / "WP16_ROUTE_CENSUS_RAW.json").read_text())
PORTAL_ROUTE_SUMMARY = json.loads((MEMORY / "WP16_PORTAL_ROUTE_SUMMARY.json").read_text())
OVERLAY_INVENTORY = json.loads((MEMORY / "WP16_OVERLAY_AND_NAV_INVENTORY.json").read_text())

REPRESENTATIVE_ROUTES = {
    "/": "main-platform-landing",
    "/sign-in": "public-sign-in",
    "/admin": "admin-landing",
    "/pm": "pm-landing",
    "/admin/people": "list-page",
    "/admin/assets/:assetId": "detail-page",
    "/daily-reports/new": "complex-form",
    "/admin/operational-inventory": "table-heavy-page",
}

COACHING_ITEMS = [
    "backend/routes/guidance_routes.py",
    "backend/routes/odr/guidance_catalog.py",
    "backend/routes/odr/guidance_routes.py",
    "frontend/src/components/HelpDrawer.jsx",
    "frontend/src/components/HelpTip.jsx",
    "frontend/src/components/operational_intelligence/GuidanceCard.jsx",
    "frontend/src/components/operational_intelligence/guidanceMap.js",
    "frontend/src/components/ui/HelpTip.jsx",
    "frontend/src/components/ui/tooltip.jsx",
    "frontend/src/pages/admin/AdminGuidanceCoverage.jsx",
    "frontend/src/pages/guidance/OperationalGuidanceCenter.jsx",
]

WHITE_LABEL_ITEMS = [
    "backend/branded_portal_emails.py",
    "backend/branding_resolver.py",
    "backend/pdf_branding.py",
    "backend/pdf_branding_rl.py",
    "backend/scripts/generate_hub_logos.py",
    "backend/scripts/rebuild_brand_assets.py",
    "frontend/src/components/MasciLogo.jsx",
    "frontend/src/components/TenantBrandingPanel.jsx",
    "frontend/src/lib/BrandingProvider.jsx",
    "frontend/src/lib/brandFilename.js",
]

PDF_ITEMS = [
    "backend/pdf_render.py",
    "backend/export_pdf_fallback.py",
    "backend/field_leadership_pdf.py",
    "backend/hub_banners_pdf.py",
    "backend/pm_welcome_pdf.py",
    "backend/training_pdf.py",
    "backend/routes/dr_v2_pdf.py",
    "backend/routes/odr/pdf.py",
    "backend/routes/field_leadership.py",
    "backend/routes/master_history.py",
    "backend/routes/trench_safety/report_distribution.py",
    "backend/routes/trench_safety/reports.py",
    "backend/routes/trench_safety/report_export.py",
    "backend/incident_engine/report_render.py",
    "backend/incident_engine/executive_report_render.py",
]

EMAIL_ITEMS = [
    "backend/branded_portal_emails.py",
    "backend/email_routing.py",
    "backend/email_routing_v2.py",
    "backend/lib/email_dispatch.py",
    "backend/lib/email_audit_status.py",
    "backend/lib/fsi_email_sender.py",
    "backend/lib/operator_digest.py",
    "backend/lib/transport_command_digest.py",
    "backend/incident_engine/morning_digest.py",
    "backend/po_digest.py",
    "backend/routes/admin_digest_config.py",
    "backend/routes/po_digest_admin.py",
    "backend/routes/safety_portal/digest.py",
    "backend/services/operations_control/email.py",
]

NOTIFICATION_ITEMS = [
    "backend/lib/notification_delivery.py",
    "backend/lib/preview_notification_certification.py",
    "backend/routes/notifications.py",
    "backend/routes/tasks_notifications.py",
    "backend/routes/trench_safety/notifications.py",
    "backend/routes/employee_requests.py",
    "backend/routes/scheduled_producers_d456.py",
    "frontend/src/components/NotificationBell.jsx",
]

FIELDS = [
    "Surface ID",
    "Portal/family",
    "Route",
    "Surface type",
    "Parent route",
    "Navigation location",
    "Hidden/detail/public status",
    "WP-17B disposition",
    "Current component family",
    "Target component family",
    "Information-architecture action",
    "Navigation action",
    "Design action",
    "Terminology action",
    "Coaching action",
    "White-label action",
    "Responsive action",
    "Dependency",
    "Current status",
    "Files affected",
    "Evidence reference",
    "Final certification status",
]


def route_portal_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for portal, routes in PORTAL_ROUTE_SUMMARY.items():
        for route in routes:
            mapping[route] = portal
    return mapping


ROUTE_PORTAL_MAP = route_portal_map()


def infer_portal(route: str, file_hint: str = "") -> str:
    if route and route in ROUTE_PORTAL_MAP:
        return ROUTE_PORTAL_MAP[route]
    if route.startswith("/admin") or "Admin" in file_hint:
        return "admin"
    if route.startswith("/pm") or route in {"/po-requests", "/project-health", "/asset-transfers", "/constraints"}:
        return "pm"
    if route.startswith("/shop") or "Shop" in file_hint:
        return "shop"
    if route.startswith("/hr") or route == "/document-expirations" or "Hr" in file_hint:
        return "hr"
    if route.startswith("/safety-portal") or "Safety" in file_hint:
        return "safety"
    if route.startswith("/dispatch-portal") or "Dispatch" in file_hint:
        return "dispatch"
    if route.startswith("/transportation-operations") or route.startswith("/transport-") or "Transportation" in file_hint:
        return "transportation"
    if route.startswith("/field-leadership") or route.startswith("/leadership") or "Leadership" in file_hint:
        return "field_leadership"
    if route.startswith("/guidance") or route.startswith("/cheatsheet") or "Guidance" in file_hint:
        return "training_guidance"
    if route.startswith("/d/") or route.startswith("/driver"):
        return "driver"
    if route.startswith("/executive"):
        return "executive"
    if route.startswith("/dev") or route.startswith("/_internal"):
        return "dev"
    return "public_shared"


def representative_status(route: str) -> str:
    if route in REPRESENTATIVE_ROUTES:
        return "READY"
    portal = infer_portal(route)
    if route.startswith("/dev"):
        return "DEFERRED_TO_17H"
    if route.startswith("/executive"):
        return "DEFERRED_TO_17G"
    if portal in {"admin", "pm", "public_shared", "transportation", "shop", "hr", "safety", "dispatch", "field_leadership", "training_guidance", "driver"}:
        return "DEFERRED_TO_17D"
    return "FOUNDATION_DEPENDENCY"


def route_surface_type(route: str, element_hint: str | None) -> str:
    if element_hint == "Navigate":
        return "redirect_route"
    if ":" in route:
        return "detail_route"
    if any(marker in route for marker in ["hub_v2", "hub_legacy", "/_internal"]):
        return "hidden_companion_route"
    return "route_screen"


def route_visibility(route: str) -> str:
    if ":" in route:
        return "DETAIL"
    if route == "/dev" or any(marker in route for marker in ["hub_v2", "hub_legacy", "/_internal"]):
        return "HIDDEN"
    return "PUBLIC"


def route_disposition(route: str, element_hint: str | None) -> str:
    if route in REPRESENTATIVE_ROUTES:
        return "REPRESENTATIVE_IMPLEMENTATION"
    if element_hint == "Navigate":
        return "CANONICALIZE_REDIRECT"
    if any(marker in route for marker in ["hub_v2", "hub_legacy"]):
        return "MERGE_OR_RETIRE"
    if route.startswith("/_internal") or route.startswith("/dev"):
        return "HIDE"
    if ":" in route:
        return "KEEP_HIDDEN_DETAIL"
    return "MIGRATE_IN_WP17D"


def row_template(**kwargs):
    row = {field: "" for field in FIELDS}
    row.update(kwargs)
    return row


def extract_route_objects(path: Path) -> list[tuple[str, str]]:
    text = path.read_text()
    return re.findall(r'\{\s*to:\s*"([^"]*)"\s*,\s*label:\s*"([^"]+)"', text, re.S)


def sign_in_nav_objects(path: Path) -> list[tuple[str, str]]:
    text = path.read_text()
    items = []
    pattern = re.compile(
        r'<Link to="([^"]+)"[^>]*data-testid="(signin-[^"]+)"[^>]*>\s*([^<→]+)',
        re.S,
    )
    for route, testid, label in pattern.findall(text):
        if testid.endswith("-link"):
            items.append((route, label.strip()))
    return items


def tx_grouped_nav_objects(path: Path) -> list[tuple[str, str]]:
    text = path.read_text()
    all_objects = re.findall(r'\{\s*to:\s*"([^"]*)"\s*,\s*icon:[^\n]+?label:\s*"([^"]+)"', text, re.S)
    return all_objects[:27]


def tx_tab_objects(path: Path) -> list[tuple[str, str]]:
    text = path.read_text()
    return re.findall(
        r'\{\s*to:\s*"([^"]*)"\s*,\s*icon:[^\n]+?label:\s*"([^"]+)"',
        text,
        re.S,
    )[:13]


def portal_from_file(rel_path: str) -> str:
    return infer_portal("", Path(rel_path).name)


def build_routes(rows: list[dict]):
    for idx, route in enumerate(ROUTE_CENSUS["routes"], start=1):
        path = route["path"]
        rows.append(
            row_template(
                **{
                    "Surface ID": f"ROUTE-{idx:04d}",
                    "Portal/family": infer_portal(path),
                    "Route": path,
                    "Surface type": route_surface_type(path, route.get("element_hint")),
                    "Parent route": "/" if path.count("/") <= 1 else path.rsplit("/", 1)[0] or "/",
                    "Navigation location": "route_tree",
                    "Hidden/detail/public status": route_visibility(path),
                    "WP-17B disposition": route_disposition(path, route.get("element_hint")),
                    "Current component family": route.get("element_hint") or "route_element",
                    "Target component family": "WP17C_CANONICAL_DETAIL_PAGE" if ":" in path else "WP17C_CANONICAL_PAGE",
                    "Information-architecture action": "KEEP" if path in REPRESENTATIVE_ROUTES else ("MERGE" if any(marker in path for marker in ["hub_v2", "hub_legacy"]) else "STANDARDIZE"),
                    "Navigation action": "SEARCH_ONLY" if route_visibility(path) != "PUBLIC" else ("REDIRECT_ALIAS" if route.get("element_hint") == "Navigate" else "CANONICAL_ENTRY"),
                    "Design action": "REPRESENTATIVE_IMPLEMENTATION" if path in REPRESENTATIVE_ROUTES else "STANDARDIZE_FOUNDATION",
                    "Terminology action": "ALIGN_TO_WP17B_TERMINOLOGY",
                    "Coaching action": "ADD_CONTEXTUAL_HELP_WHERE_REQUIRED",
                    "White-label action": "TOKENIZE_ONLY",
                    "Responsive action": "CERTIFY_IN_REPRESENTATIVE_SET" if path in REPRESENTATIVE_ROUTES else "DEFERRED_TO_WP17D",
                    "Dependency": "PortalShell + tokens + navigation canon",
                    "Current status": representative_status(path),
                    "Files affected": route.get("file") or "",
                    "Evidence reference": "WP17B_PLATFORM_MASTER_INVENTORY.md · route census",
                    "Final certification status": "PENDING",
                }
            )
        )

    rows.append(
        row_template(
            **{
                "Surface ID": "ROUTE-0481",
                "Portal/family": "transportation",
                "Route": "(index)",
                "Surface type": "index_route",
                "Parent route": "/admin/transportation/* | /transportation-operations/*",
                "Navigation location": "route_tree",
                "Hidden/detail/public status": "PUBLIC",
                "WP-17B disposition": "LOCKED_BLUEPRINT_RECONCILIATION",
                "Current component family": "TransportationApp",
                "Target component family": "WP17C_CANONICAL_PAGE",
                "Information-architecture action": "KEEP",
                "Navigation action": "CANONICAL_ENTRY",
                "Design action": "DEFERRED_TO_17D",
                "Terminology action": "ALIGN_TO_WP17B_TERMINOLOGY",
                "Coaching action": "ADD_CONTEXTUAL_HELP_WHERE_VALUABLE",
                "White-label action": "TOKENIZE_ONLY",
                "Responsive action": "DEFERRED_TO_WP17D",
                "Dependency": "Transportation shell prefix canon",
                "Current status": "DEFERRED_TO_17D",
                "Files affected": "frontend/src/pages/transportation/TransportationApp.jsx",
                "Evidence reference": "WP17B locked total reconciliation · Transportation index route",
                "Final certification status": "PENDING",
            }
        )
    )


def build_navigation(rows: list[dict]):
    counter = 1

    def push(family: str, label: str, route: str, portal: str, nav_location: str, visibility: str, files_affected: str, disposition: str = "STANDARDIZE"):
        nonlocal counter
        rows.append(
            row_template(
                **{
                    "Surface ID": f"NAV-{counter:04d}",
                    "Portal/family": portal,
                    "Route": route or "/admin/transportation",
                    "Surface type": "navigation_item",
                    "Parent route": "/",
                    "Navigation location": nav_location,
                    "Hidden/detail/public status": visibility,
                    "WP-17B disposition": disposition,
                    "Current component family": family,
                    "Target component family": "WP17C_CANONICAL_NAVIGATION_ITEM",
                    "Information-architecture action": "STANDARDIZE",
                    "Navigation action": "CANONICALIZE",
                    "Design action": "STANDARDIZE_FOUNDATION",
                    "Terminology action": "ALIGN_LABEL",
                    "Coaching action": "CONTEXTUAL_HELP_OPTIONAL",
                    "White-label action": "TOKENIZE_ONLY",
                    "Responsive action": "CANONICAL_NAV_RESPONSIVE",
                    "Dependency": "Navigation canon + shell foundation",
                    "Current status": "IN_PROGRESS" if portal in {"admin", "pm", "public_shared"} else "DEFERRED_TO_17D",
                    "Files affected": files_affected,
                    "Evidence reference": f"WP17B navigation family · {family} · {label}",
                    "Final certification status": "PENDING",
                }
            )
        )
        counter += 1

    for route, label in extract_route_objects(ROOT / "frontend/src/components/admin/sidebar/domainMap.js"):
        push("Admin V2 sidebar", label, route, "admin", "sidebar.desktop", "PUBLIC", "frontend/src/components/admin/sidebar/domainMap.js")

    hidden_admin_v3_routes = {
        "/admin/platform-overview",
        "/admin/daily/:id",
        "/admin/meetings/:id",
        "/admin/qaqc/:id",
        "/admin/jobs/:projectNumber/team",
        "/admin/leadership/records/:id",
        "/admin/equipment/:id",
        "/admin/equipment/:id/history",
        "/admin/assets/:assetId",
        "/admin/employees/:id/history",
        "/admin/incidents/:id",
        "/admin/inspections/:id",
        "/admin/asset-mapping",
        "/admin/asset-admin",
        "/admin/asset-spine",
        "/admin/geofence-reconciliation",
        "/admin/operational-inventory",
        "/admin/operational-intelligence",
        "/admin/promo-assets",
        "/admin/analytics",
        "/admin/integrations",
        "/admin/ai-configuration",
        "/admin/digest-config",
        "/admin/email",
        "/admin/sessions",
        "/admin/governance",
    }
    for route, label in extract_route_objects(ROOT / "frontend/src/app/admin/domainMapV3.js"):
        visibility = "HIDDEN" if route in hidden_admin_v3_routes else "PUBLIC"
        location = "command_palette" if visibility == "HIDDEN" else "sidebar.desktop"
        push("Admin V3 domain map", label, route, "admin", location, visibility, "frontend/src/app/admin/domainMapV3.js")

    for route, label in extract_route_objects(ROOT / "frontend/src/components/pm/sidebar/domainMap.js"):
        push("PM V2 sidebar", label, route, "pm", "sidebar.desktop", "PUBLIC", "frontend/src/components/pm/sidebar/domainMap.js")

    for route, label in extract_route_objects(ROOT / "frontend/src/components/hr/sidebar/HrSideNavV2.jsx"):
        push("HR V2 sidebar", label, route, "hr", "sidebar.desktop", "PUBLIC", "frontend/src/components/hr/sidebar/HrSideNavV2.jsx")

    for route, label in extract_route_objects(ROOT / "frontend/src/components/safety/sidebar/SafetySideNavV2.jsx"):
        push("Safety V2 sidebar", label, route, "safety", "sidebar.desktop", "PUBLIC", "frontend/src/components/safety/sidebar/SafetySideNavV2.jsx")

    for route, label in extract_route_objects(ROOT / "frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx"):
        push("Dispatch V2 sidebar", label, route, "dispatch", "sidebar.desktop", "PUBLIC", "frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx")

    for route, label in extract_route_objects(ROOT / "frontend/src/components/shop/sidebar/domainMap.js"):
        push("Shop V2 sidebar", label, route, "shop", "sidebar.desktop", "PUBLIC", "frontend/src/components/shop/sidebar/domainMap.js")

    for route, label in tx_grouped_nav_objects(ROOT / "frontend/src/pages/transportation/_shared.jsx"):
        push(
            "Transportation grouped nav",
            label,
            route,
            "transportation",
            "sidebar.desktop",
            "PUBLIC",
            "frontend/src/pages/transportation/_shared.jsx; frontend/src/components/transportation/sidebar/TransportationSideNavV2.jsx",
        )

    for route, label in tx_tab_objects(ROOT / "frontend/src/pages/transportation/_shared.jsx"):
        push(
            "Transportation child tab set",
            label,
            route,
            "transportation",
            "subnav.tabs",
            "PUBLIC",
            "frontend/src/pages/transportation/_shared.jsx",
        )

    for route, label in sign_in_nav_objects(ROOT / "frontend/src/pages/SignIn.jsx"):
        disposition = "REPRESENTATIVE_IMPLEMENTATION" if route in {"/pm/login", "/admin/login"} else "STANDARDIZE"
        push("Sign-in portal links", label, route, "public_shared", "public_entry", "PUBLIC", "frontend/src/pages/SignIn.jsx", disposition=disposition)

    nav_count = len([row for row in rows if row["Surface ID"].startswith("NAV-")])
    if nav_count != 253:
        raise SystemExit(f"Expected 253 nav items, found {nav_count}")


def build_forms(rows: list[dict]):
    counter = 1
    for path in sorted(FRONTEND.rglob("*")):
        if path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
            continue
        text = path.read_text(errors="ignore")
        matches = list(re.finditer(r"<form\b", text))
        rel = path.relative_to(ROOT).as_posix()
        portal = portal_from_file(rel)
        for _ in matches:
            rows.append(
                row_template(
                    **{
                        "Surface ID": f"FORM-{counter:03d}",
                        "Portal/family": portal,
                        "Route": "",
                        "Surface type": "form_surface",
                        "Parent route": "",
                        "Navigation location": "page_body",
                        "Hidden/detail/public status": "PUBLIC",
                        "WP-17B disposition": "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("NewDailyReportV3.jsx") else "STANDARDIZE",
                        "Current component family": "native_form",
                        "Target component family": "WP17C_CANONICAL_FORM",
                        "Information-architecture action": "KEEP",
                        "Navigation action": "N/A",
                        "Design action": "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("NewDailyReportV3.jsx") else "STANDARDIZE_FOUNDATION",
                        "Terminology action": "ALIGN_LABEL",
                        "Coaching action": "INLINE_HELP_WHERE_VALUABLE",
                        "White-label action": "TOKENIZE_ONLY",
                        "Responsive action": "CERTIFY_IN_REPRESENTATIVE_SET" if rel.endswith("NewDailyReportV3.jsx") else "DEFERRED_TO_WP17D",
                        "Dependency": "Canonical form anatomy + tokens",
                        "Current status": "IN_PROGRESS" if rel.endswith("NewDailyReportV3.jsx") else "FOUNDATION_DEPENDENCY",
                        "Files affected": rel,
                        "Evidence reference": "WP17B platform surface inventory · form count",
                        "Final certification status": "PENDING",
                    }
                )
            )
            counter += 1
    if counter - 1 != 66:
        raise SystemExit(f"Expected 66 forms, found {counter - 1}")


def build_tables(rows: list[dict]):
    counter = 1
    for path in sorted(FRONTEND.rglob("*")):
        if path.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
            continue
        text = path.read_text(errors="ignore")
        matches = list(re.finditer(r"<table\b", text))
        rel = path.relative_to(ROOT).as_posix()
        portal = portal_from_file(rel)
        for _ in matches:
            rows.append(
                row_template(
                    **{
                        "Surface ID": f"TABLE-{counter:03d}",
                        "Portal/family": portal,
                        "Route": "",
                        "Surface type": "table_surface",
                        "Parent route": "",
                        "Navigation location": "page_body",
                        "Hidden/detail/public status": "PUBLIC",
                        "WP-17B disposition": "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("AdminOperationalInventory.jsx") else "STANDARDIZE",
                        "Current component family": "native_table",
                        "Target component family": "WP17C_CANONICAL_TABLE",
                        "Information-architecture action": "KEEP",
                        "Navigation action": "N/A",
                        "Design action": "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("AdminOperationalInventory.jsx") else "STANDARDIZE_FOUNDATION",
                        "Terminology action": "ALIGN_LABEL",
                        "Coaching action": "OPTIONAL_INLINE_HELP",
                        "White-label action": "TOKENIZE_ONLY",
                        "Responsive action": "CERTIFY_IN_REPRESENTATIVE_SET" if rel.endswith("AdminOperationalInventory.jsx") else "DEFERRED_TO_WP17D",
                        "Dependency": "Canonical table anatomy + tokens",
                        "Current status": "IN_PROGRESS" if rel.endswith("AdminOperationalInventory.jsx") else "FOUNDATION_DEPENDENCY",
                        "Files affected": rel,
                        "Evidence reference": "WP17B platform surface inventory · table count",
                        "Final certification status": "PENDING",
                    }
                )
            )
            counter += 1
    if counter - 1 != 196:
        raise SystemExit(f"Expected 196 tables, found {counter - 1}")


def build_overlays(rows: list[dict]):
    counter = 1
    family_targets = {
        "dialog": "WP17C_CANONICAL_MODAL",
        "sheet": "WP17C_CANONICAL_DRAWER",
        "drawer": "WP17C_CANONICAL_DRAWER",
        "popover": "WP17C_CANONICAL_CONTEXT_PANEL",
        "tabs": "WP17C_CANONICAL_TABS",
        "pagination": "WP17C_CANONICAL_PAGINATION",
        "alert_dialog": "WP17C_CANONICAL_MODAL",
    }
    for family_key, items in OVERLAY_INVENTORY.items():
        normalized_key = family_key.replace("alert_dialog", "alert_dialog")
        for item in items:
            route_hint = ""
            rel = item.replace("./", "").replace("/app/", "")
            portal = portal_from_file(rel)
            status = "IN_PROGRESS" if rel.endswith("NotificationBell.jsx") else "FOUNDATION_DEPENDENCY"
            disposition = "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("NotificationBell.jsx") else "STANDARDIZE"
            rows.append(
                row_template(
                    **{
                        "Surface ID": f"OVERLAY-{counter:03d}",
                        "Portal/family": portal,
                        "Route": route_hint,
                        "Surface type": f"{family_key}_surface",
                        "Parent route": "",
                        "Navigation location": "overlay_or_supporting_nav",
                        "Hidden/detail/public status": "PUBLIC",
                        "WP-17B disposition": disposition,
                        "Current component family": family_key,
                        "Target component family": family_targets.get(normalized_key, "WP17C_CANONICAL_OVERLAY"),
                        "Information-architecture action": "KEEP",
                        "Navigation action": "N/A",
                        "Design action": "REPRESENTATIVE_IMPLEMENTATION" if rel.endswith("NotificationBell.jsx") else "STANDARDIZE_FOUNDATION",
                        "Terminology action": "ALIGN_LABEL",
                        "Coaching action": "N/A",
                        "White-label action": "TOKENIZE_ONLY",
                        "Responsive action": "CERTIFY_IN_REPRESENTATIVE_SET" if rel.endswith("NotificationBell.jsx") else "DEFERRED_TO_WP17D",
                        "Dependency": "Canonical overlay foundation",
                        "Current status": status,
                        "Files affected": rel,
                        "Evidence reference": "WP17B overlay/nav inventory",
                        "Final certification status": "PENDING",
                    }
                )
            )
            counter += 1
    if counter - 1 != 136:
        raise SystemExit(f"Expected 136 overlays/nav support surfaces, found {counter - 1}")


def build_named_family(rows: list[dict], prefix: str, portal: str, surface_type: str, current_family: str, target_family: str, items: list[str], evidence: str, disposition: str = "STANDARDIZE"):
    for index, item in enumerate(items, start=1):
        rows.append(
            row_template(
                **{
                    "Surface ID": f"{prefix}-{index:03d}",
                    "Portal/family": portal if portal else portal_from_file(item),
                    "Route": "",
                    "Surface type": surface_type,
                    "Parent route": "",
                    "Navigation location": "supporting_infrastructure",
                    "Hidden/detail/public status": "PUBLIC",
                    "WP-17B disposition": disposition,
                    "Current component family": current_family,
                    "Target component family": target_family,
                    "Information-architecture action": "KEEP",
                    "Navigation action": "N/A",
                    "Design action": "STANDARDIZE_FOUNDATION",
                    "Terminology action": "ALIGN_LABEL",
                    "Coaching action": "N/A",
                    "White-label action": "TOKENIZE_ONLY" if prefix != "WL" else "KEEP_RUNTIME_OWNER",
                    "Responsive action": "N/A",
                    "Dependency": "WP17C foundation governance",
                    "Current status": "FOUNDATION_DEPENDENCY",
                    "Files affected": item,
                    "Evidence reference": evidence,
                    "Final certification status": "PENDING",
                }
            )
        )


def main():
    rows: list[dict] = []
    build_routes(rows)
    build_navigation(rows)
    build_forms(rows)
    build_tables(rows)
    build_overlays(rows)
    build_named_family(rows, "PDF", "admin", "pdf_source_surface", "pdf_owner", "WP17C_CANONICAL_PDF_EXPORT", PDF_ITEMS, "WP17B locked PDF source count")
    build_named_family(rows, "EMAIL", "admin", "email_template_surface", "email_owner", "WP17C_CANONICAL_EMAIL_TEMPLATE", EMAIL_ITEMS, "WP17B locked email/template count")
    build_named_family(rows, "NOTIFY", "admin", "notification_surface", "notification_owner", "WP17C_CANONICAL_NOTIFICATION_FOUNDATION", NOTIFICATION_ITEMS, "WP17B locked notification owner count")
    build_named_family(rows, "COACH", "training_guidance", "coaching_surface", "coaching_owner", "WP17C_CANONICAL_COACHING_PATTERN", COACHING_ITEMS, "WP17B coaching standard · exact 11 findings")
    build_named_family(rows, "WL", "public_shared", "white_label_surface", "branding_owner", "WP17C_CANONICAL_BRANDING_FOUNDATION", WHITE_LABEL_ITEMS, "WP17B white-label standard · exact 10 runtime owners", disposition="KEEP_RUNTIME_OWNER")

    counts = {
        "routes": len([row for row in rows if row["Surface ID"].startswith("ROUTE-")]),
        "nav": len([row for row in rows if row["Surface ID"].startswith("NAV-")]),
        "forms": len([row for row in rows if row["Surface ID"].startswith("FORM-")]),
        "tables": len([row for row in rows if row["Surface ID"].startswith("TABLE-")]),
        "overlays": len([row for row in rows if row["Surface ID"].startswith("OVERLAY-")]),
        "pdf": len([row for row in rows if row["Surface ID"].startswith("PDF-")]),
        "emails": len([row for row in rows if row["Surface ID"].startswith("EMAIL-")]),
        "notifications": len([row for row in rows if row["Surface ID"].startswith("NOTIFY-")]),
        "coaching": len([row for row in rows if row["Surface ID"].startswith("COACH-")]),
        "white_label": len([row for row in rows if row["Surface ID"].startswith("WL-")]),
        "total": len(rows),
        "hidden_detail": len([row for row in rows if row["Surface ID"].startswith("ROUTE-") and row["Hidden/detail/public status"] in {"HIDDEN", "DETAIL"}]),
    }
    expected = {
        "routes": 481,
        "nav": 253,
        "forms": 66,
        "tables": 196,
        "overlays": 136,
        "pdf": 15,
        "emails": 14,
        "notifications": 8,
        "coaching": 11,
        "white_label": 10,
        "total": 1190,
        "hidden_detail": 113,
    }
    if counts != expected:
        raise SystemExit(f"Ledger counts mismatch. Got {counts}, expected {expected}")

    output_path = ROOT / "WP17C_IMPLEMENTATION_LEDGER.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {output_path} with {len(rows)} rows")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()