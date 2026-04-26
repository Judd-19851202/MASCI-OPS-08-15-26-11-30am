"""
MASCI Project Manager → Job auto-routing table.

Source of truth: PM Job List.pdf provided by the user (Feb 2026).
On every safety form submit (Inspection / Meeting / JHA / Incident / Daily Report)
we look up the PM by project_number (preferred) or by job-name fragment, then
auto-email the PDF to that PM plus the always-CC distribution list.

To add / change PMs, edit the PM_TABLE below. Job numbers are matched
case-insensitive on the leading prefix (so "25-01 - CP" matches "25-01-cp"
and a typed "25-01" also resolves to David Jewett — first match wins).
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# PM table — { pm_name: { "email": str, "jobs": [(job_number, job_name), ...] } }
# ---------------------------------------------------------------------------
PM_TABLE: Dict[str, Dict[str, object]] = {
    "David Jewett": {
        "email": "davidjewett@mascigc.com",
        "jobs": [
            ("20-07", "T5686 SR 15/SR600 (SANFORD, 17/92, LAKE MARY)"),
            ("21-06", "T5736 Oveido - (426, BROADWAY)"),
            ("22-08", "T5749 SR 436 (ALTAMONTE SPRINGS)"),
            ("24-06", "T5824 - SR 46 (W 1ST ST.)"),
            ("24-08", "E57B2 - SR 46 (MELLONVILLE AVE)"),
            ("24-12", "CC5744 - OXFORD RD Improvements (OXFORD)"),
            ("25-01-CP", "T5832 - SR430 (Mason Ave)"),
            ("25-03", "Vol.Co Resurface"),
            ("25-04", "Oxford Rd Surcharge Utility"),
            ("25-08", "T5838 SR 500 (US441) (Mt Dora)"),
            ("25-10", "Pavement Management Services"),
            ("25-14", "E8V62, Resurf Seminole Expressway (SR 417)"),
            ("26-02", "Resurfacing Phase I"),
            ("26-03-CP", "T5874 - SR 426 Winterhaven/Aloma"),
            ("26-04", "E58F7-SR 5"),
        ],
    },
    "Chris Wright": {
        "email": "chriswright@mascigc.com",
        "jobs": [
            ("24-13-CP", "T5841 - SR 401 (Brevard Co, Cape Canaveral)"),
            ("25-12", "N. Atlantic Ave - Drainage"),
            ("25-13", "N. Atlantic Ave - Watermain Replacement"),
            ("25-15", "E53F1 - SR 404, Brevard Co (Pineda)"),
            ("25-21", "SJR2C - Loop Trail - Spruce Creek"),
            ("26-01-CP", "NSB Corbin Park Stormwater Improvements"),
            ("26-07", "University High Parent Loop Ext"),
            ("26-09-CP", "T5871 Sub to CARR"),
        ],
    },
    "Ramon Rodriguez": {
        "email": "RamonRodriguez@mascigc.com",
        "jobs": [
            ("25-02", "E53F5 - SR 5 (Titusville)"),
            ("25-16-CP", "T5842 - SR 600 Volusia County (Orange City)"),
            ("25-22-CP", "T5860 SR 9 (I-95)"),
            ("25-24-CP", "G2 & G11 Canal St Improvement"),
        ],
    },
    "Jaymn Judd": {
        "email": "jaymn.judd@mascigc.com",
        "jobs": [
            ("26-06", "Knox McRae Master Pump Station"),
        ],
    },
}


# Always copied on every report (office + safety inbox).
ALWAYS_CC: List[str] = [
    "jaymn.judd@mascigc.com",
    "safety@mascigc.com",
]


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def _normalize_job_number(raw: str) -> str:
    """Lowercase, strip whitespace, collapse spaces around the dash."""
    if not raw:
        return ""
    s = str(raw).strip().lower()
    # "25-01 - cp" → "25-01-cp"
    s = s.replace(" - ", "-").replace(" -", "-").replace("- ", "-")
    s = s.replace(" ", "")
    return s


# Pre-build a fast lookup index { normalized_job_number: (pm_name, pm_email) }
_INDEX: Dict[str, Tuple[str, str]] = {}
for _pm, _data in PM_TABLE.items():
    _email = str(_data["email"])
    for _num, _ in _data["jobs"]:  # type: ignore[union-attr]
        _INDEX[_normalize_job_number(_num)] = (_pm, _email)


def find_pm_for_record(record: dict) -> Optional[Tuple[str, str]]:
    """
    Resolve a PM by inspecting a safety record dict.
    Returns (pm_name, pm_email) or None if no match.

    Lookup priority:
      1. record["project_number"] exact normalized match.
      2. record["project_number"] prefix match (so "25-01" matches "25-01-CP").
      3. record["project_name"] starts-with against any PM's job names.
    """
    if not record:
        return None

    num = _normalize_job_number(record.get("project_number") or "")
    if num and num in _INDEX:
        return _INDEX[num]

    # Prefix match — strip trailing "-cp" from BOTH sides
    if num:
        num_stem = num.split("-cp")[0]
        for key, val in _INDEX.items():
            key_stem = key.split("-cp")[0]
            if num_stem and key_stem and num_stem == key_stem:
                return val

    # Fallback by project name (best-effort)
    name = (record.get("project_name") or "").strip().lower()
    if name:
        for pm, data in PM_TABLE.items():
            for _, jn in data["jobs"]:  # type: ignore[union-attr]
                if jn.lower()[:25] in name or name[:25] in jn.lower():
                    return (pm, str(data["email"]))

    return None


def recipients_for_record(record: dict) -> Dict[str, object]:
    """
    Build the full distribution list for a record.
    Returns:
      {
        "pm_name": str | None,
        "pm_email": str | None,
        "to":  [pm_email]            (primary recipients)
        "cc":  ALWAYS_CC minus duplicates
        "all": deduped list of every email
      }
    """
    pm = find_pm_for_record(record)
    pm_name, pm_email = (pm if pm else (None, None))

    to: List[str] = []
    if pm_email:
        to.append(pm_email)

    cc = [e for e in ALWAYS_CC if e and (not pm_email or e.lower() != pm_email.lower())]
    # If no PM resolved, the always-CC becomes the primary "to" list so the
    # report still lands somewhere (Jaymn + safety@).
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

    return {
        "pm_name": pm_name,
        "pm_email": pm_email,
        "to": to,
        "cc": cc,
        "all": all_unique,
    }


def auto_email_enabled() -> bool:
    """True only when Resend is configured AND auto-dispatch hasn't been
    explicitly disabled via env (`AUTO_EMAIL_REPORTS=false`)."""
    if os.environ.get("AUTO_EMAIL_REPORTS", "true").strip().lower() in (
        "false",
        "0",
        "no",
        "off",
    ):
        return False
    return bool(os.environ.get("RESEND_API_KEY", "").strip())
