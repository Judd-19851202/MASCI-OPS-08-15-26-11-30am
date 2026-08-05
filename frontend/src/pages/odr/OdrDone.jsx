import React from "react";
import { useParams } from "react-router-dom";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";
import { getOdr } from "@/lib/odrApi";

export default function OdrDone() {
  const { id } = useParams();
  const [odr, setOdr] = React.useState(null);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    let live = true;
    getOdr(id)
      .then((data) => { if (live) setOdr(data); })
      .catch((error) => { if (live) setErr(error.message || "Could not load submitted record"); });
    return () => { live = false; };
  }, [id]);

  const confirmation = React.useMemo(() => buildSubmissionConfirmation({
    workflowKey: "odr",
    documentNumber: odr?.doc_id || id || "",
    submittedAt: odr?.submitted_at || odr?.created_at || new Date().toISOString(),
    submittedBy: odr?.submitted_by_name || odr?.foreman_name || odr?.created_by_name || "",
    project: odr?.project_name || odr?.project_number || "",
    contextItems: odr?.equipment_name ? [{ label: "Equipment", value: odr.equipment_name }] : [],
    expectedProcessingStatus: err ? "Filed record lookup needs follow-up" : "Filed and pending PM review",
    note: err || "",
    openRecord: { label: "Open Submitted Record", to: `/odr/${encodeURIComponent(id)}` },
    returnToPortal: { label: "Return to Portal", to: "/odr" },
    startAnother: { label: "Start Another", to: "/odr/new" },
  }), [err, id, odr]);

  return <SubmissionConfirmation confirmation={confirmation} />;
}