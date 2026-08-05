import React from "react";
import { useLocation } from "react-router-dom";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { adaptLegacyThankYouState } from "@/lib/submissionConfirmation";

export default function ThankYou() {
  const location = useLocation();
  const confirmation = React.useMemo(
    () => adaptLegacyThankYouState(location.state || {}),
    [location.state],
  );

  return <SubmissionConfirmation confirmation={confirmation} />;
}