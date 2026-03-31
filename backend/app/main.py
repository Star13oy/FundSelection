from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.market_data import fetch_etf_quote
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
    SectorHeatItem,
    SortBy,
    SortOrder,
    WatchlistItem,
    WatchlistScore,
)
from app.policy_validation import validate_policy_timestamps
from app.scoring import explain, final_score, watchlist_alerts
from app.store import (
    add_watchlist,
    all_funds,
    filter_funds,
    get_fund,
    get_market_snapshot,
    get_market_snapshots,
    init_store,
    list_watchlist,
    refresh_market_quotes,
    remove_watchlist,
    sync_fund_universe,
)

app = FastAPI(
    title="Fund Quant Backend",
    version="0.2.0",
    description="A股基金量化选基 MVP 后端接口。",
)

# Skip auto-initialization during testing or when explicitly disabled
# Set SKIP_INIT=true in environment to skip database initialization
if not os.getenv("SKIP_INIT", "").lower() in ("true", "1", "yes"):
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

_market_refresh_lock = threading.Lock()
_market_refresh_state: dict[str, object] = {
    "status": "idle",
    "running": False,
    "last_started_at": None,
    "last_finished_at": None,
    "updated_count": 0,
    "failed_count": 0,
    "skipped_count": 0,
    "error": None,
}
_score_cache_lock = threading.Lock()
_score_cache_ttl = timedelta(minutes=5)
_scored_funds_cache: dict[str, dict[str, object]] = {}
_sector_heat_cache_lock = threading.Lock()
_sector_heat_cache_ttl = timedelta(seconds=120)
_sector_heat_cache: dict[str, object] = {"items": None, "fetched_at": None}
_SECTOR_PROXY_FUNDS: tuple[tuple[str, str], ...] = (
    ("半导体", "512480"),
    ("白酒", "512690"),
    ("新能源", "516160"),
    ("人工智能", "159819"),
)


def _refresh_market_worker() -> None:
    try:
        summary = refresh_market_quotes()
        with _sector_heat_cache_lock:
            _sector_heat_cache["items"] = None
            _sector_heat_cache["fetched_at"] = None
        with _market_refresh_lock:
            _market_refresh_state.update(
                {
                    "status": "completed",
                    "running": False,
                    "last_finished_at": datetime.now().isoformat(timespec="seconds"),
                    "updated_count": summary.get("updated_count", 0),
                    "failed_count": summary.get("failed_count", 0),
                    "skipped_count": summary.get("skipped_count", 0),
                    "error": None,
                }
            )
    except Exception as exc:
        with _market_refresh_lock:
            _market_refresh_state.update(
                {
                    "status": "failed",
                    "running": False,
                    "last_finished_at": datetime.now().isoformat(timespec="seconds"),
                    "error": str(exc),
                }
            )


def _score_fields(fund: Fund, risk_profile: RiskProfile) -> tuple[float, float, float, float]:
    return final_score(fund, risk_profile)


def _invalidate_scored_funds_cache() -> None:
    with _score_cache_lock:
        _scored_funds_cache.clear()


def _get_scored_funds(risk_profile: RiskProfile) -> list[tuple[Fund, float, float, float, float]]:
    cache_key = str(risk_profile)
    with _score_cache_lock:
        cached = _scored_funds_cache.get(cache_key)
        if cached is not None:
            cached_at = cached.get("fetched_at")
            cached_items = cached.get("items")
            if isinstance(cached_at, datetime) and isinstance(cached_items, list):
                if datetime.now() - cached_at < _score_cache_ttl:
                    return cached_items

    scored_items: list[tuple[Fund, float, float, float, float]] = []
    for fund in all_funds():
        final, base, policy, overlay = _score_fields(fund, risk_profile)
        scored_items.append((fund, final, base, policy, overlay))

    with _score_cache_lock:
        _scored_funds_cache[cache_key] = {
            "items": scored_items,
            "fetched_at": datetime.now(),
        }
    return scored_items


