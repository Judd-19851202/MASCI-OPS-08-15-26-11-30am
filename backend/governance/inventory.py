"""governance.inventory — canonical operational inventory + 10-field matrix.

Programmatic mirror of /app/docs/OPERATIONAL_INVENTORY.md.

The static registries below (PORTALS, USER_TYPES, PUBLIC_ROUTES,
INVENTORY_WORKFLOWS) are the human-curated portion of the audit. The
coverage functions then join them with the live guidance registry
(`guidance.content._ARTICLES`, `_WORKFLOWS`) to produce a JSON snapshot
the admin dashboard renders.

The 10 audit fields (see docs/OPERATIONAL_INVENTORY.md §0):
  1. who_uses_it        2. login_required         3. guidance_exists
  4. onboarding_exists  5. contextual_help        6. why_explanation
  7. troubleshooting    8. discoverability        9. mobile_ux
 10. translation_readiness

Status vocabulary: "complete" | "partial" | "missing" | "n/a" | "deferred".
"""
from __future__ import annotations

from typing import Iterable

from guidance.content import _ARTICLES, _WORKFLOWS, SECTIONS

# ─────────────────────────────────────────────────────────────────────
# Static registries (human-curated; mirror the audit markdown doc)
# ─────────────────────────────────────────────────────────────────────

# 8 portals as audited. `sign_in_listed` reflects whether /sign-in
# currently surfaces a direct entry tile for this portal. `login_url` is
# the canonical login route (None if the portal has no parallel login
# door — Field Leadership is the open exception until Pass 4).
PORTALS: list[dict] = [
    {
        "key": "public", "label": "Public · Field Crew", "login_url": None,
        "token_header": None, "sign_in_listed": True, "scope": "public",
        "section_prefix": "public-", "purpose": "Anonymous / QR-driven field tools and training. No login.",
    },
    {
        "key": "hr", "label": "HR Portal", "login_url": "/hr/login",
        "token_header": "X-HR-Token", "sign_in_listed": True, "scope": "hr",
        "section_prefix": "hr-", "purpose": "Time verification · onboarding · accountability · training records.",
    },
    {
        "key": "safety", "label": "Safety Portal", "login_url": "/safety-portal/login",
        "token_header": "X-Safety-Token", "sign_in_listed": True, "scope": "safety",
        "section_prefix": "safety-", "purpose": "Incidents · corrective actions · audits · training compliance.",
    },
    {
        "key": "shop", "label": "Shop / Fleet Portal", "login_url": "/shop/login",
        "token_header": "X-Shop-Token", "sign_in_listed": False, "scope": "shop",
        "section_prefix": "shop-", "purpose": "Pre-Op review · damage · maintenance · parts · sign-offs.",
    },
    {
        "key": "dispatch", "label": "Dispatch Portal", "login_url": "/dispatch-portal/login",
        "token_header": "X-Dispatch-Token", "sign_in_listed": False, "scope": "dispatch",
        "section_prefix": "dispatch-", "purpose": "Equipment movement · availability · holds · transfers.",
    },
    {
        "key": "pm", "label": "PM Portal", "login_url": "/pm/login",
        "token_header": "X-Pm-Token", "sign_in_listed": True, "scope": "pm",
        "section_prefix": "pm-", "purpose": "Project review · labor docs · cross-portal coordination.",
    },
    {
        # Pass 4 will close this gap; today it's the worst-current-offender
        # captured by the audit as a known structural anomaly.
        "key": "leadership", "label": "Field Leadership Portal", "login_url": None,
        "token_header": None, "sign_in_listed": False, "scope": "leadership",
        "section_prefix": "field-", "purpose": "Superintendents · Foremen · writeups · coaching · field oversight.",
        "anomaly": "No portal-token login. Uses shared MASCIGC password gate at /leadership.",
    },
    {
        "key": "admin", "label": "Admin Console", "login_url": "/admin/login",
        "token_header": "X-Admin-Token", "sign_in_listed": True, "scope": "admin",
        "section_prefix": "admin-", "purpose": "Operator console: people · jobs · system · backups · governance.",
    },
]


