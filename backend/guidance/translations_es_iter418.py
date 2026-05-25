"""iter418/419/420/421 · ES translations for Phase 20.1-23 articles.

Mirrors the EN articles shipped in this batch:
  - dls-breakdown-proof          (iter418 · Phase 20.1)
  - dls-operational-exceptions   (iter419 · Phase 21.0)
  - dls-shop-recovery            (iter420 · Phase 22.0)
  - dls-offline-continuity       (iter421 · Phase 23.0)

Field-accurate operational Spanish doctrine maintained.
"""
from __future__ import annotations

EXTRA_ES: dict[str, dict] = {
    "dls-breakdown-proof": {
        "title_es": "DLS · Prueba de Avería · Continuidad",
        "summary_es": "Por qué una foto opcional justo después de AVERÍA fortalece la verdad operacional — sin frenar al conductor.",
        "body_es": [
            {"type": "p", "text":
                "Después de que un conductor toca AVERÍA, la plataforma ofrece "
                "un mensaje opcional 'Agregar foto de avería?'. El conductor "
                "puede tomar una foto rápida o saltar — ambos son válidos "
                "operacionalmente. La foto, si se captura, se convierte en "
                "prueba operacional permanente pegada a la asignación."},
            {"type": "why", "text":
                "Las averías son momentos de alta confianza en la continuidad "
                "operacional. Una sola foto en el momento de la avería "
                "fortalece la continuidad río abajo para Taller (preparación "
                "del mecánico), PM (impacto en la producción) y gobernanza "
                "(verdad operacional). Opcional significa que los conductores "
                "nunca se sienten bloqueados por el software bajo estrés "
                "operacional."},
            {"type": "next", "items": [
                "La foto se adjunta como `foto de avería` a la asignación",
                "El Taller ve la prueba de avería en el flujo de recuperación",
                "Despacho ve prueba + avería en Atención Operacional",
                "El sub-estado de recuperación comienza automáticamente en 'reportado'",
            ]},
            {"type": "warn", "text":
                "Saltar siempre es válido. Sin foto, sin problema — el toque "
                "de AVERÍA solo ya es verdad operacional. Nunca retrase la "
                "respuesta en carretera por el software."},
        ],
    },
    "dls-operational-exceptions": {
        "title_es": "DLS · Continuidad de Excepciones Operacionales",
        "summary_es": "Cómo el caos operacional — cambios de tráiler, reasignaciones en vuelo, actualizaciones retrasadas — se mantiene narrado y continuo, no borrado.",
        "body_es": [
            {"type": "p", "text":
                "Los casos extremos NO son errores. Son eventos de continuidad "
                "operacional. Cambios de tráiler a mitad de acarreo, "
                "reasignaciones durante ESPERANDO, recuperaciones de "
                "asignaciones obsoletas, actualizaciones de ciclo retrasadas "
                "— cada uno se convierte en una narrativa en el registro de "
                "la asignación, no en una bandera, no en un código de error, "
                "no en un flujo de trabajo."},
            {"type": "bullets", "items": [
                "TRAILER_SWAP — el conductor cambió tráiler durante el acarreo",
                "REASSIGNED_DURING_WAITING — despacho cambió camión durante ESPERANDO",
                "STALE_ASSIGNMENT_RECOVERED — asignación quedó parada, luego recuperada",
                "DELAYED_LIFECYCLE_UPDATE — estado llegó tarde por señal",
                "ASSIGNMENT_REASSIGNED — continuidad genérica de reasignación",
            ]},
            {"type": "why", "text":
                "Las operaciones son caóticas. Pretender que no lo son, "
                "borrando eventos caóticos del registro, destruye la "
                "continuidad río abajo. Capturar casos extremos como eventos "
                "de continuidad narrados preserva la verdad operacional sin "
                "arrastrar las operaciones hacia motores de flujo de trabajo "
                "o cromo de automatización."},
            {"type": "next", "items": [
                "Despacho registra un evento de continuidad atado a la asignación",
                "PM, Taller y gobernanza leen la misma narrativa",
                "Futuros informes Día-N ven la historia operacional completa",
            ]},
            {"type": "tip", "text":
                "Mantenga las narrativas cortas y operacionales ('Tráiler T-"
                "12 cambiado por T-09 en planta A'). SIN señalar con el dedo, "
                "SIN culpa, SIN lenguaje de flujo de trabajo."},
        ],
    },
    "dls-shop-recovery": {
        "title_es": "DLS · Continuidad de Recuperación del Taller (Avería → Retorno-al-Servicio)",
        "summary_es": "Siete estados calmados de continuidad operacional para Taller — no es un ERP de órdenes de trabajo.",
        "body_es": [
            {"type": "p", "text":
                "Cuando un camión se avería, la asignación lleva DOS pistas "
                "de estado: el ciclo del DLS (AVERÍA) y un sub-estado "
                "separado de recuperación del Taller. El Taller avanza el "
                "arco de recuperación sin tocar el ciclo del acarreo — "
                "ambos se mantienen honestos, ambos continúan."},
            {"type": "bullets", "items": [
                "reportado — se establece automáticamente cuando un conductor toca AVERÍA",
                "reconocido — el Taller lo ha visto",
                "diagnosticando — un mecánico está en el camión",
                "esperando_repuestos — bloqueado por suministro",
                "reparación_activa — repuestos en mano · trabajo de reparación en curso",
                "prueba_operacional — verificación operacional post-reparación",
                "retornado_al_servicio — de vuelta disponible para despacho",
            ]},
            {"type": "why", "text":
                "El Taller existe para mantener la continuidad operacional, "
                "no la burocracia de mantenimiento. Siete estados calmados "
                "le dicen a cada consumidor río abajo dónde está este "
                "camión en su arco de recuperación sin catálogos de "
                "repuestos, códigos de mano de obra, órdenes de trabajo o "
                "cadenas de aprobación."},
            {"type": "next", "items": [
                "Despacho lee disponibilidad desde `retornado_al_servicio`",
                "PM ve continuidad de impacto en producción",
                "`esperando_repuestos` repetido en el mismo camión = patrón operacional",
                "El historial de recuperación es solo-agregar · verdad operacional preservada",
            ]},
            {"type": "warn", "text":
                "Esto NO es un sistema de órdenes de trabajo. Sin registro "
                "de mano de obra, sin catálogo de repuestos, sin cadenas de "
                "compra. Si esas necesidades surgen, pertenecen a un sistema "
                "diferente — no a la continuidad de recuperación del DLS."},
        ],
    },
    "dls-offline-continuity": {
        "title_es": "DLS · Continuidad sin Señal (En el Campo)",
        "summary_es": "Cómo la verdad operacional sobrevive a la mala señal — sincronización invisible cuando la señal regresa.",
        "body_es": [
            {"type": "p", "text":
                "Cuando un conductor toca INICIAR TURNO en una zona sin "
                "señal, la plataforma guarda silenciosamente la actualización "
                "en el dispositivo y la sincroniza cuando la señal regresa. "
                "La verdad operacional nunca desaparece — solo espera."},
            {"type": "why", "text":
                "La verdad operacional NUNCA debe desaparecer porque la "
                "señal falló. Los conductores en pozos, fondos de obras, o "
                "rutas remotas son operacionalmente reales y la plataforma "
                "no debe castigarlos por estar donde el trabajo sucede."},
            {"type": "next", "items": [
                "El dispositivo guarda hasta 3 actualizaciones pendientes",
                "Cuando la señal regresa, la sincronización es automática",
                "El indicador muestra 'Actualización esperando sincronizar' · luego desaparece",
                "Sin paneles · sin reintentos manuales · sin lenguaje técnico",
            ]},
            {"type": "tip", "text":
                "Si la sincronización tarda demasiado (10+ minutos), abrir "
                "la página manualmente forzará otra verificación de "
                "conectividad. La operación nunca se queda atrás más allá "
                "de lo que la señal permite."},
        ],
    },
}
