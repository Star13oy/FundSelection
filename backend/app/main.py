from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.models import (
    FundDetail,
    FundsListResponse,
    FundScore,
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
from app.store import add_watchlist, filter_funds, get_fund, list_watchlist, remove_watchlist

app = FastAPI(title="Fund Quant Backend", version="0.1.0")


def _sort_key(item: FundScore, sort_by: SortBy, fee: float | None, one_year_return: float | None, max_drawdown: float | None) -> float:
    if sort_by == "fee":
        return fee if fee is not None else 0.0
    if sort_by == "one_year_return":
        return one_year_return if one_year_return is not None else 0.0
    if sort_by == "max_drawdown":
        return max_drawdown if max_drawdown is not None else 0.0
    return float(getattr(item, sort_by))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/funds", response_model=FundsListResponse)
def list_funds(
    channel: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_years: float | None = Query(default=None, ge=0),
    max_fee: float | None = Query(default=None, ge=0),
    keyword: str | None = Query(default=None),
    risk_profile: RiskProfile = Query(default="均衡"),
    sort_by: SortBy = Query(default="final_score"),
    sort_order: SortOrder = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FundsListResponse:
    funds = filter_funds(channel, category, min_years, max_fee, keyword)

    scored_with_fields: list[tuple[FundScore, float, float, float]] = []
    for fund in funds:
        final, base, policy, overlay = final_score(fund, risk_profile)
        scored_with_fields.append(
            (
                FundScore(
                    code=fund.code,
                    name=fund.name,
                    final_score=final,
                    base_score=base,
                    policy_score=policy,
                    overlay_weight=overlay,
                    explanation=explain(fund, risk_profile),
                ),
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
    fund = get_fund(code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    final, base, policy, overlay = final_score(fund, risk_profile)
    return FundDetail(
        code=fund.code,
        name=fund.name,
        final_score=final,
        base_score=base,
        policy_score=policy,
        overlay_weight=overlay,
        explanation=explain(fund, risk_profile),
        risk_level=fund.risk_level,
        channel=fund.channel,
        category=fund.category,
        one_year_return=fund.one_year_return,
        max_drawdown=fund.max_drawdown,
        fee=fund.fee,
    )


@app.get("/api/v1/compare", response_model=list[FundScore])
def compare_funds(
    codes: list[str] = Query(..., min_length=2, max_length=5),
    risk_profile: RiskProfile = Query(default="均衡"),
) -> list[FundScore]:
    if not (2 <= len(codes) <= 5):
        raise HTTPException(status_code=400, detail="codes size must be 2~5")

    results: list[FundScore] = []
    for code in codes:
        fund = get_fund(code)
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund {code} not found")
        final, base, policy, overlay = final_score(fund, risk_profile)
        results.append(
            FundScore(
                code=fund.code,
                name=fund.name,
                final_score=final,
                base_score=base,
                policy_score=policy,
                overlay_weight=overlay,
                explanation=explain(fund, risk_profile),
            )
        )

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results


@app.get("/api/v1/watchlist", response_model=list[WatchlistScore])
def get_watchlist(risk_profile: RiskProfile = Query(default="均衡")) -> list[WatchlistScore]:
    funds = list_watchlist()
    data: list[WatchlistScore] = []
    for fund in funds:
        final, base, policy, overlay = final_score(fund, risk_profile)
        data.append(
            WatchlistScore(
                code=fund.code,
                name=fund.name,
                final_score=final,
                base_score=base,
                policy_score=policy,
                overlay_weight=overlay,
                explanation=explain(fund, risk_profile),
                alerts=watchlist_alerts(fund, risk_profile),
            )
        )
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


@app.post("/api/v1/policy/validate-timestamps", response_model=PolicyTimestampCheckResponse)
def validate_policy_payload(payload: PolicyTimestampCheckRequest) -> PolicyTimestampCheckResponse:
    valid, errors = validate_policy_timestamps(
        payload.published_at,
        payload.effective_from,
        payload.observed_at,
    )
    return PolicyTimestampCheckResponse(policy_id=payload.policy_id, valid=valid, errors=errors)
