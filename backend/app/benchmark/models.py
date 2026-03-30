"""
Benchmark index models for Chinese A-share market comparison.

This module defines Pydantic models for representing market benchmark indices
and their historical price data. These models enable calculation of Information
Ratio, tracking error, and up/down capture ratios for fund performance analysis.

Critical infrastructure: Benchmark data is essential for relative performance
metrics. Without benchmarks, funds cannot be compared to market standards.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class BenchmarkIndex(BaseModel):
    """Represents a market benchmark index for Chinese A-shares.

    Attributes:
        index_code: Unique index code (e.g., '000300.SH' for CSI 300, '399001.SZ' for SZSE Composite)
        index_name: Index name in Chinese (e.g., '沪深300', '上证指数')
        index_type: Index category - broad, sector, style, bond, or commodity
        market: Market identifier - SH (Shanghai), SZ (Shenzhen), CSI (CSEC), CIC (ChinaBond)
        base_date: Index base date when the index was established
        base_value: Base value at inception (usually 100 or 1000)
        constituents_count: Number of constituent stocks/bonds (0 for bond indices)
        suitable_for_categories: List of fund categories that should use this benchmark
        data_source: Primary data source - akshare, eastmoney, wind, or chinafuck
        update_frequency: Data update frequency - daily, weekly, or monthly
        description: Index description and methodology
        created_at: Record creation timestamp
        updated_at: Record update timestamp

    Examples:
        >>> csi300 = BenchmarkIndex(
        ...     index_code="000300.SH",
        ...     index_name="沪深300",
        ...     index_type="broad",
        ...     market="CSI",
        ...     base_date=date(2004, 12, 31),
        ...     base_value=1000,
        ...     constituents_count=300,
        ...     suitable_for_categories=["宽基", "混合", "股票多空"]
        ... )
    """

    # Identifiers
    index_code: str = Field(
        ...,
        description="Index code (e.g., '000300.SH', '399001.SZ')",
        min_length=9,
        max_length=20
    )

    index_name: str = Field(
        ...,
        description="Index name (e.g., '沪深300', '上证指数')",
        min_length=2,
        max_length=50
    )

    # Classification
    index_type: Literal['broad', 'sector', 'style', 'bond', 'commodity'] = Field(
        ...,
        description="Index category: broad (market-wide), sector (industry), style (value/growth), bond, or commodity"
    )

    market: Literal['SH', 'SZ', 'CSI', 'CIC'] = Field(
        ...,
        description="Market: Shanghai (SH), Shenzhen (SZ), CSEC (CSI), or ChinaBond (CIC)"
    )

    # Metadata
    base_date: date = Field(
        ...,
        description="Index base date when established"
    )

    base_value: float = Field(
        ...,
        ge=0,
        description="Base value at inception (usually 100 or 1000)"
    )

    constituents_count: int | None = Field(
        None,
        ge=0,
        description="Number of constituent stocks/bonds (0 for bond indices)"
    )

    # Usage mapping
    suitable_for_categories: list[str] = Field(
        ...,
        min_length=1,
        description="Fund categories that should use this benchmark (e.g., ['宽基', '混合'])"
    )

    # Data source
    data_source: Literal['akshare', 'eastmoney', 'wind', 'chinafuck'] = Field(
        default='akshare',
        description="Primary data source for index data"
    )

    # Update schedule
    update_frequency: Literal['daily', 'weekly', 'monthly'] = Field(
        default='daily',
        description="Update frequency for historical data"
    )

    # Documentation
    description: str | None = Field(
        None,
        max_length=500,
        description="Index description, methodology, and composition details"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "index_code": "000300.SH",
                "index_name": "沪深300",
                "index_type": "broad",
                "market": "CSI",
                "base_date": "2004-12-31",
                "base_value": 1000,
                "constituents_count": 300,
                "suitable_for_categories": ["宽基", "混合", "股票多空"],
                "data_source": "akshare",
                "update_frequency": "daily",
                "description": "沪深300指数由上海和深圳证券市场中市值大、流动性好的300只股票组成"
            }
        }


class BenchmarkHistory(BaseModel):
    """Historical index level data for benchmark indices.

    Attributes:
        index_code: Index code (e.g., '000300.SH')
        trade_date: Trading date
        close_price: Closing price/index level
        open_price: Opening price/index level (optional)
        high_price: Highest price/index level (optional)
        low_price: Lowest price/index level (optional)
        volume: Trading volume (optional, not applicable for indices)
        turnover: Trading turnover (optional, not applicable for indices)
        daily_return: Daily return percentage calculated as (P_t - P_{t-1}) / P_{t-1}

    Examples:
        >>> history = BenchmarkHistory(
        ...     index_code="000300.SH",
        ...     trade_date=date(2025, 3, 30),
        ...     close_price=3521.45,
        ...     daily_return=0.0125
        ... )
    """

    index_code: str = Field(
        ...,
        description="Index code",
        min_length=9,
        max_length=20
    )

    trade_date: date = Field(
        ...,
        description="Trading date"
    )

    close_price: float = Field(
        ...,
        ge=0,
        description="Closing price/index level"
    )

    open_price: float | None = Field(
        None,
        ge=0,
        description="Opening price/index level"
    )

    high_price: float | None = Field(
        None,
        ge=0,
        description="Highest price/index level of the day"
    )

    low_price: float | None = Field(
        None,
        ge=0,
        description="Lowest price/index level of the day"
    )

    volume: float | None = Field(
        None,
        ge=0,
        description="Trading volume (not applicable for most indices)"
    )

    turnover: float | None = Field(
        None,
        ge=0,
        description="Trading turnover in RMB (not applicable for most indices)"
    )

    # Calculated fields
    daily_return: float | None = Field(
        None,
        description="Daily return percentage (e.g., 0.0125 for 1.25%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "index_code": "000300.SH",
                "trade_date": "2025-03-30",
                "close_price": 3521.45,
                "open_price": 3485.32,
                "high_price": 3530.18,
                "low_price": 3478.90,
                "daily_return": 0.0125
            }
        }


class BenchmarkMapping(BaseModel):
    """Maps fund categories to appropriate benchmark indices.

    This model stores the mapping logic for auto-selecting benchmarks
    based on fund category and sector.

    Attributes:
        fund_category: Fund category name (e.g., '宽基', '科技', '债券')
        benchmark_code: Primary benchmark index code
        fallback_benchmark_codes: List of fallback benchmarks if primary unavailable
        sector_override: Override benchmark for specific sectors (optional)
        description: Mapping rationale
    """

    fund_category: str = Field(
        ...,
        description="Fund category name (e.g., '宽基', '科技', '债券')"
    )

    benchmark_code: str = Field(
        ...,
        description="Primary benchmark index code"
    )

    fallback_benchmark_codes: list[str] = Field(
        default_factory=list,
        description="List of fallback benchmarks if primary unavailable"
    )

    sector_override: dict[str, str] | None = Field(
        None,
        description="Override benchmark for specific sectors (e.g., {'半导体': '399006.SZ'})"
    )

    description: str | None = Field(
        None,
        description="Mapping rationale and explanation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "fund_category": "科技",
                "benchmark_code": "399006.SZ",
                "fallback_benchmark_codes": ["000300.SH", "399001.SZ"],
                "sector_override": {
                    "半导体": "399006.SZ",
                    "人工智能": "399006.SZ"
                },
                "description": "Tech funds use CSI Tech as primary benchmark"
            }
        }


# Standard benchmark index codes for Chinese A-share markets
STANDARD_BENCHMARK_CODES = {
    # Broad market indices
    "CSI_300": "000300.SH",  # 沪深300
    "CSI_500": "000905.SH",  # 中证500
    "CSI_1000": "399406.SZ",  # 中证1000
    "SH_COMPOSITE": "000001.SH",  # 上证综指
    "SZ_COMPOSITE": "399001.SZ",  # 深证成指
    "CSI_100": "000919.SH",  # 中证100

    # Sector indices
    "CSI_TECH": "399006.SZ",  # 中证科技
    "CSI_NEW_ENERGY": "399412.SZ",  # 中证新能源
    "CSI_HEALTHCARE": "399911.SZ",  # 中证医药
    "CSI_CONSUMER": "399932.SZ",  # 中证消费
    "CSI_FINANCIAL": "399975.SZ",  # 中证金融
    "CSI_SEMI": "399006.SZ",  # 半导体 (uses CSI Tech)

    # Style indices
    "CSI_VALUE": "399932.SZ",  # 价值
    "CSI_GROWTH": "399911.SZ",  # 成长

    # Bond indices
    "CHINA_BOND_COMPOSITE": "CBA00101.CS",  # 中债综合财富指数
    "CHINA_BOND_TREASURY": "CBA00151.CS",  # 中债国债总财富指数
    "CHINA_BOND_CORPORATE": "CBA00201.CS",  # 中债企业债总财富指数
}
