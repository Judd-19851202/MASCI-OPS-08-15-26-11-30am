"""
MASCI Project Manager → Job auto-routing.

DB-BACKED (2026-04-30): the source of truth is now `db.jobs_master.pm_email`
combined with `db.project_managers`. The legacy hardcoded PM_TABLE is kept
ONLY as a synchronous fallback for code paths that don't have a DB handle
(rare); every production code path now resolves PMs via the DB.

To change a job's PM:
  • Open /admin → "Active Jobs Master" → click the PM cell → pick from dropdown.

To add a new PM:
  • Open /admin → "Project Managers" → "+ Add PM" → fill name + email.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Legacy fallback table (used ONLY when no DB lookup is wired in for the
# caller). New code paths should call resolve_pm_for_record_async() with
# the live `db` handle.
# ---------------------------------------------------------------------------
PM_TABLE: Dict[str, Dict[str, object]] = {
    "David Jewett":     {"email": "davidjewett@mascigc.com",     "jobs": []},
    "Chris Wright":     {"email": "chriswright@mascigc.com",     "jobs": []},
    "Ramon Rodriguez":  {"email": "RamonRodriguez@mascigc.com",  "jobs": []},
    "Jaymn Judd":       {"email": "jaymn.judd@mascigc.com",      "jobs": []},
}


# Always copied on every COMPLIANCE form (Site Inspection, Safety Meeting,
# JHP, Incident Report). These are the four legal/compliance forms that the
# office needs a copy of. Daily Job Reports and Equipment Pre-Op Inspections
# are operational forms — they go to the assigned PM only (no office CC).
ALWAYS_CC: List[str] = [
    "jaymn.judd@mascigc.com",
    "safety@mascigc.com",
]

# Kinds that get the always-CC pair (compliance docs).
COMPLIANCE_KINDS = {"inspection", "meeting", "jha", "incident"}

# Kinds that DO NOT get the always-CC — only the assigned PM. Operational docs.
PM_ONLY_KINDS = {"daily-report", "equipment-inspection"}


def _normalize_job_number(raw: str) -> str:
    """Lowercase, strip whitespace, collapse spaces around the dash."""
    if not raw:
        return ""
    s = str(raw).strip().lower()
    s = s.replace(" - ", "-").replace(" -", "-").replace("- ", "-")
    s = s.replace(" ", "")
    return s


# ---------------------------------------------------------------------------
# DB-backed lookup (the canonical path)
# ---------------------------------------------------------------------------
async def resolve_pm_for_record_async(
    db, record: dict
) -> Optional[Tuple[str, str]]:
    """
    Resolve a PM by querying jobs_master + project_managers.
    Returns (pm_name, pm_email) or None.

    Resolution order:
      1. Match record.project_number (normalized) against jobs_master.
         If the job has pm_email set, use that PM.
         If only project_manager (name) is set, look up the PM by name.
      2. Fallback: prefix match on project_number (so "25-01" matches "25-01-CP").
      3. Final fallback: legacy hardcoded PM_TABLE name match (covers any
         job not yet in jobs_master).
    """
    if not record:
        return None

    pn_raw = (record.get("project_number") or "").strip()
    pn_norm = _normalize_job_number(pn_raw)
    if not pn_norm:
        return None

    # Try exact match first (case-insensitive on project_number)
    job = await db.jobs_master.find_one(
        {"project_number": {"$regex": f"^{_re_escape(pn_raw)}$", "$options": "i"}},
        {"_id": 0},
    )

    # Try normalized prefix match if exact failed
    if not job:
        # Mongo can't normalize on its own — fetch all and match in Python.
        # Cheap because jobs_master is small (~30 rows).
        cursor = db.jobs_master.find({}, {"_id": 0})
        async for j in cursor:
            stored = _normalize_job_number(j.get("project_number") or "")
            if not stored:
                continue
            if stored == pn_norm:
                job = j
                break
            # Prefix-match — strip any "-cp" tail on either side
            stem_a = pn_norm.split("-cp")[0]
            stem_b = stored.split("-cp")[0]
            if stem_a and stem_a == stem_b:
                job = j
                break

    if job:
        # Prefer pm_email (canonical key) if present
        pm_email = (job.get("pm_email") or "").strip().lower()
        if pm_email:
            pm_doc = await db.project_managers.find_one(
                {"email": pm_email}, {"_id": 0}
            )
            if pm_doc:
                return (pm_doc.get("name") or "", pm_doc.get("email") or "")
            # PM email on job but no PM record — return raw email anyway.
            return (job.get("project_manager") or "", pm_email)
        # No pm_email — fall back to project_manager (name) → PM lookup
        pm_name = (job.get("project_manager") or "").strip()
        if pm_name:
            pm_doc = await db.project_managers.find_one(
                {"name": pm_name}, {"_id": 0}
            )
            if pm_doc:
                return (pm_doc.get("name") or "", pm_doc.get("email") or "")
            # Try the legacy hardcoded table as a final fallback
            if pm_name in PM_TABLE:
                return (pm_name, str(PM_TABLE[pm_name]["email"]))

    # Final fallback — legacy table by name (project_name string match)
    rec_name = (record.get("project_name") or "").strip().lower()
    if rec_name:
        for pm_name, data in PM_TABLE.items():
            jobs = data.get("jobs") or []
            for _, jn in jobs:  # type: ignore[union-attr]
                if jn.lower()[:25] in rec_name or rec_name[:25] in jn.lower():
                    return (pm_name, str(data["email"]))

    return None


def _re_escape(s: str) -> str:
    """Tiny re.escape replacement to avoid the import cost on hot path."""
    import re
    return re.escape(s)


async def recipients_for_record_async(
    db, record: dict, kind: Optional[str] = None
) -> Dict[str, object]:
    """
    DB-backed distribution list builder.

    Routing rules (per user spec, 2026-02-26 + co-PM expansion 2026-05-05):
      • Compliance kinds (inspection/meeting/jha/incident):
          Primary PM + ALL co-PMs assigned to the job + ALWAYS_CC
          (jaymn.judd + safety@). Office must keep a copy.
      • Operational kinds (daily-report / equipment-inspection):
          Primary PM + co-PMs ONLY (no office CC). Co-PMs are CC'd; the
          primary stays in To: so the email thread visibly belongs to
          them. Exception: if Jaymn IS the primary, he gets it as PM.

    Returns: {pm_name, pm_email, co_pm_emails[], to[], cc[], all[]}.
    """
    pm = await resolve_pm_for_record_async(db, record)
    pm_name, pm_email = (pm if pm else (None, None))

    # Pull the matching job again so we can grab co_pm_emails. resolve_pm_*
    # already did this lookup but didn't return the doc; cheap to re-fetch.
    co_pm_emails: List[str] = []
    pn_raw = (record.get("project_number") or "").strip()
    if pn_raw:
        job = await db.jobs_master.find_one(
            {"project_number": {"$regex": f"^{_re_escape(pn_raw)}$", "$options": "i"}},
            {"_id": 0, "co_pm_emails": 1},
        )
        if not job:
            # Fallback: normalized scan (rare path)
            pn_norm = _normalize_job_number(pn_raw)
            cursor = db.jobs_master.find({}, {"_id": 0, "project_number": 1, "co_pm_emails": 1})
            async for j in cursor:
                if _normalize_job_number(j.get("project_number") or "") == pn_norm:
                    job = j
                    break
        if job:
            raw_co = job.get("co_pm_emails") or []
            if isinstance(raw_co, list):
                primary_lower = (pm_email or "").lower()
                seen = {primary_lower} if primary_lower else set()
                for e in raw_co:
                    if not isinstance(e, str):
                        continue
                    em = e.strip().lower()
                    if em and em not in seen:
                        seen.add(em)
                        co_pm_emails.append(em)

    is_pm_only = kind in PM_ONLY_KINDS

    to: List[str] = []
    if pm_email:
        to.append(pm_email)

    if is_pm_only:
        # Co-PMs ride along on operational reports — primary remains To:,
        # co-PMs become CC: so the email thread visibly belongs to the
        # primary but every assigned PM still gets a copy.
        cc: List[str] = list(co_pm_emails)
        if not to:
            # No primary PM resolved — default office address.
            to = ["jaymn.judd@mascigc.com"]
    else:
        # Compliance kinds: co-PMs FIRST, then office CC. De-dup the
        # always-cc list against both the primary and the co-PMs so
        # ``cc`` never carries the same address twice (cosmetic — Resend
        # would de-dup again at transport, but a clean preview makes
        # debugging routing rules easier).
        seen_for_cc = {(pm_email or "").lower()} | {e.lower() for e in co_pm_emails}
        cc = list(co_pm_emails)
        # Pull the live always-CC from the DB-backed admin override; falls
        # back to the module-level env default when no override exists.
        try:
            from email_routing import get_value as _routing_get
            always_cc_dynamic = await _routing_get(db, "always_cc")
            if not isinstance(always_cc_dynamic, list):
                always_cc_dynamic = ALWAYS_CC
        except Exception:
            always_cc_dynamic = ALWAYS_CC
        for e in always_cc_dynamic:
            if not e:
                continue
            if e.lower() in seen_for_cc:
                continue
            seen_for_cc.add(e.lower())
            cc.append(e)
        if not to:
            to = cc[:]
            cc = []

    seen = set()
    all_unique: List[str] = []
    for e in to + cc:
        k = e.lower()
        if k not in seen:
            seen.add(k)
            all_unique.append(e)

    extra = record.get("distribution_list") or []
    if isinstance(extra, list):
        for e in extra:
            if not isinstance(e, str):
                continue
            e = e.strip()
            if not e:
                continue
            if e.lower() not in seen:
                seen.add(e.lower())
                all_unique.append(e)
                cc.append(e)

    return {
        "pm_name": pm_name,
        "pm_email": pm_email,
        "co_pm_emails": co_pm_emails,
        "to": to,
        "cc": cc,
        "all": all_unique,
    }


# ---------------------------------------------------------------------------
# LEGACY synchronous helpers — kept for any code that calls them directly.
# These now return a stub from PM_TABLE only. New code should use the async
# DB-backed helpers above.
# ---------------------------------------------------------------------------
def find_pm_for_record(record: dict) -> Optional[Tuple[str, str]]:
    """Legacy sync fallback. Returns None unless the project_name happens
    to match one of the 4 hardcoded PM names — only used by
    /api/auto-email/preview which has been kept for backwards-compat."""
    return None


def recipients_for_record(record: dict, kind: Optional[str] = None) -> Dict[str, object]:
    """Legacy sync fallback. Always returns the office distribution as
    primary because we can't resolve the PM without a DB handle."""
    is_pm_only = kind in PM_ONLY_KINDS
    if is_pm_only:
        to = ["jaymn.judd@mascigc.com"]
        cc: List[str] = []
    else:
        to = ALWAYS_CC[:]
        cc = []

    extra = record.get("distribution_list") or []
    if isinstance(extra, list):
        seen = {e.lower() for e in to}
        for e in extra:
            if isinstance(e, str) and e.strip() and e.strip().lower() not in seen:
                cc.append(e.strip())
                seen.add(e.strip().lower())

    return {
        "pm_name": None,
        "pm_email": None,
        "to": to,
        "cc": cc,
        "all": to + cc,
    }


def auto_email_enabled() -> bool:
    if not os.environ.get("RESEND_API_KEY", "").strip():
        return False
    flag = os.environ.get("AUTO_EMAIL_REPORTS", "").strip().lower()
    if flag in ("false", "0", "no", "off"):
        return False
    return True
