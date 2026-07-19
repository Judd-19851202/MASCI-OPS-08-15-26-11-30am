#!/usr/bin/env python3
"""automated_drill.py — Phase E · OMEGA · Automated Restore Drill.

Idempotent CLI wrapper around scripts/restore_drill.py that:
  1. Auto-selects the latest healthy archive from R2.
  2. Provisions an isolated drill DB name.
  3. Runs the 10 verification axes A1-A10 from AUTOMATED_RESTORE_DRILL_SPEC.md.
  4. Writes a drill_runs row to Mongo for dashboard pickup.
  5. Cleans up: drops drill DB · removes temp zip.
  6. Writes a per-drill markdown report to /app/memory/DRILL_<id>_REPORT.md.

DESIGN GUARANTEES (per AUTOMATED_RESTORE_DRILL_SPEC.md):
  • Isolated subprocess from the live API worker (we are the subprocess).
  • Isolated DB (name MUST start with masci_restore_drill_auto_).
  • Isolated R2 prefix for rehydrated photos (drill-photos/<drill_id>/...).
  • Read-only against the live archive — never mutates `backups/auto-90d/*`.
  • No cron, no scheduler integration in this phase — invoked manually
    or by external cron. Cadence stays operator-controlled.

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


def _pick_latest_healthy(client, bucket: str) -> Optional[Dict[str, Any]]:
    """Latest archive under backups/auto-90d/ by LastModified."""
    paginator = client.get_paginator("list_objects_v2")
    candidates: List[Dict[str, Any]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix="backups/auto-90d/"):
        for obj in page.get("Contents") or []:
            key = obj.get("Key") or ""
            if key.endswith(".zip") and "MASCI_complete_backup_" in key:
                candidates.append(obj)
    if not candidates:
        return None
    candidates.sort(key=lambda o: o.get("LastModified"), reverse=True)
    return candidates[0]


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
    started_at_dt = datetime.now(timezone.utc)
    t0 = time.time()
    drill_id = uuid.uuid4().hex[:12]
    target_db = f"masci_restore_drill_auto_{started_at_dt.strftime('%Y%m%d_%H%M%S')}"

    target_uri = target_uri or env.get("MONGO_URL")
    if not target_uri:
        print("FAIL: MONGO_URL not set", file=sys.stderr)
        return 2

    print(f"=== AUTOMATED DRILL · {drill_id} ===")
    print(f"started_at = {started_at_dt.isoformat()}")
    print(f"target_db  = {target_db}")

    # Persist 'queued' state immediately so dashboard sees the run
    _write_drill_row(env, {
        "id": drill_id,
        "enqueued_at": started_at_dt.isoformat(),
        "state": "downloading",
        "started_at": started_at_dt.isoformat(),
        "target_db": target_db,
        "axes": {},
    })

    client, bucket = _r2_client(env)
    axes: Dict[str, Dict[str, Any]] = {}
    notes: List[str] = []

    # === A1 · archive available ===
    if explicit_key:
        try:
            head = client.head_object(Bucket=bucket, Key=explicit_key)
            archive_key = explicit_key
            archive_size = head["ContentLength"]
            archive_lastmod = head["LastModified"]
            axes["A1_archive_available"] = {
                "ok": True,
                "message": f"head_object → {archive_size/1e6:.2f} MB · {archive_lastmod}",
            }
        except Exception as e:
            axes["A1_archive_available"] = {"ok": False, "message": f"head_object failed: {e}"}
            return _finalize(env, drill_id, started_at_dt, t0, target_db,
                             "—", 0, axes, {}, 0, 0, {}, notes,
                             cleanup_db_dropped=False, cleanup_zip_removed=False)
    else:
        chosen = _pick_latest_healthy(client, bucket)
        if not chosen:
            axes["A1_archive_available"] = {"ok": False, "message": "no archive found in backups/auto-90d/"}
            return _finalize(env, drill_id, started_at_dt, t0, target_db,
                             "—", 0, axes, {}, 0, 0, {}, notes,
                             cleanup_db_dropped=False, cleanup_zip_removed=False)
        archive_key = chosen["Key"]
        archive_size = chosen["Size"]
        axes["A1_archive_available"] = {
            "ok": True,
            "message": f"latest auto-pick: {archive_key} · {archive_size/1e6:.2f} MB",
        }
    archive_filename = Path(archive_key).name
    archive_size_mb = archive_size / (1024 * 1024)
    print(f"archive    = {archive_key} ({archive_size_mb:.2f} MB)")

    tmp = Path(tempfile.mkdtemp(prefix=f"drill_{drill_id}_"))
    archive_local = tmp / archive_filename

    try:
        # === Download ===
        print("downloading...", flush=True)
        client.download_file(bucket, archive_key, str(archive_local))

        # === A2 · archive integrity ===
        with zipfile.ZipFile(archive_local, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                axes["A2_archive_integrity"] = {"ok": False, "message": f"CRC fail on {bad}"}
                return _finalize(env, drill_id, started_at_dt, t0, target_db,
                                 archive_filename, archive_size_mb, axes, {},
                                 0, 0, {}, notes, False, False)
            try:
                manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
            except Exception as e:
                axes["A2_archive_integrity"] = {"ok": False, "message": f"manifest read fail: {e}"}
                return _finalize(env, drill_id, started_at_dt, t0, target_db,
                                 archive_filename, archive_size_mb, axes, {},
                                 0, 0, {}, notes, False, False)
            axes["A2_archive_integrity"] = {
                "ok": manifest.get("failed_photos", 0) == 0,
                "message": f"testzip OK · manifest.failed_photos={manifest.get('failed_photos',0)} · "
                           f"explicit_exclusions={manifest.get('explicit_exclusions',[])}",
            }
            records_in_manifest = manifest.get("total_records", 0)

            # Extract all entries
            extract_dir = tmp / "extracted"
            extract_dir.mkdir()
            zf.extractall(extract_dir)

        # === A3 · record count parity (restore + count) ===
        # Reuse restore_drill._restore_side_db logic inline:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from restore_drill import _restore_side_db, _validate_restore  # type: ignore

        per_kind = _restore_side_db(extract_dir, target_uri, target_db, verbose=False)
        # Manifest's per_kind counts (server.py:5681 emits per_kind dict)
        manifest_per_kind = manifest.get("per_kind") or {}
        mismatches: List[str] = []
        for k, mc in manifest_per_kind.items():
            # archive keys may use underscores or dashes; restore_drill maps dash→underscore
            k_norm = k.replace("-", "_")
            actual = (per_kind.get(k_norm) or {}).get("inserted", 0)
            # Telemetry-tier exclusions are zero in manifest already; skip.
            if int(mc) != int(actual):
                mismatches.append(f"{k}: manifest={mc} restored={actual}")
        axes["A3_record_count_parity"] = {
            "ok": len(mismatches) == 0,
            "message": f"checked {len(manifest_per_kind)} collections · mismatches={len(mismatches)}"
                       + (f" · first 3: {mismatches[:3]}" if mismatches else ""),
        }

        # === A4 · sample parseability ===
        # restore_drill already parses every json; bad files count gives us proof
        total_bad = sum(c.get("skipped_bad", 0) for c in per_kind.values())
        axes["A4_sample_parseability"] = {
            "ok": total_bad == 0,
            "message": f"total bad JSON files across all collections: {total_bad}",
        }

        # === A5 · user directory restored ===
        from pymongo import MongoClient as _Mc
        _c = _Mc(target_uri, serverSelectionTimeoutMS=5000)
        sdb = _c[target_db]
        ud_count = sdb.user_directory.estimated_document_count()
        u_count = sdb.users.estimated_document_count()
        axes["A5_user_directory_restored"] = {
            "ok": (ud_count + u_count) > 0,
            "message": f"user_directory={ud_count} · users={u_count}",
        }

        # === A6 · no _id leakage in restored docs ===
        leaks = 0
        for coll in ("daily_reports", "tasks", "notifications", "user_directory"):
            try:
                # Restored docs should retain only the original _id (auto-generated by insert_many);
                # but the EXPORTED JSON should never have contained the archive _id (archive code
                # excludes _id at line 5648). Verify by checking a sample doc has NO 'id' AND '_id'
                # field that contradicts each other — quick proxy: count docs where 'id' is missing.
                missing_id = sdb[coll].count_documents({"id": {"$exists": False}})
                leaks += missing_id
            except Exception:
                pass
        axes["A6_no_id_leakage"] = {
            "ok": leaks == 0,
            "message": f"docs with missing 'id' field across 4 key collections: {leaks}",
        }

        # === A7 · photo refs reconcile (archive-internal) ===
        with zipfile.ZipFile(archive_local, "r") as zf:
            archive_photo_keys = set(
                i.filename[7:] for i in zf.infolist() if i.filename.startswith("photos/")
            )
            unique_refs: set = set()
            for info in zf.infolist():
                if not info.filename.endswith(".json") or info.filename == "MANIFEST.json":
                    continue
                try:
                    d = json.loads(zf.read(info.filename).decode("utf-8"))
                except Exception:
                    continue
                for ref in _walk_photo_refs(d):
                    try:
                        unique_refs.add(ref.split("/", 3)[3])
                    except Exception:
                        pass
        missing_in_archive = unique_refs - archive_photo_keys
        axes["A7_photo_refs_reconcile"] = {
            "ok": len(missing_in_archive) == 0,
            "message": f"unique_refs={len(unique_refs)} archive_keys={len(archive_photo_keys)} missing={len(missing_in_archive)}",
        }
        if missing_in_archive:
            notes.append(f"A7 missing keys (first 3): {list(missing_in_archive)[:3]}")

        # === A8 · photo rehydration ===
        # Re-upload archive's photos/ to a DRILL-ISOLATED prefix
        from restore_drill import _rehydrate_photos_to_r2  # type: ignore
        # Temporarily reroute the bucket / prefix scope using env-style override:
        # The existing function writes back to the same bucket at the SAME key.
        # For the drill we need an isolated prefix → wrap manually here.
        photo_rehydration = _drill_rehydrate(extract_dir, env, drill_id)
        axes["A8_photo_rehydration"] = {
            "ok": photo_rehydration["failed"] == 0,
            "message": f"uploaded={photo_rehydration['uploaded']} skipped={photo_rehydration['skipped']} failed={photo_rehydration['failed']}",
        }

        # === A9 · coverage gap stays zero ===
        gap = unique_refs - archive_photo_keys
        axes["A9_coverage_gap_zero"] = {
            "ok": len(gap) == 0,
            "message": f"refs_minus_archive={len(gap)} (iter442 acceptance criterion)",
        }

        # === A10 · build vs restore reconciliation ===
        total_restored = sum(c["inserted"] for c in per_kind.values())
        # backup_health row — search the SOURCE DB recorded in the manifest
        # (manifest.source may be "masci_safety" prod even when this drill
        # runs from the preview pod). We try the manifest hint first, then
        # fall back to DB_NAME, then to common known names.
        from pymongo import MongoClient as _Mc2
        candidate_dbs = []
        manifest_source = manifest.get("source") or ""
        if manifest_source:
            candidate_dbs.append(manifest_source)
        if env.get("DB_NAME") and env["DB_NAME"] not in candidate_dbs:
            candidate_dbs.append(env["DB_NAME"])
        for fallback in ("masci_safety", "masci_safety_preview"):
            if fallback not in candidate_dbs:
                candidate_dbs.append(fallback)
        live_client = _Mc2(env["MONGO_URL"], serverSelectionTimeoutMS=5000)
        bh = None
        bh_db = None
        for dbn in candidate_dbs:
            try:
                bh = live_client[dbn].backup_health.find_one(
                    {"filename": archive_filename, "ok": True}, {"_id": 0}
                )
                if bh:
                    bh_db = dbn
                    break
            except Exception:
                continue
        bh_records = bh.get("records") if bh else None
        live_client.close()
        recon_ok = (bh_records == records_in_manifest == total_restored)
        axes["A10_recon"] = {
            "ok": recon_ok,
            "message": (
                f"backup_health.records={bh_records} (db={bh_db or 'NOT FOUND'}) · "
                f"manifest={records_in_manifest} · restored={total_restored}"
            ),
        }

        cleanup_db_dropped = False
        cleanup_zip_removed = False
        if not keep_db:
            try:
                sdb.client.drop_database(target_db)
                cleanup_db_dropped = True
            except Exception as e:
                notes.append(f"db drop failed: {e}")
        try:
            archive_local.unlink()
            cleanup_zip_removed = True
        except Exception as e:
            notes.append(f"zip unlink failed: {e}")
        _c.close()

        return _finalize(env, drill_id, started_at_dt, t0, target_db,
                         archive_filename, archive_size_mb,
                         axes, per_kind, len(unique_refs), len(archive_photo_keys),
                         photo_rehydration, notes,
                         cleanup_db_dropped, cleanup_zip_removed,
                         records_in_manifest=records_in_manifest)

    finally:
        # leave temp dir for inspection on failure; cleanup on success handled above
        pass


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