# Operational user types (mirrors audit §5). `primary_portal` is the
# native scope; `cross_portal_reads` lists other portals they have
# read-into ability from (relevant for guidance/discoverability scoring).
USER_TYPES: list[dict] = [
    {"key": "anonymous",       "label": "Anonymous / Public",        "primary_portal": "public",      "cross_portal_reads": []},
    {"key": "field_crew",      "label": "Field Crew (laborer)",      "primary_portal": "public",      "cross_portal_reads": []},
    {"key": "operator",        "label": "Equipment Operator",        "primary_portal": "public",      "cross_portal_reads": []},
    {"key": "mechanic",        "label": "Mechanic / Shop",           "primary_portal": "shop",        "cross_portal_reads": []},
    {"key": "foreman",         "label": "Foreman",                   "primary_portal": "leadership",  "cross_portal_reads": ["public"]},
    {"key": "superintendent",  "label": "Superintendent",            "primary_portal": "leadership",  "cross_portal_reads": ["pm"]},
    {"key": "pm",              "label": "Project Manager",           "primary_portal": "pm",          "cross_portal_reads": ["leadership", "safety"]},
    {"key": "hr",              "label": "HR Staff",                  "primary_portal": "hr",          "cross_portal_reads": ["leadership", "safety"]},
    {"key": "safety",          "label": "Safety Manager / Officer",  "primary_portal": "safety",      "cross_portal_reads": ["leadership"]},
    {"key": "dispatch",        "label": "Dispatch",                  "primary_portal": "dispatch",    "cross_portal_reads": ["shop"]},
    {"key": "admin",           "label": "Admin (Operator)",          "primary_portal": "admin",       "cross_portal_reads": ["hr", "safety", "shop", "dispatch", "pm", "leadership"]},
    {"key": "owner",           "label": "Owner",                     "primary_portal": "admin",       "cross_portal_reads": ["hr", "safety", "shop", "dispatch", "pm", "leadership"]},
]


# Public / anonymous-safe routes mapped to their guidance article id (or
# None if the route exists but lacks a dedicated public article). This is
# the canonical "is the public route map covered?" registry.
PUBLIC_ROUTES: list[dict] = [
    {"route": "/", "purpose": "Hub landing", "guidance_id": None},
    {"route": "/guidance", "purpose": "Operational Guidance Center", "guidance_id": "public-tools-map"},
    {"route": "/sign-in", "purpose": "Portal sign-in directory", "guidance_id": None},
    {"route": "/cheatsheet", "purpose": "Crew cheat sheet (QR poster)", "guidance_id": None},
    {"route": "/safety", "purpose": "Safety section navigation", "guidance_id": None},
    {"route": "/safety/cards", "purpose": "Field Safety Cards reference", "guidance_id": None},
    {"route": "/safety/forms", "purpose": "Safety forms hub (gated)", "guidance_id": None},
    {"route": "/field", "purpose": "Field section navigation", "guidance_id": None},
    {"route": "/field/calculators", "purpose": "Material calculator", "guidance_id": "public-material-calculator"},
    {"route": "/qaqc", "purpose": "QA/QC section", "guidance_id": "public-qaqc-basics"},
    {"route": "/submit", "purpose": "Site inspection submit (public)", "guidance_id": None},
    {"route": "/inspections/submit", "purpose": "Site inspection submit (alias)", "guidance_id": None},
    {"route": "/meetings/submit", "purpose": "Safety meeting / toolbox talk submit", "guidance_id": "public-toolbox-talks"},
    {"route": "/incidents/submit", "purpose": "Incident report submit", "guidance_id": "public-incident-basics"},
    {"route": "/daily/submit", "purpose": "Daily report submit", "guidance_id": "public-daily-report-basics"},
    {"route": "/equipment/submit", "purpose": "Equipment Pre-Op submit", "guidance_id": "public-preop-basics"},
    {"route": "/jha", "purpose": "JHA / Job Hazard Plans (read)", "guidance_id": None},
    {"route": "/trench-boxes", "purpose": "Trench Box reference", "guidance_id": None},
    {"route": "/thank-you", "purpose": "Post-submit confirmation", "guidance_id": None},
    {"route": "/training", "purpose": "Training tracks landing", "guidance_id": None},
]


