"""iter437 · Phase Sigma-II · in-place rewrite of oversized idempotency_keys.

Rewrites each row's `response` field through `_strip_for_cache`. Operates on
PROD or PREVIEW per `--db` flag. Always dry-runs first; pass --apply to mutate.

Usage:
  # Preview first (proof)
  python3 tools/idempotency_rewrite.py --db=masci_safety_preview --dry-run
  python3 tools/idempotency_rewrite.py --db=masci_safety_preview --apply

  # Then prod (after preview certified)
  python3 tools/idempotency_rewrite.py --db=masci_safety --dry-run
  python3 tools/idempotency_rewrite.py --db=masci_safety --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import bson

# Bootstrap env
for line in Path("/app/backend/.env").read_text().splitlines():
    if "=" not in line or line.strip().startswith("#"):
        continue
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Use the live strip function so behavior is identical to the writer.
sys.path.insert(0, "/app/backend")
from lib.idempotency import _strip_for_cache  # noqa: E402

from pymongo import MongoClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, choices=["masci_safety", "masci_safety_preview"])
    ap.add_argument("--apply", action="store_true", help="actually write (omit for dry-run)")
    args = ap.parse_args()

    client = MongoClient(os.environ["MONGO_URL"])
    db = client[args.db]

    print(f"[idem-rewrite] db={db.name}  apply={args.apply}")

    coll = db.idempotency_keys
    total = coll.count_documents({})
    print(f"[idem-rewrite] total rows: {total}")

    if total == 0:
        print("[idem-rewrite] nothing to rewrite")
        return

    rows_before_bytes = 0
    rows_after_bytes = 0
    rewritten = 0
    unchanged = 0

    t0 = time.monotonic()
    for doc in coll.find({}):
        before = bson.BSON.encode(doc)
        rows_before_bytes += len(before)

        original_response = doc.get("response")
        stripped = _strip_for_cache(original_response)
        if stripped == original_response:
            unchanged += 1
            rows_after_bytes += len(before)
            continue

        # Apply the rewrite
        new_doc = dict(doc)
        new_doc["response"] = stripped
        new_doc["_rewrite_iter"] = "iter437"
        after = bson.BSON.encode(new_doc)
        rows_after_bytes += len(after)

        delta_pct = ((len(before) - len(after)) / len(before)) * 100.0
        print(f"  key={(doc.get('key') or '?')[:36]}  before={len(before):>10,}  after={len(after):>6,}  -{delta_pct:.1f}%")

        if args.apply:
            coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {"response": stripped, "_rewrite_iter": "iter437"}},
            )
            rewritten += 1

    elapsed = time.monotonic() - t0
    saved = rows_before_bytes - rows_after_bytes
    print()
    print(f"[idem-rewrite] total rows scanned: {total}")
    print(f"[idem-rewrite] rows that would change: {total - unchanged}")
    print(f"[idem-rewrite] rows already minimal:   {unchanged}")
    print(f"[idem-rewrite] rows actually written:  {rewritten}")
    print(f"[idem-rewrite] before total size: {rows_before_bytes/1e6:.2f} MB")
    print(f"[idem-rewrite] after total size:  {rows_after_bytes/1e6:.2f} MB")
    print(f"[idem-rewrite] reclaim:            {saved/1e6:.2f} MB ({(saved/rows_before_bytes*100 if rows_before_bytes else 0):.1f}%)")
    print(f"[idem-rewrite] elapsed: {elapsed:.2f}s")

    # Write a report
    report = {
        "db": args.db,
        "apply": args.apply,
        "rows_scanned": total,
        "rows_unchanged": unchanged,
        "rows_rewritten": rewritten if args.apply else (total - unchanged),
        "before_bytes": rows_before_bytes,
        "after_bytes": rows_after_bytes,
        "saved_bytes": saved,
        "elapsed_s": round(elapsed, 2),
    }
    out = Path(f"/tmp/idem_rewrite_{args.db}_{'apply' if args.apply else 'dryrun'}.json")
    out.write_text(json.dumps(report, indent=2))
    print(f"[idem-rewrite] report -> {out}")


if __name__ == "__main__":
    main()
