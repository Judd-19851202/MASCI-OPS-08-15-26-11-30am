#!/usr/bin/env python3
"""r2_usage_check.py — MASCI Hub R2 bucket usage probe + 50 GB alert.

Sums all object sizes in the configured R2 bucket and emits a status
suitable for cron-with-email or for piping into the backup scheduler's
warning log.

Exit codes:
    0  → bucket size below WARN threshold (default 45 GB)
    1  → between WARN and ALERT (default 45–50 GB)  → warn
    2  → at or above ALERT threshold (default 50 GB) → page

Usage:
    python3 scripts/r2_usage_check.py
    python3 scripts/r2_usage_check.py --json
    python3 scripts/r2_usage_check.py --warn-gb 40 --alert-gb 50
    python3 scripts/r2_usage_check.py --prefix backups/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
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


def _client(env: dict):
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("FAIL: boto3 not installed. pip install boto3", file=sys.stderr)
        sys.exit(3)
    missing = [k for k in ("S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY") if not env.get(k)]
    if missing:
        print(f"FAIL: missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(3)
    return boto3.client(
        "s3",
        endpoint_url=env["S3_ENDPOINT_URL"],
        aws_access_key_id=env["S3_ACCESS_KEY"],
        aws_secret_access_key=env["S3_SECRET_KEY"],
        region_name=env.get("S3_REGION") or "auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def summarize(client, bucket: str, prefix: str = "") -> dict:
    total_bytes = 0
    total_objects = 0
    by_prefix: dict[str, dict] = {}
    paginator = client.get_paginator("list_objects_v2")
    kwargs = {"Bucket": bucket}
    if prefix:
        kwargs["Prefix"] = prefix
    for page in paginator.paginate(**kwargs):
        for o in page.get("Contents", []):
            total_bytes += o["Size"]
            total_objects += 1
            top = o["Key"].split("/", 1)[0] + "/"
            row = by_prefix.setdefault(top, {"bytes": 0, "count": 0})
            row["bytes"] += o["Size"]
            row["count"] += 1
    return {
        "bucket": bucket,
        "scoped_prefix": prefix or None,
        "total_objects": total_objects,
        "total_bytes": total_bytes,
        "total_gb": round(total_bytes / (1024**3), 3),
        "by_top_prefix": by_prefix,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="", help="restrict to this prefix")
    ap.add_argument("--warn-gb", type=float, default=45.0)
    ap.add_argument("--alert-gb", type=float, default=50.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    env = _load_env()
    client = _client(env)
    bucket = env["S3_BUCKET"]
    summary = summarize(client, bucket, args.prefix)
    summary["thresholds"] = {"warn_gb": args.warn_gb, "alert_gb": args.alert_gb}

    total_gb = summary["total_gb"]
    if total_gb >= args.alert_gb:
        status = "alert"
        rc = 2
    elif total_gb >= args.warn_gb:
        status = "warn"
        rc = 1
    else:
        status = "ok"
        rc = 0
    summary["status"] = status

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(f"Bucket          : {summary['bucket']}")
        if summary["scoped_prefix"]:
            print(f"Prefix scope    : {summary['scoped_prefix']}")
        print(f"Objects         : {summary['total_objects']:,}")
        print(f"Total           : {total_gb:.2f} GB  ({summary['total_bytes']:,} bytes)")
        print(f"Status          : {status.upper()}  (warn={args.warn_gb} GB, alert={args.alert_gb} GB)")
        if summary["by_top_prefix"]:
            print("Top-level breakdown:")
            for p, row in sorted(summary["by_top_prefix"].items(), key=lambda kv: -kv[1]["bytes"]):
                gb = row["bytes"] / (1024**3)
                print(f"  {p:<24} {gb:>8.2f} GB  ({row['count']:,} objects)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
