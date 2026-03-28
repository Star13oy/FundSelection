import { blendScore, getOverlayWeight, scoreLabel } from "./score";

describe("score utils", () => {
  test("getOverlayWeight returns configured values", () => {
    expect(getOverlayWeight("equity", "均衡")).toBe(0.15);
    expect(getOverlayWeight("etf_theme", "进取")).toBe(0.25);
    expect(getOverlayWeight("bond", "保守")).toBe(0.05);
  });

  test("blendScore calculates weighted score", () => {
    expect(blendScore(80, 90, 0.2)).toBe(82);
    expect(blendScore(88.33, 70, 0.15)).toBe(85.58);
  });

  test("scoreLabel maps score ranges", () => {
    expect(scoreLabel(95)).toBe("优选");
    expect(scoreLabel(85)).toBe("关注");
    expect(scoreLabel(70)).toBe("谨慎");
  });
});
