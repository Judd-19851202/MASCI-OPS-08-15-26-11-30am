#!/usr/bin/env python3
"""scan_production_contamination.py

P0 PRODUCTION CONTAMINATION SCAN — iter437 · 2026-02 post-deploy

READ-ONLY scan of the `masci_safety` (production) database for
records that look like test/preview/contaminated content. Outputs a
candidate report to /app/memory/PROD_CONTAMINATION_CANDIDATES.md.

DOES NOT DELETE ANYTHING. Per operator directive:
  > Do NOT randomly delete records manually.
  > Produce a cleanup candidate report BEFORE deletion.

How it works:
  * Connects to the production DB using the cluster MONGO_URL from
    /app/backend/.env, switching only DB_NAME to `masci_safety`.
  * Scans each target collection for records matching either:
      A. Time-based contamination window (default: last 48 h UTC)
      B. Content-based test markers (regex over chosen fields)
  * Captures: collection · count · earliest/latest created_at · 3
    sample IDs · reason flagged · safe-to-delete confidence.

Confidence rubric:
  HIGH      — record name/title contains explicit "pw-phase", "sigma",
              "iter", "Phase Sigma-III Test", "Test Mechanic", etc.
  MEDIUM    — record created in window AND has secondary test marker
              (e.g., T-SIGMA3 project number)
  LOW       — record created in window but no test marker (could be
              real production activity that happened during the window)

Usage:
  python3 /app/scripts/scan_production_contamination.py             # last 48h
  python3 /app/scripts/scan_production_contamination.py --hours 24  # window override
  python3 /app/scripts/scan_production_contamination.py --since "2026-05-27T00:00:00+00:00"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


# ─── Env bootstrap ──────────────────────────────────────────────────
def _load_env() -> None:
    env_path = Path("/app/backend/.env")
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
PROD_DB = "masci_safety"
PREVIEW_DB = "masci_safety_preview"
assert os.environ["MONGO_URL"]
assert os.environ.get("DB_NAME") == PREVIEW_DB, (
    "Refusing to run from a non-preview pod — this is a safety check."
)

# ─── Test markers (case-insensitive regex over chosen string fields) ─
TEST_MARKER_PATTERNS: List[str] = [
    r"pw-phase",          # Playwright Phase 1/2/3 markers
    r"pw-phase3-flow",    # Phase III specifically
    r"sigma-?i+",         # Sigma-I, Sigma-II, Sigma-III
    r"sigma3",
    r"phase[\s\-_]*sigma",
    r"\bT-SIGMA3\b",      # Phase III test project number
    r"Phase Sigma-III Test",
    r"Phase Sigma-III Public Form Cert",
    r"Phase Sigma-III Inspector",
    r"Phase Sigma-III Foreman",
    r"test\s*mechanic",
    r"testmech@",
    r"playwright",
    r"smoke[-_\s]?test",
    r"\bdummy\b",
    r"\bfake\b",
    r"placeholder",
    r"\bbrand[\s\-_]*check\b",
    r"\bDEPLOY_SMOKE\b",  # iter437 backfill marker
    # User-reported markers (notification surface)
    r"\bTST-[A-Z0-9]+",   # TST-IT24, TST-001, TST-A23-* — test equipment IDs
    r"\bPE-[a-f0-9]{6,}", # PE-be1b865f, PE-304144c7 — preview equipment IDs
]
_TEST_RX = re.compile("|".join(TEST_MARKER_PATTERNS), re.IGNORECASE)

# Fields we IGNORE for marker matching (they carry legitimate iter
# metadata or path strings that would false-positive otherwise).
SKIP_FIELDS_FOR_MARKER: set = {
    "_rewrite_iter",       # iter437 idempotency patch metadata
    "path",                # /api/* paths trip "iter437" if we stored old iters
    "namespace",
    "kind",                # noisy
}


def _str_fields(doc: Dict[str, Any], path: str = "") -> Iterable[Tuple[str, str]]:
    """Yield (field_path, value) pairs of string values worth scanning."""
    for k, v in doc.items():
        if k in SKIP_FIELDS_FOR_MARKER:
            continue
        full = f"{path}.{k}" if path else k
        if isinstance(v, str) and len(v) < 500:
            yield full, v
        elif isinstance(v, dict):
            yield from _str_fields(v, full)


def _has_test_marker(doc: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (matched, reason). reason is the first matching pattern + field."""
    for fpath, s in _str_fields(doc):
        m = _TEST_RX.search(s)
        if m:
            return True, f"{fpath}~/{m.group(0)}/"
    return False, ""


