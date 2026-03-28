import { RiskProfile } from "../types";

export function nextRiskProfile(current: RiskProfile): RiskProfile {
  if (current === "保守") return "均衡";
  if (current === "均衡") return "进取";
  return "保守";
}

export function riskDescription(profile: RiskProfile): string {
  switch (profile) {
    case "保守":
      return "优先控制回撤，降低波动。";
    case "均衡":
      return "兼顾收益与回撤，适合大多数新手。";
    case "进取":
      return "提高弹性，接受更高波动与回撤。";
  }
}
