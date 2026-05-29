# Crew-Type Readiness Matrix

_Phase V.1 · M0.2A · 2026-05-29 · FIELD READINESS INTELLIGENCE foundation._

## Mission

For every crew type, declare the **Required · Recommended · Advanced**
operational topics that distinguish a safe, productive, contract-aware
day from a noisy ODR submission.

This matrix is the source of truth for:

- the OGC catalog crew overlays (`guidance_catalog.py`)
- the M0.3 readiness engine targeted prompts
- the future FL Training Center curriculum
- the future RFI / Schedule contextual suggestion layer

The matrix lives in code at `/app/backend/routes/odr/crew_readiness_matrix.py`
and is served at `GET /api/odr/guidance/crew-readiness/{crew_type}`.

## Matrix

### Pipe Crew

| Tier | Topics |
|---|---|
| Required | utility-verification · trench-safety · grade-control · pipe-installation · compaction · joint-inspection · material-handling |
| Recommended | bedding-prep-photos · dewatering-strategy · structure-set-photos · as-built-stationing |
| Advanced | deep-trench-protection-engineered · live-utility-crossing · open-cut-vs-bore-decision |

### Utility Crew

| Tier | Topics |
|---|---|
| Required | utility-locates-verified · trench-safety · as-builts-captured · permit-compliance · compaction |
| Recommended | tie-in-photos · valve-box-set · hydrostatic-test-record |
| Advanced | cathodic-protection · directional-bore |

### Drainage Crew

| Tier | Topics |
|---|---|
| Required | utility-verification · structure-set-photos · pipe-installation · grade-control · compaction · outfall-protection |
| Recommended | inlet-protection-photos · erosion-control · tail-water-management |
| Advanced | tidal-influence-windows |

### Grading / Earthwork Crew

| Tier | Topics (grading) | Topics (earthwork) |
|---|---|---|
| Required | subgrade-prep · moisture-control · compaction-density · grade-control · haul-route-management | subgrade-prep · compaction-density · haul-route-management · stockpile-management · erosion-control |
| Recommended | stake-protection · rain-event-recovery · rough-grade-vs-fine-grade-handoff | rain-event-recovery · import-export-tracking |
| Advanced | geosynthetic-placement · lime-stabilization-curing | rock-encounter-procedures · deep-fill-staged-lifts |

### Fine Grade Crew

| Tier | Topics |
|---|---|
| Required | string-line-check · compaction-density · smoothness-tolerance · surface-prep |
| Recommended | machine-control-verification · transition-area-photos |
| Advanced | automated-grade-control-calibration |

### Stabilization Crew

| Tier | Topics |
|---|---|
| Required | mix-design-verified · moisture-control · curing-protocol · depth-verification · density-test |
| Recommended | cement-or-lime-application-rate · moisture-mapping |
| Advanced | subgrade-treatment-redo-decision |

### Paving / Asphalt Crew

| Tier | Topics (paving) |
|---|---|
| Required | mix-temperature · compaction-density · mat-thickness · joint-construction · smoothness · rolling-pattern |
| Recommended | longitudinal-joint-photos · transverse-joint-construction · tack-coat-rate · truck-cycle-time-recording |
| Advanced | night-paving-lighting-doctrine · weather-window-decision · echelon-paving-coordination |

### Milling Crew

| Tier | Topics |
|---|---|
| Required | depth-verification · haul-out-coordination · underlying-condition-photo · underground-utility-clearance · sweep-and-clean |
| Recommended | tack-coat-coordination · drum-wear-check · transition-taper |
| Advanced | variable-depth-milling-program |

### MOT Crew

| Tier | Topics |
|---|---|
| Required | setup-conformance · device-count · sign-spacing · shift-change-doctrine · advance-warning-distance · lane-closure-permits |
| Recommended | night-setup-photos · incident-response-readiness · channelizer-condition-check |
| Advanced | complex-detour-routing · high-speed-corridor-protections |

