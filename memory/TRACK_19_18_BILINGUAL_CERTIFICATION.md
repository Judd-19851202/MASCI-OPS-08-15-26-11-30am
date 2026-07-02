# Track 19.18 · Bilingual Certification

**Doctrine:** Nothing may exist only in English. Nothing may exist only in Spanish.

## New keys added in Track 19.18

10 EN→ES entries covering the Safety Case Workspace polish surface:

| EN | ES |
|---|---|
| Case story | Historia del caso |
| Next action | Próxima acción |
| On {when}, a {type} was reported at {where}{job}. | El {when}, se reportó un {type} en {where}{job}. |
| Reported by {who}. | Reportado por {who}. |
| Ready for closeout | Listo para cierre |
| Under investigation | Bajo investigación |
| Early — evidence gathering | Etapa inicial — recolección de evidencia |
| an unrecorded date | una fecha no registrada |
| an unspecified location | una ubicación no especificada |
| the on-site reporter | el reportero en el sitio |

## Track 19.17 EN/ES parity (carried forward)

All 8 new incident types + their descriptions + examples + step titles + field labels have Spanish equivalents. Certified in Track 19.17 by the testing agent (100% pass).

## Bilingual coverage matrix

| Surface | EN | ES |
|---|---|---|
| Incident type picker (17 cards) | ✓ | ✓ |
| Incident branch flows (17 flows) | ✓ | ✓ |
| Field labels (all steps) | ✓ | ✓ |
| Guardrail step labels | ✓ | ✓ |
| Header layout | ✓ | ✓ |
| ProgressRail | ✓ | ✓ |
| Submit gate messages | ✓ | ✓ |
| HelpDrawer content | ✓ | ✓ |
| Presence gate | ✓ | ✓ |
| Case Story (Track 19.18) | ✓ | ✓ |
| Next Action chip (Track 19.18) | ✓ | ✓ |
| Executive Snapshot headline (Track 19.18) | ✓ | ✓ |

## PDF bilingual note

PDF reports render in the language stored on the case at submit time (translation-on-submit doctrine). PDFs are **not** dynamically re-translated — a case submitted in Spanish stays Spanish in every PDF; a case submitted in English stays English. This is by design and matches the certified doctrine.

## Verification

- Screenshot smoke of `/incidents/report` in EN mode: all 17 cards + English labels ✓
- Screenshot smoke of `/incidents/report` in ES mode: all 17 cards + Spanish labels (Lesión al Público, Incendio, Amenaza, Robo, Vandalismo, Seguridad del Sitio, Peligro Identificado, Otro) ✓
- Language toggle (`masci.lang` localStorage) round-trips cleanly.

## Excluded

- English-only pre-existing strings NOT touched by Track 19.18 remain in whatever state they were in before Track 19.18 opened. This track does not audit the entire i18n surface — a full sweep is a separate track.

## Verdict

🟢 **Every Track 19.18-introduced string is fully bilingual.**  
🟢 **Every Track 19.17-added incident branch is fully bilingual.**  
🟢 **The Case Story auto-composer uses `t()` on the template — Spanish and English both render properly.**
