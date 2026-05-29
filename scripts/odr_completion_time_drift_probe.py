#!/usr/bin/env python3
"""
odr_completion_time_drift_probe.py — Phase V.1 · M0.4 · ADVISORY · M1-prep.

Doctrine source: `/app/memory/ODR_SIMPLICITY_TEST_DOCTRINE.md`
  Target  · < 5 min foreman ODR completion
  Stretch · < 3 min
  Ceiling · 7 min (P0 regression above this)

This probe samples the `odr_observation_events` collection (the
adoption telemetry surface) for `submit_success` events and reports
the rolling-window mean / p50 / p95 completion duration.

ADVISORY ONLY:
  * exit code is ALWAYS 0
  * never used as a build gate
  * report is consumed by the operator review

Usage:
  python3 scripts/odr_completion_time_drift_probe.py [--days 7]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "backend" / ".env")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

REPORT_PATH = REPO_ROOT / "memory" / "ODR_COMPLETION_TIME_DRIFT_REPORT.md"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _percentile(values, pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((pct / 100.0) * (len(s) - 1)))
    return float(s[k])


async def run(days: int) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"], tz_aware=True)
    db = client[os.environ["DB_NAME"]]
    cutoff = (_utc_now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    cur = db.odr_observation_events.find(
        {"kind": "submit_success", "at_utc": {"$gte": cutoff}},
        {"_id": 0, "context.duration_ms": 1, "at_utc": 1},
    )
    durations_s = []
    async for ev in cur:
        ms = (ev.get("context") or {}).get("duration_ms")
        if isinstance(ms, (int, float)) and ms > 0:
            durations_s.append(ms / 1000.0)

    sample_size = len(durations_s)
    avg_s = mean(durations_s) if durations_s else 0.0
    p50 = _percentile(durations_s, 50)
    p95 = _percentile(durations_s, 95)

    avg_min = avg_s / 60.0
    p95_min = p95 / 60.0

    target_min = 5.0
    stretch_min = 3.0
    ceiling_min = 7.0

    drift_state = "GREEN"
    if avg_min > ceiling_min:
        drift_state = "RED"
    elif avg_min > target_min:
        drift_state = "AMBER"

    report = [
        "# ODR Completion-Time Drift Report",
        "",
        f"_Window: last {days} day(s) · sample size {sample_size} · "
        f"generated {_utc_now().isoformat()}._",
        "",
        "**Doctrine source:** `ODR_SIMPLICITY_TEST_DOCTRINE.md`",
        "",
        "## Summary",
        "",
        f"- Mean completion: **{avg_min:.2f} min** ({avg_s:.0f} sec)",
        f"- p50 completion: {(p50 / 60.0):.2f} min",
        f"- p95 completion: {p95_min:.2f} min",
        f"- Drift state: **{drift_state}**",
        "",
        "## Thresholds",
        "",
        f"| Bound | Value | This window |",
        f"|---|---|---|",
        f"| Stretch goal | < {stretch_min} min | "
        f"{'PASS' if avg_min < stretch_min else 'BELOW'} |",
        f"| Target | < {target_min} min | "
        f"{'PASS' if avg_min < target_min else 'BELOW'} |",
        f"| Hard ceiling (regression) | {ceiling_min} min | "
        f"{'PASS' if avg_min < ceiling_min else 'BREACH'} |",
        "",
        "## ADVISORY",
        "",
        "This probe **never fails the build**. It surfaces the rolling",
        "completion trend so operators can intervene before regression",
        "becomes structural.",
        "",
        f"_Probe exit code: 0 (advisory)._",
    ]
    REPORT_PATH.write_text("\n".join(report) + "\n")
    print(f"odr_completion_time_drift_probe · sample={sample_size} · "
          f"mean={avg_min:.2f}min · state={drift_state}")
    print(f"  report -> {REPORT_PATH.relative_to(REPO_ROOT)}")
    client.close()
    return 0  # ADVISORY · always green to the build


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--gate", action="store_true",
                   help="Compatibility flag · advisory probe ignores gate.")
    args = p.parse_args()
    return asyncio.run(run(args.days))


if __name__ == "__main__":
    sys.exit(main())
