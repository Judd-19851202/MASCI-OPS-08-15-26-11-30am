/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("ViewDailyReport attachment surface contract", () => {
  test("renders canonical attachment evidence block with a stable test id", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/pages/ViewDailyReport.jsx"),
      "utf8",
    );

    expect(source).toContain('data.attachments?.length > 0');
    expect(source).toContain('data-testid="dr-view-attachments"');
    expect(source).toContain('Attachments & document evidence');
    expect(source).toContain('formatAttachmentSize');
  });
});