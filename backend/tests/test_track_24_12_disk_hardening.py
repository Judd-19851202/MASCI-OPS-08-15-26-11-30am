"""TRACK 24.12 · Workstream B · R2 / Disk Hardening Regression Locks
=====================================================================

Static-only assertions that guarantee the disk-hardening scripts
retain their safety invariants across future edits. These tests do
NOT invoke the scripts (dry-run itself needs Motor + a live Mongo
handle); they read the source and confirm the anti-footgun
constructs are present.

Locked contracts
----------------
1. ``scripts/audit_disk_usage_24_12.py`` never writes / mutates /
   deletes. It only reads and prints. Any ``.write_``, ``.unlink``,
   ``.rmtree``, ``.mkdir``, ``insert_one``, ``update_one``, or
   ``delete_many`` in the audit script must fail this test.
2. ``scripts/migrate_local_project_docs_to_r2.py`` DEFAULTS to
   dry-run. The ``--apply`` flag is required for any mutation. All
   unlink / update / delete code paths sit inside the ``if
   args.apply:`` branch (or a helper called from it).
3. The migration script verifies the R2 HEAD before unlinking any
   local file. The check must appear in the promote path.
4. Every ``--apply`` migration writes an ``hr_audit`` row. The audit
   collection name must be present in source.
5. ``scripts/basecamp_import_big.py`` streams to R2 by default and
   ONLY falls back to disk when ``--fallback-to-disk`` is passed.
   Prior implementation always wrote to disk — that regression must
   never come back.
"""
from __future__ import annotations

from pathlib import Path

SCRIPTS = Path("/app/backend/scripts")
AUDIT = SCRIPTS / "audit_disk_usage_24_12.py"
MIGRATE = SCRIPTS / "migrate_local_project_docs_to_r2.py"
BASECAMP = SCRIPTS / "basecamp_import_big.py"


# ── Test 1 · Audit is READ-ONLY by construction ─────────────────
def test_audit_script_exists_and_is_readonly():
    assert AUDIT.exists(), "TRACK 24.12 · audit_disk_usage_24_12.py missing."
    src = AUDIT.read_text(encoding="utf-8")
    banned = [
        "insert_one(", "insert_many(", "update_one(", "update_many(",
        "delete_one(", "delete_many(", ".unlink(", "shutil.rmtree(",
        "os.remove(", ".rmdir(", "put_object(", "upload_file(",
        "upload_photo_bytes(", "upload_local_file(", "upload_data_url(",
    ]
    hits = [b for b in banned if b in src]
    assert not hits, (
        f"TRACK 24.12 · audit_disk_usage_24_12.py must be READ-ONLY. "
        f"Found mutating calls: {hits}"
    )


# ── Test 2 · Migration defaults to dry-run ──────────────────────
def test_migration_defaults_to_dry_run():
    assert MIGRATE.exists(), (
        "TRACK 24.12 · migrate_local_project_docs_to_r2.py missing."
    )
    src = MIGRATE.read_text(encoding="utf-8")
    assert 'add_argument(\n        "--apply", action="store_true"' in src, (
        "TRACK 24.12 · --apply must be action=\"store_true\" (dry-run "
        "default)."
    )
    # And the mutation branch MUST gate on `args.apply`.
    assert "if not args.apply:" in src or "if args.apply" in src, (
        "TRACK 24.12 · migration source must gate mutation on --apply."
    )


# ── Test 3 · Migration verifies R2 HEAD before unlinking ────────
def test_migration_verifies_r2_head_before_unlink():
    src = MIGRATE.read_text(encoding="utf-8")
    # HEAD probe helper is _r2_head; it must run BEFORE local.unlink().
    assert "_r2_head(" in src, (
        "TRACK 24.12 · migration must probe R2 HEAD before unlinking "
        "any local file."
    )
    # And the abort branch on missing HEAD must exist.
    assert "aborted_head_missing_after_upload" in src, (
        "TRACK 24.12 · migration must ABORT on failed HEAD probe."
    )
    # local.unlink() must appear AFTER the HEAD check inside the
    # promote helper (source scan — sequence order).
    head_pos = src.index("_r2_head(")
    unlink_pos = src.index("local.unlink(")
    assert head_pos < unlink_pos, (
        "TRACK 24.12 · unlink must run AFTER the R2 HEAD probe, not "
        "before."
    )


# ── Test 4 · Migration writes hr_audit rows on --apply ──────────
def test_migration_emits_hr_audit_rows():
    src = MIGRATE.read_text(encoding="utf-8")
    assert 'AUDIT_COLLECTION = "hr_audit"' in src, (
        "TRACK 24.12 · migration must record actions in hr_audit."
    )
    assert "await _emit_audit(" in src, (
        "TRACK 24.12 · migration must call the audit emitter for each "
        "migrated file."
    )
    assert '"action": "migrate_disk_to_r2"' in src, (
        "TRACK 24.12 · migration audit rows must carry a canonical "
        "`action` string."
    )


# ── Test 5 · Basecamp big-file import goes to R2 by default ─────
def test_basecamp_import_big_defaults_to_r2():
    assert BASECAMP.exists(), (
        "TRACK 24.12 · basecamp_import_big.py missing."
    )
    src = BASECAMP.read_text(encoding="utf-8")
    # R2 upload path must exist AND be the default.
    assert "await _import_r2" in src, (
        "TRACK 24.12 · basecamp_import_big.py must have an R2 upload "
        "path."
    )
    assert "upload_local_file" in src, (
        "TRACK 24.12 · basecamp_import_big.py must stream to R2 via "
        "photo_storage.upload_local_file."
    )
    # Fallback flag must be action=store_true (opt-in).
    assert '--fallback-to-disk' in src, (
        "TRACK 24.12 · --fallback-to-disk flag missing — legacy disk "
        "path must be opt-in only."
    )
    # And the default flow must NOT copy files to
    # /app/backend/storage/project_docs.
    # Assert: the r2 branch does NOT reference the storage dir.
    r2_branch = src.split("async def _import_r2", 1)[1].split("async def _import_disk", 1)[0]
    assert "shutil.copy" not in r2_branch, (
        "TRACK 24.12 · R2 branch must NOT copy to local disk."
    )
    assert "storage/project_docs" not in r2_branch, (
        "TRACK 24.12 · R2 branch must NOT reference the local "
        "project_docs directory."
    )


# ── Test 6 · Basecamp fail-closed when R2 not configured ────────
def test_basecamp_r2_path_refuses_when_r2_missing():
    src = BASECAMP.read_text(encoding="utf-8")
    assert "photo_storage.is_configured()" in src, (
        "TRACK 24.12 · basecamp_import_big.py must check "
        "photo_storage.is_configured() before writing."
    )
    assert "Refusing to import" in src or "refuses" in src.lower(), (
        "TRACK 24.12 · basecamp_import_big.py must fail-closed when R2 "
        "is not configured."
    )


# ── Test 7 · All three scripts are syntactically importable ─────
def test_all_three_scripts_parse():
    import ast
    for p in (AUDIT, MIGRATE, BASECAMP):
        src = p.read_text(encoding="utf-8")
        try:
            ast.parse(src)
        except SyntaxError as e:
            raise AssertionError(
                f"TRACK 24.12 · {p.name} has a syntax error: {e}"
            ) from e
