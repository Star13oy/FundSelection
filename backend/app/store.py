from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from app.data import FUNDS
from app.db import connect, init_db
from app.market_data import clear_market_context, fetch_etf_quote, fetch_otc_quote, prepare_market_context
from app.models import FactorMetrics, Fund, MarketSnapshot, PolicyMetrics
from app.universe import load_fund_universe


def _row_to_fund(row: dict[str, object]) -> Fund:
    return Fund(
        code=str(row["code"]),
        name=str(row["name"]),
        channel=str(row["channel"]),
        category=str(row["category"]),
        fund_type=str(row["fund_type"]),
        years=float(row["years"]),
        scale_billion=float(row["scale_billion"]),
        fee=float(row["fee"]),
        risk_level=str(row["risk_level"]),
        one_year_return=float(row["one_year_return"]),
        max_drawdown=float(row["max_drawdown"]),
        tracking_error=float(row["tracking_error"]) if row["tracking_error"] is not None else None,
        liquidity_label=str(row["liquidity_label"]),
        updated_at=str(row["updated_at"]),
        factors=FactorMetrics(
            returns=float(row["factor_returns"]),
            risk_control=float(row["factor_risk_control"]),
            risk_adjusted=float(row["factor_risk_adjusted"]),
            stability=float(row["factor_stability"]),
            cost_efficiency=float(row["factor_cost_efficiency"]),
            liquidity=float(row["factor_liquidity"]),
            survival_quality=float(row["factor_survival_quality"]),
        ),
        policy=PolicyMetrics(
            support=float(row["policy_support"]),
            execution=float(row["policy_execution"]),
            regulation_safety=float(row["policy_regulation_safety"]),
        ),
    )


def _row_to_market(row: dict[str, object] | None) -> MarketSnapshot | None:
    if not row:
        return None
    return MarketSnapshot(
        current_price=float(row["current_price"]) if row["current_price"] is not None else None,
        previous_close=float(row["previous_close"]) if row["previous_close"] is not None else None,
        intraday_high=float(row["intraday_high"]) if row["intraday_high"] is not None else None,
        intraday_low=float(row["intraday_low"]) if row["intraday_low"] is not None else None,
        open_price=float(row["open_price"]) if row["open_price"] is not None else None,
        price_change_pct=float(row["price_change_pct"]) if row["price_change_pct"] is not None else None,
        price_change_value=float(row["price_change_value"]) if row["price_change_value"] is not None else None,
        nav=float(row["nav"]) if row["nav"] is not None else None,
        nav_date=str(row["nav_date"]) if row["nav_date"] is not None else None,
        nav_estimate=float(row["nav_estimate"]) if row["nav_estimate"] is not None else None,
        nav_estimate_change_pct=float(row["nav_estimate_change_pct"]) if row["nav_estimate_change_pct"] is not None else None,
        volume=float(row["volume"]) if row["volume"] is not None else None,
        turnover=float(row["turnover"]) if row["turnover"] is not None else None,
        quote_time=str(row["quote_time"]) if row["quote_time"] is not None else None,
        source=str(row["source"]) if row["source"] is not None else None,
    )


def init_store() -> None:
    init_db()
    seed_funds()
    try:
        refresh_market_quotes_if_stale()
    except Exception:
        # Do not block the whole API if the remote quote source is temporarily unavailable.
        return