def _normalize_dt(v: Any) -> str:
    if v is None:
        return "(missing)"
    if isinstance(v, datetime):
        return v.replace(tzinfo=v.tzinfo or timezone.utc).isoformat()
    return str(v)


# ─── Target collections + field hints ───────────────────────────────
# 'date_fields' = first field tried for the time window
# 'sample_fields' = fields included verbatim in the report sample
TARGETS: List[Tuple[str, List[str], List[str], str]] = [
    # (collection, date_field_candidates, sample_field_candidates, description)
    ("notifications",
     ["created_at"],
     ["id", "type", "title", "recipient_role", "linked_equipment_id"],
     "Bell notifications. Operator reported junk preview/test entries this morning. Scans ALL notifications for TST-* / PE-* equipment IDs."),
    ("field_leadership_records",
     ["created_at"],
     ["id", "kind", "employee_name", "details.hr_decision.status"],
     "Time-off requests + other field-leadership records. Kind filter applied in candidates."),
    ("time_off_public_links",
     ["created_at"],
     ["id", "employee_name", "created_by", "used_record_id"],
     "Public time-off submission tokens. Look for test names."),
    ("daily_reports",
     ["created_at", "report_date"],
     ["id", "project_number", "project_name", "prepared_by", "general_notes"],
     "Daily reports. Phase Sigma-III tests use general_notes='pw-phase3-flow8-*'."),
    ("meetings",
     ["created_at", "meeting_date"],
     ["id", "project_number", "project_name", "topic", "conducted_by", "discussion_notes"],
     "Safety meetings. Phase Sigma-III tests use 'pw-phase3-flow13/15-meeting-*' markers."),
    ("incidents",
     ["created_at", "incident_date"],
     ["id", "project_number", "incident_type", "reported_by", "description"],
     "Incidents. Phase Sigma-III tests use 'pw-phase3-flow13-incident-*' markers."),
    ("inspections",
     ["created_at", "inspection_date"],
     ["id", "project_number", "project_name", "inspector_name", "work_activity"],
     "Inspections. Preview seed legacy may have leaked under iter319."),
    ("idempotency_keys",
     ["created_at"],
     ["key", "method", "path", "user_role"],
     "Idempotency cache. Test keys would show test_user_id or 127.0.0.1 origin."),
    ("audit_events",
     ["created_at"],
     ["id", "event", "actor", "actor_email"],
     "Generic audit log. Test logins would show up as actor_email=testmech."),
    ("admin_audit",
     ["created_at"],
     ["actor", "action", "target"],
     "Admin mutation audit log."),
    ("admin_audit_log",
     ["created_at"],
     ["actor", "action", "target_id"],
     "Newer admin audit (iter172+)."),
    ("dispatch_state_events",
     ["created_at"],
     ["id", "event", "driver_id", "actor"],
     "Dispatch state machine events."),
    ("operations_events",
     ["created_at"],
     ["id", "event", "actor", "subject"],
     "Operations board events."),
    ("session_activity",
     ["created_at"],
     ["session_id", "actor_email", "ip"],
     "Session activity log."),
    ("dispatch_users",
     ["created_at"],
     ["id", "name", "role"],
     "Dispatch users — should never grow during a deploy."),
]


