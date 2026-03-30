"""
Configuration settings for the fund selection system.

This module contains all configuration parameters for factor calculations,
data processing, and system behavior.
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class FactorConfig:
    """Configuration for factor calculations."""

    # Risk-free rate (China 10-yr treasury yield)
    RISK_FREE_RATE: float = 0.03

    # Trading days per year (China A-share)
    TRADING_DAYS_PER_YEAR: int = 252

    # Minimum data requirements
    MIN_NAV_RECORDS_1Y: int = 252
    MIN_NAV_RECORDS_3Y: int = 756
    MIN_NAV_RECORDS_5Y: int = 1260
    MIN_NAV_RECORDS_SHORT: int = 100

    # Standardization parameters
    Z_SCORE_CLIP: int = 3  # Winsorize at ±3σ
    WINSORIZE_LOWER: float = 0.01
    WINSORIZE_UPPER: float = 0.99

    # Parallel processing
    MAX_WORKERS: int = 5
    BATCH_SIZE: int = 1000

    # Cache TTL (seconds)
    NAV_CACHE_TTL: int = 3600

    # Feature flags
    USE_REAL_FACTORS: bool = os.getenv("USE_REAL_FACTORS", "true").lower() == "true"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    # Database type (mysql, postgresql, sqlite)
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")

    # Connection settings
    HOST: str = os.getenv("DB_HOST", "localhost")
    PORT: int = int(os.getenv("DB_PORT", "3306"))
    USER: str = os.getenv("DB_USER", "root")
    PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DATABASE: str = os.getenv("DB_NAME", "fund_selection")

    # SQLite specific
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "fund_selection.db")


@dataclass
class APISConfig:
    """External API configuration."""

    # AkShare API
    AKSHARE_TIMEOUT: int = 30  # seconds
    AKSHARE_RETRY: int = 3

    # Market data refresh
    MARKET_DATA_REFRESH_INTERVAL: int = 30  # minutes


@dataclass
class LoggingConfig:
    """Logging configuration."""

    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = os.getenv("LOG_LEVEL", "INFO")
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE: str | None = os.getenv("LOG_FILE")


# Global configuration instances
_factor_config: FactorConfig | None = None
_db_config: DatabaseConfig | None = None
_api_config: APISConfig | None = None
_logging_config: LoggingConfig | None = None


def get_factor_config() -> FactorConfig:
    """Get factor configuration singleton."""
    global _factor_config
    if _factor_config is None:
        _factor_config = FactorConfig()
    return _factor_config


def get_db_config() -> DatabaseConfig:
    """Get database configuration singleton."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_api_config() -> APISConfig:
    """Get API configuration singleton."""
    global _api_config
    if _api_config is None:
        _api_config = APISConfig()
    return _api_config


def get_logging_config() -> LoggingConfig:
    """Get logging configuration singleton."""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config
