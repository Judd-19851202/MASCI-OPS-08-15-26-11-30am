#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

import boto3
from botocore.config import Config
from pymongo import MongoClient, UpdateOne


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
MEMORY_DIR = REPO_ROOT / "memory"
sys.path.insert(0, str(REPO_ROOT / "backend"))
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


def _walk_photo_refs(obj: Any) -> Iterable[str]:
    if isinstance(obj, str) and obj.startswith("photo://"):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _walk_photo_refs(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_photo_refs(value)


def _r2_client(env: Dict[str, str]):
    endpoint = env.get("R2_ENDPOINT") or env.get("S3_ENDPOINT_URL")
    bucket = env.get("R2_BUCKET") or env.get("S3_BUCKET")
    access = env.get("R2_ACCESS_KEY_ID") or env.get("S3_ACCESS_KEY")
    secret = env.get("R2_SECRET_ACCESS_KEY") or env.get("S3_SECRET_KEY")
    if not all([endpoint, bucket, access, secret]):
        raise RuntimeError("R2 env vars missing")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=env.get("S3_REGION", "auto"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    ), bucket


def _restore_prefixed(zf: zipfile.ZipFile, db, prefix: str) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    aggregated_members = [
        name for name in zf.namelist()
        if name.startswith("collections/") and name.endswith(".json")
    ]
    for name in aggregated_members:
        coll = Path(name).stem.replace("-", "_")
        data = json.loads(zf.read(name).decode("utf-8"))
        docs = data if isinstance(data, list) else [data]
        clean = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            row = dict(doc)
            row.pop("_id", None)
            clean.append(row)
        if clean:
            target = db[f"{prefix}__{coll}"]
            target.drop()
            target.insert_many(clean, ordered=False)
        counts[coll] = {"inserted": len(clean), "files_seen": 1, "skipped_bad": 0}
    if aggregated_members:
        return counts

    grouped: Dict[str, list[dict]] = {}
    for name in zf.namelist():
        if name == "MANIFEST.json" or not name.endswith(".json"):
            continue
        if "/json/" not in name:
            continue
        coll = name.split("/json/", 1)[0].replace("-", "_")
        try:
            doc = json.loads(zf.read(name).decode("utf-8"))
        except Exception:
            counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
            counts[coll]["files_seen"] += 1
            counts[coll]["skipped_bad"] += 1
            continue
        if isinstance(doc, dict):
            doc.pop("_id", None)
            grouped.setdefault(coll, []).append(doc)
        counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
        counts[coll]["files_seen"] += 1
    for coll, docs in grouped.items():
        db[f"{prefix}__{coll}"].drop()
        if docs:
            db[f"{prefix}__{coll}"].insert_many(docs, ordered=False)
            counts.setdefault(coll, {"inserted": 0, "files_seen": 0, "skipped_bad": 0})
            counts[coll]["inserted"] = len(docs)
    return counts


def _rehydrate_photos(zf: zipfile.ZipFile, env: Dict[str, str], drill_id: str) -> Dict[str, int]:
    client, bucket = _r2_client(env)
    counters = {"uploaded": 0, "skipped": 0, "failed": 0}
    for info in zf.infolist():
        if not info.filename.startswith("photos/") or info.is_dir():
            continue
        sub = info.filename[len("photos/"):]
        key = f"drill-photos/{drill_id}/{sub}"
        try:
            client.head_object(Bucket=bucket, Key=key)
            counters["skipped"] += 1
            continue
        except Exception:
            pass
        try:
            client.put_object(Bucket=bucket, Key=key, Body=zf.read(info.filename))
            counters["uploaded"] += 1
        except Exception:
            counters["failed"] += 1
    return counters


def _write_report(drill_id: str, summary: Dict[str, Any]) -> Path:
    MEMORY_DIR.mkdir(exist_ok=True)
    path = MEMORY_DIR / f"OPS8_DRILL_{drill_id}_REPORT.md"
    lines = [
        f"# OPS8 restore drill {drill_id}\n\n",
        f"- Archive: `{summary['archive_filename']}`\n",
        f"- Outcome: **{summary['outcome'].upper()}**\n",
        f"- Namespace prefix: `{summary['target_namespace_prefix']}`\n",
        f"- Duration: {summary['duration_minutes']} min\n",
        f"- Records restored: {summary['records_restored']}\n",
        f"- Photos rehydrated: {summary['photos_rehydrated']}\n\n",
        "## Axes\n\n",
        "| Axis | Result | Detail |\n|---|---|---|\n",
    ]
    for axis, payload in summary["axes"].items():
        lines.append(f"| {axis} | {'PASS' if payload['ok'] else 'FAIL'} | {payload['message']} |\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="OPS8 namespace restore drill")
    ap.add_argument("--backup", required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--backup-ack", action="store_true")
    ap.add_argument("--confirm", default="")
    args = ap.parse_args()
    env = _load_env()

    if not args.execute:
        print(json.dumps({"ok": False, "error": "Refusing drill without --execute."}, indent=2))
        return 2
    if args.confirm != "RUN_ISOLATED_RECOVERY_DRILL":
        print(json.dumps({"ok": False, "error": "Refusing drill without exact confirmation."}, indent=2))
        return 2
    if not args.backup_ack:
        print(json.dumps({"ok": False, "error": "Refusing drill without --backup-ack."}, indent=2))
        return 2
    if (env.get("DB_NAME") or "") == "masci_safety":
        print(json.dumps({"ok": False, "error": "Production DB execution blocked."}, indent=2))
        return 2

    started = datetime.now(timezone.utc)
    t0 = time.time()
    drill_id = uuid.uuid4().hex[:12]
    namespace_prefix = f"ops8_drill_{started.strftime('%Y%m%d_%H%M%S')}"
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"ops8_drill_{drill_id}_"))
    archive_local = tmp_dir / Path(args.backup).name

    client, bucket = _r2_client(env)
    mongo = MongoClient(env["MONGO_URL"], serverSelectionTimeoutMS=20000)
    live_db = mongo[env["DB_NAME"]]
    import asyncio
    lineage = asyncio.run(
        build_canonical_archive_lineage(
            live_db,
            current_env=env.get("APP_ENV"),
            current_db=env.get("DB_NAME"),
            requested_source_environment=(env.get("APP_ENV") or "preview").strip().lower(),
            force_refresh=True,
        )
    )
    authoritative = lineage.get("authoritative_artifact") or {}
    if not authoritative or authoritative.get("object_key") != args.backup:
        print(json.dumps({"ok": False, "error": "ARCHIVE_LINEAGE_UNVERIFIED"}, indent=2))
        return 2
    live_db.drill_runs.insert_one({
        "id": drill_id,
        "drill_id": drill_id,
        "state": "running",
        "started_at": started.isoformat(),
        "target_db": env["DB_NAME"],
        "target_namespace_prefix": namespace_prefix,
        "source_environment": (env.get("APP_ENV") or "preview").strip().lower(),
        "source_archive_key": args.backup,
        "source_archive_id": ((authoritative.get("artifact_identity") or {}).get("artifact_id")),
        "restore_purpose": "PREVIEW_BACKUP_CERTIFICATION",
        "policy_decision": "PENDING",
        "policy_reason": "awaiting_namespace_restore_validation",
        "archive_filename": Path(args.backup).name,
    })

    try:
        client.download_file(bucket, args.backup, str(archive_local))
        with zipfile.ZipFile(str(archive_local), "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise RuntimeError(f"CRC failed on {bad}")
            manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
            per_kind = _restore_prefixed(zf, live_db, namespace_prefix)
            restored_total = sum(v.get("inserted", 0) for v in per_kind.values())
            manifest_total = int(manifest.get("total_records") or 0)
            manifest_per_kind = manifest.get("per_kind") or {}
            mismatches = []
            for coll, expected in manifest_per_kind.items():
                actual = int((per_kind.get(coll.replace("-", "_")) or {}).get("inserted") or 0)
                if int(expected) != actual:
                    mismatches.append(f"{coll}: manifest={expected} restored={actual}")
            photo_refs = set()
            archive_photos = set()
            for info in zf.infolist():
                if info.filename.startswith("photos/") and not info.is_dir():
                    archive_photos.add(info.filename[len("photos/"):])
                if not info.filename.endswith(".json") or info.filename == "MANIFEST.json":
                    continue
                try:
                    payload = json.loads(zf.read(info.filename).decode("utf-8"))
                except Exception:
                    continue
                for ref in _walk_photo_refs(payload):
                    try:
                        photo_refs.add(ref.split("/", 3)[3])
                    except Exception:
                        pass
            rehydration = _rehydrate_photos(zf, env, drill_id)

        axes = {
            "A1_archive_available": {"ok": True, "message": f"downloaded {args.backup}"},
            "A2_archive_integrity": {"ok": True, "message": f"manifest.total_records={manifest_total}"},
            "A3_record_count_parity": {"ok": len(mismatches) == 0 and restored_total == manifest_total, "message": f"restored={restored_total} manifest={manifest_total} mismatches={len(mismatches)}"},
            "A4_namespace_isolation": {"ok": True, "message": f"restored into collection prefix {namespace_prefix}__* within {env['DB_NAME']}"},
            "A5_photo_refs_reconcile": {"ok": len(photo_refs - archive_photos) == 0, "message": f"unique_refs={len(photo_refs)} archive_photos={len(archive_photos)} missing={len(photo_refs - archive_photos)}"},
            "A6_photo_rehydration": {"ok": rehydration.get("failed", 0) == 0, "message": f"uploaded={rehydration['uploaded']} skipped={rehydration['skipped']} failed={rehydration['failed']}"},
        }
        outcome = "ok" if all(v["ok"] for v in axes.values()) else "failed"
        duration_minutes = round((time.time() - t0) / 60.0, 3)
        summary = {
            "drill_id": drill_id,
            "state": "done",
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "target_db": env["DB_NAME"],
            "target_namespace_prefix": namespace_prefix,
            "archive_filename": Path(args.backup).name,
            "archive_size_mb": round(archive_local.stat().st_size / (1024 * 1024), 2),
            "records_in_manifest": manifest_total,
            "records_restored": restored_total,
            "photos_rehydrated": rehydration["uploaded"],
            "outcome": outcome,
            "source_environment": (env.get("APP_ENV") or "preview").strip().lower(),
            "source_archive_key": args.backup,
            "source_archive_id": ((authoritative.get("artifact_identity") or {}).get("artifact_id")),
            "restore_purpose": "PREVIEW_BACKUP_CERTIFICATION",
            "policy_decision": "PASS" if outcome == "ok" else "FAIL",
            "policy_reason": "authoritative_environment_bound_archive_selected",
            "axes": axes,
            "per_kind": per_kind,
            "cleanup_complete": False,
        }
        report_path = _write_report(drill_id, summary)
        live_db.drill_runs.update_one({"id": drill_id}, {"$set": {**summary, "report_path": str(report_path)}}, upsert=True)
        print(json.dumps({"ok": outcome == "ok", "drill_id": drill_id, "report_path": str(report_path), "summary": summary}, indent=2)[:24000])
        return 0 if outcome == "ok" else 9
    finally:
        try:
            for coll_name in live_db.list_collection_names():
                if coll_name.startswith(f"{namespace_prefix}__"):
                    live_db[coll_name].drop()
            live_db.drill_runs.update_one({"id": drill_id}, {"$set": {"cleanup_complete": True}})
        except Exception:
            pass
        try:
            if archive_local.exists():
                archive_local.unlink()
        except Exception:
            pass
        mongo.close()


if __name__ == "__main__":
    sys.exit(main())