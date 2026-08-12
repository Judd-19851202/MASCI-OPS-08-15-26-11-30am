#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--git-ref")
    parser.add_argument("--write")
    parser.add_argument("--compare-ref-a")
    parser.add_argument("--compare-ref-b")
    args = parser.parse_args()

    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root / "backend"))
    from lib.release_fingerprint import build_release_manifest, compare_manifests, write_fingerprint_record  # noqa: WPS433

    if args.compare_ref_a and args.compare_ref_b:
        a = build_release_manifest(repo_root, git_ref=args.compare_ref_a)
        b = build_release_manifest(repo_root, git_ref=args.compare_ref_b)
        payload = compare_manifests(a, b)
        print(json.dumps(payload, indent=2))
        return 0

    if args.write:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
        status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=repo_root, text=True).splitlines()
        payload = write_fingerprint_record(
            repo_root,
            output_path=repo_root / args.write,
            base_head=head,
            workspace_status_lines=status,
        )
        print(json.dumps(payload, indent=2) if args.json else payload["content_manifest_sha256"])
        return 0

    payload = build_release_manifest(repo_root, git_ref=args.git_ref)
    print(json.dumps(payload, indent=2) if args.json or args.git_ref else payload["manifest_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())