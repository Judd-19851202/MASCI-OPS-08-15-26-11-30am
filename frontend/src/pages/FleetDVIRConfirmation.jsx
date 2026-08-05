import React from "react";
import { useLocation, useParams } from "react-router-dom";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";

export default function FleetDVIRConfirmation() {
  const { id } = useParams();
  const { state } = useLocation();
  const s = React.useMemo(() => state || {}, [state]);
  const orphan = !s.result;

  const confirmation = React.useMemo(() => {
    if (orphan) {
      return buildSubmissionConfirmation({
        workflowKey: "dvir",
        documentNumber: s.documentNumber || id || "",
        successStatus: "Submitted Record Not Loaded",
        description: "This link opened without the live filing details from the submit screen.",
        whatHappensNext: [
          "Open this confirmation from a fresh DVIR submission to see the full filed details.",
        ],
        followUpRequired: "File a new DVIR if you need a fresh confirmation from this device.",
        expectedProcessingStatus: "Filed record lookup not available from this direct link",
        returnToPortal: { label: "Return to Portal", to: "/field" },
        startAnother: { label: "Start Another", to: "/fleet/dvir/new" },
      });
    }

    const hasDefects = Number(s.defectCount || 0) > 0;
    const isOutOfService = Boolean(s.outOfService);
    return buildSubmissionConfirmation({
      workflowKey: "dvir",
      documentNumber: s.documentNumber || s.result?.doc_id || id || "",
      submittedAt: new Date().toISOString(),
      submittedBy: s.driverName || "",
      contextItems: [
        { label: "Equipment", value: s.truckUnit || "" },
      ],
      whatHappensNext: isOutOfService
        ? [
            "Dispatch can see this unit as out of service from this DVIR.",
            "Shop can review the reported defects before the unit returns to service.",
          ]
        : hasDefects
          ? [
              "Dispatch can see the filed DVIR and current unit status.",
              "Shop can review the reported defects and schedule repair follow-up.",
            ]
          : [
              "Dispatch and Shop both have the filed DVIR in the fleet record.",
              "The unit stays available unless a new defect is reported.",
            ],
      followUpRequired: isOutOfService
        ? "Do not operate this unit until Shop clears it for service."
        : hasDefects
          ? "Watch the reported condition during the shift and file another DVIR if it changes."
          : "No further action is required from you at this time.",
      expectedProcessingStatus: isOutOfService
        ? "Filed and out of service pending Shop review"
        : hasDefects
          ? "Filed and under Shop review"
          : "Filed and available in fleet records",
      returnToPortal: { label: "Return to Portal", to: "/field" },
      startAnother: { label: "Start Another", to: "/fleet/dvir/new" },
    });
  }, [id, orphan, s]);

  return <SubmissionConfirmation confirmation={confirmation} />;
}