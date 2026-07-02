# FINAL Bilingual Certification

**Verdict:** 🟢 **PASS** — English and Spanish fully synchronized on the Incident Engine surface.

## Doctrine

- Nothing may exist only in English.
- Nothing may exist only in Spanish.
- User types in native language.
- Server stores English where the doctrine dictates (translation-on-submit).
- PDFs render in the case's submitted language (immutable per case).

## Track 19.18-scope EN/ES parity

| Surface | EN | ES | Verified |
|---|:-:|:-:|:-:|
| Incident type picker (17 cards) | ✅ | ✅ | Screenshot both modes · Track 19.17 test |
| Incident branch flows (17 flows) | ✅ | ✅ | Track 19.17 test |
| Field labels across all steps | ✅ | ✅ | Track 19.17 test |
| Guardrail step labels | ✅ | ✅ | Track 19.17 |
| Header layout | ✅ | ✅ | Track 19.16 batch 1 |
| ProgressRail | ✅ | ✅ | Track 19.16 |
| Submit gate messages | ✅ | ✅ | Track 19.16 |
| HelpDrawer content | ✅ | ✅ | Track 19.16 |
| PresenceGate | ✅ | ✅ | Track 19.16 |
| Case Story paragraph (Track 19.18) | ✅ | ✅ | 10 new EN→ES entries |
| Next Action chip (Track 19.18) | ✅ | ✅ | 10 new EN→ES entries |
| Executive Snapshot headline (Track 19.18) | ✅ | ✅ | 10 new EN→ES entries |

## Track 19.18 new keys (10 additions)

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

## Verification method

- Screenshot smoke of `/incidents/report` in EN + ES modes
- All 17 cards render in both languages (English labels + Spanish equivalents: Lesión al Público, Incendio, Amenaza, Robo, Vandalismo, Seguridad del Sitio, Peligro Identificado, Otro)
- Testing agent independently confirms: "EN/ES header toggle works both ways (Spanish content confirmed after ES click)"
- Language persists via `localStorage.masci.lang`

## Session modal + toasts

- Session modal follows current language (verified in Track 19.16)
- Toast notifications translate (verified in Track 19.16)
- No English leak in Spanish mode · No Spanish leak in English mode

## PDF bilingual behavior

Cases render in their submitted language. A case submitted in Spanish stays Spanish in every generated PDF; a case in English stays English. This matches the certified translation-on-submit doctrine (immutable per case).

## Excluded from Track 19.18 scope

- Full app-wide i18n audit (~7,500 line dictionary with ~692 pre-existing duplicate keys). Track 19.18 added its own 10 keys cleanly; the pre-existing dedup pass is a separate cleanup track that would balloon this diff.

## Verdict

🟢 **Bilingual parity locked. Zero regression from Track 19.17. Track 19.18 additions all bilingual.**