# Cross-cutting operational workflows that may not be tied to a single
# portal token. Extends the per-portal _WORKFLOWS in guidance/content.py
# with the cross-cutting ones the audit identified.
INVENTORY_WORKFLOWS: list[dict] = [
    {"id": "tasks-actions",         "label": "Tasks & Actions",                "portal": "cross-portal", "guidance_id": None},
    {"id": "document-expirations",  "label": "Document Expirations",           "portal": "hr",           "guidance_id": None},
    {"id": "po-requests",           "label": "PO Requests",                    "portal": "pm",           "guidance_id": None},
    {"id": "project-health",        "label": "Project Health",                 "portal": "pm",           "guidance_id": None},
    {"id": "asset-transfers",       "label": "Asset Transfers",                "portal": "pm",           "guidance_id": None},
    {"id": "hr-time-off",           "label": "HR Time-Off Requests",           "portal": "hr",           "guidance_id": None},
    {"id": "shop-parts-catalog",    "label": "Shop Parts Catalog & Order",     "portal": "shop",         "guidance_id": None},
    {"id": "public-jha-ref",        "label": "Public JHA Reference",           "portal": "public",       "guidance_id": None},
    {"id": "public-trench-ref",     "label": "Public Trench Box Reference",    "portal": "public",       "guidance_id": None},
    {"id": "public-cheatsheet",     "label": "Public Cheat Sheet",             "portal": "public",       "guidance_id": None},
]


# ─────────────────────────────────────────────────────────────────────
# 10-field matrix computation
# ─────────────────────────────────────────────────────────────────────

_STATUS_VALUES = {"complete", "partial", "missing", "n/a", "deferred"}


def _articles_by_scope(scope: str) -> list[dict]:
    """Articles tagged with the given scope (excludes admin-only credit
    unless the scope itself is admin — same convention as
    coverage_report)."""
    out = []
    for a in _ARTICLES:
        if scope in (a.get("scopes") or []):
            out.append(a)
    return out


def _has_section(scope: str, section: str) -> bool:
    """True if at least one article exists in (scope, section)."""
    for a in _articles_by_scope(scope):
        if a.get("section") == section:
            return True
    return False


def _troubleshooting_for(scope: str) -> int:
    """Count of troubleshooting articles visible to this scope."""
    n = 0
    for a in _articles_by_scope(scope):
        if a.get("section") == "troubleshooting":
            n += 1
    return n


def _onboarding_for(scope: str) -> int:
    n = 0
    for a in _articles_by_scope(scope):
        if a.get("section") == "onboarding":
            n += 1
    return n


def _why_for(scope: str) -> int:
    n = 0
    for a in _articles_by_scope(scope):
        if a.get("section") == "knowledge":
            n += 1
    return n


# Translation readiness is computed solely by the presence of `body_es`
# and `title_es` on each article. Today these are absent across the
# board — that's the Pass 3 schema work. We emit the metric now so the
# governance dashboard can track progress as Pass 3 lands incrementally.
def _has_translation(article: dict) -> bool:
    return bool(article.get("title_es")) and bool(article.get("body_es"))


def _translation_pct_for(scope: str) -> float:
    arts = _articles_by_scope(scope)
    if not arts:
        return 0.0
    n = sum(1 for a in arts if _has_translation(a))
    return round(100.0 * n / len(arts), 1)


# ─────────────────────────────────────────────────────────────────────
# Portal matrix
# ─────────────────────────────────────────────────────────────────────

