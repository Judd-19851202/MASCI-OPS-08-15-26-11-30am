# WP-17D Active Defect Register

## P0 active defects
1. **Transportation auth/runtime drift**
   - Symptom: valid users may encounter auth/runtime instability across Transportation prefixes and mixed shells.
   - Required repair: unify shell behavior, remove duplicate nav patterns, verify route/token handling across Mission Control, Operations, Intelligence, administration, carrier workflows, and detail routes.
2. **HR partial migration drift**
   - Symptom: inconsistent shell/card/form/list/detail behavior across HR routes.
   - Required repair: converge all HR surfaces onto the canonical shell, hierarchy, spacing, controls, and coaching posture.
3. **Carrier/public external flow inconsistency**
   - Symptom: external invite, token, orientation, and verification flows still feel like legacy microsites.
   - Required repair: move all external/public transportation workflows into the canonical white-label public family.

## Current wave notes
- Shared shell defaults now converge `PortalShell` surfaces onto the WP-17D wave.
- Shared login shell, HR shell, Safety shell, PM shell, and form shell are in active convergence.
- Transportation shared shell, subnav, Mission Control cards, and external workflows are under active repair.
