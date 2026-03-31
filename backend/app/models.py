from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskProfile = Literal["保守", "均衡", "进取"]
FundType = Literal["equity", "etf_theme", "bond"]
Channel = Literal["场内", "场外"]
SortBy = Literal["final_score", "base_score", "policy_score", "one_year_return", "max_drawdown", "fee"]
SortOrder = Literal["asc", "desc"]


class Explanation(BaseModel):
    plus: list[str]
    minus: list[str]
    risk_tip: str
    applicable: str
    disclaimer: str
    formula: str


class FactorMetrics(BaseModel):
    returns: float = Field(ge=0, le=100)
    risk_control: float = Field(ge=0, le=100)
    risk_adjusted: float = Field(ge=0, le=100)
    stability: float = Field(ge=0, le=100)
    cost_efficiency: float = Field(ge=0, le=100)
    liquidity: float = Field(ge=0, le=100)
    survival_quality: float = Field(ge=0, le=100)


class PolicyMetrics(BaseModel):
    support: float = Field(ge=0, le=100)
    execution: float = Field(ge=0, le=100)
    regulation_safety: float = Field(ge=0, le=100)


class MarketSnapshot(BaseModel):
    current_price: float | None = None
    previous_close: float | None = None
    intraday_high: float | None = None
    intraday_low: float | None = None
    open_price: float | None = None
    price_change_pct: float | None = None
    price_change_value: float | None = None
    nav: float | None = None
    nav_date: str | None = None
    nav_estimate: float | None = None
    nav_estimate_change_pct: float | None = None
    volume: float | None = None
    turnover: float | None = None
    quote_time: str | None = None
    source: str | None = None


class Fund(BaseModel):
    code: str
    name: str
    channel: Channel
    category: str
    fund_type: FundType
    years: float
    scale_billion: float = Field(ge=0)
    fee: float
    risk_level: str
    one_year_return: float
    max_drawdown: float
    tracking_error: float | None = Field(default=None, ge=0)
    liquidity_label: str
    updated_at: str
    factors: FactorMetrics
    policy: PolicyMetrics


class FundScore(BaseModel):
    code: str
    name: str
    channel: Channel
    category: str
    fund_type: FundType
    scale_billion: float
    risk_level: str
    liquidity_label: str
    final_score: float
    base_score: float
    policy_score: float
    overlay_weight: float
    one_year_return: float
    max_drawdown: float
    explanation: Explanation
    market: MarketSnapshot | None = None


class FundsListResponse(BaseModel):
    items: list[FundScore]
    total: int
    page: int
    page_size: int


class FundDetail(FundScore):
    risk_level: str
    channel: Channel
    category: str
    years: float
    scale_billion: float
    one_year_return: float
    max_drawdown: float
    fee: float
    tracking_error: float | None = None
    liquidity_label: str
    updated_at: str
    factors: FactorMetrics
    policy: PolicyMetrics


class WatchlistScore(FundScore):
    alerts: list[str]


class WatchlistItem(BaseModel):
    code: str


class SectorHeatItem(BaseModel):
    label: str
    code: str
    change_pct: float | None = None
    current_price: float | None = None
    quote_time: str | None = None
    source: str | None = None


class PolicyTimestampCheckRequest(BaseModel):
    policy_id: str
    published_at: str
    effective_from: str
    observed_at: str


class PolicyTimestampCheckResponse(BaseModel):
    policy_id: str
    valid: bool
    errors: list[str]