def compute_portal_matrix() -> list[dict]:
    rows: list[dict] = []
    for p in PORTALS:
        scope = p["scope"]
        articles = _articles_by_scope(scope)
        article_count = len(articles)

        # Field 2 — login_required
        if scope == "public":
            f_login = {"status": "n/a", "detail": "Public — no login"}
        elif p.get("login_url") is None:
            f_login = {"status": "partial",
                       "detail": p.get("anomaly") or "No /<portal>/login route"}
        else:
            f_login = {"status": "complete", "detail": p["login_url"]}

        # Field 3 — guidance_exists
        if article_count == 0:
            f_guide = {"status": "missing", "detail": "0 articles for this scope"}
        elif article_count < 3:
            f_guide = {"status": "partial", "detail": f"{article_count} articles"}
        else:
            f_guide = {"status": "complete", "detail": f"{article_count} articles"}

        # Field 4 — onboarding_exists
        ons = _onboarding_for(scope)
        if scope == "admin":
            f_onb = {"status": "partial", "detail": "Admin onboarding covered via admin-* articles, no first-week walk"}
        elif ons == 0:
            f_onb = {"status": "missing", "detail": "No onboarding article scoped to this portal"}
        elif ons < 2:
            f_onb = {"status": "partial", "detail": f"{ons} onboarding article"}
        else:
            f_onb = {"status": "complete", "detail": f"{ons} onboarding articles"}

        # Field 5 — contextual_help (WhyItMattersPanel embed presence)
        # Curated knowledge derived from the audit — Pass 2 captures the
        # current binding; later passes can replace this with a scan.
        ctxt_present = {
            "public": "partial", "hr": "partial", "safety": "complete",
            "shop": "partial", "dispatch": "missing", "pm": "complete",
            "leadership": "missing", "admin": "complete",
        }
        f_ctxt = {"status": ctxt_present.get(p["key"], "missing"),
                  "detail": "WhyItMattersPanel embed coverage per audit"}

        # Field 6 — why_explanation (knowledge section articles in scope)
        whys = _why_for(scope)
        if scope == "public":
            f_why = {"status": "complete" if whys >= 1 else "partial",
                     "detail": f"{whys} 'Why It Matters' articles"}
        elif whys == 0:
            f_why = {"status": "missing", "detail": "0 knowledge articles"}
        elif whys < 3:
            f_why = {"status": "partial", "detail": f"{whys} knowledge articles"}
        else:
            f_why = {"status": "complete", "detail": f"{whys} knowledge articles"}

        # Field 7 — troubleshooting
        ts = _troubleshooting_for(scope)
        if ts == 0:
            f_ts = {"status": "missing", "detail": "0 troubleshooting articles"}
        elif ts == 1:
            f_ts = {"status": "partial", "detail": "1 troubleshooting article"}
        else:
            f_ts = {"status": "complete", "detail": f"{ts} troubleshooting articles"}

        # Field 8 — discoverability
        if scope == "public":
            f_disc = {"status": "complete", "detail": "/guidance is public-rooted"}
        elif p.get("sign_in_listed"):
            f_disc = {"status": "complete", "detail": "/sign-in surfaces this portal"}
        elif p.get("login_url") is None:
            f_disc = {"status": "missing", "detail": "No /sign-in entry; no /<portal>/login"}
        else:
            f_disc = {"status": "partial",
                      "detail": f"Direct URL only — {p['login_url']}"}

        # Field 9 — mobile_ux (curated — to be promoted to scan later)
        mobile_status = {
            "public": "complete", "hr": "complete", "safety": "complete",
            "shop": "complete", "dispatch": "complete", "pm": "complete",
            "leadership": "partial", "admin": "complete",
        }
        f_mob = {"status": mobile_status.get(p["key"], "partial"),
                 "detail": "Mobile coverage per audit; formal scan pending"}

        # Field 10 — translation_readiness
        pct = _translation_pct_for(scope)
        if scope == "admin":
            f_trn = {"status": "n/a", "detail": "Admin console is intentionally English-only"}
        elif pct == 0:
            f_trn = {"status": "missing", "detail": "0% — body_es schema not landed"}
        elif pct < 80:
            f_trn = {"status": "partial", "detail": f"{pct}% of scope-{scope} articles translated"}
        else:
            f_trn = {"status": "complete", "detail": f"{pct}% translated"}

        rows.append({
            "portal": p["key"],
            "label": p["label"],
            "login_url": p.get("login_url"),
            "sign_in_listed": p.get("sign_in_listed", False),
            "purpose": p.get("purpose"),
            "article_count": article_count,
            "anomaly": p.get("anomaly"),
            "fields": {
                "who_uses_it":         {"status": "complete", "detail": _personas_for(p["key"])},
                "login_required":      f_login,
                "guidance_exists":     f_guide,
                "onboarding_exists":   f_onb,
                "contextual_help":     f_ctxt,
                "why_explanation":     f_why,
                "troubleshooting":     f_ts,
                "discoverability":     f_disc,
                "mobile_ux":           f_mob,
                "translation_readiness": f_trn,
            },
        })
    return rows


def _personas_for(portal_key: str) -> str:
    names = [u["label"] for u in USER_TYPES if u["primary_portal"] == portal_key]
    return " · ".join(names) if names else portal_key.title()


# ─────────────────────────────────────────────────────────────────────
# User-type matrix
# ─────────────────────────────────────────────────────────────────────