def seed_funds(force: bool = False) -> None:
    if not force:
        with connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS count_rows FROM funds")
                row = cursor.fetchone() or {}
                if int(row.get("count_rows") or 0) >= 20_000:
                    return

    universe = load_fund_universe()
    if not universe:
        universe = list(FUNDS)

    with connect() as conn:
        with conn.cursor() as cursor:
            payloads = [
                {
                    "code": fund.code,
                    "name": fund.name,
                    "channel": fund.channel,
                    "category": fund.category,
                    "fund_type": fund.fund_type,
                    "years": fund.years,
                    "scale_billion": fund.scale_billion,
                    "fee": fund.fee,
                    "risk_level": fund.risk_level,
                    "one_year_return": fund.one_year_return,
                    "max_drawdown": fund.max_drawdown,
                    "tracking_error": fund.tracking_error,
                    "liquidity_label": fund.liquidity_label,
                    "updated_at": fund.updated_at,
                    "factor_returns": fund.factors.returns,
                    "factor_risk_control": fund.factors.risk_control,
                    "factor_risk_adjusted": fund.factors.risk_adjusted,
                    "factor_stability": fund.factors.stability,
                    "factor_cost_efficiency": fund.factors.cost_efficiency,
                    "factor_liquidity": fund.factors.liquidity,
                    "factor_survival_quality": fund.factors.survival_quality,
                    "policy_support": fund.policy.support,
                    "policy_execution": fund.policy.execution,
                    "policy_regulation_safety": fund.policy.regulation_safety,
                }
                for fund in universe
            ]
            sql = """
                INSERT INTO funds (
                    code, name, channel, category, fund_type, years, scale_billion, fee, risk_level,
                    one_year_return, max_drawdown, tracking_error, liquidity_label, updated_at,
                    factor_returns, factor_risk_control, factor_risk_adjusted, factor_stability,
                    factor_cost_efficiency, factor_liquidity, factor_survival_quality,
                    policy_support, policy_execution, policy_regulation_safety
                ) VALUES (
                    %(code)s, %(name)s, %(channel)s, %(category)s, %(fund_type)s, %(years)s, %(scale_billion)s, %(fee)s, %(risk_level)s,
                    %(one_year_return)s, %(max_drawdown)s, %(tracking_error)s, %(liquidity_label)s, %(updated_at)s,
                    %(factor_returns)s, %(factor_risk_control)s, %(factor_risk_adjusted)s, %(factor_stability)s,
                    %(factor_cost_efficiency)s, %(factor_liquidity)s, %(factor_survival_quality)s,
                    %(policy_support)s, %(policy_execution)s, %(policy_regulation_safety)s
                )
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    channel=VALUES(channel),
                    category=VALUES(category),
                    fund_type=VALUES(fund_type),
                    years=VALUES(years),
                    scale_billion=VALUES(scale_billion),
                    fee=VALUES(fee),
                    risk_level=VALUES(risk_level),
                    one_year_return=VALUES(one_year_return),
                    max_drawdown=VALUES(max_drawdown),
                    tracking_error=VALUES(tracking_error),
                    liquidity_label=VALUES(liquidity_label),
                    updated_at=VALUES(updated_at),
                    factor_returns=VALUES(factor_returns),
                    factor_risk_control=VALUES(factor_risk_control),
                    factor_risk_adjusted=VALUES(factor_risk_adjusted),
                    factor_stability=VALUES(factor_stability),
                    factor_cost_efficiency=VALUES(factor_cost_efficiency),
                    factor_liquidity=VALUES(factor_liquidity),
                    factor_survival_quality=VALUES(factor_survival_quality),
                    policy_support=VALUES(policy_support),
                    policy_execution=VALUES(policy_execution),
                    policy_regulation_safety=VALUES(policy_regulation_safety)
            """
            for start in range(0, len(payloads), 500):
                cursor.executemany(sql, payloads[start : start + 500])


def sync_fund_universe() -> dict[str, int]:
    seed_funds(force=True)
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count_rows FROM funds")
            row = cursor.fetchone() or {}
    return {"fund_count": int(row.get("count_rows") or 0)}


