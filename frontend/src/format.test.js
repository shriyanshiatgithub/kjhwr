import { describe, expect, it } from "vitest";
import { bufferAdvice, energyMWh, fmtMW, fmtSigned, toChartRows, ukDateTime, ukTime } from "./format";

describe("formatting", () => {
  it("formats MW and handles null", () => {
    expect(fmtMW(1234.6)).toBe("1,235 MW");
    expect(fmtMW(null)).toBe("-");
  });

  it("shows sign on errors", () => {
    expect(fmtSigned(200)).toBe("+200 MW");
    expect(fmtSigned(-50)).toBe("-50 MW");
    expect(fmtSigned(0)).toBe("0 MW");
  });

  it("renders UK local time, including summer time", () => {
    expect(ukTime("2026-01-10T12:00:00Z")).toBe("12:00"); // GMT
    expect(ukTime("2026-07-10T12:00:00Z")).toBe("13:00"); // BST
    expect(ukDateTime("2026-01-09T09:00:00Z")).toContain("09:00");
  });
});

describe("calculations", () => {
  it("converts half-hourly MW to MWh and skips nulls", () => {
    expect(energyMWh([100, 200, null])).toBe(150);
    expect(energyMWh([])).toBe(0);
  });

  it("keeps missing forecasts as null (a gap, not zero)", () => {
    const rows = toChartRows([{ start_time: "2026-01-10T00:00:00Z", forecast: null, actual: 5, error: null }]);
    expect(rows[0].forecast).toBeNull();
  });

  it("explains the buffer in words", () => {
    const text = bufferAdvice({ n: 10, bias: 50, error_p90: 800 });
    expect(text).toContain("too high");
    expect(text).toContain("800 MW");
    expect(bufferAdvice({ n: 0 })).toMatch(/Not enough data/);
  });
});
