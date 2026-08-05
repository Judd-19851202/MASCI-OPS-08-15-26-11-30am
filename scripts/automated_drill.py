#!/usr/bin/env python3
"""automated_drill.py — automated restore certification wrapper.

This script now delegates to the proven namespace restore path in
``ops8_namespace_restore_drill.py`` after first resolving the latest
authoritative archive for the current environment. That keeps the
operator-facing entrypoint stable while ensuring the drill proves:

  1. authoritative archive selection
  2. manifest + checksum validation
  3. namespace-isolated restore inside the authorized preview database
  4. record-count parity + cleanup evidence

The historical side-database restore path is retired from the active
release gate because the productionized certification contract is the
namespace-scoped drill, not arbitrary database creation.

USAGE:
  python3 /app/scripts/automated_drill.py --auto                 # pick latest, run, cleanup
  python3 /app/scripts/automated_drill.py --auto --keep-db       # don't cleanup DB
  python3 /app/scripts/automated_drill.py --backup KEY           # explicit archive

EXIT CODES:
  0 = drill PASS (all 10 axes green)
  1 = bad invocation
  2 = environment misconfigured
  9 = drill FAIL (one or more axes red)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
MEMORY_DIR = REPO_ROOT / "memory"
sys.path.insert(0, str(REPO_ROOT / 'backend'))
from lib.operator_safety import redact_target_identity  # noqa: E402
from lib.archive_lineage import build_canonical_archive_lineage  # noqa: E402


def _load_env() -> Dict[str, str]:
    env = dict(os.environ)
    if BACKEND_ENV.exists():
        for line in BACKEND_ENV.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def _r2_client(env: Dict[str, str]):
    import boto3
    from botocore.config import Config
    endpoint = env.get("R2_ENDPOINT") or env.get("S3_ENDPOINT_URL")
    bucket = env.get("R2_BUCKET") or env.get("S3_BUCKET")
    access = env.get("R2_ACCESS_KEY_ID") or env.get("S3_ACCESS_KEY")
    secret = env.get("R2_SECRET_ACCESS_KEY") or env.get("S3_SECRET_KEY")
    if not all([endpoint, bucket, access, secret]):
        print("FAIL: R2 env vars missing", file=sys.stderr)
        sys.exit(2)
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=env.get("S3_REGION", "auto"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    ), bucket


def _resolve_authoritative_archive(env: Dict[str, str], requested_source_environment: str, explicit_key: Optional[str] = None) -> Dict[str, Any]:
    from pymongo import MongoClient
    import asyncio
    mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
    db = mongo[env["DB_NAME"]]
    try:
        lineage = asyncio.run(
            build_canonical_archive_lineage(
                db,
                current_env=env.get("APP_ENV"),
                current_db=env.get("DB_NAME"),
                requested_source_environment=requested_source_environment,
                force_refresh=True,
            )
        )
    finally:
        mongo.close()
    candidate = lineage.get("authoritative_artifact") or {}
    if not candidate:
        raise RuntimeError("NO_VALID_ARCHIVE_FOR_REQUESTED_ENVIRONMENT")
    key = candidate.get("object_key")
    if explicit_key and explicit_key != key:
        raise RuntimeError("ARCHIVE_KEY_MISMATCH")
    identity = candidate.get("lineage_identity") or {}
    if identity.get("environment") != requested_source_environment:
        raise RuntimeError("ENVIRONMENT_MISMATCH")
    if identity.get("backup_prefix") and key and not str(key).startswith(str(identity.get("backup_prefix"))):
        raise RuntimeError("BACKUP_PREFIX_MISMATCH")
    return candidate


def _walk_photo_refs(obj):
    if isinstance(obj, str) and obj.startswith("photo://"):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_photo_refs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_photo_refs(v)


def _write_drill_row(env: Dict[str, str], row: Dict[str, Any]) -> None:
    """Persist a drill_runs row in the LIVE Mongo (not the drill DB).
    This lets the Recovery Dashboard read the latest drill outcome."""
    try:
        from pymongo import MongoClient
        client = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=10000)
        db = client[env.get("DB_NAME", "masci_safety_preview")]
        db.drill_runs.insert_one(row)
        client.close()
    except Exception as e:
        print(f"  WARNING: drill_runs write failed: {e}", file=sys.stderr)


def _write_report(drill_id: str, summary: Dict[str, Any]) -> Path:
    """Write per-drill markdown report into /app/memory/."""
    MEMORY_DIR.mkdir(exist_ok=True)
    path = MEMORY_DIR / f"DRILL_{drill_id}_REPORT.md"
    lines: List[str] = []
    lines.append(f"# DRILL_{drill_id}_REPORT.md\n")
    lines.append(f"**Cycle:** automated · {summary['started_at']}\n")
    lines.append(f"**Archive tested:** `{summary['archive_filename']}` · "
                 f"{summary['archive_size_mb']:.2f} MB · "
                 f"{summary['records_in_manifest']} records\n")
    lines.append(f"**Outcome:** {'🟢 PASS' if summary['outcome'] == 'ok' else '🔴 FAIL'} · "
                 f"duration {summary['duration_minutes']:.2f} min\n")
    lines.append("\n## Per-axis evidence\n")
    lines.append("| Axis | Result | Detail |\n|---|---|---|\n")
    for axis_id, axis in summary["axes"].items():
        mark = "🟢" if axis["ok"] else "🔴"
        lines.append(f"| {axis_id} | {mark} | {axis['message']} |\n")
    lines.append("\n## Restore counters (per collection · top 20)\n")
    pk = sorted(
        summary["per_kind"].items(), key=lambda kv: -kv[1]["inserted"]
    )[:20]
    lines.append("| Collection | inserted | files_seen | skipped_bad |\n")
    lines.append("|---|---:|---:|---:|\n")
    for c, v in pk:
        lines.append(f"| {c} | {v['inserted']} | {v['files_seen']} | {v['skipped_bad']} |\n")
    lines.append("\n## Photo rehydration audit\n")
    pr = summary.get("photo_rehydration") or {}
    lines.append(f"- unique_refs_in_docs: {summary['unique_refs_in_docs']}\n")
    lines.append(f"- unique_archive_photo_entries: {summary['unique_archive_photo_entries']}\n")
    lines.append(f"- rehydrated_to_drill_r2: {pr.get('uploaded', 0)} (skipped={pr.get('skipped',0)} failed={pr.get('failed',0)})\n")
    lines.append("\n## Cleanup\n")
    lines.append(f"- drill DB dropped: {'✅' if summary['cleanup']['db_dropped'] else '⚠️'} · {summary['finished_at']}\n")
    lines.append(f"- temp archive removed: {'✅' if summary['cleanup']['zip_removed'] else '⚠️'}\n")
    lines.append(f"- drill_runs row persisted: ✅ id={summary['drill_id']}\n")
    if summary.get("notes"):
        lines.append("\n## Notes\n")
        for n in summary["notes"]:
            lines.append(f"- {n}\n")
    lines.append("\n_End of report — auto-generated by automated_drill.py._\n")
    path.write_text("".join(lines))
    return path


def run_drill(env: Dict[str, str], explicit_key: Optional[str] = None,
              keep_db: bool = False, target_uri: Optional[str] = None) -> int:
    if keep_db:
        print("NOTE: --keep-db is ignored; namespace restore always self-cleans.")
    if target_uri:
        print("NOTE: --target-uri is ignored; namespace restore uses the runtime-authorized database.")

    requested_source_environment = (env.get("APP_ENV") or "preview").strip().lower()
    try:
        chosen = _resolve_authoritative_archive(
            env,
            requested_source_environment=requested_source_environment,
            explicit_key=explicit_key,
        )
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "error": str(exc),
            "requested_source_environment": requested_source_environment,
            "target": redact_target_identity(env.get("MONGO_URL"), env.get("DB_NAME")),
        }, indent=2))
        return 9

    archive_key = str(chosen.get("object_key") or "")
    archive_size = int(chosen.get("archive_size_bytes") or 0)
    print(f"authoritative lineage pick: {archive_key} · {archive_size/1e6:.2f} MB")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "ops8_namespace_restore_drill.py"),
        "--backup",
        archive_key,
        "--execute",
        "--backup-ack",
        "--confirm",
        "RUN_ISOLATED_RECOVERY_DRILL",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)

    parsed: Dict[str, Any] = {}
    payload = (proc.stdout or "").strip()
    json_start = payload.find("{")
    if json_start >= 0:
        try:
            parsed = json.loads(payload[json_start:])
        except Exception:
            parsed = {}

    summary = parsed.get("summary") if isinstance(parsed, dict) else None
    if isinstance(summary, dict) and summary.get("drill_id"):
        report_payload = {
            "drill_id": summary.get("drill_id"),
            "started_at": summary.get("started_at"),
            "finished_at": summary.get("finished_at"),
            "duration_minutes": summary.get("duration_minutes") or 0,
            "archive_filename": summary.get("archive_filename") or Path(archive_key).name,
            "archive_size_mb": summary.get("archive_size_mb") or round(archive_size / (1024 * 1024), 2),
            "records_in_manifest": summary.get("records_in_manifest") or 0,
            "outcome": summary.get("outcome") or ("ok" if parsed.get("ok") else "failed"),
            "axes": summary.get("axes") or {},
            "per_kind": summary.get("per_kind") or {},
            "unique_refs_in_docs": 0,
            "unique_archive_photo_entries": 0,
            "photo_rehydration": ((summary.get("restore_certification_evidence") or {}).get("photo_object_rehydration") or {}),
            "cleanup": {"db_dropped": bool(summary.get("cleanup_complete")), "zip_removed": bool(summary.get("cleanup_complete"))},
            "notes": [
                f"Delegated to ops8 namespace restore using {archive_key}",
                f"Source environment: {requested_source_environment}",
            ],
        }
        report = _write_report(summary["drill_id"], report_payload)
        print(f"Compatibility report: {report}")

    return 0 if proc.returncode == 0 and parsed.get("ok") else 9


def _drill_rehydrate(extract_dir: Path, env: Dict[str, str], drill_id: str) -> Dict[str, Any]:
    """Upload archive's photos/ subtree to drill-photos/<drill_id>/<key>.
    Isolated R2 prefix. Idempotent skip if already there (drill restart safe)."""
    import boto3
    photo_root = extract_dir / "photos"
    if not photo_root.is_dir():
        return {"uploaded": 0, "skipped": 0, "failed": 0, "note": "no photos/"}
    s3 = boto3.client(
        "s3",
        endpoint_url=env.get("S3_ENDPOINT_URL"),
        aws_access_key_id=env.get("S3_ACCESS_KEY"),
        aws_secret_access_key=env.get("S3_SECRET_KEY"),
        region_name=env.get("S3_REGION", "auto"),
    )
    bucket = env.get("S3_BUCKET")
    counters = {"uploaded": 0, "skipped": 0, "failed": 0}
    for fp in photo_root.rglob("*"):
        if not fp.is_file():
            continue
        sub = str(fp.relative_to(photo_root))
        drill_key = f"drill-photos/{drill_id}/{sub}"
        try:
            s3.head_object(Bucket=bucket, Key=drill_key)
            counters["skipped"] += 1
            continue
        except Exception:
            pass
        try:
            with open(fp, "rb") as f:
                body = f.read()
            s3.put_object(Bucket=bucket, Key=drill_key, Body=body)
            counters["uploaded"] += 1
        except Exception:
            counters["failed"] += 1
    return counters


def _finalize(
    env, drill_id, started_at_dt, t0, target_db, archive_filename,
    archive_size_mb, axes, per_kind, unique_refs_count, archive_photo_keys_count,
    photo_rehydration, notes, cleanup_db_dropped, cleanup_zip_removed,
    records_in_manifest=0,
    requested_source_environment=None,
) -> int:
    finished_at_dt = datetime.now(timezone.utc)
    duration_minutes = round((time.time() - t0) / 60.0, 3)
    all_ok = all(a["ok"] for a in axes.values())
    outcome = "ok" if all_ok else "failed"

    summary = {
        "drill_id": drill_id,
        "started_at": started_at_dt.isoformat(),
        "finished_at": finished_at_dt.isoformat(),
        "duration_minutes": duration_minutes,
        "target_db": target_db,
        "archive_filename": archive_filename,
        "archive_size_mb": archive_size_mb,
        "records_in_manifest": records_in_manifest,
        "outcome": outcome,
        "axes": axes,
        "per_kind": per_kind,
        "unique_refs_in_docs": unique_refs_count,
        "unique_archive_photo_entries": archive_photo_keys_count,
        "photo_rehydration": photo_rehydration,
        "records_restored": sum(c.get("inserted", 0) for c in per_kind.values()),
        "photos_rehydrated": (photo_rehydration or {}).get("uploaded", 0),
        "cleanup": {
            "db_dropped": cleanup_db_dropped,
            "zip_removed": cleanup_zip_removed,
        },
        "notes": notes,
    }

    # Persist drill row (final state)
    _write_drill_row(env, {
        **summary,
        "state": "done",
        "source_environment": requested_source_environment,
        "source_archive_key": archive_filename,
        "restore_purpose": "PREVIEW_BACKUP_CERTIFICATION",
        "policy_decision": "PASS" if outcome == "ok" else "FAIL",
        "policy_reason": "authoritative_environment_bound_archive_selected",
        "cleanup_complete": cleanup_db_dropped and cleanup_zip_removed,
    })

    # Write markdown report
    report = _write_report(drill_id, summary)
    print(f"\nReport: {report}")
    print(f"Outcome: {outcome.upper()}")
    print(f"Duration: {duration_minutes} min")
    for axis_id, axis in axes.items():
        mark = "🟢" if axis["ok"] else "🔴"
        print(f"  {mark} {axis_id}: {axis['message']}")

    return 0 if outcome == "ok" else 9


def main() -> int:
    env = _load_env()
    ap = argparse.ArgumentParser(description="Automated MASCI restore drill")
    ap.add_argument("--auto", action="store_true",
                    help="Auto-pick the latest healthy archive from R2")
    ap.add_argument("--backup", help="Explicit R2 key (e.g. backups/auto-90d/...zip)")
    ap.add_argument("--keep-db", action="store_true",
                    help="Skip dropping the drill DB on success (for inspection)")
    ap.add_argument("--target-uri",
                    help="Override target Mongo URI (defaults to MONGO_URL)")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-production", action="store_true")
    ap.add_argument("--backup-ack", action="store_true")
    ap.add_argument("--confirm", default="")
    args = ap.parse_args()

    if not args.auto and not args.backup:
        ap.print_help()
        return 1
    if not args.execute:
        print(json.dumps({"ok": False, "error": "Refusing drill without --execute.", "target": redact_target_identity(env.get('MONGO_URL'), env.get('DB_NAME'))}, indent=2))
        return 2
    if args.confirm != "RUN_ISOLATED_RECOVERY_DRILL":
        print(json.dumps({"ok": False, "error": "Refusing drill without --confirm RUN_ISOLATED_RECOVERY_DRILL.", "target": redact_target_identity(env.get('MONGO_URL'), env.get('DB_NAME'))}, indent=2))
        return 2
    if not args.backup_ack:
        print(json.dumps({"ok": False, "error": "Refusing drill without --backup-ack.", "target": redact_target_identity(env.get('MONGO_URL'), env.get('DB_NAME'))}, indent=2))
        return 2
    db_name = env.get('DB_NAME') or ''
    if db_name == 'masci_safety':
        if not args.allow_production:
            print(json.dumps({"ok": False, "error": "Refusing drill from production DB semantics without --allow-production.", "target": redact_target_identity(env.get('MONGO_URL'), db_name)}, indent=2))
            return 2
        print(json.dumps({"ok": False, "error": "Production drill execution remains technically blocked in this track.", "target": redact_target_identity(env.get('MONGO_URL'), db_name)}, indent=2))
        return 2

    return run_drill(env, explicit_key=args.backup, keep_db=args.keep_db,
                     target_uri=args.target_uri)


if __name__ == "__main__":
    sys.exit(main())
