# GOVERNANCE-HARDEN-001 · Workstream E · Certification Standard Enforcement

```
Environment    : both (this doctrine applies to every certification touching either)
Access Level   : n/a (doctrine document)
Evidence Source: derived from TRUTH-AUDIT-001 § Certification Doctrine
Confidence     : VERIFIED (doctrine restatement) · ENFORCEMENT TOOLING NOT YET BUILT
```

---

## §E.1 · Mandatory four-field header

Every certification document under `/app/memory/` **must** open with:

```
Environment    : <preview | production | both | other-named-environment>
Access Level   : <see §E.3>
Evidence Source: <see §E.4>
Confidence     : VERIFIED | INFERRED | ASSUMED  (or per-section breakdown)
```

A certification document lacking any of these four fields **fails certification automatically.** Operators must reject any such report on sight, and any future fork agent that produces a report without the header is in violation of doctrine.

## §E.2 · Why this exists

`TRUTH_AUDIT_001_REPORT_RECONCILIATION.md` documented three concrete failure modes that this header prevents:

1. **Conflating "backend default DB binding" with "credential capability"** (`AUDIT-ACCESS-VERIFY-001` Q6: answered NO when correct answer was YES).
2. **Claiming verdicts without disclosing whether prod was touched** (`POST-DEPLOY-002` § 1 verdict).
3. **Inferring credential state from webhook behaviour and reporting it as VERIFIED** (`PROD-STABILIZE-001` § Phase 1 #1-2).

In all three cases the author would have been forced to confront the gap if the four-field header had been required.

## §E.3 · Access Level enumeration

| Token | Meaning |
|---|---|
| `public-only` | HTTPS probes against publicly-routable endpoints only. No auth. |
| `preview-runtime+preview-DB` | Full root inside the preview fork pod + read/write on `masci_safety_preview` only. |
| `prod-DB-read` | Read-only Mongo access to `masci_safety`. |
| `prod-DB-read+write` | Read AND write Mongo access to `masci_safety`. **Requires explicit operator authorization stated in the report body.** |
| `prod-admin-UI` | Authenticated session as admin in the production frontend. |
| `prod-super-admin-UI` | Authenticated session as super-admin (MFA-stepped). |
| `atlas-console` | Atlas user / role / network management (UI). Operator-only. |
| `mixed` | Multiple — body MUST enumerate which level for which section. |

## §E.4 · Evidence Source enumeration

| Token | Meaning |
|---|---|
| `external-probe` | `curl` / browser request to externally-routable URL. |
| `preview-runtime` | bash/python/supervisor/logs inside preview pod. |
| `preview-DB` | Direct Mongo queries against `masci_safety_preview`. |
| `prod-DB (read-only)` | Direct Mongo `find` / `count` / `aggregate` against `masci_safety`. |
| `prod-DB (read/write)` | Direct Mongo `insert` / `update` / `delete` against `masci_safety`. |
| `operator-attested` | Underlying fact provided by the operator; agent did not directly observe it. |
| `static-analysis` | Source code review without runtime probe. |
| `existing-test-suite` | Running pre-existing jest/pytest tests and reporting their result. |
| `atlas-console` | Atlas Console screenshot or operator-attested admin action. |
| `mixed` | Multiple — body MUST enumerate per section. |

## §E.5 · Confidence enumeration

| Token | Meaning |
|---|---|
| `VERIFIED` | Primary-source observation captured in this audit directly demonstrates the claim. |
| `INFERRED` | Derived from indirect evidence; consistent but not directly observed. |
| `ASSUMED` | Held true but no observation in this audit demonstrates it. |

When a single document carries different confidence levels for different sections, the header MUST itemize: `Confidence : VERIFIED for §1-§3; INFERRED for §4; ASSUMED for §5`.

## §E.6 · Automated enforcement plan

⚠️ **Not implemented in this sprint** — implementation is a code change which would itself require its own certification.

Proposed implementation (NOT executed):

```python
# /app/backend/lib/cert_header_guard.py  (sketch — not written this sprint)
import re
from pathlib import Path

HEADER_RE = re.compile(
    r"^Environment\s*:\s*\S+.*?^Access Level\s*:\s*\S+.*?"
    r"^Evidence Source\s*:\s*\S+.*?^Confidence\s*:\s*\S+",
    re.MULTILINE | re.DOTALL,
)
CERT_GLOB = "/app/memory/*_CERTIFICATION*.md"

def scan() -> list[str]:
    failed = []
    for path in Path("/app/memory").glob("*_CERTIFICATION*.md"):
        text = path.read_text(errors="ignore")[:3000]
        if not HEADER_RE.search(text):
            failed.append(str(path))
    return failed
```

Wiring options (operator decides):
- **Pre-commit hook** in the repo: blocks commits that add a `*_CERTIFICATION*.md` without the header.
- **Backend startup check**: refuses to boot if any *_CERTIFICATION*.md lacks the header (most aggressive).
- **CI / GitHub Action**: runs on every PR.
- **Manual operator review**: reject reports lacking the header.

Until tooling is built, **enforcement is by operator review**. The operator MUST reject any new certification without the four-field header.

## §E.7 · Retroactive compliance

This doctrine is **forward-looking**. Prior certifications (POST-DEPLOY-001/002/003, MOTIVE-*, PROD-STABILIZE-001, AUDIT-ACCESS-VERIFY-001, etc.) are reconciled in `TRUTH_AUDIT_001_REPORT_RECONCILIATION.md`. They are not retroactively invalidated for missing the header; they are reconciled in place.

All new certifications starting with **TRUTH-AUDIT-001** carry the header. Every report in the GOVERNANCE-HARDEN-001 bundle (this document and its peers) carries the header at the top.

## §E.8 · Examples

### Correct header

```
# DR-EXPORT-001 · Daily Report Export Hardening Certification

Environment    : both
Access Level   : preview-runtime+preview-DB · prod-DB-read
Evidence Source: mixed (existing-test-suite + preview-runtime + prod-DB read-only)
Confidence     : VERIFIED for §1-§5; INFERRED for §6 (operator-attested email delivery)
```

### Incorrect header (auto-rejected)

```
# Some Sprint Final Certification
Verdict: PASS
Date: 2026-06-09
```

Rejected — missing all four mandatory fields.

## §E.9 · Verdict — Workstream E

✅ **PASS as a doctrine.** ⚠️ **ENFORCEMENT TOOLING NOT YET BUILT** — operator review is the current enforcement mechanism. The doctrine is restated and all GOVERNANCE-HARDEN-001 documents conform.