def compute_user_type_matrix() -> list[dict]:
    rows: list[dict] = []
    portal_by_key = {p["key"]: p for p in PORTALS}
    for u in USER_TYPES:
        primary = portal_by_key.get(u["primary_portal"], {})
        login_url = primary.get("login_url")
        # native articles count = articles in primary scope
        native = len(_articles_by_scope(u["primary_portal"]))
        # cross-portal article reach
        cross = sum(len(_articles_by_scope(s)) for s in u.get("cross_portal_reads") or [])
        if login_url is None and u["primary_portal"] != "public":
            disc = "missing"
            disc_detail = "Primary portal has no /<portal>/login"
        elif primary.get("sign_in_listed") or u["primary_portal"] == "public":
            disc = "complete"
            disc_detail = login_url or "Public landing"
        else:
            disc = "partial"
            disc_detail = "URL must be known"
        rows.append({
            "key": u["key"],
            "label": u["label"],
            "primary_portal": u["primary_portal"],
            "cross_portal_reads": u.get("cross_portal_reads") or [],
            "native_articles": native,
            "cross_portal_articles": cross,
            "fields": {
                "discoverability": {"status": disc, "detail": disc_detail},
                "guidance_exists": {"status": "complete" if native >= 3 else ("partial" if native > 0 else "missing"),
                                    "detail": f"{native} articles in primary scope"},
                "translation_readiness": {"status": "missing" if u["primary_portal"] != "admin" else "n/a",
                                          "detail": f"{_translation_pct_for(u['primary_portal'])}% translated"},
            },
        })
    return rows


# ─────────────────────────────────────────────────────────────────────
# Public route matrix
# ─────────────────────────────────────────────────────────────────────

def compute_public_route_matrix() -> list[dict]:
    article_ids = {a["id"] for a in _ARTICLES}
    rows: list[dict] = []
    for r in PUBLIC_ROUTES:
        gid = r.get("guidance_id")
        has = gid is not None and gid in article_ids
        rows.append({
            "route": r["route"],
            "purpose": r["purpose"],
            "guidance_id": gid,
            "has_guidance": has,
        })
    return rows


# ─────────────────────────────────────────────────────────────────────
# Cross-cutting workflow matrix
# ─────────────────────────────────────────────────────────────────────

def compute_workflow_matrix() -> list[dict]:
    """Cross-cutting workflows registered in INVENTORY_WORKFLOWS.

    These are NOT the per-portal _WORKFLOWS in guidance.content — those
    are exposed by /api/admin/guidance/workflow-coverage. This returns
    the extra workflows the audit identified as gaps that span portals
    or are operationally important but lacked any workflow registration.
    """
    article_ids = {a["id"] for a in _ARTICLES}
    rows: list[dict] = []
    for w in INVENTORY_WORKFLOWS:
        gid = w.get("guidance_id")
        has = gid is not None and gid in article_ids
        rows.append({
            "id": w["id"],
            "label": w["label"],
            "portal": w["portal"],
            "guidance_id": gid,
            "has_guidance": has,
        })
    return rows


# ─────────────────────────────────────────────────────────────────────
# Translation readiness (system-wide)
# ─────────────────────────────────────────────────────────────────────

def compute_translation_readiness() -> dict:
    total = len(_ARTICLES)
    title_n = sum(1 for a in _ARTICLES if a.get("title_es"))
    body_n  = sum(1 for a in _ARTICLES if a.get("body_es"))
    by_section: dict[str, dict] = {}
    for s in SECTIONS:
        sid = s["id"]
        arts = [a for a in _ARTICLES if a.get("section") == sid]
        n = len(arts)
        t = sum(1 for a in arts if a.get("title_es"))
        b = sum(1 for a in arts if a.get("body_es"))
        by_section[sid] = {
            "label": s["title"],
            "total": n,
            "title_es": t,
            "body_es": b,
            "pct_body": round(100.0 * b / n, 1) if n else 0.0,
        }
    by_scope: dict[str, dict] = {}
    for sc in ["public", "field", "leadership", "safety", "shop", "dispatch", "hr", "pm", "admin"]:
        arts = _articles_by_scope(sc)
        n = len(arts)
        t = sum(1 for a in arts if a.get("title_es"))
        b = sum(1 for a in arts if a.get("body_es"))
        by_scope[sc] = {
            "total": n,
            "title_es": t,
            "body_es": b,
            "pct_body": round(100.0 * b / n, 1) if n else 0.0,
        }
    return {
        "total_articles": total,
        "title_es_present": title_n,
        "body_es_present": body_n,
        "pct_title": round(100.0 * title_n / total, 1) if total else 0.0,
        "pct_body":  round(100.0 * body_n  / total, 1) if total else 0.0,
        "by_section": by_section,
        "by_scope": by_scope,
        "schema_landed": False,   # flipped to True once Pass 3 lands body_es
    }


# ─────────────────────────────────────────────────────────────────────
# Drift detection
# ─────────────────────────────────────────────────────────────────────

