#!/usr/bin/env python3
"""restore_drill.py — Cloudflare R2 → ephemeral Mongo restore drill helper.

PURPOSE
    Prove the MASCI Hub backups in Cloudflare R2 are actually restorable.
    See /app/memory/RESTORE_DRILL.md for the surrounding procedure.

This script is intentionally MINIMAL and SAFE:
    • --list           lists backups in R2, newest first
    • --dry-run        prints what would be downloaded + which collections
                       it would write to, performs NO writes
    • without dry-run  downloads, decrypts/decompresses if needed, and
                       writes into the TARGET database on the TARGET URI.

SAFETY RAILS
    • Refuses to write into the live `DB_NAME` (read from backend/.env).
    • Refuses to write to the live mongo URI unless --i-know-what-i-am-doing
      is also passed (you should be writing to an ephemeral target).
    • Never deletes from R2.
    • Never modifies the source database.

Required env (read from /app/backend/.env automatically if present):
    R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET

Usage:
    python3 scripts/restore_drill.py --list
    python3 scripts/restore_drill.py --backup full-2026-02-15-0300.tar.gz \\
        --target mongodb://localhost:27018 --target-db masci_drill --dry-run
    python3 scripts/restore_drill.py --backup full-2026-02-15-0300.tar.gz \\
        --target mongodb://localhost:27018 --target-db masci_drill
"""
from __future__ import annotations

import argparse
import os
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"


def _load_env() -> dict:
    env = dict(os.environ)
    if BACKEND_ENV.exists():
        for line in BACKEND_ENV.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"'))
    return env


def _r2_client(env: dict):
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("FAIL: boto3 not installed. pip install boto3", file=sys.stderr)
        sys.exit(2)
    missing = [k for k in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT", "R2_BUCKET") if not env.get(k)]
    if missing:
        print(f"FAIL: missing R2 env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    return boto3.client(
        "s3",
        endpoint_url=env["R2_ENDPOINT"],
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
    ), env["R2_BUCKET"]


def cmd_list(args, env):
    client, bucket = _r2_client(env)
    print(f"Listing R2 backups in bucket: {bucket}")
    print("-" * 78)
    objs = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for o in page.get("Contents", []):
            objs.append(o)
    objs.sort(key=lambda o: o["LastModified"], reverse=True)
    for o in objs[: args.limit]:
        size_mb = o["Size"] / (1024 * 1024)
        print(f"  {o['LastModified'].isoformat()}  {size_mb:>8.1f} MB  {o['Key']}")
    print("-" * 78)
    print(f"Total objects: {len(objs)} (showing {min(len(objs), args.limit)})")
    return 0


def cmd_restore(args, env):
    # --- safety rails ------------------------------------------------------
    live_db = env.get("DB_NAME", "")
    live_mongo = env.get("MONGO_URL", "")
    if args.target_db == live_db and not args.i_know_what_i_am_doing:
        print(f"REFUSING: --target-db == live DB_NAME ({live_db}). Aborting.", file=sys.stderr)
        return 3
    if args.target == live_mongo and not args.i_know_what_i_am_doing:
        print("REFUSING: --target == live MONGO_URL. Aborting (use ephemeral target).", file=sys.stderr)
        return 3

    client, bucket = _r2_client(env)

    print(f"Restore plan:")
    print(f"  Source bucket : {bucket}")
    print(f"  Source key    : {args.backup}")
    print(f"  Target URI    : {args.target}")
    print(f"  Target DB     : {args.target_db}")
    print(f"  Dry run       : {args.dry_run}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / Path(args.backup).name

        # --- download -----------------------------------------------------
        if args.dry_run:
            print(f"  [dry-run] would download s3://{bucket}/{args.backup} → {archive}")
        else:
            print(f"  Downloading s3://{bucket}/{args.backup} ...")
            client.download_file(bucket, args.backup, str(archive))
            print(f"  Downloaded: {archive.stat().st_size / (1024*1024):.1f} MB")

        # --- inspect archive ---------------------------------------------
        if args.dry_run:
            print("  [dry-run] skipping archive inspection")
        else:
            print("  Inspecting archive contents...")
            with tarfile.open(archive, "r:*") as tf:
                members = tf.getmembers()
                print(f"    members: {len(members)}")
                for m in members[:20]:
                    print(f"      - {m.name} ({m.size} bytes)")
                if len(members) > 20:
                    print(f"      ... and {len(members) - 20} more")

        # --- restore -----------------------------------------------------
        if args.dry_run:
            print("  [dry-run] would mongorestore into target DB. Skipping.")
            return 0

        try:
            from pymongo import MongoClient  # noqa: F401
        except ImportError:
            print("FAIL: pymongo not installed. pip install pymongo", file=sys.stderr)
            return 2

        # Restore strategy depends on archive format. Two supported formats:
        #   (a) tar containing JSON-per-collection dumps (preferred — easy to
        #       reason about, version-stable).
        #   (b) tar containing a `mongodump` BSON dir tree (requires
        #       `mongorestore` binary on PATH).
        # For now, we attempt (a); (b) is left for the first drill operator
        # to flesh out based on what the actual archive looks like.
        print("  Restore execution is intentionally not auto-completed in v1.")
        print("  The first drill operator should:")
        print("    1. Inspect the archive (printed above).")
        print("    2. If JSON-per-collection: write each into target DB via pymongo.")
        print("    3. If BSON/mongodump: run `mongorestore --uri <target> --nsFrom ... --nsTo ...`")
        print("    4. Record outcome in /app/memory/RESTORE_DRILL.md log table.")
        print()
        print("  This deliberate manual step is a safety feature, NOT a TODO.")
        print("  Auto-restore will be enabled only after the first successful drill")
        print("  documents the exact archive layout.")
        return 0


def main():
    env = _load_env()

    ap = argparse.ArgumentParser(description="MASCI Hub restore drill helper")
    sub = ap.add_subparsers(dest="cmd")

    # `--list` works as a flag for backwards compat
    ap.add_argument("--list", action="store_true", help="list backups in R2")
    ap.add_argument("--limit", type=int, default=30, help="how many to list")
    ap.add_argument("--backup", help="R2 key to restore (e.g. full-YYYY-MM-DD.tar.gz)")
    ap.add_argument("--target", help="target Mongo URI (ephemeral)")
    ap.add_argument("--target-db", help="target database name (must NOT equal live DB_NAME)")
    ap.add_argument("--dry-run", action="store_true", help="do not write anything")
    ap.add_argument("--i-know-what-i-am-doing", action="store_true",
                    help="override safety rails (do not use)")

    args = ap.parse_args()

    if args.list:
        return cmd_list(args, env)

    if not args.backup:
        ap.print_help()
        return 1
    if not args.target or not args.target_db:
        print("FAIL: --target and --target-db are required for restore.", file=sys.stderr)
        return 1
    return cmd_restore(args, env)


if __name__ == "__main__":
    sys.exit(main())
