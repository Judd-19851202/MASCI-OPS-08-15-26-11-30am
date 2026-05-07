// Field Leadership form schemas — single source of truth that drives the
// generic <FieldLeadershipForm /> renderer. Adding a new form kind = adding
// a new entry here. Backend has its own copy of `kind` + meta in
// /app/backend/routes/field_leadership.py — keep the kind keys in sync.
//
// Field types:
//   text       — single-line input
//   textarea   — multi-line
//   select     — dropdown (options: array of {en, es})
//   date       — date picker
//   datetime   — datetime picker
//   time       — time picker
//   yesno      — radio yes/no
//   ratings    — list of items each rated on a scale (rating_options)
//   number     — numeric input
//
// Common options:
//   required  — boolean
//   visible_if — { field, equals } — show only when another field has value

import {
  AlertTriangle, MessageCircle, Clock, Award, Wrench, UserCheck,
  Users, TrendingUp, GraduationCap, FileText, ShieldCheck,
} from "lucide-react";

const RATING_OPTIONS = [
  { en: "Excellent", es: "Excelente" },
  { en: "Good", es: "Bueno" },
  { en: "Needs Improvement", es: "Necesita Mejorar" },
  { en: "Unsatisfactory", es: "Insatisfactorio" },
];

const PERF_RATING_OPTIONS = [
  { en: "Outstanding", es: "Sobresaliente" },
  ...RATING_OPTIONS,
];

