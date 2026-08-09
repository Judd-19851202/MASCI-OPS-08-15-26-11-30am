import React from "react";
import { describe, expect, it, jest } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react";

jest.mock("@/lib/i18n", () => ({
  __esModule: true,
  useT: () => ({ t: (value) => value, lang: "en" }),
}));

jest.mock("react-router-dom", () => ({
  __esModule: true,
  Link: ({ to, children, ...rest }) => <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>,
}), { virtual: true });

jest.mock("@/lib/operatorLanguage", () => ({
  __esModule: true,
  sanitizeOperatorCopy: (value) => value,
}));

jest.mock("@/lib/api", () => ({
  __esModule: true,
  api: { get: () => Promise.resolve({}) },
}));

import { WorkflowCoachingDisclosure } from "../WorkflowCoachingDisclosure";
import { WhyItMattersPanel } from "@/components/guidance";

describe("WorkflowCoachingDisclosure", () => {
  it("stays collapsed by default until the operator opens it", () => {
    render(
      <WorkflowCoachingDisclosure
        testIdPrefix="workflow-check"
        blocks={[{ label: "Why this matters", body: "Keep the primary work visible first." }]}
      />,
    );

    expect(screen.getByTestId("workflow-check-trigger").getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByTestId("workflow-check-panel")).toBeNull();
    expect(screen.getByTestId("workflow-check-counter").textContent).toMatch(/workflow tips available/i);
  });

  it("reveals the shared coaching panel only after expand", () => {
    render(
      <WorkflowCoachingDisclosure
        testIdPrefix="workflow-open"
        title="Workflow tips"
        blocks={[{ label: "What happens next", body: "Open the detail and finish the review." }]}
      />,
    );

    fireEvent.click(screen.getByTestId("workflow-open-trigger"));

    expect(screen.getByTestId("workflow-open-trigger").getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByTestId("workflow-open-panel")).not.toBeNull();
    expect(screen.getByText("Open the detail and finish the review.")).not.toBeNull();
  });
});

describe("WhyItMattersPanel", () => {
  it("uses the same collapsed disclosure pattern", () => {
    render(
      <WhyItMattersPanel title="Why this matters">
        <p>Review the record before approving it.</p>
      </WhyItMattersPanel>,
    );

    const trigger = screen.getByTestId("why-it-matters-panel-trigger");
    expect(trigger.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(trigger);

    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByTestId("why-it-matters-panel-body")).not.toBeNull();
    expect(screen.getByTestId("why-it-matters-dismiss")).not.toBeNull();
  });
});