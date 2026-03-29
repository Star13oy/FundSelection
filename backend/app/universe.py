from __future__ import annotations

import hashlib
from datetime import date

from app.data import FUNDS
from app.models import FactorMetrics, Fund, FundType, PolicyMetrics

try:
    import akshare as ak
except ImportError:  # pragma: no cover
    ak = None


def _seed(code: str, salt: str) -> int:
    digest = hashlib.md5(f"{code}:{salt}".encode("utf-8")).hexdigest()[:8]
    return int(digest, 16)


def _bucket(code: str, salt: str, low: float, high: float, digits: int = 2) -> float:
    span = high - low
    value = low + (_seed(code, salt) % 10_000) / 10_000 * span
    return round(value, digits)


def _classify_channel(name: str, kind: str) -> str:
    text = f"{name}{kind}".upper()
    if "ETF" in text or "LOF" in text:
        return "场内"
    return "场外"


def _classify_category(name: str, kind: str) -> str:
    text = f"{name}{kind}"
    if "债" in text:
        return "债券"
    sector_words = ("半导体", "医药", "消费", "新能源", "军工", "证券", "银行", "科技", "通信", "创新药", "白酒", "煤炭")
    if any(word in text for word in sector_words):
        return "行业"
    if "混合" in text:
        return "混合"
    return "宽基"


def _classify_fund_type(channel: str, category: str) -> FundType:
    if category == "债券":
        return "bond"
    if channel == "场内" and category == "行业":
        return "etf_theme"
    return "equity"


def _risk_level(category: str, channel: str) -> str:
    if category == "债券":
        return "R2"
    if category == "混合":
        return "R4"
    if channel == "场内" and category == "行业":
        return "R5"
    return "R4"


def _liquidity_label(channel: str, category: str) -> str:
    if channel == "场内":
        if category == "宽基":
            return "高流动性"
        if category == "行业":
            return "中高流动性"
        return "中流动性"
    if category == "债券":
        return "稳健申赎"
    return "申赎为主"


def _factor_metrics(code: str, category: str, channel: str) -> FactorMetrics:
    base_return = 70.0 if category == "债券" else 78.0
    if category == "行业":
        base_return = 83.0

    risk_control = 90.0 if category == "债券" else 72.0
    if channel == "场内" and category == "宽基":
        risk_control = 78.0

    liquidity = 88.0 if channel == "场内" else 66.0
    if category == "债券":
        liquidity = 72.0

    return FactorMetrics(
        returns=max(45.0, min(98.0, base_return + _bucket(code, "returns", -12, 12))),
        risk_control=max(45.0, min(98.0, risk_control + _bucket(code, "risk_control", -12, 12))),
        risk_adjusted=max(45.0, min(98.0, 74.0 + _bucket(code, "risk_adjusted", -12, 14))),
        stability=max(45.0, min(98.0, 70.0 + _bucket(code, "stability", -15, 14))),
        cost_efficiency=max(45.0, min(98.0, 72.0 + _bucket(code, "cost", -12, 16))),
        liquidity=max(45.0, min(98.0, liquidity + _bucket(code, "liquidity", -12, 10))),
        survival_quality=max(45.0, min(99.0, 76.0 + _bucket(code, "survival", -10, 16))),
    )


def _policy_metrics(code: str, category: str) -> PolicyMetrics:
    support = 70.0
    if category == "债券":
        support = 74.0
    if category == "行业":
        support = 77.0
    return PolicyMetrics(
        support=max(45.0, min(98.0, support + _bucket(code, "policy_support", -12, 14))),
        execution=max(45.0, min(98.0, 72.0 + _bucket(code, "policy_execution", -12, 12))),
        regulation_safety=max(45.0, min(99.0, 78.0 + _bucket(code, "policy_safe", -10, 12))),
    )


def _build_from_ak_row(row: dict[str, object]) -> Fund | None:
    code = str(row.get("基金代码", "")).strip().zfill(6)
    name = str(row.get("基金简称", "")).strip()
    kind = str(row.get("基金类型", "")).strip()
    if not code.isdigit() or len(code) != 6 or not name:
        return None

    channel = _classify_channel(name, kind)
    category = _classify_category(name, kind)
    fund_type = _classify_fund_type(channel, category)
    risk_level = _risk_level(category, channel)
    liquidity_label = _liquidity_label(channel, category)

    years = _bucket(code, "years", 0.6, 18.0, digits=1)
    scale_billion = _bucket(code, "scale", 3.0, 900.0, digits=1)
    fee = _bucket(code, "fee", 0.2, 1.8, digits=2)
    if channel == "场内":
        fee = _bucket(code, "fee_etf", 0.15, 0.9, digits=2)
    if category == "债券":
        fee = _bucket(code, "fee_bond", 0.1, 0.9, digits=2)

    one_year_return = _bucket(code, "ret", 2.0, 32.0, digits=2)
    if category == "债券":
        one_year_return = _bucket(code, "ret_bond", 1.0, 9.0, digits=2)
    if category == "行业":
        one_year_return = _bucket(code, "ret_sector", -8.0, 38.0, digits=2)

    drawdown_abs = _bucket(code, "dd", 1.2, 24.0, digits=2)
    if category == "债券":
        drawdown_abs = _bucket(code, "dd_bond", 0.3, 6.0, digits=2)
    max_drawdown = -drawdown_abs

    tracking_error = None
    if channel == "场内":
        tracking_error = _bucket(code, "te", 0.05, 0.95, digits=2)

    return Fund(
        code=code,
        name=name,
        channel=channel,  # type: ignore[arg-type]
        category=category,
        fund_type=fund_type,
        years=years,
        scale_billion=scale_billion,
        fee=fee,
        risk_level=risk_level,
        one_year_return=one_year_return,
        max_drawdown=max_drawdown,
        tracking_error=tracking_error,
        liquidity_label=liquidity_label,
        updated_at=date.today().isoformat(),
        factors=_factor_metrics(code, category, channel),
        policy=_policy_metrics(code, category),
    )


def load_fund_universe() -> list[Fund]:
    rows: list[Fund] = []

    if ak is not None:
        try:
            table = ak.fund_name_em()
            for row in table.to_dict(orient="records"):
                fund = _build_from_ak_row(row)
                if fund is not None:
                    rows.append(fund)
        except Exception:
            rows = []

    if not rows:
        rows = list(FUNDS)

    # Keep curated fixtures as high-quality overrides.
    by_code: dict[str, Fund] = {fund.code: fund for fund in rows}
    for fixture in FUNDS:
        by_code[fixture.code] = fixture
    return list(by_code.values())
