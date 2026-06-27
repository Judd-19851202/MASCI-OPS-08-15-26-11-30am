#!/usr/bin/env python3
"""TRACK 16.00 · GitHub Repository Lifecycle Manager.

One-shot CLI that classifies every repository under a GitHub
account/org by its production-source role and retires stale
``production-health-probe`` workflows on inactive snapshot repos.
This is the one-time backfill tool for snapshots that pre-date the
Track 16.00 self-silencing workflow shape.

After this tool has run once, **no further customer action is ever
required** — every new snapshot Emergent creates from this build
forward is automatically silent because:

* The workflow file in every snapshot checks ``vars.ACTIVE_PRODUCTION_SOURCE``.
* GitHub repository variables are NOT copied to snapshots/forks.
* Therefore every fresh snapshot has the variable unset and the
  workflow self-classifies as silent.

Usage
=====

    GITHUB_PAT=ghp_xxxx \
    GITHUB_OWNER=Judd-19851202 \
    ACTIVE_PROD_REPO=Judd-19851202/MASCI-OPS-6-25-26-10m \
    python3 scripts/github_lifecycle_manager.py --apply

Or to preview without making any change:

    GITHUB_PAT=ghp_xxxx \
    GITHUB_OWNER=Judd-19851202 \
    ACTIVE_PROD_REPO=Judd-19851202/MASCI-OPS-6-25-26-10m \
    python3 scripts/github_lifecycle_manager.py --dry-run

Required PAT scopes
-------------------

* ``repo``       — to read repo contents and write the actions-disable call
* ``workflow``   — to manage workflow state
* ``actions:write`` (implied by ``workflow``)
* ``administration:write`` — OPTIONAL, only if you want branch-protection
  cleanup. Without it the script will report branch protection as
  ``UNABLE_TO_VERIFY`` and not fail.

Token safety
------------

* The token is read from the ``GITHUB_PAT`` environment variable.
* The token is NEVER printed, NEVER written to disk, NEVER logged.
* Every output line that could conceivably echo the token is sanitised.

Scope filter
------------

The script ONLY touches repos whose name matches the MASCI/Plat/Ops
snapshot pattern. Unrelated repos in the same account are skipped.
The active production repo is read-only verified (never modified).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple


GITHUB_API = "https://api.github.com"

# MASCI/Plat/Ops snapshot pattern (case-insensitive).
SNAPSHOT_NAME_RE = re.compile(
    r"^(masci[-_]ops|masci[-_]plat|masci[-_]|forgedops|.*-ops[-_])",
    re.IGNORECASE,
)

# Workflows touched by this script. Anything outside this list is left alone.
TARGET_WORKFLOW_FILES = (
    "production-health-probe.yml",
    "production-health-probe.yaml",
    "production-health-probe-pr-noop.yml",
    "production-health-probe-pr-noop.yaml",
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _api_request(
    method: str,
    path: str,
    *,
    token: str,
    body: Optional[Dict[str, Any]] = None,
    accept: str = "application/vnd.github+json",
) -> Tuple[int, Any]:
    url = path if path.startswith("http") else f"{GITHUB_API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "masci-lifecycle-manager/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    except Exception as e:  # noqa: BLE001
        return 0, {"error": f"{type(e).__name__}: {e}"}
    try:
        payload = json.loads(raw) if raw else None
    except Exception:
        payload = {"raw": raw[:400].decode("utf-8", "replace") if raw else None}
    return status, payload


def _list_repos(owner: str, token: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    page = 1
    while True:
        status, payload = _api_request(
            "GET",
            f"/users/{owner}/repos?per_page=100&page={page}&type=all",
            token=token,
        )
        if status != 200:
            # Fall back to /user/repos if /users/{owner}/repos fails (org/account).
            status, payload = _api_request(
                "GET",
                f"/user/repos?per_page=100&page={page}&affiliation=owner,collaborator,organization_member",
                token=token,
            )
        if status != 200 or not isinstance(payload, list):
            raise SystemExit(
                f"GitHub repo listing failed: HTTP {status} (page {page})"
            )
        if not payload:
            break
        out.extend(payload)
        if len(payload) < 100:
            break
        page += 1
    return out


# ---------------------------------------------------------------------------
# Classification + workflow operations
# ---------------------------------------------------------------------------

def _classify(repo: Dict[str, Any], active_full_name: str) -> str:
    full = repo.get("full_name") or ""
    name = repo.get("name") or ""
    if full == active_full_name:
        return "ACTIVE_PRODUCTION_SOURCE"
    if repo.get("archived"):
        return "ARCHIVED"
    if SNAPSHOT_NAME_RE.match(name):
        return "INACTIVE_SNAPSHOT"
    return "UNRELATED"


def _list_workflows(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    status, payload = _api_request(
        "GET", f"/repos/{owner}/{repo}/actions/workflows", token=token
    )
    if status != 200 or not isinstance(payload, dict):
        return []
    return payload.get("workflows") or []


def _disable_workflow(owner: str, repo: str, wf_id: int, token: str) -> Tuple[int, Any]:
    return _api_request(
        "PUT",
        f"/repos/{owner}/{repo}/actions/workflows/{wf_id}/disable",
        token=token,
    )


def _delete_file(
    owner: str, repo: str, path: str, token: str
) -> Tuple[int, Any]:
    # Get file SHA first.
    status, payload = _api_request(
        "GET", f"/repos/{owner}/{repo}/contents/{path}", token=token
    )
    if status != 200 or not isinstance(payload, dict):
        return status, payload
    sha = payload.get("sha")
    if not sha:
        return 0, {"error": "no sha"}
    return _api_request(
        "DELETE",
        f"/repos/{owner}/{repo}/contents/{path}",
        token=token,
        body={
            "message": "Track 16.00 — retire stale production-health-probe noop",
            "sha": sha,
        },
    )


def _strip_required_check(
    owner: str, repo: str, branch: str, token: str
) -> Tuple[str, str]:
    """Best-effort removal of `production-health-probe / probe` from
    branch protection's required status checks. Returns (status, note).
    """
    status, payload = _api_request(
        "GET",
        f"/repos/{owner}/{repo}/branches/{branch}/protection",
        token=token,
    )
    if status == 404:
        return "no_protection", "no branch protection on " + branch
    if status == 403:
        return "no_admin_scope", "PAT lacks administration:read"
    if status != 200 or not isinstance(payload, dict):
        return "unknown", f"HTTP {status}"
    rsc = (payload.get("required_status_checks") or {})
    contexts = list(rsc.get("contexts") or [])
    checks = list(rsc.get("checks") or [])
    bad_names = {"production-health-probe", "production-health-probe / probe"}
    contexts_new = [c for c in contexts if c not in bad_names]
    checks_new = [c for c in checks if c.get("context") not in bad_names]
    if contexts == contexts_new and checks == checks_new:
        return "noop", "no obsolete required check found"
    # GitHub's protection PUT requires the full body shape — best-effort.
    body = {
        "required_status_checks": {
            "strict": rsc.get("strict", False),
            "contexts": contexts_new,
        },
        "enforce_admins": (payload.get("enforce_admins") or {}).get("enabled"),
        "required_pull_request_reviews": payload.get(
            "required_pull_request_reviews"
        ),
        "restrictions": payload.get("restrictions"),
    }
    # Remove None keys — GitHub API rejects unexpected nulls.
    body = {k: v for k, v in body.items() if v is not None}
    status, _ = _api_request(
        "PUT",
        f"/repos/{owner}/{repo}/branches/{branch}/protection",
        token=token,
        body=body,
    )
    if status in (200, 201, 204):
        return "removed", "obsolete required check removed"
    if status == 403:
        return "no_admin_scope", "PAT lacks administration:write"
    return "failed", f"HTTP {status}"


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Track 16.00 GitHub lifecycle manager",
    )
    parser.add_argument("--dry-run", action="store_true", help="report only")
    parser.add_argument("--apply", action="store_true", help="make changes")
    parser.add_argument(
        "--delete-noop", action="store_true",
        help="also delete production-health-probe-pr-noop.yml on inactive repos"
    )
    parser.add_argument(
        "--strip-required-checks", action="store_true",
        help="remove obsolete required status checks (needs admin scope)"
    )
    args = parser.parse_args()

    if args.dry_run == args.apply:
        # require exactly one of --dry-run / --apply
        parser.error("specify exactly one of --dry-run or --apply")

    token = os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN") or ""
    owner = os.environ.get("GITHUB_OWNER", "").strip()
    active = (os.environ.get("ACTIVE_PROD_REPO", "") or "").strip()

    if not token:
        print("ERROR: GITHUB_PAT env var not set", file=sys.stderr)
        return 2
    if not owner:
        print("ERROR: GITHUB_OWNER env var not set", file=sys.stderr)
        return 2
    if not active:
        print("ERROR: ACTIVE_PROD_REPO env var not set", file=sys.stderr)
        return 2
    if "/" not in active:
        active = f"{owner}/{active}"

    print(f"[lifecycle] owner={owner}  active={active}  mode={'apply' if args.apply else 'dry-run'}")
    print(f"[lifecycle] token: <{len(token)} chars · redacted>")
    print()

    repos = _list_repos(owner, token)
    print(f"[lifecycle] {len(repos)} repos enumerated")
    print()

    rows: List[Dict[str, Any]] = []
    for r in sorted(repos, key=lambda x: x.get("name", "")):
        full = r.get("full_name") or ""
        name = r.get("name") or ""
        cls = _classify(r, active)
        if cls not in ("ACTIVE_PRODUCTION_SOURCE", "INACTIVE_SNAPSHOT"):
            rows.append({
                "repo": full, "class": cls, "before": "—",
                "action": "skipped (out of scope)",
                "noop": "—", "branch_protection": "—",
                "final": "skipped",
            })
            continue
        wfs = _list_workflows(owner, name, token)
        probe = next(
            (w for w in wfs if w.get("path", "").endswith("production-health-probe.yml")
             or w.get("path", "").endswith("production-health-probe.yaml")),
            None,
        )
        noop = next(
            (w for w in wfs if "production-health-probe-pr-noop" in (w.get("path") or "")),
            None,
        )
        before = (probe or {}).get("state") or "absent"
        action = "noop"
        noop_action = "n/a"
        bp_action = "skipped"

        if cls == "ACTIVE_PRODUCTION_SOURCE":
            # READ-ONLY verification
            action = "verified (no change)" if probe and probe.get("state") == "active" else f"verify — probe state={before}"
            if noop:
                noop_action = "WARN: stale noop sibling present in active repo — operator should delete"
            rows.append({
                "repo": full, "class": cls, "before": before,
                "action": action, "noop": noop_action,
                "branch_protection": "not modified (active repo)",
                "final": "active_verified" if probe and probe.get("state") == "active" else "active_attention_needed",
            })
            continue

        # INACTIVE_SNAPSHOT
        if probe and probe.get("state") == "active":
            if args.apply:
                st, _ = _disable_workflow(owner, name, probe["id"], token)
                action = f"disabled (HTTP {st})" if st in (200, 204) else f"disable failed (HTTP {st})"
            else:
                action = "would disable (dry-run)"
        elif probe:
            action = f"already {probe.get('state')}"
        else:
            action = "no probe workflow present"

        if noop:
            if args.apply and args.delete_noop:
                st, _ = _delete_file(
                    owner, name, noop.get("path") or "", token
                )
                noop_action = f"deleted (HTTP {st})" if st in (200, 201) else f"delete failed (HTTP {st})"
            elif args.delete_noop:
                noop_action = "would delete (dry-run)"
            else:
                noop_action = "present (use --delete-noop to remove)"

        if args.apply and args.strip_required_checks:
            default_branch = r.get("default_branch") or "main"
            res, note = _strip_required_check(owner, name, default_branch, token)
            bp_action = f"{res} ({note})"
        elif args.strip_required_checks:
            bp_action = "would inspect (dry-run)"

        rows.append({
            "repo": full, "class": cls, "before": before,
            "action": action, "noop": noop_action,
            "branch_protection": bp_action,
            "final": "silent" if "disabled" in action or "already disabled" in action
                     or action == "no probe workflow present" else "review",
        })

    # Render table
    print(f"{'Repo':<45} {'Class':<26} {'Before':<10} {'Action':<28} {'Noop':<14} {'BP':<22} Final")
    print("-" * 160)
    for row in rows:
        print(
            f"{row['repo']:<45} {row['class']:<26} {row['before']:<10} "
            f"{row['action']:<28} {row['noop']:<14} {row['branch_protection']:<22} {row['final']}"
        )
    print()
    print(f"[lifecycle] complete · {sum(1 for r in rows if r['final']=='silent')} repo(s) now silent · "
          f"{sum(1 for r in rows if r['final']=='active_verified')} repo(s) active+verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
