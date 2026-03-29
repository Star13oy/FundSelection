from __future__ import annotations

import os
from functools import lru_cache

import pymysql
from pymysql.cursors import DictCursor


@lru_cache(maxsize=1)
def settings() -> dict[str, str]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": os.getenv("MYSQL_PORT", "3306"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "fund_selection"),
    }


def connect(with_database: bool = True):
    cfg = settings()
    params = {
        "host": cfg["host"],
        "port": int(cfg["port"]),
        "user": cfg["user"],
        "password": cfg["password"],
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }
    if with_database:
        params["database"] = cfg["database"]
    return pymysql.connect(**params)


def init_db() -> None:
    cfg = settings()

    with connect(with_database=False) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS funds (
                    code VARCHAR(16) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    channel VARCHAR(16) NOT NULL,
                    category VARCHAR(32) NOT NULL,
                    fund_type VARCHAR(32) NOT NULL,
                    years DOUBLE NOT NULL,
                    scale_billion DOUBLE NOT NULL,
                    fee DOUBLE NOT NULL,
                    risk_level VARCHAR(16) NOT NULL,
                    one_year_return DOUBLE NOT NULL,
                    max_drawdown DOUBLE NOT NULL,
                    tracking_error DOUBLE NULL,
                    liquidity_label VARCHAR(32) NOT NULL,
                    updated_at VARCHAR(32) NOT NULL,
                    factor_returns DOUBLE NOT NULL,
                    factor_risk_control DOUBLE NOT NULL,
                    factor_risk_adjusted DOUBLE NOT NULL,
                    factor_stability DOUBLE NOT NULL,
                    factor_cost_efficiency DOUBLE NOT NULL,
                    factor_liquidity DOUBLE NOT NULL,
                    factor_survival_quality DOUBLE NOT NULL,
                    policy_support DOUBLE NOT NULL,
                    policy_execution DOUBLE NOT NULL,
                    policy_regulation_safety DOUBLE NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS market_quotes (
                    fund_code VARCHAR(16) PRIMARY KEY,
                    current_price DOUBLE NULL,
                    previous_close DOUBLE NULL,
                    intraday_high DOUBLE NULL,
                    intraday_low DOUBLE NULL,
                    open_price DOUBLE NULL,
                    price_change_pct DOUBLE NULL,
                    price_change_value DOUBLE NULL,
                    nav DOUBLE NULL,
                    nav_date VARCHAR(32) NULL,
                    nav_estimate DOUBLE NULL,
                    nav_estimate_change_pct DOUBLE NULL,
                    volume DOUBLE NULL,
                    turnover DOUBLE NULL,
                    quote_time VARCHAR(32) NULL,
                    fetched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(64) NULL,
                    raw_payload JSON NULL,
                    CONSTRAINT fk_market_quotes_fund
                        FOREIGN KEY (fund_code) REFERENCES funds(code)
                        ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS watchlist (
                    code VARCHAR(16) PRIMARY KEY,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_watchlist_fund
                        FOREIGN KEY (code) REFERENCES funds(code)
                        ON DELETE CASCADE
                )
                """
            )
