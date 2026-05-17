"""
backend/guidance — Operational Guidance Center content + RBAC routes.

Phase A scope (preview only):
  • RBAC-aware content registry (in-code Python modules)
  • Server endpoints: catalog · article-by-id · search
  • Visibility computed server-side per request, based on the caller's
    portal tokens. Search and article-fetch refuse anything the caller
    cannot see; titles of restricted articles are NEVER leaked.

The frontend mirrors a static skeleton (cards / shell / section names)
but trusts THIS module as the source of truth for which articles
actually exist for the caller's tier set.
"""
