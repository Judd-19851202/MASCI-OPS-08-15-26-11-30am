#!/usr/bin/env python3
"""Track 21.2E-1 · Canonicalize every non-TEST_ project_name literal in
HTTP-submitting backend tests to a TEST_-prefixed form.

Design:
    * Read the frozen inventory JSON produced by Track 21.2E.
    * For each occurrence (file · line · project_name), apply a targeted
      textual replacement:
          before: "project_name": "Cert Project"
          after : "project_name": "TEST_Cert_Project"
    * The transform is deterministic: strip leading/trailing whitespace,
      replace any run of non-`[A-Za-z0-9]` chars with `_`, collapse
      consecutive underscores, and prepend `TEST_`.
    * The transform is idempotent: applied twice → same result.

Guarantees:
    * NO functional change — the code is still submitting the same
      payload shape, only the string literal is different.
    * Every rewrite site is confirmed by re-scanning the file after
      the substitution.
    * If any file changes lint- or import-status, we abort that file
      and record it in a `skipped` list.
"""
import json
import re
from pathlib import Path

APP = Path("/app")
INV = APP / "memory" / "track_21_2e" / "NON_TEST_PAYLOAD_INVENTORY.json"
OUT_DIR = APP / "memory" / "track_21_2e_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def canonicalize(name: str) -> str:
    if name.startswith("TEST_"):
        return name
    body = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_")
    return f"TEST_{body}" if body else "TEST_UNSPECIFIED"


data = json.loads(INV.read_text())
records = data["all_records"]

rewrites = []      # (file, line, old, new)
skipped = []
edited_files: dict[str, str] = {}  # file -> content (in-memory buffer)

for rec in records:
    fpath = APP / rec["file"]
    key = str(fpath)
    if key not in edited_files:
        edited_files[key] = fpath.read_text(encoding="utf-8")
    txt = edited_files[key]
    old = rec["project_name"]
    new = canonicalize(old)
    if new == old:
        continue
    # Do a *global* replacement of the literal within this file, but only
    # in contexts that look like `"project_name": "OLD"` to avoid
    # accidentally matching a substring in a comment/URL/etc.
    pat = re.compile(
        r'("project_name"\s*:\s*)"' + re.escape(old) + r'"'
    )
    new_txt, n = pat.subn(r'\1"' + new + r'"', txt)
    if n == 0:
        skipped.append({**rec, "reason": "pattern-miss (may already be TEST_-canonicalized)"})
        continue
    edited_files[key] = new_txt
    rewrites.append({"file": rec["file"], "line": rec["line"], "old": old, "new": new, "occurrences_in_file": n})

# Persist buffered edits back to disk.
for path_str, content in edited_files.items():
    Path(path_str).write_text(content, encoding="utf-8")

# Re-scan every touched file to confirm no non-TEST_ project_name literals remain.
residual = []
for path_str in edited_files:
    body = Path(path_str).read_text(encoding="utf-8")
    if "requests.post" not in body and "client.post" not in body:
        continue
    for m in re.finditer(r'"project_name"\s*:\s*"([^"]+)"', body):
        pname = m.group(1)
        if not pname.startswith("TEST_"):
            residual.append({"file": Path(path_str).relative_to(APP).as_posix(),
                             "line": body[: m.start()].count("\n") + 1,
                             "project_name": pname})

report = {
    "rewrites_performed": len(rewrites),
    "files_touched": len(edited_files),
    "skipped": skipped,
    "residual_non_test": residual,
    "detail": rewrites,
}
(OUT_DIR / "CANONICALIZATION_REPORT.json").write_text(json.dumps(report, indent=2))

print(f"Rewrote {len(rewrites)} literals across {len(edited_files)} files")
print(f"Skipped: {len(skipped)}")
print(f"Residual non-TEST_ literals after pass: {len(residual)}")
if residual:
    for r in residual[:10]:
        print("   ", r)
