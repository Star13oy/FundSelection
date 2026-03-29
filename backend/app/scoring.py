from __future__ import annotations

from statistics import mean

from app.models import Explanation, Fund, RiskProfile

OVERLAY_WEIGHTS = {
    "equity": {"保守": 0.10, "均衡": 0.15, "进取": 0.20},
    "etf_theme": {"保守": 0.15, "均衡": 0.20, "进取": 0.25},
    "bond": {"保守": 0.05, "均衡": 0.08, "进取": 0.10},
}


def policy_score(fund: Fund) -> float:
    return round(
        0.4 * fund.policy.support
        + 0.3 * fund.policy.execution
        + 0.3 * fund.policy.regulation_safety,
        2,
    )


def base_score(fund: Fund) -> float:
    factor_values = [
        fund.factors.returns,
        fund.factors.risk_control,
        fund.factors.risk_adjusted,
        fund.factors.stability,
        fund.factors.cost_efficiency,
        fund.factors.liquidity,
        fund.factors.survival_quality,
    ]
    return round(mean(factor_values), 2)


def overlay_weight(fund: Fund, risk_profile: RiskProfile) -> float:
    return OVERLAY_WEIGHTS[fund.fund_type][risk_profile]


def final_score(fund: Fund, risk_profile: RiskProfile) -> tuple[float, float, float, float]:
    b_score = base_score(fund)
    p_score = policy_score(fund)
    o_weight = overlay_weight(fund, risk_profile)
    final = round(b_score * (1 - o_weight) + p_score * o_weight, 2)
    return final, b_score, p_score, o_weight


def explain(fund: Fund, risk_profile: RiskProfile) -> Explanation:
    _final, b_score, p_score, o_weight = final_score(fund, risk_profile)
    plus = []
    minus = []

    if fund.factors.risk_control >= 85:
        plus.append("风险控制表现较好（回撤控制与稳定性较优）")
    if fund.factors.cost_efficiency >= 85:
        plus.append("成本效率较高（费率与交易效率较优）")
    if p_score >= 80:
        plus.append("政策环境偏积极（政策支持与执行进度较强）")

    if fund.factors.risk_control <= 60:
        minus.append("回撤与波动压力偏高")
    if fund.fee >= 1.2:
        minus.append("费率偏高，可能侵蚀长期收益")
    if fund.policy.regulation_safety <= 70:
        minus.append("监管约束风险较高，需谨慎")

    risk_tip = (
        f"当前为{fund.risk_level}，建议与“{risk_profile}”风险偏好匹配，"
        "仅作辅助决策，不构成投资建议。"
    )
    applicable = (
        f"适合计划持有 {max(1, round(fund.years / 3))}-{max(2, round(fund.years / 2))} 年、"
        f"可接受 {fund.risk_level} 风险等级波动的投资者。"
    )
    disclaimer = "仅供参考，不构成投资建议。"

    return Explanation(
        plus=plus[:3] or ["暂无明显优势因子"],
        minus=minus[:3] or ["暂无明显短板因子"],
        risk_tip=risk_tip,
        applicable=applicable,
        disclaimer=disclaimer,
        formula=(
            f"FinalScore = BaseScore*{1 - o_weight:.2f} + PolicyScore*{o_weight:.2f}; "
            f"当前 BaseScore={b_score}, PolicyScore={p_score}"
        ),
    )


def watchlist_alerts(fund: Fund, risk_profile: RiskProfile) -> list[str]:
    final, _base, policy, _overlay = final_score(fund, risk_profile)
    alerts: list[str] = []

    if fund.max_drawdown <= -15:
        alerts.append("回撤超阈值（<= -15%）")
    if final < 75:
        alerts.append("综合评分偏低（<75）")
    if policy < 70:
        alerts.append("政策因子转弱（<70）")

    return alerts or ["状态正常"]
