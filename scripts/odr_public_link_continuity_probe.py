#!/usr/bin/env python3
"""
odr_public_link_continuity_probe.py — Phase V.1 · M0.2.

Defends the ODR Public Link Continuity contract. Sub-second probe.
Read-only · never mutates state.

Checks:
  C1. Every issued public link_id is unique across `odr_public_links`.
  C2. Every `odr.public_access.link_id`, if set, exists in the registry.
  C3. Every `odr_public_links` row references an existing ODR by id.
  C4. doc_id format is `ODR-YYYY-NNNNN` for every link.
  C5. No two ODRs share the same `doc_id` (continuity-safe identifier
      invariant).
  C6. No two ODRs share the same active link_id.
  C7. `odr_preload_attempts` outcome values fall in the closed
      enumeration.
  C8. Append-only invariant: `odr_preload_attempts` count never shrinks
      compared to snapshot (best-effort using a checkpoint file).

Usage:
  python3 scripts/odr_public_link_continuity_probe.py [--gate]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "backend" / ".env")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


DOC_ID_RX = re.compile(r"^ODR-\d{4}-\d{5}$")
ALLOWED_OUTCOMES = {
    "allowed", "denied_device_mismatch", "denied_missing_token",
    "denied_expired_context", "denied_wrong_project",
    "denied_wrong_link", "denied_date_out_of_window",
    "denied_gps_conflict", "denied_no_prior", "override_used",
}

SNAPSHOT_PATH = REPO_ROOT / "memory" / "ODR_PROBE_CONTINUITY_SNAPSHOT.json"
REPORT_PATH = (
    REPO_ROOT
    / "memory"
    / "ODR_PUBLIC_LINK_CONTINUITY_PROBE_REPORT.md"
)


def _utc_iso() -> str:
    d = datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


async def run(gate: bool) -> int:
    url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(url, tz_aware=True)
    db = client[db_name]

    failures: list[dict] = []
    warnings: list[dict] = []
    stats: dict = {"env": os.environ.get("APP_ENV"), "db": db_name}

    # ── C1 · unique link_id ──────────────────────────────────────────
    links = await db.odr_public_links.find(
        {}, {"_id": 0, "link_id": 1, "odr_id": 1, "doc_id": 1,
             "revoked_at_utc": 1}
    ).to_list(length=10000)
    stats["public_links_count"] = len(links)
    seen = Counter(link["link_id"] for link in links)
    dupes = [k for k, v in seen.items() if v > 1]
    if dupes:
        failures.append({
            "check": "C1",
            "name": "unique_link_id",
            "duplicates": dupes,
        })

    # ── C2 · odr.public_access.link_id resolves ──────────────────────
    link_set = {link["link_id"] for link in links}
    cur = db.odr.find(
        {"public_access.link_id": {"$ne": None, "$exists": True}},
        {"_id": 0, "id": 1, "doc_id": 1, "public_access.link_id": 1},
    )
    orphans = []
    odr_link_count = 0
    async for r in cur:
        link_id = (r.get("public_access") or {}).get("link_id")
        if not link_id:
            continue
        odr_link_count += 1
        if link_id not in link_set:
            orphans.append({"odr_id": r["id"], "link_id": link_id})
    stats["odrs_with_public_access"] = odr_link_count
    if orphans:
        failures.append({
            "check": "C2",
            "name": "orphan_link_on_odr",
            "orphans": orphans[:20],
        })

    # ── C3 · link rows reference existing ODR ────────────────────────
    odr_ids = set()
    cur = db.odr.find({}, {"_id": 0, "id": 1, "doc_id": 1})
    odrs = await cur.to_list(length=10000)
    odr_ids = {o["id"] for o in odrs}
    stats["odr_count"] = len(odr_ids)
    bad_refs = [
        link for link in links
        if link.get("odr_id") not in odr_ids
    ]
    if bad_refs:
        failures.append({
            "check": "C3",
            "name": "link_references_missing_odr",
            "bad_refs": bad_refs[:20],
        })

    # ── C4 · doc_id format ───────────────────────────────────────────
    bad_doc = []
    for link in links:
        if not DOC_ID_RX.match(link.get("doc_id", "")):
            bad_doc.append(link)
    for o in odrs:
        if not DOC_ID_RX.match(o.get("doc_id", "")):
            bad_doc.append({"odr_id": o.get("id"), "doc_id": o.get("doc_id")})
    if bad_doc:
        failures.append({
            "check": "C4",
            "name": "doc_id_format",
            "bad": bad_doc[:20],
        })

    # ── C5 · doc_id uniqueness ───────────────────────────────────────
    doc_id_counter = Counter(o.get("doc_id") for o in odrs)
    dup_docs = [d for d, c in doc_id_counter.items() if c > 1 and d]
    if dup_docs:
        failures.append({
            "check": "C5",
            "name": "doc_id_uniqueness",
            "duplicates": dup_docs,
        })

    # ── C6 · no two ODRs share active link_id ────────────────────────
    active_link_map: dict[str, list[str]] = {}
    for link in links:
        if link.get("revoked_at_utc"):
            continue
        active_link_map.setdefault(link["link_id"], []).append(link["odr_id"])
    shared = {k: v for k, v in active_link_map.items() if len(set(v)) > 1}
    if shared:
        failures.append({
            "check": "C6",
            "name": "link_id_shared_across_odrs",
            "shared": shared,
        })

    # ── C7 · preload_attempts outcome closed enum ────────────────────
    attempts = await db.odr_preload_attempts.find(
        {}, {"_id": 0, "attempt_id": 1, "outcome": 1}
    ).to_list(length=20000)
    stats["preload_attempts_count"] = len(attempts)
    bad_outcomes = [
        a for a in attempts
        if a.get("outcome") not in ALLOWED_OUTCOMES
    ]
    if bad_outcomes:
        failures.append({
            "check": "C7",
            "name": "preload_attempt_outcome_closed_enum",
            "bad": bad_outcomes[:20],
        })

    # ── C8 · append-only · preload_attempts never shrinks ────────────
    snapshot: dict = {}
    if SNAPSHOT_PATH.exists():
        try:
            snapshot = json.loads(SNAPSHOT_PATH.read_text())
        except Exception as exc:
            warnings.append({
                "check": "C8",
                "name": "snapshot_unreadable",
                "exc": str(exc),
            })
    prior = snapshot.get("preload_attempts_count")
    if prior is not None and stats["preload_attempts_count"] < prior:
        failures.append({
            "check": "C8",
            "name": "preload_attempts_count_shrank",
            "prior": prior,
            "now": stats["preload_attempts_count"],
        })

    # ── refresh snapshot ─────────────────────────────────────────────
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps({
        "captured_at_utc": _utc_iso(),
        "odr_count": stats["odr_count"],
        "public_links_count": stats["public_links_count"],
        "preload_attempts_count": stats["preload_attempts_count"],
    }, indent=2))

    # ── render report ────────────────────────────────────────────────
    report_lines = [
        "# ODR Public-Link Continuity Probe Report",
        "",
        f"_Generated {_utc_iso()} · env={stats['env']} · db={stats['db']}_",
        "",
        "## Counts",
        f"- ODRs: **{stats['odr_count']}**",
        f"- Public links issued: **{stats['public_links_count']}**",
        f"- ODRs with public_access.link_id: **{stats['odrs_with_public_access']}**",
        f"- Preload attempts logged: **{stats['preload_attempts_count']}**",
        "",
        "## Checks",
    ]
    for check_id, name in [
        ("C1", "Unique public link_id"),
        ("C2", "ODR public_access.link_id resolves to registry"),
        ("C3", "Registry rows reference existing ODR id"),
        ("C4", "doc_id format `ODR-YYYY-NNNNN`"),
        ("C5", "doc_id uniqueness across ODRs"),
        ("C6", "No two ODRs share an active link_id"),
        ("C7", "preload_attempts.outcome ∈ closed enum"),
        ("C8", "preload_attempts append-only (count never shrinks)"),
    ]:
        marker = "✅"
        for f in failures:
            if f["check"] == check_id:
                marker = "❌"
                break
        report_lines.append(f"- {marker} **{check_id}** · {name}")
    if failures:
        report_lines += ["", "## Failures", ""]
        for f in failures:
            report_lines.append(f"### {f['check']} · {f['name']}")
            report_lines.append("```")
            report_lines.append(json.dumps(f, indent=2, default=str))
            report_lines.append("```")
    REPORT_PATH.write_text("\n".join(report_lines) + "\n")

    print(f"odr_public_link_continuity_probe · env={stats['env']} · db={stats['db']}")
    print(f"  ODRs={stats['odr_count']}  links={stats['public_links_count']}  "
          f"with_link={stats['odrs_with_public_access']}  attempts={stats['preload_attempts_count']}")
    print(f"  failures={len(failures)}  warnings={len(warnings)}")
    if failures:
        for f in failures:
            print(f"  ❌ {f['check']} · {f['name']}")
        if gate:
            return 1
    else:
        print("  ✅ all checks passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    return asyncio.run(run(gate=args.gate))


if __name__ == "__main__":
    sys.exit(main())
