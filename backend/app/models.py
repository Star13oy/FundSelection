from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskProfile = Literal["保守", "均衡", "进取"]
FundType = Literal["equity", "etf_theme", "bond"]
Channel = Literal["场内", "场外"]
SortBy = Literal["final_score", "base_score", "policy_score", "one_year_return", "max_drawdown", "fee"]
SortOrder = Literal["asc", "desc"]


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


class Fund(BaseModel):
    code: str
    name: str
    channel: Channel
    category: str
    fund_type: FundType
    years: float
    fee: float
    risk_level: str
    one_year_return: float
    max_drawdown: float
    factors: FactorMetrics
    policy: PolicyMetrics


class FundScore(BaseModel):
    code: str
    name: str
    final_score: float
    base_score: float
    policy_score: float
    overlay_weight: float
    explanation: dict[str, list[str] | str]


class FundsListResponse(BaseModel):
    items: list[FundScore]
    total: int
    page: int
    page_size: int


class FundDetail(FundScore):
    risk_level: str
    channel: Channel
    category: str
    one_year_return: float
    max_drawdown: float
    fee: float


class WatchlistScore(FundScore):
    alerts: list[str]


class WatchlistItem(BaseModel):
    code: str


class PolicyTimestampCheckRequest(BaseModel):
    policy_id: str
    published_at: str
    effective_from: str
    observed_at: str


class PolicyTimestampCheckResponse(BaseModel):
    policy_id: str
    valid: bool
    errors: list[str]