def compute_drift() -> dict:
    """Detect operational drift — new portals/articles/routes that lack
    required fields. This is the "did anything slip through?" signal.
    Returns a structured list of drift items by category, each with a
    severity and the file/area to look at.
    """
    items: list[dict] = []

    # 1. Portals with no login_url (structural anomaly)
    for p in PORTALS:
        if p["key"] == "public":
            continue
        if not p.get("login_url"):
            items.append({
                "severity": "p0",
                "category": "portal-without-login",
                "subject": p["key"],
                "message": f"Portal {p['key']} has no /<portal>/login route. {p.get('anomaly') or ''}".strip(),
                "fix_pass": "Pass 4 — Field Leadership portal door",
            })
        if not p.get("sign_in_listed") and p.get("login_url"):
            items.append({
                "severity": "p1",
                "category": "portal-not-in-signin",
                "subject": p["key"],
                "message": f"Portal {p['key']} has a login route but is not surfaced on /sign-in.",
                "fix_pass": "Pass 4 — /sign-in directory upgrade",
            })

    # 2. Public routes without a guidance article
    article_ids = {a["id"] for a in _ARTICLES}
    for r in PUBLIC_ROUTES:
        gid = r.get("guidance_id")
        if gid is None or gid not in article_ids:
            items.append({
                "severity": "p1" if r["route"] in ("/cheatsheet", "/jha", "/trench-boxes", "/sign-in") else "p2",
                "category": "public-route-without-guidance",
                "subject": r["route"],
                "message": f"Public route {r['route']} ({r['purpose']}) has no public guidance article.",
                "fix_pass": "Pass 6 — public route coverage",
            })

    # 3. Cross-cutting workflows without guidance
    for w in INVENTORY_WORKFLOWS:
        if not w.get("guidance_id") or w["guidance_id"] not in article_ids:
            items.append({
                "severity": "p1",
                "category": "workflow-without-guidance",
                "subject": w["id"],
                "message": f"Workflow '{w['label']}' ({w['portal']}) has no guidance article.",
                "fix_pass": "Pass 6 — cross-cutting workflow coverage",
            })

    # 4. Articles without translation (system-wide aggregate)
    untranslated = [a["id"] for a in _ARTICLES if not _has_translation(a)]
    if untranslated:
        items.append({
            "severity": "p0",
            "category": "translation-missing",
            "subject": "guidance-corpus",
            "message": f"{len(untranslated)}/{len(_ARTICLES)} guidance articles have no Spanish translation (body_es).",
            "fix_pass": "Pass 3 — translation architecture + content",
        })

    # 5. Portal scopes with zero onboarding articles (excluding public/admin)
    for p in PORTALS:
        if p["key"] in ("public", "admin"):
            continue
        if _onboarding_for(p["scope"]) == 0:
            items.append({
                "severity": "p1",
                "category": "portal-no-onboarding",
                "subject": p["key"],
                "message": f"Portal {p['key']} has no scope-specific onboarding article (no first-week walk).",
                "fix_pass": "Pass 5 — persona onboarding",
            })

    # Aggregate counts
    by_severity = {"p0": 0, "p1": 0, "p2": 0}
    for it in items:
        sev = it.get("severity", "p2")
        if sev in by_severity:
            by_severity[sev] += 1

    return {
        "items": items,
        "total": len(items),
        "by_severity": by_severity,
    }


# ─────────────────────────────────────────────────────────────────────
# Top-level snapshot
# ─────────────────────────────────────────────────────────────────────

def compute_full_inventory() -> dict:
    """Top-level snapshot the dashboard renders. Pure registry inspection;
    never touches DB; never reads PII."""
    return {
        "version": 1,
        "audit_doc": "/app/docs/OPERATIONAL_INVENTORY.md",
        "generated_pass": 2,
        "totals": {
            "portals": len(PORTALS),
            "user_types": len(USER_TYPES),
            "public_routes": len(PUBLIC_ROUTES),
            "cross_cutting_workflows": len(INVENTORY_WORKFLOWS),
            "guidance_articles": len(_ARTICLES),
            "per_portal_workflows": len(_WORKFLOWS),
        },
        "portals": compute_portal_matrix(),
        "user_types": compute_user_type_matrix(),
        "public_routes": compute_public_route_matrix(),
        "workflows": compute_workflow_matrix(),
        "translation": compute_translation_readiness(),
        "drift": compute_drift(),
    }
