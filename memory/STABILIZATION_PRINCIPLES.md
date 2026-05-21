# Stabilization Principles · MASCI Operations Platform

Captured iter309 · governs operational maintenance posture for forks and future agents.

The platform is now **operational infrastructure**, not an experimental build-phase project. Crews depend on it daily. Apply these principles before touching code.

## Eight operating principles

1. **Do not refactor during stabilization without operational evidence.** Code smells are not evidence. Real crew friction, real outages, or real bug reports are.

2. **Do not mechanically apply analyzer / lint / security-scan output.** These tools generate signal AND noise. Triage every finding against operator posture before acting.

3. **Operational trust outweighs architectural purity during stabilization.** A working, slightly imperfect system in crew hands is more valuable than a refactored one that risks regression.

4. **Preserve signal-to-noise discipline in logs and error handlers.** Add log lines only when they surface something an operator would act on. Conditional emission (e.g. `if orphans: log(...)`) is preferred to unconditional emission.

5. **Crew-facing surfaces may intentionally fail quietly.** Admin surfaces should fail visibly and audibly. The two have opposite error-handling contracts and that is intentional.

6. **MD5 source/build hashing is NOT security cryptography.** Drift fingerprinting (e.g. `_compute_source_hash()`) is a build-identity contract. Do not "upgrade" it to SHA-256 to placate a scanner.

7. **Known technical debt may remain intentionally deferred** when bounded, understood, non-operational, and non-user-impacting. Document it; don't fix it preemptively.

8. **Stabilization posture priorities** (in order): reliability · consistency · bilingual trust · mobile usability · operational continuity. Above: framework purity, refactor completeness, analyzer cleanliness.

## Examples of intentional patterns (do not "fix")

- **Load-once hook patterns** — `useEffect(() => {...}, [])` is intentional when the data is fetched once per mount.
- **Static-list array keys** — `key={index}` is correct for lists that never reorder within a parent's lifetime.
- **Scope-based silent catches** — anonymous users hitting scoped endpoints should render nothing, not console-spam.
- **Preview test fixtures** — admin passwords in test files target the preview DB and are intentionally checked in for reproducibility.
- **Bounded architectural debt** — circular-looking import graphs that boot cleanly are not actual cycles.

## When in doubt

Ask the operator before refactoring, before mechanically applying any analyzer report, and before adding instrumentation. Stabilization is about not breaking what works — not about reaching a perfect score on someone else's checklist.