### Striping Crew (MOT sub-discipline)

| Tier | Topics |
|---|---|
| Required | layout-verification · weather-window · no-track-area-protection · removal-method · tape-vs-paint-decision |
| Recommended | rpm-spacing-verification · symbol-placement-photos |
| Advanced | thermoplastic-temperature-control · preform-application-environment |

### Concrete Crew

| Tier | Topics |
|---|---|
| Required | mix-design-verification · slump-air-tests · form-inspection · rebar-placement · cylinders-cast · finish-quality · curing-protocol |
| Recommended | weather-window-decision · control-joint-placement · cold-joint-prevention |
| Advanced | post-tension-protocol · mass-concrete-temperature-monitoring |

### Structures Crew

| Tier | Topics |
|---|---|
| Required | bedding-prep-photos · elevation-verification · grade-adjustments · manufacturer-tickets · manhole-frame-set |
| Recommended | watertightness-test · channel-and-bench |
| Advanced | precast-warranty-rejection-protocol |

### Curb / Sidewalk Crews

| Tier | Curb | Sidewalk |
|---|---|---|
| Required | string-line-check · joint-spacing · form-verification · finish-quality | string-line-check · compaction-of-subgrade · joint-pattern · finish-quality · ada-cross-slope-verification |
| Recommended | curb-cut-detail · ada-ramp-compliance | color-and-texture-conformance |
| Advanced | slip-form-program | decorative-stamp-protocol |

### Airfield Crew

| Tier | Topics |
|---|---|
| Required | escort-requirements · runway-access-window · fod-control · faa-restrictions · operational-window-adherence · tower-radio-protocols · notam-status |
| Recommended | lighting-coordination · deicing-influence |
| Advanced | active-runway-side-by-side-work · low-visibility-procedure-areas |

### Electrical Crew

| Tier | Topics |
|---|---|
| Required | lockout-tagout · circuit-identification · termination-photos · test-records-attached · energization-witness |
| Recommended | raceway-photos · conduit-bend-radius-verification |
| Advanced | high-voltage-protocol |

### Survey Support Crew

| Tier | Topics |
|---|---|
| Required | control-point-set · benchmark-check · stationing-survey · discrepancy-rfi-flag |
| Recommended | control-photo-monumentation · as-built-handoff |
| Advanced | lidar-scan-coordination |

### Demo Crew

| Tier | Topics |
|---|---|
| Required | utility-disconnect-verified · abatement-clearance · dust-control · haul-out-coordination · asbestos-survey-status |
| Recommended | selective-demo-photo · salvage-tracking |
| Advanced | controlled-blasting-protocol |

### Other (catch-all)

| Tier | Topics |
|---|---|
| Required | operation-description · manpower-and-equipment-record · safety-self-check · photo-of-work-performed |
| Recommended | tie-back-to-cleat-discipline |
| Advanced | (none yet) |

## Health

- 21 crew entries (covers all 16 enum.CrewType values + 5 field aliases).
- Every crew has ≥ 4 Required topics (probe-enforced via `matrix_health()`).
- Every Required topic is intended to map (over time) to either:
  - A specific ODR section/field that captures the topic, OR
  - A prompt_key in the OGC catalog (`guidance_catalog.py`).

## How this matrix is used downstream

| Wave | Use |
|---|---|
| M0.2A (now) | Live API + crew-aware overlays in OGC catalog |
| M0.3 (next) | Readiness engine surfaces "X of Y Required topics addressed" |
| M0.4+ | FL Training Center maps Recommended/Advanced → curriculum modules |
| M1+ | RFI suggestion / Schedule contextual hints reference Required topics |

## Verdict

🟢 **CREW READINESS MATRIX SEALED.** Every supported crew has a
declared topic floor. The matrix is queryable today and will power
the readiness engine, training curriculum, and contextual
suggestions in subsequent waves.

_End of CREW_TYPE_READINESS_MATRIX.md._
