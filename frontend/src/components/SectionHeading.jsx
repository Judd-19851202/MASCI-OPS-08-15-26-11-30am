import React from "react";

export function SectionHeading({ index, title, subtitle, testId = "section-heading" }) {
  return (
    <div className="wp17-section-heading" data-testid={testId}>
      <div className="wp17-section-heading__rail">
        <span className="wp17-section-heading__index" data-testid={`${testId}-index`}>{index}</span>
        <span className="wp17-section-heading__line" aria-hidden="true" />
      </div>
      <div className="wp17-section-heading__copy">
        <h2 className="wp17-section-heading__title" data-testid={`${testId}-title`}>{title}</h2>
        {subtitle ? <p className="wp17-section-heading__subtitle" data-testid={`${testId}-subtitle`}>{subtitle}</p> : null}
      </div>
    </div>
  );
}

export default SectionHeading;