export const FIELD_LEADERSHIP_FORMS = [
  {
    kind: "write_up",
    icon: AlertTriangle,
    accent: "red",
    title: { en: "Employee Write-Up", es: "Amonestación al Empleado" },
    desc: {
      en: "Document formal disciplinary or corrective action.",
      es: "Documente acción disciplinaria o correctiva formal.",
    },
    needs_signatures: true,
    allow_refusal: true,
    allows_photos: true,
    fields: [
      { name: "category", label: { en: "Category", es: "Categoría" }, type: "select", required: true,
        options: [
          { en: "Safety Violation", es: "Infracción de Seguridad" },
          { en: "Attendance", es: "Asistencia" },
          { en: "PPE Violation", es: "Infracción de EPP" },
          { en: "Equipment Abuse", es: "Abuso de Equipo" },
          { en: "Policy Violation", es: "Infracción de Política" },
          { en: "Conduct", es: "Conducta" },
          { en: "Production / Performance", es: "Producción / Desempeño" },
          { en: "Vehicle / Equipment Incident", es: "Incidente de Vehículo / Equipo" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "severity", label: { en: "Severity", es: "Severidad" }, type: "select", required: true,
        options: [
          { en: "Verbal Warning", es: "Advertencia Verbal" },
          { en: "Written Warning", es: "Advertencia Escrita" },
          { en: "Final Warning", es: "Advertencia Final" },
          { en: "Suspension Recommendation", es: "Recomendación de Suspensión" },
          { en: "Termination Recommendation", es: "Recomendación de Despido" },
        ] },
      { name: "description", label: { en: "Description of Observed Behavior / Facts", es: "Descripción del Comportamiento Observado / Hechos" }, type: "textarea", required: true, rows: 5 },
      { name: "policy_violated", label: { en: "Policy / Procedure Violated", es: "Política / Procedimiento Infringido" }, type: "text" },
      { name: "prior_warnings", label: { en: "Prior Coaching or Warnings", es: "Asesoramientos o Advertencias Previas" }, type: "textarea", rows: 3 },
      { name: "corrective_action", label: { en: "Corrective Action Required", es: "Acción Correctiva Requerida" }, type: "textarea", required: true, rows: 4 },
      { name: "follow_up_date", label: { en: "Follow-Up Date", es: "Fecha de Seguimiento" }, type: "date" },
      { name: "employee_statement", label: { en: "Employee Statement", es: "Declaración del Empleado" }, type: "textarea", rows: 4 },
    ],
  },
  {
    kind: "verbal_coaching",
    icon: MessageCircle,
    accent: "amber",
    title: { en: "Verbal Coaching", es: "Asesoramiento Verbal" },
    desc: {
      en: "Document a coaching conversation that is not a formal write-up.",
      es: "Documente una conversación de asesoramiento que no es una amonestación formal.",
    },
    needs_signatures: true,
    employee_signature_optional: true,
    fields: [
      { name: "topic", label: { en: "Coaching Topic", es: "Tema de Asesoramiento" }, type: "select", required: true,
        options: ["Safety", "Attendance", "Productivity", "Conduct", "Quality", "Equipment Care", "Communication", "Other"]
          .map(en => ({ en, es: { Safety: "Seguridad", Attendance: "Asistencia", Productivity: "Productividad", Conduct: "Conducta", Quality: "Calidad", "Equipment Care": "Cuidado del Equipo", Communication: "Comunicación", Other: "Otro" }[en] })) },
      { name: "issue_discussed", label: { en: "Issue Discussed", es: "Tema Tratado" }, type: "textarea", required: true, rows: 4 },
      { name: "expectations", label: { en: "Expectations Explained", es: "Expectativas Explicadas" }, type: "textarea", required: true, rows: 3 },
      { name: "employee_response", label: { en: "Employee Response", es: "Respuesta del Empleado" }, type: "textarea", rows: 3 },
      { name: "follow_up_needed", label: { en: "Follow-Up Needed?", es: "¿Necesita Seguimiento?" }, type: "yesno" },
      { name: "follow_up_date", label: { en: "Follow-Up Date", es: "Fecha de Seguimiento" }, type: "date", visible_if: { field: "follow_up_needed", equals: "yes" } },
    ],
  },
  {
    kind: "attendance",
    icon: Clock,
    accent: "orange",
    title: { en: "Attendance / Tardy", es: "Asistencia / Tardanza" },
    desc: {
      en: "Document attendance-related issues factually.",
      es: "Documente problemas de asistencia de manera objetiva.",
    },
    needs_signatures: true,
    allow_refusal: true,
    fields: [
      { name: "attendance_type", label: { en: "Issue Type", es: "Tipo de Problema" }, type: "select", required: true,
        options: [
          { en: "Late Arrival", es: "Llegada Tardía" },
          { en: "Left Early", es: "Salida Temprana" },
          { en: "No Call / No Show", es: "No Llamó / No Se Presentó" },
          { en: "Excessive Absences", es: "Ausencias Excesivas" },
          { en: "Pattern of Tardiness", es: "Patrón de Tardanza" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "scheduled_start", label: { en: "Scheduled Start Time", es: "Hora Programada de Inicio" }, type: "time" },
      { name: "actual_arrival", label: { en: "Actual Arrival Time", es: "Hora Real de Llegada" }, type: "time" },
      { name: "scheduled_end", label: { en: "Scheduled End Time", es: "Hora Programada de Salida" }, type: "time" },
      { name: "actual_departure", label: { en: "Actual Departure Time", es: "Hora Real de Salida" }, type: "time" },
      { name: "explanation", label: { en: "Employee Explanation", es: "Explicación del Empleado" }, type: "textarea", rows: 4 },
      { name: "prior_issues", label: { en: "Prior Attendance Issues?", es: "¿Problemas de Asistencia Previos?" }, type: "yesno" },
      { name: "corrective_step", label: { en: "Corrective Action / Next Step", es: "Acción Correctiva / Próximo Paso" }, type: "textarea", required: true, rows: 3 },
    ],
  },
  {
    kind: "recognition",
    icon: Award,
    accent: "emerald",
    title: { en: "Recognition / Reward", es: "Reconocimiento / Recompensa" },
    desc: {
      en: "Recognize outstanding work, safety leadership, or going above and beyond.",
      es: "Reconozca trabajo sobresaliente, liderazgo en seguridad o ir más allá.",
    },
    supervisor_signature_only: true,
    needs_signatures: true,
    allows_photos: true,
    fields: [
      { name: "category", label: { en: "Recognition Category", es: "Categoría de Reconocimiento" }, type: "select", required: true,
        options: [
          { en: "Safety Leadership", es: "Liderazgo en Seguridad" },
          { en: "Going Above & Beyond", es: "Ir Más Allá" },
          { en: "Teamwork", es: "Trabajo en Equipo" },
          { en: "Production Excellence", es: "Excelencia en Producción" },
          { en: "Quality Workmanship", es: "Calidad de Mano de Obra" },
          { en: "Problem Solving", es: "Resolución de Problemas" },
          { en: "Helping Another Crew", es: "Ayudar a Otra Cuadrilla" },
          { en: "Equipment Care", es: "Cuidado del Equipo" },
          { en: "Leadership", es: "Liderazgo" },
          { en: "Customer / Owner Recognition", es: "Reconocimiento del Cliente / Propietario" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "what_they_did", label: { en: "What the Employee Did", es: "Lo Que Hizo el Empleado" }, type: "textarea", required: true, rows: 5 },
      { name: "impact", label: { en: "Impact on Job / Company / Crew", es: "Impacto en Obra / Empresa / Cuadrilla" }, type: "textarea", required: true, rows: 4 },
      { name: "recommended_reward", label: { en: "Recommended Reward", es: "Recompensa Recomendada" }, type: "select",
        options: [
          { en: "Verbal Recognition", es: "Reconocimiento Verbal" },
          { en: "Written Recognition", es: "Reconocimiento Escrito" },
          { en: "Gift Card", es: "Tarjeta de Regalo" },
          { en: "Bonus Consideration", es: "Consideración de Bono" },
          { en: "Employee Spotlight", es: "Empleado Destacado" },
          { en: "Promotion Consideration", es: "Consideración de Ascenso" },
          { en: "Other", es: "Otro" },
        ] },
    ],
  },
  {
    kind: "equipment_checkout",
    icon: Wrench,
    accent: "blue",
    title: { en: "Equipment Checkout & Accountability", es: "Asignación y Responsabilidad de Equipo" },
    desc: {
      en: "Track company tools/equipment issued to employees with sign-out and return condition.",
      es: "Registre herramientas/equipo de la empresa entregados a empleados con firma y condición de devolución.",
    },
    needs_signatures: true,
    allows_photos: true,
    photos_required_when: { field: "condition", equals_any: ["Fair", "Damaged"] },
    acknowledgement: {
      en: "Employee acknowledges receipt of company property and agrees to use, maintain, and return the equipment in accordance with company policy and applicable law.",
      es: "El empleado acusa recibo de la propiedad de la empresa y acepta usar, mantener y devolver el equipo conforme a las políticas de la empresa y la ley aplicable.",
    },
    fields: [
      { name: "equipment_type", label: { en: "Equipment / Tool Type", es: "Tipo de Equipo / Herramienta" }, type: "text", required: true },
      { name: "asset_id", label: { en: "Asset ID / Serial Number", es: "ID de Activo / Número de Serie" }, type: "text" },
      { name: "condition", label: { en: "Condition at Checkout", es: "Condición al Entregar" }, type: "select", required: true,
        options: [
          { en: "New", es: "Nuevo" },
          { en: "Good", es: "Bueno" },
          { en: "Fair", es: "Aceptable" },
          { en: "Damaged", es: "Dañado" },
        ] },
      { name: "condition_description", label: { en: "Description of Condition", es: "Descripción de la Condición" }, type: "textarea", rows: 3 },
      { name: "date_issued", label: { en: "Date Issued", es: "Fecha de Entrega" }, type: "date", required: true },
      { name: "expected_return", label: { en: "Expected Return Date", es: "Fecha Esperada de Devolución" }, type: "date" },
    ],
  },
  {
    kind: "new_employee_eval",
    icon: UserCheck,
    accent: "purple",
    title: { en: "New Employee Evaluation", es: "Evaluación de Nuevo Empleado" },
    desc: {
      en: "30 / 60 / 90-day evaluation for new employees.",
      es: "Evaluación de 30 / 60 / 90 días para nuevos empleados.",
    },
    needs_signatures: true,
    allow_refusal: true,
    fields: [
      { name: "hire_date", label: { en: "Hire Date", es: "Fecha de Contratación" }, type: "date", required: true },
      { name: "evaluation_type", label: { en: "Evaluation Type", es: "Tipo de Evaluación" }, type: "select", required: true,
        options: [
          { en: "30 Day", es: "30 Días" },
          { en: "60 Day", es: "60 Días" },
          { en: "90 Day", es: "90 Días" },
        ] },
      { name: "ratings", label: { en: "Ratings", es: "Calificaciones" }, type: "ratings",
        items: [
          { key: "safety_awareness", en: "Safety Awareness", es: "Conciencia de Seguridad" },
          { key: "attendance", en: "Attendance / Reliability", es: "Asistencia / Confiabilidad" },
          { key: "attitude", en: "Attitude", es: "Actitud" },
          { key: "teamwork", en: "Teamwork", es: "Trabajo en Equipo" },
          { key: "work_quality", en: "Work Quality", es: "Calidad del Trabajo" },
          { key: "productivity", en: "Productivity", es: "Productividad" },
          { key: "communication", en: "Communication", es: "Comunicación" },
          { key: "equipment_care", en: "Equipment Care", es: "Cuidado del Equipo" },
          { key: "follow_direction", en: "Ability to Follow Direction", es: "Capacidad de Seguir Instrucciones" },
          { key: "leadership_potential", en: "Leadership Potential", es: "Potencial de Liderazgo" },
        ],
        rating_options: RATING_OPTIONS },
      { name: "strengths", label: { en: "Strengths", es: "Fortalezas" }, type: "textarea", rows: 4 },
      { name: "areas_for_improvement", label: { en: "Areas Needing Improvement", es: "Áreas que Necesitan Mejorar" }, type: "textarea", rows: 4 },
      { name: "recommended_action", label: { en: "Recommended Action", es: "Acción Recomendada" }, type: "select", required: true,
        options: [
          { en: "Continue Employment", es: "Continuar Empleo" },
          { en: "Additional Training", es: "Capacitación Adicional" },
          { en: "Extend Evaluation Period", es: "Extender Período de Evaluación" },
          { en: "Not Recommended", es: "No Recomendado" },
        ] },
      { name: "employee_comments", label: { en: "Employee Comments", es: "Comentarios del Empleado" }, type: "textarea", rows: 3 },
    ],
  },
  {
    kind: "crew_eval",
    icon: Users,
    accent: "lime",
    title: { en: "Crew Evaluation", es: "Evaluación de Cuadrilla" },
    desc: {
      en: "Evaluate crew performance and field leadership observations.",
      es: "Evalúe el desempeño de la cuadrilla y observaciones de liderazgo de campo.",
    },
    needs_signatures: true,
    supervisor_signature_only: true,
    employee_field_label: { en: "Crew / Foreman Name", es: "Nombre de Cuadrilla / Capataz" },
    fields: [
      { name: "work_performed", label: { en: "Work Performed", es: "Trabajo Realizado" }, type: "textarea", required: true, rows: 3 },
      { name: "ratings", label: { en: "Ratings", es: "Calificaciones" }, type: "ratings",
        items: [
          { key: "safety_compliance", en: "Safety Compliance", es: "Cumplimiento de Seguridad" },
          { key: "production", en: "Production", es: "Producción" },
          { key: "quality", en: "Quality", es: "Calidad" },
          { key: "organization", en: "Organization", es: "Organización" },
          { key: "housekeeping", en: "Housekeeping", es: "Orden y Limpieza" },
          { key: "equipment_care", en: "Equipment Care", es: "Cuidado del Equipo" },
          { key: "teamwork", en: "Teamwork", es: "Trabajo en Equipo" },
          { key: "communication", en: "Communication", es: "Comunicación" },
          { key: "schedule_awareness", en: "Schedule Awareness", es: "Conciencia del Cronograma" },
        ],
        rating_options: RATING_OPTIONS },
      { name: "overall_rating", label: { en: "Overall Performance Rating", es: "Calificación General" }, type: "select", required: true,
        options: PERF_RATING_OPTIONS },
      { name: "issues_observed", label: { en: "Issues Observed", es: "Problemas Observados" }, type: "textarea", rows: 3 },
      { name: "positive_observations", label: { en: "Positive Observations", es: "Observaciones Positivas" }, type: "textarea", rows: 3 },
      { name: "corrective_actions", label: { en: "Corrective Actions Needed", es: "Acciones Correctivas Necesarias" }, type: "textarea", rows: 3 },
      { name: "follow_up_required", label: { en: "Follow-Up Required?", es: "¿Necesita Seguimiento?" }, type: "yesno" },
    ],
  },
  {
    kind: "promotion_recommendation",
    icon: TrendingUp,
    accent: "indigo",
    title: { en: "Promotion Recommendation", es: "Recomendación de Ascenso" },
    desc: {
      en: "Recommend an employee for promotion, raise, or leadership development.",
      es: "Recomiende un empleado para ascenso, aumento o desarrollo de liderazgo.",
    },
    needs_signatures: true,
    supervisor_signature_only: true,
    fields: [
      { name: "current_position", label: { en: "Current Position", es: "Puesto Actual" }, type: "text", required: true },
      { name: "recommended_position", label: { en: "Recommended Position / Opportunity", es: "Puesto / Oportunidad Recomendada" }, type: "text", required: true },
      { name: "reason", label: { en: "Reason for Recommendation", es: "Motivo de la Recomendación" }, type: "textarea", required: true, rows: 4 },
      { name: "strengths", label: { en: "Strengths Observed", es: "Fortalezas Observadas" }, type: "textarea", rows: 3 },
      { name: "leadership_qualities", label: { en: "Leadership Qualities", es: "Cualidades de Liderazgo" }, type: "textarea", rows: 3 },
      { name: "safety_record", label: { en: "Safety Record / Comments", es: "Historial de Seguridad / Comentarios" }, type: "textarea", rows: 3 },
      { name: "reliability", label: { en: "Reliability / Attendance", es: "Confiabilidad / Asistencia" }, type: "textarea", rows: 2 },
      { name: "skill_level", label: { en: "Skill Level", es: "Nivel de Habilidad" }, type: "textarea", rows: 2 },
      { name: "certifications", label: { en: "Certifications / Training Completed", es: "Certificaciones / Capacitación" }, type: "textarea", rows: 2 },
      { name: "next_step", label: { en: "Recommended Next Step", es: "Próximo Paso Recomendado" }, type: "select", required: true,
        options: [
          { en: "Promotion Review", es: "Revisión de Ascenso" },
          { en: "Raise Review", es: "Revisión de Aumento" },
          { en: "Leadership Development", es: "Desarrollo de Liderazgo" },
          { en: "Additional Training", es: "Capacitación Adicional" },
          { en: "Future Consideration", es: "Consideración Futura" },
        ] },
    ],
  },
  {
    kind: "training_deficiency",
    icon: GraduationCap,
    accent: "yellow",
    title: { en: "Training Deficiency / Retraining", es: "Deficiencia de Capacitación / Reentrenamiento" },
    desc: {
      en: "Document an observed training need and assign corrective retraining.",
      es: "Documente una necesidad de capacitación observada y asigne reentrenamiento.",
    },
    needs_signatures: true,
    allow_refusal: true,
    fields: [
      { name: "deficiency_category", label: { en: "Deficiency Category", es: "Categoría de Deficiencia" }, type: "select", required: true,
        options: [
          { en: "Safety", es: "Seguridad" },
          { en: "Equipment Operation", es: "Operación de Equipo" },
          { en: "PPE", es: "EPP" },
          { en: "Excavation / Trenching", es: "Excavación / Zanjas" },
          { en: "Traffic Control", es: "Control de Tráfico" },
          { en: "Tools / Equipment", es: "Herramientas / Equipo" },
          { en: "Quality", es: "Calidad" },
          { en: "Procedure", es: "Procedimiento" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "deficiency_description", label: { en: "Description of Observed Deficiency", es: "Descripción de la Deficiencia Observada" }, type: "textarea", required: true, rows: 4 },
      { name: "potential_risk", label: { en: "Potential Risk", es: "Riesgo Potencial" }, type: "textarea", rows: 3 },
      { name: "required_retraining", label: { en: "Required Retraining", es: "Reentrenamiento Requerido" }, type: "textarea", required: true, rows: 3 },
      { name: "training_assigned_to", label: { en: "Training Assigned To", es: "Capacitación Asignada A" }, type: "select",
        options: [
          { en: "Safety Department", es: "Departamento de Seguridad" },
          { en: "Supervisor", es: "Supervisor" },
          { en: "PM", es: "PM" },
          { en: "External Trainer", es: "Capacitador Externo" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "due_date", label: { en: "Due Date", es: "Fecha Límite" }, type: "date" },
      { name: "completion_status", label: { en: "Completion Status", es: "Estado de Cumplimiento" }, type: "select",
        options: [
          { en: "Pending", es: "Pendiente" },
          { en: "Completed", es: "Completado" },
        ] },
    ],
  },
  {
    kind: "supervisor_notes",
    icon: FileText,
    accent: "slate",
    title: { en: "Supervisor Notes Log", es: "Registro de Notas del Supervisor" },
    desc: {
      en: "Internal leadership documentation log.",
      es: "Registro interno de documentación de liderazgo.",
    },
    needs_signatures: false,
    allows_photos: true,
    fields: [
      { name: "note_category", label: { en: "Note Category", es: "Categoría de Nota" }, type: "select", required: true,
        options: [
          { en: "Manpower", es: "Mano de Obra" },
          { en: "Performance", es: "Desempeño" },
          { en: "Crew Conflict", es: "Conflicto de Cuadrilla" },
          { en: "Production Concern", es: "Preocupación de Producción" },
          { en: "Safety Concern", es: "Preocupación de Seguridad" },
          { en: "Subcontractor Issue", es: "Problema con Subcontratista" },
          { en: "Leadership Observation", es: "Observación de Liderazgo" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "detailed_note", label: { en: "Detailed Note", es: "Nota Detallada" }, type: "textarea", required: true, rows: 6 },
      { name: "follow_up_required", label: { en: "Follow-Up Required?", es: "¿Necesita Seguimiento?" }, type: "yesno" },
      { name: "follow_up_date", label: { en: "Follow-Up Date", es: "Fecha de Seguimiento" }, type: "date", visible_if: { field: "follow_up_required", equals: "yes" } },
    ],
  },
];

// Existing Safety Equipment Issuance form — links out to /safety/forms/login.
// Listed in the Field Leadership hub but not part of the schema-driven flow.
export const SAFETY_EQUIPMENT_ISSUANCE_LINK = {
  kind: "safety_equipment_issuance",
  icon: ShieldCheck,
  accent: "red",
  external: true,
  to: "/safety/forms/login",
  title: { en: "Safety Equipment Issuance", es: "Entrega de Equipo de Seguridad" },
  desc: {
    en: "Existing PPE and safety-equipment accountability form. Submitted records are shared with the Safety section.",
    es: "Formulario existente de responsabilidad de EPP y equipo de seguridad. Los registros se comparten con la sección de Seguridad.",
  },
};

export function getFormByKind(kind) {
  return FIELD_LEADERSHIP_FORMS.find((f) => f.kind === kind) || null;
}

export function getFormTitle(kind, lang = "en") {
  const f = getFormByKind(kind);
  if (!f) return kind;
  return f.title[lang] || f.title.en;
}
