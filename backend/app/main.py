from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    Channel,
    FundDetail,
    Fund,
    FundsListResponse,
    FundScore,
    MarketSnapshot,
    PolicyTimestampCheckRequest,
    PolicyTimestampCheckResponse,
    RiskProfile,
    SortBy,
    SortOrder,
    WatchlistItem,
    WatchlistScore,
)
from app.policy_validation import validate_policy_timestamps
from app.scoring import explain, final_score, watchlist_alerts
from app.store import (
    add_watchlist,
    filter_funds,
    get_fund,
    get_market_snapshot,
    get_market_snapshots,
    init_store,
    list_watchlist,
    refresh_market_quotes_if_stale,
    refresh_market_quotes,
    remove_watchlist,
    sync_fund_universe,
)

app = FastAPI(
    title="Fund Quant Backend",
    version="0.2.0",
    description="A股基金量化选基 MVP 后端接口。",
)

init_store()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sort_key(
    item: FundScore,
    sort_by: SortBy,
    fee: float | None,
    one_year_return: float | None,
    max_drawdown: float | None,
) -> float:
    if sort_by == "fee":
        return fee if fee is not None else 0.0
    if sort_by == "one_year_return":
        return one_year_return if one_year_return is not None else 0.0
    if sort_by == "max_drawdown":
        return max_drawdown if max_drawdown is not None else 0.0
    return float(getattr(item, sort_by))


def _build_fund_score(fund: Fund, risk_profile: RiskProfile, market: MarketSnapshot | None = None) -> FundScore:
    final, base, policy, overlay = final_score(fund, risk_profile)
    return FundScore(
        code=fund.code,
        name=fund.name,
        channel=fund.channel,
        category=fund.category,
        risk_level=fund.risk_level,
        liquidity_label=fund.liquidity_label,
        final_score=final,
        base_score=base,
        policy_score=policy,
        overlay_weight=overlay,
        explanation=explain(fund, risk_profile),
        market=market,
    )


def _build_fund_detail(fund: Fund, risk_profile: RiskProfile) -> FundDetail:
    score = _build_fund_score(fund, risk_profile, get_market_snapshot(fund.code))
    return FundDetail(
        **score.model_dump(),
        years=fund.years,
        scale_billion=fund.scale_billion,
        one_year_return=fund.one_year_return,
        max_drawdown=fund.max_drawdown,
        fee=fund.fee,
        tracking_error=fund.tracking_error,
        updated_at=fund.updated_at,
        factors=fund.factors,
        policy=fund.policy,
    )


def _build_watchlist_score(fund: Fund, risk_profile: RiskProfile) -> WatchlistScore:
    score = _build_fund_score(fund, risk_profile, get_market_snapshot(fund.code))
    return WatchlistScore(
        **score.model_dump(),
        alerts=watchlist_alerts(fund, risk_profile),
    )


def _require_fund(code: str) -> Fund:
    fund = get_fund(code)
    if fund is None:
        raise HTTPException(status_code=404, detail=f"Fund {code} not found")
    return fund


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/funds", response_model=FundsListResponse)
def list_funds(
    channel: Channel | None = Query(default=None),
    category: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    min_years: float | None = Query(default=None, ge=0),
    min_scale: float | None = Query(default=None, ge=0),
    max_scale: float | None = Query(default=None, ge=0),
    max_fee: float | None = Query(default=None, ge=0),
    keyword: str | None = Query(default=None),
    risk_profile: RiskProfile = Query(default="均衡"),
    sort_by: SortBy = Query(default="final_score"),
    sort_order: SortOrder = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FundsListResponse:
    refresh_market_quotes_if_stale(max_age_minutes=15)
    funds = filter_funds(channel, category, risk_level, min_years, min_scale, max_scale, max_fee, keyword)
    market_map = get_market_snapshots([fund.code for fund in funds])

    scored_with_fields: list[tuple[FundScore, float, float, float]] = []
    for fund in funds:
        score = _build_fund_score(fund, risk_profile, market_map.get(fund.code))
        scored_with_fields.append(
            (
                score,
                fund.fee,
                fund.one_year_return,
                fund.max_drawdown,
            )
        )

    reverse = sort_order == "desc"
    scored_with_fields.sort(
        key=lambda row: _sort_key(row[0], sort_by, row[1], row[2], row[3]),
        reverse=reverse,
    )

    total = len(scored_with_fields)
    start = (page - 1) * page_size
    end = start + page_size
    items = [row[0] for row in scored_with_fields[start:end]]
    return FundsListResponse(items=items, total=total, page=page, page_size=page_size)


@app.get("/api/v1/funds/{code}", response_model=FundDetail)
def fund_detail(code: str, risk_profile: RiskProfile = Query(default="均衡")) -> FundDetail:
    fund = _require_fund(code)
    return _build_fund_detail(fund, risk_profile)


@app.get("/api/v1/compare", response_model=list[FundScore])
def compare_funds(
    codes: Annotated[list[str], Query(min_length=2, max_length=5)],
    risk_profile: RiskProfile = Query(default="均衡"),
) -> list[FundScore]:
    if not (2 <= len(codes) <= 5):
        raise HTTPException(status_code=400, detail="codes size must be 2~5")

    market_map = get_market_snapshots(codes)
    results = [_build_fund_score(_require_fund(code), risk_profile, market_map.get(code)) for code in codes]
    results.sort(key=lambda x: x.final_score, reverse=True)
    return results


@app.get("/api/v1/watchlist", response_model=list[WatchlistScore])
def get_watchlist(risk_profile: RiskProfile = Query(default="均衡")) -> list[WatchlistScore]:
    funds = list_watchlist()
    data = [_build_watchlist_score(fund, risk_profile) for fund in funds]
    data.sort(key=lambda x: x.final_score, reverse=True)
    return data


@app.post("/api/v1/watchlist")
def create_watchlist(payload: WatchlistItem) -> dict[str, str]:
    ok = add_watchlist(payload.code)
    if not ok:
        raise HTTPException(status_code=404, detail="Fund not found")
    return {"status": "ok", "code": payload.code}


@app.delete("/api/v1/watchlist/{code}")
def delete_watchlist(code: str) -> dict[str, str]:
    remove_watchlist(code)
    return {"status": "ok", "code": code}


@app.post("/api/v1/market/refresh")
def refresh_market() -> dict[str, object]:
    summary = refresh_market_quotes()
    return {"status": "ok", **summary}


@app.post("/api/v1/funds/sync")
def sync_funds() -> dict[str, object]:
    summary = sync_fund_universe()
    return {"status": "ok", **summary}


@app.post("/api/v1/policy/validate-timestamps", response_model=PolicyTimestampCheckResponse)
def validate_policy_payload(payload: PolicyTimestampCheckRequest) -> PolicyTimestampCheckResponse:
    valid, errors = validate_policy_timestamps(
        payload.published_at,
        payload.effective_from,
        payload.observed_at,
    )
    return PolicyTimestampCheckResponse(policy_id=payload.policy_id, valid=valid, errors=errors)
