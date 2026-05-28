#!/usr/bin/env python3
"""
walkthrough_capture.py — Phase V-Prelude · Observation Ledger.

Microscopic institutional-memory tool. Captures one operator
walkthrough verdict per invocation into the append-only
`OBSERVATION_LEDGER.json` file. No UI. No analytics. No dashboards.

The script is invoked MANUALLY by the operator after a real PM
walkthrough:

  python3 scripts/walkthrough_capture.py \\
    --scenario utility-conflict \\
    --reviewer JJ

It prompts for four short answers and appends ONE entry to the ledger.

Doctrine:
  * APPEND-ONLY — never mutates or removes prior entries.
  * Z-suffixed UTC timestamps (TRUST-TIME-1).
  * Closed-set scenarios + `custom`.
  * Duplicate (timestamp, scenario, reviewer) tuple is rejected.
  * Ledger integrity is protected by the existing
    `trendline_integrity_probe.py` (Wave 1.1B) — see the probe's
    TRENDLINES table.
  * Read-only against everything except the ledger file itself.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

LEDGER_PATH = Path("/app/memory/OBSERVATION_LEDGER.json")

SCENARIOS = (
    "utility-conflict",
    "FAA-delay",
    "MOT-sequencing",
    "drainage-conflict",
    "survey-discrepancy",
    "QC-failure",
    "owner-delay",
    "field-conflict",
    "custom",
)

PROMPTS = (
    ("worked", "1. What worked?"),
    ("friction", "2. What caused friction?"),
    ("chronology_helped", "3. Did the timeline/chronology improve understanding?"),
    ("would_help_real_ops", "4. Would this help real operations?"),
)

MAX_ANSWER_LEN = 500
MAX_NOTES_LEN = 1000


def _utc_iso() -> str:
    d = datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


def _read_ledger() -> List[Dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(
            f"OBSERVATION_LEDGER.json is not a list (got "
            f"{type(data).__name__}) — refuse to append. Triage required."
        )
    return data


def _write_ledger(rows: List[Dict[str, Any]]) -> None:
    LEDGER_PATH.write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )


def _prompt_answer(label: str) -> str:
    try:
        ans = input(label + "\n> ").strip()
    except EOFError:
        ans = ""
    return ans[:MAX_ANSWER_LEN]


def build_entry(
    *,
    scenario: str,
    reviewer: str,
    answers: Dict[str, str],
    freeze_trigger_observed: bool,
    notes: str = "",
    timestamp: str = "",
) -> Dict[str, Any]:
    """Pure function — also used by the regression suite."""
    if scenario not in SCENARIOS:
        raise ValueError(
            f"invalid scenario: {scenario!r}. "
            f"Must be one of: {', '.join(SCENARIOS)}"
        )
    reviewer = (reviewer or "").strip()
    if not reviewer:
        raise ValueError("reviewer is required (initials or short tag).")
    for key, _ in PROMPTS:
        if key not in answers:
            raise ValueError(f"missing answer for: {key}")
    entry: Dict[str, Any] = {
        "timestamp": (timestamp or _utc_iso()),
        "scenario": scenario,
        "reviewer": reviewer[:80],
        "answers": {
            key: str(answers.get(key, "") or "").strip()[:MAX_ANSWER_LEN]
            for key, _ in PROMPTS
        },
        "freeze_trigger_observed": bool(freeze_trigger_observed),
        "notes": (notes or "").strip()[:MAX_NOTES_LEN],
    }
    return entry


def append_entry(entry: Dict[str, Any], ledger_path: Path = LEDGER_PATH) -> None:
    """Validate + append. Raises SystemExit on duplicate or shape err."""
    if not ledger_path.exists():
        ledger_path.write_text("[]\n", encoding="utf-8")
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(
            f"{ledger_path} is not a JSON list — refuse to append."
        )
    # Duplicate detection — (timestamp, scenario, reviewer) tuple.
    sig = (entry["timestamp"], entry["scenario"], entry["reviewer"])
    for row in data:
        if (
            row.get("timestamp") == sig[0]
            and row.get("scenario") == sig[1]
            and row.get("reviewer") == sig[2]
        ):
            raise SystemExit(
                f"duplicate (timestamp, scenario, reviewer) rejected: {sig}"
            )
    data.append(entry)
    ledger_path.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="V-Prelude Observation Ledger capture (microscopic)."
    )
    ap.add_argument("--scenario", required=True, choices=SCENARIOS)
    ap.add_argument(
        "--reviewer",
        required=True,
        help="initials or short tag (e.g., JJ, CW)",
    )
    ap.add_argument(
        "--freeze-trigger-observed",
        action="store_true",
        help="set when ANY of the 18 freeze triggers fired during the "
             "walkthrough (will be reviewed)",
    )
    ap.add_argument(
        "--notes",
        default="",
        help="optional one-line free-text note (≤1000 chars)",
    )
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="for tests / CI — read answers from CLI args instead of stdin",
    )
    ap.add_argument("--worked", default="")
    ap.add_argument("--friction", default="")
    ap.add_argument("--chronology-helped", default="")
    ap.add_argument("--would-help-real-ops", default="")
    args = ap.parse_args()

    if args.non_interactive:
        answers = {
            "worked": args.worked,
            "friction": args.friction,
            "chronology_helped": args.chronology_helped,
            "would_help_real_ops": args.would_help_real_ops,
        }
    else:
        print(f"\n── Observation walkthrough · {args.scenario} · {args.reviewer} ──")
        print("Four short answers — keep each ≤ 500 chars. Empty is OK.\n")
        answers = {key: _prompt_answer(label) for key, label in PROMPTS}

    try:
        entry = build_entry(
            scenario=args.scenario,
            reviewer=args.reviewer,
            answers=answers,
            freeze_trigger_observed=args.freeze_trigger_observed,
            notes=args.notes,
        )
    except ValueError as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 2

    try:
        append_entry(entry)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 3

    print(
        f"\n✓ ledger entry appended · "
        f"{entry['timestamp']} · {entry['scenario']} · "
        f"{entry['reviewer']}"
    )
    print(f"  ledger: {LEDGER_PATH}")
    if entry["freeze_trigger_observed"]:
        print(
            "\n⚠  freeze_trigger_observed=true — "
            "STOP and triage before any further work."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
