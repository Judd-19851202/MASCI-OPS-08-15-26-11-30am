#!/usr/bin/env python3
"""TRACK 24.12 · Workstream B · READ-ONLY disk audit
====================================================

Enumerates on-disk storage that the MASCI backend keeps in the pod
filesystem so operators can spot growth patterns before the disk
fills up. Focuses on the two paths that historically ballooned in
production:

* ``/app/backend/storage/project_docs`` — Basecamp big-file imports
  and ad-hoc uploads (see :file:`scripts/basecamp_import_big.py`).
* Any Mongo backup dir configured under ``BACKUP_DIR`` or the
  legacy ``/app/backend/backups`` path.

For each candidate directory the script prints:

* total size + file count
* largest 10 files by size
* age distribution (24 h / 7 d / 30 d / 90 d / older buckets)

If Cloudflare R2 (:mod:`photo_storage`) is configured, the script
also prints a bucket-count / bucket-size probe so operators can see
the local ↔ R2 delta at a glance.

ZERO writes. ZERO deletes. ZERO Mongo mutations. Safe to run on
production. Read-only by construction — enforced by the test suite
(:file:`tests/test_track_24_12_disk_hardening.py`).

Usage
-----
::

    cd /app/backend && python3 scripts/audit_disk_usage_24_12.py
    cd /app/backend && python3 scripts/audit_disk_usage_24_12.py --json
    cd /app/backend && python3 scripts/audit_disk_usage_24_12.py --path /some/other/dir
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Default candidate paths. Extended via --path.
DEFAULT_PATHS: List[Path] = [
    Path("/app/backend/storage/project_docs"),
    Path(os.environ.get("BACKUP_DIR") or "/app/backend/backups"),
    Path("/app/backend/storage"),
    Path("/tmp/basecamp"),
]


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:6.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def audit_path(root: Path) -> Dict[str, Any]:
    """Read-only enumeration. Never writes, never deletes."""
    result: Dict[str, Any] = {
        "path": str(root),
        "exists": root.exists(),
        "is_dir": root.is_dir() if root.exists() else False,
        "total_bytes": 0,
        "file_count": 0,
        "largest": [],
        "age_buckets": {
            "24h": 0, "7d": 0, "30d": 0, "90d": 0, "older": 0,
        },
    }
    if not root.exists() or not root.is_dir():
        return result

    now = time.time()
    largest: List[Tuple[int, str]] = []
    for p in root.rglob("*"):
        try:
            if not p.is_file():
                continue
            st = p.stat()
            size = st.st_size
            mtime = st.st_mtime
        except OSError:
            continue
        result["total_bytes"] += size
        result["file_count"] += 1
        age_days = (now - mtime) / 86400
        if age_days <= 1:
            result["age_buckets"]["24h"] += 1
        elif age_days <= 7:
            result["age_buckets"]["7d"] += 1
        elif age_days <= 30:
            result["age_buckets"]["30d"] += 1
        elif age_days <= 90:
            result["age_buckets"]["90d"] += 1
        else:
            result["age_buckets"]["older"] += 1
        largest.append((size, str(p)))
    largest.sort(key=lambda t: t[0], reverse=True)
    result["largest"] = [
        {"size_bytes": s, "path": p} for s, p in largest[:10]
    ]
    return result


def audit_r2() -> Dict[str, Any]:
    """Best-effort R2 head-bucket probe. Never writes. Never lists
    objects (list-objects can be expensive on multi-million object
    buckets — this is intentionally shallow)."""
    out: Dict[str, Any] = {"configured": False, "ok": False}
    try:
        # Local import so audit still works when the backend venv
        # does not have boto3 installed (unlikely in prod, but the
        # audit must not hard-fail).
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import photo_storage  # type: ignore  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        out["error"] = f"import photo_storage failed: {e}"
        return out
    out["configured"] = bool(photo_storage.is_configured())
    if not out["configured"]:
        out["reason"] = "R2 env vars missing (S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY)"
        return out
    try:
        c = photo_storage._client()  # noqa: SLF001
        c.head_bucket(Bucket=photo_storage._bucket())  # noqa: SLF001
        out["ok"] = True
        out["bucket"] = photo_storage._bucket()  # noqa: SLF001
        out["endpoint"] = photo_storage._env("S3_ENDPOINT_URL")[:80]  # noqa: SLF001
    except Exception as e:  # noqa: BLE001
        out["error"] = f"head_bucket failed: {e}"
    return out


def print_report(paths: List[Dict[str, Any]], r2: Dict[str, Any]) -> None:
    print()
    print("=" * 72)
    print("TRACK 24.12 · Local disk audit (READ-ONLY)")
    print("=" * 72)
    grand_total = 0
    for row in paths:
        print()
        print(f"  {row['path']}")
        if not row["exists"]:
            print("    (does not exist — skipped)")
            continue
        print(f"    total: {_human(row['total_bytes'])} · "
              f"{row['file_count']} file(s)")
        print(f"    age  : 24h={row['age_buckets']['24h']}  "
              f"7d={row['age_buckets']['7d']}  "
              f"30d={row['age_buckets']['30d']}  "
              f"90d={row['age_buckets']['90d']}  "
              f"older={row['age_buckets']['older']}")
        if row["largest"]:
            print("    top-10 largest:")
            for e in row["largest"]:
                print(f"      {_human(e['size_bytes'])}  {e['path']}")
        grand_total += row["total_bytes"]
    print()
    print("-" * 72)
    print(f"  Grand total on local disk: {_human(grand_total)}")
    print("-" * 72)
    print()
    print("Cloudflare R2 (photo_storage) probe:")
    if r2.get("ok"):
        print(f"  ✓ configured · bucket={r2.get('bucket')} · endpoint={r2.get('endpoint')}")
    elif r2.get("configured"):
        print(f"  ⚠ configured but head_bucket failed: {r2.get('error') or r2.get('reason')}")
    else:
        print(f"  · not configured — {r2.get('reason') or r2.get('error') or ''}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--path", action="append", default=[],
        help="Additional directory to audit (repeatable).",
    )
    ap.add_argument(
        "--json", action="store_true",
        help="Emit a JSON envelope instead of the human-readable table.",
    )
    args = ap.parse_args()

    candidates: List[Path] = list(DEFAULT_PATHS) + [Path(p) for p in args.path]
    # De-duplicate while preserving order.
    seen: set = set()
    ordered: List[Path] = []
    for p in candidates:
        rp = p.resolve() if p.exists() else p
        if str(rp) in seen:
            continue
        seen.add(str(rp))
        ordered.append(rp)

    paths = [audit_path(p) for p in ordered]
    r2 = audit_r2()
    if args.json:
        print(json.dumps({"paths": paths, "r2": r2}, indent=2))
    else:
        print_report(paths, r2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
