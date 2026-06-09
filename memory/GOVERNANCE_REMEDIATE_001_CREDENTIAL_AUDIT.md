# GOVERNANCE-REMEDIATE-001 · Credential Governance Audit (test_credentials.md)

```
Environment    : preview (file lives in preview pod) · documented as cross-env
Access Level   : static-analysis of /app/memory/test_credentials.md
Evidence Source: preview-runtime file read
Confidence     : VERIFIED for file contents · INFERRED for whether listed prod credentials still work today
```

---

## §1 · Scope

Audit `/app/memory/test_credentials.md` against the directive's requirements:
- Preview credentials only
- No production-only secrets
- No production-capable service credentials

## §2 · Findings (account-level)

Values **masked**. Lengths and provenance only.

| Account email | Password reference (masked) | File claim | Class today |
|---|---|---|---|
| `jaymn.judd@mascigc.com` | `Mxxxxx123!` (10 char) | "Test accounts apply to BOTH databases" (file line 16) | 🔴 **PRODUCTION-CAPABLE** (super-admin across all 4 portals) |
| `hrmanager@mascigc.com` | `HRxxxxxxx2026!` (14 char) | per same doctrine | 🔴 PROD-CAPABLE |
| `dispatch@mascigc.com` | `Dxxxxxxxxxxx2026!` (17 char) | per same doctrine | 🔴 PROD-CAPABLE |
| `chriswright@mascigc.com` | `CxxxxxxxxxThis2026` (18 char) | per same doctrine | 🔴 PROD-CAPABLE |
| `testmech@mascigc.com` | `RxxxxxWorks2026!` (16 char) | per same doctrine | 🔴 PROD-CAPABLE |
| `asphaltpm@mascigc.com` | (no password issued) | "preview only — needs to be added in prod admin console after redeploy" | 🟡 PREVIEW-ONLY-TODAY |
| `leomasci@mascigc.com` | (no password issued) | same | 🟡 PREVIEW-ONLY-TODAY |
| `safety@mascigc.com` | (rotated to temp) | preview only | 🟡 PREVIEW-ONLY-TODAY |
| `shopmanager@mascigc.com` | (no password issued in preview) | not currently usable | 🟢 NOT-USABLE |
| `fieldleader@mascigc.com` | (deactivated 2026-05-31) | "DEACTIVATED" | 🟢 INACTIVE |

**5 currently-usable accounts have passwords documented as working in production.** This violates the requirement "Preview credentials only."

## §3 · Findings (system-secret level)

The file also documents:
- `MFA_ENCRYPTION_KEY` is "required env" and "MUST be set in production before deploy" — implies the same Fernet key is intended in both envs. (Inferred prod-shared.)
- `SUPER_ADMIN_EMAIL` + `SUPER_ADMIN_BOOTSTRAP_PASSWORD` are referenced by name; the bootstrap is documented as the path that created `jaymn.judd@mascigc.com`.

Neither is *itself* a credential in the file, but the file points at the env-var pair that controls the super-admin bootstrap. The bootstrap password is the 🔴 PROD-CAPABLE risk surface.

## §4 · Required corrective actions (NOT taken by fork)

⚠️ Per directive — **no employee passwords were changed by this fork**. The corrective actions remain operator-owned.

### Required (operator action):

1. **Update `test_credentials.md`** to insert, prominently at the top of every account block, the following annotation:

   > **DO NOT USE THIS PASSWORD AGAINST PRODUCTION.** This account's preview password is intentionally distinct from any production password. If the file states "Test accounts apply to BOTH databases," that statement is **withdrawn as of GOVERNANCE-REMEDIATE-001 (2026-06-09)**.

2. **Rotate the prod-side password** of each of the 5 PROD-CAPABLE accounts using the standard `/admin/users/{id}/reset-password` admin path (not by changing the bcrypt hash in DB). The new prod password is **operator-chosen and NOT stored in `test_credentials.md`**.

3. **Update `test_credentials.md`** to replace the historical line:
   > "Test accounts apply to BOTH databases — the preview DB was seeded with a snapshot of production users before today's change, so the same credentials work on both environments."

   with:
   > "Preview accounts are independently maintained from production accounts as of GOVERNANCE-REMEDIATE-001 (2026-06-09). Passwords listed below apply to the preview environment only."

### NOT required:

- No preview passwords need to change.
- No user account needs to be deleted.
- No preview user needs to re-enroll.
- No employee experiences anything until the operator rotates the prod-side password.

## §5 · What this audit DID NOT do (and why)

- ❌ Did not change `test_credentials.md` content. **Directive prohibits password changes; updating the file with new passwords would imply password change.** The doctrine annotation in §4.1 is the only acceptable in-place edit and the fork defers it to the operator so the operator's commit history records the governance change.
- ❌ Did not query production `user_directory` to see which of the 5 accounts still exist there or have current `must_change_password` flags set. That is a useful follow-on operator check.
- ❌ Did not attempt any prod-side login. Per AUDIT-ACCESS-VERIFY-001 doctrine, that would create an `admin_audit_log` row in production.

## §6 · Verdict — Workstream E

✅ **PASS as an audit. ❌ FAIL as a control posture.** Same as GOVERNANCE-HARDEN-001 § Workstream D conclusion: 5 PROD-CAPABLE shared credentials remain in `test_credentials.md`. Operator must execute §4.1 / §4.2 / §4.3.
