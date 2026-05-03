#!/usr/bin/env python3
"""
JHA → JHP system-wide terminology migration.

Replaces user-visible strings only. Keeps internal identifiers
(variable names, function names, API paths, Mongo collection
names) untouched so existing data and code keep working.

Run from /app:  python3 /app/scripts/jha_to_jhp_rename.py
"""
import re
from pathlib import Path

# Files to process. Anything not in this list is left alone.
TARGETS = [
    "/app/frontend/src/data/training.js",
    "/app/frontend/src/data/training_es.js",
    "/app/frontend/src/lib/i18n.js",
    "/app/frontend/src/lib/meetingTopicLibrary.js",
    "/app/frontend/src/lib/meetingTopicLibrary.es.js",
    "/app/frontend/src/lib/jobLibrary.js",
    "/app/frontend/src/lib/jhaSchema.js",
    "/app/frontend/src/pages/JhaPlansAdmin.jsx",
    "/app/frontend/src/pages/Hub.jsx",
    "/app/frontend/src/pages/AdminGuide.jsx",
    "/app/frontend/src/components/SystemHealthBadge.jsx",
    "/app/frontend/src/components/EmailReportDialog.jsx",
    "/app/frontend/src/components/ComplianceExportPanel.jsx",
    "/app/frontend/src/components/CheatSheetCard.jsx",
    "/app/frontend/src/components/BilingualConsent.jsx",
    "/app/frontend/src/components/AutoEmailRoutingPanel.jsx",
    "/app/frontend/src/components/AdminPMPanel.jsx",
    "/app/backend/training_pdf.py",
    "/app/backend/server.py",
    "/app/backend/routes/safety.py",
    "/app/backend/pm_routing.py",
    "/app/backend/ops_manual.py",
    "/app/backend/job_hazard_files.py",
    "/app/backend/pdf_render.py",
]

# Replacement pairs — applied IN ORDER. Longer / more-specific patterns
# come FIRST so they match before generic short ones.
# NOTE: each pair = (pattern_regex, replacement). The regex is intentionally
# verbose so we never touch internal identifiers (keys, var names).
RULES = [
    # Slug rename (Lesson 5 in training data — only display slug)
    ("field-05-jha", "field-05-jhp"),
    # Long EN phrases first
    ("Job Hazard Analysis (JHA / JSA)", "Job Hazard Plan (JHP)"),
    ("Job Hazard Analysis (JHA)", "Job Hazard Plan (JHP)"),
    ("Job Hazard Analysis / JSA", "Job Hazard Plan"),
    ("Job Hazard Analysis", "Job Hazard Plan"),
    # ES phrases
    ("Análisis de Peligros del Trabajo (JHA / JSA)", "Plan de Peligros del Trabajo (JHP)"),
    ("Análisis de Peligros del Trabajo (JHA)", "Plan de Peligros del Trabajo (JHP)"),
    ("Análisis de Peligros del Trabajo", "Plan de Peligros del Trabajo"),
    # Compound abbreviations
    ("JHA / JSA", "JHP"),
    ("JHA/JSA", "JHP"),
    ("JHAs", "JHPs"),
    ("Planes JHA", "Planes JHP"),
    ("planes JHA", "planes JHP"),
    # Plain JHA → JHP, but only as a STANDALONE word.
    # Word boundaries protect identifiers like jha_files, JhaSchema,
    # /api/jhas/, jha-files, etc.
    (re.compile(r"\bJHA\b"), "JHP"),
    (re.compile(r"\bJSA\b"), "JHP"),
    # ES "Análisis de Peligros" used as a section header (not part of
    # "del Trabajo") → "Plan de Peligros"
    ("Hazard Analysis", "Hazard Plan"),
    ("Análisis de Peligros", "Plan de Peligros"),
]


def apply_rules(text: str) -> tuple[str, int]:
    total = 0
    out = text
    for pat, rep in RULES:
        if isinstance(pat, str):
            new = out.replace(pat, rep)
            total += (out.count(pat))
            out = new
        else:
            new, n = pat.subn(rep, out)
            total += n
            out = new
    return out, total


def main():
    summary = []
    for path_str in TARGETS:
        p = Path(path_str)
        if not p.exists():
            summary.append((path_str, "MISSING"))
            continue
        original = p.read_text(encoding="utf-8")
        updated, count = apply_rules(original)
        if updated != original:
            p.write_text(updated, encoding="utf-8")
            summary.append((path_str, f"{count} replacements"))
        else:
            summary.append((path_str, "no changes"))
    for s in summary:
        print(f"  {s[1]:30s} {s[0]}")


if __name__ == "__main__":
    main()
