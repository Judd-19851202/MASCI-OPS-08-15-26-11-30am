"""
MASCI Restore Drill — one-off script.

Restores a Cloudflare R2 complete-backup zip into `masci_safety_preview`
(and ONLY that DB), document by document, upserting by `id`.

Safety guardrails:
  1. Refuses to run unless DB_NAME ends in `_preview`.
  2. Refuses to run unless APP_ENV=preview.
  3. Never touches `masci_safety` (prod).
  4. Skips system collections (`system.*`).
  5. Uses ordered=False bulk writes; one bad doc cannot abort an
     entire collection.

Usage:
  python tools/restore_drill.py /tmp/restore_source.zip

The script prints a per-collection summary and a final report JSON to
stdout, plus writes a manifest to /tmp/restore_drill_report.json so the
operator can diff before/after counts.
"""

from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

# ---------------------------------------------------------------------------
# Bootstrap env
# ---------------------------------------------------------------------------
for line in Path("/app/backend/.env").read_text().splitlines():
    if "=" not in line or line.strip().startswith("#"):
        continue
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DB_NAME = os.environ.get("DB_NAME", "")
APP_ENV = os.environ.get("APP_ENV", "").lower()
MONGO_URL = os.environ["MONGO_URL"]

if APP_ENV != "preview" or not DB_NAME.endswith("_preview"):
    print(
        f"REFUSING TO RUN: APP_ENV={APP_ENV!r} DB_NAME={DB_NAME!r}. "
        "Restore drill only runs against a `*_preview` database.",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
if len(sys.argv) != 2:
    print("Usage: python tools/restore_drill.py <path-to-backup.zip>", file=sys.stderr)
    sys.exit(1)

ZIP_PATH = sys.argv[1]
if not os.path.isfile(ZIP_PATH):
    print(f"Not a file: {ZIP_PATH}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Open Mongo + Zip
# ---------------------------------------------------------------------------
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
print(f"[restore-drill] target db: {db.name}  (host_info ok: {client.server_info()['ok']==1.0})")

zf = zipfile.ZipFile(ZIP_PATH, "r")
names = zf.namelist()
print(f"[restore-drill] backup file: {ZIP_PATH}  entries: {len(names):,}")

# ---------------------------------------------------------------------------
# Group entries by collection
# Backup format: <collection>/json/<doc-id>.json  (one file per document)
# Some backups also have <collection>/<bucket>.json (one big list). Handle both.
# ---------------------------------------------------------------------------
by_coll: dict[str, list[str]] = defaultdict(list)
single_payload: dict[str, str] = {}
for n in names:
    if n.endswith(".json"):
        parts = n.split("/")
        if len(parts) == 3 and parts[1] == "json":
            by_coll[parts[0]].append(n)
        elif len(parts) == 2:
            # collection/<name>.json single-file dump
            single_payload[parts[0]] = n

print(f"[restore-drill] collections (per-doc):     {len(by_coll)}")
print(f"[restore-drill] collections (single-file): {len(single_payload)}")

# Skip system collections + heavy log collections that the operator does
# NOT want to restore into preview (configurable).
SKIP_COLLECTIONS = {
    # system / mongo-internal
    "system",
    # transient telemetry / audit logs that bloat preview without being
    # operationally useful (these are also the largest by far). Restore
    # drill can be re-run with these enabled by editing this set.
    "usage_events",
    "health_monitor_runs",
    "session_activity",
    "directory_sessions",
    "training_hits",
    "hub_banner_audit",
    "guidance_search_misses",
}


# The complete-backup zip stores safety forms under kebab-case slugs
# (`daily-reports/`, `equipment-inspections/`) but MongoDB stores them
# under snake_case (`daily_reports`, `equipment_inspections`). Mirror
# the official server.py `_RESTORE_KIND_TO_COLL` mapping so this drill
# restores to the same destination the live app reads from.
KIND_TO_COLL = {
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
}


# ---------------------------------------------------------------------------
# Snapshot existing counts
# ---------------------------------------------------------------------------
print("[restore-drill] snapshotting pre-restore counts ...")
pre_counts: dict[str, int] = {}
for coll in sorted(set(by_coll) | set(single_payload)):
    pre_counts[coll] = db[coll].count_documents({})

# ---------------------------------------------------------------------------
# Restore loop
# ---------------------------------------------------------------------------
results: list[dict] = []
t_total = time.monotonic()

def _strip_id(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc

def _bulk_upsert(coll_name: str, docs: list[dict]) -> dict:
    """Upsert by `id` (string UUID) if present, else by hash of payload."""
    ops = []
    skipped = 0
    for d in docs:
        if not isinstance(d, dict):
            skipped += 1
            continue
        _strip_id(d)
        key = d.get("id") or d.get("_uid") or d.get("uuid")
        if not key:
            skipped += 1
            continue
        ops.append(UpdateOne({"id": key}, {"$set": d}, upsert=True))
    if not ops:
        return {"upserted": 0, "skipped": skipped}
    try:
        res = db[coll_name].bulk_write(ops, ordered=False)
        # NOTE: pymongo's `upserted_count` only reflects rows that hit the
        # upsert branch (no prior match). `modified_count` reflects rows
        # that did match and changed. The number of attempted writes is
        # len(ops); sum of upserted + modified can be < len(ops) when
        # writes are no-ops (incoming doc identical to existing doc).
        return {
            "ops": len(ops),
            "upserted_new": res.upserted_count or 0,
            "modified": res.modified_count or 0,
            "matched": res.matched_count or 0,
            "upserted": (res.upserted_count or 0) + (res.matched_count or 0),
            "skipped": skipped,
        }
    except BulkWriteError as e:  # partial failures
        details = e.details
        return {
            "upserted": (details.get("nUpserted", 0) + details.get("nModified", 0)),
            "skipped": skipped,
            "write_errors": len(details.get("writeErrors", [])),
        }


# Per-doc collections
for coll, files in sorted(by_coll.items()):
    if coll in SKIP_COLLECTIONS:
        results.append({"collection": coll, "skipped_intentionally": True, "doc_count": len(files)})
        continue
    # Apply kebab-→-snake mapping so safety forms land in the same
    # Mongo collection the live application reads from.
    target_coll = KIND_TO_COLL.get(coll, coll)
    t0 = time.monotonic()
    batch: list[dict] = []
    upserted_total = 0
    skipped_total = 0
    BATCH = 500
    for n in files:
        try:
            batch.append(json.loads(zf.read(n).decode("utf-8")))
        except Exception:
            skipped_total += 1
            continue
        if len(batch) >= BATCH:
            r = _bulk_upsert(target_coll, batch)
            upserted_total += r["upserted"]
            skipped_total += r.get("skipped", 0)
            batch = []
    if batch:
        r = _bulk_upsert(target_coll, batch)
        upserted_total += r["upserted"]
        skipped_total += r.get("skipped", 0)
    elapsed = time.monotonic() - t0
    results.append({
        "collection": coll,
        "target_collection": target_coll,
        "source_docs": len(files),
        "upserted": upserted_total,
        "skipped": skipped_total,
        "elapsed_s": round(elapsed, 2),
    })
    arrow = f" -> {target_coll}" if target_coll != coll else ""
    print(
        f"  {coll:36s}{arrow:20s}  source={len(files):6d}  upserted={upserted_total:6d}  "
        f"skipped={skipped_total:4d}  ({elapsed:.2f}s)"
    )


# Single-file collections (one big JSON list per file)
for coll, name in sorted(single_payload.items()):
    if coll in SKIP_COLLECTIONS:
        continue
    try:
        raw = json.loads(zf.read(name).decode("utf-8"))
    except Exception as e:
        results.append({"collection": coll, "error": f"parse {name}: {e}"})
        continue
    if not isinstance(raw, list):
        results.append({"collection": coll, "skipped": "single-file not a list"})
        continue
    t0 = time.monotonic()
    r = _bulk_upsert(coll, raw)
    elapsed = time.monotonic() - t0
    results.append({
        "collection": coll,
        "source_docs": len(raw),
        "upserted": r["upserted"],
        "skipped": r.get("skipped", 0),
        "elapsed_s": round(elapsed, 2),
        "mode": "single-file",
    })
    print(
        f"  {coll:48s}  source={len(raw):6d}  upserted={r['upserted']:6d}  "
        f"({elapsed:.2f}s)  [single-file]"
    )


# ---------------------------------------------------------------------------
# Post-restore counts
# ---------------------------------------------------------------------------
print("[restore-drill] snapshotting post-restore counts ...")
post_counts: dict[str, int] = {}
for coll in pre_counts.keys():
    post_counts[coll] = db[coll].count_documents({})

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
report = {
    "db": DB_NAME,
    "app_env": APP_ENV,
    "source_zip": ZIP_PATH,
    "total_elapsed_s": round(time.monotonic() - t_total, 2),
    "collections_per_doc": len(by_coll),
    "collections_single_file": len(single_payload),
    "skipped_collections": sorted(SKIP_COLLECTIONS),
    "results": results,
    "before": pre_counts,
    "after": post_counts,
}

Path("/tmp/restore_drill_report.json").write_text(json.dumps(report, indent=2))
print(f"\n[restore-drill] DONE. total elapsed: {report['total_elapsed_s']}s")
print(f"[restore-drill] report: /tmp/restore_drill_report.json")
