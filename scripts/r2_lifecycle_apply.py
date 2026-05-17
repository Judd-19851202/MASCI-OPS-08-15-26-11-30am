#!/usr/bin/env python3
"""r2_lifecycle_apply.py — apply MASCI Hub R2 90-day lifecycle rule.

PURPOSE
    Configure Cloudflare R2 to auto-expire MASCI Hub backups 90 days after
    creation, scoped to a sub-prefix that contains ONLY new backups written
    after iter184. Legacy backups (under the bare ``backups/`` prefix) are
    intentionally NOT covered → no retroactive deletion (per user mandate).

WHY A SUB-PREFIX?
    Cloudflare R2 lifecycle filters support prefix-based scoping only (no
    tag filters as of 2026-02). Applying a 90-day expiration to the bare
    ``backups/`` prefix would delete months of existing history on the
    first lifecycle sweep. To avoid that:
        1. server.py now writes new backups to ``backups/auto-90d/<file>``
        2. This script applies the 90-day rule to that sub-prefix ONLY
        3. Legacy backups under just ``backups/*.zip`` remain forever
           until the operator chooses to clean them up manually.

USAGE
    # Apply / re-apply the rule (idempotent)
    python3 scripts/r2_lifecycle_apply.py

    # Show the rule that would be applied without doing it
    python3 scripts/r2_lifecycle_apply.py --dry-run

    # Show the bucket's current lifecycle config
    python3 scripts/r2_lifecycle_apply.py --show

REQUIRED ENV (read from /app/backend/.env if present)
    S3_ENDPOINT_URL, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION

This script is SAFE to run repeatedly — it issues PutBucketLifecycleConfiguration
with the full desired ruleset every time (idempotent), preserving any
non-MASCI rules already present under different IDs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"

RULE_ID = "masci-backups-auto-90d"
RULE_PREFIX = "backups/auto-90d/"
EXPIRATION_DAYS = 90


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
        sys.exit(2)
    missing = [k for k in ("S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY") if not env.get(k)]
    if missing:
        print(f"FAIL: missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    return boto3.client(
        "s3",
        endpoint_url=env["S3_ENDPOINT_URL"],
        aws_access_key_id=env["S3_ACCESS_KEY"],
        aws_secret_access_key=env["S3_SECRET_KEY"],
        region_name=env.get("S3_REGION") or "auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def desired_rule() -> dict:
    """Return the desired MASCI lifecycle rule as boto3 expects it."""
    return {
        "ID": RULE_ID,
        "Status": "Enabled",
        "Filter": {"Prefix": RULE_PREFIX},
        "Expiration": {"Days": EXPIRATION_DAYS},
        # Also clean up any aborted multipart uploads that linger >7 days
        # under the same sub-prefix. Cheap insurance.
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
    }


def fetch_current(client, bucket: str):
    try:
        resp = client.get_bucket_lifecycle_configuration(Bucket=bucket)
        return resp.get("Rules", [])
    except Exception as e:
        msg = str(e)
        if "NoSuchLifecycleConfiguration" in msg or "NoSuchLifecycle" in msg:
            return []
        # R2 sometimes returns AccessDenied when no config is set — treat
        # as empty rather than fatal so we can apply for the first time.
        if "AccessDenied" in msg:
            print("  (note: GetBucketLifecycle returned AccessDenied — treating as empty)", file=sys.stderr)
            return []
        raise


def merge_rules(current: list[dict], desired: dict) -> list[dict]:
    """Replace any existing rule with our ID; preserve others as-is."""
    merged = [r for r in current if r.get("ID") != desired["ID"]]
    merged.append(desired)
    return merged


def cmd_show(args, env):
    client = _client(env)
    bucket = env["S3_BUCKET"]
    rules = fetch_current(client, bucket)
    print(f"Bucket: {bucket}")
    print(f"Current lifecycle rules: {len(rules)}")
    print(json.dumps(rules, indent=2, default=str))
    return 0


def cmd_apply(args, env):
    client = _client(env)
    bucket = env["S3_BUCKET"]
    desired = desired_rule()
    current = fetch_current(client, bucket)
    new_rules = merge_rules(current, desired)

    print(f"Bucket            : {bucket}")
    print(f"Rule ID           : {RULE_ID}")
    print(f"Filter prefix     : {RULE_PREFIX}")
    print(f"Expiration (days) : {EXPIRATION_DAYS}")
    print(f"Rules before      : {len(current)}")
    print(f"Rules after       : {len(new_rules)}")
    print("-" * 60)
    print("Will PUT:")
    print(json.dumps(new_rules, indent=2, default=str))
    print("-" * 60)

    if args.dry_run:
        print("DRY-RUN — no changes applied.")
        return 0

    try:
        client.put_bucket_lifecycle_configuration(
            Bucket=bucket,
            LifecycleConfiguration={"Rules": new_rules},
        )
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "AccessDenied" in msg or "403" in msg:
            print("", file=sys.stderr)
            print("❌ FAIL: AccessDenied on PutBucketLifecycleConfiguration.", file=sys.stderr)
            print("", file=sys.stderr)
            print("The R2 API token in backend/.env lacks lifecycle:write.", file=sys.stderr)
            print("Cloudflare's standard 'Object Read & Write' scope is NOT", file=sys.stderr)
            print("sufficient. You need either:", file=sys.stderr)
            print("  • Account → API Tokens → Custom token with", file=sys.stderr)
            print("    'Workers R2 Storage' = Edit (account-scoped), OR", file=sys.stderr)
            print("  • R2 'Admin Read & Write' bucket token", file=sys.stderr)
            print("", file=sys.stderr)
            print("After issuing a new token:", file=sys.stderr)
            print("  1. Update S3_ACCESS_KEY / S3_SECRET_KEY in backend/.env", file=sys.stderr)
            print("  2. sudo supervisorctl restart backend", file=sys.stderr)
            print("  3. Re-run: python3 scripts/r2_lifecycle_apply.py", file=sys.stderr)
            print("", file=sys.stderr)
            print("Until then, the new sub-prefix backups/auto-90d/ will accumulate", file=sys.stderr)
            print("without expiration. No data is at risk; the cleanup is just deferred.", file=sys.stderr)
            return 4
        raise
    print("✅ Lifecycle applied.")

    # Verify by reading back.
    verify = fetch_current(client, bucket)
    ours = [r for r in verify if r.get("ID") == RULE_ID]
    if not ours:
        print("⚠️  WARNING: rule not present after read-back. R2 may be eventually consistent.")
        return 1
    print(f"✅ Verified — rule '{RULE_ID}' present (Status={ours[0].get('Status')}).")
    return 0


def cmd_verify(args, env):
    """Sentinel-based lifecycle verification (Phase 2 Round 2, Initiative 3).

    Procedure:
      1. Write a tiny sentinel object under backups/auto-90d/_sentinel.txt
      2. Read it back to confirm round-trip
      3. Re-fetch the bucket's lifecycle config and confirm our rule is
         present, enabled, and targets the right prefix
      4. Delete the sentinel object so we don't accumulate clutter

    Safe to run repeatedly. Returns 0 on full success, non-zero on any
    step failure (with explicit reason).
    """
    client = _client(env)
    bucket = env["S3_BUCKET"]
    sentinel_key = "backups/auto-90d/_sentinel.txt"
    payload = f"masci-hub r2 lifecycle sentinel · {datetime.utcnow().isoformat()}Z".encode()

    print(f"Bucket : {bucket}")
    print(f"Key    : {sentinel_key}")
    print("-" * 60)

    # Step 1 — write
    try:
        client.put_object(Bucket=bucket, Key=sentinel_key, Body=payload,
                          ContentType="text/plain")
        print("✅ Step 1 — wrote sentinel object")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Step 1 — write failed: {e}", file=sys.stderr)
        return 4

    # Step 2 — read-back
    try:
        resp = client.get_object(Bucket=bucket, Key=sentinel_key)
        body = resp["Body"].read()
        if body != payload:
            print("❌ Step 2 — read-back mismatch", file=sys.stderr)
            return 5
        print("✅ Step 2 — read-back matches")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Step 2 — read failed: {e}", file=sys.stderr)
        return 5

    # Step 3 — confirm lifecycle present + enabled + targets right prefix
    rules = fetch_current(client, bucket)
    ours = [r for r in rules if r.get("ID") == RULE_ID]
    if not ours:
        print(f"⚠️  Step 3 — rule '{RULE_ID}' NOT found in lifecycle config.",
              file=sys.stderr)
        print("   New objects will accumulate WITHOUT expiration until the",
              file=sys.stderr)
        print("   rule is applied (python3 scripts/r2_lifecycle_apply.py).",
              file=sys.stderr)
        rc = 6
    else:
        r = ours[0]
        status = r.get("Status", "")
        flt = (r.get("Filter") or {}).get("Prefix", "")
        days = (r.get("Expiration") or {}).get("Days")
        ok = (status == "Enabled" and flt == RULE_PREFIX and days == EXPIRATION_DAYS)
        msg = f"Status={status} Prefix={flt} Days={days}"
        if ok:
            print(f"✅ Step 3 — lifecycle rule active · {msg}")
            rc = 0
        else:
            print(f"❌ Step 3 — lifecycle rule misconfigured · {msg}", file=sys.stderr)
            rc = 7

    # Step 4 — clean up the sentinel regardless of step 3 outcome
    try:
        client.delete_object(Bucket=bucket, Key=sentinel_key)
        print("✅ Step 4 — sentinel cleaned up")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  Step 4 — sentinel cleanup failed (will expire via lifecycle "
              f"if rule is active): {e}", file=sys.stderr)

    return rc


def main():
    env = _load_env()
    ap = argparse.ArgumentParser(description="MASCI R2 lifecycle apply")
    ap.add_argument("--dry-run", action="store_true", help="show plan without applying")
    ap.add_argument("--show", action="store_true", help="just show current config")
    ap.add_argument("--verify", action="store_true",
                    help="round-trip sentinel + confirm lifecycle rule active")
    args = ap.parse_args()

    if args.show:
        return cmd_show(args, env)
    if args.verify:
        return cmd_verify(args, env)
    return cmd_apply(args, env)


if __name__ == "__main__":
    sys.exit(main())
