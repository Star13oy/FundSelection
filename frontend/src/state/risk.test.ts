import { nextRiskProfile, riskDescription } from "./risk";

describe("risk state helpers", () => {
  test("nextRiskProfile cycles correctly", () => {
    expect(nextRiskProfile("保守")).toBe("均衡");
    expect(nextRiskProfile("均衡")).toBe("进取");
    expect(nextRiskProfile("进取")).toBe("保守");
  });

  test("riskDescription returns profile message", () => {
    expect(riskDescription("保守")).toContain("控制回撤");
    expect(riskDescription("均衡")).toContain("兼顾收益");
    expect(riskDescription("进取")).toContain("更高波动");
  });
});
