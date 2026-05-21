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
  Users, TrendingUp, GraduationCap, FileText, ShieldCheck, Undo2,
  UserX, CalendarOff,
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
      en: "Track company tools/equipment issued to employees with sign-out and replacement-value accountability.",
      es: "Registre herramientas/equipo de la empresa entregados con firma y valor de reemplazo.",
    },
    needs_signatures: true,
    allow_refusal: true,
    allows_photos: false, // Photos live on each line, not the form root
    custom_renderer: "equipment_lines",
    acknowledgement: {
      en: [
        "I acknowledge receipt of the company equipment, tools, and/or property listed above. I understand that this equipment remains the property of MASCI General Contractors Inc. and is issued to me for company business purposes only.",
        "I agree to use, secure, care for, maintain, and return all issued equipment in accordance with company policy, manufacturer instructions, and applicable safety requirements.",
        "I understand that loss, theft, damage, misuse, neglect, abuse, unauthorized use, or failure to return company equipment may result in disciplinary action and may result in financial responsibility for repair or replacement costs, only to the extent permitted by applicable federal law, Florida law, and company policy. Any payroll deduction or reimbursement will be handled only where legally permitted and with any required authorization.",
        "My signature acknowledges receipt of the listed equipment and this responsibility notice.",
      ],
      es: [
        "Reconozco haber recibido el equipo, herramientas y/o propiedad de la empresa que se enumeran arriba. Entiendo que este equipo sigue siendo propiedad de MASCI General Contractors Inc. y se me entrega únicamente para fines comerciales de la empresa.",
        "Acepto usar, asegurar, cuidar, mantener y devolver todo el equipo entregado conforme a la política de la empresa, las instrucciones del fabricante y los requisitos de seguridad aplicables.",
        "Entiendo que la pérdida, robo, daño, uso indebido, negligencia, abuso, uso no autorizado o falta de devolución del equipo de la empresa puede resultar en acción disciplinaria y puede generar responsabilidad económica por costos de reparación o reemplazo, únicamente en la medida permitida por la ley federal aplicable, la ley de Florida y la política de la empresa. Cualquier deducción de nómina o reembolso se realizará solo donde sea legalmente permitido y con cualquier autorización requerida.",
        "Mi firma reconoce la recepción del equipo enumerado y este aviso de responsabilidad.",
      ],
    },
    fields: [],
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
    // iter70 — replaces the old "Supervisor Notes Log" tile. This is the
    // formalized HR/legal Employee Termination workflow. Same schema-
    // driven renderer; uses a new `checkboxes` field type for property
    // returned, a new `equipment_lookup` custom block for outstanding
    // checkouts auto-link, and supports BOTH "refused to sign" AND
    // "employee not present" signature states.
    kind: "employee_termination",
    icon: UserX,
    accent: "red",
    title: {
      en: "Employee Termination",
      es: "Terminación de Empleo",
    },
    desc: {
      en: "Document employee separation, resignation, policy violations, or termination actions.",
      es: "Documente la separación, renuncia, infracciones de política o acciones de terminación.",
    },
    needs_signatures: true,
    allow_refusal: true,
    allows_photos: true,
    // The form has its own job + employee pickers (same as every other
    // FL form) — those cover spec fields 1, 2, 3, 4, 5, 6, and the
    // supervisor signature in 16. The schema-driven fields below cover
    // spec fields 7–15 + the rehire/law-enforcement metadata.
    fields: [
      // 7 — Type of Separation (required dropdown w/ "Other" gate)
      { name: "separation_type", label: { en: "Type of Separation", es: "Tipo de Separación" }, type: "select", required: true,
        options: [
          { en: "Safety Violation", es: "Infracción de Seguridad" },
          { en: "Company Policy Violation", es: "Infracción de Política" },
          { en: "Attendance Issues", es: "Problemas de Asistencia" },
          { en: "Performance Issues", es: "Problemas de Desempeño" },
          { en: "Insubordination", es: "Insubordinación" },
          { en: "Drug/Alcohol Violation", es: "Infracción de Drogas/Alcohol" },
          { en: "Equipment Abuse/Damage", es: "Abuso/Daño de Equipo" },
          { en: "Workplace Violence/Threats", es: "Violencia/Amenazas Laborales" },
          { en: "Reduction in Workforce", es: "Reducción de Personal" },
          { en: "End of Project", es: "Fin de Proyecto" },
          { en: "Self Termination (Quit)", es: "Renuncia Voluntaria" },
          { en: "Job Abandonment", es: "Abandono de Trabajo" },
          { en: "Failure to Meet Training Requirements", es: "Incumplimiento de Capacitación" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "separation_type_other", label: { en: "If Other, please explain", es: "Si seleccionó Otro, explique" },
        type: "textarea", rows: 2, required: true, visible_if: { field: "separation_type", equals: "Other" } },

      // 8 — Detailed Explanation (required, long text)
      { name: "detailed_explanation", label: { en: "Detailed Explanation / Incident Description",
                                               es: "Explicación Detallada / Descripción del Incidente" },
        type: "textarea", rows: 7, required: true, min_length: 40,
        help: {
          en: "Required minimum 40 characters. Explain what occurred, dates/timeline, witnesses if applicable, previous warnings, policy/safety concerns, and final action taken.",
          es: "Mínimo 40 caracteres. Explique qué ocurrió, fechas/cronología, testigos si aplica, advertencias previas, preocupaciones de política/seguridad y la acción final tomada.",
        } },

      // 9 — Prior Disciplinary Actions
      { name: "prior_disciplinary_actions", label: { en: "Prior Disciplinary Actions", es: "Acciones Disciplinarias Previas" },
        type: "select", required: true,
        options: [
          { en: "None", es: "Ninguna" },
          { en: "Verbal Coaching", es: "Asesoramiento Verbal" },
          { en: "Written Warning", es: "Advertencia Escrita" },
          { en: "Final Warning", es: "Advertencia Final" },
          { en: "Multiple Previous Incidents", es: "Múltiples Incidentes Previos" },
        ] },

      // 10 — Property Returned (checkbox group — NEW field type)
      { name: "property_returned", label: { en: "Company Property Returned", es: "Propiedad de la Empresa Devuelta" },
        type: "checkboxes",
        options: [
          { key: "hard_hat", en: "Hard Hat", es: "Casco" },
          { key: "safety_vest", en: "Safety Vest", es: "Chaleco de Seguridad" },
          { key: "radio", en: "Radio", es: "Radio" },
          { key: "keys", en: "Keys", es: "Llaves" },
          { key: "fuel_card", en: "Fuel Card", es: "Tarjeta de Combustible" },
          { key: "tablet_ipad", en: "Tablet / iPad", es: "Tableta / iPad" },
          { key: "tools_equipment", en: "Tools / Equipment", es: "Herramientas / Equipo" },
          { key: "company_vehicle", en: "Company Vehicle", es: "Vehículo de la Empresa" },
          { key: "badge_access_card", en: "Badge / Access Card", es: "Insignia / Tarjeta de Acceso" },
          { key: "other", en: "Other", es: "Otro" },
        ] },
      { name: "property_returned_other", label: { en: "Other Property Description", es: "Descripción de Otra Propiedad" },
        type: "text", visible_if: { field: "property_returned__other", equals: true } },

      // 11 — Outstanding Equipment Assigned (custom auto-lookup block).
      // The renderer reads the employee name picker and lists every
      // un-returned line from the equipment_checkout collection.
      // Supervisor reviews + confirms each chip.
      { name: "outstanding_equipment_acknowledged", type: "outstanding_equipment_lookup",
        label: { en: "Outstanding Equipment Assigned", es: "Equipo Pendiente Asignado" }, required: false },

      // 12 — Eligible for Rehire
      { name: "rehire_eligibility", label: { en: "Eligible for Rehire?", es: "¿Elegible para Recontratación?" },
        type: "select", required: true,
        options: [
          { en: "Yes", es: "Sí" },
          { en: "No", es: "No" },
          { en: "Conditional", es: "Condicional" },
        ] },
      { name: "rehire_conditions", label: { en: "Rehire Conditions", es: "Condiciones de Recontratación" },
        type: "textarea", rows: 2, required: true, visible_if: { field: "rehire_eligibility", equals: "Conditional" } },

      // 13 — Law Enforcement / Incident Report Involved
      { name: "law_enforcement_involved", label: { en: "Law Enforcement / Incident Report Involved?",
                                                   es: "¿Hubo Involucramiento de las Autoridades / Reporte de Incidente?" },
        type: "select", required: true,
        options: [
          { en: "No", es: "No" },
          { en: "Yes", es: "Sí" },
        ] },
      { name: "law_enforcement_details", label: { en: "Law Enforcement / Report Details",
                                                  es: "Detalles del Reporte / Autoridades" },
        type: "textarea", rows: 3, required: true, visible_if: { field: "law_enforcement_involved", equals: "Yes" } },

      // 14 — Witnesses (optional, one per line)
      { name: "witnesses_present", label: { en: "Witnesses Present (one per line)",
                                            es: "Testigos Presentes (uno por línea)" },
        type: "textarea", rows: 3 },
    ],
  },
  {
    kind: "equipment_return",
    icon: Undo2,
    accent: "blue",
    title: { en: "Equipment Return & Reconciliation", es: "Devolución y Reconciliación de Equipo" },
    desc: {
      en: "Close the loop on issued equipment — scan or look up by serial/asset ID, document return condition with photos, auto-flag damage or loss against the original replacement value.",
      es: "Cierre el ciclo del equipo entregado — busque por serie/ID de activo, documente la condición de devolución con fotos, marque daños o pérdidas contra el valor de reemplazo original.",
    },
    needs_signatures: true,
    allow_refusal: true,
    allows_photos: false,
    custom_renderer: "equipment_return_lines",
    acknowledgement: {
      en: [
        "I acknowledge that the equipment listed above has been returned to MASCI General Contractors Inc. in the condition documented on this form, with photographs and notes attached as evidence.",
        "I understand that any equipment listed as DAMAGED, MISSING, or LOST may result in financial responsibility for repair or replacement costs, only to the extent permitted by applicable federal law, Florida law, and company policy. Any payroll deduction or reimbursement will be handled only where legally permitted and with any required authorization.",
        "My signature confirms the return condition recorded above is accurate to the best of my knowledge.",
      ],
      es: [
        "Reconozco que el equipo enumerado arriba ha sido devuelto a MASCI General Contractors Inc. en la condición documentada en este formulario, con fotografías y notas adjuntas como evidencia.",
        "Entiendo que cualquier equipo registrado como DAÑADO, FALTANTE o PERDIDO puede generar responsabilidad económica por costos de reparación o reemplazo, únicamente en la medida permitida por la ley federal aplicable, la ley de Florida y la política de la empresa. Cualquier deducción de nómina o reembolso se realizará solo donde sea legalmente permitido y con cualquier autorización requerida.",
        "Mi firma confirma que la condición de devolución registrada arriba es precisa al mejor de mi conocimiento.",
      ],
    },
    fields: [],
  },
  // iter101 — Time Off Request: supervisor pre-approves on submit;
  // HR reviews via the HR Portal "Time Off" dashboard. Public-link
  // variant available so HR can invite office staff without logins.
  {
    kind: "time_off_request",
    icon: CalendarOff,
    accent: "cyan",
    title: { en: "Time Off Request", es: "Solicitud de Tiempo Libre" },
    desc: {
      en: "Request vacation, sick, medical, or family-emergency leave on behalf of a crew member. HR auto-cc on submit; HR approves/denies from the HR Portal.",
      es: "Solicite vacaciones, enfermedad, médico o emergencia familiar para un miembro de la cuadrilla. RRHH se entera al instante; RRHH aprueba/niega desde el Portal de RRHH.",
    },
    needs_signatures: true,
    allow_refusal: false,
    allows_photos: false,
    employee_signature_optional: true,
    fields: [
      { name: "reason", label: { en: "Reason", es: "Motivo" }, type: "select", required: true,
        options: [
          { en: "Vacation", es: "Vacaciones" },
          { en: "Sick Leave", es: "Licencia por Enfermedad" },
          { en: "Medical Appointment", es: "Cita Médica" },
          { en: "Family Emergency", es: "Emergencia Familiar" },
          { en: "Bereavement", es: "Duelo" },
          { en: "Jury Duty", es: "Servicio de Jurado" },
          { en: "Military Leave", es: "Servicio Militar" },
          { en: "Personal", es: "Personal" },
          { en: "Other", es: "Otro" },
        ] },
      { name: "reason_other", label: { en: "If Other, please explain", es: "Si seleccionó Otro, explique" },
        type: "text", required: true, visible_if: { field: "reason", equals: "Other" } },
      { name: "pay_type", label: { en: "Pay Type", es: "Tipo de Pago" }, type: "select", required: true,
        options: [
          { en: "Paid", es: "Pagado" },
          { en: "Unpaid", es: "Sin Paga" },
        ] },
      { name: "start_date", label: { en: "Start Date", es: "Fecha de Inicio" }, type: "date", required: true },
      { name: "end_date", label: { en: "End Date", es: "Fecha de Fin" }, type: "date", required: true },
      { name: "half_day_start", label: { en: "Half day on start date?", es: "¿Medio día el día de inicio?" }, type: "yesno" },
      { name: "half_day_end", label: { en: "Half day on end date?", es: "¿Medio día el día final?" }, type: "yesno" },
      { name: "total_days", label: { en: "Total Days Requested", es: "Total de Días Solicitados" }, type: "number", required: true,
        help: { en: "Auto-calc from dates above; override if needed.", es: "Auto-calculado de las fechas; ajuste si necesario." } },
      { name: "return_to_work_date", label: { en: "Return to Work Date", es: "Fecha de Retorno al Trabajo" }, type: "date" },
      { name: "contact_phone", label: { en: "Contact Phone During Leave", es: "Teléfono Durante la Ausencia" }, type: "text" },
      { name: "coverage_plan", label: { en: "Coverage Plan / Who's Covering", es: "Plan de Cobertura / Quién Cubre" }, type: "textarea", rows: 3 },
      { name: "notes", label: { en: "Notes / Additional Detail", es: "Notas / Detalle Adicional" }, type: "textarea", rows: 4 },
    ],
  },
];

// Existing Safety Equipment Issuance form — links out to /safety/forms/login.
// Listed in the Field Leadership hub but not part of the schema-driven flow.
// iter322 — append `?from=leadership` so the Safety Forms gate + hub
// render the portal-continuity banner ("← Back to Field Leadership").
export const SAFETY_EQUIPMENT_ISSUANCE_LINK = {
  kind: "safety_equipment_issuance",
  icon: ShieldCheck,
  accent: "red",
  external: false,
  internalRoute: true,
  to: "/safety/forms/login?from=leadership",
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
