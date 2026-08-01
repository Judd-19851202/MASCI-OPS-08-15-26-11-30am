import React from "react";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";

export function OperationalOutcomeFrame({
  testId,
  accent,
  familyLabel,
  familyMeta,
  kicker,
  title,
  description,
  heroIcon,
  heroMeta,
  heroAside,
  footerText,
  children,
  backTo = "/",
  backLabel = "Back to Hub",
}) {
  return (
    <OperationalPageFrame
      testId={testId}
      backTo={backTo}
      backLabel={backLabel}
      accent={accent}
      familyLabel={familyLabel}
      familyMeta={familyMeta}
      mainWidthClass="max-w-4xl"
      heroIcon={heroIcon}
      kicker={kicker}
      title={title}
      description={description}
      heroMeta={heroMeta}
      heroAside={heroAside}
      footerText={footerText}
    >
      <div className="space-y-5">{children}</div>
    </OperationalPageFrame>
  );
}

export default OperationalOutcomeFrame;