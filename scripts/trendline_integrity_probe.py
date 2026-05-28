#!/usr/bin/env python3
"""
trendline_integrity_probe.py — Phase V-Prelude · Wave 1.1B.

Append-only governance memory self-protection. The platform now stores
institutional calmness memory in two append-only JSON-list trendlines:

  · /app/memory/LOUDNESS_TRENDLINE.json          (portal-wide · IV-BETA.2)
  · /app/memory/TIMELINE_LOUDNESS_TRENDLINE.json (sidecar · V-Prelude 1.1A)

This probe defends those files against:

  1. shape regression           — file becomes an object, null, etc.
  2. silent overwrite           — entry count drops between deploys
  3. historical mutation        — early entries change after the fact
  4. malformed entry            — missing iteration / timestamp / score
  5. timestamp corruption       — naive timestamp or non-Z suffix
  6. chronology violation       — newer entry's timestamp predates
                                   an older entry's (monotonic check)
  7. duplicate iteration+ts     — exact-same (iteration, timestamp)
                                   pair recorded twice (replay bug)
  8. snapshot break             — last-known-good companion file
                                   `<trendline>.snapshot.json` diverges
                                   from the current trendline prefix

DOCTRINE (Wave 1.1B):
  * PROTECTIVE only — the probe NEVER mutates the trendline. It only
    READS, VERIFIES, and REFRESHES its own `.snapshot.json` companion.
  * Last known-good snapshot is the integrity anchor — corruption can
    be detected only relative to a remembered baseline.
  * Snapshot is itself a JSON object recording `entry_count`,
    `checksum_prefix`, `newest_ts`, `oldest_ts`, `refreshed_at`.
  * On detected corruption, probe `--gate` exits 1, prints a clear
    governance warning, and DOES NOT update the snapshot (the
    known-good anchor must remain intact for triage).

Usage:
  python3 scripts/trendline_integrity_probe.py            # human
  python3 scripts/trendline_integrity_probe.py --json     # CI JSON
  python3 scripts/trendline_integrity_probe.py --gate     # exit 1 on
                                                            #  violations
  python3 scripts/trendline_integrity_probe.py --refresh-snapshot
                                                            #  intentional
                                                            #  baseline
                                                            #  bump
                                                            #  (e.g.,
                                                            #  pruning)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ── Governance memory inventory ──────────────────────────────────────
#
# Every append-only trendline the probe should protect. New trendlines
# (Wave 2+) add an entry here.

TRENDLINES: List[Dict[str, Any]] = [
    {
        "name": "TIMELINE_LOUDNESS_TRENDLINE",
        "path": Path("/app/memory/TIMELINE_LOUDNESS_TRENDLINE.json"),
        "required_keys": ("iteration", "timestamp", "score", "aggregate"),
        "ts_key": "timestamp",
        "id_key": "iteration",
    },
    {
        "name": "LOUDNESS_TRENDLINE",
        "path": Path("/app/memory/LOUDNESS_TRENDLINE.json"),
        "required_keys": ("iteration", "timestamp", "portal_average_loudness"),
        "ts_key": "timestamp",
        "id_key": "iteration",
    },
    {
        # V-Prelude Observation Ledger — operator walkthrough verdicts.
        # Dedup key is the (scenario, reviewer) pair alongside timestamp;
        # encoded as a composite string here so the existing
        # single-`id_key` logic handles it without a refactor.
        "name": "OBSERVATION_LEDGER",
        "path": Path("/app/memory/OBSERVATION_LEDGER.json"),
        "required_keys": (
            "timestamp", "scenario", "reviewer",
            "answers", "freeze_trigger_observed",
        ),
        "ts_key": "timestamp",
        "id_key": "_dedup_composite",
    },
]

# Z-suffixed UTC ISO 8601, second OR millisecond precision. Reject any
# variant (Bug seed: trendline timestamps must always end with Z).
Z_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


# ── Helpers ──────────────────────────────────────────────────────────


def _utc_iso() -> str:
    d = datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


def _parse_z(ts: str) -> datetime:
    """Parse Z-suffixed ISO into a tz-aware datetime. Raises on bad
    input — callers must catch."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _prefix_checksum(entries: List[Dict[str, Any]], count: int) -> str:
    """Stable SHA-256 over the first `count` entries (key-sorted JSON
    repr) — guards against historical mutation."""
    blob = json.dumps(entries[:count], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _snapshot_path(trend_path: Path) -> Path:
    return trend_path.with_suffix(".snapshot.json")


# ── Per-trendline check ──────────────────────────────────────────────


def _check_one(spec: Dict[str, Any], *, refresh: bool) -> Dict[str, Any]:
    """Returns a dict with `violations`, `warnings`, `summary`, and
    optionally a `snapshot` that the caller may write."""
    path: Path = spec["path"]
    name: str = spec["name"]
    required_keys: Tuple[str, ...] = spec["required_keys"]
    ts_key: str = spec["ts_key"]
    id_key: str = spec["id_key"]

    out: Dict[str, Any] = {
        "name": name,
        "path": str(path),
        "violations": [],
        "warnings": [],
        "summary": {},
        "snapshot": None,
    }

    if not path.exists():
        out["warnings"].append(f"trendline missing — not yet seeded: {path}")
        return out

    # 1. Shape — must parse + be a list.
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        out["violations"].append(f"malformed JSON: {e.msg} (line {e.lineno})")
        return out
    if not isinstance(data, list):
        out["violations"].append(
            f"shape regression: expected JSON list, got {type(data).__name__}"
        )
        return out

    # 2. Per-entry validation.
    seen_ids: Dict[Tuple[str, str], int] = {}
    parsed_times: List[datetime] = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            out["violations"].append(f"entry[{idx}] is not a dict")
            continue
        for key in required_keys:
            if key not in entry:
                out["violations"].append(
                    f"entry[{idx}] missing required key: {key}"
                )
        ts = entry.get(ts_key)
        if isinstance(ts, str):
            if not Z_ISO_RE.match(ts):
                out["violations"].append(
                    f"entry[{idx}] timestamp not Z-suffixed UTC ISO: {ts}"
                )
            else:
                try:
                    parsed_times.append(_parse_z(ts))
                except Exception as e:  # noqa: BLE001
                    out["violations"].append(
                        f"entry[{idx}] timestamp parse failed: {e}"
                    )
                    parsed_times.append(None)  # type: ignore[arg-type]
        else:
            out["violations"].append(
                f"entry[{idx}] timestamp must be a string"
            )
            parsed_times.append(None)  # type: ignore[arg-type]
        # Duplicate detection — same (iteration, timestamp) pair.
        # OBSERVATION_LEDGER uses a composite identifier built from
        # (scenario, reviewer) so two distinct walkthroughs at the
        # same timestamp don't collide while genuine replays still do.
        if id_key == "_dedup_composite":
            scenario = entry.get("scenario", "")
            reviewer = entry.get("reviewer", "")
            ident = f"{scenario}|{reviewer}"
        else:
            ident = entry.get(id_key)
        if isinstance(ident, str) and isinstance(ts, str):
            key_pair = (ident, ts)
            if key_pair in seen_ids:
                out["violations"].append(
                    f"duplicate (iteration,timestamp) pair: "
                    f"entry[{idx}] == entry[{seen_ids[key_pair]}]: {key_pair}"
                )
            seen_ids[key_pair] = idx

    # 3. Monotonic chronology — timestamps must be non-decreasing.
    for i in range(1, len(parsed_times)):
        prev, curr = parsed_times[i - 1], parsed_times[i]
        if prev is None or curr is None:
            continue
        if curr < prev:
            out["violations"].append(
                f"chronology violation: entry[{i}] ({curr.isoformat()}) "
                f"older than entry[{i - 1}] ({prev.isoformat()})"
            )

    # 4. Snapshot continuity.
    snap_path = _snapshot_path(path)
    current_count = len(data)
    current_checksum_full = _prefix_checksum(data, current_count)
    if snap_path.exists():
        try:
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            assert isinstance(snap, dict)
            snap_count = int(snap.get("entry_count", 0))
            snap_prefix_checksum = str(snap.get("checksum_prefix", ""))
            # 4a. count never shrinks.
            if current_count < snap_count:
                out["violations"].append(
                    f"silent overwrite: count dropped from {snap_count} "
                    f"to {current_count}"
                )
            # 4b. Historical prefix unchanged.
            if current_count >= snap_count and snap_prefix_checksum:
                live_prefix_checksum = _prefix_checksum(data, snap_count)
                if live_prefix_checksum != snap_prefix_checksum:
                    out["violations"].append(
                        f"historical mutation detected: prefix of first "
                        f"{snap_count} entries no longer matches "
                        f"snapshot checksum"
                    )
        except Exception as e:  # noqa: BLE001
            out["warnings"].append(
                f"snapshot unreadable — will refresh: {e}"
            )
            snap_path = _snapshot_path(path)  # re-bind

    # 5. Summary.
    valid_times = [t for t in parsed_times if t is not None]
    summary = {
        "entry_count": current_count,
        "newest_ts": (
            max(valid_times).isoformat().replace("+00:00", "Z")
            if valid_times else None
        ),
        "oldest_ts": (
            min(valid_times).isoformat().replace("+00:00", "Z")
            if valid_times else None
        ),
        "duplicates_seen": sum(
            1 for v in out["violations"] if "duplicate" in v
        ),
        "monotonic_violations": sum(
            1 for v in out["violations"] if "chronology violation" in v
        ),
    }
    out["summary"] = summary

    # 6. If everything is clean (or only warnings) the snapshot may be
    # refreshed to capture the latest known-good baseline. We do this
    # ONLY when there are zero violations OR when --refresh-snapshot
    # was passed (operator-authorized re-baseline).
    if (not out["violations"]) or refresh:
        out["snapshot"] = {
            "entry_count": current_count,
            "checksum_prefix": current_checksum_full,
            "newest_ts": summary["newest_ts"],
            "oldest_ts": summary["oldest_ts"],
            "refreshed_at": _utc_iso(),
            "trendline": name,
        }

    return out


# ── Driver ──────────────────────────────────────────────────────────


def _run(*, refresh: bool) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for spec in TRENDLINES:
        results.append(_check_one(spec, refresh=refresh))
    total_violations = sum(len(r["violations"]) for r in results)
    total_warnings = sum(len(r["warnings"]) for r in results)
    return {
        "scanned": len(TRENDLINES),
        "total_violations": total_violations,
        "total_warnings": total_warnings,
        "results": results,
    }


def _write_snapshots(report: Dict[str, Any]) -> None:
    for spec, r in zip(TRENDLINES, report["results"]):
        snap = r.get("snapshot")
        if snap is None:
            continue
        snap_path = _snapshot_path(spec["path"])
        snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 on any integrity violation")
    ap.add_argument(
        "--refresh-snapshot",
        action="store_true",
        help="force snapshot refresh — use after intentional pruning",
    )
    args = ap.parse_args()

    report = _run(refresh=args.refresh_snapshot)

    # Write snapshots only when not gating (or always when refresh).
    _write_snapshots(report)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report["results"]:
            print(f"== {r['name']} ({r['path']}) ==")
            if r["violations"]:
                print(f"  ❌ {len(r['violations'])} violation(s):")
                for v in r["violations"]:
                    print(f"     · {v}")
            else:
                print("  ✓ clean")
            if r["warnings"]:
                print(f"  ⚠ {len(r['warnings'])} warning(s):")
                for w in r["warnings"]:
                    print(f"     · {w}")
            s = r["summary"]
            if s:
                print(
                    f"  entries={s.get('entry_count')} "
                    f"newest={s.get('newest_ts')} "
                    f"oldest={s.get('oldest_ts')}"
                )
        print(
            f"\n→ scanned={report['scanned']} "
            f"violations={report['total_violations']} "
            f"warnings={report['total_warnings']}"
        )

    if args.gate and report["total_violations"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
