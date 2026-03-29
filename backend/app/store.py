from __future__ import annotations

from typing import Iterable

from app.data import FUNDS
from app.models import Fund

WATCHLIST: set[str] = set()


def all_funds() -> list[Fund]:
    return FUNDS.copy()


def get_fund(code: str) -> Fund | None:
    return next((fund for fund in FUNDS if fund.code == code), None)


def filter_funds(
    channel: str | None,
    category: str | None,
    risk_level: str | None,
    min_years: float | None,
    min_scale: float | None,
    max_scale: float | None,
    max_fee: float | None,
    keyword: str | None,
) -> list[Fund]:
    funds: Iterable[Fund] = FUNDS

    if channel:
        funds = (fund for fund in funds if fund.channel == channel)
    if category:
        funds = (fund for fund in funds if fund.category == category)
    if risk_level:
        funds = (fund for fund in funds if fund.risk_level == risk_level)
    if min_years is not None:
        funds = (fund for fund in funds if fund.years >= min_years)
    if min_scale is not None:
        funds = (fund for fund in funds if fund.scale_billion >= min_scale)
    if max_scale is not None:
        funds = (fund for fund in funds if fund.scale_billion <= max_scale)
    if max_fee is not None:
        funds = (fund for fund in funds if fund.fee <= max_fee)
    if keyword:
        kw = keyword.strip().lower()
        funds = (
            fund
            for fund in funds
            if kw in fund.name.lower() or kw in fund.code.lower()
        )

    return list(funds)


def add_watchlist(code: str) -> bool:
    fund = get_fund(code)
    if not fund:
        return False
    WATCHLIST.add(code)
    return True


def remove_watchlist(code: str) -> None:
    WATCHLIST.discard(code)


def list_watchlist() -> list[Fund]:
    return [fund for fund in FUNDS if fund.code in WATCHLIST]
