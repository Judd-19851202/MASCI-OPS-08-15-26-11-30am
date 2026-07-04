#!/usr/bin/env python3
"""Track 21.2E · Email Safety Incident Closeout — inventory of non-TEST_ test payloads.

Static, side-effect-free scan of every backend test file for JSON payloads that
carry a `project_name` literal not beginning with `TEST_`. These are the
payloads that would have leaked live email before the SDK-level kill switch
was installed. Every entry becomes canonicalization work for the follow-up
defense-in-depth pass.

Emits:
    /app/memory/track_21_2e/NON_TEST_PAYLOAD_INVENTORY.json
    /app/memory/track_21_2e/NON_TEST_PAYLOAD_INVENTORY.md
"""
import json
import re
from pathlib import Path
from collections import defaultdict

BACKEND_TESTS = Path("/app/backend/tests")
OUT_DIR = Path("/app/memory/track_21_2e")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Endpoint routes that trigger schedule_auto_email or a Resend dispatcher.
# Sourced by grepping `schedule_auto_email(` and every direct Resend call in
# backend/server.py + backend/routes/.
EMAIL_TRIGGERING_ROUTES = {
    "/api/daily-reports",
    "/api/incidents",
    "/api/jha",
    "/api/jha-plans",
    "/api/meetings",
    "/api/safety-meetings",
    "/api/qaqc",
    "/api/inspections",
    "/api/equipment-inspections",
    "/api/pre-op-inspections",
    "/api/near-misses",
    "/api/observations",
}

pat_project = re.compile(r'"project_name"\s*:\s*"([^"]+)"')
pat_post = re.compile(r'requests\.post\s*\(\s*[fr]?"([^"]+)"|API\s*\+\s*"([^"]+)"|f["\']({URL|BASE_URL|URL}[^"\']*)["\']')

records = []
by_file = defaultdict(list)
by_project_name = defaultdict(int)

for tf in sorted(BACKEND_TESTS.rglob("test_*.py")):
    if "__pycache__" in str(tf):
        continue
    try:
        text = tf.read_text(errors="ignore")
    except Exception:
        continue
    # Skip test files that are pure unit tests (no requests.post)
    if "requests.post" not in text and "client.post" not in text:
        # Payload literals without HTTP submission cannot leak email.
        # Skip from the inventory.
        continue
    for m in pat_project.finditer(text):
        pname = m.group(1)
        if pname.startswith("TEST_"):
            continue
        line = text[: m.start()].count("\n") + 1
        rec = {
            "file": str(tf.relative_to(Path("/app"))),
            "line": line,
            "project_name": pname,
        }
        records.append(rec)
        by_file[rec["file"]].append(rec)
        by_project_name[pname] += 1

# Sort by file frequency
files_ranked = sorted(by_file.items(), key=lambda kv: -len(kv[1]))
distinct_names = sorted(by_project_name.items(), key=lambda kv: -kv[1])

summary = {
    "total_non_test_payloads": len(records),
    "distinct_files": len(by_file),
    "distinct_project_names": len(by_project_name),
    "files_top_20": [{"file": f, "occurrences": len(v)} for f, v in files_ranked[:20]],
    "project_names_top_30": [{"project_name": n, "occurrences": c} for n, c in distinct_names[:30]],
    "all_records": records,
    "email_triggering_routes_reference": sorted(EMAIL_TRIGGERING_ROUTES),
}

(OUT_DIR / "NON_TEST_PAYLOAD_INVENTORY.json").write_text(json.dumps(summary, indent=2))

# Human-readable markdown
md = ["# Track 21.2E · Non-TEST_ Payload Inventory", ""]
md.append(f"- **Total non-TEST_ payload literals in HTTP-submitting tests:** {summary['total_non_test_payloads']}")
md.append(f"- **Distinct files:** {summary['distinct_files']}")
md.append(f"- **Distinct project_name literals:** {summary['distinct_project_names']}")
md.append("")
md.append("## Top 20 offending files")
md.append("")
for row in summary["files_top_20"]:
    md.append(f"- `{row['file']}` — {row['occurrences']} occurrences")
md.append("")
md.append("## Top 30 non-TEST_ project_name literals")
md.append("")
for row in summary["project_names_top_30"]:
    md.append(f"- `{row['project_name']}` × {row['occurrences']}")
md.append("")
md.append("## Every offending record")
md.append("")
for rec in records:
    md.append(f"- `{rec['file']}:{rec['line']}` → project_name=`{rec['project_name']}`")
(OUT_DIR / "NON_TEST_PAYLOAD_INVENTORY.md").write_text("\n".join(md))

print(f"Non-TEST_ payloads: {summary['total_non_test_payloads']}")
print(f"Files: {summary['distinct_files']}")
print(f"Distinct names: {summary['distinct_project_names']}")
print(f"Emitted → {OUT_DIR/'NON_TEST_PAYLOAD_INVENTORY.json'}")
print(f"Emitted → {OUT_DIR/'NON_TEST_PAYLOAD_INVENTORY.md'}")
