# MASCI Platform — Five-Pillar Matrix (Track 13.4C · Deliverable #7)

**Five Pillars:** Powerful · Simple · Beautiful · Trusted · Proven.  
**Lens:** every Tier-1 finding is evaluated against the pillar(s) it violates and the severity of that violation.  
**Mode:** decision framework only — NO proposed fixes.

Severity scale: ◯ none · ◔ low · ◑ medium · ◕ high · ● critical.

---

## Tier-1 findings × Five Pillars

| Finding (Tier 1) | Powerful | Simple | Beautiful | Trusted | Proven | Operational impact |
|---|---|---|---|---|---|---|
| **W-01** No tenant model | ◔ | ◑ | ◯ | ● | ◕ | ForgedOps cannot productise; MASCI fine today |
| **W-02** No tenant scoping in routes | ◔ | ◑ | ◯ | ● | ◕ | Same as W-01 |
| **W-09** Hardcoded MASCI legal text (EN+ES) | ◯ | ◔ | ◯ | ● | ◕ | Legal exposure for Customer #2 |
| **W-12** No tenant onboarding surface | ◔ | ◑ | ◯ | ◕ | ◕ | Manual ops project to onboard |
| **D-01** Production Motive webhook unverified | ● | ◔ | ◯ | ● | ● | If Dispatch isn't live, the operational truth surface is fiction |
| **D-03** 100/190 assets no GPS | ● | ◑ | ◯ | ● | ◕ | Dispatcher can't locate 53 % of fleet from map |
| **D-04** 157 assets stale | ● | ◑ | ◯ | ● | ◕ | Dispatcher fog of war |
| **T-01** Safety-Critical UI Spanish 75.8 % | ◑ | ◑ | ◯ | ◕ | ● | Spanish crew reads safety strings in English — direct safety risk |
| **T-08** Outbound emails English-only | ◑ | ◔ | ◔ | ◑ | ● | Spanish recipients get English emails |
| **T-09** PDFs English-only | ◑ | ◔ | ◔ | ◑ | ● | Spanish recipients sign English PDFs |
| **V-04** `tokens.css` PROPOSAL — not wired | ◑ | ◔ | ◑ | ◔ | ● | No retheming layer ready; blocks design system + tenant |
| **W-13** Per-workflow status engines hardcoded | ◑ | ◑ | ◯ | ◑ | ◕ | Workflow customisation impossible |

---

## Tier-1 pillar summary

| Pillar | # Tier-1 findings violating | Top violator |
|---|---|---|
| **Powerful** | 6 | D-01 · D-03 · D-04 (Dispatch trust collapse if proven untrustworthy) |
| **Simple** | 5 | V-04 (no token layer means rebrand touches every JSX file) |
| **Beautiful** | 4 | V-04 (theme/visual coherence depends on tokens) |
| **Trusted** | 11 of 12 | D-01 / D-03 / D-04 / T-01 / W-01 / W-09 — trust is the dominant violated pillar |
| **Proven** | 10 of 12 | T-01 / T-08 / T-09 / V-04 — most Tier-1 findings show no Spanish or no tenant proof exists today |

### Headline pillar reading

**Trust** and **Proven** are the dominantly-violated pillars in Tier 1.

- **Trust** is violated whenever the operator sees something they
  cannot rely on (Dispatch fog of war · MASCI legal text on
  Customer #2 forms · Safety-Critical strings in the wrong language).
- **Proven** is violated whenever a critical capability exists in
  *name* but not in *verified, audited operation* — the unproved
  Motive production webhook (D-01), unproved Spanish path on
  safety-critical surfaces (T-01), `tokens.css` self-declared as
  "PROPOSAL — NOT YET WIRED" (V-04).

**Powerful** is violated in Dispatch's data-integrity findings —
without trustworthy live data, the most powerful surface on the
platform is hollow.

**Simple** and **Beautiful** are surface-level pillars in Tier 1; they
become dominant in Tier 2 (15 components for one status family,
4.6× hub size variance, etc.).

---

## Tier-2 spot-check (not exhaustive)

| Finding | Strongest pillar(s) violated |
|---|---|
| V-09 / R-03 Command-center sprawl | Simple |
| V-07 Status-chip sprawl (15 components) | Simple · Beautiful |
| R-01 Eight auth-flow variations | Simple |
| R-02 Form data duplication | Simple · Proven |
| W-03 / W-04 / W-08 Brand & email leaks | Trusted (for Customer #2) |
| V-13 Mobile evidence gap | Proven |
| V-15 Driver portal landing missing | Powerful · Trusted |

---

## What this matrix did NOT do
- Did not propose remediation per pillar.
- Did not score Tier-3 findings (they do not move the needle here).
- Did not weight pillars against each other.

Pillar weighting and remediation sequencing belong to Track 13.4D.