def refresh_market_quotes() -> dict[str, object]:
    updated: list[str] = []
    failed: dict[str, str] = {}
    skipped: list[str] = []
    prepare_market_context()

    try:
        payloads: list[dict[str, object]] = []
        for fund in all_funds():
            try:
                quote = fetch_etf_quote(fund.code, use_fallback=False) if fund.channel == "场内" else fetch_otc_quote(fund.code, use_fallback=False)
                if quote is None:
                    skipped.append(fund.code)
                    continue
                payloads.append({"fund_code": fund.code, **quote.as_db()})
                updated.append(fund.code)
            except Exception as exc:
                failed[fund.code] = str(exc)

        with connect() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO market_quotes (
                        fund_code, current_price, previous_close, intraday_high, intraday_low, open_price,
                        price_change_pct, price_change_value, nav, nav_date, nav_estimate, nav_estimate_change_pct,
                        volume, turnover, quote_time, source, raw_payload
                    ) VALUES (
                        %(fund_code)s, %(current_price)s, %(previous_close)s, %(intraday_high)s, %(intraday_low)s, %(open_price)s,
                        %(price_change_pct)s, %(price_change_value)s, %(nav)s, %(nav_date)s, %(nav_estimate)s, %(nav_estimate_change_pct)s,
                        %(volume)s, %(turnover)s, %(quote_time)s, %(source)s, %(raw_payload)s
                    )
                    ON DUPLICATE KEY UPDATE
                        current_price=VALUES(current_price),
                        previous_close=VALUES(previous_close),
                        intraday_high=VALUES(intraday_high),
                        intraday_low=VALUES(intraday_low),
                        open_price=VALUES(open_price),
                        price_change_pct=VALUES(price_change_pct),
                        price_change_value=VALUES(price_change_value),
                        nav=VALUES(nav),
                        nav_date=VALUES(nav_date),
                        nav_estimate=VALUES(nav_estimate),
                        nav_estimate_change_pct=VALUES(nav_estimate_change_pct),
                        volume=VALUES(volume),
                        turnover=VALUES(turnover),
                        quote_time=VALUES(quote_time),
                        fetched_at=CURRENT_TIMESTAMP,
                        source=VALUES(source),
                        raw_payload=VALUES(raw_payload)
                """
                for start in range(0, len(payloads), 500):
                    cursor.executemany(sql, payloads[start : start + 500])
    finally:
        clear_market_context()

    return {
        "updated_codes": updated,
        "failed_codes": failed,
        "updated_count": len(updated),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
    }


def refresh_market_quotes_if_stale(max_age_minutes: int = 30) -> None:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MIN(fetched_at) AS oldest, COUNT(*) AS count_rows FROM market_quotes")
            row = cursor.fetchone() or {}

    if not row.get("count_rows"):
        refresh_market_quotes()
        return

    oldest = row.get("oldest")
    if oldest is None or oldest < datetime.now() - timedelta(minutes=max_age_minutes):
        refresh_market_quotes()


def all_funds() -> list[Fund]:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM funds ORDER BY code")
            rows = cursor.fetchall()
    return [_row_to_fund(row) for row in rows]


def get_fund(code: str) -> Fund | None:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM funds WHERE code = %s", (code,))
            row = cursor.fetchone()
    return _row_to_fund(row) if row else None


def get_market_snapshot(code: str) -> MarketSnapshot | None:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM market_quotes WHERE fund_code = %s", (code,))
            row = cursor.fetchone()
    return _row_to_market(row)


def get_market_snapshots(codes: list[str]) -> dict[str, MarketSnapshot]:
    if not codes:
        return {}
    placeholders = ", ".join(["%s"] * len(codes))
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM market_quotes WHERE fund_code IN ({placeholders})", tuple(codes))
            rows = cursor.fetchall()
    return {str(row["fund_code"]): _row_to_market(row) for row in rows if _row_to_market(row) is not None}


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
    funds: Iterable[Fund] = all_funds()

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
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO watchlist (code) VALUES (%s)", (code,))
    return True


def remove_watchlist(code: str) -> None:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM watchlist WHERE code = %s", (code,))


def list_watchlist() -> list[Fund]:
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT f.*
                FROM watchlist w
                JOIN funds f ON f.code = w.code
                ORDER BY w.created_at DESC
                """
            )
            rows = cursor.fetchall()
    return [_row_to_fund(row) for row in rows]
