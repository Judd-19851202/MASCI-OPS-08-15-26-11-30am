/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("Additional KPI consumer contract", () => {
  test("material portal readers consume newly governed metadata", () => {
    const files = {
      hrTimeOff: fs.readFileSync(path.join(process.cwd(), "src/pages/HrTimeOff.jsx"), "utf8"),
      expirations: fs.readFileSync(path.join(process.cwd(), "src/components/ExpirationsSummary.jsx"), "utf8"),
      safetyHubV2: fs.readFileSync(path.join(process.cwd(), "src/pages/SafetyHubV2.jsx"), "utf8"),
      dispatchHubV2: fs.readFileSync(path.join(process.cwd(), "src/pages/DispatchHubV2.jsx"), "utf8"),
      leadershipHubV2: fs.readFileSync(path.join(process.cwd(), "src/pages/LeadershipHubV2.jsx"), "utf8"),
      shopHubV2: fs.readFileSync(path.join(process.cwd(), "src/pages/ShopHubV2.jsx"), "utf8"),
      safetyHub: fs.readFileSync(path.join(process.cwd(), "src/pages/SafetyHub.jsx"), "utf8"),
      commandStrip: fs.readFileSync(path.join(process.cwd(), "src/components/dispatch/command/CommandStrip.jsx"), "utf8"),
      commandCenter: fs.readFileSync(path.join(process.cwd(), "src/pages/DispatchCommandCenter.jsx"), "utf8"),
    };

    expect(files.hrTimeOff).toContain('metadata={stats?.kpi_metadata}');
    expect(files.expirations).toContain('metadata={data?.kpi_metadata}');
    expect(files.safetyHubV2).toContain('metadata={s.metadata?.sections?.corrective_actions}');
    expect(files.safetyHubV2).toContain('metadata={s.metadata?.sections?.compliance}');
    expect(files.safetyHubV2).toContain('metadata={s.metadata?.sections?.incidents}');
    expect(files.dispatchHubV2).toContain('metadata={s.metadata?.sections?.drivers_haul}');
    expect(files.dispatchHubV2).toContain('metadata={s.metadata?.sections?.fleet_shop}');
    expect(files.dispatchHubV2).toContain('metadata={s.metadata?.sections?.safety_watch}');
    expect(files.leadershipHubV2).toContain('metadata={s.saMeta?.page}');
    expect(files.leadershipHubV2).toContain('metadata={s.dsMeta?.sections?.fleet_shop}');
    expect(files.leadershipHubV2).toContain('metadata={s.exMeta}');
    expect(files.shopHubV2).toContain('metadata={s.metadata?.sections?.shop_recovery}');
    expect(files.safetyHub).toContain('metadata={kpis?.kpi_metadata?.sections?.classic_hub || kpis?.kpi_metadata?.page}');
    expect(files.commandStrip).toContain('metadata={metadata}');
    expect(files.commandCenter).toContain('metadata={summary?.kpi_metadata?.sections?.command_strip}');
    expect(files.commandCenter).toContain('metadata={metadata.fleet_shop}');
    expect(files.commandCenter).toContain('metadata={metadata.drivers_haul}');
    expect(files.commandCenter).toContain('metadata={metadata.shop_recovery}');
  });
});