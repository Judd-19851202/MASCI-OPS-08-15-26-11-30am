import React from "react";
import { WorkflowCoachingDisclosure } from "@/components/WorkflowCoachingDisclosure";

export function OperationalCoachingStrip({
  blocks = [],
  testId = "operational-coaching-strip",
  className = "",
  title,
  eyebrow,
}) {
  if (!blocks.length) return null;

  return (
    <WorkflowCoachingDisclosure
      blocks={blocks}
      title={title}
      eyebrow={eyebrow}
      icon={blocks[0]?.icon}
      testIdPrefix={testId}
      className={className}
      defaultOpen={false}
    />
  );
}

export default OperationalCoachingStrip;