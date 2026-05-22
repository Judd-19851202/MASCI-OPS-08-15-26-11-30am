// iter324 · safetyAccountabilityClass classifier — unit contract.
//
// Locks down the operator's governance rule:
//   • Consumable / daily-use PPE must NEVER classify as accountability.
//   • Serialized / recoverable PPE MUST classify into the correct class.
//   • Aging predicate respects the 90-day threshold and the "no return"
//     precondition.
import {
  getAccountabilityClass,
  isAccountabilityItem,
  isAgingAccountability,
  daysSince,
  accountabilityClassLabels,
} from "./safetyAccountabilityClass";

describe("safetyAccountabilityClass · consumable exclusion", () => {
  const CONSUMABLES = [
    { item: "Hard Hat" },
    { item: "Hard Hat", description: "with chinstrap" },
    { item: "Safety Glasses" },
    { item: "Safety Goggles" },
    { item: "Safety Vest" },
    { item: "Hi-Vis Vest" },
    { item: "Class 3 Vest" },
    { item: "Gloves", description: "leather" },
    { item: "Ear Plugs" },
    { item: "Hearing Protection" },
    { item: "Earmuffs" },
    { item: "Dust Mask" },
    { item: "Disposable N95" },
    { item: "Disposable Mask" },
    { item: "Steel Toe Boots" },
    { item: "Rain Coat" },
    { item: "Knee Pads" },
    { item: "Sunscreen" },
    { item: "Water Bottle" },
    { item: "Cooling Towel" },
  ];

  test.each(CONSUMABLES)("consumable %j must NOT classify", (it) => {
    expect(getAccountabilityClass(it)).toBeNull();
    expect(isAccountabilityItem(it)).toBe(false);
  });
});

describe("safetyAccountabilityClass · accountability classification", () => {
  const ACCOUNTABILITY = [
    [{ item: "Harness", description: "Full body" }, "fall_protection"],
    [{ item: "Lanyard" }, "fall_protection"],
    [{ item: "SRL", description: "self-retracting" }, "fall_protection"],
    [{ item: "Self-Retracting Lifeline" }, "fall_protection"],
    [{ item: "Rope Grab" }, "fall_protection"],
    [{ item: "Full-Face Respirator" }, "respiratory"],
    [{ item: "PAPR Hood" }, "respiratory"],
    [{ item: "SCBA Pack" }, "respiratory"],
    [{ item: "4-Gas Monitor" }, "gas_monitor"],
    [{ item: "BW Clip", description: "H2S" }, "gas_monitor"],
    [{ item: "Confined Space Tripod" }, "confined_space"],
    [{ item: "Winch" }, "confined_space"],
    [{ item: "Ventilator Blower" }, "confined_space"],
    [{ item: "FR Coverall" }, "fr_arc_flash"],
    [{ item: "Arc-Flash Hood" }, "fr_arc_flash"],
    [{ item: "Flame-Resistant Jacket" }, "fr_arc_flash"],
    [{ item: "Flagger Kit" }, "specialty_traffic"],
    [{ item: "Spotter Kit" }, "specialty_traffic"],
    [{ item: "Sound Level Meter", description: "calibrated" }, "calibrated_device"],
    [{ item: "Welding Hood" }, "welding"],
    [{ item: "Auto-Darkening Welding Helmet" }, "welding"],
  ];

  test.each(ACCOUNTABILITY)("%j classifies as %s", (item, expected) => {
    expect(getAccountabilityClass(item)).toBe(expected);
    expect(isAccountabilityItem(item)).toBe(true);
  });
});

describe("safetyAccountabilityClass · isAgingAccountability", () => {
  const today = new Date();
  const isoDaysAgo = (n) => {
    const d = new Date(today.getTime() - n * 86400000);
    return d.toISOString().slice(0, 10);
  };

  test("returns false when record has a return logged", () => {
    expect(
      isAgingAccountability({
        issued_date: isoDaysAgo(120),
        return: { items: [] },
        items: [{ item: "Harness" }],
      })
    ).toBe(false);
  });

  test("returns false when aging threshold not crossed", () => {
    expect(
      isAgingAccountability({
        issued_date: isoDaysAgo(45),
        items: [{ item: "Harness" }],
      })
    ).toBe(false);
  });

  test("returns false when only consumable PPE is on the record", () => {
    expect(
      isAgingAccountability({
        issued_date: isoDaysAgo(180),
        items: [{ item: "Hard Hat" }, { item: "Safety Glasses" }, { item: "Gloves" }],
      })
    ).toBe(false);
  });

  test("returns true when serialized PPE is out > 90 days, no return", () => {
    expect(
      isAgingAccountability({
        issued_date: isoDaysAgo(120),
        items: [{ item: "Hard Hat" }, { item: "Harness", description: "Full body" }],
      })
    ).toBe(true);
  });

  test("custom threshold is respected", () => {
    expect(
      isAgingAccountability(
        { issued_date: isoDaysAgo(45), items: [{ item: "Harness" }] },
        30
      )
    ).toBe(true);
  });

  test("invalid / missing issued_date returns false", () => {
    expect(isAgingAccountability({ items: [{ item: "Harness" }] })).toBe(false);
    expect(
      isAgingAccountability({ issued_date: "bogus", items: [{ item: "Harness" }] })
    ).toBe(false);
  });
});

describe("safetyAccountabilityClass · real-data field shapes (item_type)", () => {
  test("classifies real issuance shape with item_type=Harness", () => {
    expect(
      getAccountabilityClass({
        item_type: "Harness",
        description: "Full body",
        quantity: 1,
      })
    ).toBe("fall_protection");
  });

  test("real issuance shape with item_type=Hard Hat stays silent", () => {
    expect(
      getAccountabilityClass({
        item_type: "Hard Hat",
        description: "Standard hard hat L",
      })
    ).toBeNull();
  });

  test("free-text item_type_other='Custom Tool' is unclassified", () => {
    expect(
      getAccountabilityClass({
        item_type: "Other",
        item_type_other: "Custom Tool",
      })
    ).toBeNull();
  });

  test("free-text item_type_other carrying 'Gas Monitor' classifies", () => {
    expect(
      getAccountabilityClass({
        item_type: "Other",
        item_type_other: "4-Gas Monitor",
      })
    ).toBe("gas_monitor");
  });
});

describe("safetyAccountabilityClass · daysSince", () => {
  test("returns null for invalid input", () => {
    expect(daysSince(null)).toBeNull();
    expect(daysSince("not-a-date")).toBeNull();
  });

  test("returns a non-negative integer for a past date", () => {
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    const d = daysSince(yesterday);
    expect(Number.isInteger(d)).toBe(true);
    expect(d).toBeGreaterThanOrEqual(0);
  });
});

describe("safetyAccountabilityClass · accountabilityClassLabels", () => {
  test("returns deduped, ordered EN labels", () => {
    const labels = accountabilityClassLabels(
      {
        items: [
          { item: "Hard Hat" },
          { item: "Harness" },
          { item: "Lanyard" },
          { item: "4-Gas Monitor" },
        ],
      },
      "en"
    );
    expect(labels).toEqual(["Fall Protection", "Gas Monitor"]);
  });

  test("returns Spanish labels when lang='es'", () => {
    const labels = accountabilityClassLabels(
      { items: [{ item: "Harness" }] },
      "es"
    );
    expect(labels).toEqual(["Protección Contra Caídas"]);
  });
});