def _get_sector_heat_items() -> list[SectorHeatItem]:
    with _sector_heat_cache_lock:
        cached_at = _sector_heat_cache.get("fetched_at")
        cached_items = _sector_heat_cache.get("items")
        if isinstance(cached_at, datetime) and isinstance(cached_items, list):
            if datetime.now() - cached_at < _sector_heat_cache_ttl:
                return cached_items

    items: list[SectorHeatItem] = []
    for label, code in _SECTOR_PROXY_FUNDS:
        quote = fetch_etf_quote(code)
        items.append(
            SectorHeatItem(
                label=label,
                code=code,
                change_pct=quote.price_change_pct if quote else None,
                current_price=quote.current_price if quote else None,
                quote_time=quote.quote_time if quote else None,
                source=quote.source if quote else None,
            )
        )

    with _sector_heat_cache_lock:
        _sector_heat_cache["items"] = items
        _sector_heat_cache["fetched_at"] = datetime.now()
    return items


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
        fund_type=fund.fund_type,
        scale_billion=fund.scale_billion,
        risk_level=fund.risk_level,
        liquidity_label=fund.liquidity_label,
        final_score=final,
        base_score=base,
        policy_score=policy,
        overlay_weight=overlay,
        one_year_return=fund.one_year_return,
        max_drawdown=fund.max_drawdown,
        explanation=explain(fund, risk_profile),
        market=market,
    )


def _build_fund_detail(fund: Fund, risk_profile: RiskProfile) -> FundDetail:
    score = _build_fund_score(fund, risk_profile, get_market_snapshot(fund.code))
    return FundDetail(
        **score.model_dump(),
        years=fund.years,
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
    filtered = filter_funds(channel, category, risk_level, min_years, min_scale, max_scale, max_fee, keyword)
    filtered_codes = {fund.code for fund in filtered}
    scored_with_fields = [row for row in _get_scored_funds(risk_profile) if row[0].code in filtered_codes]

    reverse = sort_order == "desc"
    scored_with_fields.sort(
        key=lambda row: (
            row[4] if sort_by == "fee"
            else row[0].one_year_return if sort_by == "one_year_return"
            else row[0].max_drawdown if sort_by == "max_drawdown"
            else row[1] if sort_by == "final_score"
            else row[2] if sort_by == "base_score"
            else row[3]
        ),
        reverse=reverse,
    )

    total = len(scored_with_fields)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = scored_with_fields[start:end]
    market_map = get_market_snapshots([row[0].code for row in page_rows])
    items = [_build_fund_score(row[0], risk_profile, market_map.get(row[0].code)) for row in page_rows]
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
    with _market_refresh_lock:
        if _market_refresh_state["running"]:
            return dict(_market_refresh_state)
        _market_refresh_state.update(
            {
                "status": "started",
                "running": True,
                "last_started_at": datetime.now().isoformat(timespec="seconds"),
                "error": None,
            }
        )
    thread = threading.Thread(target=_refresh_market_worker, daemon=True)
    thread.start()
    return dict(_market_refresh_state)


@app.get("/api/v1/market/refresh-status")
def refresh_market_status() -> dict[str, object]:
    with _market_refresh_lock:
        return dict(_market_refresh_state)


@app.get("/api/v1/market/sector-heat", response_model=list[SectorHeatItem])
def market_sector_heat() -> list[SectorHeatItem]:
    return _get_sector_heat_items()


@app.post("/api/v1/funds/sync")
def sync_funds() -> dict[str, object]:
    summary = sync_fund_universe()
    _invalidate_scored_funds_cache()
    return {"status": "ok", **summary}


@app.post("/api/v1/policy/validate-timestamps", response_model=PolicyTimestampCheckResponse)
def validate_policy_payload(payload: PolicyTimestampCheckRequest) -> PolicyTimestampCheckResponse:
    valid, errors = validate_policy_timestamps(
        payload.published_at,
        payload.effective_from,
        payload.observed_at,
    )
    return PolicyTimestampCheckResponse(policy_id=payload.policy_id, valid=valid, errors=errors)
