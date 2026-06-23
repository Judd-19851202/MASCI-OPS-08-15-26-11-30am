# TRACK 15.70 · Configuration Audit (Phase 2)

_Generated 2026-06-22_

## Method

Grep of `/app/backend/**/*.py` for `mascigc.com`, `mascidocs.com`, `"MASCI"`, and `MASCI Operations Platform` — focused on **deployment-critical paths**: auth, onboarding, provisioning, routing, deployment scripts. Allowed/Blocked/Tech-Debt classification per occurrence.

## Findings (Deployment-Critical Paths Only)

| Path | Code | Class | Reason |
|---|---|:-:|---|
| `auth.py:59-63` | hardcoded MASCI owner-seed emails (5 entries) | 🔴 **BLOCKED for shared-cluster** · 🟡 **TECH-DEBT for separate-cluster** | Seeds MASCI accounts into any database the backend boots against. Must be gated by tenant-key OR env override. Currently runs unconditionally on startup. |
| `branding_resolver.py:89` | `from_display_name="MASCI Operations Platform"` (env fallback) | 🟡 **TECH-DEBT** | Only fires when `is_masci(tk)` and `tenant_branding.from_email` is unset. Acceptable for MASCI; non-MASCI tenant skips this branch entirely (verified in FM3 test). |
| `server.py:73` | `FastAPI(title="MASCI Job Site Safety Inspection API")` | ✅ **ALLOWED** | OpenAPI doc title only. Not customer-visible. Could be parameterised but low-priority. |
| `server.py:2384, 3719` | `f"MASCI Operations Platform <{sender_email}>"` From line | 🔴 **BLOCKED** | Two send sites bypass `branding_resolver.format_from_field()`. For Customer #2 deployment, emails would carry "MASCI Operations Platform <noreply@customer2.example>" as From — visible leak. **Must fix before Customer #2 go-live.** |
| `server.py:1490` | `"MASCI Operations Platform — Source Bundle"` | 🟡 **TECH-DEBT** | Admin-tier source-bundle export subject. Admin-only context. |
| `server.py:5437` | `"MASCI Hub — Full Backup"` email subject | 🟡 **TECH-DEBT** | Operator-only context. Backup-success notification. Should be tenant-aware. |
| `server.py:5439` | `"Source: mascidocs.com (production)"` | 🟡 **TECH-DEBT** | Operator-only context. |
| `server.py:4910` | `payload.get("company") or "MASCI"` (data-seed fallback) | 🟡 **TECH-DEBT** | One legacy data-seed fallback. Track 15.68C migrated most; this one missed. |
| `server.py:5354` | `record.get("project_name") or "MASCI"` (export filename fallback) | 🟡 **TECH-DEBT** | Filename fallback when project_name is missing. Should use `branding.slug`. |
| `routes/auth_directory_routes.py:114` | `os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com")` (invite link base) | 🟡 **TECH-DEBT** | Env-overridable; default falls back to MASCI URL. For Customer #2 deployment, `PUBLIC_APP_URL` must be set per-deploy. Reasonable behavior. |
| `tenant_context.py:18` | docstring example `acme.mascidocs.com` | ✅ **ALLOWED** | Documentation example. Not code. |

## Classification Summary

| Class | Count | Customer-Visible? | Action |
|---|---:|:-:|---|
| 🔴 **BLOCKED** | 3 | YES (2 in email From; 1 in user seed for shared-cluster) | Must fix before Customer #2 go-live |
| 🟡 **TECH-DEBT** | 7 | partial (mostly admin/operator surfaces) | Fix in Track 16.x |
| ✅ **ALLOWED** | 2 | NO | OK as-is |
| Other (in `/scripts/`, `/tests/`, comments, historical) | 169 | NO | Out of deployment-critical scope |

## Hardcoded References Outside Deployment-Critical Paths

A wider grep found 179 references in `/app/backend/**/*.py` (excluding `/scripts/` and `/tests/`). The vast majority are:

- Comments / docstrings (out of scope)
- Test fixtures (intentional)
- Email body templates (admin-tier only)
- Sample-data references (e.g., "MASCI Crews on Site" in legacy code)
- Backup/historical migration code

These are **Tier-2 deep-content** items captured in `ROADMAP.md`.

## Blocked-Item Remediation Sketch

### B1 · `auth.py:59-63` hardcoded MASCI owner seed

**Required change**:

```python
# Before
SEED_OWNERS = [
    ("david.jewett@mascigc.com", "David Jewett", "owner"),
    ...
]

# After
SEED_OWNERS_RAW = os.environ.get("AUTH_SEED_OWNERS", "")
if SEED_OWNERS_RAW:
    SEED_OWNERS = [parse_owner_line(l) for l in SEED_OWNERS_RAW.split("|") if l.strip()]
elif tenant_key == "masci":
    SEED_OWNERS = [
        ("david.jewett@mascigc.com", "David Jewett", "owner"),
        ...   # current MASCI defaults
    ]
else:
    SEED_OWNERS = []  # refuse to seed MASCI users into non-MASCI tenant
```

~10 LOC change. Same refusal pattern as Track 15.68C's safety/shop/hr seeds.

### B2 · `server.py:2384, 3719` hardcoded From: name

**Required change**:

```python
# Before
"from": f"MASCI Operations Platform <{sender_email}>",

# After
from branding_resolver import resolve_sender, format_from_field
sender = await resolve_sender(db)
"from": format_from_field(sender),
```

~6 LOC change at each of the 2 sites.

## Verdict

⚠️ **PARTIAL PASS** — Deployment-critical hardcoded references are
**enumerated and classified**. **3 BLOCKED items must be fixed before
Customer #2 go-live**; 7 TECH-DEBT items are non-blocking but should be
scheduled. **No hardcoded references in the resolver, parity, or
routing engine itself.**

For the purposes of Track 15.70 (deployment readiness CERTIFICATION,
not deployment EXECUTION), this honestly maps where the gaps are.
Customer #2 go-live requires the 3 BLOCKED items to be addressed in a
follow-up Track 15.71 or Track 16.x.
