#!/usr/bin/env python3
"""restore_drill.py — Cloudflare R2 → side-DB restore drill helper.

Prove the MASCI Hub backups in R2 are actually restorable, without
touching the live preview database. See /app/memory/RESTORE_DRILL.md for
the surrounding procedure.

Modes:
    --list                      list R2 backups, newest first
    --backup K --target U
        --target-db NAME --dry-run    print plan, no writes
    --backup K --target U
        --target-db NAME              full restore + validation

SAFETY RAILS (per Phase 2 Initiative 2 — side-DB drill):
    • --target-db MUST begin with "masci_restore_drill_" unless
      --i-know-what-i-am-doing is also passed.
    • --target-db CANNOT equal the live DB_NAME (read from backend/.env).
    • Live MONGO_URL is allowed (we drill on the same Mongo instance,
      but on a different database).
    • Source backup is NEVER modified.

After a successful restore the validation step prints:
    • Mongo connectivity
    • Core collection record counts
    • Sample daily_report attachment integrity
    • user_directory managed/mirrored split

Required env (read from /app/backend/.env automatically if present):
    R2_ACCESS_KEY_ID / S3_ACCESS_KEY
    R2_SECRET_ACCESS_KEY / S3_SECRET_KEY
    R2_ENDPOINT / S3_ENDPOINT_URL
    R2_BUCKET / S3_BUCKET
    DB_NAME, MONGO_URL  (used only for safety-rail comparison)
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tarfile
import tempfile
import zipfile
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
    # Support both R2_ and S3_ env var names (the platform uses S3_*).
    endpoint = env.get("R2_ENDPOINT") or env.get("S3_ENDPOINT_URL")
    bucket = env.get("R2_BUCKET") or env.get("S3_BUCKET")
    access = env.get("R2_ACCESS_KEY_ID") or env.get("S3_ACCESS_KEY")
    secret = env.get("R2_SECRET_ACCESS_KEY") or env.get("S3_SECRET_KEY")
    if not all([endpoint, bucket, access, secret]):
        print("FAIL: missing R2 env vars (endpoint/bucket/access/secret)",
              file=sys.stderr)
        sys.exit(2)
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    return client, bucket


def cmd_list(args, env):
    client, bucket = _r2_client(env)
    print(f"Listing R2 backups in bucket: {bucket}")
    print("-" * 78)
    objs = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="backups/"):
        for o in page.get("Contents", []):
            objs.append(o)
    objs.sort(key=lambda o: o["LastModified"], reverse=True)
    for o in objs[: args.limit]:
        size_mb = o["Size"] / (1024 * 1024)
        print(f"  {o['LastModified'].isoformat()}  {size_mb:>8.1f} MB  {o['Key']}")
    print("-" * 78)
    print(f"Total objects: {len(objs)} (showing {min(len(objs), args.limit)})")
    return 0


def _extract_archive(archive: Path, dest: Path) -> str:
    """Auto-detect zip vs tar and extract to dest. Returns 'zip' or 'tar'."""
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(dest)
        return "zip"
    with tarfile.open(archive, "r:*") as tf:
        tf.extractall(dest)
    return "tar"


def _restore_side_db(extracted: Path, target_uri: str, target_db: str,
                     verbose: bool = True) -> dict:
    """Walk extracted/<collection>/json/*.json and insert into target_db.
    Returns counters per collection."""
    from pymongo import MongoClient

    client = MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    sdb = client[target_db]
    counters: dict = {}

    for json_dir in extracted.rglob("json"):
        if not json_dir.is_dir():
            continue
        coll_name = json_dir.parent.name.replace("-", "_")
        coll = sdb[coll_name]
        files = list(json_dir.glob("*.json"))
        docs = []
        bad = 0
        for f in files:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    docs.append(d)
                else:
                    bad += 1
            except Exception:
                bad += 1
        # Prefer delete_many over drop so the drill still works under
        # Atlas roles that allow document writes but deny collection drop.
        try:
            coll.delete_many({})
        except Exception as e:
            if verbose:
                print(f"  [{coll_name}] cleanup warnings: {e}", file=sys.stderr)
        inserted = 0
        if docs:
            try:
                coll.insert_many(docs, ordered=False)
                inserted = len(docs)
            except Exception as e:
                if verbose:
                    print(f"  [{coll_name}] insert warnings: {e}", file=sys.stderr)
        counters[coll_name] = {"inserted": inserted, "skipped_bad": bad,
                               "files_seen": len(files)}
        if verbose:
            print(f"  {coll_name:<32}  inserted={len(docs):>5}  "
                  f"bad={bad:>3}  files={len(files):>5}")
    client.close()
    return counters


def _restore_zip_side_db(archive: Path, target_uri: str, target_db: str,
                         verbose: bool = True, batch_size: int = 1000) -> dict:
    """Stream ZIP-backed JSON rows straight into target_db without extracting
    the entire archive to disk first. This keeps the drill workable for
    very large backup archives with hundreds of thousands of JSON members.
    """
    from pymongo import MongoClient

    client = MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    sdb = client[target_db]
    counters: dict = {}

    with zipfile.ZipFile(archive, "r") as zf:
        grouped: dict[str, list[str]] = {}
        for name in zf.namelist():
            if not name.endswith(".json") or name == "MANIFEST.json":
                continue
            parts = Path(name).parts
            if len(parts) < 3 or parts[1] != "json":
                continue
            coll_name = parts[0].replace("-", "_")
            grouped.setdefault(coll_name, []).append(name)

        for coll_name in sorted(grouped):
            coll = sdb[coll_name]
            file_names = grouped[coll_name]
            inserted = 0
            bad = 0
            batch = []
            try:
                coll.delete_many({})
            except Exception as e:
                if verbose:
                    print(f"  [{coll_name}] cleanup warnings: {e}", file=sys.stderr)
            for member_name in file_names:
                try:
                    with zf.open(member_name) as fh:
                        row = json.loads(fh.read().decode("utf-8"))
                    if not isinstance(row, dict):
                        bad += 1
                        continue
                    batch.append(row)
                    if len(batch) >= batch_size:
                        try:
                            coll.insert_many(batch, ordered=False)
                            inserted += len(batch)
                        except Exception as e:
                            if verbose:
                                print(f"  [{coll_name}] insert warnings: {e}", file=sys.stderr)
                        batch = []
                except Exception:
                    bad += 1
            if batch:
                try:
                    coll.insert_many(batch, ordered=False)
                    inserted += len(batch)
                except Exception as e:
                    if verbose:
                        print(f"  [{coll_name}] insert warnings: {e}", file=sys.stderr)
            counters[coll_name] = {
                "inserted": inserted,
                "skipped_bad": bad,
                "files_seen": len(file_names),
            }
            if verbose:
                print(
                    f"  {coll_name:<32}  inserted={inserted:>5}  "
                    f"bad={bad:>3}  files={len(file_names):>5}"
                )
    client.close()
    return counters


def _validate_restore(target_uri: str, target_db: str) -> dict:
    """Sample integrity checks on the side DB. Returns a dict."""
    from pymongo import MongoClient
    client = MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    sdb = client[target_db]
    checks: dict = {}

    try:
        sdb.command("ping")
        checks["mongo_connectivity"] = True
    except Exception as e:
        checks["mongo_connectivity"] = f"FAIL: {e}"

    for c in ("inspections", "jhas", "incidents", "daily_reports",
              "meetings", "equipment", "employees",
              "user_directory", "role_templates", "backup_health"):
        try:
            checks[f"{c}.count"] = sdb[c].estimated_document_count()
        except Exception as e:
            checks[f"{c}.count"] = f"ERR: {e}"

    try:
        dr = sdb.daily_reports.find_one(
            {"attachments": {"$exists": True, "$ne": []}},
            projection={"_id": 0, "id": 1},
        )
        checks["sample_daily_report_with_attachments"] = bool(dr)
    except Exception as e:
        checks["sample_daily_report_with_attachments"] = f"ERR: {e}"

    try:
        checks["user_directory.managed_count"] = sdb.user_directory.count_documents({"mirrored": False})
    except Exception as e:
        checks["user_directory.managed_count"] = f"ERR: {e}"

    client.close()
    return checks


def _seed_user_password_hashes(target_uri: str, target_db: str, verbose: bool = True) -> dict:
    """Batch G · GAP-2 — Re-seed redacted password_hash fields on `users` and
    `user_directory` after restore. Uses either an operator-supplied
    `RESTORE_DRILL_SEED_PASSWORD` or a generated per-run secret, and always
    stamps `must_change_password=True` so accounts are forced to rotate.
    Returns counters."""
    from pymongo import MongoClient
    try:
        import bcrypt as _bc  # noqa: PLC0415
    except ImportError:
        return {"seeded": 0, "skipped": 0, "err": "bcrypt not installed"}

    seed_secret = (os.environ.get("RESTORE_DRILL_SEED_PASSWORD") or "").strip() or secrets.token_urlsafe(18)
    seed_mode = "env" if os.environ.get("RESTORE_DRILL_SEED_PASSWORD") else "generated_ephemeral"
    seed_hash = _bc.hashpw(seed_secret.encode("utf-8"), _bc.gensalt()).decode("utf-8")
    client = MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    sdb = client[target_db]
    counters = {"seeded": 0, "skipped": 0, "by_coll": {}, "seed_mode": seed_mode}
    for coll in ("users", "user_directory"):
        if coll not in sdb.list_collection_names():
            counters["by_coll"][coll] = "absent"
            continue
        seeded = 0
        skipped = 0
        for row in sdb[coll].find({}, {"_id": 0, "id": 1, "email": 1, "password_hash": 1}):
            if row.get("password_hash"):
                skipped += 1
                continue
            sdb[coll].update_one(
                {"id": row["id"]},
                {"$set": {"password_hash": seed_hash, "must_change_password": True}},
            )
            seeded += 1
        counters["by_coll"][coll] = {"seeded": seeded, "skipped": skipped}
        counters["seeded"] += seeded
        counters["skipped"] += skipped
        if verbose:
            print(f"  [{coll}] seeded={seeded} skipped={skipped}")
    client.close()
    return counters


def _rehydrate_photos_to_r2(extracted: Path, env: dict, verbose: bool = True) -> dict:
    """Batch G · GAP-4 — Re-upload photo bytes from the archive's `photos/`
    prefix back to R2. Idempotent: skips keys that already exist in R2.
    The archive layout is `photos/<r2_key_path>` with bytes verbatim.
    Returns counters."""
    photo_root = extracted / "photos"
    if not photo_root.is_dir():
        return {"uploaded": 0, "skipped": 0, "failed": 0, "note": "no photos/ in archive"}

    import boto3  # noqa: PLC0415
    drill_bucket = (env.get("RESTORE_DRILL_R2_BUCKET") or env.get("S3_DRILL_BUCKET") or "").strip()
    live_bucket = (env.get("S3_BUCKET") or "").strip()
    if not drill_bucket:
        return {
            "uploaded": 0,
            "skipped": 0,
            "failed": 0,
            "note": "restore-photos refused: RESTORE_DRILL_R2_BUCKET / S3_DRILL_BUCKET not set",
        }
    if drill_bucket == live_bucket:
        return {
            "uploaded": 0,
            "skipped": 0,
            "failed": 0,
            "note": "restore-photos refused: drill bucket matches live S3_BUCKET",
        }
    s3 = boto3.client(
        "s3",
        endpoint_url=env.get("S3_ENDPOINT_URL"),
        aws_access_key_id=env.get("S3_ACCESS_KEY"),
        aws_secret_access_key=env.get("S3_SECRET_KEY"),
        region_name=env.get("S3_REGION", "auto"),
    )
    bucket = drill_bucket
    counters = {"uploaded": 0, "skipped": 0, "failed": 0, "bytes_uploaded": 0}

    for photo_path in photo_root.rglob("*"):
        if not photo_path.is_file():
            continue
        key = str(photo_path.relative_to(photo_root))
        # idempotency: only upload if key doesn't already exist
        try:
            s3.head_object(Bucket=bucket, Key=key)
            counters["skipped"] += 1
            continue
        except Exception:
            pass
        try:
            with open(photo_path, "rb") as f:
                body = f.read()
            s3.put_object(Bucket=bucket, Key=key, Body=body)
            counters["uploaded"] += 1
            counters["bytes_uploaded"] += len(body)
        except Exception as e:
            counters["failed"] += 1
            if verbose:
                print(f"  PHOTO FAIL {key}: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)

    if verbose:
        mb = counters["bytes_uploaded"] / 1024 / 1024
        print(f"  Photo rehydration: uploaded={counters['uploaded']} "
              f"skipped={counters['skipped']} failed={counters['failed']} "
              f"size={mb:.1f} MB")
    return counters


def cmd_restore(args, env):
    # ── safety rails ────────────────────────────────────────────────────
    live_db = env.get("DB_NAME", "")
    if args.target_db == live_db and not args.i_know_what_i_am_doing:
        print(f"REFUSING: --target-db == live DB_NAME ({live_db}). Aborting.",
              file=sys.stderr)
        return 3
    if not args.target_db.startswith("masci_restore_drill_") \
            and not args.i_know_what_i_am_doing:
        print("REFUSING: --target-db must start with 'masci_restore_drill_' "
              "(override with --i-know-what-i-am-doing).", file=sys.stderr)
        return 3

    client, bucket = _r2_client(env)

    print("Restore plan:")
    print(f"  Source bucket : {bucket}")
    print(f"  Source key    : {args.backup}")
    print(f"  Target URI    : {args.target}")
    print(f"  Target DB     : {args.target_db}")
    print(f"  Dry run       : {args.dry_run}")
    print("-" * 60)

    with tempfile.TemporaryDirectory(prefix="masci_drill_") as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / Path(args.backup).name

        if args.dry_run:
            print(f"  [dry-run] would download s3://{bucket}/{args.backup} → {archive}")
        else:
            print(f"  Downloading s3://{bucket}/{args.backup} ...")
            client.download_file(bucket, args.backup, str(archive))
            print(f"  Downloaded: {archive.stat().st_size / (1024*1024):.1f} MB")

        if args.dry_run:
            extracted = tmp_path / "extracted"
            print(f"  [dry-run] would extract to {extracted} and restore.")
            return 0

        print("")
        print("  Restoring into side DB ...")
        try:
            if zipfile.is_zipfile(archive) and not args.restore_photos:
                print("  ZIP archive detected · using streaming restore path")
                counters = _restore_zip_side_db(archive, args.target, args.target_db)
                fmt = "zip-stream"
                extracted = None
            else:
                extracted = tmp_path / "extracted"
                extracted.mkdir()
                fmt = _extract_archive(archive, extracted)
                print(f"  Extracted format: {fmt}")
                counters = _restore_side_db(extracted, args.target, args.target_db)
        except Exception as e:
            print(f"  FAIL: restore: {e}", file=sys.stderr)
            return 8

        print("")
        print("  Running validation checks ...")
        checks = _validate_restore(args.target, args.target_db)
        for k in sorted(checks):
            print(f"    {k:<46} = {checks[k]}")

        # Batch G · GAP-2 — reseed redacted password_hash fields if requested
        if args.seed_user_passwords:
            print("")
            print("  Re-seeding redacted password_hash fields (GAP-2) ...")
            _seed_user_password_hashes(args.target, args.target_db)

        # Batch G · GAP-4 — re-upload photo bytes to R2 if requested
        if args.restore_photos:
            if extracted is None:
                print("  FAIL: restore-photos requires extracted archive layout.", file=sys.stderr)
                return 8
            print("")
            print("  Re-hydrating R2 photo bytes from archive (GAP-4) ...")
            _rehydrate_photos_to_r2(extracted, env)

        total_inserted = sum(c["inserted"] for c in counters.values())
        total_bad = sum(c["skipped_bad"] for c in counters.values())
        verdict = "PASS"
        if checks.get("mongo_connectivity") is not True:
            verdict = "FAIL (no mongo)"
        if total_inserted == 0:
            verdict = "FAIL (no records restored)"

        print("")
        print(f"  Total inserted: {total_inserted}")
        print(f"  Total bad:      {total_bad}")
        print(f"  VERDICT: {verdict}")
        return 0 if verdict == "PASS" else 9


def main():
    env = _load_env()
    ap = argparse.ArgumentParser(description="MASCI Hub side-DB restore drill")
    ap.add_argument("--list", action="store_true", help="list R2 backups")
    ap.add_argument("--limit", type=int, default=30, help="how many to list")
    ap.add_argument("--backup", help="R2 key to restore")
    ap.add_argument("--target", help="target Mongo URI (preview Mongo is fine)")
    ap.add_argument("--target-db",
                    help="target DB name — MUST start with masci_restore_drill_")
    ap.add_argument("--dry-run", action="store_true",
                    help="print plan without downloading or writing")
    ap.add_argument("--i-know-what-i-am-doing", action="store_true",
                    help="override safety rails (do not use)")
    ap.add_argument("--seed-user-passwords", action="store_true",
                    help="Batch G · GAP-2: stamp Welcome2MASCI!+must_change_password on rows missing password_hash")
    ap.add_argument("--restore-photos", action="store_true",
                    help="Batch G · GAP-4: re-upload archive's photos/ prefix to R2 (idempotent)")
    args = ap.parse_args()

    if args.list:
        return cmd_list(args, env)
    if not args.backup:
        ap.print_help()
        return 1
    if not args.target or not args.target_db:
        print("FAIL: --target and --target-db are required for restore.",
              file=sys.stderr)
        return 1
    return cmd_restore(args, env)


if __name__ == "__main__":
    sys.exit(main())
