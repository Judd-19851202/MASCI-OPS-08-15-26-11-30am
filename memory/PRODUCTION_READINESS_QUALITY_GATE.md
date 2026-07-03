# PRODUCTION READINESS QUALITY GATE

**Doctrine:** Six Pillars · Done Means Done · No Feature Ships Without Passing This Gate.
**Established:** Track 19.30 · 2026-07-03
**Applies to:** Every future feature, fix, workflow, form, portal, PDF, integration, automation, report, dashboard, and operational module.

---

## Preamble

A feature is **not done** because it works once.
A feature is **not done** because tests pass.
A feature is **not done** because a report says green.

A feature is **only done** when it passes the full operational quality gate below. Any single failing gate blocks the feature from being called complete. Any P0 or P1 defect is an automatic NO-GO.

---

## Required Checklist

Every applicable future feature must be verified against **every** category that applies to its scope. Categories that do not apply must be explicitly marked N/A with rationale in the track's closeout document.

### Architecture
- [ ] Architecture reviewed
- [ ] Data model reviewed
- [ ] No schema drift
- [ ] No route drift
- [ ] No payload drift
- [ ] Rollback path documented

### UX
- [ ] UI reviewed
- [ ] Empty states verified
- [ ] Loading states verified
- [ ] Success states verified
- [ ] Error states verified
- [ ] No dead ends
- [ ] No duplicate confusing paths

### Device
- [ ] Mobile (iPhone 375-430 px) reviewed
- [ ] iPad portrait reviewed
- [ ] iPad landscape reviewed
- [ ] Laptop reviewed
- [ ] Desktop reviewed
- [ ] Accessibility reviewed (touch targets ≥ 44 pt · color contrast · keyboard navigation)

### Bilingual
- [ ] English verified
- [ ] Spanish verified
- [ ] Translation-on-submit doctrine respected (canonical EN keys · content-preserving user strings)
- [ ] `useT()` hook used for every display string

### Permissions
- [ ] Backend route gate verified (role headers · directory-mirror flags)
- [ ] Frontend route gate verified (auth wrapper · redirect)
- [ ] Role-based visibility verified
- [ ] Public/private boundary verified
- [ ] No raw 401/403 leakage
- [ ] Restricted-state UI is neutral and gate-enforced

### Data & routing
- [ ] Backend route verified
- [ ] Frontend route verified
- [ ] Payload verified
- [ ] Collection write confirmed
- [ ] Historical record verified (append-only where applicable)

### Cross-portal integration
- [ ] Employee 360 integration verified where applicable
- [ ] Incident Case integration verified where applicable
- [ ] Trust Spine integration verified
- [ ] Cross-portal read/write contracts respected

### Reporting & export
- [ ] Reporting verified
- [ ] Dashboard verified
- [ ] Export verified (PDF / CSV / JSON as applicable)
- [ ] PDF layout professional (no raw DB dumps · no missing fields · no private field leakage)

### Communications
- [ ] Email verified (routes correctly through `fsi_send_email`)
- [ ] Notification verified (in-platform digest respects role)
- [ ] Dry-run available where applicable
- [ ] Audit ledger records dispatch (`email_routing_audit_v2`)

### Trust & audit
- [ ] Audit event verified (append-only)
- [ ] Autosave/draft behavior verified where applicable
- [ ] Session behavior verified (`SessionStatusOverlay` catches 401)
- [ ] Original file preservation intact (SHA-256 + R2 + base64 fallback where applicable)

### Regression & testing
- [ ] Backend unit tests added / updated
- [ ] Backend route contract tests added / updated
- [ ] Frontend build clean
- [ ] Frontend lint clean
- [ ] Regression tests added
- [ ] Playwright smoke added where applicable

### Documentation
- [ ] Documentation updated
- [ ] `PRD.md` updated (PRD updated)
- [ ] `CHANGELOG.md` updated (CHANGELOG updated)
- [ ] Track-specific closeout document authored using `FUTURE_TRACK_CLOSEOUT_TEMPLATE.md`
- [ ] Rollback path documented

### Pilot / signoff
- [ ] Pilot-user validation completed where applicable
- [ ] Executive signoff completed where required
- [ ] Remaining debt scored, roadmapped, and non-blocking

---

## Gate rules

- **All applicable categories must pass.** Any category that does not apply must be marked N/A with rationale.
- **Zero P0 defects.** Automatic NO-GO if any open P0.
- **Zero P1 defects.** Automatic NO-GO if any open P1.
- **Six Pillars aggregate ≥ 48 / 60.** Anything below is NO-GO.
- **No single pillar below 7 / 10.** Any single pillar below 7 is NO-GO.
- **Zero-drift proven** for cleanup/certification tracks. Feature tracks must document any intentional schema/route/payload changes with migration + rollback plan.

## Escalation

If a track cannot pass a category and cannot mark it N/A defensibly, the correct move is to:
1. Score the gap in the closeout document.
2. Roadmap it as a P2/P3 item with owner + rationale.
3. Deliver the feature at partial completion **only if** the platform-wide Six Pillars aggregate remains ≥ 48 and no single pillar dips below 7.

**No silent deferrals.** **No undocumented debt.**

## Owner

The main agent executing the track owns gate compliance and must reference this document in every closeout.
