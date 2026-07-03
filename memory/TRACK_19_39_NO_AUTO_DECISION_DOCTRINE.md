# TRACK 19.39 · NO-AUTO-DECISION DOCTRINE

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_37_NO_AUTO_DECISION_DOCTRINE.md`

## Doctrine
The digest is an **attention signal only.** Safety owns investigation and classification. The platform routes, records, reports, protects, and surfaces risk signals — it never decides OSHA recordability, root cause, liability, fault, discipline, or insurance responsibility.

## Verbatim notice emitted with every digest
> *"This digest is an attention signal only. Safety owns investigation and classification. The platform does not decide OSHA recordability, root cause, liability, fault, discipline, or insurance responsibility."*

The notice is:
- **Required** on every digest object (`no_auto_decision_notice`).
- **Rendered** verbatim in the email HTML footer.
- **Locked** by the Track 19.39 pytest test.

## Forbidden vocabulary in digest body/HTML
The following words / phrases must **not** appear in `executive_summary`, `top_attention_cases`, `needs_attention_today`, or `portfolio_trends`:
`osha_recordable` · `liability` · `liable` · `discipline` · `disciplinary` · `fault` · `blame` · `preventability` · `root_cause_conclusion`.

The `no_auto_decision_notice` field is **exempt** from the ban — it must be able to name what the platform does **not** decide.

Enforcement: `test_digest_body_free_of_forbidden_vocabulary` in the lock test suite.

## Rationale
Automated risk classification, when emailed weekly, becomes a policy artifact. It gets forwarded, replied to, and printed. If the digest contained OSHA-recordability determinations, it could be subpoenaed and used against the company. Attention-only wording is legally and operationally safer, and it aligns with how Safety Managers actually work — they use it to *look here first*, not to *close the case*.
