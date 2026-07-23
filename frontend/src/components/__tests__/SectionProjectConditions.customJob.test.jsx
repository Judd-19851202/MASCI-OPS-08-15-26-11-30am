import React from "react";
import { beforeEach, describe, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react";
import { SectionProjectConditions } from "../daily-report-v3/SectionProjectConditions";

jest.mock("@/lib/i18n", () => ({
  useT: () => ({ t: (value) => value }),
}));

jest.mock("@/components/JobPicker", () => ({
  JobPicker: ({ onSelect, ...props }) => (
    <div>
      <button data-testid={props["data-testid"]} onClick={() => onSelect(null)}>
        Custom job
      </button>
    </div>
  ),
}));

jest.mock("@/lib/jobLibrary", () => ({
  findJob: () => null,
}));

describe("SectionProjectConditions custom job flow", () => {
  const baseProps = {
    data: {
      project_number: "",
      project_name: "",
      location: "",
      report_date: "2026-07-23",
      prepared_by: "",
      superintendent: "",
    },
    patch: jest.fn(),
    onUseGps: jest.fn(),
    onRefreshWeather: jest.fn(),
    isFetchingGps: false,
    isFetchingWeather: false,
    weatherLabel: "",
    reportNumberPreview: "DR-2026-03532",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("reveals manual project fields after choosing the custom job path", () => {
    render(<SectionProjectConditions {...baseProps} />);

    fireEvent.click(screen.getByTestId("dr-v3-job-picker"));

    expect(screen.getByTestId("dr-v3-custom-job-fields")).toBeTruthy();
    expect(screen.getByTestId("dr-v3-custom-project-number")).toBeTruthy();
    expect(screen.getByTestId("dr-v3-custom-project-name")).toBeTruthy();
  });

  test("wires unique prepared-by and superintendent test ids", () => {
    render(<SectionProjectConditions {...baseProps} />);

    expect(screen.getByTestId("dr-v3-prepared-by-input")).toBeTruthy();
    expect(screen.getByTestId("dr-v3-prepared-by-toggle")).toBeTruthy();
    expect(screen.getByTestId("dr-v3-superintendent-input")).toBeTruthy();
    expect(screen.getByTestId("dr-v3-superintendent-toggle")).toBeTruthy();
  });
});