# ─── Scanner ────────────────────────────────────────────────────────
async def scan_collection(
    db: AsyncIOMotorDatabase,
    collection: str,
    date_fields: List[str],
    sample_fields: List[str],
    description: str,
    since_iso: str,
    since_dt: datetime,
) -> Dict[str, Any]:
    """Return a result dict for the report."""
    col = db[collection]
    if collection not in await db.list_collection_names():
        return {
            "collection": collection,
            "description": description,
            "present": False,
            "total": 0,
            "in_window": [],
            "with_marker": [],
        }

    total = await col.count_documents({})

    # Fetch ALL recent records (cap at 2000) and triage in Python so we
    # can match across naive/aware datetimes and string dates uniformly.
    recent: List[Dict[str, Any]] = []
    cursor = col.find({}, {"_id": 0})
    # Sort by first date field if it exists; if not, by created_at fallback.
    sort_field = date_fields[0] if date_fields else "created_at"
    try:
        cursor = cursor.sort(sort_field, -1).limit(2000)
    except Exception:
        cursor = col.find({}, {"_id": 0}).limit(2000)
    async for d in cursor:
        recent.append(d)

    def _doc_dt(doc: Dict[str, Any]) -> datetime | None:
        for f in date_fields:
            v = doc.get(f)
            if v is None and "." in f:
                # nested
                obj: Any = doc
                for part in f.split("."):
                    if isinstance(obj, dict):
                        obj = obj.get(part)
                    else:
                        obj = None
                        break
                v = obj
            if v is None:
                continue
            if isinstance(v, datetime):
                return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            if isinstance(v, str):
                try:
                    s = v.replace("Z", "+00:00")
                    return datetime.fromisoformat(s)
                except Exception:
                    pass
        return None

    in_window: List[Dict[str, Any]] = []
    with_marker: List[Tuple[Dict[str, Any], str]] = []
    for d in recent:
        dt = _doc_dt(d)
        matched, reason = _has_test_marker(d)
        if matched:
            with_marker.append((d, reason))
        elif dt is not None and dt >= since_dt:
            in_window.append(d)

    def _sample_row(d: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in sample_fields:
            if "." in f:
                obj: Any = d
                for part in f.split("."):
                    if isinstance(obj, dict):
                        obj = obj.get(part)
                    else:
                        obj = None
                        break
                out[f] = obj
            else:
                out[f] = d.get(f)
        # Always include the chosen date field
        for f in date_fields:
            if f in d:
                out[f] = _normalize_dt(d.get(f))
                break
        return out

    return {
        "collection": collection,
        "description": description,
        "present": True,
        "total": total,
        "in_window": [_sample_row(d) for d in in_window[:25]],
        "with_marker": [
            {**_sample_row(d), "_match": reason}
            for d, reason in with_marker[:25]
        ],
        "in_window_count": len(in_window),
        "with_marker_count": len(with_marker),
        "since_iso": since_iso,
    }


def _confidence(reason: str, sample: Dict[str, Any]) -> str:
    text = " ".join(str(v) for v in sample.values()).lower()
    if any(k in text for k in ["pw-phase", "sigma-iii", "sigma3", "phase sigma-iii"]):
        return "🔴 HIGH"
    if any(k in text for k in ["iter4", "iter3", "test mechanic", "testmech",
                                "playwright", "smoke-test", "smoke_test",
                                "brand check", "t-sigma3"]):
        return "🟠 HIGH"
    if reason == "marker":
        return "🟡 MEDIUM (marker match · review manually)"
    return "⚪ LOW (in-window only · likely real activity)"


def _render_report(results: List[Dict[str, Any]], since_iso: str, generated_at: str) -> str:
    lines: List[str] = []
    lines.append(f"# Production Contamination Candidates — iter437")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}")
    lines.append(f"**Target DB:** `{PROD_DB}` (live production)")
    lines.append(f"**Contamination window:** records created since `{since_iso}` (UTC)")
    lines.append(f"**Test markers:** `pw-phase`, `Sigma-III`, `iter4xx`, `T-SIGMA3`, `testmech`, `playwright`, `smoke-test`, `dummy`, `fake`, `placeholder`, `demo`, `qa`, `brand check`")
    lines.append("")
    lines.append("> ⚠ THIS REPORT IS A CANDIDATE LIST. NO RECORDS HAVE BEEN DELETED.")
    lines.append("> Reviewer must approve deletions explicitly before any cleanup runs.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Collection | Total | In Window | With Marker |")
    lines.append("|---|---:|---:|---:|")
    grand_window = grand_marker = 0
    for r in results:
        if not r["present"]:
            lines.append(f"| {r['collection']} | — | — | (collection absent) |")
            continue
        lines.append(
            f"| `{r['collection']}` | {r['total']} "
            f"| {r['in_window_count']} | {r['with_marker_count']} |"
        )
        grand_window += r["in_window_count"]
        grand_marker += r["with_marker_count"]
    lines.append(f"| **TOTAL** | | **{grand_window}** | **{grand_marker}** |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-collection details
    for r in results:
        if not r["present"]:
            continue
        if r["in_window_count"] == 0 and r["with_marker_count"] == 0:
            continue
        lines.append(f"## `{r['collection']}`")
        lines.append("")
        lines.append(r["description"])
        lines.append("")

        if r["with_marker_count"]:
            lines.append(
                f"### 🚨 Records with explicit test markers ({r['with_marker_count']})"
            )
            lines.append("")
            for sample in r["with_marker"][:15]:
                conf = _confidence("marker", sample)
                lines.append(f"- {conf} · " + " · ".join(
                    f"`{k}={v!r}`" for k, v in sample.items() if v is not None
                ))
            if r["with_marker_count"] > 15:
                lines.append(f"- … and {r['with_marker_count'] - 15} more")
            lines.append("")

        if r["in_window_count"]:
            lines.append(
                f"### 🟡 Records created in contamination window ({r['in_window_count']})"
            )
            lines.append("")
            for sample in r["in_window"][:15]:
                conf = _confidence("window", sample)
                lines.append(f"- {conf} · " + " · ".join(
                    f"`{k}={v!r}`" for k, v in sample.items() if v is not None
                ))
            if r["in_window_count"] > 15:
                lines.append(f"- … and {r['in_window_count'] - 15} more")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Decision matrix")
    lines.append("")
    lines.append("| Confidence | What to do |")
    lines.append("|---|---|")
    lines.append("| 🔴 HIGH (explicit pw-phase / Sigma-III markers) | Approve immediate hard delete |")
    lines.append("| 🟠 HIGH (iter / testmech / T-SIGMA3 / Brand Check) | Approve hard delete after eyeball check |")
    lines.append("| 🟡 MEDIUM (other marker matches like `demo`/`qa`) | Per-row eyeball review · may be real |")
    lines.append("| ⚪ LOW (in-window only · no marker) | LEAVE ALONE · likely real ops activity |")
    lines.append("")
    lines.append("Once you mark a confidence tier as approved, I will write a")
    lines.append("matching `cleanup_production_contamination.py` script that")
    lines.append("scoped-deletes ONLY the approved rows by exact `_id`/`id`")
    lines.append("match (no bulk regex deletes), with a dry-run preview and a")
    lines.append("post-cleanup re-scan.")
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--since", type=str, default=None)
    parser.add_argument(
        "--out", type=str,
        default="/app/memory/PROD_CONTAMINATION_CANDIDATES.md",
    )
    args = parser.parse_args()

    if args.since:
        since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    if since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)
    since_iso = since_dt.isoformat()

    print(f"Scanning production DB '{PROD_DB}' for contamination since {since_iso}")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[PROD_DB]
    # Hard safety: refuse to run if the DB name doesn't match production.
    assert db.name == PROD_DB, f"DB switch failed — got {db.name}"

    results: List[Dict[str, Any]] = []
    for collection, date_fields, sample_fields, description in TARGETS:
        print(f"  · {collection} …")
        res = await scan_collection(
            db, collection, date_fields, sample_fields, description,
            since_iso, since_dt,
        )
        results.append(res)

    generated_at = datetime.now(timezone.utc).isoformat()
    report = _render_report(results, since_iso, generated_at)
    Path(args.out).write_text(report)
    print(f"\n✅ Report written to {args.out}")

    # Echo summary to stdout
    print("\nSummary (collection · in_window · with_marker):")
    for r in results:
        if not r["present"]:
            continue
        if r["in_window_count"] or r["with_marker_count"]:
            print(f"  {r['collection']:35s} window={r['in_window_count']:>4d} marker={r['with_marker_count']:>4d}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
