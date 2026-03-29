import type { RiskProfile } from "../types.ts";

const WEIGHTS: Record<string, Record<RiskProfile, number>> = {
  equity: { 保守: 0.1, 均衡: 0.15, 进取: 0.2 },
  etf_theme: { 保守: 0.15, 均衡: 0.2, 进取: 0.25 },
  bond: { 保守: 0.05, 均衡: 0.08, 进取: 0.1 }
};

export function getOverlayWeight(fundType: keyof typeof WEIGHTS, risk: RiskProfile): number {
  return WEIGHTS[fundType][risk];
}

export function blendScore(baseScore: number, policyScore: number, overlayWeight: number): number {
  return Number((baseScore * (1 - overlayWeight) + policyScore * overlayWeight).toFixed(2));
}

export function scoreLabel(score: number): string {
  if (score >= 90) return "优选";
  if (score >= 80) return "关注";
  return "谨慎";
}
